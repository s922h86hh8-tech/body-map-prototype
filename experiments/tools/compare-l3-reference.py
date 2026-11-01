#!/usr/bin/env python3
"""Compare our independently authored L3 OBJ with a locally held VerSe segmentation mask.
Install: python -m pip install numpy scipy scikit-image nibabel trimesh
Run: python experiments/tools/compare-l3-reference.py --self-test
     python experiments/tools/compare-l3-reference.py --model /tmp/l3-v24.obj --seg /LOCAL/...seg-vert_msk.nii.gz --out /tmp/l3-local-report.json
No patient data, CT mesh or screenshot is uploaded to this GitHub repository.
A numerical comparison does not establish medical or educational anatomy approval.
"""
import argparse, json, math
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

def compare(model,reference,n=14000,iterations=40):
    src=samples(model,n,19);dst=samples(reference,n,29)
    tree=cKDTree(dst);r=np.eye(3);t=dst.mean(0)-src.mean(0)
    for _ in range(iterations):
        moved=src@r.T+t
        dist,idx=tree.query(moved,workers=-1)
        keep=dist<=np.quantile(dist,.85)
        if keep.sum()<100:raise ValueError('Not enough correspondence points')
        dr,dt=rigid(moved[keep],dst[idx[keep]])
        r,t=dr@r,dr@t+dt
        if np.linalg.norm(dr-np.eye(3))<1e-6 and np.linalg.norm(dt)<1e-5:break
    moved=src@r.T+t
    d1=tree.query(moved,workers=-1)[0]
    d2=cKDTree(moved).query(dst,workers=-1)[0]
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
        regions[name]={'n':int(mask.sum()),
                       'proxy_only':True,'distance':stats(d1[mask]) if mask.sum()>=30 else None}
    angle=math.degrees(math.acos(float(np.clip((np.trace(r)-1)/2,-1,1))))
    return {'status':'COMPARISON_ONLY_NOT_ANATOMICAL_PASS',
            'bidirectional_surface_error':stats(np.r_[d1,d2]),
            'model_to_reference_error':stats(d1),
            'reference_to_model_error':stats(d2),
            'facet_candidate_regions':regions,
            'registration':{'method':'rigid point-to-point trimmed ICP; no scale adjustment',
                            'rotation_from_RAS_degrees':round(angle,2),
                            'matrix':r.round(6).tolist(),'translation_mm':t.round(4).tolist()},
            'limitations':['ICP may converge to wrong local alignment; inspect orientation',
                           'Per-subject anatomy varies; no single specimen represents pooled average',
                           'Segmentation quality is bounded by CT voxel resolution',
                           'Facet ROIs remain manually authored and not anatomically registered',
                           'No validated acceptance threshold and no automatic anatomy approval']}

def load_vertebra_mask(filename,label):
    import nibabel as nib
    from skimage.measure import marching_cubes
    img=nib.load(str(filename))
    mask=np.asarray(img.dataobj)==label
    n=int(np.count_nonzero(mask))
    if n<300:raise ValueError(f'L3 label {label} contains only {n} voxels')
    coords=np.array(np.where(mask))
    low=np.maximum(coords.min(1)-3,0);hi=np.minimum(coords.max(1)+4,mask.shape)
    crop=mask[tuple(slice(int(a),int(b)) for a,b in zip(low,hi))]
    verts,faces,_,_=marching_cubes(crop.astype(np.uint8),.5)
    verts=nib.affines.apply_affine(img.affine,verts+low)
    mesh=trimesh.Trimesh(vertices=verts,faces=faces,process=False)
    return mesh,{'label':label,'label_voxels':n,'filename':filename.name,
                 'voxel_spacing_mm':np.linalg.norm(img.affine[:3,:3],axis=0).round(3).tolist(),
                 'surface_vertices':len(mesh.vertices),'surface_triangles':len(mesh.faces)}

def self_test():
    a=trimesh.creation.icosphere(subdivisions=3,radius=14)
    b=a.copy()
    x=trimesh.transformations.rotation_matrix(np.deg2rad(7),[0,0,1])
    x[:3,3]=[4,7,-3];b.apply_transform(x)
    report=compare(a,b,n=7000)
    assert report['bidirectional_surface_error']['p95_mm']<1.6
    print(json.dumps({'self_test':'PASS','p95_mm':report['bidirectional_surface_error']['p95_mm'],
                      'anatomical_approval':False},indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--model',type=Path)
    p.add_argument('--seg',type=Path)
    p.add_argument('--label',type=int,default=22,help='VerSe standard L3 label (check dataset version)')
    p.add_argument('--out',type=Path,default=Path('l3-local-comparison.json'))
    p.add_argument('--samples',type=int,default=14000)
    a=p.parse_args()
    if a.self_test:return self_test()
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
