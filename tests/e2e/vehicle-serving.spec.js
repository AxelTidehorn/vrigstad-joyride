import {test,expect} from '@playwright/test';
import {createServer,preview} from 'vite';
import {watchErrors} from './render-helpers.js';
for(const mode of ['development','production']) test(`GLB fleet loads through Vite ${mode}`,async({page})=>{
 const server=mode==='development' ? await createServer({server:{host:'127.0.0.1',port:0}}) : await preview({preview:{host:'127.0.0.1',port:0}});
 if(mode==='development') await server.listen();
 try {
  const url=server.resolvedUrls.local[0];
  for(const file of ['volvo240','saab900-t16','xc70-civilian','xc70-police']) {
    const response=await page.request.get(url+'media/vehicles/'+file+'.glb');
    expect(response.ok()).toBe(true);expect((await response.body()).subarray(0,4).toString()).toBe('glTF');
  }
  const errors=watchErrors(page);
  await page.setViewportSize({width:640,height:360});
  await page.goto(url);
  await expect.poll(()=>page.evaluate(()=>window.__joyride?.state().loadedVehicles)).toBeGreaterThan(0);
  await expect.poll(()=>page.evaluate(()=>window.__joyride.state().visibleVehicles)).toBeGreaterThan(0);
  expect(await page.evaluate(()=>document.querySelector('#gl').getContext('webgl2').getError())).toBe(0);
  expect(errors).toEqual([]);
 } finally {
   if(mode==='development') await server.close();
   else await new Promise(resolve=>server.httpServer.close(resolve));
 }
});
