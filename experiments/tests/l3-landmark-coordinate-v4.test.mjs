import assert from 'node:assert/strict';
import {planeAxes,voxelWorld,pointFromImageClick,imageUVFromVoxel,anatomicalReviewJson} from '../l3-landmark-coordinate-v4.mjs';
const shape=[90,70,50];
const aff=[[.5,0,0,10],[0,.6,0,-20],[0,0,1,30],[0,0,0,1]];
const grid={array_shape_xyz:shape,affine_4x4:aff};
const imageRect={left:50,top:200,width:350,height:350};
let passed=0;
for(const plane of ['axial','coronal','sagittal']){
  const [x,y,z]=planeAxes(plane);
  const voxel=[17,52,23];
  const naturalWidth=shape[x]*2,naturalHeight=shape[y]*2;
  const scale=Math.min(imageRect.width/naturalWidth,imageRect.height/naturalHeight);
  const w=naturalWidth*scale,h=naturalHeight*scale;
  const [u,v]=imageUVFromVoxel(plane,voxel,shape);
  const pos={x:imageRect.left+(imageRect.width-w)/2+u*w,
             y:imageRect.top+(imageRect.height-h)/2+v*h};
  const output=pointFromImageClick(plane,pos,{...imageRect,naturalWidth,naturalHeight},grid,voxel[z]);
  assert.deepEqual(output.voxel_ijk,voxel,plane);
  assert.deepEqual(output.world_ras_mm,[18.5,11.2,53]);
  assert.equal(output.plane,plane);
  const row={
    kind:'body_anterior',kind_ja:'椎体の前方輪郭の候補',
    ...output
  };
  const j=anatomicalReviewJson([row],{source_mask_sha256:'m123',ct_sha256:'c456'});
  assert.equal(j.ready_for_anatomical_approval,false);
  assert.equal(j.items[0].reviewer_confirmation,'unverified_candidate');
  assert.deepEqual(j.items[0].world_ras_mm,[18.5,11.2,53]);
  passed++;
}
// RAS physical coordinates must derive from original 4x4, not pixel-axis names.
const reflected=[[-.5,0,0,90],[0,-.6,0,50],[0,0,1,30],[0,0,0,1]];
assert.deepEqual(voxelWorld([17,52,23],reflected),[81.5,18.8,53]);
assert.throws(()=>pointFromImageClick('axial',{x:50,y:205},{...imageRect,naturalWidth:180,naturalHeight:140},grid,23),/outside CT/);
assert.throws(()=>pointFromImageClick('axial',{x:500,y:300},{...imageRect,naturalWidth:180,naturalHeight:140},grid,23),/outside CT/);
assert.throws(()=>pointFromImageClick('axial',{x:200,y:300},{...imageRect,naturalWidth:180,naturalHeight:140},grid,500),/Bad slice index/);
assert.throws(()=>planeAxes('unknown'),/Unknown CT plane/);
console.log('L3_LANDMARK_COORDINATE_TEST_PASS '+JSON.stringify({orthogonal_planes_checked:passed,voxel_to_RAS_matched:true,letterbox_rejection:true,LPS_world_affine_tested:true,landmarks_not_approved:true}));
