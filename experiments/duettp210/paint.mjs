// Preview/integration preparation only; no game vehicle or spawning code changes.
const instancePaint = new WeakMap();
export function applyBodyPaint(root, hex) {
  if (!/^#[0-9a-f]{6}$/i.test(hex)) throw new Error('Expected #rrggbb body paint');
  const body = root.getObjectByName('body');
  if (!body || !body.isMesh || Array.isArray(body.material)) throw new Error('Expected one body paint material');
  // GLTF clones share materials. Clone once per instance so traffic colours can
  // differ without recolouring another car or any chrome, lights or glass.
  if (instancePaint.get(body) !== body.material) {
    body.material = body.material.clone();
    instancePaint.set(body, body.material);
  }
  body.material.color.set(hex).convertSRGBToLinear();
  body.material.needsUpdate = true;
  return body.material;
}
