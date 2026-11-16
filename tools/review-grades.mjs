// Reproducible scene captures; never patches shaders or maintains uniform lists.
// Staged lighting is independent of #152. Full solar integration is checked separately.
import { build } from 'vite';
import { chromium } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
const output = resolve('.work/grades-review');
const hook = { name: 'grade-review', enforce: 'pre', transform(src, id) {
  if (!id.endsWith('/src/game/main.ts')) return;
  const marker = 'resize(); requestAnimationFrame(frame);';
  if (!src.includes(marker)) throw new Error('The review hook no longer matches src/game/main.ts');
  return src.replace(marker, `
window.__review = { grades, sceneFinish, sun, scene, dome, renderer, SUN_DIR };
resize(); requestAnimationFrame(frame);`);
} };
await build({ plugins: [hook], logLevel: 'warn', build: { outDir: output, rollupOptions: { input: resolve('src/index.html') } } });
const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--host-resolver-rules=MAP fonts.googleapis.com ~NOTFOUND, MAP fonts.gstatic.com ~NOTFOUND'] });
try {
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => { if (/WebGL.*(error|INVALID)|GL_INVALID|THREE.WebGLProgram/i.test(m.text())) errors.push(m.text()); });
  await page.addInitScript(() => {
    const callbacks = [];
    window.requestAnimationFrame = cb => { callbacks.push(cb); return callbacks.length; };
    performance.now = () => 1000;
    window.__reviewStep = () => { const pending = callbacks.splice(0); for (const cb of pending) cb(1000); };
  });
  await page.goto(pathToFileURL(output + '/index.html').href);
  await page.waitForFunction(() => window.__review);
  await page.locator('#go').click();
  const parameters = {};
  for (const environment of ['day', 'sunset', 'night']) {
    parameters[environment] = {};
    await page.evaluate(environment => {
      const { sun, scene, dome, renderer, SUN_DIR } = window.__review;
      const hemi = scene.children.find(n => n.isHemisphereLight);
      const u = dome.material.uniforms;
      const setup = {
        day: { strength: 0.95, ambient: 0.62, direction: [-0.55,0.75,0.37], top: 0x5f97c9, horizon: 0xd6e4e6, tint: 0xfff4dd, exposure: 1 },
        sunset: { strength: 0.5, ambient: 0.35, direction: [-0.9,0.1,0.3], top: 0x96728b, horizon: 0xe99a68, tint: 0xff8e38, exposure: 0.7 },
        night: { strength: 0, ambient: 0.14, direction: [-0.5,-0.5,0.2], top: 0x122137, horizon: 0x1d3046, tint: 0xff8e38, exposure: 0.65 },
      }[environment];
      sun.intensity = setup.strength * Math.PI; sun.visible = setup.strength > 0; sun.castShadow = sun.visible;
      sun.color.setHex(setup.tint).convertSRGBToLinear(); hemi.intensity = setup.ambient * Math.PI;
      SUN_DIR.fromArray(setup.direction).normalize();
      u.top.value.setHex(setup.top); u.hor.value.setHex(setup.horizon);
      u.sunC.value.setScalar(environment === 'night' ? 0 : 1);
      scene.fog.color.setHex(setup.horizon); scene.background.copy(scene.fog.color);
      renderer.toneMappingExposure = setup.exposure;
    }, environment);
    for (const preset of ['off', 'chrome', 'negative', 'gold', 'portra']) {
      parameters[environment][preset] = await page.evaluate(preset => {
        window.__review.grades.set(preset); window.__reviewStep();
        const gl = window.__review.renderer.getContext();
        if (gl.getError() !== gl.NO_ERROR) throw new Error('WebGL error');
        return window.__review.grades.state();
      }, preset);
      await page.screenshot({ path: `${output}/${environment}-${preset}.png` });
    }
  }
  if (errors.length) throw new Error(errors.join('\n'));
  mkdirSync(output, { recursive: true });
  writeFileSync(`${output}/parameters.json`, JSON.stringify({ environments: 'staged game lighting, not the solar controller', parameters }, null, 2));
  console.log('15 matched captures in ' + output);
} finally { await browser.close(); }
