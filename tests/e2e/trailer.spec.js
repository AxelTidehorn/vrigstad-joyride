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

test('all four GLBs load and animate in trailer staging', async ({ page }, info) => {
  const { buildCaptureCopy } = require('../../tools/trailer/rig.js');
  await buildCaptureCopy();
  const errors = watchErrors(page);
  await page.setViewportSize({ width: 640, height: 360 });
  await page.goto('/tools/trailer/.work/index.html');
  await page.waitForFunction(() => window.__G);
  await page.evaluate(() => {
    const G = window.__G;
    window.staged = ['volvo', 'saab', 'xc70', 'polis'].map((type, i) => G.addCar(type, G.player.x + 5 + i * 3, G.player.z, 0, 'parked'));
  });
  await expect.poll(() => page.evaluate(() => window.staged.filter(c => c.assetType).length)).toBe(4);
  const states = await page.evaluate(() => window.staged.map(c => {
    const G = window.__G;
    const before = c.assetWheels[0].spin.rotation.x;
    c.x += 1; c.h = 0.2; G.placeCar(c);
    return { type: c.type, wheels: c.assetWheels.length, spun: c.assetWheels[0].spin.rotation.x !== before, steered: c.assetWheels[0].steer.rotation.y !== 0 };
  }));
  for(const state of states) expect(state).toMatchObject({ wheels:4, spun:true, steered:true });
  await page.screenshot({path:info.outputPath('four-vehicle-fleet.png')});
  expect(await page.evaluate(() => window.__G.renderer.getContext().getError())).toBe(0);
  expect(errors).toEqual([]);
});
