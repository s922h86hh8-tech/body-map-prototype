#!/usr/bin/env python3
"""L3 CT labeled-subregion exterior-surface coverage screening (NOT anatomical approval).

Requires an L3-ONLY, voxel-level, seven-subregion NIfTI mask and an EXPLICIT
source-verified numeric label map. VerSe whole-L3 label 22 does NOT contain
seven subregion labels and MUST NOT be used as this input.

One fixed rigid registration is computed from the baseline's whole L3 surface
to the union of all seven reference labels. Candidate meshes reuse that same
registration. Only CT EXTERIOR surface triangles are evaluated, not internal
boundaries introduced by anatomical subregion labeling.
The generated model has no independently validated anatomical region IDs:
per-structure coverage is CT-region -> WHOLE unlabelled model, NOT true
same-region surface congruence, NOT a source of educational/clinical pass.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_erosion, generate_binary_structure
from scipy.spatial import cKDTree
from skimage.measure import marching_cubes
import trimesh

REGION_NAMES=('vertebral_body','pedicle','lamina','spinous_process',
              'transverse_process','superior_articular_process',
              'inferior_articular_process')
CORE=Path(__file__).with_name('compare-l3-reference-v3.2.py')
_spec=importlib.util.spec_from_file_location('l3_core_v32', CORE)
_core=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_core)

def verify_map(mapping,mask):
    if set(mapping)!=set(REGION_NAMES):
        raise ValueError('Label map must contain exactly the seven named L3 subregions')
    values=list(mapping.values())
    if any(type(v) is not int or v<=0 for v in values) or len(set(values))!=7:
        raise ValueError('Seven label IDs must be distinct positive integers verified from the source')
    unique=set(int(v) for v in np.unique(mask))
    unexpected=unique-({0}|set(values))
    if unexpected:
        raise ValueError('Unexpected mask label(s): '+str(sorted(unexpected))+
                         '; do not guess the source label mapping')
    missing=[name for name,val in mapping.items() if val not in unique]
    if missing:
        raise ValueError('Missing anatomical region labels: '+','.join(missing))
    return True

def voxel_world(vox,affine):
    vox=np.asarray(vox,dtype=np.float64)
    return vox@affine[:3,:3].T+affine[:3,3]

def reference_data(mask,affine,mapping):
    verify_map(mapping,mask)
    if mask.ndim!=3 or not np.all(np.isfinite(affine)) or np.linalg.det(affine[:3,:3])==0:
        raise ValueError('Invalid 3D mask/affine')
    union=np.isin(mask,list(mapping.values()))
    if int(union.sum())<400:
        raise ValueError('Too few segmented L3 voxels')
    occupied=np.where(union)
    for axis in range(3):
        if occupied[axis].min()==0 or occupied[axis].max()==mask.shape[axis]-1:
            raise ValueError('L3 reference touches image boundary; complete vertebra required')
    crop_min=np.maximum(np.array([v.min() for v in occupied])-2,0)
    crop_max=np.minimum(np.array([v.max() for v in occupied])+3,mask.shape)
    slices=tuple(slice(int(a),int(b)) for a,b in zip(crop_min,crop_max))
    verts,faces,_,_=marching_cubes(union[slices].astype(np.uint8),.5)
    ref_mesh=trimesh.Trimesh(vertices=voxel_world(verts+crop_min,affine),
                            faces=faces,process=False)
    # Label nearest CT surface VOXELS, not subregion interface voxels.
    exterior=union & ~binary_erosion(union,structure=generate_binary_structure(3,1),
                                     border_value=0)
    surface_voxels=np.column_stack(np.where(exterior))
    world=voxel_world(surface_voxels,affine)
    classes=mask[tuple(surface_voxels.T)]
    return ref_mesh,cKDTree(world),classes,{
        'voxel_counts':{key:int(np.count_nonzero(mask==value))
                        for key,value in mapping.items()},
        'exterior_voxel_count':int(len(classes)),
        'voxel_spacing_mm':np.linalg.norm(affine[:3,:3],axis=0).round(4).tolist()}

def stats(v):
    v=np.asarray(v,dtype=float)
    return {'samples':len(v),
            'p50_mm':round(float(np.median(v)),3),
            'p95_mm':round(float(np.quantile(v,.95)),3),
            'rms_mm':round(float(np.sqrt(np.mean(v*v))),3),
            'fraction_above_10mm':round(float(np.mean(v>10)),4)}

def evaluate(baseline,reference,tree,classes,mapping,candidates=None,n=14000):
    if n<3500:
        raise ValueError('At least 3500 common reference surface samples required')
    source=_core.samples(baseline,n,19)
    ct=_core.samples(reference,n,29)
    rotation,translation=_core.icp_fit(source,ct,np.eye(3),iterations=80)
    ct_in_model=(ct-translation)@rotation
    angle=math.degrees(math.acos(float(np.clip((np.trace(rotation)-1)/2,-1,1))))
    distances_to_voxel,idx=tree.query(ct,workers=-1)
    spacing=np.linalg.norm(reference.vertices.max(axis=0)-reference.vertices.min(axis=0))
    if not np.isfinite(spacing):
        raise ValueError('Invalid reference surface bounds')
    # Exterior surface facets are assigned by nearest exterior label voxel.
    # Report mismatched/ambiguous nearest-cell distance; do not silently discard.
    labels=classes[idx]
    clouds={'baseline':baseline}
    clouds.update(candidates or {})
    results={}
    for name,mesh in clouds.items():
        model_surface=_core.samples(mesh,n,19)
        dist=cKDTree(model_surface).query(ct_in_model,workers=-1)[0]
        per_region={}
        for region,value in mapping.items():
            subset=dist[labels==value]
            per_region[region]=stats(subset) if len(subset)>=40 else {
                'samples':int(len(subset)), 'error':'too few exterior surface points'}
        results[name]={
            'whole_reference_surface_to_unlabelled_model':stats(dist),
            'ct_exterior_region_to_unlabelled_model':per_region}
    changed={}
    for cname in (candidates or {}):
        for name in REGION_NAMES:
            a=results['baseline']['ct_exterior_region_to_unlabelled_model'][name]
            b=results[cname]['ct_exterior_region_to_unlabelled_model'][name]
            if 'p95_mm' in a and 'p95_mm' in b:
                changed.setdefault(cname,{})[name]=round(b['p95_mm']-a['p95_mm'],3)
    return {'status':'SCREENING_ONLY_NO_ANATOMICAL_APPROVAL',
            'registration':{'baseline_RAS_initialization':True,
                            'fixed_for_all_candidates':True,
                            'axis_rotation_degrees':round(angle,3),
                            'expert_verified':False,
                            'matrix':rotation.round(6).tolist(),
                            'translation_mm':translation.round(4).tolist()},
            'ct_exterior_points':n,
            'exterior_label_assignment':{
                'nearest_exterior_voxel_mean_distance_mm':round(float(distances_to_voxel.mean()),4),
                'nearest_exterior_voxel_p95_distance_mm':round(float(np.quantile(distances_to_voxel,.95)),4),
                'internal_class_boundaries_excluded':True},
            'results':results,'delta_p95_candidate_minus_baseline_mm':changed,
            'limitations':['Source mapping and L3 identity require independent verification',
                           'Source labels refer to CT exterior only; model anatomical region labels are absent',
                           'Distance to whole unlabeled model is NOT same-structure facet/lamina accuracy',
                           'Registration and correspondence unverified by an anatomy expert',
                           'Only a sampled surface, resolution-dependent nearest-neighbor proxy',
                           'Not a clinical, surgical, or teaching-quality approval']}

def self_test():
    # 7 spatially distinct synthetic slab labels on the exterior of one ellipsoid.
    shape=(66,62,54)
    indices=np.indices(shape)
    union=((indices[0]-33)/22)**2+((indices[1]-31)/20)**2+((indices[2]-27)/16)**2<1
    x=indices[0]
    mapping={name:i+1 for i,name in enumerate(REGION_NAMES)}
    mask=np.zeros(shape,dtype=np.uint8)
    for i,name in enumerate(REGION_NAMES):
        lo=9+i*7
        hi=9+(i+1)*7
        mask[union & (x>=lo)&(x<hi)]=mapping[name]
    # Ensure final slab covers all remaining union voxels.
    mask[union & (x>=58)]=mapping[REGION_NAMES[-1]]
    affine=np.diag([1.1,1.2,1.3,1.])
    ref,tree,classes,meta=reference_data(mask,affine,mapping)
    baseline=ref.copy()
    trial=ref.copy()
    trial.apply_scale(1.08)
    report=evaluate(baseline,ref,tree,classes,mapping,{'scaled_trial':trial},n=5500)
    assert report['status']=='SCREENING_ONLY_NO_ANATOMICAL_APPROVAL'
    assert report['exterior_label_assignment']['internal_class_boundaries_excluded']
    assert set(report['results']['baseline']['ct_exterior_region_to_unlabelled_model'])==set(REGION_NAMES)
    assert len(report['delta_p95_candidate_minus_baseline_mm']['scaled_trial'])>=5
    try:
        verify_map({**mapping,'extra':8},mask)
        raise AssertionError('Invalid map was accepted')
    except ValueError:
        pass
    print(json.dumps({'synthetic_test':'PASS',
                     'regions':len(mapping),
                     'baseline_p95_mm':report['results']['baseline']['whole_reference_surface_to_unlabelled_model']['p95_mm'],
                     'deformed_trial_p95_mm':report['results']['scaled_trial']['whole_reference_surface_to_unlabelled_model']['p95_mm'],
                     'ct_from_actual_subject':False,
                     'anatomical_approval':False},ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--baseline',type=Path)
    ap.add_argument('--candidate',type=Path)
    ap.add_argument('--subregions',type=Path)
    ap.add_argument('--label-map',type=Path,help='JSON with labels: {7 region names: integer IDs}')
    ap.add_argument('--source-l3-confirmed',action='store_true',
                    help='Confirm that this segmented mask is only L3, not all vertebrae')
    ap.add_argument('--samples',type=int,default=14000)
    ap.add_argument('--out',type=Path,default=Path('private-l3-subregions-report.json'))
    args=ap.parse_args()
    if args.self_test:return self_test()
    if not args.source_l3_confirmed:
        ap.error('--source-l3-confirmed is required; do not assume the input identifies L3')
    if not args.baseline or not args.subregions or not args.label_map:
        ap.error('--baseline, --subregions and --label-map are required')
    import nibabel as nib
    img=nib.load(str(args.subregions))
    arr=np.asarray(img.dataobj)
    if not np.issubdtype(arr.dtype,np.integer):
        raise ValueError('Input segmentation must be integer-labeled voxels')
    payload=json.loads(args.label_map.read_text(encoding='utf-8'))
    mapping=payload['labels']
    verify_map(mapping,arr)
    ref,tree,classes,meta=reference_data(arr,img.affine,mapping)
    baseline=trimesh.load(args.baseline,force='mesh',process=False)
    candidates={'candidate':trimesh.load(args.candidate,force='mesh',process=False)} if args.candidate else {}
    report=evaluate(baseline,ref,tree,classes,mapping,candidates,args.samples)
    report['reference_metadata']=meta
    report['source_id']=args.subregions.name
    report['mapping_source']=payload.get('mapping_source','UNSPECIFIED')
    report['labels']=mapping
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'output':str(args.out),'labelled_CT_compared':True,
                      'anatomical_approval':False},ensure_ascii=False))

if __name__=='__main__':main()
