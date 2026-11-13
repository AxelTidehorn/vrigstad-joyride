// Browser-only review tooling. Production hooks remain read-only.
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),{spawn}=require('node:child_process');
const root=process.env.REVIEW_ROOT||process.cwd(),kind=process.env.REVIEW_KIND||'saab';
async function main(){
 const port=Number(process.env.REVIEW_PORT)||({grain:8790,daylight:8791,volvo:8792,saab:8793,grades:8794}[kind]);
 const out=path.join(root,'docs/review-'+kind);fs.mkdirSync(out,{recursive:true});
 const server=spawn('python3',['-m','http.server',String(port),'--bind','127.0.0.1'],{cwd:root,stdio:'ignore'});
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const resultFile=kind==='grades'&&process.env.REVIEW_TIME?'results-'+process.env.REVIEW_TIME+'.json':'results.json';
 const result={root,kind,errors:[],captures:[],viewport:[960,540],notes:'Actual Chromium / SwiftShader. Browser-only fixed-step simulation and camera instrumentation, no screenshot pixel-diff assertions.'};
 try{
 const page=await browser.newPage({viewport:{width:960,height:540}});const cdp=await page.context().newCDPSession(page);
 page.on('pageerror',e=>result.errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')result.errors.push(m.text())});
 await page.route('**/favicon.ico',r=>r.fulfill({status:204,body:''}));
 await page.route('**/index.html*',async route=>{
  const response=await route.fetch();let body=await response.text();
  const draw=kind==='grain'?'sceneFinish.render();':kind==='grades'?'if(window.__reviewOff)renderer.render(scene,camera);else sceneFinish.render();':'renderer.render(scene, camera);';
  // Freeze only the game's RAF, preserving native RAF for browser tasks/query polling.
  body=body.replaceAll('requestAnimationFrame(frame)','window.__queue(frame)').replace('let last = performance.now();','let last = 0;').replace('  '+draw,'  /* render explicitly during review */');
  const api=`window.__review={
   render(){dome.position.copy(camera.position);${draw}},
   pose(){camera.position.set(24,hAt(24,-15)+6,-15);camera.lookAt(-30,hAt(-30,50)+4,50);sun.target.position.set(0,hAt(0,0),0);${kind==='daylight'?'daylight.update(0);streetLighting.update(0,daylight.getHour(),daylight.getSolarElevation());':''}dome.position.copy(camera.position)},
   state(){return {camera:camera.position.toArray(),quaternion:camera.quaternion.toArray(),reviewPreset:window.__reviewPreset,renderPath:window.__reviewOff?'direct':'finish',groundMaterial:scene.children.find(o=>o.isMesh&&o.material&&o.material.map===texture)?.material.type,world:cars.map(c=>[c.type,c.x,c.z]),player:[player.x,player.z],sun:sun.intensity,exposure:renderer.toneMappingExposure,...window.__joyride.state()}},
   ${kind==='grain'||kind==='grades'?'finish:()=>sceneFinish.state(),':''}
   ${kind==='volvo'||kind==='saab'?`model(view){const t=this.type||'${kind}',paint=TYPES[t].cols[0];if(!this.solo){this.solo=new THREE.Scene();this.solo.background=new THREE.Color(0xc5ced5);this.solo.add(new THREE.HemisphereLight(0xffffff,0x606060,1));const l=new THREE.DirectionalLight(0xffffff,1);l.position.set(-4,6,-3);this.solo.add(l);this.mesh=new THREE.Mesh(carGeo(t,paint),carMat);this.solo.add(this.mesh)}this.mesh.geometry=carGeo(t,paint);if(!this.mesh.geometry.boundingBox)this.mesh.geometry.computeBoundingBox();this.view=view;const p={front:[0,1,-7],side:[7,1,0],rear:[0,1,7],threequarter:[5,3,-6]}[view];camera.position.fromArray(p);camera.lookAt(0,.8,0);renderer.render(this.solo,camera);return {triangles:this.mesh.geometry.attributes.position.count/3,bounds:this.mesh.geometry.boundingBox,finite:Array.from(this.mesh.geometry.attributes.normal.array).every(Number.isFinite),frontSide:this.mesh.material.side===THREE.FrontSide}},`:''}
   async measure(){const gl=renderer.getContext(),ext=gl.getExtension('EXT_disjoint_timer_query_webgl2');
    const samples=[];for(let i=0;i<4;i++){
     let q;if(ext){q=gl.createQuery();gl.beginQuery(ext.TIME_ELAPSED_EXT,q)}
     const start=performance.now();renderer.info.autoReset=false;renderer.info.reset();${draw}const calls=renderer.info.render.calls,triangles=renderer.info.render.triangles;renderer.info.autoReset=true;
     if(ext)gl.endQuery(ext.TIME_ELAPSED_EXT);
     const submissionMs=performance.now()-start;
     if(ext){const startWait=performance.now();while(!gl.getQueryParameter(q,gl.QUERY_RESULT_AVAILABLE)){if(performance.now()-startWait>120000)throw Error('timer query timeout');await new Promise(r=>setTimeout(r,20))}const disjoint=gl.getParameter(ext.GPU_DISJOINT_EXT),ns=gl.getQueryParameter(q,gl.QUERY_RESULT);gl.deleteQuery(q);samples.push({gpuMs:disjoint?null:ns/1e6,submissionMs,calls,triangles,disjoint})}else samples.push({gpuMs:null,submissionMs,calls,triangles});
    }return {samples,renderer:gl.getParameter(gl.RENDERER),timerQueries:!!ext};
   }
  };`;
  body=body.replace('resize(); window.__queue(frame);',api+'resize();window.__queue(frame);');
  if(kind==='grades')body=body.replace('const uniforms={};',`const uniforms={};window.__setReviewGrade=name=>{window.__reviewPreset=name;window.__reviewOff=name==='off';const p=FILM_PRESETS[name]||FILM_PRESETS.negative;for(const key of ['curve','shadow','highlight','mid','green','blue','red','yellow','cyan'])uniforms['u'+key[0].toUpperCase()+key.slice(1)].value.fromArray(p[key]);for(const key of ['shoulder','greenMix','saturation','neutral'])uniforms['u'+key[0].toUpperCase()+key.slice(1)].value=p[key]};`).replace('resize();window.__queue(frame);', `window.__setConditions=time=>{const h=scene.children.find(o=>o.isHemisphereLight);SUN_DIR.set(-.55,.75,.37).normalize();sun.color.copy(col(0xfff4dd));sun.intensity=.95;h.intensity=.62;dome.material.uniforms.top.value.set(0x5f97c9);dome.material.uniforms.hor.value.set(0xd6e4e6);dome.material.uniforms.sunC.value.set(0xfff1d0);if(time==='sunset'){SUN_DIR.set(-.85,.18,.49).normalize();sun.color.copy(col(0xff9b48));sun.intensity=.50;h.intensity=.30;dome.material.uniforms.top.value.set(0xa37583);dome.material.uniforms.hor.value.set(0xd69f7c)}if(time==='night'){dome.material.uniforms.sunC.value.set(0x000000);sun.intensity=0;h.intensity=.10;dome.material.uniforms.top.value.set(0x101e32);dome.material.uniforms.hor.value.set(0x1d3046)}sun.position.copy(sun.target.position).addScaledVector(SUN_DIR,400);scene.fog.color.copy(dome.material.uniforms.hor.value)};resize();window.__queue(frame);`);
  if(kind==='grain'&&route.request().url().includes('reviewIdentity'))body=body.replace('const uniforms={uStrength:{value:strength}};','const uniforms={uStrength:{value:0}};');
  await route.fulfill({response,body});
 });
 await page.addInitScript(()=>{let cb,n=0;window.__queue=f=>cb=f;window.__step=count=>{for(let i=0;i<count;i++){n++;cb(n*1000/60)}}});
 async function load(query){await page.goto(`http://127.0.0.1:${port}/index.html`+query,{waitUntil:'load',timeout:300000});await page.locator('#go').evaluate(el=>el.click());await page.evaluate(()=>window.__step(12));await page.evaluate(()=>window.__review.pose())}
 async function shot(name,model){const info=model?await page.evaluate(v=>window.__review.model(v),model):await page.evaluate(()=>window.__review.render());const png=await cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true});fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(png.data,'base64'));const state=await page.evaluate(()=>window.__review.state());result.captures.push({name,info,state});fs.writeFileSync(path.join(out,resultFile),JSON.stringify(result,null,2));console.log(kind,name)}
 if(kind==='grain'){
  for(const [label,query]of[['direct','?grain=off'],['identity','?grain=subtle&reviewIdentity=1'],['subtle','?grain=subtle'],['strong','?grain=strong']]){
   await load(query);await shot(label);result[label]=await page.evaluate(()=>window.__review.measure());
  }
 }else if(kind==='volvo'||kind==='saab'){
  await load('');if(process.env.REVIEW_BASELINE){for(const type of ['volvo','saab']){await page.evaluate(t=>window.__review.type=t,type);for(const view of ['front','side','rear','threequarter'])await shot('baseline-'+type+'-'+view,view)}}else for(const view of ['front','side','rear','threequarter'])await shot(view,view);
  await page.evaluate(()=>window.__review.pose());await shot('game');
 }else if(kind==='daylight'){
  await load('?dev=lighting&time=13&date=2026-08-15');
  async function control(id,value,event='input'){await page.locator('#lab-'+id).evaluate((e,{value,event})=>{e.value=value;e.dispatchEvent(new Event(event,{bubbles:true}))},{value,event})}
  for(const hour of [13,17,19,20.5,22]){await control('time',hour);await page.locator('#visual-lab').evaluate(e=>e.open=false);await page.evaluate(()=>window.__review.pose());await shot('time-'+hour)}
  for(const date of ['2026-06-21','2026-12-21']){await control('date',date,'change');await control('time',13);await page.evaluate(()=>window.__review.pose());await shot(date)}
  await control('time',22);for(const mode of ['off','on']){await control('street',mode,'change');await page.evaluate(()=>window.__review.pose());await shot('street-'+mode)}
  await page.locator('#visual-lab').evaluate(e=>e.open=true);await page.locator('#lab-time').focus();const before=await page.evaluate(()=>window.__joyride.state());await page.keyboard.down('w');await page.evaluate(()=>window.__step(10));await page.keyboard.up('w');const after=await page.evaluate(()=>window.__joyride.state());result.panelBlocksDriving=before.x===after.x&&before.z===after.z;
 }else if(kind==='grades'){
  // One actual upstream world/target; browser-only uniform selection. Off renders
  // directly through the native upstream renderer. URL bypass is tested by E2E.
  await load('?film=negative');
  for(const time of ['day','sunset','night'].filter(t=>!process.env.REVIEW_TIME||process.env.REVIEW_TIME===t)){
   await page.evaluate(time=>window.__setConditions(time),time);
   for(const preset of ['off','chrome','negative','gold','portra']){
    await page.evaluate(p=>window.__setReviewGrade(p),preset);
    await shot(time+'-'+preset);
   }
  }
 }

 if(result.errors.length)throw Error(result.errors.join('\n'));
 }finally{fs.writeFileSync(path.join(out,resultFile),JSON.stringify(result,null,2));await browser.close();server.kill()}
}
main().catch(e=>{console.error(e);process.exitCode=1});
