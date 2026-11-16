import {test,expect} from '@playwright/test';
import {watchErrors} from './render-helpers.js';
const ids=['volvo240','saab900','xc70','xc70-police','impala1970','micra-k11','duett-epa'];
for(const id of ids)test(`${id} loads, renders, can be entered and drives`,async({page},info)=>{
 const errors=watchErrors(page);await page.setViewportSize({width:640,height:360});
 await page.goto('/index.html?vehicle='+id);await page.locator('#go').click();
 const state=()=>page.evaluate(()=>window.__joyride.state());
 await expect.poll(async()=>(await state()).vehicle?.status).toBe('loaded');
 await expect.poll(async()=>(await state()).vehicle.detailed).toBe(true);
 expect((await state()).vehicle.wheels).toHaveLength(4);
 await page.keyboard.down('KeyD');await expect.poll(async()=>(await state()).near,{intervals:[50]}).not.toBeNull();await page.keyboard.up('KeyD');
 await page.keyboard.press('KeyE');await expect.poll(async()=>(await state()).inCar).toBe(true);
 const before=await state();await page.keyboard.down('KeyW');await page.keyboard.down('KeyD');
 await expect.poll(async()=>{const s=await state();return Math.hypot(s.x-before.x,s.z-before.z);}).toBeGreaterThan(2);
 await page.keyboard.up('KeyW');await page.keyboard.up('KeyD');
 const after=await state();expect(after.vehicle.wheels.some(w=>Math.abs(w.spin)>0.1)).toBe(true);
 expect(after.vehicle.wheels.slice(0,2).some(w=>Math.abs(w.steer)>0.001)).toBe(true);
 expect(after.vehicle.wheels.slice(2).every(w=>w.steer===0)).toBe(true);
 expect(await page.evaluate(()=>document.querySelector('#gl').getContext('webgl2').getError())).toBe(0);
 await page.screenshot({path:info.outputPath(id+'.png')});expect(errors).toEqual([]);
});
test('a failed GLB remains an explicitly failed procedural fallback',async({page})=>{
 await page.route('**/media/vehicles/micra-k11.glb',route=>route.abort());
 await page.goto('/index.html?vehicle=micra-k11');
 await expect.poll(()=>page.evaluate(()=>window.__joyride?.state().vehicle?.status)).toBe('failed');
 expect(await page.evaluate(()=>window.__joyride.state().vehicle)).toMatchObject({fallback:true,detailed:false,wheels:[]});
});
test('shared templates, independent paint and disposal use actual GLB instances',async({page})=>{
 const {buildFixture}=await import('./render-helpers.js');await buildFixture('vehicles');
 let requests=0;page.on('request',r=>{if(r.url().endsWith('/volvo240.glb'))requests++;});
 await page.goto('/.work/vehicles/index.html');
 await expect.poll(()=>page.evaluate(()=>window.harness?.cars.filter(c=>window.harness.assets.state(c)?.status==='loaded').length)).toBe(2);
 const result=await page.evaluate(()=>{
  const {assets,cars,THREE}=window.harness;
  const [a,b]=cars.map(c=>c.mesh.getObjectByName('body'));
  const shared=a.geometry===b.geometry;
  const glass=cars[0].mesh.getObjectByName('glass_envelope'), glassMaterial=glass.material;
  const original=b.material.color.clone();
  cars[0].x+=0.1;cars[0].z-=1;cars[0].h+=0.1;assets.sync(cars[0]);
  const front=cars[0].mesh.getObjectByName('wheel_fl').parent.parent;
  const wheelDirection=new THREE.Vector3(0,0,-1).applyQuaternion(front.quaternion);
  const correctSteering=wheelDirection.x>0;
  cars[0].x-=0.1;cars[0].z+=1;cars[0].h-=0.1;assets.sync(cars[0]);
  const reverseSteering=new THREE.Vector3(0,0,-1).applyQuaternion(front.quaternion).x>0;assets.paint(cars[0],'#27406b');
  const independent=a.material!==b.material&&b.material.color.equals(original);
  const protectedGlass=glass.material===glassMaterial;
  const linear=a.material.color.equals(new THREE.Color('#27406b').convertSRGBToLinear());
  let disposed=false;a.material.addEventListener('dispose',()=>disposed=true);assets.dispose(cars[0]);
  return {shared,independent,linear,disposed,protectedGlass,correctSteering,reverseSteering,removed:assets.state(cars[0])===null};
 });
 expect(result).toEqual({shared:true,independent:true,linear:true,disposed:true,protectedGlass:true,correctSteering:true,reverseSteering:true,removed:true});expect(requests).toBe(1);
});
test('production and development asset paths serve real GLBs',async({page})=>{
 for(const name of ['volvo240','saab900-t16','xc70-civilian','xc70-police','impala1970','micra-k11','duett-p210-epa']){
  const r=await page.request.get('/dist/media/vehicles/'+name+'.glb');expect(r.ok()).toBe(true);expect((await r.body()).subarray(0,4).toString()).toBe('glTF');
 }
 const {createServer}=await import('vite');const server=await createServer({server:{port:0,host:'127.0.0.1'}});await server.listen();
 try{await page.goto(server.resolvedUrls.local[0]+'?vehicle=micra-k11');await expect.poll(()=>page.evaluate(()=>window.__joyride?.state().vehicle?.status)).toBe('loaded');}finally{await server.close();}
});
test('the GLB police variant follows the existing pursuit AI and flashes beacons',async({page})=>{
 const {build}=await import('vite');const {resolve}=await import('node:path');
 await build({logLevel:'warn',plugins:[{name:'police-test',enforce:'pre',transform(src,id){if(id.endsWith('/src/game/main.ts'))return src.replace('resize(); requestAnimationFrame(frame);','window.__policeTest = {addCar,addStar,police,player};\nresize(); requestAnimationFrame(frame);');}}],build:{outDir:resolve('.work/police'),rollupOptions:{input:resolve('src/index.html')}}});
 const errors=watchErrors(page);await page.setViewportSize({width:640,height:360});await page.goto('/.work/police/index.html');await page.locator('#go').click();
 const start=await page.evaluate(()=>{const G=window.__policeTest;const p=G.addCar('polis',G.player.x+30,G.player.z+10,0,'police','xc70-police');G.police.push(p);G.addStar();return {x:p.x,z:p.z};});
 await expect.poll(()=>page.evaluate(()=>!!window.__policeTest.police[0].mesh.getObjectByName('body'))).toBe(true);
 await expect.poll(()=>page.evaluate(start=>{const p=window.__policeTest.police[0];return Math.hypot(p.x-start.x,p.z-start.z);},start)).toBeGreaterThan(1);
 await expect.poll(()=>page.evaluate(()=>{let lit=false;window.__policeTest.police[0].mesh.traverse(n=>{if(/^lamp_(blue_module|police_grille)/.test(n.name)&&n.material?.emissiveIntensity>0)lit=true;});return lit;})).toBe(true);
 expect(errors).toEqual([]);
});
