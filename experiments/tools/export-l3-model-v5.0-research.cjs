// Export *our own* generated L3 mesh for local comparison. Never includes any CT or 3rd-party mesh.
// From repository root: node experiments/tools/export-l3-model.cjs /tmp/l3-v50.obj high
'use strict';
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const outfile=process.argv[2];
const quality=process.argv[3]||'high';
if(!outfile||!['standard','high'].includes(quality)){
 console.error('Usage: node experiments/tools/export-l3-model.cjs output.obj [standard|high]');
 process.exit(2);
}
const file=path.resolve(__dirname,'..','cleanroom-lumbar-mesh-worker-v5.0-research.js');
let output=null;
const ctx={self:{postMessage:d=>{output=d}},console,Date,Math};
vm.runInNewContext(fs.readFileSync(file,'utf8'),ctx,{filename:file});
ctx.self.onmessage({data:{id:1,level:'L3',quality,variant:'loft50'}});
if(!output||output.error)throw new Error(output?.error||'No mesh returned');
if(!output.qualityGate?.allFourWithinFivePercent||!output.qualityGate?.localPedicleFourWithinFivePercent)throw new Error('Baseline dimensions regression failed');
if(output.qualityGate.anatomyForTeachingApproved!==false)throw new Error('Unexpected anatomical approval');
const MM=44.82/(2*8.10); // v5.0 research candidate authored calibration, not a CT-based personalized scale.
const P=output.positions,F=output.indices;
let lines=['# L3 v5.0 spinous-process length candidate geometry; not CT surface', '# Units: mm (v5.0 research candidate nominal calibration)', '# Anatomical approval: NOT VALIDATED'];
for(let i=0;i<P.length;i+=3)lines.push('v '+(P[i]*MM).toFixed(7)+' '+(P[i+1]*MM).toFixed(7)+' '+(P[i+2]*MM).toFixed(7));
for(let i=0;i<F.length;i+=3)lines.push('f '+(F[i]+1)+' '+(F[i+1]+1)+' '+(F[i+2]+1));
fs.mkdirSync(path.dirname(path.resolve(outfile)),{recursive:true});
fs.writeFileSync(outfile,lines.join('\n')+'\n','utf8');
console.log(JSON.stringify({file:path.resolve(outfile),quality,vertices:output.vertices,triangles:output.triangles,
 baselineScreens:output.qualityGate.allFourWithinFivePercent,anatomicalApproval:false},null,2));
