#!/usr/bin/env python3
"""L3 reference-to-model discrepancy localization using FIXED baseline registration.
This is research-only: model-coordinate spatial bins are NOT anatomical labels.
A candidate must be compared under the SAME baseline transform, not separately optimized.
Use with a locally held publicly licensed VerSe L3 segmentation; never commit CT data.
"""
import argparse
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
import trimesh

CORE=Path(__file__).with_name('compare-l3-reference-v3.2.py')
spec=importlib.util.spec_from_file_location('l3_core_v32', CORE)
core=importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

def pstats(values):
    if len(values)==0:
        return {'n':0}
    values=np.asarray(values,dtype=float)
    return {'n':int(len(values)),
            'p50_mm':round(float(np.median(values)),3),
            'p95_mm':round(float(np.quantile(values,.95)),3),
            'rms_mm':round(float(np.sqrt(np.mean(values**2))),3),
            'over_5mm_fraction':round(float(np.mean(values>5.)),4),
            'over_10mm_fraction':round(float(np.mean(values>10.)),4)}

def axes(points):
    return {axis:{'p01_mm':round(float(np.quantile(points[:,i],.01)),2),
                  'p99_mm':round(float(np.quantile(points[:,i],.99)),2),
                  'span_mm':round(float(np.quantile(points[:,i],.99)-np.quantile(points[:,i],.01)),2)}
            for i,axis in enumerate(('x','y','z'))}

def analyze(baseline,reference,candidate=None,n=6000,seed=19):
    if n<3000:
        raise ValueError('At least 3000 sampled points required')
    src=core.samples(baseline,n,seed)
    dst=core.samples(reference,n,29)
    # Use a constrained identity/RAS-axis initialization for audit regions;
    # NOT an approved manual correspondence of articular/anatomical landmarks.
    r,t=core.icp_fit(src,dst,np.eye(3),iterations=80)
    transform_angle=math.degrees(math.acos(float(np.clip((np.trace(r)-1)/2,-1,1))))
    ct_model_axes=(dst-t)@r
    base_dist=cKDTree(src).query(ct_model_axes,workers=-1)[0]
    candidate_points=core.samples(candidate,n,seed) if candidate is not None else None
    cand_dist=cKDTree(candidate_points).query(ct_model_axes,workers=-1)[0] if candidate is not None else None
    x,y,z=ct_model_axes.T
    areas={
       'entire_ct_surface':np.ones(n,dtype=bool),
       'anterior_y_gt_0':y>0,
       'mid_y_minus8_to_0':(y>=-8)&(y<=0),
       'posterior_y_lt_minus8':y<-8,
       'far_posterior_y_lt_minus20':y<-20,
       'upper_z_gt_8':z>8,
       'upper_z_gt_15':z>15,
       'middle_z_minus8_to_8':(z>=-8)&(z<=8),
       'lower_z_lt_minus8':z<-8,
       'lower_z_lt_minus15':z<-15,
       'posterior_and_upper':(y<-8)&(z>8),
       'posterior_and_middle':(y<-8)&(z>=-8)&(z<=8),
       'posterior_and_lower':(y<-8)&(z<-8),
       'anterior_and_upper':(y>0)&(z>8),
       'anterior_and_middle':(y>0)&(z>=-8)&(z<=8),
       'anterior_and_lower':(y>0)&(z<-8),
       'lateral_abs_x_gt22':np.abs(x)>22,
       'central_abs_x_le22':np.abs(x)<=22,
    }
    roi={}
    for name,mask in areas.items():
        if mask.sum()<40:
            continue
        a=pstats(base_dist[mask])
        b=pstats(cand_dist[mask]) if cand_dist is not None else None
        roi[name]={'baseline':a}
        if b is not None:
            roi[name]['candidate']=b
            roi[name]['difference_candidate_minus_baseline_p95_mm']=round(b['p95_mm']-a['p95_mm'],3)
            roi[name]['difference_candidate_minus_baseline_rms_mm']=round(b['rms_mm']-a['rms_mm'],3)
    result={'status':'CAUSAL_SCREENING_ONLY_NOT_ANATOMICAL_APPROVAL',
            'registration':{'basis':'one baseline RAS-axis-initialized ICP used for BOTH meshes',
                            'orientation_angle_degrees':round(transform_angle,2),
                            'orientation_over_30_degrees':bool(transform_angle>30),
                            'not_anatomically_verified':True,
                            'candidate_not_independently_reregistered':True},
            'reference_surface_in_model_coordinates_mm':axes(ct_model_axes),
            'baseline_surface_coordinates_mm':axes(src),
            'candidate_surface_coordinates_mm':axes(candidate_points) if candidate_points is not None else None,
            'spatial_bins_not_anatomical_regions':roi,
            'whole_reference_surface_p95_mm':roi['entire_ct_surface']['baseline']['p95_mm'],
            'limitations':['Nearest surface-point distances depend on sampling and registration',
                           'Model axis and CT alignment require anatomical expert confirmation',
                           'No segmented vertebral body/facet/lamina masks are used',
                           'A subset of two CT scans cannot determine population anatomy',
                           'Spatial-bin improvements may conceal worsened anatomy elsewhere',
                           'Never use these screening outputs for clinical or anatomical approval']}
    return result

def self_test():
    # A deliberately asymmetrical, disconnected synthetic shape tests fixed registration
    # and whether an added posterior protrusion improves reference-to-model coverage.
    a=trimesh.util.concatenate([
       trimesh.creation.box(extents=(70,35,24)),
       trimesh.creation.box(extents=(9,18,12),transform=trimesh.transformations.translation_matrix([0,-26,1]))])
    b=trimesh.util.concatenate([
       trimesh.creation.box(extents=(70,35,24)),
       trimesh.creation.box(extents=(9,26,12),transform=trimesh.transformations.translation_matrix([0,-30,1]))])
    report=analyze(a,b,candidate=b,n=3500)
    assert report['registration']['candidate_not_independently_reregistered']
    assert 'posterior_y_lt_minus8' in report['spatial_bins_not_anatomical_regions']
    assert not report['registration']['orientation_over_30_degrees']
    assert report['status']=='CAUSAL_SCREENING_ONLY_NOT_ANATOMICAL_APPROVAL'
    print(json.dumps({'self_test':'PASS','registration':report['registration'],
                      'posterior':report['spatial_bins_not_anatomical_regions']['posterior_y_lt_minus8'],
                      'anatomical_approval':False},ensure_ascii=False))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test',action='store_true')
    ap.add_argument('--baseline',type=Path)
    ap.add_argument('--candidate',type=Path)
    ap.add_argument('--seg',type=Path)
    ap.add_argument('--label',type=int,default=22)
    ap.add_argument('--out',type=Path,default=Path('private-l3-localization.json'))
    ap.add_argument('--samples',type=int,default=6000)
    args=ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.baseline or not args.seg:
        ap.error('--baseline and --seg are required')
    baseline=trimesh.load(args.baseline,force='mesh',process=False)
    candidate=trimesh.load(args.candidate,force='mesh',process=False) if args.candidate else None
    reference,metadata=core.load_vertebra_mask(args.seg,args.label)
    result=analyze(baseline,reference,candidate,args.samples)
    result['source']={'label':args.label,
                      'mask_voxels':metadata['label_voxels'],
                      'voxel_spacing_mm':metadata['voxel_spacing_mm'],
                      'reference_source_not_embedded':True}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'computed':True,'out':str(args.out),
                      'orientation_angle_degrees':result['registration']['orientation_angle_degrees'],
                      'anatomical_approval':False},ensure_ascii=False))

if __name__=='__main__':
    main()
