// Boot/interaction logic only: a minimal DOM and renderer stub, real Three.js
// scene graph, real GLTFLoader parser and real GLB. No browser/GPU claim.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import * as controls from '../media/vehicles/preview-controls.mjs';
const ROOT=new URL('../',import.meta.url);
class Element{
  constructor(){this.listeners={};this.attributes={};this.hidden=false;this.disabled=false;this.textContent='';this.value='';this.dataset={};this.captured=new Set();}
  addEventListener(name,fn){(this.listeners[name]??=[]).push(fn);}
  emit(name,event={}){for(const fn of this.listeners[name]||[])fn({preventDefault(){},...event});}
  setAttribute(name,value){this.attributes[name]=value;}
  setPointerCapture(id){this.captured.add(id);}
  hasPointerCapture(id){return this.captured.has(id);}
  releasePointerCapture(id){this.captured.delete(id);}
  getBoundingClientRect(){return this.rect||{right:356,bottom:300,top:16};}
}
async function boot(filmMode){
  const ids=Object.fromEntries(['view','info','fallback','graphics-error','vehicle','look','checkpoint','checkpoint-note','zoom-in','zoom-out','reset'].map(id=>[id,new Element()]));
  ids.view.clientWidth=1024;ids.view.clientHeight=768;ids.view.width=300;ids.view.height=150;
  const buttons=Object.keys(controls.CAMERA_VIEWS).map(name=>{const e=new Element();e.dataset.view=name;return e;});
  const header=new Element(),look=new Element(),footer=new Element();
  header.rect={right:356,bottom:317,top:16};look.rect={bottom:66};footer.rect={top:655};
  const errors=[],frames=[];
  const location={href:'https://review.invalid/?vehicle=volvo240',search:'?vehicle=volvo240'};
  const sandbox={console:{log(){},warn(){},error(...args){errors.push(args.join(' '));}},TextDecoder,TextEncoder,URL,URLSearchParams,Blob,setTimeout,clearTimeout,
    location,matchMedia:()=>({matches:true}),reviewControls:controls,
    history:{replaceState(_a,_b,url){location.href=String(url);location.search=new URL(url).search;}},
    requestAnimationFrame:fn=>setTimeout(()=>{try{fn();}catch(error){errors.push(error.message);}},0),
    ResizeObserver:class{constructor(fn){this.fn=fn;}observe(){this.fn();}},addEventListener(){},devicePixelRatio:2};
  sandbox.window=sandbox;
  sandbox.document={baseURI:'https://review.invalid/media/vehicles/',
    getElementById:id=>ids[id],
    querySelector:selector=>({'header':header,'.look':look,'.controls':footer}[selector]),
    querySelectorAll:selector=>selector==='#views button'?buttons:[...buttons,...Object.values(ids)],
    createElement:()=>new Element(),head:{appendChild(script){
      if(filmMode==='pending')return;
      setTimeout(()=>{
        if(filmMode==='failure'){script.onerror(new Error('Film unavailable'));return;}
        try{vm.runInContext(fs.readFileSync(new URL('src/visual/film-pipeline.js',ROOT),'utf8'),context);script.onload();}
        catch(error){errors.push(error.message);script.onerror(error);}
      },0);
    }}};
  const context=vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(new URL('media/vehicles/vendor/three-r128.min.js',ROOT),'utf8'),context);
  vm.runInContext(fs.readFileSync(new URL('media/vehicles/vendor/GLTFLoader-r128.js',ROOT),'utf8'),context);
  context.THREE.WebGLRenderer=class{
    constructor({canvas}){this.canvas=canvas;this.capabilities={isWebGL2:false};this.pixelRatio=1;}
    setPixelRatio(n){this.pixelRatio=n;}getPixelRatio(){return this.pixelRatio;}
    setSize(w,h){this.canvas.width=Math.round(w*this.pixelRatio);this.canvas.height=Math.round(h*this.pixelRatio);}
    getDrawingBufferSize(v){return v.set(this.canvas.width,this.canvas.height);}
    setRenderTarget(){}render(scene){frames.push(scene);}
  };
  context.THREE.GLTFLoader.prototype.load=function(url,resolve,_progress,reject){
    const path=new URL(url,sandbox.document.baseURI).pathname.slice(1);
    fs.promises.readFile(new URL(path,ROOT)).then(data=>{
      this.parse(data.buffer.slice(data.byteOffset,data.byteOffset+data.byteLength),'',resolve,reject);
    },reject);
  };
  const js=fs.readFileSync(new URL('media/vehicles/preview.js',ROOT),'utf8')
    .replace("await import('./preview-controls.mjs')",'reviewControls');
  vm.runInContext(js,context);
  return {context,ids,buttons,errors,frames};
}
async function until(condition){
  for(let i=0;i<200;i++){if(condition())return;await new Promise(resolve=>setTimeout(resolve,5));}
  assert.fail('Preview did not reach the expected state');
}
test('GLB becomes ready even while optional film script never completes',async()=>{
  const app=await boot('pending');await until(()=>app.context.__vehicleReview?.state().ready);
  const s=app.context.__vehicleReview.state();
  assert.equal(s.vehicle,'volvo240');assert.equal(s.triangles,3748);
  assert.equal(s.modelRotationY,0);assert.deepEqual([...s.modelScale],[1,1,1]);
  assert.ok(Math.abs(s.bounds.length-4.82)<.00001);
  assert.match(app.ids.info.textContent,/authored scale/);assert.deepEqual(app.errors,[]);
});
test('existing film script boots with preview globals; controls and neutral toggle work',async()=>{
  const app=await boot('success');await until(()=>app.context.__vehicleReview?.state().ready&&app.context.__vehicleReview.state().film==='negative');
  const state=()=>app.context.__vehicleReview.state();
  app.buttons.find(b=>b.dataset.view==='front').emit('click');assert.equal(state().view,'front');assert.equal(state().projection,'orthographic');
  app.ids.view.emit('pointerdown',{pointerId:1,clientX:100,clientY:200});
  app.ids.view.emit('pointerdown',{pointerId:2,clientX:200,clientY:200});
  app.ids.view.emit('pointermove',{pointerId:2,clientX:300,clientY:200});assert.equal(state().zoom,.5);
  app.ids.view.emit('pointercancel',{pointerId:2});app.ids.view.emit('pointerup',{pointerId:1});assert.equal(state().activePointers,0);
  app.ids.look.value='off';app.ids.look.emit('change');assert.equal(state().film,'off');
  app.ids.reset.emit('click');assert.equal(state().view,'three_quarter');assert.equal(state().zoom,1);
  await until(()=>app.frames.some(scene=>scene.getObjectByName('body')));
  assert.equal(app.ids.fallback.hidden,true);
  assert.deepEqual(app.errors,[]);
});
test('film download failure retains a working neutral GLB preview',async()=>{
  const app=await boot('failure');await until(()=>app.context.__vehicleReview?.state().ready&&app.ids.look.disabled);
  assert.equal(app.context.__vehicleReview.state().vehicle,'volvo240');assert.deepEqual(app.errors,[]);
});
