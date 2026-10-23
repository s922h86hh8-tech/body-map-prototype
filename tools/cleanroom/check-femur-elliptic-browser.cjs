'use strict';
// Local Chromium automation. This does not establish iPhone or Safari behavior.
const {chromium}=require('playwright'),fs=require('node:fs'),path=require('node:path');
const assert=require('node:assert/strict');
(async()=>{
 const root=path.resolve(__dirname,'../..'),out=process.env.BODYMAP_BROWSER_OUT||'/tmp/femur-v04-browser';
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 try{
 const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true,deviceScaleFactor:1});
 const page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(String(e)));
 await page.goto('file://'+path.join(root,'experiments/cleanroom-femur-study-v0.4.html'));
 await page.waitForFunction(()=>document.body.dataset.ready==='true'||document.querySelector('#error').style.display==='flex');
 const ready=await page.evaluate(()=>document.body.dataset.ready==='true');
 if(!ready)throw Error('WebGL did not start: '+await page.locator('#error').innerText());
 const state=()=>page.evaluate(()=>({mode,framing,zoom,yaw,pitch,selected}));
 for(const view of ['front','back','lateral','oblique','medial','posteromedial']){
  await page.locator('[data-view="'+view+'"]').tap();assert.equal((await state()).mode,view);
 }
 await page.locator('[data-feature="2"]').tap();
 assert.equal((await state()).framing,'surface');assert.equal((await state()).selected,2);
 await page.locator('#scene').scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(out,'neck-portrait.png'),fullPage:true});
 const box=await page.locator('#scene').boundingBox(),x=box.x+box.width/2,y=box.y+box.height/2;
 const session=await context.newCDPSession(page);
 const touch=async(type,points)=>session.send('Input.dispatchTouchEvent',{type,touchPoints:points});
 const before=await state();
 await touch('touchStart',[{x:x-30,y,id:1}]);await touch('touchMove',[{x:x+30,y:y+12,id:1}]);await touch('touchEnd',[]);
 assert.notEqual((await state()).yaw,before.yaw);
 const beforePinch=await state();
 await touch('touchStart',[{x:x-30,y,id:1},{x:x+30,y,id:2}]);
 await touch('touchMove',[{x:x-50,y,id:1},{x:x+50,y,id:2}]);await touch('touchEnd',[]);
 assert.ok((await state()).zoom>beforePinch.zoom);
 await page.locator('[data-feature="5"]').tap();
 assert.equal((await state()).mode,'posteromedial');assert.equal((await state()).framing,'surface');
 await page.locator('#scene').scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(out,'fossa-portrait.png'),fullPage:true});
 await page.locator('#reset').tap();assert.equal((await state()).mode,'back');assert.equal((await state()).framing,'whole');
 const downloadPromise=page.waitForEvent('download');await page.locator('#download').tap();const download=await downloadPromise;
 const exported=path.join(out,'export.gltf');await download.saveAs(exported);const gltf=JSON.parse(fs.readFileSync(exported,'utf8'));
 assert.equal(gltf.asset.extras.physicalScaleValidated,false);assert.equal(gltf.asset.extras.modelId,'body-map-original-femur-study-v0.3');
 const sizes=[];
 for(const [width,height] of [[320,780],[390,844],[844,390],[1280,900]]){
  await page.setViewportSize({width,height});await page.waitForTimeout(100);
  const size=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
  assert.ok(size.scrollWidth<=size.width+1);sizes.push({...size,height});
 }
 await page.setViewportSize({width:844,height:390});await page.locator('#scene').scrollIntoViewIfNeeded();
 await page.screenshot({path:path.join(out,'landscape.png'),fullPage:true});
 assert.equal(errors.length,0);
 const stats=await page.evaluate(()=>window.__study.stats);
 console.log(JSON.stringify({status:'passed',browser:browser.version(),scope:'Local automated Chromium with SwiftShader; not iPhone/Safari',
 webglStarted:true,geometry:stats,checks:['six directions','neck close view','fossa close view','reset','synthetic touch rotation','synthetic two-touch zoom','actual glTF download','viewport overflow','no page exceptions'],sizes,exportFilename:download.suggestedFilename(),anatomicalApproval:false,iPhone:'not tested'},null,2));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});

