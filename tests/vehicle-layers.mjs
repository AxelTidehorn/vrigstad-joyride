import assert from 'node:assert/strict';
import {buildVehicleGeometryData,buildVehicleLayerData,VEHICLES} from '../src/vehicles/vehicle-library.mjs';

// Every layer must be a complete set of triangle attributes, and separating
// the Volvo must not lose any of the original combined geometry.
for(const id of Object.keys(VEHICLES)){
  const combined=buildVehicleGeometryData(id);
  const layers=buildVehicleLayerData(id);
  const expected=id==='volvo240'?['body','glazing','trim','lighting','wheels']:['body'];
  for(const name of expected)assert.ok(layers[name]?.positions.length>0,id+': missing '+name);
  let positions=0;
  for(const [name,part] of Object.entries(layers)){
    assert.equal(part.positions.length,part.normals.length,id+': '+name+' normal count');
    assert.equal(part.positions.length,part.colors.length,id+': '+name+' color count');
    assert.equal(part.positions.length%9,0,id+': '+name+' triangle alignment');
    assert.ok(part.positions.every(Number.isFinite),id+': '+name+' invalid coordinates');
    positions+=part.positions.length;
  }
  assert.equal(positions,combined.positions.length,id+': dropped vertices');
}
console.log('Vehicle geometry layers: OK');
