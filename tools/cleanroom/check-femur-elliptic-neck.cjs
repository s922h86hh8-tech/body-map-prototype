'use strict';
// Execute geometry and registered control callbacks from the real standalone
// page. This is not a browser, WebGL rendering test, or anatomical approval.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const assert=require('node:assert/strict'),{createHash}=require('node:crypto');
const root=path.resolve(__dirname,'../..');
const pagePath='experiments/cleanroom-femur-study-v0.4.html';
const page=fs.readFileSync(path.join(root,pagePath),'utf8');
const hash=s=>createHash('sha256').update(s).digest('hex');
assert.equal(hash(fs.readFileSync(path.join(root,'experiments/cleanroom-femur-study-v0.3.html'))),
  '744dd83db04d0735e395e4c5684ee130489ac4e8c69feac4651275f5eeef13e7');
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
assert.deepEqual(model,JSON.parse(fs.readFileSync(path.join(root,'assets/cleanroom/femur-shape-parameters.v0.3.json'),'utf8')));
const mesh=get('mesh');
const neck=model.primitives.find(p=>p.name==='neck'),e=neck.crossSection;
const dot3=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
assert.ok(Math.abs(Math.hypot(...e.u)-1)<1e-12&&Math.abs(Math.hypot(...e.v)-1)<1e-12);
assert.ok(Math.abs(dot3(e.u,e.v))<1e-12);
assert.ok(Math.abs(e.scaleU*e.scaleV-1)<1e-12);
const axis=neck.b.map((v,i)=>v-neck.a[i]),axisLength=Math.hypot(...axis);
assert.ok(Math.abs(dot3(e.u,axis))<1e-12&&Math.abs(dot3(e.v,axis))<1e-12);
const neckCenter=neck.a.map((v,i)=>(v+neck.b[i])/2),radius=(neck.r0+neck.r1)/2;
for(const [dir,scale] of [[e.u,e.scaleU],[e.v,e.scaleV]]){
 const p=neckCenter.map((v,i)=>v+radius*scale*dir[i]);
 assert.ok(Math.abs(get('distance('+JSON.stringify(p)+',MODEL.primitives[1])'))<1e-10);
}
buttons.find(b=>b.dataset.feature==='2').onclick();
assert.deepEqual(JSON.parse(JSON.stringify(get('({mode,framing,selected,zoom})'))),
 {mode:'oblique',framing:'surface',selected:2,zoom:1});

function inspect(m,coordinateScale=1){
  const p=m.positions,t=m.indices,V=p.length/3,edges=new Map(),parent=Array.from({length:V},(_,i)=>i);
  const find=x=>{while(parent[x]!==x){parent[x]=parent[parent[x]];x=parent[x]}return x};
  let volume=0,zeroArea=0,nearZeroArea=0,minDoubleArea=Infinity;
  assert.ok([...p,...m.normals].every(Number.isFinite));
  for(let k=0;k<t.length;k+=3){
    const ids=[t[k],t[k+1],t[k+2]];assert.ok(ids.every(i=>i<V));
    const [a,b,c]=ids.map(i=>Array.from(p.slice(i*3,i*3+3)));
    const u=b.map((v,i)=>v-a[i]),v=c.map((x,i)=>x-a[i]);
    const doubleArea=Math.hypot(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]);
    if(doubleArea===0)zeroArea++;
    if(doubleArea<1e-10*coordinateScale*coordinateScale)nearZeroArea++;
    minDoubleArea=Math.min(minDoubleArea,doubleArea);
    volume+=(a[0]*(b[1]*c[2]-b[2]*c[1])+a[1]*(b[2]*c[0]-b[0]*c[2])+a[2]*(b[0]*c[1]-b[1]*c[0]))/6;
    for(let j=0;j<3;j++){const x=ids[j],y=ids[(j+1)%3],key=x<y?x+':'+y:y+':'+x;
      edges.set(key,(edges.get(key)||0)+1);parent[find(x)]=find(y)}
  }
  return {vertices:V,triangles:t.length/3,components:new Set(parent.map((_,i)=>find(i))).size,
    badEdges:[...edges.values()].filter(v=>v!==2).length,zeroAreaTriangles:zeroArea,
    nearZeroAreaTriangles:nearZeroArea,minDoubleArea,
    eulerCharacteristic:V-edges.size+t.length/3,signedVolumeDrawingUnits:volume};
}
const geometry=inspect(mesh);
assert.equal(geometry.components,1);assert.equal(geometry.badEdges,0);
assert.equal(geometry.zeroAreaTriangles,0);assert.equal(geometry.eulerCharacteristic,2);
assert.equal(geometry.nearZeroAreaTriangles,0);
assert.ok(geometry.signedVolumeDrawingUnits>0);assert.ok(geometry.vertices<=65535);
// Compare with the same authored additions but without the subtraction.
vm.runInContext('const savedCavities=MODEL.cavities;MODEL.cavities=[];var uncarvedMesh=buildMesh();MODEL.cavities=savedCavities;',context,{timeout:60000});
const uncarved=inspect(get('uncarvedMesh'));
assert.ok(geometry.signedVolumeDrawingUnits<uncarved.signedVolumeDrawingUnits);
let fossaVertices=0,normalsTowardVoid=0;
const center=model.cavities[0].c;
for(let i=0;i<mesh.parts.length;i++)if(mesh.parts[i]===5){
  fossaVertices++;let d=0;for(let k=0;k<3;k++)d+=mesh.normals[3*i+k]*(center[k]-mesh.positions[3*i+k]);
  if(d>0)normalsTowardVoid++;
}
assert.ok(fossaVertices>30);assert.ok(normalsTowardVoid/fossaVertices>.95);
for(const [name,label] of [['front','前から'],['back','後ろから'],['lateral','外側から'],['oblique','斜めから'],['medial','内側から'],['posteromedial','後内側から']]){
  buttons.find(b=>b.dataset.view===name).onclick();assert.equal(node('#view-label').textContent,label);
}
buttons.find(b=>b.dataset.feature==='5').onclick();
assert.deepEqual(JSON.parse(JSON.stringify(get('({mode,framing,selected,zoom})'))),
  {mode:'posteromedial',framing:'surface',selected:5,zoom:1});
