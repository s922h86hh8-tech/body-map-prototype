/* Synthetic-only UI orientation tests: never a review of patient anatomy. */
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
require('../l3-verse-orientation-coordinates-v7.3.js');
const {pointFromPixel,pixelFromClick,provisionalAPCheck,basis}=globalThis.L3V73_COORDS;
let checks=0;
const n=41,mid=20,center=[12,-18,35];
for(const name of ['axial','coronal','sagittal']){
 assert.deepEqual(pointFromPixel(name,mid,mid,n,1,center),center);
 assert.deepEqual(pointFromPixel(name,mid+1,mid,n,1,center),
   center.map((v,i)=>v+basis[name].right[i]));
 assert.deepEqual(pointFromPixel(name,mid,mid-1,n,1,center),
   center.map((v,i)=>v+basis[name].up[i]));
 checks+=3;
}
assert.equal(pointFromPixel('sagittal',mid-1,mid,n,1,center)[1],center[1]-1);checks++;
const rect={left:10,top:15,width:410,height:410};
assert.deepEqual(pixelFromClick('sagittal',{x:220,y:220},rect,n),{x:21,y:20});checks++;
assert.throws(()=>pixelFromClick('axial',{x:9,y:220},rect,n),/outside CT/);checks++;
const sct='a'.repeat(64),ssg='b'.repeat(64);
const set=[
 {kind:'body_anterior',world_ras_mm:[0,19,3],source_ct_sha256:sct,source_seg_sha256:ssg},
 {kind:'spinous_posterior',world_ras_mm:[0,-15,3],source_ct_sha256:sct,source_seg_sha256:ssg},
];
const ok=provisionalAPCheck(set);
assert.equal(ok.status,'numeric_expected_order');
assert.equal(ok.ap_ras_mm,34);
assert.equal(ok.anatomy_approved,false);checks++;
const reversed=provisionalAPCheck([{...set[0],world_ras_mm:[0,-19,3]},{...set[1],world_ras_mm:[0,15,3]}]);
assert.equal(reversed.status,'numeric_reverse_warning');checks++;
assert.equal(provisionalAPCheck([set[0]]).status,'incomplete');checks++;
assert.equal(provisionalAPCheck([set[0],{...set[1],source_ct_sha256:'c'.repeat(64)}]).status,'invalid_source');checks++;
const html=fs.readFileSync(path.join(__dirname,'..','l3-verse-orientation-review-v7.3.html'),'utf8');
const match=html.match(/<script>\s*([\s\S]*?)<\/script>\s*<\/body>/);
assert.ok(match,'inline interaction script exists');
new vm.Script(match[1],{filename:'l3-verse-orientation-review-v7.3.html'});
assert.ok(html.includes('RAS') && html.includes('L3V73_COORDS'));checks++;
assert.ok(!/\bfetch\s*\(|\bXMLHttpRequest\b|\bsendBeacon\s*\(/.test(match[1]),'no network upload in inline review script');checks++;
console.log('L3_ORIENTATION_BROWSER_SOURCE_TEST_PASS '+JSON.stringify({
 synthetic_checks:checks,views:Object.keys(basis),script_parses:true,
 independent_anatomy_approval:false
}));
