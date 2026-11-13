# Vehicle production pipeline (pilot: Saab 9-5 SportCombi)

This is a **separate authoring pipeline**. Three.js remains the game renderer.
Do not create more disconnected faces in `vehicle-library.mjs` to imitate a car.
The existing procedural cars remain unchanged until a replacement passes **both**
geometry validation and human silhouette review.

## Asset convention

- Author in Blender using **metres**. **+X** points toward the vehicle's right,
  **+Y** forward and **+Z** up. Blender's `export_yup=True` produces a GLB
  with **-Z forward, +Y up**, matching the game.
- Exactly one main watertight, consistently wound, connected mesh named `body`.
  Windows can be separate `glass*` meshes; wheels must be named
  `wheel_fl`, `wheel_fr`, `wheel_rl`, `wheel_rr`.
- Details can be separate if named `lamp*`, `trim*`, `bumper*`, `mirror*`,
  `interior*`, `plate*`, `grille*`, or `badge*`. No floating panels.
  Only the *body* needs to be one closed shell.
- Paint/material splits should be assigned *within* the body mesh, rather than
  by floating coloured panels. Wheel arches must be part of the shape.
- Dimensions are checked against model-specific references. There is no
  automatic stretch-to-match operation masking a wrongly proportioned car.

## Running

Requires Blender 4.x+, Python and, for post-export validation, `trimesh` and
`numpy`. These are **modelling tools**, not game runtime dependencies.

```bash
python -m pip install -r tools/vehicle_pipeline/requirements.txt
blender -b --python tools/vehicle_pipeline/blender_import.py -- \
  --source path/to/saab95.blend \
  --output assets/vehicles/saab95Estate.glb \
  --previews build/vehicle-previews/saab95Estate
python tools/vehicle_pipeline/validate.py \
  assets/vehicles/saab95Estate.glb tools/vehicle_pipeline/saab95.json \
  --report build/vehicle-previews/saab95Estate/geometry.json
python -m unittest discover -s tests -p 'test_vehicle_*.py' -v
```

Import also accepts OBJ, FBX and GLB, but input needs correctly assigned part
names, coordinates and a **closed** body. The Blender stage rejects holes,
non-manifold edges, disconnected bodies and missing wheels. The post-export
validator inspects the **actual** GLB for dimensions, wheels, degenerate
triangles, normals, disconnected shells, detached component centres and budgets.

**These checks do not establish that a car looks like a Saab, nor detect every
internal intersection.** Before game integration, review `front.png`,
`side.png`, `rear.png`, and `three_quarter.png` against reference photos.
Geometry passing is a requirement, not an appearance approval.

## Asset lifecycle

1. Acquire a **legally reusable** 3D model, or create a reference-based mesh.
   Verify the year and body variant; *editorial-only* marketplace listings are
   not approved game assets.
2. Correct source topology in Blender. Do not hide gaps using more polygons.
3. Run exporter and validator. Fix errors in the source.
4. Compare all four previews with references; reject silhouette mismatches.
5. Only then integrate its GLB through the already included `THREE.GLTFLoader`.
   Vehicle physics remain separate from render geometry.
6. Record original creator, asset licence, and modifications in `LICENSE`.

## Current pilot status

- Validator, Blender export script and synthetic regression tests: implemented.
- Blender script syntax checked; **not executed here** (Blender unavailable).
- Licensed and silhouette-approved 2002–2005 Saab 9-5 SportCombi source: **not sourced**.
- Actual Saab GLB, visual approval, and game integration: **not done**.

This intentionally avoids installing placeholder geometry into the game.
