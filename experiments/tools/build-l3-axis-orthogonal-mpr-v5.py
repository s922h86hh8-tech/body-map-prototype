#!/usr/bin/env python3
"""Produce a NON-DIAGNOSTIC axis-orthogonal CT plane from two provisional L3 landmarks.

Pedicle *isthmus* = narrowest axis-orthogonal region, not assumed to coincide
with the midpoint of two manually selected landmark candidates. This utility
makes one reproducible MPR plane, not a narrowest-width measurement and not an
anatomical approval. Source CT intensities are not automatically calibrated HU.
Input CT/mask and output PNG/JSON can contain medical images: keep locally.
"""
import argparse,base64,hashlib,io,json,math
from pathlib import Path
import nibabel as nib
import numpy as np
from scipy.ndimage import map_coordinates
from PIL import Image

COLORS=np.array([[0,0,0],[103,191,195],[252,188,115],[174,164,223],
 [247,136,142],[149,208,153],[135,166,228],[224,203,129]],dtype=np.uint8)
PAIR_KINDS={
 'right':('pedicle_axis_right_body','pedicle_axis_right_posterior'),
 'left':('pedicle_axis_left_body','pedicle_axis_left_posterior')}
def verify_inputs(ct_path,mask_path,review_path,side):
    ctbytes=ct_path.read_bytes();maskbytes=mask_path.read_bytes()
    report=json.loads(review_path.read_text(encoding='utf8'))
    if report.get('schema')!='L3_LOCAL_LANDMARK_REVIEW_V1' or report.get('ready_for_anatomical_approval') is not False:
        raise ValueError('Only unverified v4 landmark review JSON is supported')
    if report.get('source_CT_sha256')!=hashlib.sha256(ctbytes).hexdigest():
        raise ValueError('Source CT does not match reviewed landmark file SHA256')
    if report.get('source_mask_sha256')!=hashlib.sha256(maskbytes).hexdigest():
        raise ValueError('Source segmentation does not match reviewed landmark file SHA256')
    ci=nib.load(str(ct_path));mi=nib.load(str(mask_path))
    if ci.shape!=mi.shape or np.max(np.abs(ci.affine-mi.affine))>1e-4:
        raise ValueError('Original CT and mask grids must match exactly')
    if not np.isfinite(ci.affine).all() or abs(np.linalg.det(ci.affine[:3,:3]))<1e-9:
        raise ValueError('Invalid source CT world affine')
    if any(0==n for n in ci.shape) or len(ci.shape)!=3:raise ValueError('Require original 3D CT')
    if side not in PAIR_KINDS:raise ValueError('Unknown pedicle side')
    pts={}
    for kind in PAIR_KINDS[side]:
        rows=[item for item in report.get('items',[]) if item.get('kind')==kind]
        if len(rows)!=1:raise ValueError('Exactly one '+kind+' landmark required')
        item=rows[0]
        if item.get('reviewer_confirmation')!='unverified_candidate' or item.get('authority')!='unreviewed_manual_click':
            raise ValueError('Input annotation approval state is unexpected')
        voxel=np.asarray(item.get('voxel_ijk'),dtype=float)
        world=np.asarray(item.get('world_ras_mm'),dtype=float)
        if voxel.shape!=(3,) or world.shape!=(3,) or not np.isfinite(voxel).all() or not np.isfinite(world).all():
            raise ValueError('Invalid landmark points')
        if np.any(voxel<0) or np.any(voxel>=ci.shape) or not np.array_equal(voxel,np.round(voxel)):
            raise ValueError('Landmark not on valid image voxels')
        expected=nib.affines.apply_affine(ci.affine,voxel)
        if np.linalg.norm(expected-world)>1e-4:
            raise ValueError('Landmark RAS does not match source CT affine/voxel')
        pts[kind]=world
    return ci,mi,pts,report,hashlib.sha256(ctbytes).hexdigest(),hashlib.sha256(maskbytes).hexdigest()

def plane_basis(pbody,pposterior):
    normal=np.asarray(pposterior)-np.asarray(pbody)
    length=float(np.linalg.norm(normal))
    if length<1 or length>100:
        raise ValueError('Two candidate axis points are degenerate or separated beyond technical input range')
    normal=normal/length
    guide=np.array([0.,0.,1.]) if abs(normal[2])<.9 else np.array([0.,1.,0.])
    u=np.cross(guide,normal);u=u/np.linalg.norm(u)
    v=np.cross(normal,u);v=v/np.linalg.norm(v)
    basis=np.stack([u,v,normal],axis=1)
    if np.max(np.abs(basis.T@basis-np.eye(3)))>1e-10 or np.linalg.det(basis)<.999999:
        raise ValueError('Axis-orthogonal CT plane basis is invalid')
    return u,v,normal,length

def rgba_png(gray,mask,lo,hi,overlay):
    gray=np.clip((gray-lo)/(hi-lo),0.,1.)
    rgb=np.clip(np.rint(gray*255),0,255).astype(np.uint8)
    im=np.repeat(rgb[...,None],3,axis=-1)
    if overlay:
        if np.any((mask<0)|(mask>7)):raise ValueError('CT mask contains an unknown numeric class')
        opacity=np.where(mask>0,.38,0.)[...,None]
        im=np.clip(np.rint(im*(1-opacity)+COLORS[mask]*opacity),0,255).astype(np.uint8)
    image=Image.fromarray(np.flipud(np.transpose(im,(1,0,2))),'RGB')
    target=io.BytesIO()
    image.save(target,format='PNG',optimize=True)
    return base64.b64encode(target.getvalue()).decode('ascii')

