import * as THREE from "three";
import { smoothstep } from "./lighting-math.ts";
type Road = { c: number; p: number[][] };
type Height = (x: number, z: number) => number;
type Blocked = (x: number, z: number) => boolean;
// r187 uses inverse-square falloff; this is candela, not the old r128 intensity.
const STREET_LIGHT_CANDELA = 125;
// Pure placement and schedule; never consumes the gameplay RNG.
export function streetlightLevel(solarElevation: number) {
  return smoothstep(0, 1, -solarElevation / 6);
}
export function placeStreetlights(
	roads: Road[],
	widths: number[],
	height: Height,
	blocked: Blocked,
  nearRoad: Blocked,
  halfWorld: number,
) {
	const sites: number[][] = [];
	for (const r of roads) {
		if (r.c > 2) continue;
		let remaining = 18,
			side = 1;
		for (let i = 1; i < r.p.length; i++) {
			const a = r.p[i - 1],
				b = r.p[i],
				dx = b[0] - a[0],
				dz = b[1] - a[1],
				len = Math.hypot(dx, dz);
			if (!len) continue;
			for (let d = remaining; d < len; d += 52) {
				const offset = widths[r.c] / 2 + 2.5,
					x = a[0] + (dx * d) / len - (dz / len) * offset * side,
					z = a[1] + (dz * d) / len + (dx / len) * offset * side;
				side = -side;
				if (Math.abs(x) > halfWorld - 10 || Math.abs(z) > halfWorld - 10 || blocked(x, z) || nearRoad(x, z)) continue;
				// Reject slopes and all nearby road corridors (including footpaths).
				if (
					Math.abs(height(x + 2, z) - height(x - 2, z)) > 1 ||
					Math.abs(height(x, z + 2) - height(x, z - 2)) > 1
				)
					continue;
				if (sites.some((p) => (p[0] - x) ** 2 + (p[1] - z) ** 2 < 36 ** 2))
					continue;
        sites.push([x, z]);
			}
			remaining = (((remaining - len) % 52) + 52) % 52;
		}
	}
	return sites;
}
export function createStreetLighting({
	scene,
	camera,
	roads,
	widths,
	height,
	blocked,
  nearRoad,
  halfWorld,
	coarse,
}: {
	scene: THREE.Scene;
	camera: THREE.Camera;
	roads: Road[];
	widths: number[];
	height: Height;
	blocked: Blocked;
  nearRoad: Blocked;
  halfWorld: number;
	coarse: boolean;
}) {
	const positions = placeStreetlights(roads, widths, height, blocked, nearRoad, halfWorld);
	const pole = new THREE.InstancedMesh(
		new THREE.CylinderGeometry(0.07, 0.1, 5.3, 8),
		new THREE.MeshLambertMaterial({ color: 0x616766 }),
		positions.length,
	);
	const bulbMat = new THREE.MeshLambertMaterial({
		color: 0xb7aa82,
		emissive: 0xff8e24,
		emissiveIntensity: 0,
	});
	const bulbs = new THREE.InstancedMesh(
		new THREE.BoxGeometry(0.85, 0.12, 0.32),
		bulbMat,
		positions.length,
	);
	const matrix = new THREE.Matrix4();
	const cv = document.createElement("canvas");
	cv.width = cv.height = 64;
	const ctx = cv.getContext("2d")!,
		g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
	g.addColorStop(0, "rgba(255,207,125,.65)");
	g.addColorStop(0.18, "rgba(255,162,47,.24)");
	g.addColorStop(1, "rgba(255,125,20,0)");
	ctx.fillStyle = g;
	ctx.fillRect(0, 0, 64, 64);
	const haloMat = new THREE.SpriteMaterial({
		map: new THREE.CanvasTexture(cv),
		color: 0xffb258,
		transparent: true,
		depthTest: true,
		depthWrite: false,
		opacity: 0,
	});
	const halos: THREE.Sprite[] = [];
	positions.forEach(([x, z], i) => {
		const y = height(x, z);
		matrix.makeTranslation(x, y + 2.65, z);
		pole.setMatrixAt(i, matrix);
		matrix.makeTranslation(x + 0.35, y + 5.25, z);
		bulbs.setMatrixAt(i, matrix);
		const sprite = new THREE.Sprite(haloMat);
		sprite.position.set(x + 0.35, y + 5.25, z);
		sprite.scale.set(3.4, 3.4, 1);
		scene.add(sprite);
		halos.push(sprite);
	});
	pole.material.color.convertSRGBToLinear();
	bulbMat.color.convertSRGBToLinear();
	bulbMat.emissive.convertSRGBToLinear();
	scene.add(pole, bulbs);
	// Fixed pool: no shader light-count changes while driving, no shadow maps.
	const pool = Array.from({ length: coarse ? 2 : 4 }, () => {
		const light = new THREE.PointLight(
			new THREE.Color(0xff9b32).convertSRGBToLinear(),
			0,
			26,
			2,
		);
		scene.add(light);
		return light;
	});
	const assignment = createLampPool(positions, pool.length);
  const lampHeights = positions.map(p => height(p[0], p[1]) + 4.9);
	let mode = "auto",
		level = 0,
		active = 0;
	function update(
		dt: number,
		solarElevation: number,
	) {
		const target =
			mode === "on"
				? 1
				: mode === "off"
					? 0
					: streetlightLevel(solarElevation);
		level += (target - level) * (dt === 0 ? 1 : 1 - Math.exp(-dt * 4));
		if (target === 0 && level < 0.001) level = 0;
    bulbMat.emissiveIntensity = level * 1.8;
		haloMat.opacity = level;
    assignment.update(dt, camera.position.x, camera.position.z);
    // Hide the entire bank only at fully-off; assignment never changes light
    // count, and the day/night shader variants are compiled before gameplay.
    for (let k = 0; k < pool.length; k++) {
      const light = pool[k], index = assignment.indices[k];
      light.visible = level > 0;
      light.intensity = index < 0 ? 0 : level * STREET_LIGHT_CANDELA * assignment.weights[k];
      if (index >= 0) {
        const p = positions[index];
        light.position.set(p[0] + 0.35, lampHeights[index], p[1]);
      }
    }
		active = 0;
		for (const light of pool) if (light.intensity > 0.01) active++;
		for (let i = 0; i < halos.length; i++) {
			const p = positions[i];
			halos[i].visible =
				level > 0.005 &&
				(p[0] - camera.position.x) ** 2 + (p[1] - camera.position.z) ** 2 <
					180 ** 2;
		}
	}
	return {
		update,
    prewarm(sun: THREE.DirectionalLight, compile: () => void) {
      const visible = sun.visible, castShadow = sun.castShadow;
      for (const day of [true, false]) for (const lamps of [true, false]) {
        sun.visible = sun.castShadow = day;
        for (const light of pool) light.visible = lamps;
        compile();
      }
      sun.visible = visible; sun.castShadow = castShadow;
      for (const light of pool) light.visible = level > 0;
    },
    setMode(value: string) {
			mode = value;
		},
		getMode: () => mode,
		stats: () => ({
			count: positions.length,
			budget: pool.length,
			active,
			level,
		}),
		positions,
	};
}

