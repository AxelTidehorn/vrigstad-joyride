const {chromium}=require('playwright'),fs=require('node:fs'),{spawn}=require('node:child_process');
async function main(){
 const out='docs/lighting-lab';fs.mkdirSync(out,{recursive:true});
 const server=spawn('python3',['-m','http.server','8768','--bind','127.0.0.1'],{stdio:'ignore'});
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const result={errors:[],captures:[],note:'960x540 SwiftShader; fixed camera and paused simulation. Real DOM control events; render explicitly after changes. Timings include software rendering and browser screenshot overhead, not hardware GPU FPS.'};
 try{
 const page=await browser.newPage({viewport:{width:960,height:540}});const cdp=await page.context().newCDPSession(page);
 page.on('pageerror',e=>result.errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')result.errors.push(m.text())});
 await page.route('**/favicon.ico',r=>r.fulfill({status:204,body:''}));
 await page.route('**/index.html*',async route=>{
 const response=await route.fetch();let body=await response.text();
 body=body.replace('drawMini(T);\n  renderFilmFrame();','drawMini(T);').replaceAll('requestAnimationFrame(frame)','window.__queue(frame)').replace('let last = performance.now();','let last = 0;');
 body=body.replace('resize(); window.__queue(frame);',`window.__review={
 render(){camera.position.set(24,hAt(24,-15)+6,-15);camera.lookAt(-30,hAt(-30,50)+4,50);sun.target.position.set(0,hAt(0,0),0);daylight.update(0);streetLighting.update(0,daylight.getHour());renderFilmFrame()},
 state(){return {sun:sun.intensity,exposure:renderer.toneMappingExposure,hour:daylight.getHour(),street:streetLighting.stats(),camera:camera.position.toArray(),player:[player.x,player.z],cars:cars.map(c=>[c.x,c.z]),calls:renderer.info.render.calls,programs:renderer.info.programs.length}},
 move(){return [player.x,player.z]},
 };resize();window.__queue(frame);`);
 await route.fulfill({response,body});});
 await page.addInitScript(()=>{let cb,n=0;window.__queue=f=>cb=f;window.__step=count=>{for(let i=0;i<count;i++){n++;cb(n*1000/60)}}});
 await page.goto('http://127.0.0.1:8768/index.html?dev=lighting&time=13&grain=off',{waitUntil:'load',timeout:120000});
 await page.locator('#go').evaluate(el=>el.click());await page.evaluate(()=>window.__step(12));
 async function set(id,value,event='input'){await page.locator('#lab-'+id).evaluate((el,{value,event})=>{el.value=value;el.dispatchEvent(new Event(event,{bubbles:true}))},{value,event})}
 async function shot(name){const start=Date.now();await page.evaluate(()=>window.__review.render());const image=await cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true});fs.writeFileSync(`${out}/${name}.png`,Buffer.from(image.data,'base64'));result.captures.push({name,wallMs:Date.now()-start,...await page.evaluate(()=>window.__review.state())});fs.writeFileSync(`${out}/results.json`,JSON.stringify(result,null,2));console.log(name)}
 for(const time of [13,17,19,20.5,22]){await set('time',time);await set('film','negative','change');await shot('time-'+time);if(time===13){await page.locator('#visual-lab').evaluate(el=>el.open=false)}}
 for(const time of [13,20.5]){
 await set('time',time);
 for(const film of ['off','chrome','negative','gold']){await set('film',film,'change');await shot(`${time}-${film}`)}
 }
 await set('time',22);await set('street','off','change');await shot('night-street-off');await set('street','on','change');await shot('night-street-on');
 await set('time',19);await set('cloud',0);await set('glare',3);await shot('sun-clear');await set('cloud',1);await shot('sun-cloudy');
 // Profile switch keeps camera, world and light unchanged (no stepping/render).
 const before=await page.evaluate(()=>window.__review.state());await set('film','chrome','change');const after=await page.evaluate(()=>window.__review.state());
 result.profilePreservesState=JSON.stringify(before)===JSON.stringify(after);
 await page.locator('#visual-lab').evaluate(el=>el.open=true);await page.locator('#lab-time').focus();const p=await page.evaluate(()=>window.__review.move());await page.keyboard.down('w');await page.evaluate(()=>window.__step(10));await page.keyboard.up('w');result.panelBlocksDriving=JSON.stringify(p)===JSON.stringify(await page.evaluate(()=>window.__review.move()));
 await page.locator('#gl').focus();await page.keyboard.down('w');await page.evaluate(()=>window.__step(30));await page.keyboard.up('w');result.keyboardMovesPlayer=JSON.stringify(p)!==JSON.stringify(await page.evaluate(()=>window.__review.move()));
 await page.locator('#lab-reset').evaluate(el=>el.click());result.reset=await page.evaluate(()=>({time:document.querySelector('#lab-time').value,film:document.querySelector('#lab-film').value,street:document.querySelector('#lab-street').value}));
 if(result.errors.length||!result.profilePreservesState||!result.panelBlocksDriving||!result.keyboardMovesPlayer)throw Error('Browser assertions failed');
 }finally{fs.writeFileSync(`${out}/results.json`,JSON.stringify(result,null,2));await browser.close();server.kill()}
}
main().catch(e=>{console.error(e);process.exitCode=1});
