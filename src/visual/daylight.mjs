// Approximate NOAA solar position for Vrigstad; azimuth clockwise from north.
// World axes are X east, Z south, Y up; solar angles use radians.
export const VRIGSTAD={latitude:57.3555,longitude:14.4756};
export const DEFAULT_SOLAR_DATE='2026-08-15';
export function validSolarDate(value) {
  if(typeof value!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(value))return DEFAULT_SOLAR_DATE;
  const [year,month,day]=value.split('-').map(Number);
  const d=new Date(Date.UTC(year,month-1,day));
  return d.getUTCFullYear()===year&&d.getUTCMonth()===month-1&&d.getUTCDate()===day?value:DEFAULT_SOLAR_DATE;
}
function euDst(year,month,day,hour) {
  if(month<3||month>10)return false;
  if(month>3&&month<10)return true;
  const last=new Date(Date.UTC(year,month,0));
  const lastSunday=last.getUTCDate()-last.getUTCDay();
  return month===3?(day>lastSunday||(day===lastSunday&&hour>=3))
    :(day<lastSunday||(day===lastSunday&&hour<3));
}
export function solarPosition(hour,date=DEFAULT_SOLAR_DATE,utcOffset=null) {
  const valid=validSolarDate(date),[year,month,day]=valid.split('-').map(Number);
  const dateUTC=Date.UTC(year,month-1,day);
  const n=Math.floor((dateUTC-Date.UTC(year,0,1))/86400000)+1;
  const timezone=utcOffset===null?(euDst(year,month,day,hour)?2:1):utcOffset;
  const gamma=2*Math.PI/365*(n-1+(hour-12)/24);
  const eot=229.18*(.000075+.001868*Math.cos(gamma)-.032077*Math.sin(gamma)
    -.014615*Math.cos(2*gamma)-.040849*Math.sin(2*gamma));
  const decl=.006918-.399912*Math.cos(gamma)+.070257*Math.sin(gamma)
    -.006758*Math.cos(2*gamma)+.000907*Math.sin(2*gamma)
    -.002697*Math.cos(3*gamma)+.00148*Math.sin(3*gamma);
  const hourAngle=(hour*60+eot+4*VRIGSTAD.longitude-60*timezone)/4*Math.PI/180-Math.PI;
  const lat=VRIGSTAD.latitude*Math.PI/180;
  const sine=Math.sin(lat)*Math.sin(decl)+Math.cos(lat)*Math.cos(decl)*Math.cos(hourAngle);
  const altitude=Math.asin(Math.max(-1,Math.min(1,sine)));
  const azimuth=(Math.atan2(Math.sin(hourAngle),
    Math.cos(hourAngle)*Math.sin(lat)-Math.tan(decl)*Math.cos(lat))+3*Math.PI)%(2*Math.PI);
  return {altitude,azimuth,dx:Math.sin(azimuth)*Math.cos(altitude),
    dy:Math.sin(altitude),dz:-Math.cos(azimuth)*Math.cos(altitude),date:valid};
}

// Seeded, smooth multi-day weather. No gameplay RNG and no per-frame state resets.
function weatherNoise(n) {
  const x=Math.sin(n*127.1+82.37)*43758.5453123;
  return x-Math.floor(x);
}
function weatherSmooth(x) {
  const i=Math.floor(x),f=x-i,t=f*f*(3-2*f);
  return weatherNoise(i)*(1-t)+weatherNoise(i+1)*t;
}
export function weatherCoverage(hour,date=DEFAULT_SOLAR_DATE,utcOffset=null) {
  const valid=validSolarDate(date),day=Date.parse(valid+'T00:00:00Z')/86400000;
  const [year,month,dateDay]=valid.split('-').map(Number);
  const t=day+(hour-(utcOffset===null?(euDst(year,month,dateDay,hour)?2:1):utcOffset))/24;
  // Multi-day front and intra-day fluctuations; no abrupt midnight transition.
  return Math.max(.04,Math.min(.94,.08+.60*weatherSmooth(t*.42+11)+.30*weatherSmooth(t*2.1+73)));
}
export function nextSolarDate(date) {
  const d=new Date(Date.parse(validSolarDate(date)+'T00:00:00Z')+86400000);
  return d.toISOString().slice(0,10);
}

