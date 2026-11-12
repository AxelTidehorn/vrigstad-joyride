# Low-poly vehicle model contribution (draft)

This branch proposes three original standalone procedural low-poly meshes:

- Volvo 240, replacing the existing box-only visual.
- New Holland T6, a separate parked tractor type.
- John Deere 6M, a separate parked tractor type.

The Saab 900, EPA tractor, legacy tractor, police and game physics are unchanged.
\`src/vehicles/vehicle-library.mjs\` exports a pure geometry-data function and a Three.js adapter.
\`tools/build.py\` inlines it into the standalone HTML output.

## Verification

Run \`node tests/vehicle-models.mjs\` and \`python3 tools/build.py\`.
Then test all vehicle spawns in Chromium, including slopes, shadow rendering and collisions.
The existing generic car collision radius is **not** an accurate tractor collider.
The underlying procedural meshes are prototypes and can still show overlap/z-fighting in WebGL.

## Integration note

Issue #44 plans a Vite/TypeScript migration, so this inline adapter will need moving to a module once that lands. See also #47, #49, #59, #72.

This is a draft contribution for the repository owner to review. Do not merge without approval and the listed manual smoke tests.
