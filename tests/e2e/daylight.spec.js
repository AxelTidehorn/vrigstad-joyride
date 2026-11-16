import { test, expect } from '@playwright/test';

const daylight = page => page.evaluate(() => window.__joyride?.state().daylight);

async function openScene(page, query) {
  await page.setViewportSize({ width: 640, height: 360 });
  await page.goto('/index.html?' + query, { waitUntil: 'domcontentloaded' });
  await expect.poll(async () => (await daylight(page))?.enabled).toBe(true);
}

async function captureScene(page, info, name) {
  await page.locator('#go').click();
  await expect(page.locator('#intro')).toBeHidden();
  // Hide the HUD only in the screenshot, so reviewers can inspect lighting without overlays.
  await page.locator('#ui').evaluate(element => { element.style.visibility = 'hidden'; });
  await page.screenshot({ path: info.outputPath(name), animations: 'disabled' });
}

test('midsummer daylight has a high southern sun and live shadows', async ({ page }, info) => {
  await openScene(page, 'time=13&date=2026-06-21');
  await expect.poll(async () => (await daylight(page))?.sunStrength).toBeGreaterThan(0);
  const s = await daylight(page);
  expect(s.cycle).toBe(false);
  expect(s.elevation).toBeGreaterThan(54);
  expect(s.sunVisible).toBe(true);
  expect(s.sunCastShadow).toBe(true);
  await captureScene(page, info, 'daylight-summer.png');
});

test('winter daylight uses the real low December sun', async ({ page }, info) => {
  await openScene(page, 'time=13&date=2026-12-21');
  await expect.poll(async () => (await daylight(page))?.sunStrength).toBeGreaterThan(0);
  const s = await daylight(page);
  expect(s.elevation).toBeGreaterThan(8);
  expect(s.elevation).toBeLessThan(12);
  expect(s.sunVisible).toBe(true);
  await captureScene(page, info, 'daylight-winter.png');
});

test('evening colour is available for deliberate review without an automatic cycle', async ({ page }, info) => {
  await openScene(page, 'time=20.5&date=2026-08-15');
  const s = await daylight(page);
  expect(s.hour).toBeCloseTo(20.5, 1);
  expect(s.cycle).toBe(false);
  await captureScene(page, info, 'daylight-evening.png');
});

test('night has no below-horizon directional sun or shadow pass', async ({ page }, info) => {
  await openScene(page, 'time=23&date=2026-08-15');
  await expect.poll(async () => (await daylight(page))?.sunVisible).toBe(false);
  const s = await daylight(page);
  expect(s.sunStrength).toBe(0);
  expect(s.sunCastShadow).toBe(false);
  await captureScene(page, info, 'daylight-night-unlit.png');
});

test('lighting=off preserves the original scene path', async ({ page }) => {
  await page.setViewportSize({ width: 640, height: 360 });
  await page.goto('/index.html?lighting=off', { waitUntil: 'domcontentloaded' });
  await expect.poll(async () => (await daylight(page))?.enabled).toBe(false);
  const native = await daylight(page);
  expect(native.sunVisible).toBe(true);
  expect(native.sunCastShadow).toBe(true);
  expect(await page.evaluate(() => document.querySelector('#gl').getContext('webgl2').getError())).toBe(0);
});
