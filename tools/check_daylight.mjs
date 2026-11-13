import assert from 'node:assert/strict';
import {daylightState} from '../src/visual/daylight.mjs';
const a=daylightState(13),b=daylightState(19),c=daylightState(20.5),n=daylightState(1);
assert.ok(a.altitude>.85 && b.altitude<.26);
assert.ok(a.strength>b.strength*1.9);
assert.ok(b.warm>.65);
assert.ok(a.exposure>b.exposure+.25);
assert.ok(a.skyBrightness>b.skyBrightness+.30);
assert.ok(b.skyBrightness>c.skyBrightness+.2);
assert.ok(c.skyBrightness>n.skyBrightness);
assert.equal(n.strength,0);
for(let h=0;h<24;h+=.5){
  const s=daylightState(h,h*10);
  for(const k of ['dx','dy','dz','cover','strength','exposure','skyBrightness','altitude'])assert.ok(Number.isFinite(s[k]));
}
console.log('daylight contrast checks passed');
