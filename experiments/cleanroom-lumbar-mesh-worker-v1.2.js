/* 施術者のための身体の地図: v1.2 independent L3 bone surface study worker.
 * All geometry is authored in this project; no external anatomical meshes.
 * High-detail preset tested on L2 L3 L4; not anatomical measurement accuracy.
 */
'use strict';
const objects=[];
const add=(name,region,side,verts,faces)=>objects.push({name,region,side,verts,faces});
const V={sub:(a,b)=>a.map((v,i)=>v-b[i]),add:(a,b)=>a.map((v,i)=>v+b[i]),mul:(a,s)=>a.map(v=>v*s),cross:(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],unit:a=>{let n=Math.hypot(...a);return a.map(v=>v/n)}};
function ell(name,reg,side,c,r){let vs=[],fs=[],n=12,m=8;vs.push([c[0],c[1],c[2]+r[2]]);for(let j=1;j<m;j++)for(let i=0;i<n;i++){let t=j*Math.PI/m,p=i*2*Math.PI/n;vs.push([c[0]+r[0]*Math.sin(t)*Math.cos(p),c[1]+r[1]*Math.sin(t)*Math.sin(p),c[2]+r[2]*Math.cos(t)])}let bot=vs.length;vs.push([c[0],c[1],c[2]-r[2]]);for(let i=0;i<n;i++){fs.push([0,1+i,1+(i+1)%n]);fs.push([bot,1+(m-2)*n+(i+1)%n,1+(m-2)*n+i])}for(let j=0;j<m-2;j++)for(let i=0;i<n;i++){let a=1+j*n+i,b=1+j*n+(i+1)%n;fs.push([a,a+n,b],[b,a+n,b+n])}add(name,reg,side,vs,fs)}
function tube(name,reg,side,pts,r){let vs=[],fs=[],n=8;pts.forEach((p,j)=>{let d=V.unit(V.sub(pts[Math.min(j+1,pts.length-1)],pts[Math.max(0,j-1)]));let u=V.unit(V.cross(d,Math.abs(d[2])<.9?[0,0,1]:[0,1,0])),v=V.cross(d,u);for(let i=0;i<n;i++){let a=i*2*Math.PI/n;vs.push(V.add(p,V.add(V.mul(u,r*Math.cos(a)),V.mul(v,r*Math.sin(a)))))}});for(let j=0;j<pts.length-1;j++)for(let i=0;i<n;i++){let a=j*n+i,b=j*n+(i+1)%n;fs.push([a,b,a+n],[b,b+n,a+n])}let a=vs.length;vs.push(pts[0],pts.at(-1));for(let i=0;i<n;i++)fs.push([a,(i+1)%n,i],[a+1,(pts.length-1)*n+i,(pts.length-1)*n+(i+1)%n]);add(name,reg,side,vs,fs)}
function bone(name,reg,s,a,b,r){tube(name,reg,s,[a,b],r);ell(name+'近位',reg,s,a,[r*1.4,r*1.35,r*1.4]);ell(name+'遠位',reg,s,b,[r*1.4,r*1.35,r*1.4])}
const PROPORTIONS={"version":"0.2","units":"arbitrary drawing units","height":177,"means_mm":{"height":1696.7,"acromiale":1363.5,"iliocristale":957.2,"trochanterion_laterale":832.0,"mid_patella":448.9,"upper_arm":315.5,"forearm":250.8}};
const BODY_H=PROPORTIONS.height, M=PROPORTIONS.means_mm;
const A={shoulder:BODY_H*M.acromiale/M.height,crest:BODY_H*M.iliocristale/M.height,trochanter:BODY_H*M.trochanterion_laterale/M.height,knee:BODY_H*M.mid_patella/M.height};
A.radial=A.shoulder-BODY_H*M.upper_arm/M.height;A.wrist=A.radial-BODY_H*M.forearm/M.height;
// Original qualitative construction from anatomical descriptions, not traced vertices.
// No dimensions here are measured bone dimensions.
function implicitMesh(name,reg,side,field,lo,hi,step){
 const n=lo.map((v,i)=>Math.ceil((hi[i]-v)/step)+1),idx=(x,y,z)=>x+n[0]*(y+n[1]*z),values=new Float64Array(n[0]*n[1]*n[2]),coords=[];
 for(let z=0;z<n[2];z++)for(let y=0;y<n[1];y++)for(let x=0;x<n[0];x++){let p=[lo[0]+x*step,lo[1]+y*step,lo[2]+z*step],k=idx(x,y,z);coords[k]=p;values[k]=field(p)}
 const vs=[],fs=[],cache=new Map(),corners=[[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]],tets=[[0,1,2,6],[0,2,3,6],[0,3,7,6],[0,7,4,6],[0,4,5,6],[0,5,1,6]];
 function vertex(a,b){let t=values[a]/(values[a]-values[b]);const end=t<1e-7?a:t>1-1e-7?b:null,key=end!==null?'p'+end:a<b?a+':'+b:b+':'+a;if(cache.has(key))return cache.get(key);let p=end!==null?coords[end]:coords[a].map((v,i)=>v+t*(coords[b][i]-v)),k=vs.length;vs.push(p);cache.set(key,k);return k}
 function tri(a,b,c,out){if(a===b||b===c||a===c)return;const normal=V.cross(V.sub(vs[b],vs[a]),V.sub(vs[c],vs[a]));if(Math.hypot(...normal)<1e-12)return;if(normal[0]*out[0]+normal[1]*out[1]+normal[2]*out[2]<0)[b,c]=[c,b];fs.push([a,b,c])}
 for(let z=0;z<n[2]-1;z++)for(let y=0;y<n[1]-1;y++)for(let x=0;x<n[0]-1;x++){let c=corners.map(a=>idx(x+a[0],y+a[1],z+a[2]));if(c.every(k=>values[k]<0)||c.every(k=>values[k]>=0))continue;for(const t of tets){let a=t.map(k=>c[k]).filter(k=>values[k]<0),b=t.map(k=>c[k]).filter(k=>values[k]>=0);
  const ci=[0,0,0],co=[0,0,0];for(const v of a)for(let j=0;j<3;j++)ci[j]+=coords[v][j]/a.length;
  for(const v of b)for(let j=0;j<3;j++)co[j]+=coords[v][j]/b.length;
  const out=[co[0]-ci[0],co[1]-ci[1],co[2]-ci[2]];
  if(a.length===1)tri(...b.map(k=>vertex(a[0],k)),out);
  else if(a.length===3)tri(...a.map(k=>vertex(k,b[0])),out);
  else if(a.length===2){let q=[vertex(a[0],b[0]),vertex(a[0],b[1]),vertex(a[1],b[0]),vertex(a[1],b[1])];tri(q[0],q[1],q[2],out);tri(q[1],q[3],q[2],out)}
 }}
 add(name,reg,side,vs,fs);
}
function ed(p,c,r){return (Math.hypot(...p.map((v,i)=>(v-c[i])/r[i]))-1)*Math.min(...r)}
function smoothMin(a,b,k){let h=Math.max(k-Math.abs(a-b),0)/k;return Math.min(a,b)-h*h*k*.25}

