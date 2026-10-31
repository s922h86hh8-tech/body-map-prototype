// L3 v2.5 regression test. Run at repo root: node experiments/tests/l3-v2.5-regression.cjs
// Tests geometry/mesh and facet-normal *proxy* only; never grants anatomical approval.
'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const base=path.resolve(__dirname,'..');
const workerSource=fs.readFileSync(path.join(base,'cleanroom-lumbar-mesh-worker-v2.4.js'),'utf8');
const html=fs.readFileSync(path.join(base,'cleanroom-l3-anatomical-review-v2.5.html'),'utf8');
const moduleMatch=html.match(/<script type="module">([\s\S]*?)<\/script>/);
assert(moduleMatch,'missing module');
const moduleText=moduleMatch[1].replace(/^import .*$/gm,'');
new vm.Script(moduleText);
assert.match(html,/facetNormalProxy\(data\.positions,data\.indices\)/);
assert.match(html,/displayFacetProxyV25\(selected\)/);
assert.match(html,/cleanroom-lumbar-mesh-worker-v2\.4\.js/);
const from=moduleText.indexOf('function facetNormalProxy(');
const to=moduleText.indexOf('\nfunction ',from+10);
assert(from>=0 && to>from,'missing facet function');
const proxy=new Function(moduleText.slice(from,to)+';return facetNormalProxy;')();
const report=[];
for(const quality of ['standard','high']){
 const result=[];
 const sandbox={self:{postMessage:x=>result.push(x)},Date,Math,Number,Array,Object,Map,Set,Float32Array,Float64Array,Uint8Array,Uint32Array,console};
 vm.runInNewContext(workerSource,sandbox);
 sandbox.self.onmessage({data:{id:1,level:'L3',quality,variant:'loft24'}});
 const d=result.at(-1);
 assert(d && !d.error,d?.error||'missing geometry');
 assert.equal(d.topology.components,1);
 for(const k of ['boundary','nonManifold','zero','nonFinite'])assert.equal(d.topology[k],0,k);
 assert.equal(d.qualityGate.allFourWithinFivePercent,true);
 assert.equal(d.qualityGate.localPedicleFourWithinFivePercent,true);
 assert.equal(d.qualityGate.anatomyForTeachingApproved,false);
 if(quality==='standard'){assert.equal(d.vertices,14792);assert.equal(d.triangles,29584)}
 else{assert.equal(d.vertices,21826);assert.equal(d.triangles,43652)}
 const f=proxy(d.positions,d.indices);
 assert.equal(f.measured,true);
 assert.equal(f.qualitativeSignsMatch,true);
 assert.equal(f.independentSpecimenValidation,false);
 assert.equal(f.curvatureValidated,false);
 assert.equal(f.teachingApproved,false);
 for(const r of f.regions){
  assert(r.faceCount>=20);
  assert(Number.isFinite(r.dispersionDegrees));
  assert(Number.isFinite(r.sensitivityDegrees));
 }
 report.push({quality,vertices:d.vertices,triangles:d.triangles,facetROIs:f.regions.length,
  directionProxy:f.qualitativeSignsMatch,anatomyApproved:false});
}
console.log(JSON.stringify({technicalRegression:'PASS',anatomicalApproval:'NOT VALIDATED',report},null,2));
