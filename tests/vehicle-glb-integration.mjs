import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { VEHICLE_ASSETS } from '../src/vehicles/vehicle-assets.mjs';

// Structural guardrails, not exact mesh counts: Round 2 batches details into
// fewer primitives while preserving geometry, materials and wheel rigs.
const expected = {
  volvo: { wheelbase: 2.65, minMeshes: 20 },
  saab: { wheelbase: 2.517, minMeshes: 35 },
  xc70: { wheelbase: 2.763, minMeshes: 50 },
  polis: { wheelbase: 2.763, minMeshes: 60 }
};
const wheelNames = ['wheel_fl','wheel_fr','wheel_rl','wheel_rr'];
for (const [id,spec] of Object.entries(expected)) {
  const info=VEHICLE_ASSETS[id];
  assert.ok(info,'missing vehicle asset manifest entry: '+id);
  const path=fileURLToPath(new URL('../'+info.url,import.meta.url));
  const glb=readFileSync(path);
  assert.equal(glb.toString('utf8',0,4),'glTF',id+' invalid GLB magic');
  assert.equal(glb.readUInt32LE(4),2,id+' must be GLB v2');
  assert.equal(glb.readUInt32LE(8),glb.byteLength,id+' invalid GLB byte length');
  const jsonLength=glb.readUInt32LE(12);
  assert.equal(glb.toString('utf8',16,20),'JSON',id+' missing JSON chunk');
  const gltf=JSON.parse(glb.toString('utf8',20,20+jsonLength).trim());
  assert.ok(gltf.meshes.length>=spec.minMeshes,id+' incomplete GLB meshes');
  const nodes=new Map(gltf.nodes.map(node=>[node.name,node]));
  for(const name of wheelNames) assert.ok(nodes.has(name),id+' missing '+name);
  const wheelZ=name=>nodes.get(name).translation[2];
  const baseline=(wheelZ('wheel_rl')+wheelZ('wheel_rr')-wheelZ('wheel_fl')-wheelZ('wheel_fr'))/2;
  assert.ok(Math.abs(baseline-spec.wheelbase)<.02,id+' incorrect wheelbase: '+baseline);
  assert.ok(nodes.has('body'),id+' missing primary body node');
  if(id==='polis'){
    assert.ok([...nodes.keys()].some(name=>/^lamp_blue_module/.test(name)),
      'police lightbar must expose separately named blue modules');
  }
  console.log('validated GLB:',id,glb.byteLength+' bytes',gltf.meshes.length+' meshes');
}
console.log('Vehicle GLB integration checks passed.');
