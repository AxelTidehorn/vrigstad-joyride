// Pure geometry sanity checks; no browser required.
import assert from 'node:assert/strict';
import {estimateResidentialPlots} from '../src/environment/residential-neighborhood.mjs';
const homes=[{bi:0,x:0,z:0,area:100},{bi:1,x:20,z:0,area:100},
             {bi:2,x:0,z:25,area:100}];
const road=[{c:1,p:[[-40,-15],[40,-15]]}];
const run=()=>estimateResidentialPlots(homes,[],road,{1:6});
const lots=run();
assert.equal(lots.size,3);
assert.deepEqual(Array.from(lots.entries()),Array.from(run().entries()),'deterministic');
const a=lots.get(0);
assert.ok(a.some(p=>Math.abs(p.x-10)<.01),'bisector halfway to next house');
assert.ok(a.every(p=>p.z>=-10.81),'road verge clips lot');
assert.ok(a.some(p=>Math.abs(p.z-12.5)<.01),'bisector to rear neighbour');
assert.ok(a.every(p=>Number.isFinite(p.x)&&Number.isFinite(p.z)));
console.log('residential plot cell checks passed');
