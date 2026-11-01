#!/usr/bin/env python3
"""Compare our independently authored L3 OBJ with a locally held VerSe segmentation mask.
Install: python -m pip install numpy scipy scikit-image nibabel trimesh
Run: python experiments/tools/compare-l3-reference-v3.0.py --self-test
     python experiments/tools/compare-l3-reference-v3.0.py --model /tmp/l3-v24.obj --seg /LOCAL/...seg-vert_msk.nii.gz --out /tmp/l3-local-report.json
No patient data, CT mesh or screenshot is uploaded to this GitHub repository.
A numerical comparison does not establish medical or educational anatomy approval.
"""
import argparse, json, math, itertools
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import trimesh
MM_PER_UNIT=44.82/(2*8.10)

def samples(mesh,n,seed):
    pts,_=trimesh.sample.sample_surface(mesh,n,seed=seed)
    return np.asarray(pts,dtype=float)

def rigid(a,b):
    ac,bc=a.mean(0),b.mean(0)
    u,_,vt=np.linalg.svd((a-ac).T@(b-bc))
    q=np.linalg.det(vt.T@u.T)
    r=vt.T@np.diag([1,1,1 if q>0 else -1])@u.T
    return r,bc-r@ac

def all_right_handed_axis_orientations():
    """24 proper rotations. Axis mirroring is not permitted."""
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((-1.,1.), repeat=3):
            r=np.eye(3)[list(perm)]*np.array(signs)[:,None]
            if np.linalg.det(r)>0.5:
                yield r

def icp_fit(src,dst,initial_rotation,iterations=24,trim=.85):
    tree=cKDTree(dst)
    r=initial_rotation.copy()
    t=dst.mean(0)-src.mean(0)@r.T
    for _ in range(iterations):
        moved=src@r.T+t
        dist,idx=tree.query(moved,workers=-1)
        keep=dist<=np.quantile(dist,trim)
        if int(keep.sum())<100:
            raise ValueError('Not enough valid ICP correspondences')
        dr,dt=rigid(moved[keep],dst[idx[keep]])
        r,t=dr@r,dr@t+dt
        if np.linalg.norm(dr-np.eye(3))<1e-6 and np.linalg.norm(dt)<1e-5:
            break
    return r,t

def symmetric_error(src,dst,r,t):
    moved=src@r.T+t
    a=cKDTree(dst).query(moved,workers=-1)[0]
    b=cKDTree(moved).query(dst,workers=-1)[0]
    errors=np.r_[a,b]
    return float(np.sqrt(np.mean(errors*errors))),a,b

def compare(model,reference,n=14000,iterations=80):
    src=samples(model,n,19)
    dst=samples(reference,n,29)
    k=min(3500,n)
    coarse_src,coarse_dst=src[:k],dst[:k]
    candidates=[]
    for seed_number,initial in enumerate(all_right_handed_axis_orientations()):
        r,t=icp_fit(coarse_src,coarse_dst,initial,iterations=16)
        cost,_,_=symmetric_error(coarse_src,coarse_dst,r,t)
        candidates.append((cost,seed_number,r))
    candidates.sort(key=lambda a:a[0])
    refined=[]
    for _,seed_number,r0 in candidates[:4]:
        r,t=icp_fit(src,dst,r0,iterations=iterations)
        cost,d1,d2=symmetric_error(src,dst,r,t)
        refined.append((cost,seed_number,r,t,d1,d2))
    refined.sort(key=lambda a:a[0])
    cost,seed,r,t,d1,d2=refined[0]
    if not np.isfinite(cost):
        raise ValueError('Registration score is not finite')
    alternative=[]
    for alt_cost,alt_seed,alt_r,*_ in refined[1:]:
        relative=alt_r@r.T
        angle=math.degrees(math.acos(float(np.clip((np.trace(relative)-1)/2,-1,1))))
        alternative.append({'seed':alt_seed,'rms_mm':round(float(alt_cost),3),
                            'rotation_separation_degrees':round(angle,2)})
    possible_ambiguity=any(a['rms_mm']<=cost*1.03 and a['rotation_separation_degrees']>30
                           for a in alternative)

    def stats(d):
        return {'mean_mm':round(float(d.mean()),3),
                'p95_mm':round(float(np.quantile(d,.95)),3),
                'rms_mm':round(float(np.sqrt(np.mean(d*d))),3)}

    facet_centers={'upper_right':[3.82,-5.1,4.2],
                   'upper_left':[-3.82,-5.1,4.2],
                   'lower_right':[5.87,-4.73,-3.06],
                   'lower_left':[-5.87,-4.73,-3.06]}
    regions={}
    for name,c in facet_centers.items():
        mask=np.linalg.norm(src-np.array(c)*MM_PER_UNIT,axis=1)<1.6*MM_PER_UNIT
        regions[name]={'n':int(mask.sum()),'proxy_only':True,
                       'distance':stats(d1[mask]) if mask.sum()>=30 else None}
    angle=math.degrees(math.acos(float(np.clip((np.trace(r)-1)/2,-1,1))))
    return {'status':'COMPARISON_ONLY_NOT_ANATOMICAL_PASS',
            'bidirectional_surface_error':stats(np.r_[d1,d2]),
            'model_to_reference_error':stats(d1),
            'reference_to_model_error':stats(d2),
            'facet_candidate_regions':regions,
            'registration':{'method':'24 proper initial axis rotations, trimmed ICP; best 4 refined, symmetric score; no scaling',
                            'expert_verified':False,
                            'selected_seed':seed,'candidate_count':len(candidates),
                            'rms_mm':round(float(cost),3),
                            'possible_orientation_ambiguity':possible_ambiguity,
                            'alternative_candidates':alternative,
                            'rotation_from_model_axes_degrees':round(angle,2),
                            'matrix':r.round(6).tolist(),
                            'translation_mm':t.round(4).tolist()},
            'limitations':['Alignment with mesh surface samples is approximate; sampling error is not zero',
                           'Orientation/side registration needs visual expert verification',
                           'One CT subject may differ from pooled morphological averages',
                           'Segmentation quality and voxel resolution limit reference accuracy',
                           'Facet ROIs are model-authored proxies, not independently segmented CT facets',
                           'No validated anatomy acceptance threshold; NEVER auto-approve anatomy',
                           'v2.8 limited iterations caused failed rotated synthetic test; v2.9 increases refinement iterations']}

