// Experimental L3 v2.2 posterior bony structure, hand-authored section landmarks.
// Move pedicles, laminae, superior/inferior processes, spinous process and canal
// coherently to test published L3 mean spinal canal width/depth/area. Not CT-derived.
// Updated transverse process tip was calibrated for stable width at both resolutions.
// This is a candidate, NOT a validated patient or specimen model.
function L3LandmarkLoftV22(p){
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
  d=smoothMin(d,sectionLoft(q,1,[[-3.996,5.24,94,1.45,2.05],[-3.274,5.49,94,1.77,2.43],[-2.216,5.53,94,1.75,2.58],[-1.058,5.55,94,2.12,2.46],[-0.25,5.16,94,2.39,2.33]]),.96);
  d=smoothMin(d,sectionLoft(q,0,[[1,-5.97,94,0.99,1.72],[2.35,-5.25,94,1.08,1.7],[4.2,-3.52,94,1.2,1.89],[5.8,-1.84,94,1.36,2.12]]),.73);
  d=smoothMin(d,sectionLoft(q,0,[[5.4,-4.76,94,0.99,1.3],[7,-5.19,94.01,0.91,1.11],[9.6,-5.79,94.09,0.71,0.8],[12.4,-6.23,94.22,0.6,0.59],[15.2,-6.46,94.36,0.48,0.43]]),.65);
  d=smoothMin(d,sectionLoft(q,2,[[95.2,5.06,-4.488,1.38,1.32],[96.65,5.11,-4.678,1.43,1.4],[98.3,5.06,-4.918,1.24,1.25],[99.7,5,-5.088,0.81,0.84],[100.5,5,-5.098,0.34,0.39]]),.68);
  d=smoothMin(d,sectionLoft(q,2,[[88.85,4.33,-5.988,0.49,0.53],[89.8,4.33,-5.838,1.03,0.92],[91.12,4.41,-5.428,1.33,1.11],[93.2,4.78,-4.838,1.1,1.05],[94.5,4.86,-4.718,0.81,0.87]]),.68);
  d=smoothMin(d,capsule(p,[side*5.1,-4.268,95.45],[side*4.63,-5.398,91.18],1.12),.68);
  d=smoothMin(d,ed(p,[side*5.65,-5.878,98.81],[.56,.6,.76]),.25);
  d=smoothMin(d,ed(p,[side*7.1,-6.43,94.35],[.53,.62,.64]),.22);
  d=Math.max(d,-ed(p,[side*3.77,-4.818,98.2],[.82,1.23,1.3]));
  d=Math.max(d,-ed(p,[side*6.24,-3.32,91.1],[1,1.1,.85]));
 }
 d=smoothMin(d,sectionLoft(p,1,[[-14.35,0,94,0.58,1.12],[-13.122,0,94,1,1.48],[-11.196,0,94,1.23,1.54],[-8.926,0,94,1.19,1.62],[-6.576,0,94,1.22,1.64],[-5.09,0,94,0.93,1.48]]),.72);
 // Anatomically directed triangular lumbar foramen, rounded by smoothing.
 const polygon=[[-4.30,-1.38],[4.30,-1.38],[0,-4.84]],lines=[];
 for(let i=0;i<3;i++){
  const a=polygon[i],b=polygon[(i+1)%3],ex=b[0]-a[0],ey=b[1]-a[1];
  lines.push((ex*(y-a[1])-ey*(x-a[0]))/Math.hypot(ex,ey));
 }
 const tri=smoothMaxLoft(smoothMaxLoft(lines[0],lines[1],.66),lines[2],.66);
 return Math.max(d,-Math.max(tri,Math.abs(dz)-6.72));
}


