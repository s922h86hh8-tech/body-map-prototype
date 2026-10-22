'use strict';
// Measure procedural surface diagnostics from the pinned standalone page.
// This is not a browser, WebGL rendering test, or anatomical approval.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),{createHash}=require('node:crypto');
const root=path.resolve(__dirname,'../..');
const pagePath='experiments/cleanroom-femur-study-v0.3.html';
const page=fs.readFileSync(path.join(root,pagePath),'utf8');
const hash=s=>createHash('sha256').update(s).digest('hex');
assert.equal(/<script[^>]+src=|<link[^>]+stylesheet|@import|fetch\(/i.test(page),false);
const nodes=new Map(),buttons=[];
const node=key=>{if(!nodes.has(key))nodes.set(key,{style:{},dataset:{},textContent:'',disabled:false,
  attributes:{},listeners:{},setAttribute(k,v){this.attributes[k]=v},
  addEventListener(k,v){this.listeners[k]=v},getContext(){return null}});return nodes.get(key)};
for(const m of page.matchAll(/<button\b([^>]*)>([^<]*)<\/button>/g)){
  const b=node('button:'+buttons.length);b.textContent=m[2];
  for(const a of m[1].matchAll(/([\w-]+)="([^"]*)"/g)){
    if(a[1].startsWith('data-'))b.dataset[a[1].slice(5)]=a[2];
    else b.attributes[a[1]]=a[2];
    if(a[1]==='id')nodes.set('#'+a[2],b);
  }buttons.push(b);
}
const body=node('body');
const document={body,querySelector:s=>node(s),querySelectorAll:s=>{
  const match=s.match(/^\[data-(\w+)\]$/);if(!match)throw Error('Unsupported test selector '+s);
  return buttons.filter(b=>match[1] in b.dataset);
}};
const context=vm.createContext({document,window:{addEventListener(){}},console,
  requestAnimationFrame(){},setTimeout(){},devicePixelRatio:1,
  btoa:s=>Buffer.from(s,'binary').toString('base64')});
const script=page.match(/<script>([\s\S]*?)<\/script>/)[1];
vm.runInContext(script,context,{timeout:10000});
vm.runInContext('mesh=buildMesh()',context,{timeout:60000});
const get=s=>vm.runInContext(s,context,{timeout:10000});
const model=JSON.parse(JSON.stringify(get('MODEL')));
assert.deepEqual(model,JSON.parse(fs.readFileSync(path.join(root,'assets/cleanroom/femur-shape-parameters.v0.2.json'),'utf8')));
const mesh=get('mesh');

assert.equal(hash(page),'744dd83db04d0735e395e4c5684ee130489ac4e8c69feac4651275f5eeef13e7',
 'Input changed: review the evaluation method before reusing it.');