def load_vertebra_mask(filename,label):
    import nibabel as nib
    from skimage.measure import marching_cubes
    img=nib.load(str(filename))
    mask=np.asarray(img.dataobj)==label
    n=int(np.count_nonzero(mask))
    if n<300:raise ValueError(f'L3 label {label} contains only {n} voxels')
    coords=np.array(np.where(mask))
    # Truncated vertebra masks invalidate a full-surface comparison.
    for axis in range(3):
        if coords[axis].min()==0 or coords[axis].max()==mask.shape[axis]-1:
            raise ValueError('Reference L3 mask touches CT image boundary; choose a complete L3 case')
    low=np.maximum(coords.min(1)-3,0);hi=np.minimum(coords.max(1)+4,mask.shape)
    crop=mask[tuple(slice(int(a),int(b)) for a,b in zip(low,hi))]
    verts,faces,_,_=marching_cubes(crop.astype(np.uint8),.5)
    verts=nib.affines.apply_affine(img.affine,verts+low)
    mesh=trimesh.Trimesh(vertices=verts,faces=faces,process=False)
    return mesh,{'label':label,'label_voxels':n,'filename':filename.name,
                 'voxel_spacing_mm':np.linalg.norm(img.affine[:3,:3],axis=0).round(3).tolist(),
                 'surface_vertices':len(mesh.vertices),'surface_triangles':len(mesh.faces)}

def self_test():
    """Asymmetric synthetic vertebra-like object; tests 0/45/90/180 rotations."""
    box=trimesh.creation.box(extents=(84,42,26))
    rear=trimesh.creation.box(extents=(15,25,20))
    rear.apply_translation([0,-31,0])
    bump=trimesh.creation.icosphere(subdivisions=1,radius=11)
    bump.apply_translation([30,-18,14])
    a=trimesh.util.concatenate([box,rear,bump])
    records=[]
    for degree in (0,45,90,180):
        b=a.copy()
        tf=trimesh.transformations.rotation_matrix(np.deg2rad(degree),[0,0,1])
        tf[:3,3]=[100,45,-3]
        b.apply_transform(tf)
        report=compare(a,b,n=3500,iterations=80)
        p95=report['bidirectional_surface_error']['p95_mm']
        if not p95<3.6:
            raise AssertionError(f'Incorrect alignment {degree} degrees: p95={p95} mm')
        if report['status']!='COMPARISON_ONLY_NOT_ANATOMICAL_PASS':
            raise AssertionError('Unexpected anatomy approval')
        records.append({'rotation_degrees':degree,'p95_mm':p95})
    # A known geometric deformation must increase the error after successful registration.
    unmodified=compare(a,a.copy(),n=3500,iterations=80)
    altered=a.copy()
    altered.vertices[:,0]*=1.15
    changed=compare(a,altered,n=3500,iterations=80)
    unchanged_p95=unmodified['bidirectional_surface_error']['p95_mm']
    altered_p95=changed['bidirectional_surface_error']['p95_mm']
    if altered_p95 < unchanged_p95+2.0:
        raise AssertionError('Real geometry change was not sufficiently distinguishable')
    print(json.dumps({'self_test':'PASS','registration_checks':records,
                      'shape_change_detection':{'unmodified_p95_mm':unchanged_p95,
                                                'width_plus_15pct_p95_mm':altered_p95},
                      'anatomical_approval':False},indent=2))

