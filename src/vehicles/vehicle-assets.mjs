/**
 * Blender glTF adapter, deliberately independent of the world and physics.
 * Blender exports are in metres, Y-up and -Z-forward after GLB export.
 * The loader constructor is injected so this can be imported unchanged by
 * the Vite/Three r187 application later.
 */
export const VEHICLE_ASSETS = Object.freeze({
  volvo: { url: 'media/vehicles/volvo240.glb', radius: 0.35 },
  saab: { url: 'media/vehicles/saab900-t16.glb', radius: 0.35 },
  xc70: { url: 'media/vehicles/xc70-civilian.glb', radius: 0.345 },
  polis: { url: 'media/vehicles/xc70-police.glb', radius: 0.345 }
});
export function createVehicleAssets(THREE, Loader) {
  const cache = new Map();
  let warned = false;
  function preload(type) {
    const info = VEHICLE_ASSETS[type];
    if (!info || !Loader) return null;
    if (!cache.has(type)) {
      cache.set(type, new Promise((resolve, reject) => {
        new Loader().load(info.url, result => resolve(result.scene), undefined, reject);
      }).catch(error => {
        console.warn('GLB loading failed; retaining original vehicle:', type, error);
        return null;
      }));
    }
    return cache.get(type);
  }
  function install(car, type, fallback, paint) {
    const spec = VEHICLE_ASSETS[type];
    if (!spec) return;
    if (!Loader) {
      if (!warned) console.warn('GLTFLoader unavailable, using original vehicle geometry');
      warned = true;
      return;
    }
    const task = preload(type);
    if (!task) return;
    task.then(template => {
      if (!template || !car.mesh.parent || car.assetType) return;
      const visual = template.clone(true);
      // One paint colour per car, not per shared GLB. Only recolour civilian
      // body paint: leave glass, trim, wheels, lamps and police livery intact.
      if (type !== 'polis' && paint) {
        visual.traverse(node => {
          if (node.name !== 'body' || !node.isMesh) return;
          const recolour = material => {
            const instance = material.clone();
            instance.color.set(paint);
            return instance;
          };
          node.material = Array.isArray(node.material)
            ? node.material.map(recolour) : recolour(node.material);
        });
      }
      // Separate wheels from the body rig so body roll and pitch do not tilt
      // their contact patches. Their GLB mesh origins are the hub centres.
      visual.updateMatrixWorld(true);
      const wheelNodes = [];
      visual.traverse(node => {
        if (/^wheel_(fl|fr|rl|rr)$/.test(node.name)) wheelNodes.push(node);
      });
      const wheels = [];
      for (const node of wheelNodes) {
        const hub = new THREE.Vector3(), orientation = new THREE.Quaternion();
        node.getWorldPosition(hub);
        node.getWorldQuaternion(orientation);
        node.parent.remove(node);
        const steer = new THREE.Group(), spin = new THREE.Group();
        steer.position.copy(hub);
        node.position.set(0, 0, 0);
        node.quaternion.copy(orientation);
        spin.add(node);
        steer.add(spin);
        car.mesh.add(steer);
        wheels.push({ steer, spin, front: /^wheel_f/.test(node.name) });
      }
      const beacons = [];
      visual.traverse(node => {
        if (!node.isMesh) return;
        node.castShadow = true;
        node.receiveShadow = true;
        if (/^lamp_(blue_module|police_grille)/.test(node.name)) {
          // Each police car needs its own emissive material state.
          node.material = node.material.clone();
          node.material.emissive = new THREE.Color('#176cff');
          node.material.emissiveIntensity = 0;
          beacons.push(node.material);
        }
      });
      visual.position.y = -0.72; // Cancel current body's +0.72m rig pivot.
      car.bodyRig.add(visual);
      car.assetFallback = fallback;
      visual.visible = !!car.assetDetailed;
      fallback.visible = !car.assetDetailed;
      for (const wheel of wheels) wheel.steer.visible = !!car.assetDetailed;
      car.assetType = type;
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
  function setDetailed(car, enabled) {
    car.assetDetailed = !!enabled;
    if (!car.visual) return;
    car.visual.visible = !!enabled;
    car.assetFallback.visible = !enabled;
    for (const wheel of car.assetWheels || []) wheel.steer.visible = !!enabled;
  }
  function has(type) { return !!VEHICLE_ASSETS[type]; }
  function update(car) {
    if (!car.assetWheels) return;
    const steerAngle = car.driveState?.steer || 0;
    for (const wheel of car.assetWheels) {
      wheel.steer.rotation.y = wheel.front ? steerAngle : 0;
      wheel.spin.rotation.x = -car.assetWheelTravel / car.assetWheelRadius;
    }
  }
  function setEmergencyLights(car, active) {
    if (!car.assetBeacons) return;
    for (const material of car.assetBeacons) material.emissiveIntensity = active ? 1.8 : 0;
  }
  function dispose(car) {
    if (!car.assetWheels) return;
    for (const wheel of car.assetWheels) car.mesh.remove(wheel.steer);
    car.assetWheels = null;
    car.assetBeacons = null;
  }
  return { has, preload, install, setDetailed, update, setEmergencyLights, dispose };
}
