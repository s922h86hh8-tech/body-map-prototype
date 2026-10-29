// L3 independent landmark-loft geometry v2.0.
// Hand-authored anatomical constraints, no traced mesh vertices, no third-party textures.
const KIDNEY_HALF=[[0,.75],[1.7,-.1],[3.5,-.91],[5.65,-1.24],[7.50,-.16],[8.15,2.95],[8.01,5],[6.70,7.68],[4.10,9.48],[0,10]];
const KIDNEY_POLAR=KIDNEY_HALF.map(([x,y])=>[Math.atan2(y-4,x),Math.hypot(x,y-4)]);
function kidneyRadius(angle){
 const a=KIDNEY_POLAR;let i=0;while(i<a.length-2&&angle>a[i+1][0])i++;
 const t=clamp((angle-a[i][0])/(a[i+1][0]-a[i][0]),0,1),p1=a[i][1],p2=a[i+1][1],p0=a[Math.max(0,i-1)][1],p3=a[Math.min(a.length-1,i+2)][1];
 return (2*t*t*t-3*t*t+1)*p1+(t*t*t-2*t*t+t)*(p2-p0)*.5+(-2*t*t*t+3*t*t)*p2+(t*t*t-t*t)*(p3-p1)*.5;
}
function sectionLoft(p,axis,sections){
 const a=p[axis];let j=0;while(j<sections.length-2&&a>sections[j+1][0])j++;
 const A=sections[j],B=sections[j+1],q=clamp((a-A[0])/(B[0]-A[0]),0,1),t=q*q*(3-2*q),mix=k=>A[k]+(B[k]-A[k])*t;
 const u=axis===0?1:0,v=axis===2?1:2,r0=mix(3),r1=mix(4);
 const cross=(Math.hypot((p[u]-mix(1))/r0,(p[v]-mix(2))/r1)-1)*Math.min(r0,r1);
 const cap=Math.max(sections[0][0]-a,a-sections.at(-1)[0]);
 return Math.hypot(Math.max(cross,0),Math.max(cap,0))+Math.min(Math.max(cross,cap),0);
}
function smoothMaxLoft(a,b,k){return -smoothMin(-a,-b,k)}
function L3LandmarkLoftV2(p){
 const [x,y,z]=p,ax=Math.abs(x),dz=z-94,t=calibratedLumbarParameters('L3'),u=clamp((dz/t.H+1)/2,0,1);
 const waist=Math.pow(Math.max(0,1-(dz/t.H)**2),1.4);
 const widthScale=((1-u)*t.Wlower+u*t.W)/8.15*(1-.08*waist);
 const depthScale=((1-u)*t.Dlower+u*t.D)*2/11.25*(1-.052*waist);
 const rx=ax/widthScale,ry=(y-4)/depthScale,theta=Math.atan2(ry,rx),radius=kidneyRadius(theta);
 const rel=Math.hypot(rx,ry)/radius,wall=(Math.hypot(rx,ry)-radius)*Math.min(widthScale,depthScale);
 const depression=.43*Math.pow(Math.max(0,1-rel*rel),2),frontness=clamp((ry+5.5)/11.25,0,1);
 const height=t.Hposterior+(t.H-t.Hposterior)*frontness;
 let d=Math.max(wall,Math.abs(dz)-(height-depression));
 d-=.08*Math.exp(-Math.pow((Math.abs(dz)-(height-.32))/.38,2)-Math.pow(rel/.97,8));
 for(const side of [-1,1]){
  if(side*x < -.05)continue; // each process belongs to its anatomical side only
  const q=[side*x,y,z];
  d=smoothMin(d,sectionLoft(q,1,[[-6.35,5.24,94,1.45,2.05],[-5.2,5.49,94,1.77,2.43],[-3.5,5.53,94,1.75,2.58],[-1.7,5.55,94,2.12,2.46],[-.25,5.16,94,2.39,2.33]]),.96);
  d=smoothMin(d,sectionLoft(q,0,[[1,-10.25,94,.99,1.72],[2.35,-9.53,94,1.08,1.7],[4.2,-7.8,94,1.2,1.89],[5.8,-6.12,94,1.36,2.12]]),.73);
  d=smoothMin(d,sectionLoft(q,0,[[5.4,-5.83,94,.99,1.3],[7,-6.26,94.01,.91,1.11],[9,-6.86,94.09,.71,.8],[11.2,-7.3,94.22,.51,.53],[13.1,-7.53,94.36,.35,.33]]),.65);
  d=smoothMin(d,sectionLoft(q,2,[[95.2,5.06,-7.27,1.38,1.32],[96.65,5.11,-7.46,1.43,1.4],[98.3,5.06,-7.7,1.24,1.25],[99.7,5,-7.87,.81,.84],[100.5,5,-7.88,.34,.39]]),.68);
  d=smoothMin(d,sectionLoft(q,2,[[88.85,4.33,-8.77,.49,.53],[89.8,4.33,-8.62,1.03,.92],[91.12,4.41,-8.21,1.33,1.11],[93.2,4.78,-7.62,1.1,1.05],[94.5,4.86,-7.5,.81,.87]]),.68);
  d=smoothMin(d,capsule(p,[side*5.1,-7.05,95.45],[side*4.63,-8.18,91.18],1.12),.68);
  d=smoothMin(d,ed(p,[side*5.65,-8.66,98.81],[.56,.6,.76]),.25);
  d=smoothMin(d,ed(p,[side*7.1,-7.5,94.35],[.53,.62,.64]),.22);
  d=Math.max(d,-ed(p,[side*3.77,-7.6,98.2],[.82,1.23,1.3]));
  d=Math.max(d,-ed(p,[side*6.24,-3.32,91.1],[1,1.1,.85]));
 }
 d=smoothMin(d,sectionLoft(p,1,[[-14.35,0,94,.58,1.12],[-13.55,0,94,1,1.48],[-12.48,0,94,1.23,1.54],[-11.28,0,94,1.19,1.62],[-10,0,94,1.22,1.64],[-9.37,0,94,.93,1.48]]),.72);
 // Anatomically directed triangular lumbar foramen, rounded by smoothing.
 const polygon=[[-4.30,-1.38],[4.30,-1.38],[0,-9.12]],lines=[];
 for(let i=0;i<3;i++){
  const a=polygon[i],b=polygon[(i+1)%3],ex=b[0]-a[0],ey=b[1]-a[1];
  lines.push((ex*(y-a[1])-ey*(x-a[0]))/Math.hypot(ex,ey));
 }
 const tri=smoothMaxLoft(smoothMaxLoft(lines[0],lines[1],.66),lines[2],.66);
 return Math.max(d,-Math.max(tri,Math.abs(dz)-6.72));
}
