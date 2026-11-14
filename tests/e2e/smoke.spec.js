// Smoke tests for the built pages. They assert on the DOM and on the window.__joyride test hook, never on pixels:
// headless WebGL output varies between machines. The screenshots are attached for humans to look at.
import { test, expect } from '@playwright/test';

// Collects console errors and uncaught exceptions from the moment the page starts loading.
function watchErrors(page) {
  const errors = [];
  page.on('console', m => {
    if (m.type() !== 'error') return;
    // A CDN or font outage is not our bug; failed loads from our own origin still count.
    const url = m.location().url;
    if (m.text().startsWith('Failed to load resource') && url && new URL(url).origin !== new URL(page.url()).origin) return;
    errors.push(m.text());
  });
  page.on('pageerror', e => errors.push(String(e)));
  return errors;
}

// True when the page itself gave #gl a WebGL context. A canvas keeps one context type for life, so asking for '2d'
// returns null only if a WebGL context already exists. (Asking for 'webgl' here would create one and always pass.)
async function expectWebGL(page) {
  await expect(page.locator('#fail')).toBeHidden();
  expect(await page.evaluate(() => document.getElementById('gl').getContext('2d'))).toBeNull();
}

const state = page => page.evaluate(() => window.__joyride.state());

test.describe('game (index.html)', () => {
  test('loads with no console errors and a WebGL canvas', async ({ page }, testInfo) => {
    const errors = watchErrors(page);
    await page.goto('/index.html');
    await expect(page.locator('#intro')).toBeVisible();
    await expectWebGL(page);
    expect(await state(page)).toMatchObject({ started: false, inCar: false });
    await page.screenshot({ path: testInfo.outputPath('game-intro.png') });
    expect(errors).toEqual([]);
  });

  test('Start hides the intro and shows the HUD', async ({ page }) => {
    const errors = watchErrors(page);
    await page.goto('/index.html');
    await expect(page.locator('#intro')).toBeVisible();                 // covers the whole view, HUD included
    expect(await state(page)).toMatchObject({ started: false });

    await page.locator('#go').click();
    await expect(page.locator('#intro')).toBeHidden();
    expect(await state(page)).toMatchObject({ started: true });
    await expect(page.locator('#toast')).toContainText('Find a car');   // only Start shows this
    await expect(page.locator('#sign')).toBeVisible();
    await expect(page.locator('#street')).toContainText('Torget');
    await expect(page.locator('#stars')).toHaveText('★★★');
    await expect(page.locator('#stars b')).toHaveCount(0);              // <b> is a lit star: none when not wanted
    await expect(page.locator('#mini')).toBeVisible();
    expect(errors).toEqual([]);
  });

  test('W moves the player, and E next to a parked showcase car gets you in', async ({ page }, testInfo) => {
    const errors = watchErrors(page);
    await page.goto('/index.html');
    await page.locator('#go').click();
    const from = await state(page);
    expect(from).toMatchObject({ started: true, inCar: false, car: null });

    await page.keyboard.down('KeyW');
    await expect.poll(async () => { const s = await state(page); return Math.hypot(s.x - from.x, s.z - from.z); }).toBeGreaterThan(1);
    await page.keyboard.up('KeyW');
    await page.keyboard.press('KeyR');                            // back to the spawn point at Torget

    // The Torget showcase replaces the old fixed starter Volvo position.
    // Release D as soon as a car is in reach so slow runners do not walk past it.
    await page.keyboard.down('KeyD');
    await expect.poll(async () => (await state(page)).near, { intervals: [50] }).not.toBeNull();
    await page.keyboard.up('KeyD');
    // Verify a parked car is available, without hard-coding which showcase
    // vehicle happens to be nearest after collision-aware placement.
    await expect.poll(async () => (await state(page)).near).toBe('parked');
    const prompt = page.locator('#prompt');
    await expect(prompt).toContainText('Steal the ');
    const carName = (await prompt.textContent()).replace(/^E\s*Steal the\s*/, '').trim();
    expect(carName).not.toBe('');
    await page.keyboard.press('KeyE');

    await expect(page.locator('#speed')).toBeVisible();
    await expect(page.locator('#carname')).toHaveText(carName);
    const entered = await state(page);
    expect(entered).toMatchObject({ inCar: true, drivetrain: 'v4' });
    expect(entered.car).toBeTruthy();
    // Stealing a parked car has an intentional 35% witness probability.
    expect([0, 1]).toContain(entered.stars);
    await page.screenshot({ path: testInfo.outputPath('game-in-showcase-car.png') });

    // Exercise the actual gameplay input path, not only the standalone engine.
    await expect.poll(async () => (await state(page)).gear).toBe('1');
    await expect(page.locator('#gear')).toHaveText('AUTO 1');
    await page.keyboard.down('KeyW');
    try {
      await expect.poll(async () => Number(await page.locator('#kmh').textContent()),
        { timeout: 20000, intervals: [100] }).toBeGreaterThan(2);
    } finally {
      await page.keyboard.up('KeyW');
    }
    expect(errors).toEqual([]);
  });

  test('cats are around, and the kiosk sells cat treats from its menu', async ({ page }, testInfo) => {
    const errors = watchErrors(page);
    await page.goto('/index.html');
    await page.locator('#go').click();
    await expect.poll(async () => (await state(page)).cats).toBeGreaterThan(0);   // Torget is built-up, so cats spawn at once
    expect(await state(page)).toMatchObject({ treats: 0 });

    // With the camera as Start leaves it, the kiosk lucka is about 4.6 m to the player's left.
    await page.keyboard.down('KeyA');
    await expect.poll(async () => page.locator('#prompt').textContent(), { intervals: [50] }).toBe('EHandla i kiosken');
    await page.keyboard.up('KeyA');

    await page.keyboard.press('KeyE');
    await expect(page.locator('#kmenu')).toBeVisible();
    await page.screenshot({ path: testInfo.outputPath('game-kiosk-menu.png') });
    await page.keyboard.press('Digit2');
    await expect(page.locator('#kmenu')).toBeHidden();
    await expect(page.locator('#treats')).toHaveText('Cat treats: 3');
    expect(await state(page)).toMatchObject({ treats: 3 });

    await page.keyboard.press('KeyE');
    await expect(page.locator('#kmenu')).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.locator('#kmenu')).toBeHidden();
    expect(await state(page)).toMatchObject({ treats: 3 });
    expect(errors).toEqual([]);
  });
});

test.describe('map (map.html)', () => {
  test('loads with no console errors and draws the map', async ({ page }, testInfo) => {
    const errors = watchErrors(page);
    await page.goto('/map.html');
    await expectWebGL(page);
    // A place label only gets a screen position once a frame has been drawn with the camera.
    await expect(page.locator('#labels .lbl', { hasText: /^Torget$/ })).toHaveAttribute('style', /translate/);
    await page.screenshot({ path: testInfo.outputPath('map.png') });
    expect(errors).toEqual([]);
  });
});
