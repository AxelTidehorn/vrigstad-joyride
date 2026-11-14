// Parse an authored GLB with the preview's actual pinned loader. No GPU/FPS claim.
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const [file,report]=process.argv.slice(2);
if(!file||!report)throw new Error('Usage: node check_preview_glb.mjs MODEL.glb REPORT.json');
// Node has no browser image decoder. Expose PNG dimensions to the real loader;
// actual image decoding is separately checked with Pillow and Blender reimport.
const bitmapHeader=async blob=>{
 const b=Buffer.from(await blob.arrayBuffer());
 if(b.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')throw new Error('Expected embedded PNG');
 return {width:b.readUInt32BE(16),height:b.readUInt32BE(20),close(){}};
};
const context=vm.createContext({console,TextDecoder,TextEncoder,URL,Blob,fetch,setTimeout,clearTimeout,self:{URL},navigator:{userAgent:"Node CPU structural check"},createImageBitmap:bitmapHeader});
for(const name of ['three-r128.min.js','GLTFLoader-r128.js'])vm.runInContext(fs.readFileSync(path.join(root,'media/vehicles/vendor',name),'utf8'),context);
const bytes=fs.readFileSync(file),THREE=context.THREE;
const gltf=await new Promise((resolve,reject)=>new THREE.GLTFLoader().parse(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'',resolve,reject));
let meshes=0,triangles=0;
gltf.scene.traverse(o=>{if(o.isMesh){meshes++;triangles+=(o.geometry.index?.count??o.geometry.attributes.position.count)/3;}});
for(const name of ['body','wheel_fl','wheel_fr','wheel_rl','wheel_rr'])if(!gltf.scene.getObjectByName(name))throw new Error('Missing '+name);
const size=new THREE.Box3().setFromObject(gltf.scene).getSize(new THREE.Vector3());
const result={ok:true,loader:'existing Three r128 GLTFLoader',meshes,triangles,dimensions_glb_xyz_m:size.toArray(),browser_gpu_or_safari_tested:false,texture_check:"PNG dimensions supplied for CPU scene parsing only; no GPU upload/decoding claim"};
fs.writeFileSync(report,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
