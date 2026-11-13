/**
 * Vrigstad Joyride cinematic grade (Three.js r128).
 *
 * The main scene renders once to a LINEAR render target with ACES tone mapping;
 * this fullscreen pass applies the creative Classic Negative-inspired transform
 * to display-referred sRGB. Do not include Three's <encodings_fragment> in the
 * final shader: that would encode the result twice.
 *
 * The ?film=off URL flag removes ONLY the creative grade for matched screenshots.
 * Fine, monochrome grain is applied after the grade, before the WebGL canvas is
 * composited under the HTML UI (which never receives grain).
 * No settings UI, new dependencies, world edits or additional simulation passes.
 */
renderer.outputEncoding = THREE.LinearEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
// Reduced from 1.29: protect white facades and bright roads without dimming
// the world uniformly (the directional/fill balance is retuned separately).
renderer.toneMappingExposure = 1.03; // 1.13 was still washing out pale facades

// A distant sky sphere, centered on the active camera. The fog colour matches
// the horizon; the sphere is rendered before all world geometry with no depth write.
const filmHorizon = new THREE.Color(0x798b8f);
scene.background = filmHorizon;
scene.fog = new THREE.Fog(filmHorizon, 390, 2000);
const filmSky = new THREE.Mesh(new THREE.SphereGeometry(3000, 32, 18), new THREE.ShaderMaterial({
  uniforms: {
    uZenith: { value: new THREE.Color(0x2c5277) },
    uHorizon: { value: filmHorizon },
    uSunDirection: { value: new THREE.Vector3(0, -1, 0) },
    uCloudTime: { value: 0 },
    uCloudCoverage: { value: 0.4 }
  },
  side: THREE.BackSide,
  depthWrite: false,
  depthTest: false,
  fog: false,
  toneMapped: false,
  vertexShader: `
    varying float vElevation;
    varying vec3 vSkyDir;
    void main() {
      vSkyDir = normalize(position);
      vElevation = vSkyDir.y;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: `
    uniform vec3 uZenith;
    uniform vec3 uHorizon;
    uniform vec3 uSunDirection;
    uniform float uCloudTime;
    uniform float uCloudCoverage;
    varying float vElevation;
    varying vec3 vSkyDir;
    float cloudHash(vec2 p) {
      return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);
    }
    float cloudNoise(vec2 p) {
      vec2 i=floor(p),f=fract(p);
      f=f*f*(3.0-2.0*f);
      return mix(mix(cloudHash(i),cloudHash(i+vec2(1.0,0.0)),f.x),
        mix(cloudHash(i+vec2(0.0,1.0)),cloudHash(i+vec2(1.0,1.0)),f.x),f.y);
    }
    void main() {
      float t=pow(smoothstep(-0.16,0.80,vElevation),0.78);
      vec3 sky=mix(uHorizon,uZenith,t);
      sky+=vec3(0.022,0.012,-0.008)*(1.0-smoothstep(-0.12,0.25,vElevation));
      // Cheap cloud bank instead of expensive volumetric raymarching.
      vec2 coord=vSkyDir.xz/max(0.18,vSkyDir.y+0.23)*1.7+vec2(uCloudTime,0.0);
      float layer=.62*cloudNoise(coord)+.27*cloudNoise(coord*2.3)+.11*cloudNoise(coord*4.9);
      float cloud=smoothstep(.59-uCloudCoverage*.26,.77-uCloudCoverage*.15,layer);
      cloud*=smoothstep(-.08,.19,vElevation)*step(.01,uCloudCoverage);
      vec3 cloudCol=mix(vec3(.63,.66,.70),vec3(.94,.94,.91),smoothstep(0.0,.6,vElevation));
      sky=mix(sky,cloudCol,cloud*.85);
      float towardSun=max(0.0,dot(normalize(vSkyDir),normalize(uSunDirection)));
      float disc=smoothstep(.99965,.99994,towardSun)*step(0.01,uSunDirection.y);
      float halo=pow(towardSun,85.0)*step(0.01,uSunDirection.y);
      sky+=vec3(1.0,.88,.73)*(disc*1.35+halo*.30)*(1.0-cloud*.85);
      gl_FragColor=vec4(sky,1.0);
    }
  `
}));
filmSky.renderOrder = -1000;
filmSky.frustumCulled = false;
scene.add(filmSky);

// Rendering into a plain target bypasses canvas antialiasing. Preserve edge
// quality via WebGL2 MSAA; WebGL1 still uses the portable colour target.
const FilmTargetType = renderer.capabilities.isWebGL2
  ? THREE.WebGLMultisampleRenderTarget : THREE.WebGLRenderTarget;
const filmTarget = new FilmTargetType(1, 1, {
  minFilter: THREE.LinearFilter,
  magFilter: THREE.LinearFilter,
  format: THREE.RGBAFormat,
  type: THREE.UnsignedByteType,
  depthBuffer: true,
  stencilBuffer: false
});
if (filmTarget.isWebGLMultisampleRenderTarget) filmTarget.samples = coarse ? 2 : 4;
filmTarget.texture.encoding = THREE.LinearEncoding;
filmTarget.texture.generateMipmaps = false;
const filmFrameScene = new THREE.Scene();
const filmFrameCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
// Grain is stable in framebuffer pixel space. Avoid per-frame random seeds:
// animated white noise would shimmer badly on thin geometry and during driving.
// Strong is the default by artistic decision; no new settings system.
// URL overrides for review: ?grain=off, ?grain=subtle, ?grain=strong.
const FILM_GRAIN_STRENGTH = 1.35;
const filmGrainSetting = new URLSearchParams(location.search).get('grain');
const filmGrainStrength = filmGrainSetting === 'off' ? 0.0
  : filmGrainSetting === 'strong' ? 1.35
  : filmGrainSetting === 'subtle' ? 0.62
  : FILM_GRAIN_STRENGTH;

// Mist / weak diffusion (1/8 strength as artistic reference).
// The mask prefers isolated bright glints, avoiding broad white walls or sky.
// Review without a new settings UI using ?mist=off, ?mist=subtle, ?mist=strong.
const FILM_MIST_STRENGTH = 0.42;
const filmMistSetting = new URLSearchParams(location.search).get('mist');
const filmMistStrength = filmMistSetting === 'off' ? 0
  : filmMistSetting === 'strong' ? 0.95
  : filmMistSetting === 'subtle' ? 0.42 : FILM_MIST_STRENGTH;
const filmFrameMaterial = new THREE.ShaderMaterial({
  depthTest: false,
  depthWrite: false,
  toneMapped: false,
  uniforms: {
    uScene: { value: filmTarget.texture },
    uGrade: { value: new URLSearchParams(location.search).get('film') === 'off' ? 0.0 : 1.0 },
    uGrain: { value: filmGrainStrength },
    uMist: { value: filmMistStrength },
    uMistTexel: { value: new THREE.Vector2(1,1) },
    uSunUv: { value: new THREE.Vector2(-2,-2) },
    uSunGlare: { value: 0 }
  },
  vertexShader: `
    varying vec2 vUv;
    void main() {
      vUv = uv;
      gl_Position = vec4(position.xy, 0.0, 1.0);
    }
  `,
  fragmentShader: `
    uniform sampler2D uScene;
    uniform float uGrade;
    uniform float uGrain;
    uniform float uMist;
    uniform vec2 uMistTexel;
    uniform vec2 uSunUv;
    uniform float uSunGlare;
    varying vec2 vUv;

    // The texture contains ACES-tonemapped LINEAR colour.
    // Encode to sRGB once, at the end of the rendering pipeline.
    vec3 toSRGB(vec3 x) {
      x = max(x, vec3(0.0));
      vec3 low = 12.92 * x;
      vec3 high = 1.055 * pow(x, vec3(1.0 / 2.4)) - 0.055;
      return mix(low, high, step(vec3(0.0031308), x));
    }
    vec3 classicNegative(vec3 c) {
      // Controlled photographic S-curve in display space, keeping black and
      // white points without clipping interiors or the pale house facades.
      // Wider white shoulder than v0.6: retain local differences within pale
      // siding, cloudy sky and sunlit concrete instead of approaching pure white.
      vec3 curve = smoothstep(vec3(0.045), vec3(1.045), c);
      c = mix(c, curve, 0.36);
      float y = dot(c, vec3(0.2126, 0.7152, 0.0722));

      // Cool low values, softly warm high values; no heavy orange/teal split.
      float shadows = 1.0 - smoothstep(0.12, 0.57, y);
      float highlights = smoothstep(0.53, 0.89, y);
      c += vec3(-0.016, 0.002, 0.028) * shadows;
      // Keep chromatic warmth, but stop actively lifting bright luminance.
      c += vec3(0.008, 0.001, -0.010) * highlights;
      // A stronger chroma-preserving photographic shoulder: compress bright
      // material responses without flattening the whole day scene or crushing
      // the difference between a white wall and a warmer roof.
      // Unlike subtracting a constant RGB value, scaling all three channels
      // together maintains the colour ratio of sunlit yellows and brick.
      float shoulderY = dot(c, vec3(0.2126, 0.7152, 0.0722));
      float shoulder = smoothstep(0.59, 0.95, shoulderY);
      c *= 1.0 - 0.092 * shoulder;

      // Foliage should be olive/forest green, not a bright lime-coloured mass.
      float green = smoothstep(0.022, 0.20, c.g - max(c.r, c.b));
      c = mix(c, c * vec3(0.93, 0.85, 0.88), green * 0.94);

      // Strong but restrained sky/blue-car separation.
      float blue = smoothstep(0.035, 0.24, c.b - c.r)
                 * smoothstep(-0.03, 0.15, c.b - c.g);
      c += vec3(-0.016, -0.007, 0.023) * blue;

      // Pigmented red timber and ochre should retain their character.
      float red = smoothstep(0.035, 0.23, c.r - c.g)
                * smoothstep(0.015, 0.20, c.r - c.b);
      c += vec3(0.018, 0.002, -0.007) * red;

      float neutral = dot(c, vec3(0.2126, 0.7152, 0.0722));
      c = mix(vec3(neutral), c, 1.045);
      return clamp(c, 0.0, 1.0);
    }
    // Fine, deterministic screen-space grain: single luminance value is added
    // equally to all three channels, so there are no coloured speckles.
    // Fixed sampling avoids temporal flicker even while the camera is moving.
    float grainHash(vec2 pixel) {
      vec3 p = fract(vec3(pixel.xyx) * vec3(0.1031, 0.1030, 0.0973));
      p += dot(p, p.yzx + 33.33);
      return fract((p.x + p.y) * p.z);
    }
    // Strictly brightness-selective micro diffusion. Eight taps in the
    // existing final pass; large equally bright areas yield no halo because
    // they have a high mask coverage. Thin glints remain isolated.
    float mistLuma(vec2 uv) {
      vec3 c = texture2D(uScene, clamp(uv,vec2(0.001),vec2(0.999))).rgb;
      return dot(c,vec3(0.2126,0.7152,0.0722));
    }
    float mistBright(vec2 uv) {
      return smoothstep(0.63,0.89,mistLuma(uv));
    }
    void main() {
      vec3 base = clamp(toSRGB(texture2D(uScene, vUv).rgb), 0.0, 1.0);
      vec3 graded = mix(base, classicNegative(base), uGrade);

      // Selective Black-Pro-Mist-like highlight glow after colour grading.
      // Only compact, intense peaks contribute; the source image remains sharp.
      // No all-scene blur, no glow on DOM HUD or minimap.
      if (uMist > 0.0) {
        vec2 t=uMistTexel;
        float n0=mistBright(vUv+vec2( 3.0, 0.0)*t);
        float n1=mistBright(vUv+vec2(-3.0, 0.0)*t);
        float n2=mistBright(vUv+vec2( 0.0, 3.0)*t);
        float n3=mistBright(vUv+vec2( 0.0,-3.0)*t);
        float n4=mistBright(vUv+vec2( 7.0, 7.0)*t);
        float n5=mistBright(vUv+vec2(-7.0, 7.0)*t);
        float n6=mistBright(vUv+vec2( 7.0,-7.0)*t);
        float n7=mistBright(vUv+vec2(-7.0,-7.0)*t);
        float local=(n0+n1+n2+n3)*0.125+(n4+n5+n6+n7)*0.125;
        float peak=max(max(max(n0,n1),max(n2,n3)),max(max(n4,n5),max(n6,n7)));
        float isolated=1.0-smoothstep(0.22,0.55,local);
        float mistGlow=0.095*uMist*peak*isolated;
        graded=clamp(graded+vec3(1.0,0.95,0.87)*mistGlow,0.0,1.0);
      }

      // Camera-facing sun glare: limited to bright scenery, not the DOM overlay.
      // A/B via ?lighting=off or a fixed ?time=13 / ?time=19.
      if (uSunGlare > 0.001) {
        vec2 delta=(vUv-uSunUv)*vec2(1.7778,1.0);
        float r2=dot(delta,delta);
        float nearSun=exp(-r2*95.0)*.54+exp(-r2*13.0)*.16;
        float sceneBright=smoothstep(.46,.84,dot(graded,vec3(.2126,.7152,.0722)));
        graded=clamp(graded+vec3(1.0,.88,.72)*uSunGlare*nearSun*(.38+.62*sceneBright),0.0,1.0);
      }

      // Grain is most visible in middle tones, subdued near deep black and
      // diffuse whites. No blur or extra texture fetches are needed.
      if (uGrain > 0.0) {
        float luminance = dot(graded, vec3(0.2126, 0.7152, 0.0722));
        float midtone = smoothstep(0.03, 0.30, luminance)
                      * (1.0 - 0.62 * smoothstep(0.61, 0.97, luminance));
        float amplitude = 0.023 * uGrain * (0.25 + 0.75 * midtone);
        float fine = grainHash(floor(gl_FragCoord.xy));
        float irregular = grainHash(floor(gl_FragCoord.xy * 0.57) + vec2(91.0, 17.0));
        float monochrome = (fine * 0.85 + irregular * 0.15) - 0.5;
        graded = clamp(graded + vec3(monochrome * amplitude), 0.0, 1.0);
      }
      gl_FragColor = vec4(graded, 1.0);
    }
  `
});
filmFrameScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), filmFrameMaterial));

// Keep target resolution exactly aligned with the renderer's physical pixels.
const filmDrawingSize = new THREE.Vector2();
function resizeFilmFrame() {
  renderer.getDrawingBufferSize(filmDrawingSize);
  const w=Math.max(1,filmDrawingSize.x),h=Math.max(1,filmDrawingSize.y);
  filmTarget.setSize(w,h);
  filmFrameMaterial.uniforms.uMistTexel.value.set(1/w,1/h);
}
function renderFilmFrame() {
  filmSky.position.copy(camera.position);
  renderer.setRenderTarget(filmTarget);
  renderer.render(scene, camera);
  renderer.setRenderTarget(null);
  renderer.render(filmFrameScene, filmFrameCamera);
}
