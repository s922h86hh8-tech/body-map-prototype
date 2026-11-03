// Pure coordinate helpers for LOCAL L3 source CT review (never anatomy approval).
// CT masks are canonical RAS, with 2x nearest-neighbor PNG images generated from
// np.flipud(label_slice.T). Marker placement reverses screen Y and accounts for
// object-fit: contain; original CT image/segmentation geometry is not modified.
const sectionAxes={axial:[0,1,2],coronal:[0,2,1],sagittal:[1,2,0]};
const clamp=(x,lo,hi)=>Math.max(lo,Math.min(hi,x));
export function planeAxes(plane){
 if(!Object.prototype.hasOwnProperty.call(sectionAxes,plane))throw new Error('Unknown CT plane');
 return sectionAxes[plane];
}
export function voxelWorld(voxel,affine){
 if(voxel?.length!==3||affine?.length!==4||affine.some(row=>row.length!==4))throw new Error('Invalid voxel/world transform');
 const p=affine.slice(0,3).map(row=>row[0]*voxel[0]+row[1]*voxel[1]+row[2]*voxel[2]+row[3]);
 if(!p.every(Number.isFinite))throw new Error('Non-finite world landmark');
 return p;
}
export function pointFromImageClick(plane,click,imageBox,canonical,sectionIndex){
 const [i,j,k]=planeAxes(plane);
 const shape=canonical?.array_shape_xyz;
 const affine=canonical?.affine_4x4;
 if(shape?.length!==3||!shape.every(x=>Number.isInteger(x)&&x>0))throw new Error('Missing voxel shape');
 if(!Number.isInteger(sectionIndex)||sectionIndex<0||sectionIndex>=shape[k])throw new Error('Bad slice index');
 const {left,top,width,height,naturalWidth,naturalHeight}=imageBox;
 if(![left,top,width,height,naturalWidth,naturalHeight].every(Number.isFinite)||width<=0||height<=0||naturalWidth<=0||naturalHeight<=0)throw new Error('Bad image rectangle');
 const scale=Math.min(width/naturalWidth,height/naturalHeight);
 const renderW=naturalWidth*scale,renderH=naturalHeight*scale;
 const x0=left+(width-renderW)/2,y0=top+(height-renderH)/2;
 const u=(click.x-x0)/renderW,v=(click.y-y0)/renderH;
 if(u<0||v<0||u>=1||v>=1)throw new Error('Click in image letterbox / outside CT');
 const voxel=[0,0,0];
 voxel[i]=clamp(Math.floor(u*shape[i]),0,shape[i]-1);
 voxel[j]=clamp(shape[j]-1-Math.floor(v*shape[j]),0,shape[j]-1);
 voxel[k]=sectionIndex;
 return {voxel_ijk:voxel,world_ras_mm:voxelWorld(voxel,affine),
         on_image_uv:[u,v],plane,section_index:sectionIndex};
}
export function imageUVFromVoxel(plane,voxel,shape){
 const [i,j,k]=planeAxes(plane);
 if(voxel?.length!==3||shape?.length!==3||!voxel.every((v,ax)=>Number.isInteger(v)&&v>=0&&v<shape[ax]))throw new Error('Invalid indexed landmark');
 return [(voxel[i]+.5)/shape[i],(shape[j]-voxel[j]-.5)/shape[j]];
}
export function anatomicalReviewJson(landmarks,source){
 if(!Array.isArray(landmarks)||!source?.source_mask_sha256||!source?.ct_sha256)throw new Error('Missing provenance');
 return {schema:'L3_LOCAL_LANDMARK_REVIEW_V1',basis:'single individual CT RAS/mm',
   note:'Landmarks are provisional human selections on source CT images; NOT independently expert-validated.',
   source_mask_sha256:source.source_mask_sha256,
   source_CT_sha256:source.ct_sha256,
   anatomical_name_to_numeric_class_mapping_verified:false,
   affine_independently_anatomically_verified:false,
   ready_for_anatomical_approval:false,
   items:landmarks.map(item=>({
     kind:item.kind,kind_ja:item.kind_ja,
     world_ras_mm:[...item.world_ras_mm],
     voxel_ijk:[...item.voxel_ijk],
     plane:item.plane,section_index:item.section_index,
     reviewer_confirmation:'unverified_candidate',
     authority:'unreviewed_manual_click'}))};
}
