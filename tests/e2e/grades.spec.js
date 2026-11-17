import { test, expect } from '@playwright/test';

test('Classic Negative renders after the scene and off bypasses the grade', async ({ page }, info) => {
  const errors = [];
  page.on('console', message => {
    if (message.type() === 'error' && !message.text().startsWith('Failed to load resource')) errors.push(message.text());
  });
  page.on('pageerror', error => errors.push(String(error)));
  await page.setViewportSize({ width: 640, height: 360 });
  for (const profile of ['negative', 'off', 'unknown']) {
    await page.goto('/index.html?film=' + profile);
    await expect.poll(() => page.evaluate(() => window.__joyride?.state().rendering.frames)).toBeGreaterThan(3);
    const state = await page.evaluate(() => window.__joyride.state());
    expect(state.film).toMatchObject({ setting: profile, preset: profile === 'negative' ? 'negative' : 'off', enabled: profile === 'negative' });
    if (profile === 'negative') {
      expect(state.rendering.copies).toBeGreaterThan(0);
      expect(state.rendering.passes).toBe(state.rendering.copies);
      expect(state.film.parameters.foliageReach).toBe(1);
    } else expect(state.rendering.copies).toBe(0);
    expect(await page.evaluate(() => document.querySelector('#gl').getContext('webgl2').getError())).toBe(0);
    await page.screenshot({ path: info.outputPath(profile + '.png') });
  }
  expect(errors).toEqual([]);
});
