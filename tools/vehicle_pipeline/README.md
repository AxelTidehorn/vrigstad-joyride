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

## Historical Saab 9-5 pilot status

- Validator, Blender export script and synthetic regression tests: implemented.
- Initial Saab 9-5 pilot only syntax-checked Blender. Later Volvo 240, Saab 900
  and XC70 experiments execute Blender 4.3.2 headlessly; see round-2 evidence below.
- Licensed and silhouette-approved 2002–2005 Saab 9-5 SportCombi source: **not sourced**.
- Actual Saab GLB, visual approval, and game integration: **not done**.

This intentionally avoids installing placeholder geometry into the game.

## Reference-driven silhouette gate

The historical Saab 9-5 pilot status above applies only to that unsourced asset.
Headless Blender 4.3.2 now runs in Codex for the isolated Volvo 240 and Saab 900
experiments. The Saab's existing pipeline now includes axle-registered silhouette
verification, internal control curves and automated numerical tests.
See [SILHOUETTE.md](SILHOUETTE.md) for commands, configuration and quality rules,
and [the Saab before/after report](../../experiments/saab900/silhouette/README.md).
No existing game vehicle is replaced.

## Shared-body variants (XC70 P2 experiment)

`experiments/xc70p2/model.py` builds one closed base and separate police collections.
`variants.py` switches paint and equipment visibility on that same body. The
master Blender file retains both; the existing exporter consumes temporary
visible-variant snapshots. `verify_variants.py` independently compares the two
actual GLBs' common geometry. No game assets are replaced.
The CPU `check_preview_glb.mjs` adapter now supports embedded PNGs by exposing
header dimensions to the real pinned loader. It does not simulate GPU texture
upload; PNG decoding is checked independently with Pillow and Blender reimport.

## Current shared vehicle refinements

[Vehicle refinement round 2](../../experiments/round2/README.md) retains the existing
exporter, validator, reimport and Three loader. `surface_refinement.py` adds local
pressed sheet-metal reveals, physical support rows, closed fixture bezels and
hierarchy helpers. It does not replace body construction or repair exports.

`compare_shared_geometry.py CIVIL.glb POLICE.glb --report FILE.json` compares every
original glTF mesh node, all material primitives, world-space triangles and parent
hierarchy. Paint is allowed to vary; body, glass, tail lamps and wheel rig are not.
This avoids false matches caused by randomized loader names for split primitives.
Six binary-GLB regression fixtures cover material-only differences and changed /
missing glass, multi-material lamps, wheel parents and independent variant meshes.

XC70 `model.py` owns one body/opening/lamp implementation. `round2.py` applies
common forms; `variants.py` changes material and equipment visibility. The existing
review step supports `--snapshots-only` to save both export snapshots without
rerendering. A real temporary rear-aperture mutation was exported through the same
CLI twice and verified identical. Current reports and pose tests are linked in
the round-2 review; no game integration or measured hardware FPS is implied.
