#!/usr/bin/env python3
"""L3 research CT: sweep perpendicular MPR planes along an UNVERIFIED proposed axis.

This tool intentionally does NOT return an anatomical pedicle width/height,
nor a verified pedicle isthmus. It provides source-grid cross-sectional
diagnostics for ONE selected numeric source class (1..7) that MUST be
anatomically mapped and reviewed independently. Other connected bone is
excluded by numeric class; a central connected component is identified for
screening only. Crop/out-of-image sections are flagged and NEVER approved.
The underlying CT can contain sensitive images; only local/private use.
"""
import argparse,base64,hashlib,importlib.util,json,math
from pathlib import Path
import nibabel as nib
import numpy as np
from scipy.ndimage import map_coordinates,label as connected_components

REF=Path(__file__).with_name('build-l3-axis-orthogonal-mpr-v5.py')
spec=importlib.util.spec_from_file_location('mpr_v5',REF)
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

def select_center_component(class_mask,mm_per_pixel,max_seed_mm=4.0):
    """Select closest connected component to grid center; cap seed distance."""
    n=class_mask.shape[0]
    if class_mask.ndim!=2 or class_mask.shape[0]!=class_mask.shape[1]:
        raise ValueError('Expected square MPR grid')
    labels,num=connected_components(class_mask.astype(bool),structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
    if num<1:return None,'selected_class_absent'
    center=np.array([(n-1)/2,(n-1)/2])
    nearest=None
    for component in range(1,num+1):
        pts=np.argwhere(labels==component)
        minimum=float(np.linalg.norm((pts-center)*mm_per_pixel,axis=1).min())
        if nearest is None or minimum<nearest[0]:
            nearest=(minimum,pts,component)
    distance,pts,idx=nearest
    if distance>max_seed_mm:return None,'no_class_component_within_seed_radius'
    mask=(labels==idx)
    if mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any():
        return None,'component_touches_MPR_field_of_view'
    return mask,None

def proxy_summary(mask,spacing):
    """PCA ellipse + axis-aligned bbox proxies, NOT anatomical diameters."""
    coords=np.argwhere(mask)
    if len(coords)<8:
        return None,'too_few_pixels_for_cross_section'
    xy=(coords-coords.mean(axis=0))*spacing
    cov=np.cov(xy.T)
    eig=np.sort(np.linalg.eigvalsh(cov))
    if eig[0]<=0:return None,'degenerate_covariance'
    sizes=(np.max(coords,axis=0)-np.min(coords,axis=0)+1)*spacing
    return {
      'component_area_proxy_mm2':round(float(len(coords)*spacing*spacing),3),
      'component_pixels':len(coords),
      'component_bbox_axes_mm':np.round(sizes,3).tolist(),
      'component_PCA_ellipse_minor_proxy_mm':round(float(4*np.sqrt(eig[0])),3),
      'component_PCA_ellipse_major_proxy_mm':round(float(4*np.sqrt(eig[1])),3),
      'not_an_anatomical_isthmus_width':True},None

def sweep(ct_file,mask_file,landmark_file,side,numeric_label,out,
          step_mm=.5,margin_mm=1.0,pixels=101,spacing_mm=.35):
    if not(1<=numeric_label<=7):raise ValueError('numeric class ID must be 1..7')
    if not(.25<=step_mm<=2.0 and 0<=margin_mm<=6.0):
        raise ValueError('Unreviewed spacing or end margin')
    if not(65<=pixels<=251 and pixels%2==1 and .2<=spacing_mm<=.8):
        raise ValueError('Invalid research slice grid')
    ci,mi,pts,record,ctsha,masksha=base.verify_inputs(ct_file,mask_file,landmark_file,side)
    pair=base.PAIR_KINDS[side]
    a,b=pts[pair[0]],pts[pair[1]]
    u,v,normal,length=base.plane_basis(a,b)
    if length<2*margin_mm+step_mm:
        raise ValueError('Provisional axis too short for repeatable sweep')
    ct=np.asanyarray(ci.dataobj,dtype=np.float32)
    seg=np.asanyarray(mi.dataobj)
    if not np.isfinite(ct).all() or not np.array_equal(seg,np.rint(seg)):
        raise ValueError('Invalid paired CT intensity or source numeric segmentation')
    if seg.min()<0 or seg.max()>7:raise ValueError('Unexpected numeric class values')
    seg=seg.astype(np.uint8)
    lo,hi=np.percentile(ct,[1,99.5])
    if hi<=lo:raise ValueError('Cannot make source-image diagnostic contrast')
    # Deliberately include both ends of reviewed interval in stable 0.5-mm steps;
    # do not extend past user-selected landmark points.
    steps=np.arange(margin_mm,length-margin_mm+step_mm/4,step_mm)
    if len(steps)>200:raise ValueError('Unreviewed large number of CT planes')
    ts=(np.arange(pixels,dtype=np.float64)-(pixels-1)/2)*spacing_mm
    ii,jj=np.meshgrid(ts,ts,indexing='ij')
    plane_offset=u.reshape(3,1,1)*ii+v.reshape(3,1,1)*jj
    inv=np.linalg.inv(ci.affine)
    results=[]
    for k,travel in enumerate(steps):
        world=a.reshape(3,1,1)+travel*normal.reshape(3,1,1)+plane_offset
        index=nib.affines.apply_affine(inv,world.reshape(3,-1).T).T
        valid=np.all((index>=0)&(index<=np.asarray(ct.shape).reshape(3,1)-1),axis=0).reshape((pixels,pixels))
        samples=map_coordinates(seg,index,order=0,mode='constant',cval=0).reshape((pixels,pixels))
        binary=(samples==numeric_label)
        component,why=select_center_component(binary,spacing_mm)
        proxy=None
        if component is not None:
            # If any component intersects ORIGINAL source CT crop boundary,
            # estimates may be truncated. Reject the whole plane as approval input.
            coords=np.argwhere(component)
            if coords.size:
                selected=world[:,component]
                ijk=nib.affines.apply_affine(inv,selected.T)
                if np.any((ijk<.51)|(ijk>np.asarray(ct.shape)-1.51)):
                    why='component_touches_original_CT_crop_boundary'
                elif not bool(valid[component].all()):
                    why='component_outside_CT_grid'
                if why is None:
                    proxy,why=proxy_summary(component,spacing_mm)
        count=int(np.count_nonzero(binary))
        result={
          'index':k,'travel_mm_from_body_candidate':round(float(travel),3),
          'fraction_from_body_candidate':round(float(travel/length),6),
          'center_world_ras_mm':np.round(a+travel*normal,5).tolist(),
          'selected_numeric_label':numeric_label,
          'same_label_pixels_in_MPR':count,
          'component_accepted_for_proxy':why is None and proxy is not None,
          'invalid_reason':why,
          'component_diagnostics':proxy,
          'ROI_is_not_anatomically_verified':True}
        results.append(result)
    accepted=[row for row in results if row['component_accepted_for_proxy']]
    # The MINIMUM below is a provisional sampled *numerical* proxy only.
    # Never expose it as the true pedicle isthmus.
    rank=sorted(accepted,key=lambda row:row['component_diagnostics']['component_PCA_ellipse_minor_proxy_mm'])
    nominated=rank[0]['index'] if rank else None
    preview_indices={0,len(results)//2,len(results)-1}
    if nominated is not None:preview_indices.add(nominated)
    previews=[]
    for idx in sorted(preview_indices):
        t=results[idx]['travel_mm_from_body_candidate']
        world=a.reshape(3,1,1)+t*normal.reshape(3,1,1)+plane_offset
        uvw=nib.affines.apply_affine(inv,world.reshape(3,-1).T).T
        gray=map_coordinates(ct,uvw,order=1,mode='nearest').reshape((pixels,pixels))
        lbl=map_coordinates(seg,uvw,order=0,mode='constant',cval=0).reshape((pixels,pixels))
        previews.append({
          'plane_index':idx,
          'display_image_base64_png':base.rgba_png(gray,lbl,float(lo),float(hi),True),
          'center_world_ras_mm':results[idx]['center_world_ras_mm'],
          'selected_class_status':results[idx]['invalid_reason'],
          'potentially_sensitive_CT_image':True})
    outdata={
      'schema':'L3_PEDICLE_AXIS_MULTI_MPR_V6_RESEARCH_ONLY',
      'source_CT_sha256':ctsha,'source_mask_sha256':masksha,
      'side_candidate':side,'selected_numeric_label_unverified_name':numeric_label,
      'anatomic_label_mapping_confirmed':False,
      'axis_endpoints_reviewed_by_expert':False,
      'all_source_landmarks_unverified':True,
      'input_uses_fictitious_demo_points':bool(record.get('synthetic_technical_demo_not_anatomy',False)),
      'axis_length_mm':round(float(length),5),'normal_RAS':normal.round(9).tolist(),
      'plane_normal_orthogonal_to_axis':True,
      'sampling_step_mm':step_mm,'sampling_grid_spacing_mm':spacing_mm,
      'sampling_interval_margin_mm':margin_mm,
      'n_planes':len(results),'n_valid_numeric_roi_planes':len(accepted),
      'CT_grid_shape':list(ci.shape),
      'planes':results,
      'minimum_proxy_plane_index_if_any':nominated,
      'minimum_proxy_is_anatomical_pedicle_isthmus':False,
      'previews':previews,
      'not_an_anatomic_width_or_height_measurement':True,
      'no_numeric_acceptance_threshold':True,
      'expert_anatomy_approved':False}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(outdata,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf8')
    return {'status':'MULTIPLE_L3_CT_PLANES_TECHNICALLY_COMPUTED',
       'planes':len(results),'valid_numeric_ROI_planes':len(accepted),
       'rejected_planes':{reason:sum(x['invalid_reason']==reason for x in results)
                          for reason in sorted(set(x['invalid_reason'] for x in results if x['invalid_reason']))},
       'source_ct_SHA256_match':True,
       'smallest_numeric_ellipse_proxy_plane_index':nominated,
       'minimum_proxy_is_anatomic_isthmus':False,
       'source_numeric_label_mapped_to_anatomy':False,
       'anatomy_approved':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('ct','mask','landmarks','out'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--side',choices=['right','left'],required=True)
    p.add_argument('--numeric-label',type=int,required=True)
    p.add_argument('--step-mm',type=float,default=.5)
    p.add_argument('--margin-mm',type=float,default=1.)
    p.add_argument('--pixels',type=int,default=101)
    p.add_argument('--spacing-mm',type=float,default=.35)
    a=p.parse_args()
    result=sweep(a.ct,a.mask,a.landmarks,a.side,a.numeric_label,a.out,
                 step_mm=a.step_mm,margin_mm=a.margin_mm,pixels=a.pixels,spacing_mm=a.spacing_mm)
    print('L3_V6_MULTI_MPR '+json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
