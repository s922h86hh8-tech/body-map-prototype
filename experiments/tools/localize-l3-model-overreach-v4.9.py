#!/usr/bin/env python3
"""Find model-side surface mismatch locations without claiming anatomical labels.
All variants use the SAME baseline CT rigid pose from research v4.7.
Bins are just model X/Y/Z positions; no named CT subregion mapping.
"""
import argparse,importlib.util,json
from pathlib import Path
import numpy as np
import nibabel as nib
import trimesh
from scipy.spatial import cKDTree

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('v47',HERE/'compare-l3-bidirectional-holdout-v4.7.py')
v47=importlib.util.module_from_spec(spec);spec.loader.exec_module(v47)
def stats(d):
    if len(d)<75:return {'samples':len(d),'status':'too_few_surface_samples'}
    return {'samples':len(d),'p95_mm':round(float(np.quantile(d,.95)),3),
            'p50_mm':round(float(np.median(d)),3),
            'above_8mm_fraction':round(float(np.mean(d>8.0)),4)}
def run(models,image,n=12000):
    if n<4000:raise ValueError('Too few surface samples')
    prior=v47.compare(models['v24'],models['v33'],models['v35'],image,samples=5000)
    if 'pose' not in prior:raise ValueError('Could not find a pose within test prior')
    pose=prior['pose']
    r=np.asarray(pose['rotation_matrix']);t=np.asarray(pose['translation_mm'])
    source=np.asarray(image.dataobj)
    if not np.issubdtype(source.dtype,np.integer):
        if not np.array_equal(source,np.rint(source)):raise ValueError('noninteger class mask')
        source=source.astype(np.int16)
    reference,_,_,_,crop=v47.old.label_data(source,image.affine)
    ct_world=v47.old.core.samples(reference,n,701)
    ct_local=(ct_world-t)@r
    tree=cKDTree(ct_local)
    regions={'all':lambda p:np.ones(len(p),dtype=bool),
      'far_posterior_y_lt_minus30':lambda p:p[:,1]<-30,
      'posterior_y_lt_minus20':lambda p:p[:,1]<-20,
      'rear_mid_y_minus30_to_minus10':lambda p:(p[:,1]>=-30)&(p[:,1]<-10),
      'posterior_and_lower':lambda p:(p[:,1]<-15)&(p[:,2]<-8),
      'posterior_and_upper':lambda p:(p[:,1]<-15)&(p[:,2]>8),
      'inferior_z_lt_minus10':lambda p:p[:,2]<-10,
      'superior_z_gt10':lambda p:p[:,2]>10,
      'anterior_y_gt0':lambda p:p[:,1]>0,
      'lateral_abs_x_gt20':lambda p:np.abs(p[:,0])>20,
      'central_abs_x_le20':lambda p:np.abs(p[:,0])<=20}
    rows={}
    for name,mesh in models.items():
        points=v47.old.core.samples(mesh,n,811)
        distances=tree.query(points,workers=-1)[0]
        rows[name]={k:stats(distances[fn(points)]) for k,fn in regions.items()}
    changes={}
    for key in regions:
        a=rows['v24'][key];b=rows['v35'][key]
        if 'p95_mm' in a and 'p95_mm' in b:
            changes[key]=round(b['p95_mm']-a['p95_mm'],3)
    return {'status':'MODEL_SIDE_LOCALIZATION_RESEARCH_ONLY',
            'pose':{'selected':pose['selected_small_rotation_start'],
                    'rotation_deg':pose['selected_rotation_deg'],
                    'expert_approved':False},
            'crop_border_contact':crop['touches_original_crop_boundary'],
            'regions_are_model_space_not_CT_anatomy':True,
            'counts_and_p95_by_shape':rows,
            'v35_minus_v24_model_to_ct_p95_mm':changes,
            'source_numeric_to_anatomic_map_verified':False,
            'anatomy_approved':False}
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for k in ('mask','v24','v33','v35','out'):
        ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--samples',type=int,default=12000)
    a=ap.parse_args()
    models={k:trimesh.load(str(getattr(a,k)),force='mesh',process=False)
            for k in ('v24','v33','v35')}
    result=run(models,nib.load(str(a.mask)),a.samples)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'computed':True,'result':str(a.out),'anatomical_approval':False}))
if __name__=='__main__':main()
