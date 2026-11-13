// node tools/check_residential_neighborhood.mjs
// Deterministic, dependency-free spatial and geometry smoke test.
// This tests path layout and the batched mesh contract, not WebGL appearance.
import assert from 'node:assert/strict';
import {createResidentialNeighborhood} from '../src/environment/residential-neighborhood.mjs';

const children=[];
class Color {
  constructor(c='#ffffff'){this.set(c);}
  set(c){if(typeof c==='number'){this.r=((c>>>16)&255)/255;this.g=((c>>>8)&255)/255;this.b=(c&255)/255;return this;}
    this.r=parseInt(c.slice(1,3),16)/255;this.g=parseInt(c.slice(3,5),16)/255;this.b=parseInt(c.slice(5,7),16)/255;return this;}
  multiplyScalar(x){this.r*=x;this.g*=x;this.b*=x;return this;}
}
class Vector{set(...v){this.val=v;return this;}}
class Object3D{
  constructor(){this.position=new Vector();this.rotation=new Vector();this.scale=new Vector();}
  updateMatrix(){this.matrix={pos:this.position.val.slice(),rot:this.rotation.val.slice(),scale:this.scale.val.slice()};}
}
class BufferGeometry{
  constructor(){this.attributes={};}
  setAttribute(key,val){this.attributes[key]=val;}
  computeVertexNormals(){}
}
class Float32BufferAttribute{constructor(array,itemSize){this.array=array;this.itemSize=itemSize;}}
class Mesh{constructor(geo,mat){this.geometry=geo;this.material=mat;}}
class InstancedMesh extends Mesh{
  constructor(geo,mat,count){super(geo,mat);this.count=count;this.instances=[];this.instanceMatrix={};this.instanceColor={};this.colors=[];}
  setMatrixAt(i,m){this.instances[i]=structuredClone(m);}
  setColorAt(i,c){this.colors[i]=[c.r,c.g,c.b];}
}
class MeshLambertMaterial{constructor(o={}){this.color=o.color;}}
const shape=(kind)=>(class{constructor(){this.kind=kind}});
const THREE={Color,Object3D,BufferGeometry,Float32BufferAttribute,Mesh,InstancedMesh,MeshLambertMaterial,
  BoxGeometry:shape('box'),CylinderGeometry:shape('cylinder'),DodecahedronGeometry:shape('hedge'),
  IcosahedronGeometry:shape('leaf'),ConeGeometry:shape('spruce'),DoubleSide:2};
const buildings=[],sites=[];
for(let i=0;i<48;i++){
  const x=-575+i*25;
  const p=[x-5,9,x+5,9,x+5,17,x-5,17];
  buildings.push({p,k:0});
  sites.push({bi:i,kind:0,area:110,poly:p,x,z:13,
    entryX:x,entryZ:7.6,normalX:0,normalZ:-1,type:'farmhouse'});
}
const inPoly=(p,x,z)=>{let inside=false;for(let i=0,j=p.length-2;i<p.length;j=i,i+=2)
  if((p[i+1]>z)!==(p[j+1]>z)&&x<(p[j]-p[i])*(z-p[i+1])/(p[j+1]-p[i+1])+p[i])inside=!inside;
  return inside;};
const env={sites,buildings,roads:[{c:2,p:[[-700,0],[700,0]]}],roadWidths:[9,7.5,5.5,3.5],
  hAt:()=>0,inPoly,protectedCenters:[]};
const scene={add:(...items)=>children.push(...items)};
const stats=createResidentialNeighborhood(THREE,scene,env);
assert(stats.walks>=15, 'No meaningful road-linked garden walks');
assert(stats.drives>0, 'No test driveways');
assert(stats.trees>0, 'No garden trees');
assert(stats.hedges+stats.walls+stats.fences>0, 'No boundary objects');
assert(children.length<=22, 'Too many draw-call batches');
assert(children.some(x=>x.geometry.attributes?.position), 'Missing unified path mesh');
for(const child of children){
  const positions=child.geometry.attributes?.position?.array||[];
  assert(positions.every(Number.isFinite),'Invalid generated surface vertex');
  if(child instanceof InstancedMesh){
    assert.equal(child.instances.length,child.count);
    assert(child.instances.every(x=>x.pos.every(Number.isFinite)&&x.scale.every(Number.isFinite)));
  }
}
const repeat=[];
const stats2=createResidentialNeighborhood(THREE,{add:(...m)=>repeat.push(...m)},env);
assert.deepEqual(stats,stats2,'Garden placement is not deterministic');
console.log('Residential neighborhood verified',stats,'batches:',children.length);
