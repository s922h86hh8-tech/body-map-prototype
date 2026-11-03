#!/usr/bin/env python3
"""Construct 7 deliberately NON-ANATOMICAL test axes through source numeric classes.
This is a diagnostic control for 'why 0 accepted planes with whole-bone center'.
Generated landmarks must never be interpreted as actual pedicle axes.
"""
import argparse,hashlib,json
from pathlib import Path
import nibabel as nib
import numpy as np

def make(mask_file,ct_file,directory):
    ci=nib.load(str(ct_file));mi=nib.load(str(mask_file))
    if mi.shape!=ci.shape or np.max(np.abs(mi.affine-ci.affine))>1e-4:
        raise ValueError('CT and segmentation must share the exact affine')
    classes=np.asanyarray(mi.dataobj)
    if not np.array_equal(classes,np.rint(classes)):raise ValueError('Invalid class mask')
    classes=classes.astype(np.int16)
    if not np.array_equal(np.unique(classes),np.arange(8)):
        raise ValueError('Expected 0 and 7 numeric classes')
    directory.mkdir(parents=True,exist_ok=True)
    table=[]
    for numeric_class in range(1,8):
        coords=np.argwhere(classes==numeric_class)
        if len(coords)<300:raise ValueError('One numeric class unexpectedly sparse')
        mean=coords.mean(axis=0)
        center=coords[np.argmin(((coords-mean)**2).sum(axis=1))].copy()
        # Select an image axis with room for +/-6 voxels, NOT an anatomical direction.
        room=np.minimum(center,np.array(mi.shape)-1-center)
        viable=np.where(room>=7)[0]
        if len(viable)==0:
            raise ValueError('No +/-6-voxel test axis fits within original CT grid')
        direction=int(viable[np.argmax(room[viable])])
        delta=np.zeros(3,dtype=int);delta[direction]=6
        start=(center-delta).tolist();end=(center+delta).tolist()
        kinds=('pedicle_axis_right_body','pedicle_axis_right_posterior')
        entries=[{
            'kind':kind,
            'voxel_ijk':voxel,
            'world_ras_mm':nib.affines.apply_affine(ci.affine,voxel).tolist(),
            'reviewer_confirmation':'unverified_candidate',
            'authority':'unreviewed_manual_click'}
            for kind,voxel in zip(kinds,[start,end])]
        record={
          'schema':'L3_LOCAL_LANDMARK_REVIEW_V1',
          'source_CT_sha256':hashlib.sha256(ct_file.read_bytes()).hexdigest(),
          'source_mask_sha256':hashlib.sha256(mask_file.read_bytes()).hexdigest(),
          'ready_for_anatomical_approval':False,
          'synthetic_technical_demo_not_anatomy':True,
          'fictitious_axis_purpose':'numeric class centroid nearest occupied voxel, tests software ONLY',
          'source_numeric_class_without_anatomical_name':numeric_class,
          'items':entries}
        (directory/f'demo-numeric-{numeric_class}.json').write_text(json.dumps(record),encoding='utf8')
        table.append({'class_id':numeric_class,'voxel_count':len(coords),
          'axis_dimension_image_only':direction,
          'landmark_source_occupied_voxel':True,
          'anatomical_pedicle_axis':False})
    return {'status':'SEVEN_FICTIONAL_SOURCE_NUMERIC_CLASS_AXES_CREATED',
            'classes':table,'anatomical_approval':False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mask',type=Path,required=True)
    p.add_argument('--ct',type=Path,required=True)
    p.add_argument('--out-dir',type=Path,required=True)
    a=p.parse_args()
    print('L3_V61_AXIS_DEMOS '+json.dumps(make(a.mask,a.ct,a.out_dir),ensure_ascii=False))
if __name__=='__main__':main()