// L3-like vertebra. Coordinates are qualitative, not CT measurements.
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function capsule(p,a,b,r){let v=V.sub(b,a),u=clamp(V.sub(p,a).reduce((s,x,i)=>s+x*v[i],0)/v.reduce((s,x)=>s+x*x,0),0,1);return Math.hypot(...V.sub(p,V.add(a,V.mul(v,u))))-r}
function lumbarBaselineField(p){
 let d=ed(p,[0,3,94],[8,5.7,4.2]);
 for(let side of [-1,1]){d=smoothMin(d,capsule(p,[side*5,0,94],[side*12,-2,94],1.35),1);d=smoothMin(d,ed(p,[side*4,-4,94],[2.2,3.5,2]),1)}
 d=smoothMin(d,capsule(p,[0,-5,94],[0,-12,94],1.4),1);
 return d;
}
function lumbarV01Field(p){
 const [x,y,z]=p,ax=Math.abs(x);
 // Thick kidney-like centrum, with upper/lower endplates gently concave.
 const radial=Math.pow(Math.abs(x/8.0),2.35)+Math.pow(Math.abs((y-4.0)/5.65),2.2);
 let d=Math.max((Math.pow(radial,1/2.2)-1)*5.6,Math.abs(z-94)-4.3);
 // Smooth front wall and cortical rim of the vertebral body.
 const rim=Math.exp(-Math.pow((Math.abs(z-94)-3.85)/.48,2));
 d-=.18*rim*Math.exp(-Math.pow(x/7.5,4));
 // Paired pedicles connecting the body to the posterior arch.
 for(const side of [-1,1]){
  d=smoothMin(d,capsule(p,[side*5.45,-.45,94],[side*5.85,-5.7,94],1.55),.55);
  // Inferior and superior notches are schematic, not a verified nerve exit.
  d=smoothMin(d,ed(p,[side*6.15,-5.4,94],[2.35,2.2,2.65]),.65);
  // Lamina forms a continuous posterior arch to the midline.
  d=smoothMin(d,capsule(p,[side*6.15,-6.1,94],[side*1.7,-10.1,94],1.25),.65);
  // Transverse processes are flattened and directed laterally.
  d=smoothMin(d,capsule(p,[side*6.25,-5.8,94],[side*13.3,-7.6,94.2],1.02),.48);
  // Superior articular processes with inward-facing facet surfaces.
  d=smoothMin(d,ed(p,[side*5.3,-7.4,97.9],[1.5,1.6,2.5]),.6);
  // Inferior articular processes below the lamina.
  d=smoothMin(d,ed(p,[side*4.65,-8.3,90.3],[1.5,1.55,2.1]),.55);
 }
 // Broad, nearly horizontal lumbar spinous process.
 d=smoothMin(d,capsule(p,[0,-9.7,94],[0,-14.3,94.0],1.48),.65);
 d=smoothMin(d,ed(p,[0,-13.5,94],[1.6,1.9,2.15]),.6);
 // Vertebral foramen: central opening behind body, between pedicles and lamina.
 const canal=Math.max(Math.abs(z-94)-6.0,(Math.pow(Math.abs(x/4.0),2.3)+Math.pow(Math.abs((y+4.0)/3.3),2.1)-1)*3.2);
 d=Math.max(d,-canal);
 return d;
}

function lumbarV02Field(p){
 const [x,y,z]=p,ax=Math.abs(x),dz=z-94;
 const radial=Math.pow(ax/8.0,2.4)+Math.pow(Math.abs((y-4)/5.7),2.25);
 const bodySide=(Math.pow(radial,1/2.25)-1)*5.7;
 // Biconcave endplate depressions, strongest at the centrum center.
 const centerDep=.44*Math.exp(-Math.pow(x/5.9,4)-Math.pow((y-4)/4.2,4));
 const cap= Math.abs(dz)-(4.35-centerDep);
 let d=Math.max(bodySide,cap);
 const rim=Math.exp(-Math.pow((Math.abs(dz)-3.95)/.48,2));
 d-=.12*rim*Math.exp(-Math.pow(x/7.6,6));
 for(const side of [-1,1]){
  d=smoothMin(d,capsule(p,[side*5.4,-.4,94],[side*5.65,-5.85,94],1.52),.55);
  d=smoothMin(d,ed(p,[side*5.85,-5.7,94],[2.3,2.05,2.55]),.58);
  d=smoothMin(d,capsule(p,[side*5.9,-6.1,94],[side*1.45,-10.1,94],1.2),.6);
  // Tapered costal process: thicker root, flattened rounded tip.
  d=smoothMin(d,capsule(p,[side*6.3,-5.8,94],[side*10.8,-7.3,94.1],1.05),.45);
  d=smoothMin(d,capsule(p,[side*10.5,-7.2,94.1],[side*13.2,-7.9,94.4],.72),.4);
  d=smoothMin(d,ed(p,[side*5.2,-7.3,97.65],[1.65,1.65,2.5]),.6);
  d=smoothMin(d,ed(p,[side*4.7,-8.2,90.55],[1.42,1.52,2.0]),.55);
  // Mammillary process as a small dorsal prominence on the superior process.
  d=smoothMin(d,ed(p,[side*5.55,-8.7,98.6],[.75,.7,.9]),.25);
 }
 d=smoothMin(d,capsule(p,[0,-9.5,94],[0,-12.6,94],1.55),.55);
 d=smoothMin(d,ed(p,[0,-13.4,94],[1.75,1.9,2.25]),.5);
 // Rounded triangular canal (broad anterior base, narrower posterior apex).
 const q=clamp((y+1.2)/(-6.2),0,1);
 const halfWidth=4.15-1.4*q;
 const canalCross=Math.max((ax/halfWidth)-1,Math.abs((y+4.15)/3.3)-1)*2.9;
 const canal=Math.max(canalCross,Math.abs(dz)-6.2);
 d=Math.max(d,-canal);
 return d;
}


