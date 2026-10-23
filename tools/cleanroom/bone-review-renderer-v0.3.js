// Original Canvas2D software rasterizer. Geometry is unchanged from v0.2.
// Interpolate vertex lighting and depth; no per-triangle edge strokes.
const DISPLAY={mode:'high',maxPixels:2400000};
function prepareSmooth(o){
 const ns=o.verts.map(()=>[0,0,0]),ao=new Float64Array(ns.length),weights=new Float64Array(ns.length);
 o.faces.forEach((f,i)=>{const a=o.verts[f[0]],b=o.verts[f[1]],c=o.verts[f[2]],n=V.cross(V.sub(b,a),V.sub(c,a)),area=Math.hypot(...n);for(const j of f){for(let k=0;k<3;k++)ns[j][k]+=n[k];ao[j]+=o.shades[i].ao*area;weights[j]+=area}});
 o.smooth=ns.map((n,i)=>({n:V.unit(n),ao:weights[i]?ao[i]/weights[i]:1}));
}
function rasterSize(w,h){
 const native=Math.min(3,Math.max(1,devicePixelRatio||1));
 const requested=DISPLAY.mode==='high'?Math.max(2,native):1;
 const ratio=Math.min(requested,Math.sqrt(DISPLAY.maxPixels/(w*h)));
 return [Math.max(1,Math.floor(w*ratio)),Math.max(1,Math.floor(h*ratio))];
}
function drawScene(canvas,yaw,pitch,zoom){
 const ctx=canvas.getContext('2d');if(!ctx)return;
 const rect=canvas.getBoundingClientRect(),[w,h]=rasterSize(Math.max(1,rect.width),Math.max(1,rect.height));
 canvas.width=w;canvas.height=h;
 const image=ctx.createImageData(w,h),pixels=image.data,depth=new Float32Array(w*h);depth.fill(-Infinity);
 const box=frame[viewState.target],center=canvas===$('interactive')&&viewState.center?viewState.center:box.c;
 const scale=Math.min(w,h)*.9/box.diameter*zoom,model=pool[viewState.target+':'+viewState.revision]||[];
 for(const o of model){
  if(!visible(o))continue;if(!o.smooth)prepareSmooth(o);
  const vv=o.verts.map(p=>{const q=rotate(V.sub(p,center),yaw,pitch);return [w/2+q[0]*scale,h/2-q[1]*scale,q[2]]});
  const light=o.smooth.map(s=>{const n=rotate(s.n,yaw,pitch);return (.42+.55*Math.max(0,n[0]*-.32+n[1]*.55+n[2]*.77))*s.ao});
  const base=o.name.includes('歯冠')?[233,229,213]:[214,204,178];
  for(let fi=0;fi<o.faces.length;fi++){
   if(rotate(o.shades[fi].n,yaw,pitch)[2]<-.08)continue;
   const ids=o.faces[fi],a=vv[ids[0]],b=vv[ids[1]],c=vv[ids[2]],den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);
   if(Math.abs(den)<1e-10)continue;
   const x0=Math.max(0,Math.ceil(Math.min(a[0],b[0],c[0])-.5)),x1=Math.min(w-1,Math.floor(Math.max(a[0],b[0],c[0])-.5));
   const y0=Math.max(0,Math.ceil(Math.min(a[1],b[1],c[1])-.5)),y1=Math.min(h-1,Math.floor(Math.max(a[1],b[1],c[1])-.5));
   const dax=(b[1]-c[1])/den,day=(c[0]-b[0])/den,dbx=(c[1]-a[1])/den,dby=(a[0]-c[0])/den;
   const sa=light[ids[0]],sb=light[ids[1]],sc=light[ids[2]];
   for(let y=y0;y<=y1;y++){
    let wa=dax*(x0+.5-c[0])+day*(y+.5-c[1]),wb=dbx*(x0+.5-c[0])+dby*(y+.5-c[1]);
    for(let x=x0;x<=x1;x++,wa+=dax,wb+=dbx){
     const wc=1-wa-wb;if(wa< -1e-7||wb< -1e-7||wc< -1e-7)continue;
     const z=wa*a[2]+wb*b[2]+wc*c[2],index=y*w+x;if(z<=depth[index])continue;depth[index]=z;
     const shade=wa*sa+wb*sb+wc*sc,k=index*4;
     pixels[k]=base[0]*shade;pixels[k+1]=base[1]*shade;pixels[k+2]=base[2]*shade;pixels[k+3]=255;
    }
   }
  }
 }
 ctx.putImageData(image,0,0);
}
function setDisplay(mode){DISPLAY.mode=mode;document.querySelectorAll('[data-quality]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.quality===mode)));drawAll()}
document.querySelectorAll('[data-quality]').forEach(b=>b.addEventListener('click',()=>setDisplay(b.dataset.quality)));
