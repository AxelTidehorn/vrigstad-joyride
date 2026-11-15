// Actual-GLB browser check, including depth precision for the existing film target.
import {chromium} from '@playwright/test';
import {writeFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
const out=fileURLToPath(new URL('./build/',import.meta.url));
const url=process.argv[2]||'http://127.0.0.1:8059/experiments/impala1970/preview.html';
const browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1024,height:768},hasTouch:true});
const errors=[],depth=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
const frame=()=>page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
try{
  await page.goto(url);
  await page.waitForFunction(()=>window.__vehicleReview?.state().ready);
  for(const mode of ['off','negative']){
    await page.selectOption('#look',mode);
    for(const view of ['side','front','rear','top','three_quarter']){
      await page.locator(`button[data-view="${view}"]`).click();
      for(const zoom of ['normal','minimum','maximum']){
        if(zoom!=='normal')await page.evaluate(which=>{
          const button=document.querySelector(which==='minimum'?'#zoom-in':'#zoom-out');
          for(let i=0;i<30;i++)button.click();
        },zoom);
        await frame();
        const probe=await page.evaluate(()=>{
          const state=window.__vehicleReview.state(),box=new THREE.Box3().setFromObject(scene.getObjectByName('body').parent);
          let depth=0;
          for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z]){
            const p=new THREE.Vector3(x,y,z).applyMatrix4(camera.matrixWorldInverse);depth=Math.max(depth,-p.z);
          }
          const n=camera.near,f=camera.far;
          const step=camera.isOrthographicCamera?(f-n)/65535:(f-n)*depth*depth/(f*n*65535);
          return {view:state.view,zoom:state.zoom,near_m:n,far_m:f,worst_car_depth_m:depth,conservative_16bit_step_m:step,ready:state.ready};
        });
        if(!probe.ready||probe.view!==view||probe.conservative_16bit_step_m>=.001)throw new Error('Insufficient camera depth precision: '+JSON.stringify(probe));
        depth.push({mode,...probe});
      }
    }
  }
  await page.locator('button[data-view="three_quarter"]').click();
  await page.selectOption('#paint','#653b43');await frame();
  await page.screenshot({path:out+'browser-preview.png'});
  const result={ok:errors.length===0,browser:'Chromium headless / SwiftShader, touch emulation',viewport:[1024,768],state:await page.evaluate(()=>window.__vehicleReview.state()),depth_samples:depth,errors,scope:'Actual current GLB, both film modes, five fixed views and zoom extremes. Conservative 16-bit depth bound below 1 mm. Screenshot requires human inspection; no pixel-diff approval, physical Safari or game integration claim.'};
  await writeFile(out+'browser-preview.json',JSON.stringify(result,null,2)+'\n');
  if(!result.ok)throw new Error(JSON.stringify(errors));
  console.log(JSON.stringify({ok:true,depth_samples:depth.length,max_16bit_step_m:Math.max(...depth.map(x=>x.conservative_16bit_step_m)),errors}));
}finally{await browser.close();}
