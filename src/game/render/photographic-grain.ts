import type { SceneEffect } from './scene-finish';

export function resolveGrain(requested: string | null) {
  const value = requested?.trim().toLowerCase() ?? '';
  let strength = value === 'subtle' ? 0.62 : value === 'strong' ? 1.5 : 0;
  if (value && Number.isFinite(Number(value)) && Number(value) > 0) strength = Math.min(2, Number(value));
  const setting = strength === 0 ? 'off' : value === 'subtle' || value === 'strong' ? value : String(strength);
  return { requested, setting, strength, enabled: strength > 0 };
}

export function createPhotographicGrain(search = location.search) {
  let resolved = resolveGrain(new URLSearchParams(search).get('grain'));
  const uniforms = { uStrength: { value: resolved.strength }, uGrainPixelRatio: { value: 1 } };
  const effect: SceneEffect = {
    order: 20, enabled: () => resolved.enabled, uniforms,
    shader: `uniform float uStrength,uGrainPixelRatio;
float grainHash(vec2 pixel){vec3 p=fract(vec3(pixel.xyx)*vec3(.1031,.1030,.0973));p+=dot(p,p.yzx+33.33);return fract((p.x+p.y)*p.z);}
vec3 photographicGrain(vec3 c){
 float y=dot(c,vec3(.2126,.7152,.0722));
 float mid=smoothstep(.03,.30,y)*(1.-.62*smoothstep(.61,.97,y));
 vec2 pixel=gl_FragCoord.xy/uGrainPixelRatio;
 float noise=.85*grainHash(floor(pixel))+.15*grainHash(floor(pixel*.57)+vec2(91.,17.))-.5;
 return clamp(c+vec3(noise*.023*uStrength*(.25+.75*mid)),0.,1.);
}`,
    apply: 'if(uStrength>0.) c=photographicGrain(c);',
  };
  return {
    effect,
    set(value: string | null) { resolved = resolveGrain(value); uniforms.uStrength.value = resolved.strength; },
    setPixelRatio(value: number) { uniforms.uGrainPixelRatio.value = Math.max(1, value); },
    state: () => ({ ...resolved }),
  };
}