// Solar direction is geographic; exposure, clouds and tint are artistic.
export function daylightState(hour, cloudTime=0, coverage=null, date=DEFAULT_SOLAR_DATE,utcOffset=null) {
  const h=((hour%24)+24)%24;
  const solar=solarPosition(h,date,utcOffset);
  const altitude=solar.altitude;
  const elevation=altitude*180/Math.PI;
  const daytime=Math.max(0,Math.min(1,(elevation+1.2)/16));
  const warm=Math.max(0,Math.min(1,(35-elevation)/29));
  const cover=coverage===null?weatherCoverage(h,date,utcOffset):Math.max(0,Math.min(1,coverage));
  // Broad cloud shadows: coherent across the entire scene; not a weather model.
  // Cloud cover also attenuates direct sun and glare, not just sky colour.
  const shade=Math.max(.30,1-cover*.82);
  // Twilight keeps residual skylight after direct sun fades; actual night
  // still requires headlights and street lamps, not artificial daylight.
  const twilight=Math.max(0,Math.min(1,(elevation+9)/12));
  return {
    hour:h,date:solar.date,altitude,azimuth:solar.azimuth,daytime,warm,cover,shade,
    dx:solar.dx,dy:solar.dy,dz:solar.dz,
    strength:daytime*(1.44-.48*warm)*shade,
    exposure:.69+.30*daytime-.11*warm+.03*(1-shade),
    skyBrightness:Math.max(.15,(.25+.75*daytime)*(1-.27*warm)),
    twilight
  };
}
// One absolute simulation clock shared with future seasons/events (#114).
// Input is Stockholm civil time. A repeated autumn hour chooses the first
// occurrence; a nonexistent spring hour normalizes forward. Advancing thereafter
// uses UTC instants, so solar direction is continuous through DST transitions.
export function createSolarClock(date=DEFAULT_SOLAR_DATE,hour=15.5) {
 const utc=new Date(0),local=new Date(0);let instant=0,offset=1,currentDate='',currentHour=0,cacheYear=0,start=0,end=0;
 function sync(){
  utc.setTime(instant);const year=utc.getUTCFullYear();
  if(year!==cacheYear){cacheYear=year;utc.setTime(Date.UTC(year,3,0));const march=utc.getUTCDate()-utc.getUTCDay();utc.setTime(Date.UTC(year,10,0));const october=utc.getUTCDate()-utc.getUTCDay();start=Date.UTC(year,2,march,1);end=Date.UTC(year,9,october,1)}
  offset=instant>=start&&instant<end?2:1;local.setTime(instant+offset*3600000);
  currentDate=local.toISOString().slice(0,10);currentHour=local.getUTCHours()+local.getUTCMinutes()/60+local.getUTCSeconds()/3600+local.getUTCMilliseconds()/3600000;
 }
 function set(value,h){const valid=validSolarDate(value),[year,month,day]=valid.split('-').map(Number),hours=Number.isFinite(h)?((h%24)+24)%24:15.5;instant=Date.parse(valid+'T00:00:00Z')+(hours-(euDst(year,month,day,hours)?2:1))*3600000;sync()}
 set(date,hour);
 return {set,advanceHours(h){instant+=h*3600000;sync()},getHour:()=>currentHour,getDate:()=>currentDate,getOffset:()=>offset,getInstant:()=>instant};
}