const add=(a,b)=>a.map((v,i)=>v+b[i]),sub=(a,b)=>a.map((v,i)=>v-b[i]);
const mul=(a,t)=>a.map(v=>v*t),dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
const norm=a=>Math.hypot(...a),unit=a=>mul(a,1/norm(a));
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const point=i=>Array.from(mesh.positions.slice(3*i,3*i+3));
function solve(A,b){
 const M=A.map((r,i)=>[...r,b[i]]),N=b.length;
 for(let i=0;i<N;i++){
  let pivot=i;for(let j=i+1;j<N;j++)if(Math.abs(M[j][i])>Math.abs(M[pivot][i]))pivot=j;
  assert.ok(Math.abs(M[pivot][i])>1e-12,'Degenerate sphere fit');
  [M[i],M[pivot]]=[M[pivot],M[i]];
  const d=M[i][i];for(let k=i;k<=N;k++)M[i][k]/=d;
  for(let j=0;j<N;j++)if(j!==i){const f=M[j][i];for(let k=i;k<=N;k++)M[j][k]-=f*M[i][k]}
 }return M.map(r=>r[N]);
}
function fitSphere(points){
 assert.ok(points.length>=4);
 // Recenter before algebraic least squares: equal vertex weights, not area weights.
 const origin=points.reduce((s,p)=>add(s,mul(p,1/points.length)),[0,0,0]);
 const A=Array.from({length:4},()=>[0,0,0,0]),b=[0,0,0,0];
 for(const p of points){const q=sub(p,origin),r=[2*q[0],2*q[1],2*q[2],1],v=dot(q,q);
  for(let j=0;j<4;j++){b[j]+=r[j]*v;for(let k=0;k<4;k++)A[j][k]+=r[j]*r[k]}}
 const x=solve(A,b),c=x.slice(0,3),center=add(origin,c),radius=Math.sqrt(x[3]+dot(c,c));
 const residuals=points.map(p=>norm(sub(p,center))-radius);
 return {vertices:points.length,center,radius,rmsRadialResidual:Math.sqrt(residuals.reduce((s,x)=>s+x*x,0)/points.length),
 maxAbsoluteRadialResidual:Math.max(...residuals.map(Math.abs))};
}
function section(positions,indices,origin,normal){
 const nodes=new Map(),segments=new Map();
 function node(p){const key=p.map(x=>Math.round(x*1e6)).join(':');if(!nodes.has(key))nodes.set(key,{p,neighbors:new Set()});return key}
 for(let i=0;i<indices.length;i+=3){
  const tri=Array.from(indices.slice(i,i+3),j=>Array.from(positions.slice(j*3,j*3+3))),hits=[];
  for(let j=0;j<3;j++){const a=tri[j],b=tri[(j+1)%3],da=dot(sub(a,origin),normal),db=dot(sub(b,origin),normal);
   if(Math.abs(da)<1e-9)hits.push(a);
   if(da*db<0)hits.push(add(a,mul(sub(b,a),da/(da-db))));
  }
  const unique=[...new Map(hits.map(p=>[p.map(x=>Math.round(x*1e6)).join(':'),p])).values()];
  if(unique.length!==2)continue;
  const [a,b]=unique.map(node),key=[a,b].sort().join('|');if(a===b||segments.has(key))continue;
  segments.set(key,[a,b]);nodes.get(a).neighbors.add(b);nodes.get(b).neighbors.add(a);
 }
 assert.ok(segments.size,'Plane did not intersect mesh');
 let length=0,centroid=[0,0,0];
 for(const [a,b] of segments.values()){const p=nodes.get(a).p,q=nodes.get(b).p,L=norm(sub(p,q));length+=L;centroid=add(centroid,mul(add(p,q),L/2))}
 centroid=mul(centroid,1/length);
 const visited=new Set(),groups=[];
 for(const key of nodes.keys())if(!visited.has(key)){const group=[],stack=[key];visited.add(key);
 while(stack.length){const k=stack.pop();group.push(k);for(const v of nodes.get(k).neighbors)if(!visited.has(v)){visited.add(v);stack.push(v)}}groups.push(group)}
 const basisU=unit(cross(normal,Math.abs(normal[0])<.9?[1,0,0]:[0,1,0])),basisV=cross(normal,basisU);
 const contours=groups.map((keys,index)=>{
  const keySet=new Set(keys);let L=0,C=[0,0,0];
  for(const [a,b] of segments.values())if(keySet.has(a)&&keySet.has(b)){
   const p=nodes.get(a).p,q=nodes.get(b).p,l=norm(sub(p,q));L+=l;C=add(C,mul(add(p,q),l/2))}
  C=mul(C,1/L);
  const closed=keys.every(k=>nodes.get(k).neighbors.size===2);
  let containsAxisOrigin=null;
  if(closed){
   const ordered=[],seen=new Set();let current=keys[0],previous=null;
   while(!seen.has(current)){seen.add(current);ordered.push(nodes.get(current).p);
    const next=[...nodes.get(current).neighbors].find(k=>k!==previous);previous=current;current=next}
   assert.equal(ordered.length,keys.length);
   const xy=ordered.map(p=>[dot(sub(p,origin),basisU),dot(sub(p,origin),basisV)]);
   let inside=false;
   for(let i=0,j=xy.length-1;i<xy.length;j=i++){
    const [xi,yi]=xy[i],[xj,yj]=xy[j];
    if((yi>0)!==(yj>0)&&0<(xj-xi)*(-yi)/(yj-yi)+xi)inside=!inside;
   }containsAxisOrigin=inside;
  }
  return {index,closed,vertices:keys.length,perimeter:L,perimeterWeightedCentroid:C,containsAxisOrigin,
   centroidToConstructionAxisDistance:norm(sub(C,origin))};
 });
 const candidates=contours.filter(c=>c.closed&&c.containsAxisOrigin);
 return {origin,normal,segments:segments.size,components:groups.length,nonDegreeTwoNodes:[...nodes.values()].filter(x=>x.neighbors.size!==2).length,
 perimeter:length,perimeterWeightedCentroid:centroid,centroidToConstructionAxisDistance:norm(sub(centroid,origin)),contours,
 axisContainingContourCandidate:candidates.length===1?candidates[0]:null,
 anatomicalAxisApproved:false};
}
function rayTriangle(o,d,a,b,c){
 const e1=sub(b,a),e2=sub(c,a),p=cross(d,e2),det=dot(e1,p);
 if(Math.abs(det)<1e-10)return null;
 const inv=1/det,tv=sub(o,a),u=dot(tv,p)*inv;if(u < -1e-9 || u>1+1e-9)return null;
 const q=cross(tv,e1),v=dot(d,q)*inv;if(v < -1e-9 || u+v>1+1e-9)return null;
 const t=dot(e2,q)*inv;return t>=0?t:null;
}
function meshHits(o,d){
 const hits=[];for(let i=0;i<mesh.indices.length;i+=3){
 const t=rayTriangle(o,d,...Array.from(mesh.indices.slice(i,i+3),point));if(t!==null)hits.push(t)}
 return hits.sort((a,b)=>a-b).filter((x,i,a)=>!i||x-a[i-1]>1e-6);
}
function firstFieldEntry(fn,o,d){
 let a=0,fa=fn(o);assert.ok(fa>0,'Ray must start outside');
 for(let b=.25;b<=160;b+=.25){const fb=fn(add(o,mul(d,b)));if(fa>0&&fb<=0){
  for(let i=0;i<50;i++){const mid=(a+b)/2;if(fn(add(o,mul(d,mid)))>0)a=mid;else b=mid}
  const t=(a+b)/2;return {distanceFromRayOrigin:t,position:add(o,mul(d,t))};
 }a=b;fa=fb}return null;
}
// Independent analytic checks for numeric routines.
const knownCenter=[3,-2,5],knownRadius=7;
const sphereTest=fitSphere([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]].map(p=>add(knownCenter,mul(p,knownRadius))));
assert.ok(norm(sub(sphereTest.center,knownCenter))<1e-10&&Math.abs(sphereTest.radius-knownRadius)<1e-10);
assert.ok(Math.abs(rayTriangle([.2,.2,1],[0,0,-1],[0,0,0],[1,0,0],[0,1,0])-1)<1e-10);
assert.equal(rayTriangle([2,2,1],[0,0,-1],[0,0,0],[1,0,0],[0,1,0]),null);
const octa={positions:[1,0,0,-1,0,0,0,1,0,0,-1,0,0,0,1,0,0,-1],
 indices:[0,2,4,2,1,4,1,3,4,3,0,4,2,0,5,1,2,5,3,1,5,0,3,5]};
