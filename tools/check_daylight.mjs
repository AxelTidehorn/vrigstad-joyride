import assert from 'node:assert/strict';
import {solarPosition,daylightState,VRIGSTAD} from '../src/visual/daylight.mjs';
const deg=x=>x*180/Math.PI;
const summer=solarPosition(13,'2026-06-21'),winter=solarPosition(12,'2026-12-21');
assert.ok(Math.abs(VRIGSTAD.latitude-57.3555)<.00001);
assert.ok(deg(summer.altitude)>54&&deg(summer.altitude)<58,'summer noon around 56 degrees');
assert.ok(deg(winter.altitude)>8&&deg(winter.altitude)<11,'winter noon around 9 degrees');
assert.ok(summer.dz>0,'noon sun south (+Z)');
assert.ok(solarPosition(8,'2026-08-15').dx>0,'morning sun east (+X)');
assert.ok(solarPosition(19,'2026-08-15').dx<0,'evening sun west (-X)');
assert.ok(solarPosition(13,'2026-06-21').altitude>solarPosition(13,'2026-12-21').altitude);
const midday=daylightState(13),dusk=daylightState(20.5),night=daylightState(23);
assert.ok(midday.strength>dusk.strength);
assert.ok(midday.exposure>dusk.exposure);
assert.ok(midday.skyBrightness>dusk.skyBrightness);
assert.equal(night.strength,0);
for(let h=0;h<24;h+=.5){
  const s=daylightState(h,h*10,.5,'2026-08-15');
  for(const k of ['dx','dy','dz','altitude','azimuth','cover','strength','exposure','skyBrightness','twilight'])
    assert.ok(Number.isFinite(s[k]),k);
}
console.log('Geographic solar checks passed');
