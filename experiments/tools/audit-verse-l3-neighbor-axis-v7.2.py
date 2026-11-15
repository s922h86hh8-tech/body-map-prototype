#!/usr/bin/env python3
"""VerSe L3 numeric-label neighbor / RAS world-axis technical audit, NOT an anatomy approval.

Input: one locally held, matching CT and vertebra-label NIfTI pair.  Reports
only neighbor relative positions, labels and axis metadata.  Neither a NIfTI
affine nor mask-label order independently verifies anterior/posterior anatomy.
No CT images, mask arrays or absolute world centroids are emitted to stdout.
Generated local JSON must not be published without a separate privacy review.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

SCHEMA='L3_VERSE_NEIGHBOR_AXIS_V7_2_RESEARCH_ONLY'
LABELS={20:'L1',21:'L2',22:'L3',23:'L4',24:'L5',25:'L6'}

def audit_neighbor_geometry(mask,affine):
    arr=np.asarray(mask)
    mat=np.asarray(affine,dtype=float)
    if arr.ndim!=3 or mat.shape!=(4,4) or not np.isfinite(mat).all():
        raise ValueError('Expected 3D labels and finite 4x4 affine')
    if abs(np.linalg.det(mat[:3,:3]))<1e-10:
        raise ValueError('Singular voxel-to-RAS affine')
    if not np.issubdtype(arr.dtype,np.number) or not np.isfinite(arr).all() or not np.array_equal(arr,np.rint(arr)):
        raise ValueError('Labels are not finite integers')
    # Sums and centroids need not allocate a patient-point cloud or 3D visualization.
    records={}
    for label in LABELS:
        coords=np.nonzero(arr==label)
        n=int(coords[0].size)
        if n:
            ijk=np.array([float(v.mean()) for v in coords],dtype=float)
            world=mat[:3,:3]@ijk+mat[:3,3]
            records[label]={'count':n,'world':world}
    if 22 not in records:
        raise ValueError('No VerSe L3 numeric label 22')
    reference=records[22]['world']
    # Only relative positions/physical spans are emitted; no absolute world
    # coordinates are serialized to the report.
    relative={}
    for label,record in records.items():
        d=record['world']-reference
        relative[str(label)]={
            'source_label_name':LABELS[label],
            'source_label_voxels':record['count'],
            'offset_from_22_RAS_mm':[round(float(x),3) for x in d],
            'euclidean_centroid_distance_mm':round(float(np.linalg.norm(d)),3)
        }
    status={}
    if 21 in records:
        status['L2_number_above_L3_in_RAS_S']=bool(records[21]['world'][2]>reference[2])
    else:
        status['L2_number_above_L3_in_RAS_S']=None
    if 23 in records:
        status['L4_number_below_L3_in_RAS_S']=bool(records[23]['world'][2]<reference[2])
    else:
        status['L4_number_below_L3_in_RAS_S']=None
    present_both=(21 in records and 23 in records)
    expected_order=(present_both and status['L2_number_above_L3_in_RAS_S'] and status['L4_number_below_L3_in_RAS_S'])
    spacing=np.linalg.norm(mat[:3,:3],axis=0)
    return {
        'schema':SCHEMA,
        'present_labels':sorted(records),
        'reference_label':22,
        'label_offsets_from_L3_RAS_mm':relative,
        'neighbor_z_order_checks':status,
        'neighbor_labels_21_and_23_both_present':present_both,
        'neighbor_z_order_expected_in_affine_RAS':bool(expected_order),
        'source_affine_axis_lengths_mm':[round(float(s),4) for s in spacing],
        'source_RAS_world_convention_assumed_from_NIfTI_affine':True,
        'anterior_posterior_independent_landmarks_verified':False,
        'actual_anatomical_level_independently_verified':False,
        'numerical_order_confirms_anatomy':False,
        'expert_anatomy_approved':False,
        'publish_or_adopt_model':False,
        'warning':'Mask labels and NIfTI RAS affine cannot independently prove anatomical level, front/back or completeness.'
    }

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as fp:
        for chunk in iter(lambda:fp.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

def run(ct_path,seg_path,case_id,out_path):
    import nibabel as nib
    ct=nib.load(str(ct_path));seg=nib.load(str(seg_path))
    if len(ct.shape)!=3 or ct.shape!=seg.shape or not np.allclose(ct.affine,seg.affine,rtol=0,atol=1e-4):
        raise ValueError('CT and segmentation geometry mismatch; no resampling allowed')
    result=audit_neighbor_geometry(np.asanyarray(seg.dataobj),seg.affine)
    result.update({'case_id_local':case_id,'source_ct_sha256':sha256(ct_path),
                   'source_seg_sha256':sha256(seg_path),
                   'source_pair_identity_independently_verified':False,
                   'ct_mask_geometry_equal':True})
    out_path.parent.mkdir(parents=True,exist_ok=True)
    out_path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print('L3_VERSE_NEIGHBOR_AXIS '+json.dumps({
        'case':case_id,
        'labels':result['present_labels'],
        'neighbors_both_present':result['neighbor_labels_21_and_23_both_present'],
        'z_order_expected':result['neighbor_z_order_expected_in_affine_RAS'],
        'z_offsets_mm':{key:value['offset_from_22_RAS_mm'][2]
                       for key,value in result['label_offsets_from_L3_RAS_mm'].items()
                       if key in ('21','23')},
        'front_back_expert_verified':False,
        'anatomy_approved':False},ensure_ascii=False))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ct',type=Path,required=True)
    p.add_argument('--seg',type=Path,required=True)
    p.add_argument('--case-id',required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    run(a.ct,a.seg,a.case_id,a.out)

if __name__=='__main__':
    main()
