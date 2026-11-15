# Chevrolet Impala 1970 — shape refinement

[Review gallery](index.html) · [Touch / paint viewer](preview.html) ·
[Before / after](review/before-after.png) · [Delivery ZIP](impala1970-delivery.zip)

Refines the existing **16439 Impala Sport Sedan, four-door hardtop** from
`6c7f32c783aa0923cb2f18836157a7ef1cccfc9b` on the separate branch
`experiment/impala-1970-shape`. The existing loft, closed wheel wells, inset window
frames, materials, exporter and validator are retained. All generation, rendering
and checks ran in Codex with headless Blender 4.3.2. No reviewer setup is required.
No game code, physics, existing vehicle, main or Oliver repository was changed.
Human visual approval remains pending.

## Actual form changes

- Front centre remains in place; outer corners retreat into a shallow V. Grille,
  lamp housings and bumper follow that plan instead of a flat front plane.
- Broad fender crowns flank depressed hood channels and a raised central hood.
  Outer front steel now supports the upper headlamp bezel corners. These are
  changes to the closed steel mesh, not painted lines or additional chrome.
- Narrower waist and a tucked lower side replace flatter slab sides, preserving
  the existing wheel openings, hubs and tracks.
- Lower rear deck sits between broad quarter shoulders; tail and bumper corners
  return inward. A fin-like intermediate draft was rejected.
- Windshield becomes more upright, upper opening moves forward, roof broadens
  60 mm across its upper section and gains a controlled transverse crown. The
  existing pillarless hardtop construction and overall design height remain.
- Existing glass sash is fitted to the changed pane geometry, not old widths.
  Five grille blades replace six to reserve the polygon budget for body shape.

Measured steel differences are recorded in [preservation.json](shape-review/preservation.json).
At the fixed hood sample the centre rises 29.5 mm and the channel falls 20.9 mm;
front relief is 89.1 mm at x = 0.775 m. Waist width at y = 0, z = 0.60 falls
67.1 mm. Rear deck sample falls 64.0 mm. Actual front-pane inclination increases
from 32.15° to 39.97° above horizontal. These compare the two models; they are
**not millimetre accuracy claims against perspective photographs**.

## Review evidence

Identical camera metadata, physical framing, material values and lighting are
used for both versions; each comparison applies the same crop to both images.

- [Side and both three-quarter comparisons](review/before-after.png).
- [Exact front and rear comparison](review/ends-before-after.png).
- [Front and rear close comparisons](review/fascia-before-after.png).
- [Steel and tyres only](review/body-before-after.png), without glass, chrome or
  lighting changes concealing the body shape.
- [Same-mode clay comparison](review/blockout-final.png); despite its historical
  filename this now compares the prior finished master with this refinement.
- [Six final views](review/contact-sheet.png), [front close-up](review/front_detail.png),
  [rear close-up](review/rear_detail.png), [factory dimensions](review/dimensions.png).
- [Same-scale fleet comparison](review/fleet-scale.png) and
  [side comparison](review/fleet-side-scale.png). Only the Impala was regenerated;
  Saab and 240 images use the unchanged existing masters and same fixed rig.

Raw before / after images and cameras are in `shape-review/`; final raw renders
and exact transparent orthographic masks remain in `build/final/`.

## Source, asset and compatibility

[`model.py`](model.py) and [`parameters.json`](parameters.json) are authoritative.
[`build/model.blend`](build/model.blend) is the editable master, organised into
BODY, GLASS, CHROME, RUBBER, LIGHTS, DETAILS and WHEELS collections.
[`build/impala1970-hardtop.glb`](build/impala1970-hardtop.glb) is GLB 2.0 in metres,
Y-up / −Z forward, with one closed `body` and `wheel_fl`, `wheel_fr`, `wheel_rl`,
`wheel_rr`. Fixture names, parenting, material values and body origin are retained.
All 16 tyre / rim / whitewall / spoke meshes retain their world geometry and
origins against the frozen prior master. Individual body paint still works.

| Property | Current result |
| --- | --- |
| Length / body width / height | 5.4864 / 2.0269 / 1.3970 m |
| Wheelbase | 3.0226 m |
| Front / rear overhang | 0.9500 / 1.5138 m |
| Front / rear hub track | 1.61036 / 1.60782 m |
| Overall width including mirrors | 2.210 m |
| Triangles / mesh primitives | **19,856 / 27**, below 20,000 budget |
| Materials / textures | **12 / 0** |
| Tyre overall diameter | 0.700 m, estimate; 15-inch rim documented |

