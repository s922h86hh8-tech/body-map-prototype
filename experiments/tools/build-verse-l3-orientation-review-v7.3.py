#!/usr/bin/env python3
"""Local-only RAS-axis original-CT review panes for VerSe numeric L3 label 22.

NON-DIAGNOSTIC, NOT ANATOMICAL APPROVAL. Input JSON output embeds CT image
slices: keep private and off public GitHub, Pages, and Actions artifacts.
Orientations explicitly follow RAS world axes, NOT inferred anatomy.
Axial: image RIGHT=+R, image TOP=+A; coronal RIGHT=+R, TOP=+S;
sagittal RIGHT=+A, TOP=+S. Never auto-approve body/spinous landmarks.
"""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path

import nibabel as nib
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates

SCHEMA="L3_VERSE_ORIENTATION_REVIEW_V7_3_LOCAL_ONLY"
AXES={
    'axial': {'right':[1.,0.,0.], 'up':[0.,1.,0.], 'screen_edge':['R','A']},
    'coronal': {'right':[1.,0.,0.], 'up':[0.,0.,1.], 'screen_edge':['R','S']},
    'sagittal': {'right':[0.,1.,0.], 'up':[0.,0.,1.], 'screen_edge':['A','S']},
}
def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()

def pixel_world(center,plane,x,y,n,pitch):
    """Pixel-center RAS/mm. +screen Y down corresponds to -RAS 'up'."""
    if plane not in AXES: raise ValueError('Unknown plane')
    if not (0<=x<n and 0<=y<n and n>=25 and n%2==1 and pitch>0):
        raise ValueError('Invalid pixel or grid')
    c=np.asarray(center,float)
    a=AXES[plane]
    return c+(x-(n-1)/2)*pitch*np.array(a['right'])+((n-1)/2-y)*pitch*np.array(a['up'])

def slice_images(ct,seg,affine,center,plane,n,pitch):
    """Sample world-aligned RAS planes directly, including noncanonical source affines."""
    if n>401 or not(.25<=pitch<=1.5):raise ValueError('Unreviewed image dimensions')
    a=AXES[plane]
    half=(n-1)/2
    xx,yy=np.meshgrid(np.arange(n,dtype=float)-half,half-np.arange(n,dtype=float))
    xyz=np.asarray(center,dtype=float)[:,None,None]+pitch*(
        np.array(a['right'])[:,None,None]*xx[None,:,:]+
        np.array(a['up'])[:,None,None]*yy[None,:,:])
    inv=np.linalg.inv(affine)
    ijk=np.asarray(inv[:3,:3]@xyz.reshape(3,-1)+inv[:3,3,None])
    inside=np.all((ijk>=0)&(ijk<=np.array(ct.shape)[:,None]-1),axis=0).reshape(n,n)
    intens=map_coordinates(ct.astype(np.float32,copy=False),ijk,order=1,mode='constant',cval=0).reshape(n,n)
    labels=map_coordinates(seg,ijk,order=0,mode='constant',cval=0).reshape(n,n)==22
    # Presentation window ONLY, source intensities are NOT confirmed HU.
    if not inside.any():raise ValueError('Slice wholly outside CT')
    lo,hi=np.percentile(intens[inside],[1,99.5])
    if not (np.isfinite(lo) and np.isfinite(hi) and hi>lo):
        raise ValueError('Degenerate CT presentation window')
    gray=np.clip((intens-lo)/(hi-lo)*255,0,255).astype(np.uint8)
    gray[~inside]=0
    rgb=np.repeat(gray[:,:,None],3,axis=2)
    over=rgb.copy()
    # Cyan highlight for label 22 only; no claims about remaining structures.
    over[labels,0]=np.clip(np.rint(.65*over[labels,0]+.35*38),0,255).astype(np.uint8)
    over[labels,1]=np.clip(np.rint(.65*over[labels,1]+.35*218),0,255).astype(np.uint8)
    over[labels,2]=np.clip(np.rint(.65*over[labels,2]+.35*245),0,255).astype(np.uint8)
    def encoded(arr):
        f=io.BytesIO()
        Image.fromarray(arr,'RGB').save(f,format='PNG',optimize=True)
        return base64.b64encode(f.getvalue()).decode('ascii')
    return {'ct_png_base64':encoded(rgb),'ct_l3_overlay_png_base64':encoded(over),
            'source_CT_plane_inside_fraction':round(float(inside.mean()),6),
            'l3_pixels_in_plane':int(labels.sum()),
            'display_window_source_values':[round(float(lo),3),round(float(hi),3)]}

