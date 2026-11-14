import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import {CAMERA_VIEWS,orbitState,setFixedView,pointerDown,pointerMove,pointerUp,zoomBy,reviewRegion,frameReviewCamera} from '../media/vehicles/preview-controls.mjs';

// Exercise the actual pinned loader and exported GLB without a browser or GPU.
const context=vm.createContext({console,TextDecoder,TextEncoder,URL,Blob,setTimeout,clearTimeout});
vm.runInContext(fs.readFileSync(new URL('../media/vehicles/vendor/three-r128.min.js',import.meta.url),'utf8'),context);
vm.runInContext(fs.readFileSync(new URL('../media/vehicles/vendor/GLTFLoader-r128.js',import.meta.url),'utf8'),context);
const THREE=context.THREE;
const bytes=fs.readFileSync(new URL('../experiments/volvo240/renders/iter_02/volvo240.glb',import.meta.url));
const buffer=bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);
const source=await new Promise((resolve,reject)=>new THREE.GLTFLoader().parse(buffer,'',g=>resolve(g.scene),reject));
const box=new THREE.Box3().setFromObject(source),target=box.getCenter(new THREE.Vector3());
const dimensions=box.getSize(new THREE.Vector3()),radius=dimensions.length()/2,corners=[];
for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z])corners.push(new THREE.Vector3(x,y,z));

test('actual GLB loads at real dimensions and -Z-forward wheel positions',()=>{
  assert.ok(Math.abs(dimensions.z-4.82)<.00001);
  assert.ok(Math.abs(dimensions.x-1.71)<.00001);
  assert.ok(Math.abs(dimensions.y-1.43)<.00001);
  for(const name of ['wheel_fl','wheel_fr','wheel_rl','wheel_rr']){
    const wheel=source.getObjectByName(name);assert.ok(wheel,name);
    const c=new THREE.Box3().setFromObject(wheel).getCenter(new THREE.Vector3());
    assert.equal(c.z<0,name.includes('_f'),name+' front/rear');
    assert.equal(c.x<0,name.endsWith('l'),name+' left/right');
  }
  assert.ok(source.getObjectByName('body'));
});
test('pinch spread zooms in; releasing one finger continues without a jump',()=>{
  const s=orbitState();pointerDown(s,1,100,200);pointerDown(s,2,200,200);
  const az=s.az;pointerMove(s,2,300,200);assert.equal(s.zoom,.5);assert.equal(s.az,az);
  pointerUp(s,2);pointerMove(s,1,100,200);assert.equal(s.az,az);
  pointerMove(s,1,120,200);assert.ok(Math.abs(s.az-(az-.14))<1e-12);
  pointerUp(s,1);assert.equal(s.pointers.size,0);
  assert.equal(pointerMove(s,1,900,900),false);
});
test('cancelled, third and crossing touches do not create invalid zoom',()=>{
  const s=orbitState();pointerDown(s,1,100,100);pointerDown(s,2,200,100);
  assert.equal(pointerDown(s,3,300,100),false);
  pointerMove(s,2,100,100);assert.ok(Number.isFinite(s.zoom));
  pointerUp(s,1);pointerUp(s,2);assert.equal(s.pointers.size,0);
  zoomBy(s,100);assert.equal(s.zoom,2.8);zoomBy(s,.00001);assert.equal(s.zoom,.45);
  zoomBy(s,NaN);assert.equal(s.zoom,.45);
});
test('fixed views restore neutral zoom and reset active gesture state',()=>{
  const s=orbitState();pointerDown(s,1,100,100);zoomBy(s,.6);
  assert.equal(setFixedView(s,'top'),true);assert.equal(s.zoom,1);assert.equal(s.pointers.size,0);
  assert.equal(s.el,Math.PI/2);assert.equal(s.ortho,true);
  assert.equal(setFixedView(s,'__proto__'),false);
});
for(const [width,height,panels] of [
  [1024,768,{headerRight:356,headerBottom:270,lookBottom:66,controlsTop:655}],
  [768,1024,{headerRight:356,headerBottom:270,lookBottom:66,controlsTop:910}],
  [1366,1024,{headerRight:356,headerBottom:270,lookBottom:66,controlsTop:910}],
  [390,844,{headerRight:380,headerBottom:230,lookBottom:80,controlsTop:720}],
]){
  test(`five views fit the available ${width}×${height} review region`,()=>{
    const region=reviewRegion(width,height,panels);
    for(const name of Object.keys(CAMERA_VIEWS)){
      const state=orbitState();setFixedView(state,name);
      const camera=frameReviewCamera(THREE,{state,perspective:new THREE.PerspectiveCamera(38,1,.05,1000),
        orthographic:new THREE.OrthographicCamera(-3,3,3,-3,.05,1000),target,corners,radius,width,height,region});
      for(const point of corners){
        const p=point.clone().project(camera),x=(p.x+1)*width/2,y=(1-p.y)*height/2;
        assert.ok(x>=region.x-1&&x<=region.x+region.width+1,`${name}: x=${x}`);
        assert.ok(y>=region.y-1&&y<=region.y+region.height+1,`${name}: y=${y}`);
        assert.ok(p.z>=-1&&p.z<=1,`${name}: clip z=${p.z}`);
      }
      if(name==='side'){
        const front=new THREE.Vector3(0,.7,-1.42).project(camera);
        const rear=new THREE.Vector3(0,.7,1.23).project(camera);
        assert.ok(front.x<rear.x,'front points left in side view');
      }
      if(name==='top'){
        const front=new THREE.Vector3(0,.7,-1.42).project(camera);
        const rear=new THREE.Vector3(0,.7,1.23).project(camera);
        assert.ok(front.y>rear.y,'front points up in top view');
      }
    }
  });
}
