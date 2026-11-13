// Runs the original assertion bodies under an explicitly reduced software profile.
// All actual rendering is verified separately by the fixed-camera review tool.
const fs=require('node:fs'),path=require('node:path'),{spawnSync}=require('node:child_process');
const root=process.cwd(),dir=path.join(root,'work/software-smoke');fs.mkdirSync(dir,{recursive:true});
const entry=require.resolve('@playwright/test').replace(/index\.js$/,'index.mjs'),base=path.join(root,'playwright.config.js');
fs.writeFileSync(path.join(dir,'fixture.mjs'),`import {test as base,expect} from '${entry}';
export {expect};export const test=base.extend({page:async({page},use)=>{
 await page.route('**/favicon.ico',r=>r.fulfill({status:204,body:''}));
 await page.route(/\\/(index|map)\\.html(?:\\?.*)?$/,async route=>{const response=await route.fetch();const body=(await response.text()).replace('renderer.shadowMap.enabled = true;','renderer.shadowMap.enabled = false; renderer.render=(scene,camera)=>{scene.updateMatrixWorld();camera.updateMatrixWorld()};').replace('  drawMini(T);','  /* functional profile: no minimap redraw */').replace('const CW = (coarse || renderer.capabilities.maxTextureSize < 4096) ? 2048 : 4096, K = CW / S;','const CW = 128, K = CW / S;').replace('const CW = (Math.min(innerWidth, innerHeight) < 600 || renderer.capabilities.maxTextureSize < 4096) ? 2048 : 4096;','const CW = 128;');await route.fulfill({response,body})});
 await use(page);
}});`);
for(const name of fs.readdirSync(path.join(root,'tests/e2e'))){if(!name.endsWith('.spec.js'))continue;let code=fs.readFileSync(path.join(root,'tests/e2e',name),'utf8');code=code.replace(/from ['"]@playwright\/test['"]/g,"from './fixture.mjs'");fs.writeFileSync(path.join(dir,name),code)}
fs.writeFileSync(path.join(dir,'config.mjs'),`import {default as base} from '${base}';export default {...base,testDir:'${dir}',outputDir:'${root}/test-results/software',timeout:180000,expect:{timeout:60000},use:{...base.use,deviceScaleFactor:.5,trace:'off',launchOptions:{...base.use.launchOptions,executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium'}},webServer:{...base.webServer,cwd:'${root}'}};`);
const status=spawnSync(process.execPath,[require.resolve('@playwright/test/cli'),'test','--config',path.join(dir,'config.mjs'),'--workers=1',...process.argv.slice(2)],{cwd:root,stdio:'inherit',env:process.env});process.exitCode=status.status??1;