def generate(ct_path,mask_path,review_path,side,out_path,fraction=.5,pixels=101,spacing_mm=.35):
    if not(0<=fraction<=1):raise ValueError('fraction must be 0-1')
    if pixels<33 or pixels>301 or pixels%2!=1 or not(.1<=spacing_mm<=1.5):
        raise ValueError('Unreviewed sampling grid parameters')
    ci,mi,points,review,ctsha,masksha=verify_inputs(ct_path,mask_path,review_path,side)
    start,end=PAIR_KINDS[side]
    body,posterior=points[start],points[end]
    u,v,n,axis_length=plane_basis(body,posterior)
    center=body+fraction*(posterior-body)
    t=(np.arange(pixels,dtype=float)-(pixels-1)/2)*spacing_mm
    i,j=np.meshgrid(t,t,indexing='ij')
    xyz=(center.reshape(3,1,1)+
         u.reshape(3,1,1)*i+v.reshape(3,1,1)*j)
    ijk=nib.affines.apply_affine(np.linalg.inv(ci.affine),xyz.reshape(3,-1).T).T
    mask_inside=np.all((ijk>=0)&(ijk<=np.array(ci.shape).reshape(3,1)-1),axis=0).reshape(pixels,pixels)
    ct=np.asanyarray(ci.dataobj,dtype=np.float32)
    labels=np.asanyarray(mi.dataobj)
    if not np.isfinite(ct).all() or not np.array_equal(labels,np.rint(labels)):
        raise ValueError('Invalid reference CT intensity or numeric labels')
    labels=labels.astype(np.int16)
    if np.min(labels)<0 or np.max(labels)>7:raise ValueError('Unexpected numeric label encoding')
    sampled=map_coordinates(ct,ijk,order=1,mode='constant',cval=float(np.min(ct))).reshape((pixels,pixels))
    sampled_labels=map_coordinates(labels,ijk,order=0,mode='constant',cval=0).reshape((pixels,pixels))
    low=float(np.percentile(ct,1.))
    high=float(np.percentile(ct,99.5))
    if high<=low:raise ValueError('Source CT window is degenerate')
    grayscale=rgba_png(sampled,sampled_labels,low,high,False)
    overlay=rgba_png(sampled,sampled_labels,low,high,True)
    result={
      'schema':'L3_AXIS_ORTHOGONAL_MPR_V5_TECHNICAL_ONLY',
      'source_CT_sha256':ctsha,'source_mask_sha256':masksha,
      'side_candidate':side,
      'source_landmarks_are_unverified':True,
      'input_demo_points':bool(review.get('synthetic_technical_demo_not_anatomy',False)),
      'axis_points_world_ras_mm':{'body_end':body.tolist(),'posterior_end':posterior.tolist()},
      'axis_length_between_points_mm':round(axis_length,6),
      'plane_fraction_along_two_points':fraction,
      'plane_center_world_ras_mm':center.round(6).tolist(),
      'plane_normal_world_ras':n.round(9).tolist(),
      'plane_horizontal_world_ras':u.round(9).tolist(),
      'plane_vertical_world_ras':v.round(9).tolist(),
      'sample_grid_pixels':pixels,'sampling_mm_per_pixel':spacing_mm,
      'CT_mask_were_in_exact_same_grid':True,
      'plane_points_inside_source_CT_fraction':round(float(mask_inside.mean()),6),
      'sampled_nonzero_class_counts':{str(k):int(np.count_nonzero(sampled_labels==k)) for k in range(1,8)},
      'image_ct_base64_png':grayscale,'image_overlay_base64_png':overlay,
      'source_intensity_units':'not independently confirmed as HU',
      'plane_is_pedicle_isthmus_verified':False,
      'not_a_pedicle_width_or_height_measurement':True,
      'medical_anatomy_approved':False}
    out_path.parent.mkdir(parents=True,exist_ok=True)
    out_path.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
    return {'schema':result['schema'],'side':side,'input_demo_points':result['input_demo_points'],
            'source_CT_SHA256_verified':True,
            'CT_mask_grid_agrees':True,'axis_length_mm':round(axis_length,3),
            'plane_orthogonality_max_error':round(float(np.max(np.abs(np.stack([u,v,n],axis=1).T@np.stack([u,v,n],axis=1)-np.eye(3)))),10),
            'inside_fraction':result['plane_points_inside_source_CT_fraction'],
            'pixel_dims':[pixels,pixels],
            'anatomical_approval':False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('ct','mask','landmarks','out'):p.add_argument('--'+k,required=True,type=Path)
    p.add_argument('--side',choices=('right','left'),required=True)
    p.add_argument('--fraction',type=float,default=.5)
    p.add_argument('--pixels',type=int,default=101)
    p.add_argument('--spacing-mm',type=float,default=.35)
    a=p.parse_args()
    result=generate(a.ct,a.mask,a.landmarks,a.side,a.out,a.fraction,a.pixels,a.spacing_mm)
    print('L3_V5_MPR_TECHNICAL '+json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
