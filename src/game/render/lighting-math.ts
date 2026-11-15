export function smoothstep(a: number, b: number, x: number) {
  const t = Math.max(0, Math.min(1, (x - a) / (b - a)));
  return t * t * (3 - 2 * t);
}
export function hash(x: number, z = 0, offset = 0, scale = 43758.5453) {
  const v = Math.sin(x * 127.1 + z * 311.7 + offset) * scale;
  return v - Math.floor(v);
}
export function noise2(x: number, z: number) {
  const ix = Math.floor(x), iz = Math.floor(z);
  const a = smoothstep(0, 1, x - ix), b = smoothstep(0, 1, z - iz);
  return (hash(ix, iz) * (1 - a) + hash(ix + 1, iz) * a) * (1 - b)
    + (hash(ix, iz + 1) * (1 - a) + hash(ix + 1, iz + 1) * a) * b;
}
