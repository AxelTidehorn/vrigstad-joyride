import { test, expect } from '@playwright/test';

const daylight = page => page.evaluate(() => window.__joyride?.state().daylight);

async function captureScene(page, info, filename) {
  // Capture the actual playable scene; the intro card would obscure the lighting.
  await page.locator('#go').click();
  await expect(page.locator('#intro')).toBeHidden();
  await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
  await page.screenshot({ path: info.outputPath(filename) });
}

test('geographic daylight preserves daytime, winter, dusk, night shadows and native bypass', async ({ page }, info) => {
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  await page.setViewportSize({ width: 640, height: 360 });

  await page.goto('/index.html?time=13&date=2026-06-21');
  await expect.poll(async () => (await daylight(page))?.sunStrength).toBeGreaterThan(0);
  const summer = await daylight(page);
  expect(summer.cycle).toBe(false);
  expect(summer.elevation).toBeGreaterThan(54);
  expect(summer.sunVisible).toBe(true);
  expect(summer.sunCastShadow).toBe(true);
  await captureScene(page, info, 'daylight-summer.png');

  await page.goto('/index.html?time=13&date=2026-12-21');
  await expect.poll(async () => (await daylight(page))?.elevation).toBeGreaterThan(8);
  const winter = await daylight(page);
  expect(winter.elevation).toBeLessThan(12);
  expect(winter.sunVisible).toBe(true);
  await captureScene(page, info, 'daylight-winter.png');

  await page.goto('/index.html?time=20.5&date=2026-08-15');
  await expect.poll(async () => (await daylight(page))?.date).toBe('2026-08-15');
  await captureScene(page, info, 'daylight-evening.png');

  await page.goto('/index.html?time=23&date=2026-08-15');
  await expect.poll(async () => (await daylight(page))?.sunVisible).toBe(false);
  const night = await daylight(page);
  expect(night.sunStrength).toBe(0);
  expect(night.sunCastShadow).toBe(false);
  await captureScene(page, info, 'daylight-night-unlit.png');

  await page.goto('/index.html?lighting=off');
  await expect.poll(async () => (await daylight(page))?.enabled).toBe(false);
  const native = await daylight(page);
  expect(native.sunVisible).toBe(true);
  expect(native.sunCastShadow).toBe(true);
  expect(await page.evaluate(() => document.querySelector('#gl').getContext('webgl2').getError())).toBe(0);
  expect(errors).toEqual([]);
});
