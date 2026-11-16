import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { vehicleDefinition, type VehicleId } from './vehicle-registry';
type Car = { mesh: THREE.Object3D; x: number; z: number; h: number };
type Definition = NonNullable<ReturnType<typeof vehicleDefinition>>;
type Wheel = { pivot: THREE.Group; spin: THREE.Group; front: boolean };
type View = { car: Car; definition: Definition; fallback: THREE.Mesh; status: 'idle'|'loading'|'loaded'|'failed'; root?: THREE.Group; wheels: Wheel[]; materials: Set<THREE.Material>; beacons: THREE.MeshStandardMaterial[]; selected: boolean; removed: boolean; x: number; z: number; heading: number; travel: number; distance: number };
const DETAIL_RANGE_M = 120, REFRESH_SECONDS = 0.35;
// Rendering owns resource lifetime; no simulation or gameplay rules are mutated.
export function createVehicleVisuals(coarse: boolean) {
  const loader = new GLTFLoader();
  const templates = new Map<string, Promise<THREE.Group>>();
  const views: View[] = [];
  const records = new WeakMap<Car, View>();
  let elapsed = REFRESH_SECONDS, time = 0;
  function load(v: View) {
    if (v.status !== 'idle') return;
    v.status = 'loading';
    let task = templates.get(v.definition.id);
    if (!task) { task = loader.loadAsync(v.definition.url).then(g => g.scene); templates.set(v.definition.id, task); }
    task.then(template => {
      if (v.removed) return;
      const root = template.clone(true);
      root.updateMatrixWorld(true);
      const nodes = v.definition.wheels.map(name => root.getObjectByName(name));
      if (nodes.some(n => !n) || !root.getObjectByName(v.definition.body)) throw new Error('Missing body/wheel nodes');
      for (let i = 0; i < nodes.length; i++) {
        const node = nodes[i]!, pivot = new THREE.Group(), spin = new THREE.Group();
        node.getWorldPosition(pivot.position);
        const rotation = node.getWorldQuaternion(new THREE.Quaternion());
        node.removeFromParent(); node.position.set(0,0,0); node.quaternion.copy(rotation);
        spin.add(node); pivot.add(spin); root.add(pivot);
        v.wheels.push({ pivot, spin, front: i < 2 });
      }
      root.traverse(node => {
        if (!(node instanceof THREE.Mesh)) return;
        node.castShadow = !coarse; node.receiveShadow = true;
        if (v.definition.police && /^lamp_(blue_module|police_grille)/.test(node.name)) {
          node.material = node.material.clone(); v.materials.add(node.material);
          node.material.emissive.set(0x176cff).convertSRGBToLinear();
          v.beacons.push(node.material);
        }
      });
      v.root = root; v.car.mesh.add(root); v.status = 'loaded'; show(v);
    }).catch(error => { if (!v.removed) { v.status = 'failed'; console.warn('Vehicle asset failed:', v.definition.id, error); } });
  }
  function show(v: View) { const visible = v.selected && v.status === 'loaded'; v.fallback.visible = !visible; if (v.root) v.root.visible = visible; }
  return {
    attach(car: Car, id: VehicleId, fallback: THREE.Mesh) {
      const definition = vehicleDefinition(id)!;
      const v: View = { car, definition, fallback, status: 'idle', wheels: [], materials: new Set(), beacons: [], selected: false, removed: false, x: car.x, z: car.z, heading: car.h, travel: 0, distance: 0 };
      views.push(v); records.set(car,v);
    },
    sync(car: Car) {
      const v = records.get(car); if (!v) return;
      const dx = car.x-v.x, dz = car.z-v.z, distance = Math.hypot(dx,dz);
      let dh = car.h-v.heading; dh = Math.atan2(Math.sin(dh),Math.cos(dh));
      const steering = distance > 0.001 && distance < 20 ? Math.max(-0.6,Math.min(0.6,Math.atan(v.definition.wheelbase*dh/distance))) : 0;
      if (distance < 20) v.travel += dx*Math.sin(car.h)-dz*Math.cos(car.h);
      for (const w of v.wheels) { w.pivot.rotation.y = w.front ? steering : 0; w.spin.rotation.x = -v.travel/v.definition.radius; }
      v.x=car.x; v.z=car.z; v.heading=car.h;
    },
    update(focus: {x:number;z:number}, dt:number) {
      elapsed += dt; time += dt;
      if (elapsed >= REFRESH_SECONDS) {
        elapsed=0;
        for (const v of views) v.distance=Math.hypot(v.car.x-focus.x,v.car.z-focus.z);
        views.sort((a,b)=>a.distance-b.distance);
        let count=0;
        for (const v of views) { v.selected=v.distance<DETAIL_RANGE_M && count++<(coarse?3:8); if(v.selected) load(v); show(v); }
      }
      for (const v of views) for (const beacon of v.beacons) beacon.emissiveIntensity = v.selected && Math.floor(time/0.22)%2 ? 1.8 : 0;
    },
    paint(car: Car, color: string) {
      const v=records.get(car); if(!v?.root || v.definition.police) return;
      const body=v.root.getObjectByName(v.definition.body);
      body?.traverse(node=>{ if(!(node instanceof THREE.Mesh)) return;
        const recolor=(material:THREE.MeshStandardMaterial)=>{ const m=v.materials.has(material)?material:material.clone(); m.color.set(color).convertSRGBToLinear(); v.materials.add(m); return m; };
        node.material=Array.isArray(node.material)?node.material.map(recolor):recolor(node.material);
      });
    },
    state(car: Car) { const v=records.get(car); return v ? { id:v.definition.id,status:v.status,detailed:!!v.root?.visible,wheels:v.wheels.map(w=>({steer:w.pivot.rotation.y,spin:w.spin.rotation.x})),fallback:v.fallback.visible } : null; },
    dispose(car: Car) { const v=records.get(car); if(!v)return; v.removed=true; v.root?.removeFromParent(); for(const m of v.materials)m.dispose(); views.splice(views.indexOf(v),1); records.delete(car); },
  };
}
