#!/usr/bin/env python3
"""L3 repeat-sampling robustness check with pose locked to v4.7 baseline.

No new anatomical labels, no assumption of correct anatomical orientation.
Compute pose ONCE from authored v2.4 and source CT, then resample surface
point clouds with different deterministic seeds. Report variability of signed
v3.5-v2.4 distance changes, WITHOUT medical acceptance threshold.
"""
import argparse,importlib.util,json
from pathlib import Path
import numpy as np
import nibabel as nib
import trimesh
from scipy.spatial import cKDTree

HERE=Path(__file__).parent
name='compare-l3-bidirectional-holdout-v4.7.py'
spec=importlib.util.spec_from_file_location('v47',HERE/name)
v47=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v47)

def scalar(d):
    return float(np.quantile(d,.95))

def summarize(values):
    return {'median_mm':round(float(np.median(values)),3),
            'minimum_mm':round(float(np.min(values)),3),
            'maximum_mm':round(float(np.max(values)),3),
            'all_trials_improved':bool(np.all(np.array(values)<0)),
            'repeats':len(values)}

def evaluate(baseline,candidate,mask,n=5000,repeats=5):
    if repeats<3 or repeats>12:raise ValueError('repeats out of range')
    if n<3500:raise ValueError('points too few')
    base=v47.compare(baseline,baseline,candidate,mask,n)
    if 'pose' not in base:
        return {'status':'REJECTED_POSE_NOT_ESTABLISHED', 'anatomy_approved':False}
    pose=base['pose']
    r=np.asarray(pose['rotation_matrix'],dtype=float)
    t=np.asarray(pose['translation_mm'],dtype=float)
    source=np.asarray(mask.dataobj)
    if not np.issubdtype(source.dtype,np.integer):
        if not np.array_equal(source,np.round(source)):raise ValueError('Invalid mask labels')
        source=source.astype(np.int16)
    reference,_,_,_,crop=v47.old.label_data(source,mask.affine)
    data={direction:[] for direction in ('ct_to_model','model_to_ct','bidirectional')}
    for j in range(repeats):
        seed=101+13*j
        ct=v47.old.core.samples(reference,n,seed)
        ct_local=(ct-t)@r
        a=v47.old.core.samples(baseline,n,seed+1000)
        b=v47.old.core.samples(candidate,n,seed+1000)
        def distances(model):
            c2m=cKDTree(model).query(ct_local,workers=-1)[0]
            m2c=cKDTree(ct_local).query(model,workers=-1)[0]
            return {'ct_to_model':scalar(c2m),
                    'model_to_ct':scalar(m2c),
                    'bidirectional':scalar(np.r_[c2m,m2c])}
        old=distances(a);new=distances(b)
        for k in data:
            data[k].append(round(new[k]-old[k],3))
    return {'status':'SAMPLE_REPRODUCIBILITY_ONLY_NOT_ANATOMY_APPROVAL',
            'repeats':repeats,'points_per_surface_per_repeat':n,
            'sampling_seed_scheme':'101+13*j for reference; +1000 for both models',
            'initial_registration':{'small_angle_pose_start':pose['selected_small_rotation_start'],
                                    'selected_rotation_deg':pose['selected_rotation_deg'],
                                    'anatomy_expert_verified':False},
            'crop_boundary_contact':crop['touches_original_crop_boundary'],
            'delta_p95_v35_minus_v24_mm':{k:{'values_mm':v,**summarize(v)} for k,v in data.items()},
            'limitation':'Nearest sampled surface points at fixed UNVALIDATED pose; not original CT anatomical correspondence.',
            'anatomy_approved':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('mask','v24','v35','out'):
        p.add_argument('--'+key,required=True,type=Path)
    p.add_argument('--points',type=int,default=5000)
    p.add_argument('--repeats',type=int,default=5)
    a=p.parse_args()
    b=trimesh.load(str(a.v24),force='mesh',process=False)
    c=trimesh.load(str(a.v35),force='mesh',process=False)
    report=evaluate(b,c,nib.load(str(a.mask)),a.points,a.repeats)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],
                      'repeats':report.get('repeats'),
                      'anatomy_approved':False},ensure_ascii=False))
if __name__=='__main__':main()
