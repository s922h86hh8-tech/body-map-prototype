'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..');
const harness=fs.readFileSync(path.join(__dirname,'check-bone-review-v0.8.cjs'),'utf8').split("const out=path.join(root,'docs/validation');")[0];
// Reuse only the DOM/VM setup. No mesh-generation jobs are executed here.
const probeScript=`
const probes={};
for(const side of [-1,1]){
 const points={
  septum:[0,4.5,-4.3],
  septum_concha_air:[side*.38,4.5,-4.3],
  inferior_concha:[side*1.2,4.5,-4.45],
  lower_nasal_air:[side*.6,5,-5.5],
  orbital_floor:[side*3.4,5,-2.8],
  orbital_roof:[side*3.1,4,2.6]
 };
 for(const [name,p] of Object.entries(points))probes[side+':'+name]=get('skullNewField('+JSON.stringify(p)+')');
 for(const y of [2,4,6]){const t=(y-.45)/6.7,x=2.15+t;probes[side+':orbit_void_'+y]=get('skullNewField('+JSON.stringify([side*x,y,-.5])+')')}
}
for(const [key,value] of Object.entries(probes)){
 const air=key.includes('air')||key.includes('void');assert.ok(air?value>0:value<0,key+' sign '+value);
}
// Check the intended surface deformation relative to the unchanged envelope,
// at the fossa and eminence centers; these are design probes, not clinical metrics.
const envelopeY=(x,z)=>4.65+2.35*Math.sqrt(1-x*x/(4.8*4.8)-(z+4.35)*(z+4.35)/(2.65*2.65));
const maxillaY=(x,z)=>{let lo=5,hi=8;for(let i=0;i<45;i++){const y=(lo+hi)/2;if(get('maxillaBodyD('+JSON.stringify([x,y,z])+')')<0)lo=y;else hi=y}return (lo+hi)/2};
const fossa=maxillaY(3.1,-4.65)-envelopeY(3.1,-4.65),eminence=maxillaY(2.05,-5.6)-envelopeY(2.05,-5.6);
assert.ok(fossa<-.2,'fossa should recess');assert.ok(eminence>.03,'eminence should project');
const result={html_sha256:crypto.createHash('sha256').update(html).digest('hex'),probes,canine_surface_delta:{fossa,eminence},meaning:'Signed field probes verify authored air/solid layout and deformation direction only; no anatomical accuracy, mesh fidelity, dimensions or thickness approval.'};
fs.writeFileSync(path.join(root,'docs/validation/cleanroom-face-features-v0.8.json'),JSON.stringify(result,null,2)+'\\n');console.log(JSON.stringify(result,null,2));
`;
new Function('require','__dirname',harness+probeScript)(require,__dirname);