## Checks actually run

- Pinned Blender Modeler: 0 errors / 0 warnings.
- Source body: one connected component, zero open/nonmanifold edges,
  inconsistent edges, degenerate faces or nonadjacent self-intersection candidates.
- All component meshes closed and consistently wound. Six closed glass panes;
  zero glass/body surface intersections, minimum sampled signed backing gap
  about 1.095 mm. All four tyres have zero body surface intersection candidates.
- Unchanged strict raw GLB topology/dimensions validator passes. No export repair,
  welding or relaxed criteria. Blender reimport and actual Three r128 parsing pass.
- Actual exported-GLB steering, wheel spin and body-motion probe passes, as does
  per-instance paint isolation. No in-game integration or driving test claimed.
- Independent source regeneration matches all 27 meshes within 1 µm.
- Five validator tests, 11 numerical silhouette tests and 11 preview/control/boot
  tests pass. Five full game smoke tests pass; their log is in `build/e2e-tests.txt`.
- `build/protected-files.json` compares existing Saab / 240 / XC70 masters,
  exports and game sources byte-for-byte against baseline `6c7f32c`.

`summary.json` collects actual check results and asset/source hashes.
`shape-review/preservation.json` independently checks protected geometry,
materials and node names against the old master. Seated lens ribs / trim joints
contain intentional fixture intersections; checks do not prove exhaustive
collision freedom between every pair of fixtures. Actual current GLB also passed the existing browser preview in Chromium software
WebGL at 1024 × 768, both film modes, five fixed views and zoom extremes. A visual
check caught striped glass caused by an excessively broad preview camera depth
range in the film target, rather than intersecting source panes. The local Impala
preview now derives near/far planes from the existing model bounds. Its
`preview-check.mjs` verifies a conservative 16-bit depth step below 1 mm and saves
`build/browser-preview.json` / `.png`. No geometry, polygon offset, material bias
or game rendering changes were used to hide the problem. Physical iPad Safari
GPU/FPS has not been measured.

## Reference assessment and remaining limits

The GM 1970 brochure labels this hardtop on pages 16–17; it is the primary source
for cabin and front form. Factory Sport Sedan dimensions constrain scale and
axles. Licensed photographs supplement shared fascia and rear-quarter details;
ordinary sedan roofs are excluded. See [references.md](references.md) for source
URLs, variant restrictions and uncertainties.

Six final views, close-ups and steel-only renders were visually inspected. The
front relief and hood/fender separation are clearer, the sides less box-like and
the rear deck more distinct from its shoulders. Major scale, wheel placement and
material style are preserved. The model remains a stylised approximation: exact
hood-channel curvature, rear-quarter swell, windshield wrap and bumper returns
need better clean hardtop photographs before further metric refinement. Grille
and bumper sections remain simplified; opaque glass has no detailed interior.

No complete reliable orthographic 16439 side reference was obtained. **No global
silhouette IoU or exact photographic contour accuracy is claimed.** The existing
`review/reference-comparison.json` is explicitly a limited, perspective side-glass
study against the historical initial blockout, not the baseline for this shape
refinement. It cannot certify hood, roof, overhangs or the whole car. New before /
after sheets compare directly against the latest finished model at `6c7f32c`.

## Reproduction

Use repository vehicle-pipeline Python requirements and Blender Modeler pinned to
`c8f245982108e2627972768d4311cbe172b58137`. Retain repository +Y-forward authoring
rather than Modeler's default forward convention.

```bash
BMOD=/workspace/work/blender-modeler/scripts/bmod.py \
VEHICLE_PYTHON=/workspace/work/venv/bin/python \
bash experiments/impala1970/build.sh
```

`review.py`, `fleet.py` and `shape_body_review.py` use the existing Modeler renderer.
`shape_audit.py OLD_MASTER.blend REPORT.json` runs within that Blender workflow;
extract the prior master from commit `6c7f32c` outside the repository for comparison.
`package.py` asserts checks, preserves identical cameras and composes real PNGs
and the source/master/export ZIP. Source regeneration uses the existing
`experiments/round2/reproduction.py` comparison. No new generator or export pipeline.

The existing static `preview.html` keeps touch rotation, zoom, fixed views, paint
selection, film treatment and PNG fallback. The gallery uses relative paths and
is GitHub Pages compatible; repository source alone is not a claim of a newly
published live viewer. PNG sheets are directly reviewable in a browser / iPad.
