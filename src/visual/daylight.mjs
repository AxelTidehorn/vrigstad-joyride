// Small experimental daylight controller. Pure solar state + renderer adapter.
// Sunrise / sunset approximations are aesthetic, not an astronomical ephemeris.
export function daylightState(hour, cloudTime=0) {
  const h=((hour%24)+24)%24;
  // Deliberately stylized Swedish summer arc, from 05:00 to 21:00.
  const phase=(h-5)/16;
  const raw=Math.sin(Math.PI*phase);
  const altitude=phase>0&&phase<1?Math.pow(Math.max(0,raw),1.6)*.96:-.12;
  const daytime=Math.max(0,Math.min(1,altitude/.22));
  const warm=Math.max(0,Math.min(1,(.62-altitude)/.52));
  const azimuth=Math.PI*(h-5)/16;
  const cloudNoise=.5+.24*Math.sin(cloudTime*.19+1.7)+.14*Math.sin(cloudTime*.43-0.8);
  const cover=Math.max(0,Math.min(.82,cloudNoise));
  // Broad cloud shadows: coherent across the entire scene; not a weather model.
  const shade=Math.max(.35,1-cover*.49);
  return {
    hour:h,altitude,daytime,warm,cover,shade,
    dx:Math.cos(azimuth)*Math.cos(Math.max(-.12,altitude)*1.12),
    dy:Math.max(-.15,altitude),
    dz:Math.sin(azimuth)*Math.cos(Math.max(-.12,altitude)*1.12),
    strength:daytime*(2.15-1.25*warm)*shade,
    exposure:.66+.56*daytime-.32*warm+.05*(1-shade),
    skyBrightness:Math.max(.09,(.14+.86*daytime)*(1-.43*warm))
  };
}
export function createDaylightController(THREE, config) {
  const {sun,hemi,renderer,camera,scene,sky,filmFrameMaterial,filmHorizon}=config;
  const params=new URLSearchParams(location.search);
  const enabled=params.get('lighting')!=='off';
  const specified=params.get('time');
  const fixedHour=specified!==null&&Number.isFinite(Number(specified))?Number(specified):null;
  const cycle=params.get('cycle')==='on';
  const speed=Number(params.get('daySpeed'));
  const daySpeed=Number.isFinite(speed)&&speed>0?Math.min(5,speed):1;
  let hour=fixedHour===null?15.5:fixedHour;
  const vector=new THREE.Vector3(),sunClip=new THREE.Vector3(),look=new THREE.Vector3(),skyCool=new THREE.Color(0x4c80b2),skyWarm=new THREE.Color(0xc86b73),skyNight=new THREE.Color(0x14243a);
  const ambientCold=new THREE.Color(0xc8d9ed),ambientWarm=new THREE.Color(0xffa776);
  const sunCold=new THREE.Color(0xfff2df),sunWarm=new THREE.Color(0xffaa66);
  const horizonDay=new THREE.Color(0x91b9d4),horizonDusk=new THREE.Color(0xf0a16e),horizonNight=new THREE.Color(0x1d3046);
  let clock=0,adapt=1.03;
  function update(dt) {
    if(!enabled)return;
    clock+=dt;
    if(cycle)hour=(hour+dt*daySpeed*24/720)%24;
    const state=daylightState(hour,clock);
    vector.set(state.dx,state.dy,state.dz).normalize();
    sun.position.copy(sun.target.position).addScaledVector(vector,400);
    sun.intensity=state.strength;
    sun.color.copy(sunCold).lerp(sunWarm,state.warm*.98);
    hemi.intensity=.065+.49*state.daytime-.18*state.warm*state.daytime;
    hemi.color.copy(ambientCold).lerp(ambientWarm,state.warm*.78);
    sky.material.uniforms.uZenith.value.copy(skyCool).lerp(skyWarm,state.warm*.86)
      .lerp(skyNight,1-state.daytime);
    filmHorizon.copy(horizonDay).lerp(horizonDusk,state.warm*.86)
      .lerp(horizonNight,1-state.daytime);
    sky.material.uniforms.uHorizon.value.copy(filmHorizon);
    // Skydome bypasses ACES, so its brightness needs independent control.
    sky.material.uniforms.uSkyBrightness.value=state.skyBrightness;
    scene.fog.color.copy(filmHorizon).multiplyScalar(state.skyBrightness);
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
      Math.pow((facing-.35)/.65,1.4)*state.daytime*state.shade*(.65+1.15*state.warm):0;
    return state;
  }
  return {update,enabled,getHour:()=>hour};
}
