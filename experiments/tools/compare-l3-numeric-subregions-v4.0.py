#!/usr/bin/env python3
"""CT L3 numeric-label exterior coverage (crop-cap filtered), with no guessed anatomy correspondence.

Inputs: a genuine one-L3 NIfTI mask with exactly 7 nonzero integer labels,
       1+ independently authored OBJ shapes. Outputs numeric CLASS IDs only.
The 1..7 IDs are NOT mapped to vertebral body, lamina etc without source legend.
All models share a SINGLE v2.4 RAS-initialized registration; no scale adjustment.
Distances from CT class exterior -> ANY model surface are NOT articular-surface
or same-anatomic-region accuracy. NEVER grants anatomical approval.
"""
import argparse, importlib.util, json, math
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_erosion, generate_binary_structure
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes
import nibabel as nib
import trimesh

CORE=Path(__file__).with_name('compare-l3-reference-v3.2.py')
s=importlib.util.spec_from_file_location('l3_ref_v32',CORE)
core=importlib.util.module_from_spec(s)
s.loader.exec_module(core)

def label_data(mask,affine):
    if mask.ndim!=3 or not np.issubdtype(mask.dtype,np.integer):
        raise ValueError('Requires 3D INTEGER label mask')
    labels=sorted(int(v) for v in np.unique(mask) if v>0)
    if len(labels)!=7:
        raise ValueError(f'Requires 7 positive labels, got {labels}; DO NOT guess anatomy')
    if (mask<0).any() or not np.isfinite(affine).all() or abs(np.linalg.det(affine[:3,:3]))<1e-8:
        raise ValueError('Invalid label/affine')
    union=mask>0
    pos=np.where(union)
    if union.sum()<500:
        raise ValueError('L3 mask too small')
    boundary_faces={'x_min':int(union[0,:,:].sum()),
                    'x_max':int(union[-1,:,:].sum()),
                    'y_min':int(union[:,0,:].sum()),
                    'y_max':int(union[:,-1,:].sum()),
                    'z_min':int(union[:,:,0].sum()),
                    'z_max':int(union[:,:,-1].sum())}
    touched=any(v>0 for v in boundary_faces.values())
    bmin=np.maximum(np.array([p.min() for p in pos])-2,0)
    bmax=np.minimum(np.array([p.max() for p in pos])+3,mask.shape)
    local=union[tuple(slice(int(a),int(b)) for a,b in zip(bmin,bmax))]
    # One-voxel zero-padding closes a cropped surface numerically, but cannot
    # recover anatomy outside the crop. Flag every boundary contact.
    v,f,_,_=marching_cubes(np.pad(local.astype(np.uint8),1),.5)
    # Locate candidate triangles in ORIGINAL mask voxel coordinates, before affine.
    # Face-centroid proximity to any original image border excludes synthetic cap
    # triangles and neighboring uncertain CT boundary geometry. This is still NOT
    # a reliable proof of complete anatomy or original segmentation correctness.
    original_voxel_vertices=v-1+bmin
    face_centers=original_voxel_vertices[f].mean(axis=1)
    edge_margin_voxels=2.0
    allowed=np.all((face_centers>=edge_margin_voxels) &
                   (face_centers<np.asarray(mask.shape)-1-edge_margin_voxels),axis=1)
    kept=int(allowed.sum())
    if kept<300 or kept/len(f)<0.3:
        raise ValueError('Too few non-border CT triangles; cannot compare this crop')
    v=nib.affines.apply_affine(affine,original_voxel_vertices)
    mesh=trimesh.Trimesh(vertices=v,faces=f[allowed],process=False)
    exterior=union&~binary_erosion(union,
                   structure=generate_binary_structure(3,1),border_value=0)
    vox=np.column_stack(np.where(exterior))
    inside=np.all((vox>=2) & (vox<np.asarray(mask.shape)-3),axis=1)
    vox=vox[inside]
    if len(vox)<150:raise ValueError('Too few safe exterior voxels after crop filtering')
    xyz=nib.affines.apply_affine(affine,vox)
    outer_labels=mask[tuple(vox.T)]
    return mesh,cKDTree(xyz),outer_labels,labels,{
        'touches_original_crop_boundary':bool(touched),
        'positive_voxels_on_six_crop_faces':boundary_faces,
        'zero_padding_used_for_surface_closure':True,
        'border_proximity_exclusion_voxels':2.0,
        'reference_triangles_all':int(len(f)),
        'reference_triangles_after_border_filter':kept,
        'fraction_of_reference_triangles_excluded':round(float(1-kept/len(f)),4),
        'reference_completeness_verified':False}

