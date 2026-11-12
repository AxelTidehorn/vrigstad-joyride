import assert from 'node:assert/strict';
import {VEHICLES,buildVehicleGeometryData,createVehicleGeometry,disposeVehicleGeometries} from '../src/vehicles/vehicle-library.mjs';

class MockGeometry{
  constructor(){this.attributes={};this.disposed=false;}
  setAttribute(name,value){this.attributes[name]=value;}
  computeBoundingSphere(){}
  dispose(){this.disposed=true;}
}
class MockAttribute{constructor(data,size){this.array=data;this.itemSize=size;}}
const THREE={BufferGeometry:MockGeometry,Float32BufferAttribute:MockAttribute};
for(const id of Object.keys(VEHICLES)){
 const raw=buildVehicleGeometryData(id);
 const vertices=raw.positions.length/3;
 assert.ok(vertices>300,id+' missing geometry');
 assert.equal(vertices%3,0,id+' invalid triangle count');
 assert.equal(raw.positions.length,raw.normals.length);
 assert.equal(raw.positions.length,raw.colors.length);
 assert.ok(raw.positions.every(Number.isFinite));
 assert.ok(raw.normals.every(Number.isFinite));
 assert.ok(raw.colors.every(x=>Number.isFinite(x)&&x>=0&&x<=1));
 assert.ok(Math.min(...raw.positions.filter((_,i)=>i%3===1))>-.1,'below ground: '+id);
 const a=createVehicleGeometry(THREE,id),b=createVehicleGeometry(THREE,id);
 assert.equal(a,b,'must share cached geometry');
 assert.ok(a.attributes.position&&a.attributes.normal&&a.attributes.color);
 console.log(id+': '+vertices/3+' triangles OK');
}
assert.notEqual(createVehicleGeometry(THREE,'volvo240',{paint:'#c7bda4'}),
                createVehicleGeometry(THREE,'volvo240',{paint:'#9d3438'}));
assert.throws(()=>buildVehicleGeometryData('unknown'),RangeError);
disposeVehicleGeometries(THREE);
console.log('Geometry sanity checks passed. In-game WebGL visuals still need review.');
