# Blockout review and validation log

**Decision: reject for integration. Another iteration is justified, but none was
performed after correction cycle 2.** Geometry and resemblance are separate gates.

Environment: Blender 4.3.2, headless Workbench, Python virtualenv with trimesh
4.12.2 and numpy 2.5.4. Blender Modeler commit
`c8f245982108e2627972768d4311cbe172b58137`; no upstream helper edits.
Repository base `8d7198c3f81361c964cf3e0f988e84584dcd761e`.

## Specification and construction

One closed body shell, four named closed wheel meshes; metres, +Y front, +X right,
+Z up. A longitudinal loft shares each cross-section ring with the next, closes
at both ends and is cut with four recessed wheel-well cylinders. The centre
spine and recessed inner walls remain connected. Glazing regions are faces of
the body, not floating panels. Wheels are simple turned envelopes with hub
interfaces. No cosmetic detail, textures or police equipment.

Dimensions: 4.82 m long, 1.71 m wide, 1.43 m high, 2.65 m wheelbase. This is a
rounded 1990 North America manual envelope; detailed shape and market matching
remain estimated (see `references.md`). Export never rescales the model.

## iter_00 — initial blockout, visually reviewed

Read Modeler report, supplemental report and actual GLB validator result. Opened
all eight views in `clay_sheet.png` and the individual side image; compared with
all four downloaded photo previews. Front/side/rear/top and both front
three-quarter views reveal these issues:

1. **Export gate failure first:** two body material regions become two GLB
   primitives; trimesh sees no single `body` node. Fix: one body material with
   corner vertex colors for clay glazing, retaining the original closed mesh.
2. **Nose and tail, front/rear/low views:** large triangular shading patches on
   warped end-cap n-gons. Fix: close ends with horizontal planar strips, retaining
   the integrated extremity shape; do not cover them with detached fascia boxes.
3. **C-pillar, side/rear three-quarter:** side glazing extends too far rearward.
   Fix: reserve a 0.14 m longitudinal C-pillar region instead of 0.055 m.
4. **Recognizability:** long hood and upright sedan cabin are present, but naked
   nose/tail are generic, the shoulder is too broad/faceted and the roof corners
   are too sharp. Keep these as appearance concerns, independent of dimensions.
5. **Reference limitations:** photo views use perspective and different markets.
   Their silhouettes cannot justify millimetre-level fits or Swedish trim claims.

Modeler: 0 errors, 0 warnings, body 638 vertices / 1,272 triangles / 1 island.
Supplement: no boundary/winding/degenerate/BVH-overlap findings. GLB: rejected,
6 nodes, 3,576 triangles; expected exactly one `body` node, found 0.

## iter_01 — correction cycle 1, visually reviewed and rejected

Edited the **same source**, not regenerated from a new design. Added cap strips,
vertex color regions and a wider C-pillar; retained dimensions, wheels, loft and
reference assumptions. Opened all eight views in its sheet.

1. **Cap edit introduced six boundary edges.** Modeler displayed this only as an
   informational open-mesh message while its summary still said 0 errors. The
   repository's Blender body gate rejected the source before GLB export. Final
   fix required: explicitly triangulate the bottom five-vertex cap region; its
   first three vertices alone are collinear, so a standalone bottom cap triangle
   is invalid. No validator weakening or automatic hole repair.
2. **End-face visual patches:** visibly reduced (fixed relative to iter_00),
   but supplemental BVH screening now flags 7 non-adjacent contacts/overlaps at
   front/rear end regions. Closure alone will not resolve this warning.
3. **C-pillar:** wider in side/rear views (fixed), but rear quarterlight is still
   fused visually with the rear door window. Add a 45 mm in-mesh divider at
   y=-0.84 m, keeping the same shell and color scheme.
4. **Broad shoulder and roof corners:** visibly too angular; carried forward.
5. **Front/rear identity:** still not distinct enough to approve as a Volvo 240.

Modeler summary 0/0, but 6 boundary edges; supplemental 7 overlap candidates.
Repository Blender exporter exit 1: `body: 6 boundary/non-manifold edges`.
No iter_01 GLB exists; see `export.log` and `export_status.json`.

## iter_02 — correction cycle 2, FINAL, visually reviewed

Closed bottom caps using explicit non-collinear triangles; added the 45 mm rear
quarterlight divider. Opened the entire final eight-view sheet and individual
three-quarter image. Reviewed the repository export views separately. No further
geometry edits or generation runs followed this review.

Previous critiques:

1. **Six boundary edges: fixed in Blender.** Body 724 vertices / 1,444 triangles;
   1 island, 0 boundary/non-manifold edges, 0 inconsistent-winding edges,
   0 degenerate triangles, positive signed volume 6.375658 m³.
2. **Seven end-region overlap candidates: NOT fixed.** Supplemental BVH screening
   still reports 7 pairs, localized around y=±2.32 m and z≈0.75–0.85 m. Inspecting
   triangle coordinates shows re-entrant end-section levels where the belt is
   above the upper base row. Some contacts reach non-adjacent cap interiors.
   This is unresolved geometric risk even though the mesh is topologically closed.
3. **Quarterlight divider: fixed as a clay region**, visible in side/three-quarter
   views. It is not a floating strip. Its position/angle still needs reference work.
