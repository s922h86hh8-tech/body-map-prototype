#!/usr/bin/env python3
"""Four proper 180-degree basis hypotheses for LumASe L3 mask orientation.
Orientation is neither inferred from numeric label IDs nor validated clinically.
All candidate shapes evaluated under each fixed v2.4 registration hypothesis.
No shapes, CT, or patient data are committed.
"""
import argparse,importlib.util,json,math
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
import nibabel as nib
import trimesh

TOOL=Path(__file__).with_name('compare-l3-numeric-subregions-v4.0.py')
sp=importlib.util.spec_from_file_location('l3_numeric_v40',TOOL)
m=importlib.util.module_from_spec(sp)
sp.loader.exec_module(m)
core=m.core

ROTATIONS={
 'nominal_RAS_identity':np.eye(3),
 'yaw_180_about_Z':np.diag([-1.,-1.,1.]),
 'roll_180_about_X':np.diag([1.,-1.,-1.]),
 'pitch_180_about_Y':np.diag([-1.,1.,-1.])}

def analyze(baseline,trial,mask,affine,n=7000):
    ref,tree,classes,labels,crop=m.label_data(mask,affine)
    source=core.samples(baseline,n,19)
    ct=core.samples(ref,n,29)
    sample_trial=core.samples(trial,n,19)
    ct_class_indices=classes[tree.query(ct,workers=-1)[1]]
    output={}
    for name,initial in ROTATIONS.items():
        r,t=core.icp_fit(source,ct,initial,iterations=80)
        cost,model_ct,ct_model=core.symmetric_error(source,ct,r,t)
        ct_local=(ct-t)@r
        trial_ct_distance=cKDTree(sample_trial).query(ct_local,workers=-1)[0]
        base_ct_distance=cKDTree(source).query(ct_local,workers=-1)[0]
        class5=ct_local[ct_class_indices==5]
        if len(class5)<60:raise ValueError('No sufficient label 5 on CT exterior')
        output[name]={
          'initial_rotation_det':round(float(np.linalg.det(initial)),5),
          'final_rotation_from_identity_degrees':round(math.degrees(math.acos(float(np.clip((np.trace(r)-1)/2,-1,1)))),2),
          'symmetric_rms_mm':round(float(cost),3),
          'symmetric_p95_mm':round(float(np.quantile(np.r_[model_ct,ct_model],.95)),3),
          'base_ct_to_model_p95_mm':round(float(np.quantile(base_ct_distance,.95)),3),
          'trial_ct_to_model_p95_mm':round(float(np.quantile(trial_ct_distance,.95)),3),
          'trial_minus_baseline_p95_mm':round(float(np.quantile(trial_ct_distance,.95)-np.quantile(base_ct_distance,.95)),3),
          'numeric_class5_spatial_center_xyz_mm':np.mean(class5,axis=0).round(3).tolist(),
          'numeric_class5_centroid_is_negative_y':bool(np.mean(class5[:,1])<0),
          'not_anatomically_verified':True}
    ordered=sorted(output,key=lambda k:output[k]['symmetric_rms_mm'])
    return {'label_ids_not_anatomy_names':labels,
        'crop_boundary_contact':crop['touches_original_crop_boundary'],
        'excluded_border_fraction':crop['fraction_of_reference_triangles_excluded'],
        'hypotheses':output,'lowest_rms_hypothesis_only_not_anatomy_validation':ordered[0],
        'anatomical_approval':False,
        'warning':'Rigid ICP local minima and any local crop orientation ambiguity require independent anatomist validation; a lower surface RMS alone does NOT guarantee correct L3 orientation.'}

def main():
    a=argparse.ArgumentParser(description=__doc__)
    for key in ('mask','baseline','trial','out'):a.add_argument('--'+key,type=Path,required=True)
    a.add_argument('--samples',type=int,default=7000)
    args=a.parse_args()
    image=nib.load(str(args.mask))
    mask=np.asarray(image.dataobj)
    if np.issubdtype(mask.dtype,np.floating):
        if not np.array_equal(mask,np.round(mask)):raise ValueError('Mask not integer valued')
        mask=mask.astype(np.int16)
    base=trimesh.load(args.baseline,force='mesh',process=False)
    trial=trimesh.load(args.trial,force='mesh',process=False)
    report=analyze(base,trial,mask,image.affine,args.samples)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('L3_ORIENTATION_HYPOTHESIS '+json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
