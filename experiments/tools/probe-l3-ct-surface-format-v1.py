#!/usr/bin/env python3
"""Research method B: source-L3 segmentation -> RAS/mm surface -> glTF/GLB round-trip.

Uses only licensed, checksum-verified public LumASe _L3_seg.nii.gz, no CT
image or participant data committed. No zero padding, no artificial closure:
source crop edge may remain open. No 1..7 label-to-anatomy mapping is inferred.
Passing source conversion tests does NOT confer scientific/anatomy approval.
"""
import argparse,hashlib,io,json
from pathlib import Path
import nibabel as nib
import numpy as np
from skimage.measure import marching_cubes
import trimesh

def evaluate(source_path):
    img=nib.load(str(source_path))
    array=np.asanyarray(img.dataobj)
    if array.ndim!=3 or not np.isfinite(array).all() or not np.array_equal(array,np.rint(array)):
        raise ValueError('The reference must be a finite integer-valued 3D segmentation')
    fg=array>0
    if int(fg.sum())<500:raise ValueError('Not a viable L3 segmentation')
    label_ids=sorted(int(v) for v in np.unique(array) if v>0)
    if len(label_ids)!=7:raise ValueError('Expected 7 numeric subregion labels, no semantic mapping assumed')
    crop_face_voxels=[int(fg[0,:,:].sum()),int(fg[-1,:,:].sum()),
          int(fg[:,0,:].sum()),int(fg[:,-1,:].sum()),
          int(fg[:,:,0].sum()),int(fg[:,:,-1].sum())]
    # Native crop, deliberate NO padding: do not invent artificial closing faces.
    local_verts,faces,_,_=marching_cubes(fg.astype(np.float32),level=.5)
    verts=nib.affines.apply_affine(img.affine,local_verts).astype(np.float64)
    model=trimesh.Trimesh(vertices=verts,faces=faces,process=False)
    glb=trimesh.exchange.gltf.export_glb(model)
    reimport=trimesh.load(io.BytesIO(glb),file_type='glb',force='mesh',process=False)
    if len(reimport.faces)<100:
        raise ValueError('GLB reimport has no useful geometry')
    extent_drift=np.max(np.abs(model.extents-reimport.extents))
    if not np.isfinite(extent_drift) or extent_drift>1e-3:
        raise ValueError(f'Source GLB geometric bounding-size drift too high: {extent_drift} mm')
    return {
      'status':'CT_SOURCE_GEOMETRY_TECHNICAL_CONVERSION_ONLY',
      'labels_numeric_only':label_ids,
      'original_mask_nonzero_voxels':int(fg.sum()),
      'original_nifti_array_axis_codes':list(nib.aff2axcodes(img.affine)),
      'world_coordinate_system_after_affine':'RAS mm',
      'native_spacing_mm':np.linalg.norm(img.affine[:3,:3],axis=0).round(4).tolist(),
      'source_voxels_on_crop_faces':crop_face_voxels,
      'cropped_reference_touches_border':any(crop_face_voxels),
      'mesh_surface_closure_from_padding':False,
      'source_surface_vertices':len(model.vertices),
      'source_surface_faces':len(model.faces),
      'source_surface_watertight':bool(model.is_watertight),
      'source_surface_extents_mm':model.extents.round(3).tolist(),
      'glb_buffer_bytes_not_stored':len(glb),
      'glb_reimport_faces':len(reimport.faces),
      'glb_reimport_extents_mm':reimport.extents.round(3).tolist(),
      'max_extent_drift_mm':round(float(extent_drift),7),
      'no_anatomical_label_map':True,
      'source_anatomy_completeness_verified':False,
      'source_reference_bias_unknown':True,
      'not_approved_for_teaching':True}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mask',required=True,type=Path)
    a=p.parse_args()
    result=evaluate(a.mask)
    print('CT_SURFACE_TRIAL '+json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
