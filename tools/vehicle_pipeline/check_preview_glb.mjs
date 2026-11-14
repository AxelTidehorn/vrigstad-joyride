// Parse an authored GLB with the preview's actual pinned loader. No GPU/FPS claim.
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const [file,report]=process.argv.slice(2);
if(!file||!report)throw new Error('Usage: node check_preview_glb.mjs MODEL.glb REPORT.json');
const context=vm.createContext({console,TextDecoder,TextEncoder,URL,Blob,setTimeout,clearTimeout});
for(const name of ['three-r128.min.js','GLTFLoader-r128.js'])vm.runInContext(fs.readFileSync(path.join(root,'media/vehicles/vendor',name),'utf8'),context);
const bytes=fs.readFileSync(file),THREE=context.THREE;
const gltf=await new Promise((resolve,reject)=>new THREE.GLTFLoader().parse(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'',resolve,reject));
let meshes=0,triangles=0;
gltf.scene.traverse(o=>{if(o.isMesh){meshes++;triangles+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3;}});
for(const name of ['body','wheel_fl','wheel_fr','wheel_rl','wheel_rr'])if(!gltf.scene.getObjectByName(name))throw new Error('Missing '+name);
const size=new THREE.Box3().setFromObject(gltf.scene).getSize(new THREE.Vector3());
const result={ok:true,loader:'existing Three r128 GLTFLoader',meshes,triangles,dimensions_glb_xyz_m:size.toArray(),browser_gpu_or_safari_tested:false};
fs.writeFileSync(report,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
