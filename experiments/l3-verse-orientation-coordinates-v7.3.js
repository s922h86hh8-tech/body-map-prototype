/* Pure RAS pixel/marker geometry. Local-only research; NO anatomical approval. */
(function (root) {
  'use strict';
  const basis = Object.freeze({
    axial: Object.freeze({right:[1,0,0],up:[0,1,0]}),
    coronal: Object.freeze({right:[1,0,0],up:[0,0,1]}),
    sagittal: Object.freeze({right:[0,1,0],up:[0,0,1]})
  });
  function pointFromPixel(plane,x,y,pixels,pitch,center) {
    const a=basis[plane];
    if (!a || !Number.isInteger(pixels) || pixels<25 || pixels%2!==1 ||
        !Number.isFinite(pitch) || pitch<=0 || !Array.isArray(center) ||
        center.length!==3 || center.some(v=>!Number.isFinite(v)) ||
        !Number.isFinite(x) || !Number.isFinite(y) ||
        x<0 || y<0 || x>=pixels || y>=pixels) {
      throw new Error('Invalid RAS slice pixel geometry');
    }
    const dx=(x-(pixels-1)/2)*pitch;
    const dy=((pixels-1)/2-y)*pitch;
    return center.map((v,i)=>Number((v+dx*a.right[i]+dy*a.up[i]).toFixed(6)));
  }
  function pixelFromClick(plane,click,rect,pixels) {
    if (!basis[plane] || !Number.isInteger(pixels) || pixels<25 ||
        !rect || [rect.left,rect.top,rect.width,rect.height,click.x,click.y].some(v=>!Number.isFinite(v)) ||
        rect.width<=0 || rect.height<=0) throw new Error('Invalid click geometry');
    const x=(click.x-rect.left)/rect.width;
    const y=(click.y-rect.top)/rect.height;
    if (x<0 || x>=1 || y<0 || y>=1) throw new Error('Click outside CT image');
    return {x:Math.min(pixels-1,Math.floor(x*pixels)), y:Math.min(pixels-1,Math.floor(y*pixels))};
  }
  function provisionalAPCheck(items) {
    const anterior=items.find(i=>i.kind==='body_anterior');
    const posterior=items.find(i=>i.kind==='spinous_posterior');
    if (!anterior || !posterior) return {status:'incomplete',ap_ras_mm:null,anatomy_approved:false};
    if (anterior.source_ct_sha256!==posterior.source_ct_sha256 ||
        anterior.source_seg_sha256!==posterior.source_seg_sha256 ||
        !Array.isArray(anterior.world_ras_mm) || !Array.isArray(posterior.world_ras_mm) ||
        anterior.world_ras_mm.length!==3 || posterior.world_ras_mm.length!==3 ||
        [...anterior.world_ras_mm,...posterior.world_ras_mm].some(v=>!Number.isFinite(v))) {
      return {status:'invalid_source',ap_ras_mm:null,anatomy_approved:false};
    }
    const d=Number((anterior.world_ras_mm[1]-posterior.world_ras_mm[1]).toFixed(3));
    return {
      status:d>0.5?'numeric_expected_order':d<-.5?'numeric_reverse_warning':'numerically_ambiguous',
      ap_ras_mm:d,anatomy_approved:false
    };
  }
  root.L3V73_COORDS=Object.freeze({basis,pointFromPixel,pixelFromClick,provisionalAPCheck});
})(typeof globalThis!=='undefined'?globalThis:this);
