import { describe, expect, it } from 'vitest';
import { createSolarClock, daylightState, solarPosition, validSolarDate, weatherCoverage } from '../../src/game/render/solar-clock';

const deg = (radians: number) => radians * 180 / Math.PI;

describe('geographic daylight in Vrigstad', () => {
  it('keeps the Swedish summer/winter sun geometry and compass directions', () => {
    const summer = solarPosition(13, '2026-06-21');
    const winter = solarPosition(12, '2026-12-21');
    expect(deg(summer.altitude)).toBeGreaterThan(54);
    expect(deg(summer.altitude)).toBeLessThan(58);
    expect(deg(winter.altitude)).toBeGreaterThan(8);
    expect(deg(winter.altitude)).toBeLessThan(11);
    expect(summer.dz).toBeGreaterThan(0); // south is +Z
    expect(solarPosition(8, '2026-08-15').dx).toBeGreaterThan(0);
    expect(solarPosition(19, '2026-08-15').dx).toBeLessThan(0);
  });

  it('keeps Stockholm DST, civil date rollover and invalid date handling', () => {
    const spring = createSolarClock('2026-03-29', 1.99);
    spring.advanceHours(0.02);
    expect(spring.getHour()).toBeGreaterThan(3);
    expect(spring.getHour()).toBeLessThan(3.02);
    const autumn = createSolarClock('2026-10-25', 2.99);
    autumn.advanceHours(0.02);
    expect(autumn.getHour()).toBeGreaterThan(2);
    expect(autumn.getHour()).toBeLessThan(2.02);
    const end = createSolarClock('2026-12-31', 23.99);
    end.advanceHours(0.02);
    expect(end.getDate()).toBe('2027-01-01');
    expect(validSolarDate('2026-02-30')).toBe('2026-08-15');
  });

  it('never illuminates from below the horizon and crosses dawn/dusk smoothly', () => {
    for (const date of ['2026-06-21', '2026-08-15', '2026-12-21']) {
      const reused = daylightState(0, 0, date);
      let previous = 0;
      for (let hour = 0; hour < 24; hour += 1 / 60) {
        const current = daylightState(hour, 0, date, null, reused);
        expect(current).toBe(reused);
        if (current.dy <= 0) expect(current.strength).toBe(0);
        expect(Math.abs(current.strength - previous)).toBeLessThan(0.03);
        previous = current.strength;
      }
    }
  });

  it('keeps weather bounded, changing and continuous across midnight', () => {
    for (let hour = 0; hour < 24; hour += 0.5) {
      const cover = weatherCoverage(hour, '2026-08-15');
      expect(cover).toBeGreaterThanOrEqual(0);
      expect(cover).toBeLessThanOrEqual(1);
    }
    expect(Math.abs(weatherCoverage(23.999, '2026-08-15') - weatherCoverage(0, '2026-08-16'))).toBeLessThan(0.002);
    expect(Math.abs(weatherCoverage(12, '2026-08-15') - weatherCoverage(12, '2026-08-18'))).toBeGreaterThan(0.001);
  });

  it('supports the same output object across updates and sunlight is disabled at night', () => {
    const output = daylightState(13, 0.2, '2026-08-15');
    const updated = daylightState(23, 0.8, '2026-08-15', null, output);
    expect(updated).toBe(output);
    expect(updated.strength).toBe(0);
    expect(updated.exposure).toBeLessThan(daylightState(13).exposure);
  });
});