export function createDaylightController(THREE,{sun,hemi,renderer,camera,scene,dome,SUN_DIR,col}) {
 const params=new URLSearchParams(location.search);let enabled=params.get('lighting')!=='off';
 const initialEnabled=enabled,original={sun:sun.intensity,hemi:hemi.intensity,exposure:renderer.toneMappingExposure,sunColor:sun.color.clone(),hemiColor:hemi.color.clone(),fog:scene.fog.color.clone(),background:scene.background.clone(),direction:SUN_DIR.clone(),top:dome.material.uniforms.top.value.clone(),hor:dome.material.uniforms.hor.value.clone(),sunC:dome.material.uniforms.sunC.value.clone()};
 const initial={hour:params.has('time')&&Number.isFinite(+params.get('time'))?((+params.get('time')%24)+24)%24:15.5,date:validSolarDate(params.get('date')),cycle:params.get('cycle')==='on'||(!params.has('time')&&params.get('cycle')!=='off')};
 const clock=createSolarClock(initial.date,initial.hour);
 let hour=clock.getHour(),date=clock.getDate(),cycle=initial.cycle,cloudOverride=null,glare=1,elapsed=0,occlusion=1;
 const speed=Math.max(.01,Math.min(5,Number(params.get('daySpeed'))||1));
 const vector=new THREE.Vector3(),ambient=col(0xc8d9ed),cold=col(0xfff4dd),warm=col(0xff8e38),topDay=new THREE.Color(0x5f97c9),topDusk=new THREE.Color(0xb66b72),topNight=new THREE.Color(0x122137),horDay=new THREE.Color(0xd6e4e6),horDusk=new THREE.Color(0xe99a68),horNight=new THREE.Color(0x1d3046);
 const hash=(x,z)=>{const v=Math.sin(x*127.1+z*311.7)*43758.5453;return v-Math.floor(v)};
 function noise(x,z){const ix=Math.floor(x),iz=Math.floor(z);let a=x-ix,b=z-iz;a=a*a*(3-2*a);b=b*b*(3-2*b);return (hash(ix,iz)*(1-a)+hash(ix+1,iz)*a)*(1-b)+(hash(ix,iz+1)*(1-a)+hash(ix+1,iz+1)*a)*b}
 const smooth=(a,b,x)=>{const t=Math.max(0,Math.min(1,(x-a)/(b-a)));return t*t*(3-2*t)};
 function update(dt){
  if(!enabled)return;
  elapsed+=dt;
  if(cycle){clock.advanceHours(dt*speed/30);hour=clock.getHour();date=clock.getDate()}
  const state=daylightState(hour,elapsed,cloudOverride,date,clock.getOffset());
  vector.set(state.dx,state.dy,state.dz);SUN_DIR.copy(vector);
  sun.position.copy(sun.target.position).addScaledVector(vector,400);
  const scale=1.7/Math.max(.18,vector.y+.23),x=vector.x*scale+elapsed*.0025,z=vector.z*scale;
  const layer=.62*noise(x,z)+.27*noise(x*2.3,z*2.3)+.11*noise(x*4.9,z*4.9);
  const cover=smooth(.59-state.cover*.26,.77-state.cover*.15,layer)*smooth(-.08,.19,vector.y)*(state.cover>.01?1:0);
  occlusion+=(1-cover*.7-occlusion)*(1-Math.exp(-dt*2));
  sun.intensity=state.strength*occlusion;sun.color.copy(cold).lerp(warm,state.warm);
  hemi.intensity=.07+.40*state.daytime+.13*state.twilight;
  hemi.color.copy(ambient).lerp(warm,state.warm*.25);
  renderer.toneMappingExposure=state.exposure;
  const u=dome.material.uniforms;
  u.top.value.copy(topDay).lerp(topDusk,state.warm*.8).lerp(topNight,1-state.daytime);
  u.hor.value.copy(horDay).lerp(horDusk,state.warm*.8).lerp(horNight,1-state.daytime);
  u.sunC.value.setRGB(1,.88-.30*state.warm,.73-.5*state.warm);
  u.daylight.value=1;u.skyBrightness.value=state.skyBrightness*(1-state.cover*.10);u.coverage.value=state.cover;u.cloudTime.value=elapsed*.0025;u.glare.value=glare;u.warm.value=state.warm;
  scene.fog.color.copy(u.hor.value).multiplyScalar(u.skyBrightness.value);scene.background.copy(scene.fog.color);
 }
 return {get enabled(){return enabled},update,getHour:()=>hour,getDate:()=>date,getCycle:()=>cycle,getCoverage:()=>cloudOverride===null?weatherCoverage(hour,date,clock.getOffset()):cloudOverride,
  getSolarElevation:()=>solarPosition(hour,date,clock.getOffset()).altitude*180/Math.PI,
  setHour(v){enabled=true;clock.set(date,v);hour=clock.getHour();date=clock.getDate();cycle=false;update(0)},setDate(v){enabled=true;clock.set(v,hour);date=clock.getDate();hour=clock.getHour();update(0)},setCycle(v){enabled=true;cycle=v},setCoverage(v){cloudOverride=v;update(0)},setGlare(v){glare=v;update(0)},
  reset(){enabled=initialEnabled;clock.set(initial.date,initial.hour);hour=clock.getHour();date=clock.getDate();cycle=initial.cycle;cloudOverride=null;glare=1;
   if(enabled)update(0);else{SUN_DIR.copy(original.direction);sun.position.copy(sun.target.position).addScaledVector(SUN_DIR,400);sun.intensity=original.sun;sun.color.copy(original.sunColor);hemi.intensity=original.hemi;hemi.color.copy(original.hemiColor);renderer.toneMappingExposure=original.exposure;scene.fog.color.copy(original.fog);scene.background.copy(original.background);const u=dome.material.uniforms;u.top.value.copy(original.top);u.hor.value.copy(original.hor);u.sunC.value.copy(original.sunC);u.daylight.value=0}
  },
  state:()=>({enabled,hour,date,cycle,coverage:cloudOverride===null?weatherCoverage(hour,date,clock.getOffset()):cloudOverride,sunStrength:sun.intensity,exposure:renderer.toneMappingExposure,elevation:solarPosition(hour,date,clock.getOffset()).altitude*180/Math.PI})};
}
