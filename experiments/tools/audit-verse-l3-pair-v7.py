#!/usr/bin/env python3
"""Research-only VerSe CT/vertebra mask pair integrity screen (NOT anatomy approval).

Inputs are original local NIfTI CT and label volumes from the SAME source case.
Never auto-download, publish, reorient, pad, repair, or export source medical images.
Run: python experiments/tools/audit-verse-l3-pair-v7.py --ct /private/ct.nii.gz --seg /private/seg.nii.gz --case-id local-code --out /private/report.json
Requires numpy, scipy, nibabel. Does NOT establish vertebral identity or clinical accuracy.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy import ndimage

SCHEMA='L3_VERSE_PAIR_INTEGRITY_V7_RESEARCH_ONLY'

def file_sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):
            h.update(chunk)
    return h.hexdigest()

def inspect_arrays(ct,seg,ct_affine,seg_affine,label_value=22):
    """Checks numerical geometry only. 'Uncropped' does NOT mean anatomically complete."""
    ct=np.asarray(ct); seg=np.asarray(seg)
    a=np.asarray(ct_affine,dtype=np.float64)
    b=np.asarray(seg_affine,dtype=np.float64)
    if ct.ndim!=3 or seg.ndim!=3 or ct.shape!=seg.shape:
        raise ValueError('CT and mask must be 3D and have exactly identical voxel shape')
    if a.shape!=(4,4) or b.shape!=(4,4) or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Invalid or missing affine')
    affine_delta=float(np.max(np.abs(a-b)))
    if affine_delta>1e-4:
        raise ValueError('CT and mask NIfTI affine mismatch; resampling not authorized')
    if abs(np.linalg.det(a[:3,:3]))<1e-9:
        raise ValueError('Noninvertible source world transform')
    if not np.issubdtype(seg.dtype,np.number) or not np.isfinite(seg).all() or not np.array_equal(seg,np.rint(seg)):
        raise ValueError('Mask labels must be finite integer-valued voxels')
    if not np.issubdtype(ct.dtype,np.number) or not np.isfinite(ct).all():
        raise ValueError('CT source values not finite; cannot evaluate pair as-is')
    if label_value!=22:
        raise ValueError('This protocol screens VerSe L3 label 22 only')
    target=seg==label_value
    voxel_count=int(np.count_nonzero(target))
    faces={
        'i_min':int(np.count_nonzero(target[0,:,:])),
        'i_max':int(np.count_nonzero(target[-1,:,:])),
        'j_min':int(np.count_nonzero(target[:,0,:])),
        'j_max':int(np.count_nonzero(target[:,-1,:])),
        'k_min':int(np.count_nonzero(target[:,:,0])),
        'k_max':int(np.count_nonzero(target[:,:,-1])),
    }
    touching=[name for name,count in faces.items() if count>0]
    if voxel_count:
        components,number=ndimage.label(target,structure=np.ones((3,3,3),dtype=np.uint8))
        sizes=np.bincount(components[target],minlength=number+1)[1:]
        coordinates=np.where(target)
        bbox=[[int(np.min(ax)),int(np.max(ax))] for ax in coordinates]
        vox_sizes=np.linalg.norm(a[:3,:3],axis=0)
        volume=float(voxel_count*abs(np.linalg.det(a[:3,:3])))
    else:
        number=0; sizes=np.array([],dtype=int);bbox=None
        vox_sizes=np.linalg.norm(a[:3,:3],axis=0)
        volume=0.
    source_geometry_screen=(voxel_count>0 and not touching and number==1)
    return {
        'schema':SCHEMA,
        'ct_mask_same_grid':True,
        'max_affine_element_difference':round(affine_delta,8),
        'volume_shape_ijk':list(map(int,ct.shape)),
        'voxel_spacing_axis_lengths_mm':[round(float(x),6) for x in vox_sizes],
        'reference_label':22,
        'label22_present':voxel_count>0,
        'label22_voxel_count':voxel_count,
        'label22_proxy_volume_mm3':round(volume,3),
        'label22_bbox_ijk':bbox,
        'label22_boundary_voxels_by_face':faces,
        'label22_touching_volume_faces':touching,
        'label22_connected_components_26':int(number),
        'largest_component_voxels':int(max(sizes,default=0)),
        'technical_geometry_screen_pass':bool(source_geometry_screen),
        'warning':'No boundary contact and one component do not prove complete bone, correct L3 identity, orientation, or segmentation accuracy.',
        'correct_l3_identity_expert_verified':False,
        'source_pair_provenance_expert_verified':False,
        'anatomical_landmarks_expert_verified':False,
        'anatomy_approved':False,
        'publish_or_adopt_model':False,
    }

def run(ct_path,seg_path,case_id,out_path):
    import nibabel as nib
    if not case_id or any(c in case_id for c in ('/','\\','\n')):
        raise ValueError('case-id must be a nonempty local identifier, not a path')
    ct_img=nib.load(str(ct_path));seg_img=nib.load(str(seg_path))
    result=inspect_arrays(np.asanyarray(ct_img.dataobj),np.asanyarray(seg_img.dataobj),ct_img.affine,seg_img.affine)
    result.update({
        'source_dataset_declared':'VerSe 2020 (caller-declared; unverified by checksum alone)',
        'case_id_local':case_id,
        'ct_sha256':file_sha256(ct_path),
        'seg_sha256':file_sha256(seg_path),
        'source_pair_identity_independently_verified':False,
        'license_of_exact_files_verified':False,
        'ct_intensity_is_HU_verified':False,
        'candidate_not_approval':True,
    })
    out_path.parent.mkdir(parents=True,exist_ok=True)
    out_path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('ct','seg','out'):
        p.add_argument('--'+arg,required=True,type=Path)
    p.add_argument('--case-id',required=True)
    x=p.parse_args()
    r=run(x.ct,x.seg,x.case_id,x.out)
    print('L3_VERSE_PAIR_SCREEN '+json.dumps({
        'geometry_screen_pass':r['technical_geometry_screen_pass'],
        'label22_voxels':r['label22_voxel_count'],
        'component_count':r['label22_connected_components_26'],
        'touching_faces':r['label22_touching_volume_faces'],
        'anatomy_approved':False},ensure_ascii=False))
if __name__=='__main__': main()