const octaSection=section(octa.positions,octa.indices,[0,0,.2],[0,0,1]);
assert.equal(octaSection.components,1);assert.equal(octaSection.nonDegreeTwoNodes,0);
assert.ok(norm(sub(octaSection.perimeterWeightedCentroid,[0,0,.2]))<1e-10);
assert.ok(Math.abs(octaSection.perimeter-4*Math.SQRT2*.8)<1e-10);
assert.ok(octaSection.axisContainingContourCandidate?.containsAxisOrigin);
const shifted=octa.positions.map((v,i)=>i%3===0?v+4:v);
const twoSection=section([...octa.positions,...shifted],[...octa.indices,...octa.indices.map(i=>i+6)],[0,0,.2],[0,0,1]);
assert.equal(twoSection.components,2);
assert.ok(twoSection.axisContainingContourCandidate?.containsAxisOrigin);
assert.ok(norm(sub(twoSection.axisContainingContourCandidate.perimeterWeightedCentroid,[0,0,.2]))<1e-10);
const outsideSection=section(octa.positions,octa.indices,[10,0,.2],[0,0,1]);
assert.equal(outsideSection.axisContainingContourCandidate,null);
const rootTest=firstFieldEntry(p=>norm(p)-2,[5,0,0],[-1,0,0]);
assert.ok(Math.abs(rootTest.distanceFromRayOrigin-3)<1e-10);

