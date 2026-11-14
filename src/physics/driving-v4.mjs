/**
 * Driving Physics Lab V4 integrated source. Pure vehicle dynamics; no THREE or DOM.
 * Heading 0 faces -Z. All gearbox selections are automatic.
 * FWD/RWD/AWD are gameplay archetypes, not calibrated vehicle specifications.
 */
// Vrigstad Joyride — drive feel A/B experiment. Baseline is exact V2 when feel='v2'.
// Local body axes: +u forward, +v to driver's right; yaw positive turns right.
// Heading 0 faces world -Z. No rendering / THREE / asset dependencies.
export const VEHICLE_PRESETS = Object.freeze({
  fwd: { name: 'FWD · Saab', drive: 'fwd', mass: 1350, wheelbase: 2.60, width: 1.72, maxSpeed: 40, acceleration: 4.5, grip: 1.0, yawInertia: 1.04 },
  rwd: { name: 'RWD · Volvo', drive: 'rwd', mass: 1430, wheelbase: 2.65, width: 1.73, maxSpeed: 38, acceleration: 4.7, grip: 1.0, yawInertia: 1.02 },
  awd: { name: 'AWD · Polis', drive: 'awd', mass: 1570, wheelbase: 2.68, width: 1.78, maxSpeed: 42, acceleration: 5.1, grip: 1.10, yawInertia: 1.10 },
});
export const SURFACES = Object.freeze({
  asphalt: { name: 'Asfalt', mu: 1.05, lateral: 1.05, rolling: .020 },
  gravel:  { name: 'Grus', mu: .70, lateral: .61, rolling: .035 },
  grass:   { name: 'Gräs', mu: .46, lateral: .35, rolling: .060 },
});
// The game keeps an automatic gearbox. These are reference *variants*, not
// implied specifications for every engine/trim sharing the same body shell.
// Volvo: https://www.encycarpedia.com/se/volvo/86-240-gl-sedan
// Saab 900: Saab-Scania 1988 technical brochure, Turbo 16S, 8.7s
// Saab 9-5: https://www.auto-data.net/se/saab-9-5-sport-combi-facelift-2001-generation-7158
export const VEHICLE_VARIANTS = Object.freeze({
  volvo: {label:'Volvo 240 GL 2.3 (1986–93)',type:'rwd',mass:1310,target0to100:11.6,power:1.6371},
  saab: {label:'Saab 900 Turbo 16S (1988)',type:'fwd',mass:1290,target0to100:8.7,power:2.1374},
  saab95Estate: {label:'Saab 9-5 SportCombi 2.3t 185 hp (2003)',type:'fwd',mass:1680,target0to100:8.8,power:2.7337},
});
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));

