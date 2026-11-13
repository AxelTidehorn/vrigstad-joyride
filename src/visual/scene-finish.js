// r128: retain upstream's ACES, sRGB output, material conversions and encoded fog.
// The target is RGBA8 (not a hardware sRGB texture). Its encoding tells r128's
// scene shaders to write sRGB, exactly like the canvas. Raw final sampling must
// NOT decode/encode or tone-map a second time. No automatic encoding chunks.
const sceneFinish=(()=>{
const FILM_PRESETS = {
  negative: {
    curve:[.045,1.045,.36], shadow:[-.016,.002,.028], highlight:[.008,.001,-.010],
    mid:[0,0,0], shoulder:.092,
    green:[.93,.85,.88], greenMix:.94, blue:[-.016,-.007,.023],
    red:[.018,.002,-.007], yellow:[0,0,0], cyan:[0,0,0],
    saturation:1.045, neutral:0
  },
  chrome: {
    curve:[.025,1.055,.28], shadow:[-.010,.001,.019], highlight:[0,0,0],
    mid:[0,0,0], shoulder:.085,
    green:[.96,.91,.94], greenMix:.85, blue:[-.018,-.006,.018],
    red:[-.018,.004,.006], yellow:[-.012,-.010,.012], cyan:[-.009,-.004,.012],
    saturation:.81, neutral:.85
  },
  gold: {
    curve:[.015,1.06,.20], shadow:[.008,.002,-.009], highlight:[.023,.013,-.024],
    mid:[.016,.006,-.012], shoulder:.085,
    green:[1.02,.98,.88], greenMix:.65, blue:[-.010,.002,.018],
    red:[.024,.002,-.008], yellow:[.018,.012,-.014], cyan:[-.008,.002,.012],
    saturation:1.065, neutral:.60
  },
  portra: {
    curve:[.015,1.075,.18], shadow:[-.005,.002,.012], highlight:[.008,.005,-.006],
    mid:[.006,.002,-.003], shoulder:.105,
    green:[1.01,.98,.97], greenMix:.70, blue:[.004,.006,-.006],
    red:[.004,.003,.002], yellow:[.004,.003,-.002], cyan:[.004,.003,0],
    saturation:.94, neutral:.92
  }
};
const q=new URLSearchParams(location.search).get('film');
const enabled=Object.prototype.hasOwnProperty.call(FILM_PRESETS,q);
const preset=FILM_PRESETS[enabled?q:'negative'];
const uniforms={};
for(const key of ['curve','shadow','highlight','mid','green','blue','red','yellow','cyan'])uniforms['u'+key[0].toUpperCase()+key.slice(1)]={value:new THREE.Vector3(...preset[key])};
for(const key of ['shoulder','greenMix','saturation','neutral'])uniforms['u'+key[0].toUpperCase()+key.slice(1)]={value:preset[key]};

if(!enabled)return {render:()=>renderer.render(scene,camera),resize(){},state:()=>({enabled:false,targets:0})};
const Target=renderer.capabilities.isWebGL2?THREE.WebGLMultisampleRenderTarget:THREE.WebGLRenderTarget;
const target=new Target(1,1,{minFilter:THREE.LinearFilter,magFilter:THREE.LinearFilter,depthBuffer:true,stencilBuffer:false});
target.texture.encoding=THREE.sRGBEncoding;target.texture.generateMipmaps=false;
if(target.isWebGLMultisampleRenderTarget)target.samples=coarse?2:4;
uniforms.uScene={value:target.texture};
const screen=new THREE.Scene(),view=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
const material=new THREE.ShaderMaterial({depthTest:false,depthWrite:false,toneMapped:false,uniforms,
vertexShader:'varying vec2 vUv;void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}',
fragmentShader:`uniform sampler2D uScene;varying vec2 vUv;
uniform vec3 uCurve,uShadow,uHighlight,uMid,uGreen,uBlue,uRed,uYellow,uCyan;
uniform float uShoulder,uGreenMix,uSaturation,uNeutral;
    vec3 photographicGrade(vec3 c) {
      // Controlled photographic S-curve in display space, keeping black and
      // white points without clipping interiors or the pale house facades.
      // Wider white shoulder than v0.6: retain local differences within pale
      // siding, cloudy sky and sunlit concrete instead of approaching pure white.
      vec3 curve = smoothstep(vec3(uCurve.x), vec3(uCurve.y), c);
      c = mix(c, curve, uCurve.z);
      float y = dot(c, vec3(0.2126, 0.7152, 0.0722));

      // Cool low values, softly warm high values; no heavy orange/teal split.
      float shadows = 1.0 - smoothstep(0.12, 0.57, y);
      float highlights = smoothstep(0.53, 0.89, y);
      // Chroma gate protects greys/white paint from the warmer looks.
      float chroma = max(c.r,max(c.g,c.b))-min(c.r,min(c.g,c.b));
      float tint = mix(1.0, smoothstep(.015,.16,chroma), uNeutral);
      c += uShadow * shadows * tint;
      c += uMid * (4.0*y*(1.0-y)) * tint;
      // Keep chromatic warmth, but stop actively lifting bright luminance.
      c += uHighlight * highlights * tint;
      // A stronger chroma-preserving photographic shoulder: compress bright
      // material responses without flattening the whole day scene or crushing
      // the difference between a white wall and a warmer roof.
      // Unlike subtracting a constant RGB value, scaling all three channels
      // together maintains the colour ratio of sunlit yellows and brick.
      float shoulderY = dot(c, vec3(0.2126, 0.7152, 0.0722));
      float shoulder = smoothstep(0.59, 0.95, shoulderY);
      c *= 1.0 - uShoulder * shoulder;

      // Foliage should be olive/forest green, not a bright lime-coloured mass.
      float green = smoothstep(0.022, 0.20, c.g - max(c.r, c.b));
      c = mix(c, c * uGreen, green * uGreenMix);

      // Strong but restrained sky/blue-car separation.
      float blue = smoothstep(0.035, 0.24, c.b - c.r)
                 * smoothstep(-0.03, 0.15, c.b - c.g);
      c += uBlue * blue;

      // Pigmented red timber and ochre should retain their character.
      float red = smoothstep(0.035, 0.23, c.r - c.g)
                * smoothstep(0.015, 0.20, c.r - c.b);
      c += uRed * red;

      float yellow = smoothstep(.03,.20,min(c.r,c.g)-c.b)
                   * (1.0-smoothstep(.08,.30,abs(c.r-c.g)));
      float cyan = smoothstep(.025,.18,min(c.g,c.b)-c.r);
      c += uYellow * yellow + uCyan * cyan;
      float neutral = dot(c, vec3(0.2126, 0.7152, 0.0722));
      c = mix(vec3(neutral), c, uSaturation);
      return clamp(c, 0.0, 1.0);
    }

vec3 finishColor(vec3 c){return photographicGrade(c);}
void main(){gl_FragColor=vec4(finishColor(texture2D(uScene,vUv).rgb),1.);}`});
screen.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2),material));
const size=new THREE.Vector2();
return {
 render(){renderer.setRenderTarget(target);renderer.render(scene,camera);renderer.setRenderTarget(null);renderer.render(screen,view)},
 resize(){renderer.getDrawingBufferSize(size);target.setSize(Math.max(1,size.x),Math.max(1,size.y))},
 state:()=>({enabled:true,targets:1,setting:q,preset:q})
};
})();
