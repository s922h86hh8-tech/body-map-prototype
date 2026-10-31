// L3 v2.8 root-cause gate regression. Run from repository root:
// node experiments/tests/l3-v2.8-root-cause-regression.cjs
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const exp=path.resolve(__dirname,'..');
const baseline=fs.readFileSync(path.join(exp,'cleanroom-lumbar-mesh-worker-v2.4.js'),'utf8');
const current=fs.readFileSync(path.join(exp,'cleanroom-lumbar-mesh-worker-v2.8.js'),'utf8');
const html=fs.readFileSync(path.join(exp,'cleanroom-l3-anatomical-review-v2.8.html'),'utf8');
const embedded=html.match(/<script type="module">([\s\S]*?)<\/script>/);
assert(embedded,'HTML module missing');
new vm.Script(embedded[1].replace(/^import .*$/gm,''));
assert.match(html,/displayRootCauseV28\(selected\)/);
assert.match(html,/cleanroom-lumbar-mesh-worker-v2\.8\.js/);
function render(src,quality){
 let result;
 const ctx={self:{postMessage:x=>{result=x}},console};
 vm.runInNewContext(src,ctx);
 ctx.self.onmessage({data:{id:1,level:'L3',quality,variant:'loft24'}});
 assert(result&&!result.error,result?.error||'No worker result');
 return result;
}
const observations=[];
for(const quality of ['standard','high']){
 const prior=render(baseline,quality),currentResult=render(current,quality);
 for(const name of ['positions','indices','colors']){
  const a=prior[name],b=currentResult[name];assert.equal(a.length,b.length);
  for(let i=0;i<a.length;i++)assert.equal(a[i],b[i],quality+' '+name+' '+i);
 }
 assert.equal(currentResult.qualityGate.allFourWithinFivePercent,true);
 assert.equal(currentResult.qualityGate.localPedicleFourWithinFivePercent,true);
 assert.equal(currentResult.qualityGate.anatomyForTeachingApproved,false);
 const a=currentResult.causeAudit;
 assert(a,'Cause analysis missing');
 assert.equal(a.standaloneL3.technicalMeshPassed,true);
 assert.equal(a.standaloneL3.numericScreenPassed,true);
 assert.equal(a.standaloneL3.readyForIndependentAnatomyApproval,false);
 assert.equal(a.standaloneL3.approvalGranted,false);
 assert.equal(a.applicationToL2L4.approved,false);
 assert.equal(a.causes.length,8);
 const blockers=Array.from(a.standaloneL3.blockers).sort();
 assert.deepEqual(blockers,['EXPERT_REVIEW','FACET_CURVATURE','FACET_IDENTIFICATION','PEDICLE_AXIS','REFERENCE_SHAPE']);
 assert.equal(a.causes.find(c=>c.code==='NEIGHBOR_JOINT').level,'隣接椎骨への展開');
 assert.equal(currentResult.pedicleAxisProxy.centerlineIndependentlyAnatomical,false);
 assert.equal(currentResult.pedicleAxisProxy.ctReferenceRegistered,false);
 observations.push({quality,vertices:currentResult.vertices,triangles:currentResult.triangles,geometryExactlyUnchanged:true,blockers});
}
console.log(JSON.stringify({technicalRegression:'PASS',independentAnatomyApproval:'NOT YET',observations},null,2));
