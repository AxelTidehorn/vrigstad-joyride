import { hash, smoothstep } from "./lighting-math";
// Approximate NOAA solar position for Vrigstad; azimuth clockwise from north.
// World axes are X east, Z south, Y up; solar angles use radians.
export const VRIGSTAD = { latitude: 57.3555, longitude: 14.4756 };
export const DEFAULT_SOLAR_DATE = "2026-08-15";
export function validSolarDate(value: unknown) {
	if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value))
		return DEFAULT_SOLAR_DATE;
	const [year, month, day] = value.split("-").map(Number);
	const d = new Date(Date.UTC(year, month - 1, day));
	return d.getUTCFullYear() === year &&
		d.getUTCMonth() === month - 1 &&
		d.getUTCDate() === day
		? value
		: DEFAULT_SOLAR_DATE;
}
let calendarKey = '';
let calendarValue = { year: 0, month: 0, day: 0, dayNumber: 0, instant: 0 };
function calendar(date: string) {
  if (date !== calendarKey) {
    calendarKey = validSolarDate(date);
    const [year, month, day] = calendarKey.split('-').map(Number);
    const instant = Date.UTC(year, month - 1, day);
    calendarValue = { year, month, day, instant, dayNumber: Math.floor((instant - Date.UTC(year, 0, 1)) / 86400000) + 1 };
  }
  return calendarValue;
}
let dstYear = 0, marchSunday = 0, octoberSunday = 0;
function euDst(year: number, month: number, day: number, hour: number) {
	if (month < 3 || month > 10) return false;
	if (month > 3 && month < 10) return true;
	if (year !== dstYear) {
    dstYear = year;
    const last = new Date(Date.UTC(year, 3, 0));
    marchSunday = last.getUTCDate() - last.getUTCDay();
    last.setTime(Date.UTC(year, 10, 0));
    octoberSunday = last.getUTCDate() - last.getUTCDay();
  }
  const lastSunday = month === 3 ? marchSunday : octoberSunday;
	return month === 3
		? day > lastSunday || (day === lastSunday && hour >= 3)
		: day < lastSunday || (day === lastSunday && hour < 3);
}
export interface SolarPosition { altitude: number; azimuth: number; dx: number; dy: number; dz: number; date: string }
export function solarPosition(
	hour: number,
	date = DEFAULT_SOLAR_DATE,
	utcOffset: number | null = null,
  out = {} as SolarPosition,
) {
  const { year, month, day, dayNumber: n } = calendar(date);
	const timezone =
		utcOffset === null ? (euDst(year, month, day, hour) ? 2 : 1) : utcOffset;
	const gamma = ((2 * Math.PI) / 365) * (n - 1 + (hour - 12) / 24);
	const eot =
		229.18 *
		(0.000075 +
			0.001868 * Math.cos(gamma) -
			0.032077 * Math.sin(gamma) -
			0.014615 * Math.cos(2 * gamma) -
			0.040849 * Math.sin(2 * gamma));
	const decl =
		0.006918 -
		0.399912 * Math.cos(gamma) +
		0.070257 * Math.sin(gamma) -
		0.006758 * Math.cos(2 * gamma) +
		0.000907 * Math.sin(2 * gamma) -
		0.002697 * Math.cos(3 * gamma) +
		0.00148 * Math.sin(3 * gamma);
	const hourAngle =
		(((hour * 60 + eot + 4 * VRIGSTAD.longitude - 60 * timezone) / 4) *
			Math.PI) /
			180 -
		Math.PI;
	const lat = (VRIGSTAD.latitude * Math.PI) / 180;
	const sine =
		Math.sin(lat) * Math.sin(decl) +
		Math.cos(lat) * Math.cos(decl) * Math.cos(hourAngle);
	const altitude = Math.asin(Math.max(-1, Math.min(1, sine)));
	const azimuth =
		(Math.atan2(
			Math.sin(hourAngle),
			Math.cos(hourAngle) * Math.sin(lat) - Math.tan(decl) * Math.cos(lat),
		) +
			3 * Math.PI) %
		(2 * Math.PI);
  out.altitude = altitude; out.azimuth = azimuth;
  out.dx = Math.sin(azimuth) * Math.cos(altitude); out.dy = Math.sin(altitude);
  out.dz = -Math.cos(azimuth) * Math.cos(altitude); out.date = calendarKey;
  return out;
}

