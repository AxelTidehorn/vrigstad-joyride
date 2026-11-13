import assert from 'node:assert/strict';
import {daylightState} from '../src/visual/daylight.mjs';
const noon=daylightState(13,0),sunset=daylightState(20,0),night=daylightState(1,0);
assert.ok(noon.altitude>sunset.altitude);
assert.ok(noon.strength>sunset.strength);
assert.ok(night.strength<.05);
assert.ok(sunset.warm>noon.warm);
assert.deepEqual(daylightState(13,0),daylightState(13,0));
for(let h=0;h<24;h+=.5){
  const s=daylightState(h,h*10);
  for(const k of ['dx','dy','dz','cover','strength','exposure'])assert.ok(Number.isFinite(s[k]));
}
console.log('daylight-state geometry checks passed');
