// Run with: node tools/check_house_catalog.mjs
// Dependency-free geometry/footprint smoke tests, not a browser-rendering test.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { HOUSE_TYPES, houseSkin, footprintRect, createHouseGeometry } from '../src/houses/house-library.mjs';

class Color {
  constructor(hex) {
    this.r=parseInt(hex.slice(1,3),16)/255;
    this.g=parseInt(hex.slice(3,5),16)/255;
    this.b=parseInt(hex.slice(5,7),16)/255;
  }
}
class Float32BufferAttribute {
  constructor(array,itemSize){this.array=array;this.itemSize=itemSize;}
}
class BufferGeometry {
  constructor(){this.attributes={};}
  setAttribute(key,attribute){this.attributes[key]=attribute;}
  computeVertexNormals(){}
}
const THREE={Color,Float32BufferAttribute,BufferGeometry};

const palettes={
  cottage:['red','yellow','cream'],
  bungalow:['mexi','brick','ochre'],
  villa80:['red','green','cream']
};
let combinations=0;
for(const [type,skins] of Object.entries(palettes)){
  for(const skin of skins)for(const face of ['+x','-x','+z','-z']){
    const mesh=createHouseGeometry(THREE,type,skin,face);
    const points=mesh.attributes.position.array,colors=mesh.attributes.color.array;
    assert.equal(points.length,colors.length);
    assert.equal(points.length%9,0);
    assert(points.length>900);
    assert(points.every(Number.isFinite));
    assert(colors.every(x=>Number.isFinite(x)&&x>=0&&x<=1));
    for(let i=0;i<points.length;i+=9){
      const ux=points[i+3]-points[i],uy=points[i+4]-points[i+1],uz=points[i+5]-points[i+2];
      const vx=points[i+6]-points[i],vy=points[i+7]-points[i+1],vz=points[i+8]-points[i+2];
      const cx=uy*vz-uz*vy,cy=uz*vx-ux*vz,cz=ux*vy-uy*vx;
      assert(cx*cx+cy*cy+cz*cz>1e-10, `Degenerate triangle ${type}/${skin}/${face}`);
    }
    combinations++;
  }
}
function rectangle(length,width,angle){
  const ux=Math.cos(angle),uz=Math.sin(angle),vx=-uz,vz=ux;
  return [[-length/2,-width/2],[length/2,-width/2],[length/2,width/2],[-length/2,width/2]]
    .flatMap(([a,b])=>[a*ux+b*vx+120,a*uz+b*vz-40]);
}
for(const angle of [0,.37,1.13,2.61]){
  const f=footprintRect(rectangle(12,8,angle));
  assert(f&&f.fit>.999999);
  assert(Math.abs(f.length-12)<1e-6);
  assert(Math.abs(f.width-8)<1e-6);
}
assert.equal(houseSkin('cottage','#843b30',0),'red');
assert.equal(houseSkin('bungalow','#843b30',0),'brick');
const data=JSON.parse(readFileSync(new URL('../data/vrigstad.json',import.meta.url),'utf8'));
const types={cottage:0,bungalow:0,villa80:0};
let eligible=0;
data.b.forEach((b,i)=>{
  if(b.k!==0||b.facade==='bespoke'||!b.g)return;
  const f=footprintRect(b.p);
  if(!f||f.area<52||f.area>450||f.fit<.965||f.width<6.5||f.length>18.2)return;
  const options=Object.entries(HOUSE_TYPES).filter(([type,spec])=>{
    const sx=(f.length-.22)/spec.length,sz=(f.width-.22)/spec.width;
    return sx>=.82&&sx<=1.35&&sz>=.81&&sz<=1.34&&Math.abs(sx-sz)<=.19;
  });
  if(!options.length)return;
  eligible++;
  const hash=(Math.imul(Math.round(b.p[0]*10),73856093)^
    Math.imul(Math.round(b.p[1]*10),19349663)^Math.imul(i+1,83492791))>>>0;
  if(hash%5<=1)types[options[Math.floor(hash/5)%options.length][0]]++;
});
assert(eligible>100);
assert(Object.values(types).every(n=>n>4));
console.log('Verified',combinations,'mesh configurations,',eligible,'matching footprints; sampled:',types);
