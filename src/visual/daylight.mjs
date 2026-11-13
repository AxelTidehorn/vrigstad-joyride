// Small experimental daylight controller. Pure solar state + renderer adapter.
// Sunrise / sunset approximations are aesthetic, not an astronomical ephemeris.
export function daylightState(hour, cloudTime=0, coverage=null) {
  const h=((hour%24)+24)%24;
  // Deliberately stylized Swedish summer arc, from 05:00 to 21:00.
  const phase=(h-5)/16;
  const raw=Math.sin(Math.PI*phase);
  const altitude=phase>0&&phase<1?Math.pow(Math.max(0,raw),1.6)*.96:-.12;
  const daytime=Math.max(0,Math.min(1,altitude/.22));
  const warm=Math.max(0,Math.min(1,(.62-altitude)/.52));
  const azimuth=Math.PI*(h-5)/16;
  const cloudNoise=.5+.24*Math.sin(cloudTime*.19+1.7)+.14*Math.sin(cloudTime*.43-0.8);
  const cover=coverage===null?Math.max(0,Math.min(.82,cloudNoise)):Math.max(0,Math.min(1,coverage));
  // Broad cloud shadows: coherent across the entire scene; not a weather model.
  // Cloud cover also attenuates direct sun and glare, not just sky colour.
  const shade=Math.max(.30,1-cover*.82);
  // Twilight keeps residual skylight after direct sun fades; actual night
  // still requires headlights and street lamps, not artificial daylight.
  const twilight=Math.max(0,Math.min(1,(h>=12?21.7-h:h-4.3)/2.0));
  return {
    hour:h,altitude,daytime,warm,cover,shade,
    dx:Math.cos(azimuth)*Math.cos(Math.max(-.12,altitude)*1.12),
    dy:Math.max(-.15,altitude),
    dz:Math.sin(azimuth)*Math.cos(Math.max(-.12,altitude)*1.12),
    strength:daytime*(1.44-.48*warm)*shade,
    exposure:.69+.30*daytime-.11*warm+.03*(1-shade),
    skyBrightness:Math.max(.15,(.25+.75*daytime)*(1-.27*warm)),
    twilight
  };
}
export function createDaylightController(THREE, config) {
  const {sun,hemi,renderer,camera,scene,sky,filmFrameMaterial,filmHorizon}=config;
  const params=new URLSearchParams(location.search);
  let enabled=params.get('lighting')!=='off';
  const initialEnabled=enabled;
  const specified=params.get('time');
  const fixedHour=specified!==null&&Number.isFinite(Number(specified))?Number(specified):null;
  let cycle=params.get('cycle')==='on';
  const speed=Number(params.get('daySpeed'));
  const daySpeed=Number.isFinite(speed)&&speed>0?Math.min(5,speed):1;
  let hour=fixedHour===null?15.5:fixedHour;
  const vector=new THREE.Vector3(),sunClip=new THREE.Vector3(),look=new THREE.Vector3(),skyCool=new THREE.Color(0x4c80b2),skyWarm=new THREE.Color(0xc86b73),skyNight=new THREE.Color(0x14243a);
  const ambientCold=new THREE.Color(0xc8d9ed),ambientWarm=new THREE.Color(0xffa776);
  const sunCold=new THREE.Color(0xfff2df),sunWarm=new THREE.Color(0xff8b36);
  const horizonDay=new THREE.Color(0x91b9d4),horizonDusk=new THREE.Color(0xf0a16e),horizonNight=new THREE.Color(0x1d3046);
  let clock=0,adapt=.95,coverage=null,glare=1,occlusion=1;
  const initialHour=hour,initialCycle=cycle;
  function hash(x,z){return ((Math.sin(x*127.1+z*311.7)*43758.5453)%1+1)%1}
  function noise(x,z){const ix=Math.floor(x),iz=Math.floor(z);let a=x-ix,b=z-iz;a=a*a*(3-2*a);b=b*b*(3-2*b);return (hash(ix,iz)*(1-a)+hash(ix+1,iz)*a)*(1-b)+(hash(ix,iz+1)*(1-a)+hash(ix+1,iz+1)*a)*b}
  const smooth=(a,b,x)=>{const t=Math.max(0,Math.min(1,(x-a)/(b-a)));return t*t*(3-2*t)};
  function update(dt) {
    if(!enabled)return;
    clock+=dt;
    if(cycle)hour=(hour+dt*daySpeed*24/720)%24;
    const state=daylightState(hour,clock,coverage);
    vector.set(state.dx,state.dy,state.dz).normalize();
    sun.position.copy(sun.target.position).addScaledVector(vector,400);
    // Sample the same projected cloud field as the skydome at the sun.
    const scale=1.7/Math.max(.18,vector.y+.23),x=vector.x*scale+clock*.0025,z=vector.z*scale;
    const layer=.62*noise(x,z)+.27*noise(x*2.3,z*2.3)+.11*noise(x*4.9,z*4.9);
    const cloud=smooth(.59-state.cover*.26,.77-state.cover*.15,layer)*smooth(-.08,.19,vector.y)*(state.cover>.01?1:0);
    occlusion+=(1-cloud*.70-occlusion)*(1-Math.exp(-dt*2));
    sun.intensity=state.strength*occlusion;
    sun.color.copy(sunCold).lerp(sunWarm,state.warm*.98);
    hemi.intensity=.09+.35*state.daytime-.065*state.warm*state.daytime
      +.13*state.twilight;
    hemi.color.copy(ambientCold).lerp(ambientWarm,state.warm*.78);
    sky.material.uniforms.uZenith.value.copy(skyCool).lerp(skyWarm,state.warm*.86)
      .lerp(skyNight,1-state.daytime);
    filmHorizon.copy(horizonDay).lerp(horizonDusk,state.warm*.86)
      .lerp(horizonNight,1-state.daytime);
    sky.material.uniforms.uHorizon.value.copy(filmHorizon);
    // Skydome bypasses ACES, so its brightness needs independent control.
    sky.material.uniforms.uSkyBrightness.value=state.skyBrightness*(1-state.cover*.10);
    scene.fog.color.copy(filmHorizon).multiplyScalar(state.skyBrightness);
    sky.material.uniforms.uSunDiffusion.value=.17+.35*state.warm;
    sky.material.uniforms.uSunTint.value.set(1,.88-.20*state.warm,.73-.43*state.warm);
    sky.material.uniforms.uSunDirection.value.copy(vector);
    sky.material.uniforms.uCloudTime.value=clock*.0025;
    sky.material.uniforms.uCloudCoverage.value=state.cover;
    // Avoid exposure oscillation: adapt over roughly 1.5 s.
    const target=state.exposure;
    adapt+=(target-adapt)*(1-Math.exp(-dt*1.5));
    renderer.toneMappingExposure=adapt;
    sunClip.copy(camera.position).addScaledVector(vector,1000).project(camera);
    camera.getWorldDirection(look);
    const facing=Math.max(0,look.dot(vector));
    const visible=sunClip.z>-1&&sunClip.z<1&&facing>.35&&state.altitude>0;
    filmFrameMaterial.uniforms.uSunUv.value.set(sunClip.x*.5+.5,sunClip.y*.5+.5);
    filmFrameMaterial.uniforms.uSunGlare.value=visible?
      Math.pow((facing-.35)/.65,1.4)*state.daytime*state.shade*occlusion*glare*(.38+1.40*state.warm):0;
    return state;
  }
  return {update,get enabled(){return enabled},getHour:()=>hour,getCycle:()=>cycle,
    setHour(value){enabled=true;hour=((value%24)+24)%24;cycle=false;adapt=daylightState(hour,clock,coverage).exposure;update(0)},
    setCycle(value){enabled=true;cycle=value},setCoverage(value){coverage=value;update(0)},setGlare(value){glare=value;update(0)},
    reset(){enabled=initialEnabled;hour=initialHour;cycle=initialCycle;coverage=null;glare=1;adapt=daylightState(hour).exposure;update(0)}
  };
}
