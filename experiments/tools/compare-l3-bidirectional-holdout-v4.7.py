#!/usr/bin/env python3
"""Research-only L3 pose screen using CT world (RAS) axes, NOT a medical registration.
Source NIfTI array-axis codes (e.g. RAS vs LPS) are NOT an anatomical correction
after applying the affine: both become physical world RAS coordinates. A 180deg
surface-only fit can reverse anatomy and must never become the approved pose.
We test small initial tilts, reject final poses exceeding an authored-axis tolerance,
and separately report unrestricted flipped-pose scores as diagnostic warnings.
No named CT subregion mapping; no facet congruence, independent experts or approval.
"""
import argparse, hashlib, importlib.util, json, math
from pathlib import Path
import numpy as np
import nibabel as nib
import trimesh
from scipy.spatial import cKDTree

BASE=Path(__file__).with_name('compare-l3-numeric-subregions-v4.5.py')
spec=importlib.util.spec_from_file_location('numeric_v45',BASE)
old=importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)

def axis_angle(r):
    return float(np.degrees(np.arccos(np.clip((np.trace(r)-1)/2,-1,1))))

def spin(axis,degrees):
    a=np.zeros(3);a[axis]=1
    theta=np.radians(degrees)
    x,y,z=a; c=np.cos(theta);s=np.sin(theta);k=1-c
    return np.array([[c+x*x*k,x*y*k-z*s,x*z*k+y*s],
                     [y*x*k+z*s,c+y*y*k,y*z*k-x*s],
                     [z*x*k-y*s,z*y*k+x*s,c+z*z*k]])

def check_affine(image):
    m=image.affine
    if abs(np.linalg.det(m[:3,:3]))<1e-9 or not np.isfinite(m).all():
        raise ValueError('Invalid NIfTI world affine')
    axes=nib.orientations.aff2axcodes(m)
    if set(axes[:2]) not in ({'R','A'},{'L','P'}):
        # This is a controlled research assay and not a general converter.
        raise ValueError('Unexpected NIfTI axes: manual conversion needed')
    if axes[2]!='S':
        raise ValueError('Unsupported Z axis; do not guess')
    return {'voxel_array_axis_codes':list(axes),
            'world_coordinates_after_affine':'RAS (right/anterior/superior)',
            'model_axes':'+X right, +Y anterior, +Z superior',
            'qform_code':int(image.header['qform_code']),
            'sform_code':int(image.header['sform_code']),
            'world_affine_is_independently_anatomical_verified':False}