def mask_affine_self_test():
    """Synthetic NIfTI voxel mask: verify L3 selection, affine transform, and truncation rejection."""
    import tempfile
    import nibabel as nib
    with tempfile.TemporaryDirectory() as temp_dir:
        folder=Path(temp_dir)
        vol=np.zeros((50,46,42),dtype=np.uint8)
        grid=np.indices(vol.shape,dtype=float)
        ellipsoid=((grid[0]-25)/9)**2+((grid[1]-22)/7)**2+((grid[2]-21)/5)**2
        vol[ellipsoid<1]=22
        vol[4:9,4:9,4:9]=21
        affine=np.array([[0.,0.,-0.8,80.],
                         [0.,1.25,0.,-40.],
                         [1.1,0.,0.,25.],
                         [0.,0.,0.,1.]])
        filename=folder/'synthetic_l3_seg.nii.gz'
        nib.save(nib.Nifti1Image(vol,affine),str(filename))
        mesh,meta=load_vertebra_mask(filename,22)
        physical_center=np.mean(mesh.vertices,axis=0)
        expected_center=nib.affines.apply_affine(affine,[25,22,21])
        if np.linalg.norm(physical_center-expected_center)>1.0:
            raise AssertionError(f'Affine ignored or incorrectly applied: {physical_center} vs {expected_center}')
        if meta['label_voxels']!=int(np.count_nonzero(vol==22)):
            raise AssertionError('Incorrect label-specific voxel count')
        if not np.allclose(sorted(meta['voxel_spacing_mm']),[.8,1.1,1.25]):
            raise AssertionError('Incorrect voxel spacing')
        if not len(mesh.faces)>100:
            raise AssertionError('3D surface extraction failed')
        truncated=vol.copy()
        truncated[:3,:3,:3]=22
        bad=folder/'synthetic_truncated_l3_seg.nii.gz'
        nib.save(nib.Nifti1Image(truncated,affine),str(bad))
        boundary_rejected=False
        try:
            load_vertebra_mask(bad,22)
        except ValueError as exc:
            boundary_rejected='boundary' in str(exc)
        if not boundary_rejected:
            raise AssertionError('Truncated L3 mask was not rejected')
        print(json.dumps({'mask_self_test':'PASS',
                          'volumetric_label':'L3 label 22',
                          'voxel_spacing_mm':meta['voxel_spacing_mm'],
                          'world_centroid_mm':physical_center.round(3).tolist(),
                          'reference_mesh_faces':len(mesh.faces),
                          'truncated_mask_rejected':True,
                          'actual_CT_used':False,
                          'anatomical_approval':False},indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--self-test-mask',action='store_true',help='Use synthetic NIfTI to test label/affine/truncation')
    p.add_argument('--model',type=Path)
    p.add_argument('--seg',type=Path)
    p.add_argument('--label',type=int,default=22,help='VerSe standard L3 label (check dataset version)')
    p.add_argument('--out',type=Path,default=Path('l3-local-comparison.json'))
    p.add_argument('--samples',type=int,default=14000)
    a=p.parse_args()
    if a.self_test:return self_test()
    if a.self_test_mask:return mask_affine_self_test()
    if not a.model or not a.seg:p.error('--model and --seg required')
    if a.samples<3000 or a.samples>100000:p.error('--samples must be 3000..100000')
    model=trimesh.load(a.model,force='mesh',process=False)
    if model.is_empty or len(model.faces)<100:raise ValueError('Model OBJ invalid')
    reference,meta=load_vertebra_mask(a.seg,a.label)
    report=compare(model,reference,n=a.samples)
    report['reference']=meta
    report['model']={'filename':a.model.name,'source':'project-authored L3 v2.4'}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'result_file':str(a.out),'p95_mm':report['bidirectional_surface_error']['p95_mm'],
                      'anatomical_approval':False},indent=2))
if __name__=='__main__':main()