// V4: lightweight automatic powertrains. All vehicles use an automatic box; no manual gears.
// Engine curves, torque converter and gear selection are game-feel approximations,
// not measured dynamometer data for particular production years/engines.
export const AUTO_SPECS = Object.freeze({
  rwd: { label:'Volvo · lågvarvig', idle:780, redline:5400, torque:232, peak:2600,
         ratios:[2.45,1.45,1.00,.70], final:3.73, radius:.320, efficiency:.85, response:.19, brake:.70, shift:.33 },
  fwd: { label:'Saab · varvvillig', idle:850, redline:6200, torque:225, peak:3850,
         ratios:[2.85,1.72,1.12,.78], final:3.75, radius:.315, efficiency:.86, response:.13, brake:.55, shift:.27 },
  awd: { label:'Polis · snabb automat', idle:860, redline:6400, torque:290, peak:4000,
         ratios:[3.30,1.96,1.39,.98,.74], final:3.52, radius:.325, efficiency:.84, response:.12, brake:.63, shift:.25 },
});
const mix=(a,b,t)=>a+(b-a)*t;
function torqueFraction(rpm,p){
  // Flat, broad torque plateau below peak, gentle fade at higher revs.
  const n=clamp(rpm/p.peak,0,2.3);
  return n<=1 ? mix(.70,1,Math.pow(n,.75)) : clamp(1-.30*Math.pow(n-1,1.28),.53,1);
}
function automaticForce(c,rawPedal,dt,spec){
  const p=AUTO_SPECS[c.type], speed=c.u;
  // The backward key acts as progressive braking until nearly stopped,
  // then selects R automatically. W does the equivalent from reverse.
  if(rawPedal<-.06 && speed<.43)c.range='R';
  else if(rawPedal>.06 && speed>-.43)c.range='D';
  const wantsForward=c.range==='D',switchingAgainstMotion=(wantsForward&&((rawPedal<-.06&&speed>.43)||(speed<-.5&&rawPedal>.06)))||(!wantsForward&&((rawPedal>.06&&speed<-.43)||(speed>.5&&rawPedal<-.06)));
  c.shiftLock=Math.max(0,c.shiftLock-dt);
  c.shiftTime=Math.max(0,c.shiftTime-dt);
  const travel=Math.abs(speed),gearIndex=wantsForward?Math.max(0,c.gear-1):0;
  const ratio=p.ratios[gearIndex];
  const wheelRpm=travel/(2*Math.PI*p.radius)*60;
  const coupled=wheelRpm*ratio*p.final;
  const request=(wantsForward?Math.max(0,rawPedal):Math.max(0,-rawPedal));
  const converterSlip=(1-clamp(travel/9,0,1))*(220+530*request);
  const targetRpm=clamp(Math.max(p.idle,coupled+converterSlip),p.idle,p.redline);
  c.rpm+= (targetRpm-c.rpm)*(1-Math.exp(-dt/.105));
  if(wantsForward && c.shiftLock<=0 && !switchingAgainstMotion){
    // High throttle holds a gear longer. Low throttle cruises early.
    // Choose reachable road-speed shift points, with generous hysteresis.
    // The former 5050 RPM WOT target kept the Volvo in 2/3 and Saab in 3.
    const shiftUp=1750+650*request;
    const shiftDown=900+400*request;
    let next=c.gear;
    if(c.gear<p.ratios.length && coupled>shiftUp)next=c.gear+1;
    else if(c.gear>1 && coupled<shiftDown)next=c.gear-1;
    // Kickdown: allow one lower gear when demand is high, if safe.
    else if(request>.84 && c.gear>1 && coupled<p.peak*.65 && wheelRpm*p.ratios[c.gear-2]*p.final<shiftUp*.85)
      next=c.gear-1;
    if(next!==c.gear){c.gear=next;c.shiftTime=p.shift;c.shiftLock=.72;c.shiftCount++;}
  }
  const driveInput=clamp(request,0,1);
  // RPM is calculated from actual vehicle speed after a converter slip allowance.
  const wheelTorque=p.torque*torqueFraction(c.rpm,p)*p.ratios[Math.max(0,c.gear-1)]*p.final*p.efficiency;
  const converterBoost=mix(1.20,1,clamp(travel/8,0,1));
  // Stronger response up to ordinary road speeds; preserve the existing
  // top-speed taper instead of making cars sit on the hard speed limiter.
  const midrangeBoost=1+.48*(1-clamp((travel-16)/18,0,1));
  let wheelForce=wheelTorque/p.radius*converterBoost*driveInput*midrangeBoost*clamp(1-.16*travel/25,.74,1);
  // Brief, visible but not violent power interruption during an automatic shift.
  if(c.shiftTime>0)wheelForce*=.33;
  // A gentle soft limiter, not an instantaneous velocity jump.
  if(travel>spec.maxSpeed*.88)wheelForce*=clamp((spec.maxSpeed*1.09-travel)/(spec.maxSpeed*.21),0,1);
  let engineForce=0;
  if(switchingAgainstMotion){
    // W/S first slows the car, then automatically picks D/R at low speed.
    engineForce=-Math.sign(speed)*spec.mass*5.6*Math.abs(rawPedal);
  }else if(driveInput>.01){
    engineForce=(wantsForward?1:-1)*wheelForce*(wantsForward?1:.66);
  }else if(Math.abs(speed)>.4){
    // Engine braking decelerates the car, varies by engine/ratio/RPM.
    const fraction=clamp((c.rpm-p.idle)/(p.redline-p.idle),0,1);
    engineForce=-Math.sign(speed)*spec.mass*p.brake*(.45+.95*fraction);
  }
  c.engineLoad=clamp(driveInput,0,1);
  c.gearLabel=c.range==='R'?'R':String(c.gear);
  return engineForce;
}

