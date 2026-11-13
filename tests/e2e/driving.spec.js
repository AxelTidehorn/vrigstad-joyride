import {test, expect} from '@playwright/test';

test('V4 player can enter, accelerate, and use automatic gear', async ({page}) => {
  const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  await page.goto('/index.html');
  await page.locator('#go').click();
  await page.keyboard.down('KeyD');
  await expect.poll(() => page.evaluate(() => window.__joyride.state().near),
    {intervals:[50],timeout:10000}).toBe('parked');
  await page.keyboard.up('KeyD');
  await page.keyboard.press('KeyE');
  await expect.poll(() => page.evaluate(() => window.__joyride.state().inCar)).toBe(true);
  await expect.poll(() => page.evaluate(() => window.__joyride.state().gear)).toBe('1');
  expect(await page.evaluate(() => window.__joyride.state().drivetrain)).toBe('v4');
  await expect(page.locator('#gear')).toHaveText('AUTO 1');
  await page.keyboard.down('KeyW');
  await expect.poll(async () => Number(await page.locator('#kmh').textContent()),
    {intervals:[100],timeout:12000}).toBeGreaterThan(2);
  await page.keyboard.up('KeyW');
  await expect(page.locator('#speed')).toBeVisible();
  expect(errors).toEqual([]);
});
