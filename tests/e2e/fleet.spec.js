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
  const original=b.material.color.clone();assets.paint(cars[0],'#27406b');
  const independent=a.material!==b.material&&b.material.color.equals(original);
  const linear=a.material.color.equals(new THREE.Color('#27406b').convertSRGBToLinear());
  let disposed=false;a.material.addEventListener('dispose',()=>disposed=true);assets.dispose(cars[0]);
  return {shared,independent,linear,disposed,removed:assets.state(cars[0])===null};
 });
 expect(result).toEqual({shared:true,independent:true,linear:true,disposed:true,removed:true});expect(requests).toBe(1);
});
test('production and development asset paths serve real GLBs',async({page})=>{
 for(const name of ['volvo240','saab900-t16','xc70-civilian','xc70-police','impala1970','micra-k11','duett-p210-epa']){
  const r=await page.request.get('/dist/media/vehicles/'+name+'.glb');expect(r.ok()).toBe(true);expect((await r.body()).subarray(0,4).toString()).toBe('glTF');
 }
 const {createServer}=await import('vite');const server=await createServer({server:{port:0,host:'127.0.0.1'}});await server.listen();
 try{await page.goto(server.resolvedUrls.local[0]+'?vehicle=micra-k11');await expect.poll(()=>page.evaluate(()=>window.__joyride?.state().vehicle?.status)).toBe('loaded');}finally{await server.close();}
});