def build(ct_path,seg_path,case_id,out_path,n=225,pitch=.65):
    if not case_id or len(case_id)>70 or any(c in case_id for c in ('/','\\','\n')):
        raise ValueError('Invalid local case id')
    if n<25 or n>401 or n%2!=1 or not(.25<=pitch<=1.5):
        raise ValueError('Invalid output grid')
    ci=nib.load(str(ct_path));mi=nib.load(str(seg_path))
    if len(ci.shape)!=3 or ci.shape!=mi.shape:
        raise ValueError('CT and segmentation 3D shapes must match')
    if not np.allclose(ci.affine,mi.affine,atol=1e-4,rtol=0):
        raise ValueError('CT and segmentation source world affines differ')
    aff=np.asarray(ci.affine,float)
    if not np.isfinite(aff).all() or abs(np.linalg.det(aff[:3,:3]))<1e-9:
        raise ValueError('Invalid NIfTI affine')
    mask=np.asarray(mi.dataobj)
    if not np.isfinite(mask).all() or not np.array_equal(mask,np.rint(mask)):
        raise ValueError('Invalid non-integer label mask')
    vox=np.nonzero(mask==22)
    if vox[0].size==0:raise ValueError('No numeric label 22')
    mean_ijk=np.array([np.mean(a) for a in vox])
    center=aff[:3,:3]@mean_ijk+aff[:3,3]
    ct=np.asarray(ci.dataobj,dtype=np.float32)
    if not np.isfinite(ct).all():raise ValueError('Invalid CT array')
    result={
      'schema':SCHEMA,
      'source_dataset_declared':'VerSe20 secondary mirror (not official restructured provenance)',
      'case_id_local':case_id,
      'source_CT_sha256':sha256(ct_path),
      'source_mask_sha256':sha256(seg_path),
      'source_l3_numeric_label':22,
      'label22_source_voxels':int(vox[0].size),
      'center_world_ras_mm':[float(v) for v in center],
      'view_pixels_each_side':n,
      'pitch_mm_per_pixel':pitch,
      'screens':{},
      'note':'Image right and top directions are RAS-world axes ONLY, not expert-verified anatomy.',
      'source_CT_values_are_HU_verified':False,
      'landmark_selections_independently_expert_verified':False,
      'front_back_anatomical_direction_verified':False,
      'anatomy_approved':False,
      'images_are_sensitive_do_not_upload':True,
    }
    for plane,a in AXES.items():
        result['screens'][plane]={
          'pixel_right_ras':a['right'],'pixel_up_ras':a['up'],
          'right_edge':a['screen_edge'][0],'top_edge':a['screen_edge'][1],
          **slice_images(ct,mask,aff,center,plane,n,pitch)
        }
    out_path.parent.mkdir(parents=True,exist_ok=True)
    out_path.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
    return {
      'schema':SCHEMA,'case':case_id,
      'label22_voxels':result['label22_source_voxels'],
      'panes':list(result['screens']),
      'ras_direction_labels':{k:[v['right_edge'],v['top_edge']] for k,v in result['screens'].items()},
      'images_encoded_in_private_JSON':True,
      'anatomy_approved':False,
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--ct',type=Path,required=True)
    ap.add_argument('--seg',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--case-id',required=True)
    ap.add_argument('--pixels',type=int,default=225)
    ap.add_argument('--pitch',type=float,default=.65)
    a=ap.parse_args()
    print('L3_ORIENTATION_PANES '+json.dumps(build(a.ct,a.seg,a.case_id,a.out,a.pixels,a.pitch),ensure_ascii=False))

if __name__=='__main__':
    main()
