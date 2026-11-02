// Research-only regression for inferior articular process candidate v3.5.
// This is NOT a validation of CT-based anatomical accuracy.
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const read=name=>fs.readFileSync(path.join(root,name),'utf8');
const src24=read('cleanroom-lumbar-mesh-worker-v2.4.js');
const src33=read('cleanroom-lumbar-mesh-worker-v3.3-research.js');
const src35=read('cleanroom-lumbar-mesh-worker-v3.5-research.js');
function run(source,quality,variant){
 let output=null;
 const ctx={self:{postMessage:d=>{output=d}},console,Date,Math};
 vm.runInNewContext(source,ctx);
 ctx.self.onmessage({data:{id:1,level:'L3',quality,variant}});
 assert(output&&!output.error,output?.error||'no output');
 return output;
}
const result=[];
for(const quality of ['standard','high']){
 const baseline=run(src24,quality,'loft24');
 const old=run(src35,quality,'loft24');
 const previous=run(src33,quality,'loft33');
 const carried=run(src35,quality,'loft33');
 const candidate=run(src35,quality,'loft35');
 for(const [a,b] of [[baseline,old],[previous,carried]]){
  for(const key of ['positions','indices','colors']){
   assert.equal(a[key].length,b[key].length,key+' length');
   for(let i=0;i<a[key].length;i++)assert.equal(a[key][i],b[key][i],key+' '+i);
  }
 }
 assert.equal(candidate.topology.components,1);
 for(const key of ['boundary','nonManifold','zero','nonFinite'])assert.equal(candidate.topology[key],0,key);
 assert.equal(candidate.qualityGate.allFourWithinFivePercent,true);
 assert.equal(candidate.qualityGate.localPedicleFourWithinFivePercent,true);
 assert.equal(candidate.qualityGate.anatomyForTeachingApproved,false);
 assert(candidate.triangles>previous.triangles,'expect added inferior geometry');
 const minZ=mesh=>{let x=Infinity;for(let i=2;i<mesh.positions.length;i+=3)x=Math.min(x,mesh.positions[i]);return x};
 assert(minZ(candidate)<minZ(previous)-1,'expected inferior z extension');
 result.push({quality,baselineTri:baseline.triangles,priorTri:previous.triangles,
   trialTri:candidate.triangles,inferiorExtensionModelUnits:minZ(previous)-minZ(candidate)});
}
console.log(JSON.stringify({status:'TECHNICAL RESEARCH REGRESSION PASS',
  anatomicalApproval:'NOT VERIFIED',result},null,2));
