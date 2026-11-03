#!/usr/bin/env python3
"""Build one browser-readable JSON review bundle from a locally held, licensed L3 mask.

Inputs: an integer-labeled L3 NIfTI segmentation, NOT raw CT image.
Output: local JSON with GLB source surface + axial/coronal/sagittal segmentation
slices; no mesh/case data is committed or uploaded by this script.
The CT-derived shape is INDIVIDUAL SUBJECT DATA, potentially cropped,
and not independently approved for anatomy teaching.
"""
import argparse,base64,hashlib,io,json
from pathlib import Path
import nibabel as nib
import numpy as np
from PIL import Image
from skimage.measure import marching_cubes
import trimesh

COLORS=np.array([
 [7,19,30,255],  # background (non-identifying visual)
 [103,191,195,255],[252,188,115,255],[174,164,223,255],
 [247,136,142,255],[149,208,153,255],[135,166,228,255],
 [224,203,129,255]],dtype=np.uint8)

def encode_image(slice2d):
    if slice2d.ndim!=2 or slice2d.max()>7 or slice2d.min()<0:
        raise ValueError('Unexpected 2D label range')
    # Input plane array has (horizontal,vertical) axes. Image rows run top down.
    im=Image.fromarray(COLORS[np.flipud(slice2d.T)],'RGBA')
    im=im.resize((im.width*2,im.height*2),resample=Image.Resampling.NEAREST)
    memory=io.BytesIO()
    im.save(memory,'PNG',optimize=True)
    return base64.b64encode(memory.getvalue()).decode('ascii')

def source_metadata(image,foreground,bytes_hash):
    m=image.affine
    axcodes=nib.aff2axcodes(m)
    original_shape=list(image.shape)
    faces=[int(foreground[0,:,:].sum()),int(foreground[-1,:,:].sum()),
           int(foreground[:,0,:].sum()),int(foreground[:,-1,:].sum()),
           int(foreground[:,:,0].sum()),int(foreground[:,:,-1].sum())]
    return {'source_mask_sha256':bytes_hash,
            'array_axes_before_reorientation':list(axcodes),
            'original_array_shape':original_shape,
            'source_voxels_on_six_crop_faces':faces,
            'source_crop_boundary_touched':any(faces),
            'native_spacing_mm':np.linalg.norm(m[:3,:3],axis=0).round(5).tolist(),
            'numeric_class_names_not_verified':True,
            'full_anatomic_completeness_not_verified':True,
            'source_is_segmentation_not_original_CT_image':True}

def build(mask_file,out_file):
    raw=mask_file.read_bytes()
    im=nib.load(str(mask_file))
    if not np.isfinite(im.affine).all() or abs(np.linalg.det(im.affine[:3,:3]))<1e-9:
        raise ValueError('Invalid source NIfTI affine')
    arr=np.asanyarray(im.dataobj)
    if arr.ndim!=3 or not np.isfinite(arr).all() or not np.array_equal(arr,np.rint(arr)):
        raise ValueError('Mask must have 3D integer-valued labels')
    label_ids=sorted(int(x) for x in np.unique(arr) if x>0)
    if label_ids!=list(range(1,8)) or np.min(arr)<0:
        raise ValueError('Expected exactly unverified numeric class IDs 1..7')
    orig=(arr>0)
    if np.count_nonzero(orig)<500:raise ValueError('L3 segmentation too small')
    metadata=source_metadata(im,orig,hashlib.sha256(raw).hexdigest())
    canonical=nib.as_closest_canonical(im)
    # Source datasets here are RAS/LPS axis-aligned, not oblique images.
    # Oblique CT requires explicit resampling of section axes (not silently guessed).
    aff=canonical.affine
    mm=np.diag(aff[:3,:3])
    off=aff[:3,:3]-np.diag(mm)
    if not np.all(mm>0) or np.max(np.abs(off))>1e-4:
        raise ValueError('Oblique / unexpected NIfTI orientation: section resampling required')
    arr=np.asanyarray(canonical.dataobj).astype(np.uint8)
    fg=arr>0
    pos=np.array(np.nonzero(fg))
    lower=pos.min(axis=1)
    upper=pos.max(axis=1)
    center=(lower+upper)//2
    if any(int(n)<5 for n in fg.shape):raise ValueError('Unexpected small image')
    # NO pad and NO cap: do not invent missing bone at scan crop edges.
    verts,faces,_,_=marching_cubes(fg.astype(np.float32),level=.5)
    xyz=nib.affines.apply_affine(aff,verts)
    mesh=trimesh.Trimesh(vertices=xyz,faces=faces,process=False)
    glb=trimesh.exchange.gltf.export_glb(mesh)
    reloaded=trimesh.load(io.BytesIO(glb),file_type='glb',force='mesh',process=False)
    if len(mesh.faces)!=len(reloaded.faces):raise ValueError('GLB reimport changed triangle count')
    extent_delta=float(np.max(np.abs(mesh.extents-reloaded.extents)))
    if extent_delta>1e-3:raise ValueError('GLB extent changed')
    sections={
      'axial':{'slice_index':int(center[2]),'world_coordinate_mm':round(float(aff[2,2]*center[2]+aff[2,3]),3),
               'image_base64_png':encode_image(arr[:,:,center[2]])},
      'coronal':{'slice_index':int(center[1]),'world_coordinate_mm':round(float(aff[1,1]*center[1]+aff[1,3]),3),
               'image_base64_png':encode_image(arr[:,center[1],:])},
      'sagittal':{'slice_index':int(center[0]),'world_coordinate_mm':round(float(aff[0,0]*center[0]+aff[0,3]),3),
               'image_base64_png':encode_image(arr[center[0],:,:])}
    }
    out={'schema':'L3_REVIEW_BUNDLE_V1_NONCLINICAL',
         'source_type':'CT-derived integer segmentation mask, NOT raw grayscale CT',
         'coordinate_system':'RAS','units':'mm',
         'numeric_labels':label_ids,'numeric_to_anatomical_map_verified':False,
         'source':metadata,
         'surface':{'glb_base64':base64.b64encode(glb).decode('ascii'),
                    'glb_sha256':hashlib.sha256(glb).hexdigest(),
                    'vertices':len(mesh.vertices),'triangles':len(mesh.faces),
                    'watertight':bool(mesh.is_watertight),
                    'source_surface_bbox_mm':mesh.bounds.round(4).tolist(),
                    'source_surface_extents_mm':mesh.extents.round(4).tolist(),
                    'bbox_glb_roundtrip_error_mm':round(extent_delta,7)},
         'sections':sections,
         'scope':'independent research review only, no teaching approval',
         'anatomy_approved':False,
         'expert_pose_reviewed':False,
         'geometry_gaps_reconstructed':False}
    out_file.parent.mkdir(parents=True,exist_ok=True)
    out_file.write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
    return {'output':str(out_file),'bytes':out_file.stat().st_size,
            'source_mask_sha256':metadata['source_mask_sha256'],
            'triangles':len(mesh.faces),'glb_faces_verified':len(reloaded.faces),
            'section_images':list(sections),
            'coordinate_system':'RAS','crop_boundary_touched':metadata['source_crop_boundary_touched'],
            'anatomy_approved':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mask',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    print('L3_BUNDLE_BUILT '+json.dumps(build(a.mask,a.out),ensure_ascii=False))
if __name__=='__main__':main()