def stats(arr):
    arr=np.asarray(arr,dtype=float)
    if len(arr)<30:return {'n':len(arr),'status':'insufficient surface samples'}
    return {'n':len(arr),'p95_mm':round(float(np.quantile(arr,.95)),3),
            'rms_mm':round(float(np.sqrt(np.mean(arr**2))),3),
            'over10_frac':round(float(np.mean(arr>10.)),4)}

def compare(baseline,candidates,mask,affine,n=7000):
    ref,tree,classes,labels,crop_diagnostic=label_data(mask,affine)
    if n<3500:raise ValueError('Sampling too small')
    old=core.samples(baseline,n,19)
    ct=core.samples(ref,n,29)
    # RAS-only initialization, as in v3.4. Check orientation; do not assume approval.
    r,t=core.icp_fit(old,ct,np.eye(3),iterations=80)
    angle=math.degrees(math.acos(float(np.clip((np.trace(r)-1)/2,-1,1))))
    ct_local=(ct-t)@r
    nearest_voxel_mm,idx=tree.query(ct,workers=-1)
    ct_ids=classes[idx]
    results={}
    for name,mesh in {'v24':baseline,**candidates}.items():
        sampled=core.samples(mesh,n,19)
        d=cKDTree(sampled).query(ct_local,workers=-1)[0]
        results[name]={'all':stats(d),
                       'by_numeric_label_only':{
                           str(k):stats(d[ct_ids==k]) for k in labels}}
    delta={}
    for name in candidates:
        delta[name]={str(k):round(results[name]['by_numeric_label_only'][str(k)].get('p95_mm',float('nan'))-
                            results['v24']['by_numeric_label_only'][str(k)].get('p95_mm',float('nan')),3)
                     for k in labels}
    return {'status':'DIAGNOSTIC_ONLY_NOT_ANATOMICAL_PASS',
            'numeric_labels_observed':labels,
            'numeric_to_anatomical_names_source_verified':False,
            'reference_crop_diagnostic':crop_diagnostic,
            'registration':{'baseline_fixed_for_all':True,'scale_fixed':True,
                'RAS_initialized':True,'rotation_degrees':round(angle,2),
                'expert_verified':False},
            'reference_exterior_class_assignment':{
                'nearest_surface_voxel_p95_mm':round(float(np.quantile(nearest_voxel_mm,.95)),3),
                'internal_label_boundaries_excluded':True},
            'results':results,'delta_candidate_minus_v24_p95_mm':delta,
            'limitations':['Unverified numeric-class-to-anatomical-name map; DO NOT name regions',
                           'Border-adjacent synthetic cap faces excluded; missing anatomy outside crop remains UNKNOWN',
                           'Registration is not expert-verified',
                           'Only CT exterior -> unlabelled whole model distances',
                           'No same-anatomic-region correspondence, normals or facet congruence',
                           'Sampling/voxel resolution and population variation are unquantified',
                           'No clinical, teaching or anatomical approval']}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mask',type=Path,required=True)
    ap.add_argument('--v24',type=Path,required=True)
    ap.add_argument('--v33',type=Path,required=True)
    ap.add_argument('--v35',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--samples',type=int,default=7000)
    args=ap.parse_args()
    img=nib.load(str(args.mask))
    arr=np.asarray(img.dataobj)
    if not np.issubdtype(arr.dtype,np.integer):
        if not np.isfinite(arr).all() or not np.array_equal(arr,np.round(arr)):
            raise ValueError('Label array not integer-valued')
        arr=arr.astype(np.int16)
    models={name:trimesh.load(f,force='mesh',process=False)
            for name,f in [('v24',args.v24),('v33',args.v33),('v35',args.v35)]}
    result=compare(models['v24'],{'v33':models['v33'],'v35':models['v35']},arr,img.affine,args.samples)
    result['case_checksum_tracking_required']=True
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'result_file':str(args.out),'numeric_labels':result['numeric_labels_observed'],
                     'anatomical_names_verified':False,
                     'crop_boundary_touched':result['reference_crop_diagnostic']['touches_original_crop_boundary'],
                     'reference_triangles_excluded_fraction':result['reference_crop_diagnostic']['fraction_of_reference_triangles_excluded'],
                     'anatomy_approved':False}))

if __name__=='__main__':main()
