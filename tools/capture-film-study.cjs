// Browser-only instrumentation: production game and simulation are unmodified.
// Run after python3 tools/build.py; requires Playwright and Chromium for development.
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const {spawn} = require('node:child_process');
const out = path.resolve('docs/film-study');
const sites = {
  torget: {eye:[-30,6,44], target:[8,4,-5]},
  residential: {eye:[42,5,-82], target:[15,4,-126]},
  rural: {eye:[630,4,628], target:[535,3,608]},
  industrial: {eye:[573,7,141], target:[640,5,191]}
};
const hook = `window.__filmStudy = {
  presets:FILM_PRESETS, name:filmPresetName,
  gpu(){const gl=renderer.getContext(),ext=gl.getExtension('WEBGL_debug_renderer_info');return {renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):'unavailable',timerQueries:!!gl.getExtension('EXT_disjoint_timer_query_webgl2')}},
  settings(){return {preset:filmPresetName,grade:filmFrameMaterial.uniforms.uGrade.value,grain:filmFrameMaterial.uniforms.uGrain.value,mist:filmFrameMaterial.uniforms.uMist.value}},
  pose(s) {
    const [x,y,z]=s.eye,[tx,ty,tz]=s.target;
    camera.position.set(x,hAt(x,z)+y,z);
    camera.lookAt(tx,hAt(tx,tz)+ty,tz);
    sun.target.position.set(x,hAt(x,z),z);
    sun.position.copy(sun.target.position).addScaledVector(SUN_DIR,400);
    renderFilmFrame();
  },
  select(name) {
    const p=FILM_PRESETS[name]||FILM_PRESETS.negative,u=filmFrameMaterial.uniforms;
    u.uGrade.value=name==='off'?0:1;
    for(const key of ['curve','shadow','highlight','mid','green','blue','red','yellow','cyan'])
      u['u'+key[0].toUpperCase()+key.slice(1)].value.fromArray(p[key]);
    for(const key of ['shoulder','greenMix','saturation','neutral'])
      u['u'+key[0].toUpperCase()+key.slice(1)].value=p[key];
    renderer.render(filmFrameScene,filmFrameCamera);
  },
  effects(grain,mist){filmFrameMaterial.uniforms.uGrain.value=grain;filmFrameMaterial.uniforms.uMist.value=mist;renderer.render(filmFrameScene,filmFrameCamera)},
  state(){return {camera:camera.position.toArray(), rotation:camera.quaternion.toArray(),
    cars:cars.map(c=>[c.x,c.z,c.h,c.v]), player:[player.x,player.z],
    exposure:renderer.toneMappingExposure, sun:sun.position.toArray(),
    calls:renderer.info.render.calls, triangles:renderer.info.render.triangles}},
  walk(){return [player.x,player.z]},
  car(){return {inCar, x:pcar?.x,z:pcar?.z}},
  nearby(){const c=cars.find(c=>c.mode!=='ai');player.x=c.x+2;player.z=c.z;return [c.x,c.z]},
  render(){renderer.render(filmFrameScene,filmFrameCamera);}
};`;
async function main(){
 fs.mkdirSync(out,{recursive:true});
 const server=spawn('python3',['-m','http.server','8765','--bind','127.0.0.1'],{stdio:'ignore'});
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-features=Vulkan']});
 const only=process.env.CAPTURE_ONLY;
 const results={viewport:[1280,720], lighting:'off (existing static light)', frames:12, sites, errors:[], captures:[], states:{}};
 if(only){const previous=JSON.parse(fs.readFileSync(path.join(out,'results.json'),'utf8'));Object.assign(results,previous,{sites,captures:previous.captures.filter(c=>c.site!==only)})}
 try {
 const page=await browser.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});
 const cdp=await page.context().newCDPSession(page);
 const screenshot=async file=>{const shot=await cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true,captureBeyondViewport:false});const data=Buffer.from(shot.data,'base64');if(file)fs.writeFileSync(path.join(out,file),data);return data};
 page.on('pageerror',e=>results.errors.push(String(e)));
 page.on('console',m=>{if(m.type()==='error')results.errors.push(m.text())});
 await page.route('**/index.html*',async route=>{
   const response=await route.fetch(); let body=await response.text();
   const anchor='resize(); requestAnimationFrame(frame);';
   if(body.split(anchor).length!==2)throw Error('capture hook anchor changed');
   body=body.replace('drawMini(T);\n  renderFilmFrame();', 'drawMini(T); /* render explicitly after deterministic stepping */').replace(anchor,hook+'\n'+anchor).replaceAll('requestAnimationFrame(frame)', 'window.__gameRAF(frame)').replace('let last = performance.now();','let last = 0;');
   await route.fulfill({response,body});
 });
 await page.addInitScript(()=>{
   let pending; let n=0;
   window.__gameRAF=cb=>{pending=cb;return n};
   window.__step=count=>{for(let i=0;i<count;i++){n++;const cb=pending;pending=null;cb(n*1000/60)}};
 });
 await page.goto('http://127.0.0.1:8765/index.html?film=negative&grain=off&mist=off&lighting=off',{waitUntil:'load',timeout:120000});
 console.log('loaded'); await page.locator('#go').evaluate(el=>el.click());
 await page.evaluate(()=>window.__step(12));console.log('stepped');
 results.started=await page.locator('#intro').isHidden();
 results.gpu=await page.evaluate(()=>window.__filmStudy.gpu());
 for(const [site,pose] of Object.entries(sites)){
   if(only&&site!==only)continue;
   await page.evaluate(s=>window.__filmStudy.pose(s),pose);
   const state=await page.evaluate(()=>window.__filmStudy.state());
   results.states[site]=state;
   for(const preset of ['off','chrome','negative','gold','portra']){
     await page.evaluate(p=>window.__filmStudy.select(p),preset);
     const after=await page.evaluate(()=>window.__filmStudy.state());
     if(JSON.stringify(after)!==JSON.stringify(state))throw Error('world/camera changed during preset comparison');
     const file=`${site}-${preset}.png`;
     await screenshot(file);
     results.captures.push({site,preset,file,state:site});
     fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2));console.log(file);
   }
 }
 if(only)return;
 await page.evaluate(s=>window.__filmStudy.pose(s),sites.torget);
 for(const preset of ['chrome','negative','gold','portra']){
   await page.evaluate(p=>{window.__filmStudy.select(p);window.__filmStudy.effects(1.35,.42)},preset);
   await screenshot(`effects-${preset}.png`);
 }
 // Frozen frame must repeat exactly, including screen-space grain.
 await page.evaluate(()=>window.__filmStudy.render());
 console.log('effects complete');const first=await screenshot();
 await page.evaluate(()=>window.__filmStudy.render());
 results.repeatIdentical=first.equals(await screenshot());
 // Real keyboard input through existing gameplay handlers.
 const before=await page.evaluate(()=>window.__filmStudy.walk());
 await page.keyboard.down('w');await page.evaluate(()=>window.__step(30));await page.keyboard.up('w');
 results.walk={before,after:await page.evaluate(()=>window.__filmStudy.walk())};
 await page.evaluate(()=>window.__filmStudy.nearby());
 await page.keyboard.press('e');
 results.enterCar=await page.evaluate(()=>window.__filmStudy.car());
 await page.keyboard.down('w');await page.evaluate(()=>window.__step(60));await page.keyboard.up('w');
 results.drive=await page.evaluate(()=>window.__filmStudy.car());
 await page.keyboard.down('Space');await page.evaluate(()=>window.__step(180));await page.keyboard.up('Space');
 await page.keyboard.press('e');results.exitCar=await page.evaluate(()=>window.__filmStudy.car());
 console.log('keyboard smoke complete');
 // URL parser checks against actual freshly loaded game, including fallback.
 results.selection={};
 for(const p of ['chrome','negative','gold','portra','off','unknown']){
   await page.goto(`http://127.0.0.1:8765/index.html?film=${p}&grain=off&mist=off&lighting=off`,{waitUntil:'load',timeout:120000});
   results.selection[p]=await page.evaluate(()=>window.__filmStudy.settings());console.log('selection',p,results.selection[p]);
 }
 if(results.errors.some(e=>/WebGLProgram|VALIDATE_STATUS|ERROR: 0:|ReferenceError|TypeError/.test(e)))throw Error(results.errors.join('\n'));
 if(!results.started || !results.enterCar.inCar || results.exitCar.inCar)throw Error('smoke check failed');
 } finally {fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2));await browser.close();server.kill()}
}
module.exports={hook,sites};
if(require.main===module)main().catch(e=>{console.error(e);process.exitCode=1});
