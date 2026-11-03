#!/usr/bin/env python3
"""Source L3 numeric-class crop integrity census in ORIGINAL 3D NIfTI grid.

Compares each source integer class (1..7) with the SIX ORIGINAL input
cropping faces. Avoids reliance on interpolated/undersampled MPR slices.
This determines source truncation risk, NOT clinical/anatomical completeness.
Numeric IDs do not have verified anatomical names.
"""
import argparse,json,hashlib
from pathlib import Path
import nibabel as nib
import numpy as np
from scipy.ndimage import label as conn_label

FACES=('x_low','x_high','y_low','y_high','z_low','z_high')
def scan(mask_path):
    img=nib.load(str(mask_path))
    arr=np.asarray(img.dataobj)
    if arr.ndim!=3 or not np.isfinite(arr).all() or not np.array_equal(arr,np.rint(arr)):
        raise ValueError('Expect finite integer-valued 3D L3 mask')
    if np.min(arr)<0 or np.max(arr)>7:
        raise ValueError('Expected source numeric classes 0..7')
    arr=arr.astype(np.uint8)
    if not np.array_equal(np.unique(arr),np.arange(8)):
        raise ValueError('Exactly source numeric IDs 0..7 required')
    result=[]
    for class_id in range(1,8):
        region=arr==class_id
        count=int(region.sum())
        face_counts=dict(zip(FACES,[
            int(region[0,:,:].sum()),int(region[-1,:,:].sum()),
            int(region[:,0,:].sum()),int(region[:,-1,:].sum()),
            int(region[:,:,0].sum()),int(region[:,:,-1].sum())]))
        components,n=conn_label(region,structure=np.ones((3,3,3),dtype=np.uint8))
        binc=np.bincount(components.ravel(),minlength=n+1)
        binc[0]=0
        largest_id=int(np.argmax(binc))
        largest=components==largest_id
        largest_border={
          'x_low':bool(largest[0,:,:].any()),
          'x_high':bool(largest[-1,:,:].any()),
          'y_low':bool(largest[:,0,:].any()),
          'y_high':bool(largest[:,-1,:].any()),
          'z_low':bool(largest[:,:,0].any()),
          'z_high':bool(largest[:,:,-1].any())}
        result.append({
          'numeric_class':class_id,
          'voxel_count':count,
          'source_crop_face_voxel_counts':face_counts,
          'source_class_touches_any_original_crop_face':any(face_counts.values()),
          '26_connected_component_count':int(n),
          'largest_component_voxel_count':int(binc[largest_id]),
          'largest_component_touches_crop_face':any(largest_border.values()),
          'largest_component_crop_faces':[face for face,yes in largest_border.items() if yes],
          'class_anatomical_name_confirmed':False,
          'complete_3D_anatomy_verified':False})
    return {'source_sha256':hashlib.sha256(mask_path.read_bytes()).hexdigest(),
            'source_array_axis_codes':list(nib.aff2axcodes(img.affine)),
            'source_input_voxel_shape':list(arr.shape),
            'source_class_report':result,
            'flag_does_not_prove_real_anatomical_structure_truncation':True,
            'not_approved_for_teaching':True}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mask',type=Path,required=True)
    a=p.parse_args()
    r=scan(a.mask)
    print('L3_V63_CROP_CLASS_CENSUS '+json.dumps(r,ensure_ascii=False))
if __name__=='__main__':main()
