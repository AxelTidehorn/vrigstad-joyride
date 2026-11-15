import assert from 'node:assert/strict';
import {streetlightLevel,placeStreetlights} from '../src/game/render/street-lighting.ts';
import {daylightState} from '../src/game/render/solar-clock.ts';
assert.equal(streetlightLevel(2),0,'lights off above horizon');
assert.equal(streetlightLevel(-7),1,'lights on below civil twilight');
assert.ok(Math.abs(streetlightLevel(-3)-.5)<.0001,'smooth twilight transition');
const roads=[{c:0,p:[[0,0],[200,0]]}],h=()=>0;
const a=placeStreetlights(roads,[8],h,()=>false,()=>false,1100);
assert.ok(a.length>=3);assert.deepEqual(a,placeStreetlights(roads,[8],h,()=>false,()=>false,1100));
for(const p of a)assert.ok(Math.abs(p[1])>5);
assert.deepEqual(placeStreetlights(roads,[8],h,()=>true,()=>false,1100),[]);
assert.deepEqual(placeStreetlights(roads,[8],x=>x*2,()=>false,()=>false,1100),[]);
for(const time of [13,17,19,20.5,22]){
 const clear=daylightState(time,0),cloud=daylightState(time,1);
 assert.ok(cloud.strength<=clear.strength);assert.ok(clear.exposure<1.1);
}
console.log('Lighting schedule, placement, slope, cloud and exposure checks passed');
const {createLampPool}=await import('../src/game/render/street-lighting.ts');
const pool=createLampPool([[0,0],[40,0],[80,0]],2);
for(let i=0;i<60;i++)pool.update(1/60,0,0);
assert.deepEqual([...pool.indices],[0,1]);
// Moving the priority boundary a little retains stable slots.
for(let i=0;i<60;i++)pool.update(1/60,42,0);
assert.deepEqual([...pool.indices],[0,1]);
let moved=false, previous=[...pool.weights], old=[...pool.indices];
for(let i=0;i<100;i++){
 pool.update(1/60,70,0);
 for(let k=0;k<2;k++){
   if(pool.indices[k]!==old[k]) {assert.ok(previous[k]<=1/21+.0001,'relocate only after fade out');moved=true;}
   assert.ok(pool.weights[k]>=0&&pool.weights[k]<=1);
 }
 old=[...pool.indices];previous=[...pool.weights];
}
assert.ok(moved);assert.ok(pool.indices.includes(2));assert.ok(!pool.indices.includes(0));
console.log('Stable pool, hysteresis and zero-weight reassignment checks passed');