node('#reset').onclick();
assert.deepEqual(JSON.parse(JSON.stringify(get('({mode,framing,zoom})'))),{mode:'back',framing:'whole',zoom:1});
const gltf=JSON.parse(JSON.stringify(get('makeGLTF()')));
assert.equal(gltf.asset.version,'2.0');assert.equal(gltf.asset.extras.physicalScaleValidated,false);
assert.equal(gltf.asset.extras.anatomyAudit,'pending');
const bytes=Buffer.from(gltf.buffers[0].uri.split(',')[1],'base64');
assert.equal(bytes.length,gltf.buffers[0].byteLength);
assert.equal(gltf.accessors[0].count,geometry.vertices);
assert.equal(gltf.accessors[2].count,geometry.triangles*3);
const positionView=gltf.bufferViews[0],normalView=gltf.bufferViews[1],indexView=gltf.bufferViews[2];
const exported={positions:new Float32Array(bytes.buffer,bytes.byteOffset+positionView.byteOffset,geometry.vertices*3),
  normals:new Float32Array(bytes.buffer,bytes.byteOffset+normalView.byteOffset,geometry.vertices*3),
  indices:new Uint16Array(bytes.buffer,bytes.byteOffset+indexView.byteOffset,geometry.triangles*3)};
const exportGeometry=inspect(exported,1/200);
assert.equal(exportGeometry.badEdges,0);assert.equal(exportGeometry.zeroAreaTriangles,0);
assert.equal(exportGeometry.nearZeroAreaTriangles,0);
assert.ok(exportGeometry.signedVolumeDrawingUnits>0);
const gltfPath='assets/cleanroom/right-proximal-femur-study.v0.3.gltf';
fs.writeFileSync(path.join(root,gltfPath),JSON.stringify(gltf));
if(process.env.BODYMAP_MESH_DUMP)fs.writeFileSync(process.env.BODYMAP_MESH_DUMP,JSON.stringify({
  positions:Array.from(mesh.positions),normals:Array.from(mesh.normals),indices:Array.from(mesh.indices),parts:Array.from(mesh.parts)}));
console.log(JSON.stringify({status:'passed',scope:'Elliptic-neck geometry, basis and control callbacks; no browser rendering',ellipticBasisChecks:'unit, perpendicular, area-product and isolated boundary points passed',
  geometry,fossa:{vertices:fossaVertices,normalsTowardVoid,removedVolumeDrawingUnits:uncarved.signedVolumeDrawingUnits-geometry.signedVolumeDrawingUnits,
  openSurfaceEvidence:'One connected closed genus-zero mesh, no separate enclosed cavity component'},
  controls:['six view callbacks','schematic fossa selection and close view','reset to whole posterior'],
  exportGeometry,files:{page:{path:pagePath,sha256:hash(page)},gltf:{path:gltfPath,sha256:hash(JSON.stringify(gltf))}},
  anatomyAccuracy:'not approved',physicalScaleValidated:false,browserRendering:'not tested by this script',iPhoneNewVersion:'not tested'},null,2));

