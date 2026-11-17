import { test, expect } from '@playwright/test';

for (const theme of ['light', 'dark']) test(`managed map renders in ${theme} theme`, async ({ page }, info) => {
  const errors = [];
  page.on('pageerror', error => errors.push(String(error)));
  await page.setViewportSize({ width: 640, height: 360 });
  await page.emulateMedia({ colorScheme: theme });
  await page.goto('/map.html');
  await expect(page.locator('#labels .lbl', { hasText: /^Torget$/ })).toHaveAttribute('style', /translate/);
  expect(await page.evaluate(() => document.querySelector('#gl').getContext('webgl2').getError())).toBe(0);
  await page.screenshot({ path: info.outputPath('map-' + theme + '.png') });
  expect(errors).toEqual([]);
});