// Continuous L3 SDF, originally authored for this project; NOT a CT model.
function roundedBox(p,c,radii,r){const q=p.map((x,i)=>Math.abs(x-c[i])-radii[i]);return Math.hypot(...q.map(v=>Math.max(v,0)))+Math.min(Math.max(...q),0)-r}
function lumbarV04Field(p){
 const [x,y,z]=p,ax=Math.abs(x),dz=z-94;
 const radial=Math.pow(ax/8.05,2.38)+Math.pow(Math.abs((y-4.05)/5.76),2.20);
 const dep=.30*Math.exp(-Math.pow(x/6.4,4)-Math.pow((y-4)/4.5,4));
 let d=Math.max((Math.pow(radial,1/2.2)-1)*5.76,Math.abs(dz)-(4.34-dep));
 d-=.12*Math.exp(-Math.pow((Math.abs(dz)-3.85)/.40,2)-Math.pow(x/7.6,6));
 for(const side of [-1,1]){
  d=smoothMin(d,capsule(p,[side*5.55,-.45,94],[side*5.85,-5.65,94],1.53),.56);
  d=smoothMin(d,ed(p,[side*5.93,-5.55,94],[2.15,2.12,2.65]),.54);
  d=smoothMin(d,capsule(p,[side*5.85,-6.0,94],[side*1.35,-10.08,94],1.19),.59);
  d=smoothMin(d,capsule(p,[side*6.2,-5.8,94.1],[side*10.35,-6.85,94.05],1.06),.46);
  d=smoothMin(d,capsule(p,[side*10.2,-6.84,94.05],[side*13.25,-7.73,94.24],.71),.33);
  d=smoothMin(d,ed(p,[side*5.12,-7.45,97.8],[1.47,1.56,2.46]),.61);
  d=smoothMin(d,ed(p,[side*4.35,-8.23,90.3],[1.43,1.51,2.01]),.53);
  d=smoothMin(d,ed(p,[side*5.48,-8.78,98.56],[.74,.73,.9]),.27);
  d=smoothMin(d,ed(p,[side*7.30,-7.10,93.84],[.65,.65,.72]),.23);
  d=Math.max(d,-ed(p,[side*7.45,-4.05,89.43],[1.49,1.55,.84]));
 }
 d=smoothMin(d,capsule(p,[0,-9.6,94],[0,-11.0,94],1.55),.56);
 d=smoothMin(d,roundedBox(p,[0,-12.46,94],[1.10,1.90,1.52],.44),.52);
 const frac=clamp((-1.45-y)/7.5,0,1),w=4.02*(1-.58*Math.pow(frac,1.07));
 d=Math.max(d,-Math.max((ax-w)*.9,y+1.42,-9.13-y,Math.abs(dz)-6.85));
 return d;
}