const head=model.primitives.find(p=>p.name==='head');
const headPoints=Array.from(mesh.parts,(part,i)=>part===1?point(i):null).filter(Boolean);
const headFits=[{selection:'nearest-primitive label 1; entire authored region',...fitSphere(headPoints)}];
for(const tolerance of [.5,1,2]){
 const selected=headPoints.filter(p=>Math.abs(norm(sub(p,head.c))-head.r[0])<=tolerance);
 headFits.push({selection:'label 1 and distance to authored sphere within tolerance',toleranceDrawingUnits:tolerance,...fitSphere(selected)});
}
const slices={};
for(const key of ['neck','proximalShaft']){
 const axis=model.constructionAxes[key],normal=unit(sub(axis.b,axis.a));
 slices[key]=[.25,.5,.75].map(fraction=>({fraction,...section(mesh.positions,mesh.indices,add(axis.a,mul(sub(axis.b,axis.a),fraction)),normal)}));
}
const fossaPoints=Array.from(mesh.parts,(part,i)=>part===5?point(i):null).filter(Boolean);
assert.ok(fossaPoints.length);
const gt=model.primitives.find(p=>p.name==='greater_trochanter'),cavity=model.cavities[0];
const out=unit(sub(cavity.c,gt.c)),rayOrigin=add(cavity.c,mul(out,80)),rayDirection=mul(out,-1);
const fields=get('({field,solid,cutZ:MODEL.cutZ})');
const carved=firstFieldEntry(fields.field,rayOrigin,rayDirection);
const uncarved=firstFieldEntry(p=>Math.max(fields.solid(p),fields.cutZ-p[2]),rayOrigin,rayDirection);
const intersections=meshHits(rayOrigin,rayDirection);
assert.ok(carved&&uncarved&&intersections.length>=2);
const result={
 schema:'body-map-surface-diagnostics-v0.1',auditDate:'2026-10-22',status:'calculation completed; anatomical approval withheld',
 page:{path:pagePath,sha256:hash(page)},parameters:{path:'assets/cleanroom/femur-shape-parameters.v0.2.json',
 sha256:hash(fs.readFileSync(path.join(root,'assets/cleanroom/femur-shape-parameters.v0.2.json')))},
 scriptSha256:hash(fs.readFileSync(__filename)),units:'arbitrary drawing units, not mm',
 mesh:{vertices:mesh.positions.length/3,triangles:mesh.indices.length/3},
 numericSelfChecks:['known sphere center/radius','ray triangle hit/miss','octahedron closed section, centroid/perimeter and containing contour','two disjoint contours and correct enclosing-contour selection','no enclosing contour rejected','sphere field entry'],
 headFits,
 sections:{method:'whole-mesh plane intersections; segment-length-weighted contour centroid; planes from authored axes',values:slices},
 fossaLabelRegion:{vertices:fossaPoints.length,min:[0,1,2].map(k=>Math.min(...fossaPoints.map(p=>p[k]))),
 max:[0,1,2].map(k=>Math.max(...fossaPoints.map(p=>p[k]))),meaning:'procedural label 5, not audited anatomical fossa boundary'},
 fossaDirectionalProfile:{method:'ray through cavity center, directed from outside toward greater-trochanter construction center',
 rayOrigin,rayDirection,carvedFieldEntry:carved,uncarvedFieldEntry:uncarved,
 directionalRecession:carved.distanceFromRayOrigin-uncarved.distanceFromRayOrigin,
 meshIntersectionDistances:intersections,firstMeshVsFieldDifference:intersections[0]-carved.distanceFromRayOrigin},
 limitations:['author-derived labels and planes; no independent anatomical segmentation',
 'vertex-weighted algebraic sphere fit; no area weighting or clinical validation',
 'section centroid is a contour statistic, not a validated neck or shaft axis',
 'one directional ray is not maximum fossa depth or tendon footprint',
 'no anatomical tolerance, clinical angle or physical scale approval; iPhone not tested'],
 anatomicalApproval:false,physicalScaleValidated:false,iPhoneNewVersion:'not tested'
};
console.log(JSON.stringify(result,null,2));
