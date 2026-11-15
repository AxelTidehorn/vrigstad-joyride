import * as THREE from "three";
import { noise2, smoothstep } from "./lighting-math.ts";
import { LEGACY_LIGHT } from "../../world/three-legacy";
import {
	createSolarClock,
	daylightState,
	validSolarDate,
} from "./solar-clock";
interface DaylightContext {
	sun: THREE.DirectionalLight;
	hemi: THREE.HemisphereLight;
	renderer: THREE.WebGLRenderer;
	scene: THREE.Scene & { fog: THREE.FogExp2; background: THREE.Color };
	dome: THREE.Mesh<THREE.SphereGeometry, THREE.ShaderMaterial>;
	SUN_DIR: THREE.Vector3;
	col: (value: number) => THREE.Color;
}
export function createDaylightController({
	sun,
	hemi,
	renderer,
	scene,
	dome,
	SUN_DIR,
	col,
}: DaylightContext) {
	const params = new URLSearchParams(location.search);
	let enabled = params.get("lighting") !== "off";
	const initialEnabled = enabled,
		original = {
			sun: sun.intensity,
			hemi: hemi.intensity,
			exposure: renderer.toneMappingExposure,
			sunColor: sun.color.clone(),
			hemiColor: hemi.color.clone(),
			fog: scene.fog.color.clone(),
			background: scene.background.clone(),
			direction: SUN_DIR.clone(),
			top: dome.material.uniforms.top.value.clone(),
			hor: dome.material.uniforms.hor.value.clone(),
			sunC: dome.material.uniforms.sunC.value.clone(),
		};
	const initial = {
		hour:
			params.has("time") && Number.isFinite(Number(params.get("time")))
				? ((Number(params.get("time")) % 24) + 24) % 24
				: 15.5,
		date: validSolarDate(params.get("date")),
    cycle: params.get('cycle') === 'on',
	};
	const clock = createSolarClock(initial.date, initial.hour);
	let hour = clock.getHour(),
		date = clock.getDate(),
		cycle = initial.cycle,
		glare = 1,
		elapsed = 0,
		occlusion = 1;
	let cloudOverride: number | null = null;
  const state = daylightState(hour, cloudOverride, date, clock.getOffset());
	const speed = Math.max(
		0.01,
		Math.min(5, Number(params.get("daySpeed")) || 1),
	);
	const vector = new THREE.Vector3(),
		ambient = col(0xc8d9ed),
		cold = col(0xfff4dd),
		warm = col(0xff8e38),
		topDay = new THREE.Color(0x5f97c9),
		topDusk = new THREE.Color(0xb66b72),
		topNight = new THREE.Color(0x122137),
		horDay = new THREE.Color(0xd6e4e6),
		horDusk = new THREE.Color(0xe99a68),
		horNight = new THREE.Color(0x1d3046);
	function update(dt: number) {
		if (!enabled) return;
		elapsed += dt;
		if (cycle) {
			clock.advanceHours((dt * speed) / 30);
			hour = clock.getHour();
			date = clock.getDate();
		}
		if (cycle || dt === 0) daylightState(hour, cloudOverride, date, clock.getOffset(), state);
		vector.set(state.dx, state.dy, state.dz);
		SUN_DIR.copy(vector);
		sun.position.copy(sun.target.position).addScaledVector(vector, 400);
		const scale = 1.7 / Math.max(0.18, vector.y + 0.23),
			x = vector.x * scale + elapsed * 0.0025,
			z = vector.z * scale;
		const layer =
			0.62 * noise2(x, z) +
			0.27 * noise2(x * 2.3, z * 2.3) +
			0.11 * noise2(x * 4.9, z * 4.9);
		const cover =
			smoothstep(0.59 - state.cover * 0.26, 0.77 - state.cover * 0.15, layer) *
			smoothstep(-0.08, 0.19, vector.y) *
			(state.cover > 0.01 ? 1 : 0);
		occlusion += (1 - cover * 0.7 - occlusion) * (1 - Math.exp(-dt * 2));
		sun.intensity = state.strength * occlusion * LEGACY_LIGHT;
    sun.visible = sun.intensity > 0;
    sun.castShadow = sun.visible;
		sun.color.copy(cold).lerp(warm, state.warm);
		hemi.intensity =
			(0.07 + 0.4 * state.daytime + 0.13 * state.twilight) * LEGACY_LIGHT;
		hemi.color.copy(ambient).lerp(warm, state.warm * 0.25);
		renderer.toneMappingExposure = state.exposure;
		const u = dome.material.uniforms;
		u.top.value
			.copy(topDay)
			.lerp(topDusk, state.warm * 0.8)
			.lerp(topNight, 1 - state.daytime);
		u.hor.value
			.copy(horDay)
			.lerp(horDusk, state.warm * 0.8)
			.lerp(horNight, 1 - state.daytime);
		u.sunC.value.setRGB(1, 0.88 - 0.3 * state.warm, 0.73 - 0.5 * state.warm);
		u.daylight.value = 1;
		u.skyBrightness.value = state.skyBrightness * (1 - state.cover * 0.1);
		u.coverage.value = state.cover;
		u.cloudTime.value = elapsed * 0.0025;
		u.glare.value = glare;
		u.warm.value = state.warm;
		scene.fog.color.copy(u.hor.value).multiplyScalar(u.skyBrightness.value);
		scene.background.copy(scene.fog.color);
	}
	return {
		get enabled() {
			return enabled;
		},
		update,
		getHour: () => hour,
		getDate: () => date,
		getCycle: () => cycle,
    getCoverage: () => enabled ? state.cover : 0,
    getGlare: () => glare,
    getSolarElevation: () => state.altitude * 180 / Math.PI,
		setHour(v: number) {
			enabled = true;
			clock.set(date, v);
			hour = clock.getHour();
			date = clock.getDate();
			cycle = false;
			update(0);
		},
		setDate(v: string) {
			enabled = true;
			clock.set(v, hour);
			date = clock.getDate();
			hour = clock.getHour();
			update(0);
		},
		setCycle(v: boolean) {
			enabled = true;
			cycle = v;
      update(0);
		},
		setCoverage(v: number | null) {
      enabled = true;
			cloudOverride = v === null ? null : Math.max(0, Math.min(1, v));
			update(0);
		},
		setGlare(v: number) {
      enabled = true;
			glare = Math.max(0, Math.min(3, v));
			update(0);
		},
		reset() {
			enabled = initialEnabled;
			clock.set(initial.date, initial.hour);
			hour = clock.getHour();
			date = clock.getDate();
			cycle = initial.cycle;
			cloudOverride = null;
			glare = 1;
			daylightState(hour, cloudOverride, date, clock.getOffset(), state);
      if (enabled) update(0);
			else {
				SUN_DIR.copy(original.direction);
				sun.position.copy(sun.target.position).addScaledVector(SUN_DIR, 400);
				sun.intensity = original.sun;
        sun.visible = true; sun.castShadow = true;
				sun.color.copy(original.sunColor);
				hemi.intensity = original.hemi;
				hemi.color.copy(original.hemiColor);
				renderer.toneMappingExposure = original.exposure;
				scene.fog.color.copy(original.fog);
				scene.background.copy(original.background);
				const u = dome.material.uniforms;
				u.top.value.copy(original.top);
				u.hor.value.copy(original.hor);
				u.sunC.value.copy(original.sunC);
				u.daylight.value = 0;
			}
		},
		state: () => ({
			enabled,
			hour,
			date,
			cycle,
      coverage: enabled ? state.cover : 0,
      glare: enabled ? glare : 1,
      sunStrength: sun.intensity,
      sunVisible: sun.visible,
      sunCastShadow: sun.castShadow,
      sunDirectionY: SUN_DIR.y,
      exposure: renderer.toneMappingExposure,
      elevation: state.altitude * 180 / Math.PI,
		}),
	};
}