// L3 v0.5: independent morphology study. Arbitrary units, not CT dimensions.
// Body indentation, posterior arch, upper/lower facets, and process profiles
// are shaped in a continuous signed-distance field (no separate overlay meshes).
function lumbarV05Field(p){
 const [x,y,z]=p,ax=Math.abs(x),dz=z-94;
 // Kidney-like upper profile: shallow indentation on the posterior midline.
 const posteriorWeight=Math.exp(-Math.pow(x/2.75,2)-Math.pow((y+1.45)/2.85,2));
 const yContour=y-.69*posteriorWeight;
 const radial=Math.pow(ax/8.12,2.42)+Math.pow(Math.abs((yContour-4.04)/5.72),2.22);
 const endplateBowl=.37*Math.exp(-Math.pow(x/6.2,4)-Math.pow((y-4.0)/4.55,4));
 let d=Math.max((Math.pow(radial,1/2.22)-1)*5.72,Math.abs(dz)-(4.30-endplateBowl));
 // Thin continuous rim at the superior and inferior endplates.
 const rim=Math.exp(-Math.pow((Math.abs(dz)-3.83)/.34,2));
 d-=.135*rim*Math.exp(-Math.pow(x/7.5,6)-Math.pow((y-4.1)/5.3,6));
 for(const side of [-1,1]){
  // Pedicles connect the posterior body to the laminae.
  d=smoothMin(d,capsule(p,[side*5.45,-.37,94],[side*5.72,-5.72,94],1.59),.67);
  d=smoothMin(d,ed(p,[side*5.8,-5.5,94],[2.0,2.08,2.57]),.66);
  d=smoothMin(d,capsule(p,[side*5.65,-6.05,94],[side*1.20,-10.18,94],1.23),.62);
  // Tapered lumbar costal process; posterior-swept, flat distal tip.
  d=smoothMin(d,capsule(p,[side*6.15,-5.78,94.06],[side*9.70,-6.66,94.17],1.07),.54);
  d=smoothMin(d,capsule(p,[side*9.45,-6.65,94.18],[side*13.13,-7.59,94.42],.69),.40);
  d=smoothMin(d,ed(p,[side*12.9,-7.55,94.41],[.65,.78,.55]),.22);
  // Superior articular process: upright; facetal surface toward medial side.
  d=smoothMin(d,ed(p,[side*5.09,-7.43,97.65],[1.44,1.55,2.45]),.62);
  d=smoothMin(d,ed(p,[side*5.52,-8.89,98.37],[.70,.70,.81]),.24);
  // Inferior articular process: directed lower and slightly medial,
  // convex lateral surface for contact with adjacent lower vertebra.
  d=smoothMin(d,ed(p,[side*4.25,-8.38,90.23],[1.42,1.44,2.0]),.60);
  // Attach inferior articular process to vertebral lamina and pars.
  d=smoothMin(d,capsule(p,[side*5.20,-6.42,94.03],[side*4.25,-8.38,90.95],1.10),.64);
  // Accessory tubercle on posterior base of costal process.
  d=smoothMin(d,ed(p,[side*7.25,-7.28,94.00],[.64,.63,.79]),.29);
  // Small medial facing facet indentation (shallow, not a through-hole).
  const medialFacet=Math.exp(
     -Math.pow((x-side*3.78)/.51,2)
     -Math.pow((y+7.42)/1.02,2)
     -Math.pow((z-97.67)/1.33,2));
  d+=.22*medialFacet;
  // Inferior vertebral notch, close to the caudal pedicle border.
  // Surrogate contour; no adjacent level or spinal nerve is modeled.
  const inferiorNotch=ed(p,[side*5.67,-3.69,91.22],[1.32,1.50,.97]);
  d=Math.max(d,-inferiorNotch);
 }
 // Flattened broad quadrangular lumbar spinous process, gently rough tip.
 d=smoothMin(d,capsule(p,[0,-9.47,94],[0,-10.76,94],1.58),.60);
 d=smoothMin(d,roundedBox(p,[0,-12.42,94],[1.15,1.86,1.62],.39),.52);
 // Gentle longitudinal ridge on the dorsal crest, without a second mesh.
 d=smoothMin(d,ed(p,[0,-13.83,94],[.59,.52,1.34]),.22);
 // Vertebral foramen: broad anterior edge, rounded triangular posterior apex.
 // Continuous superior-inferior opening; not a square tube or bone hole mesh.
 const fraction=clamp((-1.46-y)/7.7,0,1);
 const width=4.02*(1-.84*Math.pow(fraction,1.12));
 const opening=Math.max((ax-width)*.91,y+1.49,-9.28-y,Math.abs(dz)-6.72);
 d=Math.max(d,-opening);
 return d;
}
function lumbarV06Field(p){
 const [x,y,z]=p,ax=Math.abs(x),dz=z-94;
 // Kidney-like upper profile: shallow indentation on the posterior midline.
 const posteriorWeight=Math.exp(-Math.pow(x/2.75,2)-Math.pow((y+1.45)/2.85,2));
 const yContour=y-.69*posteriorWeight;
 const radial=Math.pow(ax/8.12,2.42)+Math.pow(Math.abs((yContour-4.04)/5.72),2.22);
 const endplateBowl=.37*Math.exp(-Math.pow(x/6.2,4)-Math.pow((y-4.0)/4.55,4));
 let d=Math.max((Math.pow(radial,1/2.22)-1)*5.72,Math.abs(dz)-(4.30-endplateBowl));
 // Thin continuous rim at the superior and inferior endplates.
 const rim=Math.exp(-Math.pow((Math.abs(dz)-3.83)/.34,2));
 d-=.135*rim*Math.exp(-Math.pow(x/7.5,6)-Math.pow((y-4.1)/5.3,6));
 for(const side of [-1,1]){
  // Pedicles connect the posterior body to the laminae.
  d=smoothMin(d,capsule(p,[side*5.45,-.37,94],[side*5.72,-5.72,94],1.59),.67);
  d=smoothMin(d,ed(p,[side*5.8,-5.5,94],[2.0,2.08,2.57]),.66);
  d=smoothMin(d,capsule(p,[side*5.65,-6.05,94],[side*1.20,-10.18,94],1.23),.62);
  // Tapered lumbar costal process; posterior-swept, flat distal tip.
  d=smoothMin(d,capsule(p,[side*6.15,-5.78,94.06],[side*9.70,-6.66,94.17],1.07),.54);
  d=smoothMin(d,capsule(p,[side*9.45,-6.65,94.18],[side*13.13,-7.59,94.42],.69),.40);
  d=smoothMin(d,ed(p,[side*12.9,-7.55,94.41],[.65,.78,.55]),.22);
  // Superior articular process: upright; facetal surface toward medial side.
  d=smoothMin(d,ed(p,[side*5.09,-7.43,97.65],[1.44,1.55,2.45]),.62);
  d=smoothMin(d,ed(p,[side*5.52,-8.89,98.37],[.70,.70,.81]),.24);
  // Inferior articular process: directed lower and slightly medial,
  // convex lateral surface for contact with adjacent lower vertebra.
  d=smoothMin(d,ed(p,[side*4.25,-8.38,90.23],[1.42,1.44,2.0]),.60);
  // Attach inferior articular process to vertebral lamina and pars.
  d=smoothMin(d,capsule(p,[side*5.20,-6.42,94.03],[side*4.25,-8.38,90.95],1.10),.64);
  // Accessory tubercle on posterior base of costal process.
  d=smoothMin(d,ed(p,[side*7.25,-7.28,94.00],[.64,.63,.79]),.29);
  // Small medial facing facet indentation (shallow, not a through-hole).
  const medialFacet=Math.exp(
     -Math.pow((x-side*3.78)/.51,2)
     -Math.pow((y+7.42)/1.02,2)
     -Math.pow((z-97.67)/1.33,2));
  d+=.27*medialFacet;
  // Gently convex lateral-facing lower joint facet; stay on the single bone SDF.
  const lateralFacet=Math.exp(-Math.pow((x-side*5.34)/.52,2)
     -Math.pow((y+8.17)/1.03,2)-Math.pow((z-90.37)/1.08,2));
  d-=.15*lateralFacet;
  // Inferior vertebral notch, close to the caudal pedicle border.
  // Surrogate contour; no adjacent level or spinal nerve is modeled.
  const inferiorNotch=ed(p,[side*5.67,-3.69,91.22],[1.32,1.50,.97]);
  d=Math.max(d,-inferiorNotch);
 }
 // Flattened broad quadrangular lumbar spinous process, gently rough tip.
 d=smoothMin(d,capsule(p,[0,-9.47,94],[0,-10.76,94],1.58),.60);
 d=smoothMin(d,roundedBox(p,[0,-12.42,94],[1.15,1.86,1.62],.39),.52);
 // Gentle longitudinal ridge on the dorsal crest, without a second mesh.
 d=smoothMin(d,ed(p,[0,-13.83,94],[.59,.52,1.34]),.22);
 // Vertebral foramen: broad anterior edge, rounded triangular posterior apex.
 // Continuous superior-inferior opening; not a square tube or bone hole mesh.
 const fraction=clamp((-1.46-y)/7.7,0,1);
 const width=4.02*(1-.84*Math.pow(fraction,1.12));
 const opening=Math.max((ax-width)*.91,y+1.49,-9.28-y,Math.abs(dz)-6.72);
 d=Math.max(d,-opening);
 return d;
}


