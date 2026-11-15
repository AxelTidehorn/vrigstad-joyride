import { test, expect } from '@playwright/test';
import { watchErrors, buildFixture } from './render-helpers.js';
for (const [query, setting, strength] of [['','off',0],['=','off',0],['=-1','off',0],['=foo','off',0],['=subtle','subtle',0.62],['=strong','strong',1.5]]) {
  test(`grain ${query || 'default'} renders multiple frames`, async ({ page }, info) => {
    const errors = watchErrors(page);
    await page.setViewportSize({ width: 640, height: 360 });
    await page.goto('/index.html' + (query ? '?grain' + query : ''));
    await expect.poll(() => page.evaluate(() => window.__joyride?.state().rendering.frames)).toBeGreaterThan(3);
    const s = await page.evaluate(() => window.__joyride.state());
    expect(s.grain).toMatchObject({ setting, strength, enabled: strength > 0 });
    if (strength) { expect(s.rendering.copies).toBeGreaterThan(2); expect(s.rendering.passes).toBe(s.rendering.copies); }
    else { expect(s.rendering.copies).toBe(0); expect(s.rendering.nativeFrames).toBe(s.rendering.frames); expect(s.rendering.width).toBe(0); }
    expect(await page.evaluate(() => document.querySelector('#gl').getContext('webgl2').getError())).toBe(0);
    if (strength) await page.screenshot({ path: info.outputPath(`grain-${setting}.png`) });
    expect(errors).toEqual([]);
  });
}
test('disabling grain resumes native rendering without copies or draws', async ({ page }) => {
  await buildFixture('grain');
  const errors = watchErrors(page);
    await page.setViewportSize({ width: 640, height: 360 });
  await page.goto('/.work/grain/index.html');
  await expect.poll(() => page.evaluate(() => window.harness?.finish.state().frames)).toBeGreaterThan(3);
  await page.evaluate(() => window.harness.grain.set('strong'));
  await expect.poll(() => page.evaluate(() => window.harness.finish.state().passes)).toBeGreaterThan(3);
  const before = await page.evaluate(() => { window.harness.grain.set('off'); return window.harness.finish.state(); });
  await expect.poll(() => page.evaluate(() => window.harness.finish.state().nativeFrames)).toBeGreaterThan(before.nativeFrames + 3);
  const after = await page.evaluate(() => window.harness.finish.state());
  expect(after.copies).toBe(before.copies); expect(after.passes).toBe(before.passes);
  expect(await page.evaluate(() => window.harness.renderer.getContext().getError())).toBe(0);
  expect(errors).toEqual([]);
});
