import {test,expect} from '@playwright/test';
test('Duett choice loads four GLB wheels, can be entered and driven',async({page},testInfo)=>{
 test.setTimeout(240000);
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.goto('/index.html?vehicle=duett');
 const state=()=>page.evaluate(()=>window.__joyride.state());
 await expect.poll(async()=>{const s=await state();return s.showcase.find(c=>c.type==='duett');},{timeout:60000}).toMatchObject({loaded:true,wheels:4});
 await page.locator('#go').click();
 // The selected car occupies the nearest clear Torget showcase slot. Walk
 // toward it using real controls; no teleport or writable simulation hook.
 await page.keyboard.down('KeyW');
 try{await expect(page.locator('#prompt')).toContainText('Volvo Duett',{timeout:60000});}
 finally{await page.keyboard.up('KeyW');}
 await expect(page.locator('#prompt')).toContainText('Volvo Duett');
 await page.keyboard.press('KeyE');
 await expect.poll(state).toMatchObject({inCar:true,car:'duett'});
 const before=await state();await page.keyboard.down('KeyW');
 try{await expect.poll(async()=>{const s=await state();return Math.hypot(s.x-before.x,s.z-before.z);},{timeout:60000}).toBeGreaterThan(2);}finally{await page.keyboard.up('KeyW');}
 await page.screenshot({path:testInfo.outputPath('duett-driving.png')});
 expect(errors).toEqual([]);
});