// v0.7 independent procedural level variants, not measured human dimensions.
// v0.8 Independent vertebral-level morphology parameters.
// Design coordinates are dimensionless project units, NOT clinical measurements.
const MORPH={
 L2:{W:7.52,D:5.4,H:4.08,bodyY:4.1,ped:5.27,arch:-9.68,
  trans:11.9,rootY:-5.95,tipY:-7.5,supX:4.77,infX:4.15,
  spin:-13.65,spinZ:1.52,canal:3.72,facetTilt:.08},
 L3:{W:8.10,D:5.72,H:4.3,bodyY:4.04,ped:5.53,arch:-10.08,
  trans:13.15,rootY:-5.79,tipY:-7.64,supX:5.08,infX:4.25,
  spin:-13.88,spinZ:1.62,canal:4.02,facetTilt:.22},
 L4:{W:8.70,D:6.03,H:4.56,bodyY:4.0,ped:5.86,arch:-10.34,
  trans:12.48,rootY:-4.95,tipY:-7.20,supX:5.39,infX:4.61,
  spin:-13.77,spinZ:1.76,canal:4.29,facetTilt:.36}
};
function levelV08(p,id){
 const t=MORPH[id]||MORPH.L3,[x,y,z]=p,ax=Math.abs(x),dz=z-94;
 const pinch=.43*Math.exp(-Math.pow(x/2.6,2)-Math.pow((y+1.3)/1.9,2));
 const r=Math.pow(ax/t.W,2.42)+Math.pow(Math.abs((y-pinch-t.bodyY)/t.D),2.22);
 const cup=.29*Math.exp(-Math.pow(x/(t.W*.78),4)-Math.pow((y-t.bodyY)/(t.D*.78),4));
 let d=Math.max((Math.pow(r,1/2.22)-1)*t.D,Math.abs(dz)-(t.H-cup));
 const rim=Math.exp(-Math.pow((Math.abs(dz)-(t.H-.45))/.41,2));
 d-=.11*rim*Math.exp(-Math.pow(x/(t.W*.92),6)-Math.pow((y-t.bodyY)/(t.D*.93),6));
 for(const side of [-1,1]){
  const px=side*t.ped;
  d=smoothMin(d,capsule(p,[px,-.4,94],[px+side*.23,-5.67,94],1.58),.64);
  d=smoothMin(d,ed(p,[px+side*.34,-5.56,94],[2.1,2.1,2.6]),.57);
  d=smoothMin(d,capsule(p,[px+side*.24,-6.15,94],[side*1.34,t.arch,94],1.22),.62);
  // L4's costal process arises more anteriorly, versus L2/L3 at the arch.
  d=smoothMin(d,capsule(p,[px+side*.5,t.rootY,94.09],[side*(t.trans-3.1),t.tipY+.81,94.19],1.08),.48);
  d=smoothMin(d,capsule(p,[side*(t.trans-3.3),t.tipY+.82,94.19],[side*t.trans,t.tipY,94.32],.70),.38);
  d=smoothMin(d,ed(p,[side*(t.trans-.25),t.tipY,94.32],[.65,.70,.54]),.22);
  d=smoothMin(d,ed(p,[side*t.supX,-7.4,97.7],[1.43,1.52,2.44]),.61);
  d=smoothMin(d,ed(p,[side*t.infX,-8.36,90.25],[1.43,1.44,2.0]),.57);
  // Pars/lamina bridge guarantees the inferior process is not a detached island.
  d=smoothMin(d,capsule(p,[side*(t.ped-.31),-6.44,94.04],[side*t.infX,-8.36,90.92],1.12),.67);
  d=smoothMin(d,ed(p,[side*(t.supX+.42),-8.75,98.5],[.70,.66,.86]),.25);
  d=smoothMin(d,ed(p,[side*(t.ped+1.7),t.rootY-1.24,94.0],[.64,.61,.72]),.23);
  // Facet fields: medial facing recess and laterally convex lower facet.
  const depression=Math.exp(-Math.pow((x-side*(t.supX-1.18))/.54,2)
    -Math.pow((y+7.40-.4*t.facetTilt*(side*x-t.supX))/1.00,2)
    -Math.pow((z-97.72)/1.17,2));
  d+=.25*depression;
  const convex=Math.exp(-Math.pow((x-side*(t.infX+1.06))/.71,2)
    -Math.pow((y+8.3-.22*t.facetTilt)/.96,2)-Math.pow((z-90.27)/1.08,2));
  d-=.12*convex;
  d=Math.max(d,-ed(p,[side*(t.ped+.26),-3.70,91.26],[1.31,1.44,.92]));
 }
 d=smoothMin(d,capsule(p,[0,t.arch+.56,94],[0,-10.76,94],1.53),.55);
 const center=(t.spin-10.78)/2,half=Math.max(1.15,(-t.spin-10.78)/2);
 d=smoothMin(d,roundedBox(p,[0,center,94],[1.12,half,t.spinZ],.41),.54);
 const depth=clamp((-1.45-y)/7.65,0,1),halfWidth=t.canal*(1-.69*Math.pow(depth,1.07));
 d=Math.max(d,-Math.max((ax-halfWidth)*.91,y+1.45,-9.26-y,Math.abs(dz)-6.7));
 return d;
}


