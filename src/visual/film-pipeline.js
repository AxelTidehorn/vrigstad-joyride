/**
 * Vrigstad Joyride cinematic grade (Three.js r128).
 *
 * The main scene renders once to a LINEAR render target with ACES tone mapping;
 * this fullscreen pass applies the creative Classic Negative-inspired transform
 * to display-referred sRGB. Do not include Three's <encodings_fragment> in the
 * final shader: that would encode the result twice.
 *
 * The ?film=off URL flag removes ONLY the creative grade for matched screenshots.
 * No settings UI, new dependencies, world edits or additional simulation passes.
 */
renderer.outputEncoding = THREE.LinearEncoding;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.29;

// A distant sky sphere, centered on the active camera. The fog colour matches
// the horizon; the sphere is rendered before all world geometry with no depth write.
const filmHorizon = new THREE.Color(0x84969a);
scene.background = filmHorizon;
scene.fog = new THREE.Fog(filmHorizon, 285, 1840);
const filmSky = new THREE.Mesh(new THREE.SphereGeometry(3000, 32, 18), new THREE.ShaderMaterial({
  uniforms: {
    uZenith: { value: new THREE.Color(0x2c5277) },
    uHorizon: { value: filmHorizon }
  },
  side: THREE.BackSide,
  depthWrite: false,
  depthTest: false,
  fog: false,
  toneMapped: false,
  vertexShader: `
    varying float vElevation;
    void main() {
      vElevation = normalize(position).y;
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }
  `,
  fragmentShader: `
    uniform vec3 uZenith;
    uniform vec3 uHorizon;
    varying float vElevation;
    void main() {
      float t = pow(smoothstep(-0.16, 0.80, vElevation), 0.78);
      vec3 sky = mix(uHorizon, uZenith, t);
      // Very subtle warmth where Swedish daylight meets the landscape.
      sky += vec3(0.022, 0.012, -0.008) * (1.0 - smoothstep(-0.12, 0.25, vElevation));
      gl_FragColor = vec4(sky, 1.0);
    }
  `
}));
filmSky.renderOrder = -1000;
filmSky.frustumCulled = false;
scene.add(filmSky);

const filmTarget = new THREE.WebGLRenderTarget(1, 1, {
  minFilter: THREE.LinearFilter,
  magFilter: THREE.LinearFilter,
  format: THREE.RGBAFormat,
  type: THREE.UnsignedByteType,
  depthBuffer: true,
  stencilBuffer: false
});
filmTarget.texture.encoding = THREE.LinearEncoding;
filmTarget.texture.generateMipmaps = false;
const filmFrameScene = new THREE.Scene();
const filmFrameCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const filmFrameMaterial = new THREE.ShaderMaterial({
  depthTest: false,
  depthWrite: false,
  toneMapped: false,
  uniforms: {
    uScene: { value: filmTarget.texture },
    uGrade: { value: new URLSearchParams(location.search).get('film') === 'off' ? 0.0 : 1.0 }
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
      vec3 curve = smoothstep(vec3(0.045), vec3(0.955), c);
      c = mix(c, curve, 0.42);
      float y = dot(c, vec3(0.2126, 0.7152, 0.0722));

      // Cool low values, softly warm high values; no heavy orange/teal split.
      float shadows = 1.0 - smoothstep(0.12, 0.57, y);
      float highlights = smoothstep(0.53, 0.89, y);
      c += vec3(-0.016, 0.002, 0.028) * shadows;
      c += vec3(0.027, 0.013, -0.015) * highlights;

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
    void main() {
      vec3 base = clamp(toSRGB(texture2D(uScene, vUv).rgb), 0.0, 1.0);
      gl_FragColor = vec4(mix(base, classicNegative(base), uGrade), 1.0);
    }
  `
});
filmFrameScene.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), filmFrameMaterial));

// Keep target resolution exactly aligned with the renderer's physical pixels.
const filmDrawingSize = new THREE.Vector2();
function resizeFilmFrame() {
  renderer.getDrawingBufferSize(filmDrawingSize);
  filmTarget.setSize(Math.max(1, filmDrawingSize.x), Math.max(1, filmDrawingSize.y));
}
function renderFilmFrame() {
  filmSky.position.copy(camera.position);
  renderer.setRenderTarget(filmTarget);
  renderer.render(scene, camera);
  renderer.setRenderTarget(null);
  renderer.render(filmFrameScene, filmFrameCamera);
}
