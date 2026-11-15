// Actual Vehicle Lab loader compatibility, without claiming WebGL/browser QA.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import vm from 'node:vm';
import {applyBodyPaint} from './paint.mjs';
const context=vm.createContext({console,setTimeout,clearTimeout,TextDecoder,TextEncoder,URL,Blob,atob,btoa});
for(const file of ['three-r128.min.js','GLTFLoader-r128.js'])vm.runInContext(readFileSync(new URL('../../media/vehicles/vendor/'+file,import.meta.url),'utf8'),context);
const bytes=readFileSync(new URL('../../media/vehicles/duett-p210-epa.glb',import.meta.url));
const data=bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength);
const asset=await new Promise((resolve,reject)=>new context.THREE.GLTFLoader().parse(data,'',resolve,reject));
const scene=asset.scene;scene.updateMatrixWorld(true);
for(const name of ['body','wheel_fl','wheel_fr','wheel_rl','wheel_rr'])assert.ok(scene.getObjectByName(name),name);
const box=new context.THREE.Box3().setFromObject(scene),size=box.getSize(new context.THREE.Vector3());
assert.ok(Math.abs(size.y-1.750)<.002);assert.ok(Math.abs(size.z-4.100)<.002);
const snapshot=[];scene.traverse(o=>{if(o.isMesh&&o.name!=='body')snapshot.push([o,o.material.color.getHex()]);});
applyBodyPaint(scene,'#719a95');for(const [node,colour] of snapshot)assert.equal(node.material.color.getHex(),colour);
const report={ok:true,loader:'Unchanged vendored Three r128 GLTFLoader used by the Vehicle Lab page',bounds_m:{width:size.x,height:size.y,length:size.z},four_named_hubs:true,independent_paint:true,browser_webgl_tested:false,physical_ipad_tested:false,scope:'Actual GLB parsed by the preview loader in Node; no claim that the interactive page was browser-rendered.'};
writeFileSync(new URL('./build/preview-loader.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
