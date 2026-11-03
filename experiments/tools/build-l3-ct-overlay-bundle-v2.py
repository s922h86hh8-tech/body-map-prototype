#!/usr/bin/env python3
"""One-source CT+mask voxel-aligned review bundle (LOCAL ONLY).

Requires the exact CT and L3 segmentation belonging to the same source scan.
No HU calibration is assumed unless independently verified. Uses percentile
contrast for visualization, NEVER diagnostic quantitative measurement.
Output contains an original CT slice in each direction (may be sensitive):
do not commit, upload, or publish a generated JSON.
"""
import argparse,base64,hashlib,importlib.util,io,json
from pathlib import Path
import nibabel as nib
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
source=HERE/'build-l3-local-review-bundle-v1.py'
spec=importlib.util.spec_from_file_location('l3_review_v1',source)
v1=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v1)

def image_to_b64(rgb):
    rgba=np.concatenate([rgb,np.full(rgb.shape[:2]+(1,),255,dtype=np.uint8)],axis=2)
    im=Image.fromarray(np.flipud(rgba.transpose(1,0,2)),'RGBA')
    im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
    buf=io.BytesIO()
    im.save(buf,format='PNG',optimize=True)
    return base64.b64encode(buf.getvalue()).decode('ascii')

def render_section(ct_slice,mask_slice,lo,hi):
    if ct_slice.shape!=mask_slice.shape:raise ValueError('Slice grid mismatch')
    ct_float=np.asarray(ct_slice,dtype=np.float64)
    normalized=(np.clip((ct_float-lo)/(hi-lo),0,1)*255).astype(np.uint8)
    grayscale=np.repeat(normalized[:,:,None],3,axis=2)
    colors=v1.COLORS[mask_slice.astype(np.intp),:3]
    # 35% overlay for each numeric region, 0% for background.
    opacity=np.where(mask_slice>0,.35,0)[:,:,None]
    blended=np.clip(np.rint(grayscale*(1-opacity)+colors*opacity),0,255).astype(np.uint8)
    return image_to_b64(grayscale),image_to_b64(blended)

def build_pair(mask_path,ct_path,out_path):
    mask_sha=hashlib.sha256(mask_path.read_bytes()).hexdigest()
    ct_sha=hashlib.sha256(ct_path.read_bytes()).hexdigest()
    mi=nib.load(str(mask_path)); ci=nib.load(str(ct_path))
    if mi.shape!=ci.shape:
        raise ValueError('Original CT and label volume shapes do not match')
    max_aff=float(np.max(np.abs(mi.affine-ci.affine)))
    if max_aff>1e-4:raise ValueError('CT and mask affine mismatch; resampling not authorized')
    baseline=v1.build(mask_path,out_path)
    j=json.loads(out_path.read_text(encoding='utf8'))
    mask=nib.as_closest_canonical(mi)
    ct=nib.as_closest_canonical(ci)
    if mask.shape!=ct.shape or not np.allclose(mask.affine,ct.affine,atol=1e-5):
        raise ValueError('CT versus segmentation canonical world coordinates mismatch')
    raw=np.asanyarray(ct.dataobj,dtype=np.float32)
    if not np.isfinite(raw).all():raise ValueError('CT intensity has NaN or Inf')
    labels=np.asanyarray(mask.dataobj)
    # Percentile display window; not necessarily physically calibrated HU.
    lo=float(np.percentile(raw,1))
    hi=float(np.percentile(raw,99.5))
    if hi<=lo:raise ValueError('Unusable CT visualization intensity range')
    for key,axis in [('axial',2),('coronal',1),('sagittal',0)]:
        section=j['sections'][key]
        idx=section['slice_index']
        if key=='axial':
            p=raw[:,:,idx];m=labels[:,:,idx]
        elif key=='coronal':
            p=raw[:,idx,:];m=labels[:,idx,:]
        else:
            p=raw[idx,:,:];m=labels[idx,:,:]
        grayscale,overlay=render_section(p,m,lo,hi)
        section['ct_image_base64_png']=grayscale
        section['ct_overlay_base64_png']=overlay
        section['matched_source_grid']=True
        # Keep v1 numeric-label image as the third distinct view.
    j['schema']='L3_REVIEW_BUNDLE_V2_CT_AND_MASK_NONCLINICAL'
    j['source_type']='paired ORIGINAL CT voxel intensities and L3 segmentation mask (not validated HU)'
    j['paired_source']={'mask_sha256':mask_sha,
                        'ct_sha256':ct_sha,
                        'original_CT_shape_matches_mask':True,
                        'original_CT_affine_max_abs_error':round(max_aff,9),
                        'CT_intensity_units':'SOURCE VALUES; HOUNSFIELD UNITS NOT INDEPENDENTLY VERIFIED',
                        'contrast_method':'fixed source volume p1-p99.5 for display only',
                        'visualization_lo':round(lo,3),
                        'visualization_hi':round(hi,3),
                        'potential_sensitive_medical_image':True}
    j['anatomy_approved']=False
    j['expert_pose_reviewed']=False
    out_path.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
    return {'source_ct_sha256':ct_sha,'source_mask_sha256':mask_sha,
            'grid_exact':max_aff<1e-4,'slices_with_original_CT':list(j['sections']),
            'window':[round(lo,2),round(hi,2)],'glb_triangles':baseline['triangles'],
            'bundle_bytes':out_path.stat().st_size,'no_anatomy_approval':True}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--mask',required=True,type=Path)
    ap.add_argument('--ct',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    a=ap.parse_args()
    print('L3_PAIRED_SOURCE_BUNDLE '+json.dumps(build_pair(a.mask,a.ct,a.out),ensure_ascii=False))
if __name__=='__main__':main()