const POOL_RANGE_M = 85;
const POOL_HYSTERESIS_M = 12;
const POOL_FADE_SECONDS = 0.35;
// Stable nearest slots with hysteresis. A slot moves only at zero weight, then
// fades in at its new lamp. No extra dynamic lights or per-update allocations.
export function createLampPool(positions: number[][], budget: number) {
  const indices = new Int32Array(budget).fill(-1);
  const desired = new Int32Array(budget).fill(-1);
  const ranks = new Float64Array(budget);
  const fades = new Float64Array(budget);
  const weights = new Float64Array(budget);
  return { indices, weights, update(dt: number, x: number, z: number) {
    desired.fill(-1); ranks.fill(Infinity);
    for (let i = 0; i < positions.length; i++) {
      const p = positions[i], distance = Math.hypot(p[0] - x, p[1] - z);
      if (distance >= POOL_RANGE_M) continue;
      const rank = distance - (indices.includes(i) ? POOL_HYSTERESIS_M : 0);
      for (let k = 0; k < budget; k++) if (rank < ranks[k]) {
        for (let j = budget - 1; j > k; j--) { ranks[j] = ranks[j - 1]; desired[j] = desired[j - 1]; }
        ranks[k] = rank; desired[k] = i; break;
      }
    }
    const step = Math.max(0, dt) / POOL_FADE_SECONDS;
    for (let k = 0; k < budget; k++) {
      if (indices[k] >= 0 && !desired.includes(indices[k])) {
        fades[k] = Math.max(0, fades[k] - step);
        if (fades[k] === 0) indices[k] = -1;
      }
    }
    for (let k = 0; k < budget; k++) {
      if (indices[k] < 0) {
        for (const i of desired) if (i >= 0 && !indices.includes(i)) { indices[k] = i; fades[k] = 0; break; }
      }
      const i = indices[k];
      if (i >= 0 && desired.includes(i)) fades[k] = Math.min(1, fades[k] + step);
      weights[k] = i < 0 ? 0 : fades[k] * (1 - smoothstep(55, POOL_RANGE_M, Math.hypot(positions[i][0] - x, positions[i][1] - z)));
    }
  } };
}
