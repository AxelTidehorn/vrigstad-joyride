import * as THREE from 'three';

import type { createPhotographicGrades } from './photographic-grades';

// Apply Classic Negative after the native ACES/sRGB scene render.
export function createSceneFinish(renderer: THREE.WebGLRenderer, scene: THREE.Scene, camera: THREE.Camera, grade: ReturnType<typeof createPhotographicGrades>) {
  const effect = grade.effect;
  const size = new THREE.Vector2();
  let frame: THREE.FramebufferTexture | undefined;
  let material: THREE.ShaderMaterial | undefined;
  let screen: THREE.Scene | undefined;
  const view = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  let frames = 0, copies = 0, passes = 0, nativeFrames = 0;
  function resize() {
    if (!frame) return;
    renderer.getDrawingBufferSize(size);
    if (frame.image.width === size.x && frame.image.height === size.y) return;
    frame.dispose();
    frame = undefined;
  }
  function prepare() {
    if (!material) {
      const uniforms = { uScene: { value: null }, ...effect.uniforms };
      material = new THREE.ShaderMaterial({
        uniforms, depthTest: false, depthWrite: false, toneMapped: false,
        vertexShader: 'varying vec2 vUv; void main(){vUv=uv;gl_Position=vec4(position.xy,0.,1.);}',
        fragmentShader: `uniform sampler2D uScene; varying vec2 vUv;\n${effect.shader}\nvoid main(){vec3 c=texture2D(uScene,vUv).rgb;${effect.apply}gl_FragColor=vec4(c,1.);}`,
      });
      screen = new THREE.Scene();
      screen.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material));
    }
    if (!frame) {
      renderer.getDrawingBufferSize(size);
      frame = new THREE.FramebufferTexture(Math.max(1, size.x), Math.max(1, size.y));
      frame.colorSpace = THREE.NoColorSpace;
      material.uniforms.uScene.value = frame;
    }
  }
  return {
    render() {
      renderer.render(scene, camera);
      frames++;
      if (!effect.enabled()) { nativeFrames++; return; }
      resize();
      prepare();
      renderer.copyFramebufferToTexture(frame!);
      copies++;
      renderer.render(screen!, view);
      passes++;
    },
    resize,
    state: () => ({ frames, copies, passes, nativeFrames,
      width: frame?.image.width ?? 0, height: frame?.image.height ?? 0 }),
  };
}