4. **Broad chamfer and sharp roof corners: NOT fixed.** Three-quarter views still
   look like a simplified generic sedan. Hood/trunk have insufficient primary
   curvature and the abrupt circular rear arch does not match the photographed
   rear opening particularly well.
5. **Volvo resemblance: NOT approved.** The long hood, upright greenhouse,
   horizontal beltline, narrow track, front/rear axle spacing and short trunk are
   plausible. Front and rear are too similar, roof transitions too angular and
   lower body too slab-like. Omitted lamps/grille/trim are intentional at this
   stage, but their absence cannot excuse all of the primary-form mismatch.

### Actual export result — rejected

The repository's Blender quality gate passes and its unchanged exporter creates
`volvo240.glb`. The unchanged post-export validator reports:

- **body: has open/non-manifold edges**
- **body: disconnected shells/panels**
- 5 mesh nodes, **3,748 triangles** (below the 20,000 experiment budget).
- 4.8200 × 1.7100 × 1.4300 m; wheelbase 2.6500 m. All wheel names/sides pass.

Diagnosis, **read-only copy only**: exported body has 2,589 attribute-split
vertices and 603 connected pieces in the validator's raw representation. Merging
coincident positions in a diagnostic copy gives 724 vertices, 1 closed shell,
consistent winding. This points to flat-shading/color seams duplicating positions
in glTF. The exported GLB was **not** welded or repaired, the validator was **not**
changed, and this diagnostic does **not** override its rejection. See
`export_diagnostic.json`. A later task should explicitly resolve the pipeline's
position-vs-attribute topology contract, with regression coverage.

The Blender .blend body satisfies the topological closed-shell requirements.
The export does not pass the repository contract, and BVH end-region findings
remain. This is not a geometrically cleared or game-ready result.

### Runtime and visual limits still open

- Wheel object origins currently lie on the vehicle centreline; wheel geometry
  is positioned at the estimated tracks. Before animation use, origins need
  relocating to axle hub centres without moving geometry, then verification.
- Suspension, complete underbody, panel topology, interiors, LODs, collision and
  game integration are outside this clay experiment. No claim of runtime testing.
- The 50 mm nominal radial tire/well clearance is parameter-level clearance;
  steering/suspension travel was not simulated.
- Blender emitted EGL_BAD_MATCH messages but completed the renders via its
  available rendering path. PNG files were opened and visually inspected.
- BVH is a screening check, not an exhaustive solid-intersection proof.

## Commands actually executed

From repository root (Modeler checked out separately at `/workspace/work/blender-modeler`):

```sh
python3 /workspace/work/blender-modeler/scripts/bmod.py --where
# Repeat these commands for NN=00,01,02, after the documented source edits.
python3 /workspace/work/blender-modeler/scripts/bmod.py \
  --model experiments/volvo240/model.py --spec experiments/volvo240/spec.json \
  --out experiments/volvo240/renders/iter_NN --mode none
python3 /workspace/work/blender-modeler/scripts/bmod.py \
  --script experiments/volvo240/review.py \
  --blend experiments/volvo240/renders/iter_NN/model.blend \
  --out experiments/volvo240/renders/iter_NN/review_log -- \
  experiments/volvo240/renders/iter_NN
blender -b --python-exit-code 1 --python tools/vehicle_pipeline/blender_import.py -- \
  --source experiments/volvo240/renders/iter_NN/model.blend \
  --output experiments/volvo240/renders/iter_NN/volvo240.glb \
  --previews experiments/volvo240/renders/iter_NN/repository_previews
/workspace/work/venv/bin/python tools/vehicle_pipeline/validate.py \
  experiments/volvo240/renders/iter_NN/volvo240.glb experiments/volvo240/vehicle.json \
  --report experiments/volvo240/renders/iter_NN/glb_geometry.json
```

Initial review used Modeler's material clay setting; later reviews use a render
handler selecting Workbench vertex colors. No Modeler helper source was patched.
iter_01 exporter failed; its validator was not run because there was no GLB.

`python -m unittest discover -s tests -p 'test_vehicle_*.py' -v`: **5 passed**.
Python source compilation and `run.py --help` passed. No gameplay/e2e suite was
run because no game source or current asset changed. No third correction cycle.

## Next decision for human review

Another iteration is justified **only after this checkpoint is inspected**.
Priority: (1) remove the end-profile re-entrance/contact findings, (2) agree how
raw GLB attribute splits should be validated, (3) soften/refine primary roof,
shoulder, nose/tail and rear-arch silhouettes against better orthographic
references, then (4) validate wheel origins. Do not begin cosmetic detail to
hide these issues. This experiment deliberately ends here.

The prescribed `/codex/browser/projectless/.../output` attachment directory was
not writable by this Cloud environment (including the available escalation).
Artifacts are preserved in this branch's `experiments/volvo240/` directory and
in a ZIP alongside the checkout. This delivery-path limitation is separate from
the model's geometry/appearance failures.

The final repository front/side/rear/three-quarter PNGs were also opened. They
show a uniformly colored body because that preview's Workbench material setting
does not evaluate the vertex-color shader. The Modeler adapter's vertex-color
clay views display the glazing regions for the silhouette review.
