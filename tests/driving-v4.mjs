import assert from 'node:assert/strict';
import {createBodyMotion,stepBodyMotion} from '../src/physics/body-motion.mjs';
import {AUTO_SPECS, VEHICLE_PRESETS, newCar, stepCar} from '../src/physics/driving-v4.mjs';

const dt=1/120;
function simulate(type,seconds,input,settings={}){
  const c=newCar(type);
  for(let i=0;i<Math.round(seconds/dt);i++){
    stepCar(c,typeof input==='function'?input(i*dt,c):input,dt,
      {feel:'balanced',powertrain:'v4',surface:'asphalt',...settings});
    assert.ok([c.x,c.z,c.h,c.u,c.v,c.r,c.rpm].every(Number.isFinite),type+' finite state');
  }
  return c;
}
for(const type of Object.keys(VEHICLE_PRESETS)){
  assert.ok(AUTO_SPECS[type],'automatic gearbox missing for '+type);
  const car=simulate(type,16,{throttle:1});
  assert.ok(car.u>12,type+' accelerates');
  assert.ok(car.gear>1,type+' automatic upshifts');
  assert.ok(car.shiftCount>0,type+' records shifts');
  assert.ok(car.rpm>=AUTO_SPECS[type].idle,type+' engine idles');
  const backwards=simulate(type,4,{throttle:-1});
  assert.ok(backwards.u<-.5 && backwards.range==='R',type+' selects reverse automatically');
  const stopped=simulate(type,4,{steer:1});
  assert.ok(stopped.distance<.001,type+' cannot steer-drive at rest');
  const sliding=simulate(type,8,t=>({throttle:1,steer:t>2?.5:0}),{surface:'gravel'});
  assert.ok(sliding.distance>10 && Number.isFinite(sliding.slip),type+' corner finite');
}
const limited=simulate('rwd',16,{throttle:1},{speedLimit:8.33,hardCap:8.33,powerScale:.6});
assert.ok(limited.u<=8.33001,'EPA speed cap respected');
const capped=simulate('awd',16,{throttle:1},{speedLimit:2.5,hardCap:2.5});
assert.ok(capped.u<=2.50001,'water speed cap respected');
const direct=simulate('rwd',8,{throttle:1},{powertrain:'v3'});
assert.equal(direct.gearLabel,'–','V3 direct drive remains an A/B option');

for(const [type,power] of [['rwd',.63],['fwd',.765]]){
  const car=simulate(type,45,{throttle:1},{powerScale:power});
  assert.ok(car.gear>=4,type+' must reach overdrive using in-game power scaling: got '+car.gear);
}
const motion=createBodyMotion();
for(let i=0;i<240;i++)stepBodyMotion(motion,{lateralAcceleration:7.5,forwardAcceleration:3.5,speed:18,distance:i*.15},dt);
assert.ok(motion.roll>.04&&motion.roll<.12,'body banks smoothly under cornering');
assert.ok(motion.pitch>.01&&motion.pitch<.08,'body pitches up while accelerating');
for(let i=0;i<600;i++)stepBodyMotion(motion,{speed:0},dt);
assert.ok(Math.abs(motion.roll)<.005&&Math.abs(motion.pitch)<.005,'body settles after inputs stop');
assert.ok(Math.abs(motion.heave)<.01,'heave settles after terrain');
// At the same entry speed, momentary roadside excursions must not kill speed.
const road=newCar('rwd'),verge=newCar('rwd');
for(const c of [road,verge])c.u=23;
for(let i=0;i<120;i++){
  stepCar(road,{throttle:.3},dt,{feel:'balanced',powertrain:'v4',surface:'asphalt',powerScale:1.2,hardCap:38,grassFraction:0});
  stepCar(verge,{throttle:.3},dt,{feel:'balanced',powertrain:'v4',surface:'asphalt',powerScale:1.2,hardCap:38,grassFraction:.25});
}
assert.ok(road.u-verge.u<1.8,'one wheel on grass should not produce a dramatic speed penalty');
const allGrass=newCar('rwd');allGrass.u=23;
for(let i=0;i<120;i++)stepCar(allGrass,{throttle:.3},dt,{feel:'balanced',powertrain:'v4',surface:'asphalt',powerScale:1.2,hardCap:38,grassFraction:1});
assert.ok(allGrass.u>18,'grass should not instantly erase momentum');
const launch=newCar('rwd');
let zeroToHundred=null;
for(let i=0;i<Math.round(25/dt);i++){
  stepCar(launch,{throttle:1},dt,{feel:'balanced',powertrain:'v4',surface:'asphalt',
    powerScale:1.26,hardCap:38});
  if(zeroToHundred===null&&launch.u*3.6>=100)zeroToHundred=(i+1)*dt;
}
console.log('Volvo 0–100:',zeroToHundred===null?'not reached':zeroToHundred.toFixed(2)+' s',
            '25s gear',launch.gear);
assert.ok(zeroToHundred!==null&&zeroToHundred<17.5,
  'Volvo 0–100 should be playable and measurable, without instant max speed');
console.log('Driving V4: automatic gearboxes, launch, partial grass and speed continuity passed.');
