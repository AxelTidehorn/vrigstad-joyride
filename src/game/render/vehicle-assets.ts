import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

interface Wheel { steer: THREE.Group; spin: THREE.Group; front: boolean }
interface VehicleVisual {
  mesh: THREE.Group;
  assetType?: string;
  assetDetailed?: boolean;
  visual?: THREE.Group;
  assetFallback?: THREE.Mesh;
  assetWheels?: Wheel[];
  assetBeacons?: THREE.MeshStandardMaterial[];
  assetMaterials?: Set<THREE.Material>;
  assetWheelRadius?: number;
  assetWheelTravel: number;
  visualSteer?: number;
}
export const VEHICLE_ASSETS = Object.freeze({
  volvo: { url: 'media/vehicles/volvo240.glb', radius: 0.35 },
  saab: { url: 'media/vehicles/saab900-t16.glb', radius: 0.35 },
  xc70: { url: 'media/vehicles/xc70-civilian.glb', radius: 0.345 },
  polis: { url: 'media/vehicles/xc70-police.glb', radius: 0.345 }
});
export function createVehicleAssets() {
  const cache = new Map<string, Promise<THREE.Group | null>>();
  const revisions = new WeakMap<VehicleVisual, number>();
  function preload(type: string) {
    const info = VEHICLE_ASSETS[type as keyof typeof VEHICLE_ASSETS];
    if (!info) return null;
    if (!cache.has(type)) {
      cache.set(type, new Promise<THREE.Group>((resolve, reject) => {
        new GLTFLoader().load(info.url, result => resolve(result.scene), undefined, reject);
      }).catch(error => {
        console.warn('GLB loading failed; retaining original vehicle:', type, error);
        return null;
      }));
    }
    return cache.get(type);
  }
  function install(car: VehicleVisual, type: string, fallback: THREE.Mesh, paint: string) {
    const revision = (revisions.get(car) ?? 0) + 1; revisions.set(car, revision);
    const spec = VEHICLE_ASSETS[type as keyof typeof VEHICLE_ASSETS];
    if (!spec) return;
    const task = preload(type);
    if (!task) return;
    task.then(template => {
      if (!template || !car.mesh.parent || car.assetType || revisions.get(car) !== revision) return;
      const visual = template.clone(true);
      const materials = new Set<THREE.Material>();
      // One paint colour per car, not per shared GLB. Only recolour civilian
      // body paint: leave glass, trim, wheels, lamps and police livery intact.
      if (type !== 'polis' && paint) {
        visual.traverse(node => {
          if (node.name !== 'body' || !(node instanceof THREE.Mesh)) return;
          const recolour = (material: THREE.MeshStandardMaterial) => {
            const instance = material.clone();
            instance.color.set(paint).convertSRGBToLinear();
            materials.add(instance);
            return instance;
          };
          node.material = Array.isArray(node.material)
            ? node.material.map(recolour) : recolour(node.material);
        });
      }
      // Separate wheels from the body rig so body roll and pitch do not tilt
      // their contact patches. Their GLB mesh origins are the hub centres.
      visual.updateMatrixWorld(true);
      const wheelNodes: THREE.Object3D[] = [];
      visual.traverse(node => {
        if (/^wheel_(fl|fr|rl|rr)$/.test(node.name)) wheelNodes.push(node);
      });
      const wheels: Wheel[] = [];
      for (const node of wheelNodes) {
        const hub = new THREE.Vector3(), orientation = new THREE.Quaternion();
        node.getWorldPosition(hub);
        node.getWorldQuaternion(orientation);
        node.parent!.remove(node);
        const steer = new THREE.Group(), spin = new THREE.Group();
        steer.position.copy(hub);
        node.position.set(0, 0, 0);
        node.quaternion.copy(orientation);
        spin.add(node);
        steer.add(spin);
        car.mesh.add(steer);
        wheels.push({ steer, spin, front: /^wheel_f/.test(node.name) });
      }
      const beacons: THREE.MeshStandardMaterial[] = [];
      visual.traverse(node => {
        if (!(node instanceof THREE.Mesh)) return;
        node.castShadow = true;
        node.receiveShadow = true;
        if (/^lamp_(blue_module|police_grille)/.test(node.name)) {
          // Each police car needs its own emissive material state.
          node.material = node.material.clone();
          node.material.emissive = new THREE.Color('#176cff').convertSRGBToLinear();
          node.material.emissiveIntensity = 0;
          beacons.push(node.material);
          materials.add(node.material);
        }
      });
      visual.position.y = 0; // Original rendering pivot: GLB geometry is Y-up in world units.
      car.mesh.add(visual);
      car.assetFallback = fallback;
      visual.visible = !!car.assetDetailed;
      fallback.visible = !car.assetDetailed;
      for (const wheel of wheels) wheel.steer.visible = !!car.assetDetailed;
      car.assetType = type;
      car.assetMaterials = materials;
      car.visual = visual;
      car.assetWheels = wheels;
      car.assetBeacons = beacons;
      car.assetWheelRadius = spec.radius;
      car.assetWheelTravel = 0;
      if (wheels.length !== 4) {
        console.warn('Expected four named GLB wheels:', type, wheels.length);
      }
    });
  }
  function setDetailed(car: VehicleVisual, enabled: boolean) {
    car.assetDetailed = !!enabled;
    if (!car.visual) return;
    car.visual.visible = !!enabled;
    car.assetFallback!.visible = !enabled;
    for (const wheel of car.assetWheels || []) wheel.steer.visible = !!enabled;
  }
  function has(type: string) { return Object.hasOwn(VEHICLE_ASSETS, type); }
  function update(car: VehicleVisual) {
    if (!car.assetWheels) return;
    const steerAngle = car.visualSteer || 0;
    for (const wheel of car.assetWheels) {
      wheel.steer.rotation.y = wheel.front ? steerAngle : 0;
      wheel.spin.rotation.x = -car.assetWheelTravel / car.assetWheelRadius!;
    }
  }
  function setEmergencyLights(car: VehicleVisual, active: boolean) {
    if (!car.assetBeacons) return;
    for (const material of car.assetBeacons) material.emissiveIntensity = active ? 1.8 : 0;
  }
  function dispose(car: VehicleVisual) {
    revisions.set(car, (revisions.get(car) ?? 0) + 1);
    for (const wheel of car.assetWheels ?? []) car.mesh.remove(wheel.steer);
    if (car.visual) car.mesh.remove(car.visual);
    for (const material of car.assetMaterials ?? []) material.dispose();
    car.assetWheels = undefined; car.assetBeacons = undefined;
    car.assetMaterials = undefined; car.visual = undefined; car.assetType = undefined;
  }
  return { has, preload, install, setDetailed, update, setEmergencyLights, dispose };
}
