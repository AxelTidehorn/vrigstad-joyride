/**
 * Blender glTF adapter, deliberately independent of the world and physics.
 * Blender exports are in metres, Y-up and -Z-forward after GLB export.
 * The loader constructor is injected so this can be imported unchanged by
 * the Vite/Three r187 application later.
 */
export const VEHICLE_ASSETS = Object.freeze({
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
  function install(car, type, fallback) {
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
      visual.traverse(node => {
        if (node.isMesh) {
          node.castShadow = true;
          node.receiveShadow = true;
        }
      });
      visual.position.y = -0.72; // Cancel current body's +0.72m rig pivot.
      car.bodyRig.add(visual);
      car.bodyRig.remove(fallback);
      car.assetType = type;
      car.visual = visual;
      car.assetWheels = wheels;
      car.assetWheelRadius = spec.radius;
      car.assetWheelTravel = 0;
      if (wheels.length !== 4) {
        console.warn('Expected four named GLB wheels:', type, wheels.length);
      }
    });
  }
  function update(car) {
    if (!car.assetWheels) return;
    const steerAngle = car.driveState?.steer || 0;
    for (const wheel of car.assetWheels) {
      wheel.steer.rotation.y = wheel.front ? steerAngle : 0;
      wheel.spin.rotation.x = -car.assetWheelTravel / car.assetWheelRadius;
    }
  }
  function dispose(car) {
    if (!car.assetWheels) return;
    for (const wheel of car.assetWheels) car.mesh.remove(wheel.steer);
    car.assetWheels = null;
  }
  return { preload, install, update, dispose };
}
