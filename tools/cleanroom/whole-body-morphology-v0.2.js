// Original qualitative construction from anatomical descriptions, not traced vertices.
// No dimensions here are measured bone dimensions.
function implicitMesh(name,reg,side,field,lo,hi,step){
 const n=lo.map((v,i)=>Math.ceil((hi[i]-v)/step)+1),idx=(x,y,z)=>x+n[0]*(y+n[1]*z),values=new Float64Array(n[0]*n[1]*n[2]),coords=[];
 for(let z=0;z<n[2];z++)for(let y=0;y<n[1];y++)for(let x=0;x<n[0];x++){let p=[lo[0]+x*step,lo[1]+y*step,lo[2]+z*step],k=idx(x,y,z);coords[k]=p;values[k]=field(p)}
 const vs=[],fs=[],cache=new Map(),corners=[[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1]],tets=[[0,1,2,6],[0,2,3,6],[0,3,7,6],[0,7,4,6],[0,4,5,6],[0,5,1,6]];
 function vertex(a,b){let t=values[a]/(values[a]-values[b]);const end=t<1e-7?a:t>1-1e-7?b:null,key=end!==null?'p'+end:a<b?a+':'+b:b+':'+a;if(cache.has(key))return cache.get(key);let p=end!==null?coords[end]:coords[a].map((v,i)=>v+t*(coords[b][i]-v)),k=vs.length;vs.push(p);cache.set(key,k);return k}
 function tri(a,b,c){if(a===b||b===c||a===c)return;let norm=V.cross(V.sub(vs[b],vs[a]),V.sub(vs[c],vs[a]));if(Math.hypot(...norm)<1e-10)return;let p=vs[a].map((v,i)=>(v+vs[b][i]+vs[c][i])/3),g=[0,1,2].map(i=>{let h=[...p],l=[...p];h[i]+=.02;l[i]-=.02;return field(h)-field(l)});if(norm.reduce((s,v,i)=>s+v*g[i],0)<0)[b,c]=[c,b];fs.push([a,b,c])}
 for(let z=0;z<n[2]-1;z++)for(let y=0;y<n[1]-1;y++)for(let x=0;x<n[0]-1;x++){let c=corners.map(a=>idx(x+a[0],y+a[1],z+a[2]));if(c.every(k=>values[k]<0)||c.every(k=>values[k]>=0))continue;for(let t of tets){let a=t.map(k=>c[k]).filter(k=>values[k]<0),b=t.map(k=>c[k]).filter(k=>values[k]>=0);if(a.length===1)tri(...b.map(k=>vertex(a[0],k)));else if(a.length===3)tri(...a.map(k=>vertex(k,b[0])));else if(a.length===2){let q=[vertex(a[0],b[0]),vertex(a[0],b[1]),vertex(a[1],b[0]),vertex(a[1],b[1])];tri(q[0],q[1],q[2]);tri(q[1],q[3],q[2])}}}
 add(name,reg,side,vs,fs);
}
function ed(p,c,r){return (Math.hypot(...p.map((v,i)=>(v-c[i])/r[i]))-1)*Math.min(...r)}
function smoothMin(a,b,k){let h=Math.max(k-Math.abs(a-b),0)/k;return Math.min(a,b)-h*h*k*.25}
function skullField(p){
 let d=ed(p,[0,-1.7,168],[7.5,9.2,9]);
 d=smoothMin(d,ed(p,[0,4.6,160.1],[5.6,4.6,4.5]),1.1);
 for(let s of [-1,1]){d=smoothMin(d,ed(p,[s*5.9,5.6,161.3],[1.4,1.7,1.6]),.8);d=Math.max(d,-ed(p,[s*3.45,8.9,163.6],[2.3,4.2,2.25]))}
 // Piriform aperture approximation: narrower upper end, wider lower end.
 const nw=1.15+.25*Math.max(0,160.8-p[2]);
 d=Math.max(d,-ed(p,[0,9,159.9],[nw,3.6,2.15]));
 // Qualitative foramen magnum opening; internal cranial anatomy is not modeled.
 d=Math.max(d,-ed(p,[0,-1,156.8],[2.6,3.1,3.3]));return d;
}
function skull(){
 implicitMesh('頭蓋・眼窩・梨状口','head','M',skullField,[-9,-12,154],[9,11,178],.7);
 for(let s of [-1,1]){tube('頬骨弓','head','M',[[s*6.3,6,161],[s*7.6,3,161],[s*7.3,-.8,161]],.62);ell('乳様突起','head','M',[s*5.9,-1.7,157.9],[1,1.1,1.7]);
 let outline=[[s*5.8,-.2,159],[s*6.1,1.3,153.1],[s*4.9,4.5,153.4],[s*5.1,3.6,158.5],[s*5.9,1.7,157.5]],rv=[...outline.map(p=>[p[0]-.4,p[1],p[2]]),...outline.map(p=>[p[0]+.4,p[1],p[2]])],rf=[];for(let i=1;i<4;i++)rf.push([0,i,i+1],[5,5+i+1,5+i]);for(let i=0;i<5;i++){let k=(i+1)%5;rf.push([i,k,i+5],[k,k+5,i+5])}add('下顎枝','head','M',rv,rf);ell('下顎頭','head','M',[s*5.8,-.2,159],[1.1,.7,.65]);tube('下顎筋突起','head','M',[[s*5.9,2.2,154.8],[s*5.1,3.6,158.5]],.6)}
 let jaw=[],upper=[];for(let i=0;i<=20;i++){let t=i*Math.PI/20;jaw.push([5.8*Math.cos(t),3.1+5.7*Math.sin(t),152.8-.7*Math.sin(t)]);upper.push([4.8*Math.cos(t),3.4+5.3*Math.sin(t),156])}
 tube('下顎体','head','M',jaw,1.05);tube('上顎歯槽弓','head','M',upper,.85);
 for(let i=0;i<16;i++){let t=(i+.5)*Math.PI/16,x=4.7*Math.cos(t),y=3.5+5.4*Math.sin(t),rz=.5;ell('上顎歯冠'+(i+1),'head','M',[x,y,155.1],[.43,.56,rz]);ell('下顎歯冠'+(i+1),'head','M',[x*.96,y-.1,153.95],[.42,.52,rz])}
}
// Ringed loft with flat endplates and a shallow kidney indentation posteriorly.
function vertebralBody(name,reg,c,w,depth,h){let vs=[],fs=[],n=16;
 for(let j=0;j<4;j++){let z=[-h,-h*.67,h*.67,h][j],q=j===0||j===3?1:.92;for(let i=0;i<n;i++){let t=i*2*Math.PI/n,x=w*Math.cos(t)*q,y=depth*Math.sin(t)*q;if(y<0)y+=.42*Math.exp(-x*x/(w*w*.18));vs.push([c[0]+x,c[1]+y,c[2]+z])}}
 let a=vs.length;vs.push([c[0],c[1],c[2]-h],[c[0],c[1],c[2]+h]);for(let i=0;i<n;i++){let k=(i+1)%n;fs.push([a,k,i],[a+1,3*n+i,3*n+k]);for(let j=0;j<3;j++){let u=j*n+i,v=j*n+k;fs.push([u,v,u+n],[v,v+n,u+n])}}add(name,reg,'M',vs,fs)
}
function spine(){
 for(let i=0;i<24;i++){
  const neck=i<7,thor=i>=7&&i<19,reg=neck?'neck':thor?'back':'lumbar',level=neck?'C'+(i+1):thor?'T'+(i-6):'L'+(i-18);
  let z=neck?157-i*1.2:thor?147.2-(i-7)*2.4:117.7-(i-19)*3.1;
  let y=neck?1.4+1.1*Math.sin(i*Math.PI/6):thor?-3.3*Math.sin((i-7)*Math.PI/11):2.5*Math.sin((i-19)*Math.PI/5);
  let w=neck?2.1:thor?2.5+(i-7)*.07:3.7+(i-19)*.12,depth=neck?1.4:thor?2:2.5,h=neck?.43:thor?.8:1.07;
  if(i===0){let ring=[];for(let k=0;k<=20;k++){let t=k*2*Math.PI/20;ring.push([3.2*Math.cos(t),y-1.5+2.5*Math.sin(t),z])}tube('C1環椎輪','neck','M',ring,.5);for(let s of [-1,1])ell('C1外側塊','neck','M',[s*2.8,y-1.2,z],[.8,1.1,.75]);continue}
  vertebralBody('椎体'+(i+1),reg,[0,y,z],w,depth,h);
  if(i===1){tube('C2歯突起','neck','M',[[0,y,z+.3],[0,y,z+1.5]],.55);ell('C2歯突起先端','neck','M',[0,y,z+1.5],[.55,.55,.6])}
  const archY=y-depth-2.4,span=neck?2.4:thor?2.7:3.2;
  for(let s of [-1,1]){
   tube(level+'椎弓根・椎弓板',reg,'M',[[s*w*.75,y-depth*.4,z],[s*span,y-depth-1.4,z],[s*1.4,archY,z],[0,archY-.5,z]],neck?.42:.62);
   if(neck){let pts=[];for(let k=0;k<=12;k++){let t=k*2*Math.PI/12;pts.push([s*(3.1+.7*Math.cos(t)),y-1+.75*Math.sin(t),z])}tube(level+'横突孔周囲','neck','M',pts,.3)}
   else tube(level+'横突起',reg,'M',[[s*span,y-depth-1,z],[s*(thor?5.2:6),y-depth-(thor?2:1.2),z+(thor?.3:0)]],thor?.55:.5);
   ell(level+'関節突起模式',reg,'M',[s*span,y-depth-1.3,z+h*.65],[.65,.75,h*.8]);
  }
  if(neck&&i<6){for(let s of [-1,1])tube(level+'二分棘突起',reg,'M',[[0,archY-.3,z],[s*.55,archY-1.8,z-.25]],.35)}
  else tube(level+'棘突起',reg,'M',[[0,archY-.3,z],[0,archY-(thor?3.6:2.7),z-(thor?(i>9&&i<15?2.1:1):.1)]],thor?.6:neck?.45:.95);
 }
}
// Curved thin plate with a ridge, acromion and coracoid, rather than a tetrahedron.
function scapula(s){let side=s>0?'R':'L',z=A.shoulder,p=(x,y,h)=>[s*x,y,h];
 let rows=[[5.5,-6.5,z-1],[10,-8,z-3],[18,-6,z-1],[19.5,-5,z-4],[13,-8,z-17],[8,-8,z-11]],vs=rows.map(v=>p(...v)),fs=[[0,1,5],[1,4,5],[1,3,4],[1,2,3]];add('肩甲骨体','shoulder',side,vs,fs);
 tube('肩甲棘','shoulder',side,[p(6,-7,z-4),p(12,-9,z-4),p(18,-7,z-2)],.75);tube('肩峰','shoulder',side,[p(18,-7,z-2),p(21,-3,z+.1),p(21.5,1,z)],1);tube('烏口突起','shoulder',side,[p(18,-4,z-3),p(18,1,z-2),p(17.5,3,z-3)],.6);ell('関節窩模式','shoulder',side,p(20,-2,z-3.2),[.8,1.4,2]);
}
// Iliac fan surfaces and pubic/ischial rami leave a real opening in projection.
function pelvisSide(s){let side=s>0?'R':'L',p=(x,y,z)=>[s*x,y,z],top=A.crest-1,hip=A.trochanter+3;
 let rim=[[4,-4,top-3],[6,-7,top],[11,-7,top+.7],[16,-4,top-.5],[17,0,top-3],[15,4,top-5]],base=[10,-1,hip+1],vs=[p(...base),...rim.map(v=>p(...v))],fs=[];for(let i=1;i<rim.length;i++)fs.push([0,i,i+1]);add('腸骨翼','pelvis',side,vs,fs);tube('腸骨稜','pelvis',side,rim.map(v=>p(...v)),.7);
 ell('寛骨臼周縁模式','pelvis',side,p(10.8,1,hip),[2.9,2.5,2.5]);
 tube('恥骨枝','pelvis',side,[p(10,2,hip),p(5,6,hip-4),p(1,6,hip-7)],1.2);
 tube('坐骨・下恥骨枝','pelvis',side,[p(10,-1,hip),p(10,-3,hip-8),p(7,-1,hip-11),p(1,6,hip-7)],1.25);
}
// Tapered, slightly bowed shafts and separate articular-end lobes.
function shaft(name,reg,side,a,b,r0,r1){let pts=[],vs=[],fs=[],n=12;for(let j=0;j<=8;j++){let t=j/8,p=a.map((v,i)=>v+(b[i]-v)*t);p[1]+=.55*Math.sin(t*Math.PI);let r=(r0+(r1-r0)*t)*(1-.22*Math.sin(t*Math.PI));for(let i=0;i<n;i++){let q=i*2*Math.PI/n;vs.push([p[0]+r*Math.cos(q),p[1]+r*.78*Math.sin(q),p[2]])}}for(let j=0;j<8;j++)for(let i=0;i<n;i++){let a=j*n+i,b=j*n+(i+1)%n;fs.push([a,b,a+n],[b,b+n,a+n])}let k=vs.length;vs.push(a,b);for(let i=0;i<n;i++)fs.push([k,(i+1)%n,i],[k+1,8*n+i,8*n+(i+1)%n]);add(name,reg,side,vs,fs)}
function sacrum(){implicitMesh('仙骨・仙骨孔','pelvis','M',p=>{let width=2.2+(p[2]-86)*.25,d=ed(p,[0,-2,94],[Math.max(2,width),2.6,9]);for(let s of [-1,1])for(let k=0;k<4;k++)d=Math.max(d,-ed(p,[s*(2.5-k*.3),-2,98-k*2.8],[.65,5,.65]));return d},[-7,-6,84],[7,3,104],.7);tube('尾骨','pelvis','M',[[0,-2,86],[0,-.5,83],[0,1,81.5]],.7)}