def compare(v24,v33,v35,image,samples=5000,angle_limit=35):
    if samples<3500 or samples>25000:raise ValueError('sample count out of range')
    if not (10 <= angle_limit <= 45):raise ValueError('unreviewed angle limit')
    header=check_affine(image)
    label=np.asarray(image.dataobj)
    if not np.array_equal(label,np.rint(label)):raise ValueError('noninteger segmentation')
    label=label.astype(np.int16)
    ref,tree,classes,labels,crop=old.label_data(label,image.affine)
    # Mesh vertices are authored RAS-compatible local coordinates, scaled in mm.
    src=old.core.samples(v24,samples,19)
    dst=old.core.samples(ref,samples,29)
    starts=[('identity',np.eye(3))]+[(f'{name}{degrees:+d}',spin(axis,degrees))
            for axis,name in enumerate('XYZ') for degrees in (-20,20)]
    acceptable=[]
    raw=[]
    for name,rotation in starts:
        r,t=old.core.icp_fit(src,dst,rotation,iterations=55)
        error,_,_=old.core.symmetric_error(src,dst,r,t)
        angle=axis_angle(r)
        raw.append({'start':name,'rms_mm':round(float(error),3),
                    'final_rotation_degrees':round(angle,2),
                    'within_anatomical_prior':bool(angle<=angle_limit)})
        if angle<=angle_limit:
            acceptable.append((error,name,r,t))
    if not acceptable:
        return {'status':'REJECTED_NO_AXIS_CONSISTENT_REGISTRATION',
                'pose_candidates':raw,'expert_verified':False,'anatomy_approved':False,
                'header':header,'crop':crop}
    acceptable.sort(key=lambda x:x[0])
    score,choice,r,t=acceptable[0]
    # Independent 180deg hypothesis as a *negative control only*.
    flips={}
    for name,init in [('yaw_180',np.diag([-1.,-1.,1.])),
                      ('pitch_180',np.diag([-1.,1.,-1.])),
                      ('roll_180',np.diag([1.,-1.,-1.]))]:
        hr,ht=old.core.icp_fit(src,dst,init,iterations=55)
        hscore,_,_=old.core.symmetric_error(src,dst,hr,ht)
        flips[name]={'rms_mm':round(float(hscore),3),
                     'final_rotation_deg':round(axis_angle(hr),2),
                     'excluded_from_anatomical_pose_selection':True}
    ct_local=(dst-t)@r
    nearest_voxel,idx=tree.query(dst,workers=-1)
    kinds=classes[idx]
    metrics={}
    for name,m in [('v24',v24),('v33',v33),('v35',v35)]:
        sample=old.core.samples(m,samples,19)
        ref_to_model=cKDTree(sample).query(ct_local,workers=-1)[0]
        model_to_ref=cKDTree(dst).query(sample@r.T+t,workers=-1)[0]
        metrics[name]={
            'all':old.stats(ref_to_model),  # legacy v4.6 label
            'ct_to_model':old.stats(ref_to_model),
            'model_to_ct':old.stats(model_to_ref),
            'bidirectional':old.stats(np.r_[ref_to_model,model_to_ref]),
            'numeric_only':{str(k):old.stats(ref_to_model[kinds==k]) for k in labels}}
    warning=[key for key,val in flips.items() if val['rms_mm']<=float(score)*1.05]
    # These are heuristic screening criteria, NOT anatomy quality thresholds.
    # Any large one-sided worsening needs independent review.
    prior=None
    baseline=metrics['v24']
    trials={}
    for key in ('v33','v35'):
        target=metrics[key]
        delta={way:round(target[way]['p95_mm']-baseline[way]['p95_mm'],3)
               for way in ('ct_to_model','model_to_ct','bidirectional')}
        trials[key]={'delta_p95_mm':delta,
                     'ct_to_model_improved':delta['ct_to_model']<-.25,
                     'model_to_ct_regressed_over_1mm':delta['model_to_ct']>1.,
                     'flip_hypothesis_close_or_better':bool(warning),
                     'anatomy_approved':False}
    return {'status':'AXIS_PRIOR_BIDIRECTIONAL_RESEARCH_ONLY_NOT_APPROVED',
            'candidate_changes_from_v24':trials,
            'header':header,'crop':crop,
            'pose':{'selected_small_rotation_start':choice,
                    'selected_rotation_deg':round(axis_angle(r),2),
                    'selected_rms_mm':round(float(score),3),
                    'angle_limit_deg':angle_limit,
                    'evaluated_small_tilt_candidates':raw,
                    'flipped_pose_negative_controls':flips,
                    'flipped_pose_within_5pct_of_selected':warning,
                    'world_axis_prior_assumed_not_expert_verified':True,
                    'rotation_matrix':r.round(6).tolist(),
                    'translation_mm':t.round(5).tolist(),
                    'independently_validated_anatomic_landmarks':False},
            'class_ids_not_anatomical_names':labels,
            'exterior_point_to_voxel_p95_mm':round(float(np.quantile(nearest_voxel,.95)),3),
            'metrics':metrics,
            'uncertainty':['Even limited rotation may be anatomically incorrect',
                           'NIfTI qform/sform may not reflect true anatomy; needs expert review',
                           'Neither mask numeric IDs nor model regions have source-verified names',
                           'CT scan cropped; artificial boundary cap triangles excluded',
                           'A 180-degree score improvement cannot override anatomy-direction prior',
                           'No quantitative cutoffs validated for educational approval',
                           'Bidirectional distances are nearest sampled surface points, NOT anatomical correspondence'],
            'anatomy_approved':False}

def self_test():
    assert check_affine(nib.Nifti1Image(np.zeros((10,10,10)),np.diag([1.,1.,1.,1.])))['world_coordinates_after_affine'].startswith('RAS')
    assert check_affine(nib.Nifti1Image(np.zeros((10,10,10)),np.diag([-1.,-1.,1.,1.])))['world_coordinates_after_affine'].startswith('RAS')
    assert axis_angle(np.eye(3))<1e-5
    assert abs(axis_angle(spin(2,180))-180)<1e-5
    assert abs(axis_angle(spin(2,25))-25)<1e-5
    print(json.dumps({'self_test':'PASS','tested':'RAS/LPS array orientation and proper rotation guard',
                      'independent_anatomic_validation':False,'anatomy_approved':False}))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--mask',type=Path)
    parser.add_argument('--v24',type=Path)
    parser.add_argument('--v33',type=Path)
    parser.add_argument('--v35',type=Path)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--samples',type=int,default=5000)
    args=parser.parse_args()
    if args.self_test:return self_test()
    if not all((args.mask,args.v24,args.v33,args.v35,args.out)):
        parser.error('All mask/model/out paths are required')
    m={k:trimesh.load(str(f),force='mesh',process=False)
       for k,f in [('v24',args.v24),('v33',args.v33),('v35',args.v35)]}
    result=compare(m['v24'],m['v33'],m['v35'],nib.load(str(args.mask)),args.samples)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':result['status'],
                      'selected_pose':result.get('pose',{}).get('selected_small_rotation_start'),
                      'anatomy_approved':False}))
if __name__=='__main__':main()
