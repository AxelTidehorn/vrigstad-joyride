import {test,expect} from '@playwright/test';
for(const [query,enabled] of [['',false],['?film=off',false],['?film=unknown',false],['?film=chrome',true],['?film=negative',true],['?film=gold',true],['?film=portra',true]])test('scene effect '+(query||'default'),async({page})=>{
  const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.goto('/index.html'+query);
  await expect.poll(()=>page.evaluate(()=>window.__joyride.state().visual.enabled)).toBe(enabled);
  expect(await page.evaluate(()=>window.__joyride.state().visual.targets)).toBe(enabled?1:0);
  expect(errors).toEqual([]);
});
