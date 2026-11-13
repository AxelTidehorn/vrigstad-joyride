import assert from 'node:assert/strict';
import {daylightState} from '../src/visual/daylight.mjs';
const noon=daylightState(13),evening=daylightState(19),
  dusk=daylightState(20.5),night=daylightState(22);
assert.ok(noon.altitude>.8);
assert.ok(noon.strength>evening.strength);
assert.ok(noon.exposure<1.05,'noon exposure bounded');
assert.ok(noon.strength<1.15,'noon direct sun bounded');
assert.ok(evening.skyBrightness<noon.skyBrightness);
assert.ok(dusk.skyBrightness>.19,'twilight does not collapse to black');
assert.ok(dusk.exposure>.59,'twilight world exposure stays usable');
assert.ok(dusk.twilight>.2,'residual sky illumination at dusk');
assert.equal(night.strength,0,'night has no sunlight');
assert.ok(night.skyBrightness<dusk.skyBrightness,'night remains darker');
assert.ok(daylightState(13,0).strength<daylightState(13,100).strength || 
  daylightState(13,0).strength>daylightState(13,100).strength,'cloud variation affects direct light');
for(let h=0;h<24;h+=.5){
  const s=daylightState(h,h*10);
  for(const k of ['dx','dy','dz','cover','shade','strength','exposure','skyBrightness','twilight'])
    assert.ok(Number.isFinite(s[k]),k+' finite');
}
console.log('balanced daylight checks passed');
