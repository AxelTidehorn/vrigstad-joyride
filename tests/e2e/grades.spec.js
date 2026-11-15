import { test, expect } from '@playwright/test';
import { watchErrors, buildFixture } from './render-helpers.js';
for (const [requested, preset] of [['off','off'],['unknown','off'],['Chrome','chrome'],['negative','negative'],['gold','gold'],['portra','portra']]) {
  test(`film ${requested} reports the active profile and renders`, async ({ page }, info) => {
    const errors = watchErrors(page);
    await page.setViewportSize({ width: 640, height: 360 });
    await page.goto('/index.html?film=' + requested);
    await expect.poll(() => page.evaluate(() => window.__joyride?.state().rendering.frames)).toBeGreaterThan(3);
    const s = await page.evaluate(() => window.__joyride.state());
    expect(s.film).toMatchObject({ setting: requested, preset, enabled: preset !== 'off' });
    if (preset === 'off') expect(s.rendering.copies).toBe(0);
    else { expect(s.rendering.copies).toBeGreaterThan(2); expect(s.rendering.passes).toBe(s.rendering.copies); }
    expect(await page.evaluate(() => document.querySelector('#gl').getContext('webgl2').getError())).toBe(0);
    await page.screenshot({ path: info.outputPath(`day-${preset}.png`) });
    expect(errors).toEqual([]);
  });
}
test('production profile setter applies every uniform and bypasses off', async ({ page }) => {
  await buildFixture('grades');
  const errors = watchErrors(page);
    await page.setViewportSize({ width: 640, height: 360 });
  await page.goto('/.work/grades/index.html');
  await page.waitForFunction(() => window.harness);
  for (const preset of ['negative', 'chrome', 'gold', 'portra']) {
    const result = await page.evaluate(preset => {
      const { grades, finish } = window.harness;
      grades.set(preset); finish.render();
      const state = grades.state(), values = {};
      for (const [key, value] of Object.entries(state.parameters)) {
        const actual = grades.effect.uniforms['u' + key[0].toUpperCase() + key.slice(1)].value;
        values[key] = actual?.isVector3 ? actual.toArray() : actual;
      }
      return { parameters: state.parameters, values };
    }, preset);
    expect(result.values).toEqual(result.parameters);
  }
  const before = await page.evaluate(() => { window.harness.grades.set('unknown'); return window.harness.finish.state(); });
  await expect.poll(() => page.evaluate(() => window.harness.finish.state().nativeFrames)).toBeGreaterThan(before.nativeFrames + 3);
  expect(await page.evaluate(() => window.harness.finish.state().copies)).toBe(before.copies);
  expect(await page.evaluate(() => window.harness.grades.state())).toMatchObject({ preset: 'off', enabled: false });
  expect(await page.evaluate(() => window.harness.renderer.getContext().getError())).toBe(0);
  expect(errors).toEqual([]);
});