// v1.0 morphology refinement. Anatomical orientation:
// +Y anterior, -Y posterior; +Z superior; X lateral.
// Based on descriptive anatomy only; no copied mesh or patient imaging.
// The named 3D landmarks and geometry parameters are schematic.
function smoothMax(a,b,k){return -smoothMin(-a,-b,k)}
function levelV10(p,id){
 const t=MORPH[id]||MORPH.L3;
 const [x,y,z]=p,ax=Math.abs(x),dz=z-94;
 // Posterior vertebral-body waist: reniform (kidney-shaped) superior outline.
 const notch=.67*Math.exp(-Math.pow(x/2.77,2)-Math.pow((y+1.29)/1.95,2));
 const radial=Math.pow(ax/t.W,2.39)+Math.pow(Math.abs((y-notch-t.bodyY)/t.D),2.23);
 const disk=.40*Math.exp(-Math.pow(x/(t.W*.77),4)-Math.pow((y-t.bodyY)/(t.D*.75),4));
 let d=Math.max((Math.pow(radial,1/2.23)-1)*t.D,Math.abs(dz)-(t.H-disk));
 // Apophyseal ring as a softly continuous rim, never an overlaid ring object.
 const rim=Math.exp(-Math.pow((Math.abs(dz)-(t.H-.41))/.37,2));
 d-=.125*rim*Math.exp(-Math.pow(x/(t.W*.92),6)-Math.pow((y-t.bodyY)/(t.D*.93),6));
 for(const side of [-1,1]){
  const px=side*t.ped;
  // Pedicle and lamina remain a single solid arch.
  d=smoothMin(d,capsule(p,[px,-.39,94],[px+side*.25,-5.67,94],1.59),.63);
  d=smoothMin(d,ed(p,[px+side*.30,-5.60,94],[2.09,2.05,2.56]),.57);
  d=smoothMin(d,capsule(p,[px+side*.24,-6.15,94],[side*1.34,t.arch,94],1.25),.61);
  // Costal processes: thin distally, their origin moves anteriorly in L4.
  d=smoothMin(d,capsule(p,[px+side*.5,t.rootY,94.09],[side*(t.trans-3.1),t.tipY+.81,94.19],1.03),.48);
  d=smoothMin(d,capsule(p,[side*(t.trans-3.3),t.tipY+.82,94.19],[side*t.trans,t.tipY,94.32],.66),.37);
  d=smoothMin(d,ed(p,[side*(t.trans-.25),t.tipY,94.32],[.63,.65,.51]),.19);
  // Strong upright superior articular process and medially facing concave facet.
  d=smoothMin(d,ed(p,[side*t.supX,-7.40,97.69],[1.43,1.53,2.44]),.60);
  // Inferior process has a convex, anterolateral facet and is linked to pars.
  d=smoothMin(d,ed(p,[side*t.infX,-8.36,90.25],[1.43,1.44,2.02]),.56);
  d=smoothMin(d,capsule(p,[side*(t.ped-.31),-6.44,94.04],[side*t.infX,-8.36,90.92],1.12),.67);
  d=smoothMin(d,ed(p,[side*(t.supX+.42),-8.75,98.50],[.70,.66,.85]),.25);
  d=smoothMin(d,ed(p,[side*(t.ped+1.7),t.rootY-1.24,94.0],[.61,.63,.70]),.23);
  // The facet surface itself is a shallow, curved recess on the
  // posteromedial aspect of the superior articular process.
  const facetX=side*(t.supX-2.08);
  const facetY=-7.95-.20*t.facetTilt;
  const scoop=ed(p,[facetX,facetY,98.00],[1.38,1.23,1.47]);
  d=smoothMax(d,-scoop,.13);
  // Lower facet has a slight laterally/anteriorly projected convex surface.
  const bulge=ed(p,[side*(t.infX+1.03),-8.05+.23*t.facetTilt,90.22],[.69,.93,1.05]);
  d=smoothMin(d,bulge,.13);
  // Superior notch shallow; inferior notch substantially deeper on pedicle.
  const lowerNotch=ed(p,[side*(t.ped+.35),-3.75,91.94],[1.17,1.37,1.23]);
  const upperNotch=ed(p,[side*(t.ped+.35),-3.75,96.04],[.90,1.14,.80]);
  d=smoothMax(d,-lowerNotch,.12);
  d=smoothMax(d,-upperNotch,.09);
 }
 // Short quadrangular, nearly horizontal lumbar spinous process.
 d=smoothMin(d,capsule(p,[0,t.arch+.56,94],[0,-10.76,94],1.53),.54);
 const rear=(t.spin-10.78)/2,depth=Math.max(1.15,(-t.spin-10.78)/2);
 d=smoothMin(d,roundedBox(p,[0,rear,94],[1.12,depth,t.spinZ],.41),.54);
 // Posterior apex rounded rather than rectangular, triangular canal.
 const fraction=clamp((-1.45-y)/7.65,0,1);
 const halfWidth=t.canal*(1-.75*Math.pow(fraction,1.10));
 const canal=Math.max((ax-halfWidth)*.90,y+1.45,-9.20-y,Math.abs(dz)-6.71);
 d=smoothMax(d,-canal,.10);
 return d;
}

