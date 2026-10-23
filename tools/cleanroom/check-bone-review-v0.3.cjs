'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const {createCanvas}=require('@napi-rs/canvas');
const root=path.resolve(__dirname,'../..'),read=p=>fs.readFileSync(path.join(root,p),'utf8'),sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const base=read('experiments/cleanroom-bone-review-v0.2.html'),html=read('experiments/cleanroom-bone-review-v0.3.html');
assert.equal(sha(base),'9c863e23907a2d5d37911cb23a841203e06dfb10bb6dbed8520ebe79a84afc73');
const script=h=>h.match(/<script>([\s\S]*?)<\/script>/)[1];
assert.equal(script(base).split('function drawScene(')[0],script(html).split('// Original Canvas2D software rasterizer.')[0],'Geometry and preparation must remain unchanged');
const nodes=new Map(),buttons=[],surfaces=new Map(),jobs=[];
let viewport={width:400,height:360};
function node(id){if(!nodes.has(id)){const n={id,dataset:{},attrs:{},events:{},checked:true,setAttribute(k,v){this.attrs[k]=v},addEventListener(k,v){this.events[k]=v},getBoundingClientRect(){return viewport},getContext(){if(!surfaces.has(id))surfaces.set(id,createCanvas(1,1));return surfaces.get(id).getContext('2d')},setPointerCapture(){}};
for(const k of ['width','height'])Object.defineProperty(n,k,{get(){return surfaces.get(id)?.[k]},set(v){if(!surfaces.has(id))surfaces.set(id,createCanvas(1,1));surfaces.get(id)[k]=v}});nodes.set(id,n)}return nodes.get(id)}
for(const type of ['target','revision','pose','focus','quality'])for(const key of {target:['skull','lumbar'],revision:['new','old'],pose:['front','side','back','top','oblique'],focus:['orbit','arch','jaw','facets','spinous'],quality:['high','light']}[type]){const b=node(type+key);b.dataset[type]=key;buttons.push(b)}
const document={getElementById:node,querySelectorAll:s=>{const m=s.match(/^\[data-(.*)\]$/);return m?buttons.filter(b=>b.dataset[m[1]]):[]}};
const context=vm.createContext({document,window:{addEventListener(){}},devicePixelRatio:3,setTimeout:f=>jobs.push(f),console});vm.runInContext(script(html),context);
const get=s=>vm.runInContext(s,context,{timeout:180000});
const legacy=script(base).slice(script(base).indexOf('function drawScene('),script(base).indexOf('const $=id=>')).replace('function drawScene(','function drawSceneLegacy(');vm.runInContext(legacy,context);
const out=path.join(root,'docs/validation'),result={date:'2026-10-23',html_sha256:sha(html),base_html_sha256:sha(base),geometry_unchanged:true,iphone_tested:false,anatomical_approval:false,render_timings_ms:{}};
const compare=createCanvas(1200,1200),cc=compare.getContext('2d');cc.fillStyle='#192d36';cc.fillRect(0,0,1200,1200);
let row=0;
for(const [target,focus] of [['skull','orbit'],['lumbar','facets']]){
get(`viewState.target='${target}';viewState.revision='new';generate('${target}','new');describe();focusScene('${focus}')`);
const objects=get(`pool['${target}:new']`),expected=target==='skull'?[33425,66738]:[19817,39634];
assert.deepEqual([objects.reduce((n,o)=>n+o.verts.length,0),objects.reduce((n,o)=>n+o.faces.length,0)],expected);
get("drawSceneLegacy($('interactive'),viewState.yaw,viewState.pitch,viewState.zoom)");cc.drawImage(surfaces.get('interactive'),0,row*600,600,600);
let t=Date.now();get("drawScene($('interactive'),viewState.yaw,viewState.pitch,viewState.zoom)");result.render_timings_ms[target+'_high']=Date.now()-t;
assert.equal(node('interactive').width,1200);assert.equal(node('interactive').height,1080);
const high=surfaces.get('interactive').toBuffer('image/png'),pixels=surfaces.get('interactive').getContext('2d').getImageData(0,0,1200,1080).data;
assert.ok(pixels.filter((v,i)=>i%4===3&&v===255).length>50000,'Model must render visible pixels');cc.drawImage(surfaces.get('interactive'),600,row*600,600,600);
get("setDisplay('light')");assert.equal(node('interactive').width,400);assert.equal(node('interactive').height,360);assert.equal(node('qualitylight').attrs['aria-pressed'],'true');
get("setDisplay('high')");assert.equal(sha(surfaces.get('interactive').toBuffer('image/png')),sha(high),'Switching display mode must preserve view and be deterministic');
assert.ok(objects.every(o=>o.smooth.length===o.verts.length&&o.smooth.every(s=>s.n.every(Number.isFinite)&&Number.isFinite(s.ao))));
node('reset').onclick();assert.equal(get('viewState.center'),null);assert.equal(get('viewState.zoom'),1);
row++;
}
cc.fillStyle='#fff';cc.font='22px sans-serif';cc.fillText('v0.2 flat shading',12,28);cc.fillText('v0.3 smooth / high resolution',612,28);cc.fillText('Same v0.2 geometry / skull orbit',12,590);cc.fillText('Same v0.2 geometry / lumbar facets',12,1190);
fs.writeFileSync(path.join(out,'cleanroom-bone-review-v0.3-comparison.jpg'),compare.toBuffer('image/jpeg',92));
// Both geometry revisions use the same renderer and quality controls.
get("activate('skull','old')");while(jobs.length)jobs.shift()();assert.equal(get('viewState.target'),'skull');assert.equal(get('viewState.revision'),'old');get("focusScene('jaw');setDisplay('light')");assert.equal(get('viewState.focus'),'jaw');
node('jaw').onchange({target:{checked:false}});node('teeth').onchange({target:{checked:false}});assert.equal(get("pool['skull:old'].filter(visible).some(o=>o.name.includes('下顎')||o.name.includes('歯冠'))"),false);
viewport={width:2000,height:1200};const size=get('rasterSize(2000,1200)');assert.ok(size[0]*size[1]<=2400000,'Per-canvas allocation cap');
// Occlusion must use per-pixel depth, independent of triangle submission order.
get(`viewState.target='lumbar';viewState.revision='new';viewState.center=null;viewState.zoom=1;
const synthetic=(z,ao)=>({name:'test',verts:[[-3,z,-3],[3,z,-3],[0,z,3]],faces:[[0,1,2]],shades:[{n:[0,1,0],ao}],smooth:[0,1,2].map(()=>({n:[0,1,0],ao}))});
const savedModel=pool['lumbar:new'];const nearTest=synthetic(2,.9),farTest=synthetic(-2,.2);pool['lumbar:new']=[nearTest,farTest];`);
viewport={width:120,height:120};get("drawScene($('interactive'),0,0,1)");const a=surfaces.get('interactive').toBuffer('image/png');get("pool['lumbar:new']=[farTest,nearTest];drawScene($('interactive'),0,0,1)");assert.equal(sha(a),sha(surfaces.get('interactive').toBuffer('image/png')));get("pool['lumbar:new']=savedModel");
result.controls='High/light resolution, deterministic restored output, focus preserved, reset, previous geometry and head visibility passed; per-pixel depth order independent';
result.display='Area-weighted vertex normals and vertex-light interpolation; no per-face strokes. High requests max(2,min(3,DPR)) pixels per CSS pixel, capped at 2.4M pixels per canvas; light requests 1. Geometry unchanged.';
result.inputs=Object.fromEntries(['tools/cleanroom/bone-review-renderer-v0.3.js','tools/cleanroom/build-bone-review-v0.3.py','tools/cleanroom/check-bone-review-v0.3.cjs'].map(p=>[p,sha(read(p))]));
fs.writeFileSync(path.join(out,'cleanroom-bone-review-v0.3.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
