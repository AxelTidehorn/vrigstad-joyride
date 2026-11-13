// Small experimental daylight controller. Pure solar state + renderer adapter.
// Sunrise / sunset approximations are aesthetic, not an astronomical ephemeris.
export function daylightState(hour, cloudTime=0) {
  const h=((hour%24)+24)%24;
  const phase=(h-4)/18;
  const altitude=Math.sin(Math.PI*phase);
  const daytime=Math.max(0,Math.min(1,altitude/.30));
  const warm=Math.pow(1-Math.max(0,altitude),3);
  const azimuth=Math.PI*(h-4)/18;
  const cloudNoise=.5+.24*Math.sin(cloudTime*.19+1.7)+.14*Math.sin(cloudTime*.43-0.8);
  const cover=Math.max(0,Math.min(.82,cloudNoise));
  // Broad cloud shadows: coherent across the entire scene; not a weather model.
  const shade=Math.max(.35,1-cover*.49);
  return {
    hour:h,altitude,daytime,warm,cover,shade,
    dx:Math.cos(azimuth)*Math.cos(Math.max(-.12,altitude)*1.12),
    dy:Math.max(-.15,altitude),
    dz:Math.sin(azimuth)*Math.cos(Math.max(-.12,altitude)*1.12),
    strength:daytime*(1.35-.42*warm)*shade,
    exposure:.82+.26*daytime+.08*(1-shade)
  };
}
export function createDaylightController(THREE, config) {
  const {sun,hemi,renderer,camera,sky,filmFrameMaterial,filmHorizon}=config;
  const params=new URLSearchParams(location.search);
  const enabled=params.get('lighting')!=='off';
  const specified=params.get('time');
  const fixedHour=specified!==null&&Number.isFinite(Number(specified))?Number(specified):null;
  const cycle=params.get('cycle')==='on';
  const speed=Number(params.get('daySpeed'));
  const daySpeed=Number.isFinite(speed)&&speed>0?Math.min(5,speed):1;
  let hour=fixedHour===null?15.5:fixedHour;
  const vector=new THREE.Vector3(),sunClip=new THREE.Vector3(),look=new THREE.Vector3(),skyCool=new THREE.Color(0xb8c9da),skyWarm=new THREE.Color(0xffc18c);
  const ambientCold=new THREE.Color(0xbccbdc),ambientWarm=new THREE.Color(0xffc499);
  const sunCold=new THREE.Color(0xfff2df),sunWarm=new THREE.Color(0xffaa66);
  const horizonDay=new THREE.Color(0x798b8f),horizonDusk=new THREE.Color(0xd18b75);
  let clock=0,adapt=1.03;
  function update(dt) {
    if(!enabled)return;
    clock+=dt;
    if(cycle)hour=(hour+dt*daySpeed*24/720)%24;
    const state=daylightState(hour,clock);
    vector.set(state.dx,state.dy,state.dz).normalize();
    sun.position.copy(sun.target.position).addScaledVector(vector,400);
    sun.intensity=.03+state.strength;
    sun.color.copy(sunCold).lerp(sunWarm,state.warm*.90);
    hemi.intensity=.13+.23*state.daytime;
    hemi.color.copy(ambientCold).lerp(ambientWarm,state.warm*.65);
    sky.material.uniforms.uZenith.value.copy(skyCool).lerp(skyWarm,state.warm*.45);
    filmHorizon.copy(horizonDay).lerp(horizonDusk,state.warm*.62);
    sky.material.uniforms.uHorizon.value.copy(filmHorizon);
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
      Math.pow((facing-.35)/.65,2)*state.daytime*state.shade*.90:0;
    return state;
  }
  return {update,enabled,getHour:()=>hour};
}