export function newCar(type='rwd',x=0,z=0,h=0,vehicleId=null){
  if(!VEHICLE_PRESETS[type]) throw Error('Unknown vehicle '+type);
  return { type, vehicleId, x,z,h, u:0,v:0,r:0, steer:0, slip:0, speed:0, slipFront:0, slipRear:0, gripFront:0, gripRear:0, surface:'asphalt', distance:0, smoothedThrottle:0, slideResponse:0, range:'D', gear:1, gearLabel:'1', rpm:AUTO_SPECS[type].idle, engineLoad:0, shiftTime:0, shiftLock:0, shiftCount:0 };
}
export function stepCar(c,input={},dt=1/120,settings={}){
  if(!(dt>0&&dt<=.05)) throw Error('stepCar expects dt in (0, .05]');
  const preset=VEHICLE_PRESETS[c.type],variant=VEHICLE_VARIANTS[c.vehicleId],
        base=variant?{...preset,mass:variant.mass}:preset,
        spec=settings.speedLimit?{...base,maxSpeed:Math.min(base.maxSpeed,settings.speedLimit)}:base,
        surface=SURFACES[settings.surface||c.surface]||SURFACES.asphalt;
  const balanced=settings.feel==='balanced';
  const m=spec.mass,g=9.81,L=spec.wheelbase,lf=L*.47,lr=L*.53;
  const inertia=(m*L*L*.34)*spec.yawInertia;
  const steerIn=clamp(input.steer||0,-1,1),pedal=clamp(input.throttle||0,-1,1);
  c.smoothedThrottle=balanced ? c.smoothedThrottle+(pedal-c.smoothedThrottle)*(1-Math.exp(-dt/(Math.abs(pedal)>Math.abs(c.smoothedThrottle)?.20:.12))) : pedal;
  const throttle=c.smoothedThrottle;
  const brake=clamp(input.brake||0,0,1),handbrake=clamp(input.handbrake||0,0,1);
  const steerMax=.49/(1+Math.abs(c.u)/12);
  const targetSteer=steerIn*steerMax;
  c.steer+=clamp(targetSteer-c.steer,-(balanced?1.55:3.0)*dt,(balanced?1.55:3.0)*dt);
  const steer=c.steer;
  // Grass is sampled at the wheels by the game, not by the car center.
  // Grass changes traction immediately but does not act like a speed limiter.
  const grass=clamp(settings.grassFraction??(settings.surface==='grass'?1:0),0,1);
  const mu=(surface.mu*(1-grass)+SURFACES.grass.mu*grass)*spec.grip;
  const lateralMu=(surface.lateral*(1-grass)+SURFACES.grass.lateral*grass)*spec.grip;
  const normalFront=m*g*(lr/L),normalRear=m*g*(lf/L);
  const forwardV=c.u;
  let engine;
  if(settings.powertrain==='v3'){
    // Exact V3 traction input for an honest A/B comparison.
    engine=m*spec.acceleration*throttle;
    if(throttle>0) engine*=clamp(1-Math.max(0,forwardV)/spec.maxSpeed*.68,.19,1);
    if(throttle<0&&forwardV>1.0) engine*=1.15;
    if(throttle>0&&forwardV<-.5) engine*=1.15;
    c.gearLabel='–';c.rpm=0;c.shiftCount=0;
  }else{
    // The same already-smoothed throttle as V3: chassis behavior is unchanged.
    engine=automaticForce(c,throttle,dt,spec);
  }
  engine *= clamp((settings.powerScale??1)*(variant?.power??1),0.20,3.5);
  let frontDrive=spec.drive==='fwd'?.96:spec.drive==='awd'?.48:0;
  let rearDrive=1-frontDrive;
  let fxF=engine*frontDrive,fxR=engine*rearDrive;
  if(brake){
    let sign=Math.sign(forwardV);if(Math.abs(forwardV)<.25)sign=Math.sign(throttle)||0;
    fxF-=sign*m*12.0*.63*brake;
    fxR-=sign*m*12.0*.37*brake;
  }
  if(handbrake){
    const sign=Math.sign(forwardV)||1;
    fxR-=sign*m*7.0*handbrake;
  }
  // Lateral tire forces from slip angles. Smooth near zero to avoid division blow-up.
  const denom=Math.max(Math.abs(forwardV),2.5);
  const alphaF=Math.atan2(c.v+lf*c.r,denom)-steer;
  const alphaR=Math.atan2(c.v-lr*c.r,denom);
  const moving=clamp(Math.abs(c.u)/1.8,0,1);
  let fyF=-normalFront*9.0*alphaF*moving,fyR=-normalRear*10.5*alphaR*moving;
  // Mild arcade power-oversteer: driven rear tires give up lateral grip sooner.
  const powerSlide=clamp((Math.abs(c.u)-4)/8,0,1)*clamp((Math.abs(steer)-.055)/.18,0,1)*clamp(throttle,0,1);
  c.slideResponse=balanced ? c.slideResponse+(powerSlide-c.slideResponse)*(1-Math.exp(-dt/(powerSlide>c.slideResponse?.22:.18))) : powerSlide;
  const rearSlide=spec.drive==='rwd'?((balanced?.38:.43)*c.slideResponse):spec.drive==='awd'?(.15*c.slideResponse):0;
  // Friction-circle limit: accelerating through the driven tires takes away cornering grip.
  function axle(x,y,normal,hand=0){
    const mx=normal*mu, my=normal*lateralMu;
    const clampedX=clamp(x,-mx*.78,mx*.78);
    const available=my*Math.sqrt(Math.max(0,1-(clampedX/mx)**2));
    const lateralLimit=available*(1-.72*hand)*(1-(normal===normalRear?rearSlide:0));
    return [clampedX,clamp(y,-lateralLimit,lateralLimit),lateralLimit];
  }
  let f=axle(fxF,fyF,normalFront),r=axle(fxR,fyR,normalRear,handbrake);
  fxF=f[0];fyF=f[1];fxR=r[0];fyR=r[1];
  // Resolved front-wheel force in the car's body coordinates.
  const Fx=fxR+fxF*Math.cos(steer)-fyF*Math.sin(steer);
  const Fy=fyR+fxF*Math.sin(steer)+fyF*Math.cos(steer);
  // Rolling drag increases gradually when the whole car is off the road.
  // A clipped corner (one wheel in grass) must not erase momentum.
  const rolling=(surface.rolling*(1-grass)+.032*grass)*g;
  // Drag is gentle at city speed and grows with speed. Keep the V3 A/B baseline untouched.
  const aero=settings.powertrain==='v3'?.0036:.0006;
  const resistance=rolling*Math.tanh(forwardV*3)+aero*forwardV*Math.abs(forwardV);
  let udot=Fx/m+c.v*c.r-resistance;
  let vdot=Fy/m-c.u*c.r;
  let rdot=(lf*(fxF*Math.sin(steer)+fyF*Math.cos(steer))-lr*fyR)/inertia;
  // Arcade yaw stabiliser: limit unrecoverable spins while preserving slip.
  const steerYaw=(Math.abs(c.u)>0.25?c.u/L*Math.tan(steer):0);
  const slipMagnitude=Math.abs(Math.atan2(c.v,Math.max(4,Math.abs(c.u))));
  // Avoid the stabiliser snapping an established slide straight against the
  // player's countersteer. A weaker stabiliser remains to prevent endless spins.
  const driftBlend=clamp((slipMagnitude-.065)/.19,0,1)*clamp((Math.abs(c.u)-5)/9,0,1);
  const baseYawAssist=spec.drive==='rwd'?(balanced?1.6:1.5):spec.drive==='fwd'?1.8:2.3;
  const yawAssist=baseYawAssist*(1-.68*driftBlend);
  // The yaw target is also bounded by the tire/road lateral grip budget.
  const allowedYaw=lateralMu*g/Math.max(4,Math.abs(c.u));
  const targetYaw=clamp(steerYaw,-allowedYaw,allowedYaw);
  rdot+=(targetYaw-c.r)*yawAssist;
  if(Math.abs(c.u)<1&&Math.abs(c.v)<.5){vdot-=c.v*4;rdot-=c.r*5}
  const prevU=c.u;
  c.u=clamp(c.u+udot*dt,-8,settings.hardCap??spec.maxSpeed*1.17);
  if(!throttle&&!brake&&!handbrake&&prevU*c.u<0)c.u=0;
  c.v+=vdot*dt;
  c.r=clamp(c.r+rdot*dt,-1.65,1.65);
  // Suppress unrealistically endless pirouettes; lower factor at speed.
  c.r*=Math.exp(-dt*(.32+.15*Math.abs(c.u)/20));
  c.v*=Math.exp(-dt*(balanced?.48:.40)*(1-.45*driftBlend));
  c.h+=c.r*dt;
  if(c.h>Math.PI)c.h-=2*Math.PI;if(c.h< -Math.PI)c.h+=2*Math.PI;
  const wx=Math.sin(c.h)*c.u+Math.cos(c.h)*c.v;
  const wz=-Math.cos(c.h)*c.u+Math.sin(c.h)*c.v;
  c.x+=wx*dt;c.z+=wz*dt;
  c.distance+=Math.hypot(wx,wz)*dt;
  c.speed=Math.hypot(c.u,c.v);
  c.slip=Math.abs(c.u)<.5?0:Math.atan2(c.v,Math.abs(c.u));
  c.slipFront=alphaF;c.slipRear=alphaR;
  c.gripFront=f[2];c.gripRear=r[2];
  c.surface=grass>.5?'grass':settings.surface||c.surface;
  if(![c.u,c.v,c.r,c.h,c.x,c.z,c.rpm].every(Number.isFinite))throw Error('Non-finite car state');
  return c;
}

