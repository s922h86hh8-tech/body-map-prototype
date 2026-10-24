// Original finishing pass for authored bone meshes. No topology/field changes.
// Teeth, separate bones and separate anatomical openings are never welded together.
const SURFACE_FINISH={version:'0.6',pairs:8,positive:.45,negative:-.47,maxDisplacement:{skull:.12,jaw:.1,lumbar:.08}};
function boneNeighbours(o){
 const sets=o.verts.map(()=>new Set());for(const [a,b,c] of o.faces){sets[a].add(b);sets[a].add(c);sets[b].add(a);sets[b].add(c);sets[c].add(a);sets[c].add(b)}return sets.map(s=>[...s]);
}
function finishBoneSurface(o,target){
 if(o.name.includes('歯冠'))return;
 const before=o.verts.map(p=>p.slice()),neighbours=boneNeighbours(o),limit=SURFACE_FINISH.maxDisplacement[target==='lumbar'?'lumbar':o.name.includes('下顎')?'jaw':'skull'];
 let points=before.map(p=>p.slice());
 for(let pair=0;pair<SURFACE_FINISH.pairs;pair++)for(const amount of [SURFACE_FINISH.positive,SURFACE_FINISH.negative]){
  const next=points.map((p,i)=>{
   const ns=neighbours[i];if(!ns.length)return p.slice();const mean=[0,0,0];for(const j of ns)for(let k=0;k<3;k++)mean[k]+=points[j][k]/ns.length;
   const q=p.map((v,k)=>v+amount*(mean[k]-v)),d=q.map((v,k)=>v-before[i][k]),len=Math.hypot(...d);
   return len>limit?before[i].map((v,k)=>v+d[k]*limit/len):q;
  });points=next;
 }
 // Line search preserves each original triangle's orientation and positive area.
 const normals=o.faces.map(f=>V.cross(V.sub(before[f[1]],before[f[0]]),V.sub(before[f[2]],before[f[0]])));
 let strength=1,accepted=null;
 for(let attempt=0;attempt<12;attempt++,strength*=.5){
  const candidate=before.map((p,i)=>p.map((v,k)=>v+(points[i][k]-v)*strength));
  const good=o.faces.every((f,i)=>{const n=V.cross(V.sub(candidate[f[1]],candidate[f[0]]),V.sub(candidate[f[2]],candidate[f[0]]));return Math.hypot(...n)>1e-10&&n.reduce((sum,v,k)=>sum+v*normals[i][k],0)>0});
  if(good){accepted=candidate;break}
 }
 if(!accepted)throw Error('Surface finish could not preserve triangle orientations');
 o.verts=accepted;o.finished=true;o.neighbours=neighbours;
 o.finishReport={strength,maxDisplacement:Math.max(...before.map((p,i)=>Math.hypot(...V.sub(accepted[i],p)))),limit};
}
function finishVertexLighting(o){
 let values=o.smooth;
 for(let pass=0;pass<3;pass++){
  values=values.map((v,i)=>{
   const n=v.n.map(x=>x*2);let ao=v.ao*2,total=2;
   for(const j of o.neighbours[i]){const other=values[j],dot=v.n.reduce((s,x,k)=>s+x*other.n[k],0);if(dot<.25)continue;
    const w=dot*dot;for(let k=0;k<3;k++)n[k]+=other.n[k]*w;ao+=other.ao*w;total+=w;
   }
   return {n:V.unit(n),ao:ao/total};
  });
 }
 o.smooth=values;
}