// Morphometric design reference from lumbar-reference-v1.2.json (Koziej 2025 Tables 3–5).
const CALIBRATION_MM_PER_UNIT=44.82/(2*8.10);
const LUMBAR_REF_MM={"L2":{"upperEndplateWidth":42.98,"upperEndplateDepth":32.12,"anteriorBodyHeight":25.75,"posteriorBodyHeight":27.02,"pedicleWidth":8.23,"spinalCanalWidth":22.15,"pedicleHeight":14.9,"spinalCanalDepth":15.08,"lowerEndplateWidth":46.1,"lowerEndplateDepth":32.91},"L3":{"upperEndplateWidth":44.82,"upperEndplateDepth":33.17,"anteriorBodyHeight":26.83,"posteriorBodyHeight":26.67,"pedicleWidth":9.71,"spinalCanalWidth":22.62,"pedicleHeight":14.52,"spinalCanalDepth":14.69,"lowerEndplateWidth":49.12,"lowerEndplateDepth":33.76},"L4":{"upperEndplateWidth":47.5,"upperEndplateDepth":33.83,"anteriorBodyHeight":26.86,"posteriorBodyHeight":25.76,"pedicleWidth":11.52,"spinalCanalWidth":23.19,"pedicleHeight":14.2,"spinalCanalDepth":15.06,"lowerEndplateWidth":50.63,"lowerEndplateDepth":34.07}};
function calibratedLumbarParameters(id){
 const r=LUMBAR_REF_MM[id]||LUMBAR_REF_MM.L3,b=MORPH[id]||MORPH.L3,s=CALIBRATION_MM_PER_UNIT;
 return {...b,W:r.upperEndplateWidth/(2*s),D:r.upperEndplateDepth/(2*s),
 Wlower:r.lowerEndplateWidth/(2*s),Dlower:r.lowerEndplateDepth/(2*s),
 H:r.anteriorBodyHeight/(2*s),Hposterior:r.posteriorBodyHeight/(2*s),
 canal:r.spinalCanalWidth/(2*s),
 pedRadiusX:r.pedicleWidth/(2*s),pedRadiusZ:r.pedicleHeight/(2*s)};
}
// Matching parametric radii is NOT proof of matching real mesh dimensions.
function levelV11(p,id){
 const t=calibratedLumbarParameters(id);
 const [x,y,z]=p,ax=Math.abs(x),dz=z-94;
 // Posterior vertebral-body waist: reniform (kidney-shaped) superior outline.
 const notch=.67*Math.exp(-Math.pow(x/2.77,2)-Math.pow((y+1.29)/1.95,2));
 const bodyFraction=clamp((dz/t.H+1)/2,0,1);
 const halfW=t.Wlower*(1-bodyFraction)+t.W*bodyFraction;
 const halfD=(t.Dlower*(1-bodyFraction)+t.D*bodyFraction)*1.04; // independent section-fit correction, not a measured anatomical constant
 const radial=Math.pow(ax/halfW,2.39)+Math.pow(Math.abs((y-notch-t.bodyY)/halfD),2.23);
 const disk=.40*Math.exp(-Math.pow(x/(halfW*.77),4)-Math.pow((y-t.bodyY)/(halfD*.75),4));
 const frontness=clamp((y-(t.bodyY-halfD))/(2*halfD),0,1);
 const halfH=t.Hposterior*(1-frontness)+t.H*frontness;
 let d=Math.max((Math.pow(radial,1/2.23)-1)*halfD,Math.abs(dz)-(halfH-disk));
 // Apophyseal ring as a softly continuous rim, never an overlaid ring object.
 const rim=Math.exp(-Math.pow((Math.abs(dz)-(t.H-.41))/.37,2));
 d-=.125*rim*Math.exp(-Math.pow(x/(halfW*.92),6)-Math.pow((y-t.bodyY)/(halfD*.93),6));
 for(const side of [-1,1]){
  const px=side*t.ped;
  // Pedicle and lamina remain a single solid arch.
  const ellipseZ=94+(z-94)*(t.pedRadiusX/t.pedRadiusZ);
  d=smoothMin(d,capsule([x,y,ellipseZ],[px,-.39,94],[px+side*.25,-5.67,94],t.pedRadiusX),.63);
  d=smoothMin(d,ed(p,[px+side*.30,-5.60,94],[2.09,2.05,2.56]),.57);
  d=smoothMin(d,capsule(p,[px+side*.24,-6.15,94],[side*1.34,t.arch,94],1.25),.61);
  // Costal processes: thin distally, their origin moves anteriorly in L4.
  d=smoothMin(d,capsule(p,[px+side*.5,t.rootY,94.09],[side*(t.trans-3.1),t.tipY+.81,94.19],1.03),.48);
  d=smoothMin(d,capsule(p,[side*(t.trans-3.3),t.tipY+.82,94.19],[side*t.trans,t.tipY,94.32],.66),.37);
  d=smoothMin(d,ed(p,[side*(t.trans-.25),t.tipY,94.32],[.63,.65,.51]),.19);
  // Strong upright superior articular process and medially facing concave facet.
  d=smoothMin(d,ed(p,[side*t.supX,-7.40,97.69],[1.43,1.53,2.44]),.60);
  // Inferior process has a convex, anterolateral facet and is linked to pars.
  d=smoothMin(d,ed(p,[side*t.infX,-8.36,90.25],[1.43,1.44,2.02]),.56);
  d=smoothMin(d,capsule(p,[side*(t.ped-.31),-6.44,94.04],[side*t.infX,-8.36,90.92],1.12),.67);
  d=smoothMin(d,ed(p,[side*(t.supX+.42),-8.75,98.50],[.70,.66,.85]),.25);
  d=smoothMin(d,ed(p,[side*(t.ped+1.7),t.rootY-1.24,94.0],[.61,.63,.70]),.23);
  // The facet surface itself is a shallow, curved recess on the
  // posteromedial aspect of the superior articular process.
  const facetX=side*(t.supX-2.08);
  const facetY=-7.95-.20*t.facetTilt;
  const scoop=ed(p,[facetX,facetY,98.00],[1.38,1.23,1.47]);
  d=smoothMax(d,-scoop,.13);
  // Lower facet has a slight laterally/anteriorly projected convex surface.
  const bulge=ed(p,[side*(t.infX+1.03),-8.05+.23*t.facetTilt,90.22],[.69,.93,1.05]);
  d=smoothMin(d,bulge,.13);
  // Superior notch shallow; inferior notch substantially deeper on pedicle.
  const lowerNotch=ed(p,[side*(t.ped+.35),-3.75,91.94],[1.17,1.37,1.23]);
  const upperNotch=ed(p,[side*(t.ped+.35),-3.75,96.04],[.90,1.14,.80]);
  d=smoothMax(d,-lowerNotch,.12);
  d=smoothMax(d,-upperNotch,.09);
 }
 // Short quadrangular, nearly horizontal lumbar spinous process.
 d=smoothMin(d,capsule(p,[0,t.arch+.56,94],[0,-10.76,94],1.53),.54);
 const rear=(t.spin-10.78)/2,depth=Math.max(1.15,(-t.spin-10.78)/2);
 d=smoothMin(d,roundedBox(p,[0,rear,94],[1.12,depth,t.spinZ],.41),.54);
 // Posterior apex rounded rather than rectangular, triangular canal.
 const fraction=clamp((-1.45-y)/7.65,0,1);
 const halfWidth=t.canal*(1-.75*Math.pow(fraction,1.10));
 const canal=Math.max((ax-halfWidth)*.90,y+1.45,-9.20-y,Math.abs(dz)-6.71);
 d=smoothMax(d,-canal,.10);
 return d;
}


// Clean-room cortical surface study v1.2: all values authored for this project.
// Decorative submillimetre relief is NOT reconstructed from a scan or atlas.
// It is masked away from the canal, pedicles, endplates and facet bearing areas.
function smoothStep01(t){const v=clamp(t,0,1);return v*v*(3-2*v)}
function levelV12(p,id){
 let d=levelV11(p,id);if(id!=='L3')return d;
 const [x,y,z]=p,dz=z-94,t=calibratedLumbarParameters(id);
 const anterior=smoothStep01((y+.75)/2.8);
 const midHeight=smoothStep01((t.H-Math.abs(dz)-.40)/1.25);
 const macro=.58*Math.sin(.99*x+.46*z)*Math.cos(.76*y-1.16*z)
            +.24*Math.sin(2.18*x+.39*y-.88*z)*Math.sin(1.19*y+.51*z);
 const fine=.18*Math.sin(4.25*x+1.17*y)*Math.cos(3.75*z-.44*x);
 d+=anterior*midHeight*(.11*macro+.034*fine);
 const left=Math.exp(-Math.pow((x+3.55)/2.15,2)-Math.pow((y+8.25)/1.8,2));
 const right=Math.exp(-Math.pow((x-3.55)/2.15,2)-Math.pow((y+8.25)/1.8,2));
 d+=.039*(left+right)*smoothStep01((2.5-Math.abs(dz))/1.3)
   *Math.sin(.81*x+.43*z)*Math.cos(.98*y-.61*z);
 return d;
}

// Deterministic 3D value noise for decorative bone coloration.
// The color texture is original and contains no anatomical data.
function hash3(ix,iy,iz){
 let n=(Math.imul(ix,374761393)+Math.imul(iy,668265263)+Math.imul(iz,1442695041))|0;
 n=Math.imul(n^(n>>>13),1274126177);
 return ((n^(n>>>16))>>>0)/4294967295;
}
function noise3(x,y,z){
 const i=Math.floor(x),j=Math.floor(y),k=Math.floor(z);
 const u=smoothStep01(x-i),v=smoothStep01(y-j),w=smoothStep01(z-k);
 const m=(a,b,t)=>a+(b-a)*t;
 const n0=m(m(hash3(i,j,k),hash3(i+1,j,k),u),m(hash3(i,j+1,k),hash3(i+1,j+1,k),u),v);
 const n1=m(m(hash3(i,j,k+1),hash3(i+1,j,k+1),u),m(hash3(i,j+1,k+1),hash3(i+1,j+1,k+1),u),v);
 return m(n0,n1,w);
}

