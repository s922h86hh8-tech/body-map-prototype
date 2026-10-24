// Authored shapes for isolated review. All coordinates are design values.
// Original Gray 1918 figs 188/190 and 92/93 were inspected qualitatively.
// No image pixels, extracted outlines, third-party mesh or scan coordinates used.
const SHAPE_REVIEW={version:'0.8',units:'arbitrary drawing units',anatomicalApproval:false,
 sources:{skull:['Gray 1918 Fig.188 lateral','Gray 1918 Fig.190 frontal','Gray 1918 Fig.157 maxilla','Gray 1918 Fig.176/177 mandible'],lumbar:['Gray 1918 Fig.92 lateral','Gray 1918 Fig.93 above/posterior']},
 design:{cranialCenter:[0,-2.5,4.2],cranialRadii:[7.15,9.1,6.9],skullGridStep:.3,jawGridStep:.25,lumbarGridStep:.18},
 scope:'Original qualitative surface study; not an individual specimen or validated anatomy.'};
function superD(p,c,r,n=2.4){return (Math.pow(p.reduce((s,v,i)=>s+Math.pow(Math.abs((v-c[i])/r[i]),n),0),1/n)-1)*Math.min(...r)}
function segmentD(p,a,b,r){const q=p.map((v,i)=>v/r[i]),aa=a.map((v,i)=>v/r[i]),bb=b.map((v,i)=>v/r[i]),d=V.sub(bb,aa),den=d.reduce((s,v)=>s+v*v,0),t=Math.max(0,Math.min(1,V.sub(q,aa).reduce((s,v,i)=>s+v*d[i],0)/den));return (Math.hypot(...V.sub(q,V.add(aa,V.mul(d,t))))-1)*Math.min(...r)}
const minBlend=(a,b,k=.35)=>smoothMin(a,b,k);
const maxBlend=(a,b,k=.2)=>-smoothMin(-a,-b,k);
// Revised authored surfaces after qualitative review of Gray 1918 figs188/190/157/176.
// None of these coordinates are extracted landmarks or measured dimensions.
function vaultD(p){
 let d=ed(p,[0,-2.5,4.2],[7.15,9.1,6.9]);
 d=minBlend(d,ed(p,[0,-7,1.7],[5.3,4.1,4.0]),.9);
 d=minBlend(d,ed(p,[0,3.3,3.2],[6.15,3.15,4.7]),.9);
 return d;
}
function orbitD(p,s){
 // Rounded quadrilateral entrance, tapering posteriorly and medially.
 // Four principal walls are retained; this is not a specimen-derived orbit.
 const t=Math.max(0,Math.min(1,(p[1]-.45)/6.7)),cx=2.15+1.0*t;
 const sx=.22+.78*t,sz=.24+.76*t,dx=(s*p[0]-cx)/sx,dz=(p[2]+.5)/sz;
 const outline=[[-1.9,-.9],[-1.45,-1.5],[1.35,-1.4],[2.05,-.25],[1.6,1.45],[-.85,1.75],[-2.0,.9]];
 let q=-1e6;
 for(let i=0;i<outline.length;i++){
  const a=outline[i],b=outline[(i+1)%outline.length],ex=b[0]-a[0],ez=b[1]-a[1];
  const plane=((dx-a[0])*ez-(dz-a[1])*ex)/Math.hypot(ex,ez)*Math.min(sx,sz);
  q=maxBlend(q,plane,.24);
 }
 return maxBlend(q,.45-p[1],.2);
}
function maxillaBodyD(p){
 const x=Math.abs(p[0]),z=p[2],front=Math.max(0,Math.min(1,(p[1]-4.8)/1.3));
 const g=(cx,cz,wx,wz)=>Math.exp(-Math.pow((x-cx)/wx,2)-Math.pow((z-cz)/wz,2));
 // A shallow continuous canine fossa lateral to a vertical canine eminence.
 // Deform the anterior surface, rather than drilling a separate spherical pit.
 const shift=front*(.48*g(3.1,-4.65,1.0,1.05)+.16*g(.75,-5.5,.65,.55)-.25*g(2.05,-5.6,.48,1.0));
 return ed([p[0],p[1]+shift,p[2]],[0,4.65,-4.35],[4.8,2.35,2.65]);
}
function nasalInteriorD(p){
 // Simplified continuous bony septum. Ethmoid/vomer boundary is not segmented.
 let d=superD(p,[0,4.0,-4.15],[.19,2.35,2.35],3);
 for(const s of [-1,1]){
  // Curved inferior conchal lamina: rooted laterally, with a free medial edge.
  // Thickness is a drawing choice, not a measured anatomical thickness.
  const u=(s*p[0]-1.12)/.55,z=-4.45+.38*u*u;
  const plate=Math.max(Math.abs(p[2]-z)-.16,Math.abs(p[1]-4.45)-1.05,Math.abs(u)-1);
  d=minBlend(d,plate,.16);
 }
 return d;
}
function nasalD(p){
 // Rounded, inferiorly broader entrance; no flat-sided trapezoid.
 const u=(p[2]+4.15)/2.05,rx=Math.max(.55,1.25-.28*u);
 return ed(p,[0,7.1,-4.15],[rx,5.1,2.05]);
}
function archBand(p,rx,ry,y0,zc,halfWidth,halfHeight,n=2.5){
 const y=p[1]-y0,q=Math.hypot(p[0]/rx,y/ry),cos=Math.min(1,Math.abs(p[0])/rx);
 const radial=(q-1)*Math.min(rx,ry),z=p[2]-(zc[0]+zc[1]*cos*cos),hz=halfHeight[0]+halfHeight[1]*cos*cos;
 const cross=(Math.pow(Math.pow(Math.abs(radial/halfWidth),n)+Math.pow(Math.abs(z/hz),n),1/n)-1)*Math.min(halfWidth,hz);
 return Math.max(cross,y0-.25-p[1]);
}
function skullNewField(p){
 let d=vaultD(p);
 // Broad continuous maxillary envelope, recessed laterally into the cheek.
 d=minBlend(d,maxillaBodyD(p),1.35);
 d=minBlend(d,archBand(p,4.5,5.7,1.4,[-6.75,.25],.4,[.6,0],2.4),.85);
 for(const s of [-1,1]){
  d=minBlend(d,superD(p,[s*5.25,-2.8,-1.0],[1.25,3.2,2.0],2.3),.65);
  d=minBlend(d,segmentD(p,[s*5.6,-3,-.5],[s*5.4,-3.7,-3.1],[.65,.85,.8]),.45);
  d=minBlend(d,ed(p,[s*5.4,-3.7,-3.1],[.7,.9,1.4]),.4);
  // Thin orbital floor behind the facial margin, rather than a protruding shelf.
  d=minBlend(d,ed(p,[s*3.3,3.6,-2.5],[2.15,2.55,.38]),1.05);
  // Oblique cheek envelope blends broadly into the maxilla, with no diagonal tube.
  d=minBlend(d,ed(p,[s*4.65,3.8,-2.75],[1.4,1.75,1.65]),1.65);
  d=minBlend(d,ed(p,[s*5.25,3.5,-1.9],[1.2,1.65,1.35]),1.35);
  d=minBlend(d,segmentD(p,[s*5.45,4.75,-1.85],[s*5.65,4.3,1.0],[.42,.55,.5]),.85);
  const controls=[[5.8,3.9,-2.1],[6.7,2.5,-2.0],[6.7,-.8,-1.9],[6.05,-2.8,-1.65]];
  for(let k=0;k<6;k++)d=minBlend(d,segmentD(p,bezierArch(controls,k/6,s),bezierArch(controls,(k+1)/6,s),[.38,.5,.32]),.45);
 }
 // Frontal surface itself forms the superior orbital margin; no added brow tubes.
 for(const s of [-1,1])d=minBlend(d,segmentD(p,[s*.8,6.15,.25],[s*1.05,6.55,-3.2],[.32,.48,.6]),.7);
 d=minBlend(d,segmentD(p,[0,6.3,.25],[0,7.35,-2.1],[.52,.42,.45]),.6);
 d=maxBlend(d,-orbitD(p,-1),.28);d=maxBlend(d,-orbitD(p,1),.28);
 d=maxBlend(d,-nasalD(p),.22);
 d=minBlend(d,nasalInteriorD(p),.12);
 d=minBlend(d,ed(p,[0,7.3,-6.05],[.28,.5,.23]),.35);
 d=Math.max(d,-ed(p,[0,-2.7,-5.7],[2.2,2.8,3.2]));
 for(const s of [-1,1]){
  d=Math.max(d,-segmentD(p,[s*5.35,-2.7,-2.6],[s*8,-2.7,-2.6],[1.2,.5,.6]));
  // Infraorbital aperture only; the previous isolated canine-pit subtraction is removed.
  d=maxBlend(d,-ed(p,[s*2.75,6.75,-3.25],[.18,.9,.17]),.06);
 }
 return d;
}
function jawNewField(p){
 // A broad horseshoe-shaped mandibular body instead of joined circular tubes.
 let d=archBand(p,4.6,5.6,1.1,[-10.3,.7],.65,[1.5,-.55],3);
 d=minBlend(d,ed(p,[0,6.85,-10.55],[1.25,.5,1.0]),.35);
 for(const s of [-1,1]){
  // Rounded gonial angle with an inclined anterior ramus border.
  let r=polygonExtrusion(p,s*4.55,[[0,-10.2],[2.7,-10.0],[3.1,-8.1],[3.0,-6.0],[2.6,-4.6],[-.6,-4.6],[-1.4,-8.9],[-1.0,-9.65]],.6)-.25;
  r=minBlend(r,segmentD(p,[s*4.55,-.8,-6],[s*4.85,-1.15,-3.1],[.55,.6,.65]),.4);
  r=minBlend(r,ed(p,[s*4.85,-1.15,-3.05],[1.0,.6,.5]),.3);
  r=minBlend(r,polygonExtrusion(p,s*4.55,[[1.7,-5.9],[2.8,-3.25],[3.2,-5.7]],.42)-.12,.4);
  r=Math.max(r,-ed(p,[s*4.6,.6,-3.8],[1.5,1.35,1.15]));
  d=minBlend(d,r,.6);
  d=minBlend(d,segmentD(p,[s*4.8,2.8,-7.5],[s*3.7,5.3,-9.3],[.25,.35,.3]),.25);
  d=Math.max(d,-ed(p,[s*2.8,6.1,-9.55],[.24,1.1,.24]));
 }
 return d;
}
function toothArchNew(){
 for(const upper of [true,false])for(let i=0;i<16;i++){
  const t=(i+.5)*Math.PI/16,j=Math.min(i,15-i),x=4.5*Math.cos(t),y=1.4+5.7*Math.sin(t),z=(upper?-7.85:-8.95)+.45*Math.abs(Math.cos(t));
  const front=j>=6,canine=j===5,molar=j<=2,rx=front?.41:canine?.42:molar?.56:.46,ry=front?.31:canine?.4:molar?.62:.47,rz=canine?.62:front?.52:.45;
  crownMesh((upper?'上':'下')+'歯冠'+(i+1),[x*(upper?1:.97),y+(upper?.08:0),z],[rx,ry,rz],t,upper,front);
 }
}
function buildSkullNew(){
 implicitMesh('頭蓋・顔面連続面','head','M',skullNewField,[-9,-13,-9],[9,12,13],.3);
 implicitMesh('下顎連続面','head','M',jawNewField,[-7,-3,-13],[7,10,-1],.25);
 toothArchNew();
}
// Interpolated cross-sections: every row is an authored design section, not a scan.
const LUMBAR_SECTIONS=[[-1.75,4.1,3.05],[-1.5,4,2.95],[-.8,3.7,2.7],[0,3.6,2.6],[.8,3.75,2.75],[1.5,4.1,3],[1.7,4.15,3.05]];
function section(z){let a=LUMBAR_SECTIONS[0],b=LUMBAR_SECTIONS.at(-1);for(let i=0;i<LUMBAR_SECTIONS.length-1;i++)if(z>=LUMBAR_SECTIONS[i][0]&&z<=LUMBAR_SECTIONS[i+1][0]){a=LUMBAR_SECTIONS[i];b=LUMBAR_SECTIONS[i+1];break}let t=Math.max(0,Math.min(1,(z-a[0])/(b[0]-a[0])));return [a[1]+t*(b[1]-a[1]),a[2]+t*(b[2]-a[2])]}
function lumbarBodyD(p){
 let [w,deep]=section(p[2]),x=p[0],y=p[1]-1.5;
 // Reniform posterior indentation; edge thickens towards the endplates.
 let py=y+(y<0?.7*Math.exp(-x*x/3):0),rad=(Math.pow(Math.pow(Math.abs(x/w),2.5)+Math.pow(Math.abs(py/deep),2.5),1/2.5)-1)*2.6;
 let end=Math.max(-1.75-p[2],p[2]-1.7),d=Math.max(rad,end);
 // Shallow endplate concavity with a retained peripheral rim.
 const r=Math.hypot(x/3.5,y/2.6),dip=.15*Math.max(0,1-r*r);
 return Math.max(d,p[2]-(1.7-dip),(-1.75+dip)-p[2]);
}
function lumbarNewField(p){
 let d=lumbarBodyD(p);
 for(let s of [-1,1]){
  // Pedicles are thick roots; laminae broaden toward the spinous base.
  d=minBlend(d,segmentD(p,[s*2.8,-.3,.65],[s*2.65,-2.5,.55],[.85,.9,.9]),.5);
  d=minBlend(d,segmentD(p,[s*2.65,-2.5,.55],[s*.65,-4.3,.2],[.85,.7,.95]),.5);
  // Long, flattened transverse process tapers from root to tip.
  d=minBlend(d,segmentD(p,[s*2.8,-1.5,.1],[s*4.8,-2,.1],[1.1,.7,.55]),.5);
  d=minBlend(d,segmentD(p,[s*4.6,-2,.1],[s*7.1,-1.7,.3],[.9,.45,.35]),.45);
  // Articular pillars with concave upper and convex lower facet approximations.
  d=minBlend(d,superD(p,[s*2.65,-2.6,1.65],[.95,1.05,1.3],2.6),.45);
  d=minBlend(d,superD(p,[s*1.95,-3.1,-1.3],[.7,.9,1.25],2.6),.45);const n=V.unit([s*.78,.62,-.08]);d=minBlend(d,orientedEllipsoidD(p,V.add([s*1.95,-3.1,-1.4],V.mul(n,.32)),n,[.65,.9,.5]),.25);d=minBlend(d,ed(p,[s*3.05,-3.05,2.2],[.42,.45,.7]),.3);
 }
 // Broad quadrilateral spinous plate rather than a circular rod.
 d=minBlend(d,polygonExtrusion(p,0,[[-4.1,.9],[-7.45,.35],[-7.8,-1.35],[-6.6,-1.65],[-4.05,-.6]],.9)-.16,.45);
 // A triangular canal is defined independently of the assembled arch pieces.
 const canal=Math.max(Math.abs(p[0])-(1.65+.38*(p[1]+2.0)),p[1]+.8,-4.1-p[1]);
 d=Math.max(d,-canal);
 // Concave inward/backward superior facet surfaces; still qualitative.
 for(let s of [-1,1]){const n=V.unit([-s*.78,-.62,.08]),c=V.add([s*2.65,-2.6,1.65],V.mul(n,.88));d=Math.max(d,-orientedEllipsoidD(p,c,n,[.8,1.05,1.0]));d=maxBlend(d,-ed(p,[s*3.1,-1.1,-1.7],[.6,.9,.4]),.1);}
 return d;
}
function buildLumbarNew(){implicitMesh('腰椎連続面','lumbar','M',lumbarNewField,[-9,-9,-4],[9,6,4],.18)}

