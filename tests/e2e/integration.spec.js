import {test,expect} from '@playwright/test';
import {watchErrors,buildFixture} from './render-helpers.js';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
test('combined shader grades before grain, with one copy and draw, and independent bypass',async({page})=>{
 await buildFixture('combined');const errors=watchErrors(page);
 await page.goto('/.work/combined/index.html');await page.waitForFunction(()=>window.harness);
 expect(await page.evaluate(()=>window.harness.finish.state().copies)).toBe(0);
 for(const [film,grain] of [['negative','strong'],['off','subtle'],['gold','off']]){
  const before=await page.evaluate(([f,g])=>{const h=window.harness;h.grades.set(f);h.grain.set(g);return h.finish.state();},[film,grain]);
  await expect.poll(()=>page.evaluate(()=>window.harness.finish.state().copies)).toBeGreaterThan(before.copies+3);
  const after=await page.evaluate(()=>window.harness.finish.state());
  expect(after.copies-before.copies).toBe(after.frames-before.frames);expect(after.passes).toBe(after.copies);
 }
 const order=await page.evaluate(()=>{
  const r=window.harness.renderer,gl=r.getContext();
  return r.info.programs.flatMap(p=>gl.getAttachedShaders(p.program).map(s=>gl.getShaderSource(s))).find(s=>s.includes('c=photographicGrade(c);'));
 });
 expect(order.indexOf('c=photographicGrade(c);')).toBeLessThan(order.indexOf('c=photographicGrain(c);'));
 const before=await page.evaluate(()=>{const h=window.harness;h.grain.set('off');h.grades.set('off');return h.finish.state();});
 await expect.poll(()=>page.evaluate(()=>window.harness.finish.state().nativeFrames)).toBeGreaterThan(before.nativeFrames+3);
 expect(await page.evaluate(()=>window.harness.finish.state().copies)).toBe(before.copies);
 expect(await page.evaluate(()=>window.harness.renderer.getContext().getError())).toBe(0);expect(errors).toEqual([]);
});
test('actual solar lighting, all profiles and GLB fleet render together',async({page},info)=>{
 await require('../../tools/trailer/rig.js').buildCaptureCopy();const errors=watchErrors(page);
 await page.setViewportSize({width:960,height:540});
 await page.addInitScript(()=>{
  const callbacks=[];window.requestAnimationFrame=cb=>{callbacks.push(cb);return callbacks.length;};performance.now=()=>1000;
  window.stepReview=()=>{for(const cb of callbacks.splice(0))cb(1000);};
 });
 await page.goto('/tools/trailer/.work/index.html?dev=lighting');await page.waitForFunction(()=>window.__G);
 await page.locator('#go').click();
 await page.evaluate(()=>{const G=window.__G;window.staged=['volvo','saab','xc70','polis'].map((t,i)=>G.addCar(t,G.player.x-7+i*4,G.player.z-8,0,'parked'));});
 await expect.poll(()=>page.evaluate(()=>window.staged.filter(c=>c.assetType).length)).toBe(4);
 for(const [environment,hour] of [['day',13],['sunset',20.5],['night',23]]){
  await page.evaluate(hour=>{const G=window.__G;G.refreshVehicleDetail(G.player);G.daylight.setHour(hour);for(let i=0;i<30;i++)G.streetLighting.update(1/30,G.daylight.getSolarElevation());G.grain.set('off');},hour);
  for(const profile of ['off','chrome','negative','gold','portra']){
   await page.evaluate(profile=>{window.__G.grades.set(profile);window.stepReview();},profile);
   await page.screenshot({path:info.outputPath(`${environment}-${profile}.png`)});
  }
  await page.evaluate(()=>{window.__G.grain.set('strong');window.stepReview();});
  const s=await page.evaluate(()=>window.__joyride.state());
  expect(s.film.preset).toBe('portra');expect(s.grain.enabled).toBe(true);expect(s.rendering.passes).toBe(s.rendering.copies);
  expect(s.visibleVehicles).toBeGreaterThan(0);
  await page.screenshot({path:info.outputPath(`${environment}-portra-grain.png`)});
 }
 expect(await page.evaluate(()=>window.__G.renderer.getContext().getError())).toBe(0);expect(errors).toEqual([]);
});
