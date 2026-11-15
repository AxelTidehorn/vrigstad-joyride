import assert from 'node:assert/strict';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import '../src/world/three-legacy.ts';
import { createVehicleAssets } from '../src/game/render/vehicle-assets.ts';
const load = GLTFLoader.prototype.load;
const template = new THREE.Group();
const body = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshStandardMaterial()); body.name='body'; template.add(body);
for(const name of ['wheel_fl','wheel_fr','wheel_rl','wheel_rr']){const wheel=new THREE.Group();wheel.name=name;template.add(wheel);}
const lamp = new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshStandardMaterial());lamp.name='lamp_blue_module';template.add(lamp);
GLTFLoader.prototype.load=function(url,done){queueMicrotask(()=>done({scene:template}));};
try {
 const assets=createVehicleAssets();
 const make=paint=>{const mesh=new THREE.Group();new THREE.Scene().add(mesh);const fallback=new THREE.Mesh();mesh.add(fallback);const car={mesh,assetWheelTravel:1,visualSteer:.3};assets.install(car,'volvo',fallback,paint);return car;};
 const a=make('#27406b'),b=make('#7a2530');await new Promise(resolve=>setImmediate(resolve));
 assert.equal(a.assetWheels.length,4);
 const expected=new THREE.Color('#27406b').convertSRGBToLinear();
 assert.ok(a.visual.getObjectByName('body').material.color.equals(expected));
 assert.notEqual(a.visual.getObjectByName('body').material,b.visual.getObjectByName('body').material);
 assert.ok(a.assetBeacons[0].emissive.equals(new THREE.Color('#176cff').convertSRGBToLinear()));
 assets.update(a);assert.equal(a.assetWheels[0].steer.rotation.y,.3);assert.notEqual(a.assetWheels[0].spin.rotation.x,0);
 assets.setDetailed(a,true);assert.equal(a.visual.visible,true);assert.equal(a.assetFallback.visible,false);
 assets.setDetailed(a,false);assert.equal(a.visual.visible,false);assert.equal(a.assetFallback.visible,true);
 const owned=[...a.assetMaterials];let disposed=0;for(const m of owned)m.addEventListener('dispose',()=>disposed++);
 assets.dispose(a);assert.equal(disposed,owned.length);assert.equal(a.mesh.children.length,1);
 // Cancellation before a cached asynchronous install must leave only fallback.
 const c=make('#27406b');assets.dispose(c);await new Promise(resolve=>setImmediate(resolve));assert.equal(c.visual,undefined);
 console.log('Adapter paint, wheels, fallback, cancellation and material disposal passed');
} finally {GLTFLoader.prototype.load=load;}
