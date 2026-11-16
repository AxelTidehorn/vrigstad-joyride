// Controller regressions use real exports in Node, without building or patching the game.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {build} from 'vite';
await build({configFile:false,publicDir:false,logLevel:'error',build:{outDir:'.work/visual-test',lib:{entry:'src/game/render/vehicle-visuals.ts',formats:['es'],fileName:()=> 'visuals.mjs'},rolldownOptions:{external:id=>id==='three'||id.startsWith('three/')}}});
const {createVehicleVisuals}=await import('../.work/visual-test/visuals.mjs');
THREE.ColorManagement.enabled=false;
const loader=new GLTFLoader(), original=GLTFLoader.prototype.loadAsync;
const requests=[];
async function parse(url){const b=readFileSync('src/public/'+url);return loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'');}
GLTFLoader.prototype.loadAsync=async function(url){requests.push(url);return parse(url);};
const focus={x:0,z:0};
function car(x=0){const mesh=new THREE.Group(),fallback=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshBasicMaterial());mesh.add(fallback);return {mesh,fallback,x,z:0,h:0};}
async function settled(assets,cars){for(let i=0;i<100;i++){if(cars.every(c=>assets.state(c)?.status!=='loading'))return;await new Promise(r=>setTimeout(r,10));}assert.fail('GLB controller did not settle');}
try {
 const assets=createVehicleVisuals(false), a=car(), b=car(2);
 assets.attach(a,'volvo240',a.fallback);assets.attach(b,'volvo240',b.fallback,'#abcdef');
 assets.paint(a,'#27406b'); // input before asynchronous load must survive
 assets.update(focus,.01);await settled(assets,[a,b]);
 const bodyA=a.mesh.getObjectByName('body'),bodyB=b.mesh.getObjectByName('body');
 assert.equal(requests.length,1);assert.equal(bodyA.geometry,bodyB.geometry);
 assert.notEqual(bodyA.material,bodyB.material);
 assert.ok(bodyB.material.color.equals(new THREE.Color('#abcdef').convertSRGBToLinear()));
 assert.ok(bodyA.material.color.equals(new THREE.Color('#27406b').convertSRGBToLinear()));
 const originalColor=bodyB.material.color.clone(),glass=a.mesh.getObjectByName('glass_envelope'),glassMaterial=glass.material;
 assets.paint(a,'#992233');assert.ok(bodyB.material.color.equals(originalColor));assert.equal(glass.material,glassMaterial);
 a.x+=.1;a.z-=1;a.h+=.1;assets.sync(a);
 assert.ok(assets.state(a).wheels[0].steer<0);assert.ok(assets.state(a).wheels[0].spin<0);
 a.x-=.1;a.z+=1;a.h-=.1;assets.sync(a);assert.ok(assets.state(a).wheels[0].steer<0);
 a.x+=100;const spin=assets.state(a).wheels[0].spin;assets.sync(a);assert.equal(assets.state(a).wheels[0].spin,spin);
 let disposed=false;bodyA.material.addEventListener('dispose',()=>disposed=true);assets.dispose(a);assert.ok(disposed);assert.equal(assets.state(a),null);
 // Preserve police paint and exercise the actual exported beacon meshes.
 const police=car();assets.attach(police,'xc70-police',police.fallback,'#ff0000');assets.update(focus,.4);await settled(assets,[police]);
 const policeBody=police.mesh.getObjectByName('body'),paint=policeBody.material;assets.paint(police,'#ff0000');assert.equal(policeBody.material,paint);
 const beacons=[];police.mesh.traverse(n=>{if(/^lamp_(blue_module|police_grille)/.test(n.name)&&n.material)beacons.push(n.material);});assert.ok(beacons.length>0);
 assets.update(focus,.22);const lit=beacons[0].emissiveIntensity;assets.update(focus,.22);assert.notEqual(beacons[0].emissiveIntensity,lit);
 // Failed nearest models cannot starve a healthy fourth model on coarse devices.
 GLTFLoader.prototype.loadAsync=async function(url){if(url.endsWith('micra-k11.glb'))throw new Error('expected missing asset');return parse(url);};
 const coarse=createVehicleVisuals(true), cars=[1,2,3,4].map(x=>car(x));
 cars.forEach((c,i)=>coarse.attach(c,i===3?'volvo240':'micra-k11',c.fallback));
 const warn=console.warn;console.warn=()=>{};
 try{coarse.update(focus,.4);await settled(coarse,cars.slice(0,3));}finally{console.warn=warn;}
 coarse.update(focus,.4);await settled(coarse,cars);
 assert.equal(coarse.state(cars[3]).status,'loaded');assert.ok(coarse.state(cars[3]).detailed);
 assert.ok(cars.slice(0,3).every(c=>coarse.state(c).fallback));
 // Both detail caps and range culling remain effective.
 for(const [isCoarse,limit] of [[true,3],[false,8]]){
  const pool=createVehicleVisuals(isCoarse), cs=Array.from({length:9},(_,i)=>car(i+1));cs.forEach(c=>pool.attach(c,'volvo240',c.fallback));
  pool.update(focus,.4);await settled(pool,cs);assert.equal(cs.filter(c=>pool.state(c).detailed).length,limit);
  pool.update({x:1000,z:0},.4);assert.ok(cs.every(c=>pool.state(c).fallback));
 }
 // Preserve the supported uniform ancestor scale when detaching wheel nodes.
 const template=new THREE.Group(), parent=new THREE.Group();parent.scale.setScalar(2);template.add(parent);
 parent.add(Object.assign(new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial()),{name:'body'}));
 for(const name of ['wheel_fl','wheel_fr','wheel_rl','wheel_rr']){const n=new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());n.name=name;n.scale.setScalar(.5);n.position.set(name.endsWith('l')?-1:1,1,name.includes('_f')?-1:1);parent.add(n);}
 template.updateMatrixWorld(true);const expected=new THREE.Box3().setFromObject(template);
 GLTFLoader.prototype.loadAsync=async()=>({scene:template});
 const scaled=createVehicleVisuals(false), sc=car();scaled.attach(sc,'volvo240',sc.fallback);scaled.update(focus,.4);await settled(scaled,[sc]);sc.mesh.updateMatrixWorld(true);
 const bounds=new THREE.Box3().setFromObject(sc.mesh.children.find(n=>n!==sc.fallback));assert.ok(bounds.min.distanceTo(expected.min)<1e-8&&bounds.max.distanceTo(expected.max)<1e-8);
 // Removing an instance while loading must not resurrect its visual.
 let resolve;GLTFLoader.prototype.loadAsync=()=>new Promise(r=>resolve=r);
 const pending=createVehicleVisuals(false), removed=car();pending.attach(removed,'volvo240',removed.fallback);pending.update(focus,.4);pending.dispose(removed);resolve({scene:template});await new Promise(r=>setImmediate(r));assert.equal(removed.mesh.children.length,1);assert.equal(pending.state(removed),null);
 console.log('vehicle visuals: cache, pending paint, glass/livery, wheel transforms, disposal, failure recovery, detail caps and beacons passed');
} finally {GLTFLoader.prototype.loadAsync=original;}
