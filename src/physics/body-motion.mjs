/**
 * Lightweight visual suspension for arcade cars. Only moves the rendered body:
 * tire forces, collisions and terrain contact stay in the driving model.
 * Local +X is right and -Z is forward. Positive roll leans left (outside a right turn).
 */
export const createBodyMotion = () => ({roll:0,rollV:0,pitch:0,pitchV:0,heave:0,heaveV:0});
const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
function spring(s,axis,target,frequency,damping,dt){
  const velocity=axis+'V',omega=frequency*2*Math.PI;
  s[velocity]+=((target-s[axis])*omega*omega-2*damping*omega*s[velocity])*dt;
  s[axis]+=s[velocity]*dt;
}
export function stepBodyMotion(s,signals,dt){
  if(!(dt>0))return s;
  const {forwardAcceleration=0,lateralAcceleration=0,speed=0,distance=0,terrainOffset=0,surface='asphalt'}=signals;
  const roll=clamp(lateralAcceleration/9.81*.085,-.115,.115);
  const pitch=clamp(forwardAcceleration/9.81*.062,-.075,.075);
  const rough=surface==='grass'?.022:surface==='gravel'?.014:.003;
  const ripple=rough*clamp(Math.abs(speed)/6,0,1)*(.6*Math.sin(distance*1.7)+.4*Math.sin(distance*4.1));
  const heave=clamp(terrainOffset*.48+ripple,-.065,.065);
  const n=Math.ceil(dt/(1/120)),h=dt/n;
  for(let i=0;i<n;i++){
    spring(s,'roll',roll,1.65,.77,h);
    spring(s,'pitch',pitch,1.85,.74,h);
    spring(s,'heave',heave,2.7,.82,h);
  }
  return s;
}
