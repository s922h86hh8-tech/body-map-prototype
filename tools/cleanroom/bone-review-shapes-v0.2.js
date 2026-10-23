// Authored shapes for isolated review. All coordinates are design values.
// Original Gray 1918 figs 188/190 and 92/93 were inspected qualitatively.
// No image pixels, extracted outlines, third-party mesh or scan coordinates used.
const SHAPE_REVIEW={version:'0.2',units:'arbitrary drawing units',anatomicalApproval:false,
 sources:{skull:['Gray 1918 Fig.188 lateral','Gray 1918 Fig.190 frontal','Gray 1918 Fig.157 maxilla','Gray 1918 Fig.176/177 mandible'],lumbar:['Gray 1918 Fig.92 lateral','Gray 1918 Fig.93 above/posterior']},
 design:{cranialCenter:[0,-2.2,4.7],cranialRadii:[7.2,9.4,7.5],skullGridStep:.5,lumbarGridStep:.25},
 scope:'Original qualitative surface study; not an individual specimen or validated anatomy.'};
function superD(p,c,r,n=2.4){return (Math.pow(p.reduce((s,v,i)=>s+Math.pow(Math.abs((v-c[i])/r[i]),n),0),1/n)-1)*Math.min(...r)}
function segmentD(p,a,b,r){const q=p.map((v,i)=>v/r[i]),aa=a.map((v,i)=>v/r[i]),bb=b.map((v,i)=>v/r[i]),d=V.sub(bb,aa),den=d.reduce((s,v)=>s+v*v,0),t=Math.max(0,Math.min(1,V.sub(q,aa).reduce((s,v,i)=>s+v*d[i],0)/den));return (Math.hypot(...V.sub(q,V.add(aa,V.mul(d,t))))-1)*Math.min(...r)}
const minBlend=(a,b,k=.35)=>smoothMin(a,b,k);
const maxBlend=(a,b,k=.2)=>-smoothMin(-a,-b,k);
function vaultD(p){
 // Cranial vault, lower occiput and flattened frontal squama are blended surfaces.
 let d=ed(p,[0,-2.2,4.7],[7.2,9.4,7.5]);
 d=minBlend(d,ed(p,[0,-7,.1],[5.6,4.4,5.8]),.9);
 d=minBlend(d,superD(p,[0,3.7,3.5],[6.25,3.2,3.8],2.5),.9);
 return d;
}
function orbitD(p,s){
 // Truncated pyramidal recess, rounded quadrilateral rim, posteriorly narrowing.
 let t=Math.max(0,Math.min(1,(p[1]-1)/7)),dx=s*p[0]-(2.2+1.05*t),dz=p[2]+.55-.14*dx;
 let rx=.65+1.8*t,rz=.55+1.35*t;
 const q=(Math.pow(Math.pow(Math.abs(dx/rx),2.6)+Math.pow(Math.abs(dz/rz),2.6),1/2.6)-1)*Math.min(rx,rz);
 return Math.max(q,1-p[1],p[1]-14);
}
function nasalD(p){let z=p[2]+4.2,rx=1.25-.18*z;return Math.max(ed(p,[0,8,-4.2],[Math.max(.5,rx),4,2.25]),4.2-p[1])}
function skullNewField(p){
 let d=vaultD(p);
 // Maxilla and a thinner bridge between orbit and alveolar arch.
 d=minBlend(d,superD(p,[0,6.05,-4.8],[4.25,2.75,2.55],2.5),.7);
 if(p[2]<-5.4){for(let i=0;i<20;i++){let a=i*Math.PI/20,b=(i+1)*Math.PI/20;d=minBlend(d,segmentD(p,[4.65*Math.cos(a),1.7+6*Math.sin(a),-6.8+.4*Math.abs(Math.cos(a))],[4.65*Math.cos(b),1.7+6*Math.sin(b),-6.8+.4*Math.abs(Math.cos(b))],[.65,.75,.65]),.4)}}
 for(let s of [-1,1]){
  d=minBlend(d,superD(p,[s*5.2,-2,-1.5],[1.5,3.5,2.3],2.3),.7);
  d=minBlend(d,segmentD(p,[s*5.7,-2.5,.5],[s*5.3,-3.5,-5],[.8,1,1]),.45);
  d=minBlend(d,superD(p,[s*5.45,4.4,-2.3],[1.35,2.1,1.45],2.7),.6);
  d=minBlend(d,segmentD(p,[s*5.7,4.2,-2.4],[s*6.2,4.8,1.4],[.85,1.2,.9]),.5);
  d=minBlend(d,segmentD(p,[s*5.6,4.6,-2.4],[s*3.8,7,-5.2],[.7,1.1,.85]),.45);
  // Zygomatic arch continuous with its temporal root; temporal space is left open.
  const controls=[[6,4.6,-2.3],[7,3.2,-2.35],[7,.1,-2.65],[6.2,-2.2,-2.1]];for(let k=0;k<6;k++)d=minBlend(d,segmentD(p,bezierArch(controls,k/6,s),bezierArch(controls,(k+1)/6,s),[.5,.65,.45]),.38);
  d=minBlend(d,ed(p,[s*5.3,-3.5,-5],[.85,1.2,1.55]),.4);
 }
 // Rounded brow and nasal bones; cavity subtraction follows the union.
 for(let s of [-1,1]){const brow=[[s*.8,7.1,.5],[s*2.6,7,1.25],[s*4.4,6.6,1.15],[s*6,5.2,.4]];for(let i=0;i<3;i++)d=minBlend(d,segmentD(p,brow[i],brow[i+1],[.6,.85,.6]),.45)}
 d=minBlend(d,superD(p,[0,7,-1.5],[.9,1.1,1.6],2.3),.4);
 d=maxBlend(d,-orbitD(p,-1),.15);d=maxBlend(d,-orbitD(p,1),.15);
 d=maxBlend(d,-nasalD(p),.14);
 // Foramen magnum opens the lower posterior base, not the orbit.
 d=Math.max(d,-ed(p,[0,-2.7,-6],[2.2,2.8,3.5]));
 for(let s of [-1,1]){
  d=Math.max(d,-segmentD(p,[s*4.8,-1.4,-3.4],[s*8,-1.4,-3.4],[1.5,.58,.7]));
  d=maxBlend(d,-ed(p,[s*2.85,8.55,-4.95],[1.05,1.0,.85]),.12);d=Math.max(d,-ed(p,[s*2.7,8.1,-3.7],[.32,1.2,.3]));
 }
 return d;
}
function jawNewField(p){
 let d=1e3;
 // U-shaped body: an anterior chin continuous with the horizontal body.
 for(let i=0;i<24;i++){let a=i*Math.PI/24,b=(i+1)*Math.PI/24;
  const pa=[5.1*Math.cos(a),1.5+6.4*Math.sin(a),-10.3+1.5*Math.pow(Math.cos(a),2)],pb=[5.1*Math.cos(b),1.5+6.4*Math.sin(b),-10.3+1.5*Math.pow(Math.cos(b),2)];
  d=minBlend(d,segmentD(p,pa,pb,[.65,.8,1.15-.7*Math.pow(Math.cos((a+b)/2),2)]),.4)
 }
 for(let s of [-1,1]){
  // Broad ramus with a sigmoid notch separating condyle and coronoid.
  let r=superD(p,[s*5.15,1,-6.1],[.75,2.35,2.8],3);
  r=minBlend(r,segmentD(p,[s*5.3,-.7,-6],[s*5.3,-1.2,-3.1],[.65,.75,.8]),.45);
  r=minBlend(r,ed(p,[s*5.3,-1.2,-3.1],[1.2,.64,.55]),.35);
  r=minBlend(r,polygonExtrusion(p,s*5.0,[[1.7,-5.9],[3.1,-3.05],[3.5,-5.8]],.5)-.12,.35);
  r=Math.max(r,-ed(p,[s*5.1,.8,-3.5],[1.5,1.1,.95]));
  d=minBlend(d,r,.55);
  d=minBlend(d,segmentD(p,[s*4.8,2.8,-7.5],[s*3.4,6.3,-9],[.3,.45,.4]),.25);d=Math.max(d,-ed(p,[s*2.8,7.25,-9.4],[.28,1.3,.28]));
 }
 return d;
}
function toothArchNew(){
 for(let upper of [true,false])for(let i=0;i<16;i++){
  let t=(i+.5)*Math.PI/16,x=4.65*Math.cos(t),y=1.7+6.0*Math.sin(t),z=(upper?-7.95:-8.85)+.5*Math.abs(Math.cos(t));
  // Incisors have a flatter crown; posterior crowns are broader. No roots modeled.
  let front=Math.sin(t)>.85,rx=front?.43:.52,ry=front?.35:.65,rz=front?.5:.42;
  crownMesh((upper?'上':'下')+'歯冠'+(i+1),[x*(upper?1:.97),y+(upper?.1:0),z],[rx,ry,rz],t,upper,front);
 }
}
function buildSkullNew(){
 implicitMesh('頭蓋・顔面連続面','head','M',skullNewField,[-9,-13,-9],[9,12,13],.5);
 implicitMesh('下顎連続面','head','M',jawNewField,[-7,-3,-12],[7,10,-1],.4);
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
function buildLumbarNew(){implicitMesh('腰椎連続面','lumbar','M',lumbarNewField,[-9,-9,-4],[9,6,4],.25)}

function crownMesh(name,c,r,t,upper,incisor){let vs=[],fs=[],n=12,levels=[[-1,.86,.8],[-.7,1,1],[.65,.94,1],[1,.75,.75]],tx=-4.65*Math.sin(t),ty=6*Math.cos(t),len=Math.hypot(tx,ty);tx/=len;ty/=len;for(let j=0;j<4;j++)for(let i=0;i<n;i++){let a=i*2*Math.PI/n,power=incisor?.5:.67,x=Math.sign(Math.cos(a))*Math.pow(Math.abs(Math.cos(a)),power)*r[0]*levels[j][1],y=Math.sign(Math.sin(a))*Math.pow(Math.abs(Math.sin(a)),power)*r[1]*levels[j][2];vs.push([c[0]+tx*x-ty*y,c[1]+ty*x+tx*y,c[2]+r[2]*levels[j][0]])}for(let j=0;j<3;j++)for(let i=0;i<n;i++){let a=j*n+i,b=j*n+(i+1)%n;fs.push([a,b,a+n],[b,b+n,a+n])}let k=vs.length;vs.push([c[0],c[1],c[2]-r[2]],[c[0],c[1],c[2]+r[2]]);for(let i=0;i<n;i++)fs.push([k,(i+1)%n,i],[k+1,3*n+i,3*n+(i+1)%n]);add(name,'head','M',vs,fs)}

// Cubic design curve for a continuous arch; not traced image coordinates.
function bezierArch(c,t,s){const u=1-t;return [0,1,2].map(i=>(i===0?s:1)*(u*u*u*c[0][i]+3*u*u*t*c[1][i]+3*u*t*t*c[2][i]+t*t*t*c[3][i]))}
function polygonExtrusion(p,x0,pts,half){let inside=false,dist=1e6,y=p[1],z=p[2];for(let i=0,j=pts.length-1;i<pts.length;j=i++){const a=pts[j],b=pts[i],dy=b[0]-a[0],dz=b[1]-a[1],t=Math.max(0,Math.min(1,((y-a[0])*dy+(z-a[1])*dz)/(dy*dy+dz*dz)));dist=Math.min(dist,Math.hypot(y-a[0]-t*dy,z-a[1]-t*dz));if((a[1]>z)!==(b[1]>z)&&y<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0])inside=!inside}return Math.max((inside?-1:1)*dist,Math.abs(p[0]-x0)-half)}
function orientedEllipsoidD(p,c,n,r){const u=V.unit([-n[1],n[0],0]),v=V.cross(n,u),q=V.sub(p,c),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);return ed([dot(q,u),dot(q,v),dot(q,n)],[0,0,0],r)}