function crownMesh(name,c,r,t,upper,incisor){let vs=[],fs=[],n=12,levels=[[-1,.86,.8],[-.7,1,1],[.65,.94,1],[1,.75,.75]],tx=-4.65*Math.sin(t),ty=6*Math.cos(t),len=Math.hypot(tx,ty);tx/=len;ty/=len;for(let j=0;j<4;j++)for(let i=0;i<n;i++){let a=i*2*Math.PI/n,power=incisor?.5:.67,x=Math.sign(Math.cos(a))*Math.pow(Math.abs(Math.cos(a)),power)*r[0]*levels[j][1],y=Math.sign(Math.sin(a))*Math.pow(Math.abs(Math.sin(a)),power)*r[1]*levels[j][2];vs.push([c[0]+tx*x-ty*y,c[1]+ty*x+tx*y,c[2]+r[2]*levels[j][0]])}for(let j=0;j<3;j++)for(let i=0;i<n;i++){let a=j*n+i,b=j*n+(i+1)%n;fs.push([a,b,a+n],[b,b+n,a+n])}let k=vs.length;vs.push([c[0],c[1],c[2]-r[2]],[c[0],c[1],c[2]+r[2]]);for(let i=0;i<n;i++)fs.push([k,(i+1)%n,i],[k+1,3*n+i,3*n+(i+1)%n]);add(name,'head','M',vs,fs)}

// Cubic design curve for a continuous arch; not traced image coordinates.
function bezierArch(c,t,s){const u=1-t;return [0,1,2].map(i=>(i===0?s:1)*(u*u*u*c[0][i]+3*u*u*t*c[1][i]+3*u*t*t*c[2][i]+t*t*t*c[3][i]))}
function polygonExtrusion(p,x0,pts,half){let inside=false,dist=1e6,y=p[1],z=p[2];for(let i=0,j=pts.length-1;i<pts.length;j=i++){const a=pts[j],b=pts[i],dy=b[0]-a[0],dz=b[1]-a[1],t=Math.max(0,Math.min(1,((y-a[0])*dy+(z-a[1])*dz)/(dy*dy+dz*dz)));dist=Math.min(dist,Math.hypot(y-a[0]-t*dy,z-a[1]-t*dz));if((a[1]>z)!==(b[1]>z)&&y<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0])inside=!inside}return Math.max((inside?-1:1)*dist,Math.abs(p[0]-x0)-half)}
function orientedEllipsoidD(p,c,n,r){const u=V.unit([-n[1],n[0],0]),v=V.cross(n,u),q=V.sub(p,c),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);return ed([dot(q,u),dot(q,v),dot(q,n)],[0,0,0],r)}
