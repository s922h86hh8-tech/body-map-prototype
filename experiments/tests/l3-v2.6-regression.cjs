// L3 v2.6 strict regression: exact geometry identity with v2.4 and repeatable sweep.
// Run from repo root: node experiments/tests/l3-v2.6-regression.cjs
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const base=path.resolve(__dirname,'..');
const src24=fs.readFileSync(path.join(base,'cleanroom-lumbar-mesh-worker-v2.4.js'),'utf8');
const src26=fs.readFileSync(path.join(base,'cleanroom-lumbar-mesh-worker-v2.6.js'),'utf8');
const html=fs.readFileSync(path.join(base,'cleanroom-l3-anatomical-review-v2.6.html'),'utf8');
assert.match(html,/cleanroom-lumbar-mesh-worker-v2\.6\.js/);
const code=html.match(/<script type="module">([\s\S]*?)<\/script>/);
assert(code,'html module script missing');
new vm.Script(code[1].replace(/^import .*$/gm,''));
function generate(src,quality){
 let response=null;
 const ctx={self:{postMessage:d=>{response=d}},console};
 vm.runInNewContext(src,ctx,{filename:'worker.js'});
 ctx.self.onmessage({data:{id:1,level:'L3',quality,variant:'loft24'}});
 assert(response&&!response.error,response?.error||'no response');
 return response;
}
const report=[];
for(const q of ['standard','high']){
 const a=generate(src24,q),b=generate(src26,q);
 for(const key of ['positions','indices','colors']){
  assert.equal(a[key].length,b[key].length,key+' length');
  for(let i=0;i<a[key].length;i++)assert.equal(b[key][i],a[key][i],key+' element '+i);
 }
 for(const key of ['vertices','triangles'])assert.equal(b[key],a[key]);
 assert.equal(b.topology.components,1);
 for(const k of ['boundary','nonManifold','zero','nonFinite'])assert.equal(b.topology[k],0);
 assert.equal(b.qualityGate.allFourWithinFivePercent,true);
 assert.equal(b.qualityGate.localPedicleFourWithinFivePercent,true);
 assert.equal(b.qualityGate.anatomyForTeachingApproved,false);
 const p=b.pedicleSweep;
 assert(p&&p.rows.length===9&&p.sides.length===2&&p.allCrossSectionsHaveTwoRayHits);
 assert.equal(p.measuredPedicleAnatomicAxis,false);
 assert.equal(p.measuredAxisNormalIsthmus,false);
 assert.equal(p.referenceSpecimenCompared,false);
 assert.equal(p.medicallyApproved,false);
 assert.equal(p.anyMinimumAtSearchBoundary,true,'scan minimum must warn at search boundary for current geometry');
 assert(p.sides.some(x=>x.minimumWidthAtSearchBoundary),'boundary flag must be shown');
 for(const s of p.sides){
  assert(Number.isFinite(s.sampledMinWidthMM)&&Number.isFinite(s.sampledMinHeightMM));
  assert(s.samplesWidth===9&&s.samplesHeight===9);
 }
 report.push({quality:q,vertices:b.vertices,triangles:b.triangles,exactIdentity:true,
  sampledWidthHeightMin:p.sides.map(s=>({side:s.side,width:s.sampledMinWidthMM,
   widthY:s.sampledMinWidthY,height:s.sampledMinHeightMM,heightY:s.sampledMinHeightY}))});
}
console.log(JSON.stringify({result:'TECHNICAL PASS',anatomicalApproval:'NOT ESTABLISHED',report},null,2));