// Seeded, smooth multi-day weather. No gameplay RNG and no per-frame state resets.
function weatherSmooth(x: number) {
	const i = Math.floor(x),
		f = x - i,
		t = smoothstep(0, 1, f);
	return hash(i, 0, 82.37, 43758.5453123) * (1 - t) + hash(i + 1, 0, 82.37, 43758.5453123) * t;
}
export function weatherCoverage(
	hour: number,
	date = DEFAULT_SOLAR_DATE,
	utcOffset: number | null = null,
) {
  const { year, month, day: dateDay, instant } = calendar(date);
  const day = instant / 86400000;
	const t =
		day +
		(hour -
			(utcOffset === null
				? euDst(year, month, dateDay, hour)
					? 2
					: 1
				: utcOffset)) /
			24;
	// Multi-day front and intra-day fluctuations; no abrupt midnight transition.
	return Math.max(
		0.04,
		Math.min(
			0.94,
			0.08 +
				0.6 * weatherSmooth(t * 0.42 + 11) +
				0.3 * weatherSmooth(t * 2.1 + 73),
		),
	);
}
export interface DaylightState extends SolarPosition {
  hour: number; daytime: number; warm: number; cover: number; shade: number;
  strength: number; exposure: number; skyBrightness: number; twilight: number;
}
// Solar direction is geographic; exposure, clouds and tint are artistic.
export function daylightState(
	hour: number,
	coverage: number | null = null,
	date = DEFAULT_SOLAR_DATE,
	utcOffset: number | null = null,
  out = {} as DaylightState,
) {
	const h = ((hour % 24) + 24) % 24;
	const solar = solarPosition(h, date, utcOffset, out);
	const altitude = solar.altitude;
	const elevation = (altitude * 180) / Math.PI;
	const daytime = Math.max(0, Math.min(1, elevation / 16));
	const warm = Math.max(0, Math.min(1, (35 - elevation) / 29));
	const cover =
		coverage === null
			? weatherCoverage(h, date, utcOffset)
			: Math.max(0, Math.min(1, coverage));
	// Broad cloud shadows: coherent across the entire scene; not a weather model.
	// Cloud cover also attenuates direct sun and glare, not just sky colour.
	const shade = Math.max(0.3, 1 - cover * 0.82);
	// Twilight keeps residual skylight after direct sun fades; actual night
	// still requires headlights and street lamps, not artificial daylight.
	const twilight = Math.max(0, Math.min(1, (elevation + 9) / 12));
  out.hour = h; out.daytime = daytime; out.warm = warm; out.cover = cover; out.shade = shade;
  out.strength = daytime * (1.44 - 0.48 * warm) * shade;
  out.exposure = 0.69 + 0.3 * daytime - 0.11 * warm + 0.03 * (1 - shade);
  out.skyBrightness = Math.max(0.15, (0.25 + 0.75 * daytime) * (1 - 0.27 * warm));
  out.twilight = twilight;
  return out;
}
// Absolute UTC-based solar clock presented in Stockholm civil time.
// Input is Stockholm civil time. A repeated autumn hour chooses the first
// occurrence; a nonexistent spring hour normalizes forward. Advancing thereafter
// uses UTC instants, so solar direction is continuous through DST transitions.
export function createSolarClock(date = DEFAULT_SOLAR_DATE, hour = 15.5) {
	const utc = new Date(0),
		local = new Date(0);
	let instant = 0,
		offset = 1,
		currentDate = "",
		currentHour = 0,
		cacheYear = 0,
		start = 0,
		end = 0,
    cachedDay = NaN;
	function sync() {
		utc.setTime(instant);
		const year = utc.getUTCFullYear();
		if (year !== cacheYear) {
			cacheYear = year;
			utc.setTime(Date.UTC(year, 3, 0));
			const march = utc.getUTCDate() - utc.getUTCDay();
			utc.setTime(Date.UTC(year, 10, 0));
			const october = utc.getUTCDate() - utc.getUTCDay();
			start = Date.UTC(year, 2, march, 1);
			end = Date.UTC(year, 9, october, 1);
		}
		offset = instant >= start && instant < end ? 2 : 1;
		local.setTime(instant + offset * 3600000);
		const dayInstant = Math.floor((instant + offset * 3600000) / 86400000);
    if (dayInstant !== cachedDay) { cachedDay = dayInstant; currentDate = local.toISOString().slice(0, 10); }
		currentHour =
			local.getUTCHours() +
			local.getUTCMinutes() / 60 +
			local.getUTCSeconds() / 3600 +
			local.getUTCMilliseconds() / 3600000;
	}
	function set(value: string, h: number) {
		const valid = validSolarDate(value),
			[year, month, day] = valid.split("-").map(Number),
			hours = Number.isFinite(h) ? ((h % 24) + 24) % 24 : 15.5;
		instant =
			Date.parse(valid + "T00:00:00Z") +
			(hours - (euDst(year, month, day, hours) ? 2 : 1)) * 3600000;
		sync();
	}
	set(date, hour);
	return {
		set,
		advanceHours(h: number) {
			instant += h * 3600000;
			sync();
		},
		getHour: () => currentHour,
		getDate: () => currentDate,
		getOffset: () => offset,
		getInstant: () => instant,
	};
}
