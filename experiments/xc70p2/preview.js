// These four bindings are the existing film pipeline's preview-only environment.
let renderer,scene,camera;
const coarse=matchMedia('(pointer: coarse)').matches;
(async function(){
'use strict';
const canvas=document.getElementById('view'),info=document.getElementById('info');
const fallback=document.getElementById('fallback'),errorBox=document.getElementById('graphics-error');
const selector=document.getElementById('vehicle'),look=document.getElementById('look');
const buttons=[...document.querySelectorAll('#views button')];
const assets={civilian:{file:'build/xc70-civilian.glb',rotation:0,length:null,label:'XC70 P2 civilian'},police:{file:'build/xc70-police.glb',rotation:0,length:null,label:'XC70 P2 Swedish police'}};
function fail(message){
  canvas.hidden=true;fallback.hidden=false;errorBox.hidden=false;
  errorBox.textContent=message+' The PNG sheet and downloads remain available above.';
  info.textContent='Interactive view unavailable; showing a fixed PNG.';
  document.querySelectorAll('button,select').forEach(element=>element.disabled=true);
}
try{
  if(!window.THREE||!THREE.GLTFLoader)throw new Error('The preview libraries did not load.');
  renderer=new THREE.WebGLRenderer({canvas,antialias:true,powerPreference:'low-power'});
}catch(error){fail(error.message);return;}
const controls=await import('../../media/vehicles/preview-controls.mjs');
const state=controls.orbitState(),cache=new Map();
const target=new THREE.Vector3(),size=new THREE.Vector3(),corners=[];
let root=null,currentId=null,sequence=0,queued=false,filmReady=false,ready=false,triangleCount=0;
let selectedView='three_quarter',radius=3,bounds=null,contextLost=false;
scene=new THREE.Scene();
const perspective=new THREE.PerspectiveCamera(38,1,.05,1000);
const orthographic=new THREE.OrthographicCamera(-3,3,3,-3,.05,1000);
camera=perspective;
renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,1.5));
renderer.outputEncoding=THREE.sRGBEncoding;
scene.background=new THREE.Color('#798b8f');
scene.add(new THREE.HemisphereLight(0xf0ebd8,0x475b52,1.1));
const key=new THREE.DirectionalLight(0xffedcf,.9);key.position.set(-4,7,-5);scene.add(key);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(18,18),new THREE.MeshLambertMaterial({color:0x667467}));
floor.rotation.x=-Math.PI/2;floor.position.y=-.022;scene.add(floor);
const grid=new THREE.GridHelper(14,28,0x687b70,0x758477);grid.position.y=-.012;
grid.material.transparent=true;grid.material.opacity=.32;scene.add(grid);
const loader=new THREE.GLTFLoader();
function invalidate(){if(!queued&&!contextLost){queued=true;requestAnimationFrame(draw);}}
function draw(){
  queued=false;if(contextLost)return;
  const width=canvas.clientWidth,height=canvas.clientHeight;if(!width||!height)return;
  const pixelRatio=renderer.getPixelRatio();
  if(canvas.width!==Math.round(width*pixelRatio)||canvas.height!==Math.round(height*pixelRatio)){
    renderer.setSize(width,height,false);if(filmReady)resizeFilmFrame();
  }
  const header=document.querySelector('header').getBoundingClientRect();
  const region=controls.reviewRegion(width,height,{headerRight:header.right,headerBottom:header.bottom,
    lookBottom:document.querySelector('.look').getBoundingClientRect().bottom,
    controlsTop:document.querySelector('.controls').getBoundingClientRect().top});
  camera=controls.frameReviewCamera(THREE,{state,perspective,orthographic,target,corners,radius,width,height,region});
  if(filmReady)renderFilmFrame();else renderer.render(scene,camera);
  if(ready)fallback.hidden=true;
}
function chooseView(name){
  if(!controls.setFixedView(state,name))return;
  selectedView=name;buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===name)));invalidate();
}
function freeView(){selectedView=null;buttons.forEach(b=>b.setAttribute('aria-pressed','false'));}
async function sourceFor(config){
  if(!cache.has(config.file))cache.set(config.file,new Promise((resolve,reject)=>loader.load(config.file,g=>{
    g.scene.traverse(obj=>{if(!obj.isMesh)return;const list=Array.isArray(obj.material)?obj.material:[obj.material];
      for(const mat of list){mat.metalness=0;mat.roughness=.88;mat.envMapIntensity=0;mat.needsUpdate=true;}
    });resolve(g.scene);
  },undefined,reject)));
  try{return await cache.get(config.file);}catch(error){cache.delete(config.file);throw error;}
}
async function show(id){
  const config=assets[id];if(!config)return;
  const request=++sequence;ready=false;info.textContent='Loading '+config.label+'…';
  try{
    const source=await sourceFor(config);if(request!==sequence)return;
    if(root)scene.remove(root);
    root=new THREE.Group();root.add(source.clone(true));root.rotation.y=config.rotation;
    root.updateMatrixWorld(true);
    let box=new THREE.Box3().setFromObject(root);box.getSize(size);
    if(config.length)root.scale.setScalar(config.length/size.z);
    root.updateMatrixWorld(true);box.setFromObject(root);box.getCenter(target);
    root.position.x-=target.x;root.position.z-=target.z;root.position.y-=box.min.y;
    root.updateMatrixWorld(true);box.setFromObject(root);box.getCenter(target);box.getSize(size);
    bounds={width:size.x,height:size.y,length:size.z};radius=size.length()/2;
    corners.length=0;
    for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z])corners.push(new THREE.Vector3(x,y,z));
    triangleCount=0;root.traverse(obj=>{if(obj.isMesh)triangleCount+=(obj.geometry.index?obj.geometry.index.count:obj.geometry.attributes.position.count)/3;});
    scene.add(root);currentId=id;ready=true;canvas.hidden=false;
    info.textContent=`${size.z.toFixed(2)} m long · ${triangleCount.toLocaleString()} triangles · ${config.length?'uniform review scale':'authored scale'}`;
    document.getElementById('checkpoint').hidden=id!=='civilian';document.getElementById('checkpoint-note').hidden=id!=='civilian';
    chooseView('three_quarter');
    const url=new URL(location.href);url.searchParams.set('vehicle',id);history.replaceState(null,'',url);
  }catch(error){if(request!==sequence)return;if(currentId)selector.value=currentId;info.textContent='Could not load this model. Choose another vehicle or open the PNG review sheet.';console.error('Vehicle preview load failed',error);}
}
selector.addEventListener('change',()=>show(selector.value));
buttons.forEach(button=>button.addEventListener('click',()=>chooseView(button.dataset.view)));
document.getElementById('zoom-in').addEventListener('click',()=>{controls.zoomBy(state,.85);invalidate();});
document.getElementById('zoom-out').addEventListener('click',()=>{controls.zoomBy(state,1/.85);invalidate();});
document.getElementById('reset').addEventListener('click',()=>chooseView('three_quarter'));
canvas.addEventListener('pointerdown',event=>{
  if(controls.pointerDown(state,event.pointerId,event.clientX,event.clientY)){canvas.setPointerCapture(event.pointerId);event.preventDefault();}
});
canvas.addEventListener('pointermove',event=>{
  if(controls.pointerMove(state,event.pointerId,event.clientX,event.clientY)){freeView();invalidate();event.preventDefault();}
});
function release(event){controls.pointerUp(state,event.pointerId);if(canvas.hasPointerCapture(event.pointerId))canvas.releasePointerCapture(event.pointerId);}
canvas.addEventListener('pointerup',release);canvas.addEventListener('pointercancel',release);canvas.addEventListener('lostpointercapture',event=>controls.pointerUp(state,event.pointerId));
canvas.addEventListener('wheel',event=>{event.preventDefault();controls.zoomBy(state,Math.exp(event.deltaY*(event.deltaMode===1?.035:.001)));invalidate();},{passive:false});
canvas.addEventListener('keydown',event=>{
  if(event.key==='+'||event.key==='=')controls.zoomBy(state,.85);
  else if(event.key==='-')controls.zoomBy(state,1/.85);
  else if(event.key==='ArrowLeft')state.az-=.1;
  else if(event.key==='ArrowRight')state.az+=.1;
  else if(event.key==='ArrowUp')state.el=controls.clamp(state.el+.1,-.12,Math.PI/2);
  else if(event.key==='ArrowDown')state.el=controls.clamp(state.el-.1,-.12,Math.PI/2);
  else return;event.preventDefault();freeView();invalidate();
});
canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();contextLost=true;info.textContent='Graphics paused. The PNG review sheet is available while Safari restores the view.';});
canvas.addEventListener('webglcontextrestored',()=>{contextLost=false;info.textContent='Graphics restored.';invalidate();});
window.addEventListener('resize',invalidate);
if(window.ResizeObserver){const observer=new ResizeObserver(invalidate);[canvas,document.querySelector('header'),document.querySelector('.controls')].forEach(element=>observer.observe(element));}
function applyLook(){if(filmReady){setFilmPreset(look.value);filmFrameMaterial.uniforms.uGrain.value=look.value==='off'?0:.3;filmFrameMaterial.uniforms.uMist.value=0;}invalidate();}
look.addEventListener('change',()=>{applyLook();const url=new URL(location.href);url.searchParams.set('film',look.value);history.replaceState(null,'',url);});
window.__vehicleReview=Object.freeze({state:()=>({vehicle:currentId,ready,view:selectedView,projection:state.ortho?'orthographic':'perspective',az:state.az,el:state.el,zoom:state.zoom,activePointers:state.pointers.size,triangles:triangleCount,bounds:bounds?{...bounds}:null,film:filmReady?look.value:'unavailable',modelScale:root?root.scale.toArray():null,modelRotationY:root?root.rotation.y:null})});
const requested=new URLSearchParams(location.search).get('vehicle');selector.value=Object.prototype.hasOwnProperty.call(assets,requested)?requested:'civilian';
// The optional film pass must never hold up the primary GLB preview.
const initialModel=show(selector.value);
try{
  await new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='../../src/visual/film-pipeline.js';script.onload=resolve;script.onerror=reject;document.head.appendChild(script);});
  filmReady=true;look.value=new URLSearchParams(location.search).get('film')==='off'?'off':'negative';applyLook();resizeFilmFrame();
}catch(error){look.disabled=true;look.title='Film preview unavailable; neutral view remains active.';renderer.outputEncoding=THREE.sRGBEncoding;}
await initialModel;
})().catch(error=>{document.getElementById('info').textContent='The interactive preview could not start. Open the PNG sheet in Review sheets above.';console.error(error);});