// Independent section-proxy audit: derive dimensions FROM OUTPUT VERTICES.
// This is NOT a clinical endplate measurement or CT registration.
function sectionProxyAudit(mesh,level){
 const ref=LUMBAR_REF_MM[level],t=calibratedLumbarParameters(level),mm=CALIBRATION_MM_PER_UNIT;
 const sections=[],maxError={};
 for(const surface of ['upper','lower']){
  const targetZ=94+(surface==='upper'?.86:-.86)*t.H;
  let n=0,minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
  for(const point of mesh.verts){
   const [x,y,z]=point;
   if(Math.abs(z-targetZ)>.23||y< -2.65)continue;
   minX=Math.min(minX,x);maxX=Math.max(maxX,x);
   minY=Math.min(minY,y);maxY=Math.max(maxY,y);n++;
  }
  if(n<40)throw Error('断面に十分なメッシュ頂点がありません：'+level+surface);
  const keyW=surface==='upper'?'upperEndplateWidth':'lowerEndplateWidth';
  const keyD=surface==='upper'?'upperEndplateDepth':'lowerEndplateDepth';
  const measuredW=mm*(maxX-minX),measuredD=mm*(maxY-minY);
  const errW=100*(measuredW/ref[keyW]-1),errD=100*(measuredD/ref[keyD]-1);
  sections.push({surface,verticesSampled:n,widthMM:measuredW,depthMM:measuredD,
    targetWidthMM:ref[keyW],targetDepthMM:ref[keyD],
    widthErrorPct:errW,depthErrorPct:errD});
 }
 const maxAbsSectionErrorPct=Math.max(...sections.flatMap(s=>[Math.abs(s.widthErrorPct),Math.abs(s.depthErrorPct)]));
 return {
  reference:'Koziej et al. 2025; lumbar-reference-v1.2.json',
  sectionMethod:'Vertex extrema at z=±0.86*design anterior half-height, tolerance 0.23 project units, y>-2.65 (arch excluded).',
  sliceMeasurementsNotClinical:true,
  sections,
  maxAbsSectionErrorPct,
  designFitWithin2_5pct:maxAbsSectionErrorPct<=2.5
 };
}

const SETTINGS=Object.freeze({standard:.60,high:.43});
self.onmessage=function(event){
 const {id,level,quality,variant='crafted'}=event.data||{};
 try {
  if(!MORPH[level]||!Object.hasOwn(SETTINGS,quality)||!['legacy','refined','measured','crafted'].includes(variant))throw new Error('不正な形状要求');
  const step=(quality==='high'&&level==='L4'&&variant==='refined')?.44:SETTINGS[quality],t0=Date.now();
  objects.length=0;
  implicitMesh(level,'lumbar','M',p=>(variant==='legacy'?levelV08(p,level):variant==='refined'?levelV10(p,level):variant==='crafted'?levelV12(p,level):levelV11(p,level)),[-17.5,-19.2,85],[17.5,14,104],step);
  const m=objects[0];
  if(!m||!m.verts.length||!m.faces.length)throw new Error('形状生成結果が空です');
  // Validate manifold edge membership and connected components, not just faces.
  let invalid=0,zero=0,nonFinite=0;const edges=new Map(),adj=Array.from({length:m.verts.length},()=>[]);
  for(const v of m.verts)if(!v.every(Number.isFinite))nonFinite++;
  for(const f of m.faces){
   if(!f.every(i=>Number.isInteger(i)&&i>=0&&i<m.verts.length)){invalid++;continue}
   const [a,b,c]=f.map(i=>m.verts[i]),normal=V.cross(V.sub(b,a),V.sub(c,a));
   if(Math.hypot(...normal)<1e-9)zero++;
   for(let k=0;k<3;k++){
    const a=f[k],b=f[(k+1)%3],key=Math.min(a,b)+':'+Math.max(a,b);
    edges.set(key,(edges.get(key)||0)+1);adj[a].push(b);adj[b].push(a);
   }
  }
  let boundary=0,nonManifold=0;
  for(const n of edges.values()){if(n===1)boundary++;if(n>2)nonManifold++}
  const seen=new Uint8Array(m.verts.length);let components=0;
  for(let i=0;i<seen.length;i++){
   if(seen[i])continue;components++;const stack=[i];seen[i]=1;
   while(stack.length){const x=stack.pop();for(const n of adj[x])if(!seen[n]){seen[n]=1;stack.push(n)}}
  }
  if(invalid||zero||nonFinite||boundary||nonManifold||components!==1)
   throw new Error('メッシュ検査不合格：'+JSON.stringify({invalid,zero,nonFinite,boundary,nonManifold,components}));
  const positions=new Float32Array(m.verts.length*3);
  const indices=new Uint32Array(m.faces.length*3);
  m.verts.forEach((v,i)=>{positions[i*3]=v[0];positions[i*3+1]=v[1];positions[i*3+2]=v[2]-94});
  m.faces.forEach((f,i)=>indices.set(f,i*3));
  const proxy=(variant==='measured'||variant==='crafted')?sectionProxyAudit(m,level):null;
  // Color values are procedural illustration only. No externally sourced texture.
  let colors=null;
  if(variant==='crafted'){
   colors=new Float32Array(m.verts.length*3);
   for(let i=0;i<m.verts.length;i++){
    const [x,y,z]=m.verts[i];
    const fine=(.55*noise3(x*.70,y*.70,z*.70)
        +.30*noise3(x*1.95,y*1.95,z*1.95)
        +.15*noise3(x*5.80,y*5.80,z*5.80))-.50;
    const bodyMask=smoothStep01((y+.85)/2.5);
    const lightVariation=(.047*bodyMask+.020*(1-bodyMask))*fine;
    const v=Math.max(.85,Math.min(.99,.932+lightVariation));
    colors[3*i]=v;colors[3*i+1]=v*.960;colors[3*i+2]=v*.894;
   }
  }
  const result={id,level,quality,variant,vertices:m.verts.length,triangles:m.faces.length,step,elapsedMs:Date.now()-t0,proxy,topology:{components,boundary,nonManifold,zero,nonFinite},colors,positions,indices};
  objects.length=0;
  self.postMessage(result,colors?[positions.buffer,indices.buffer,colors.buffer]:[positions.buffer,indices.buffer]);
 }catch(error){
  objects.length=0;
  self.postMessage({id,level,quality,variant,error:String(error?.message||error)});
 }
};