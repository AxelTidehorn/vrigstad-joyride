import { test, expect } from '@playwright/test';
import { createRequire } from 'node:module';
import { readFileSync } from 'node:fs';
import { watchErrors } from './render-helpers.js';
const require = createRequire(import.meta.url);
test('trailer capture builds and stages a car with the shipped render path', async ({ page }) => {
  const { buildCaptureCopy } = require('../../tools/trailer/rig.js');
  await buildCaptureCopy();
  const errors = watchErrors(page);
  await page.setViewportSize({ width: 640, height: 360 });
  await page.goto('/tools/trailer/.work/index.html?grain=strong&film=negative');
  await page.waitForFunction(() => window.__G && window.__joyride);
  await page.evaluate(readFileSync('tools/trailer/inpage.js', 'utf8'));
  const result = await page.evaluate(() => {
    const car = window.__X.makeCar('volvo', '#27406b', 0, 0, 0);
    window.__X.recolor(car, 'volvo', '#7a2530');
    window.__G.removeCar(car);
    return window.__joyride.state();
  });
  expect(result.started).toBe(false);
  expect(await page.evaluate(() => window.__G.renderer.getContext().getError())).toBe(0);
  expect(errors).toEqual([]);
});
