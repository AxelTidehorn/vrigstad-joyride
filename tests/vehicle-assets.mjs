import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {Box3,Vector3} from 'three';
const {VEHICLES:registry}=await import('../src/game/render/vehicle-registry.ts');
const loader=new GLTFLoader();
for(const spec of registry){
 const b=readFileSync('src/public/'+spec.url);
 const gltf=await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'');
 const root=gltf.scene;root.updateMatrixWorld(true);
 assert.ok(root.getObjectByName(spec.body));
 for(const name of spec.wheels)assert.ok(root.getObjectByName(name));
 root.traverse(n=>{for(const x of n.matrixWorld.elements)assert.ok(Number.isFinite(x));});
 const fl=root.getObjectByName('wheel_fl').getWorldPosition(new Vector3()),rl=root.getObjectByName('wheel_rl').getWorldPosition(new Vector3());
 assert.ok(fl.z<rl.z,'front must face -Z');assert.ok(fl.x<0,'left must be -X');assert.ok(Math.abs(rl.z-fl.z-spec.wheelbase)<.002);
 const size=new Box3().setFromObject(root).getSize(new Vector3());assert.ok(size.x>1&&size.x<3&&size.y>1&&size.y<3&&size.z>3&&size.z<7);
 console.log(spec.id,'parsed by GLTFLoader; dimensions m',size.toArray().map(v=>v.toFixed(3)).join(' x '));
}
assert.equal(registry.length,7);
