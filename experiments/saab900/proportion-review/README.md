# Saab 900: profile and controlled-surface refinement

The latest existing Saab master was edited in place through `../model.py`.
The before file is the hood-corrected checkpoint retained in Git, not the first
blockout. No new vehicle generator or replacement body architecture was created.
Body, glass, wheels, details, exporter and coordinate conventions remain the same.

## Findings and actual changes

The previous cowl/cabin sat too far aft relative to the front axle; the windshield
had a shallow apparent angle and a broad painted upper transition. The high roof
was short and curved, and the height-driven cross-sections wrapped the side glass
outward toward its ends. The quarter window extended too far into the hatch.

- Cowl/rear hood station moves from y=.84 to 1.00 m, leaving the existing wedge
  toward the nose and a short physical cowl break. The upper roof/windscreen
  station moves from y=.24 to .48 m. This shifts the cabin architecture forward
  relative to the unchanged axles rather than stretching the whole car.
- Roof has a longer, flatter high section with a defined rear break at y=-.95.
  Transverse crown drops from 47 to 25 mm; maximum vehicle height stays 1.420 m.
- B-pillar centre moves from -.49 to -.40 m; quarter-glass rear limit moves from
  -1.48 to -1.28 m. Door handle, mirror, door boundary and spoiler are reseated
  where their supporting geometry changed. Existing parts are reused.
- Side glass/backing uses a common real plane across the long door and quarter
  windows. The 6 mm thick panes have a fitted-plane RMS of 3.00 mm including
  both surfaces, compared with 6.72–7.72 mm before; the extra geometric warp is
  removed. Normals remain standard smooth body / flat glass. No weighted-normal
  or material-only replacement is used to simulate these shape changes.
- Hatch upper contour becomes a controlled descending run joining that rear roof
  break; lower rear volume, nose, bumpers, all wheels/rims, lamps and grille stay.
  No extra cosmetic equipment or new texture was added.

The direct audit preserves 36 complete components byte-for-coordinate, including
all wheels, bumpers, grille and lamps. Body bounds are identical: steel width
1.690 m, shell length 4.480 m, ground/shell minimum .235 m and top 1.420 m.
Overall length including bumpers remains 4.680 m; wheelbase is 2.517 m.
Adapted trim is listed separately. See `change-audit.json`.

## Reference-based before/after measurements

Same source mask, wheelbase registration and region definitions in both runs.
No independent width/height fitting or IoU optimisation.

| Measurement | Before | After |
|---|---:|---:|
| Global IoU | 0.8998 | 0.9147 |
| Windscreen region mean absolute profile error, canonical px | 25.62 | 10.34 |
| Roof region mean absolute profile error, px | 9.93 | 4.34 |
| Rear region mean absolute profile error, px | 4.19 | 2.20 |
| Hood region mean absolute profile error, px | 6.09 | 7.53 |

The hood region is slightly worse; it is not hidden by the higher total score.
Forward cabin/cowl placement is supported by the side reference and the complete
three-quarter photos. Its effect on the hood is a deliberate relational change,
not a claim that every local surface became more accurate. The normalised mask
excludes mirrors/bumper extensions; some nose/lower-body differences remain.

The manufacturer side illustration is pre-facelift and small, not a calibrated
1988 Turbo 16 engineering drawing. Facelift photographs are perspective views.
The reports correctly retain `metric_geometry_verified:false`; errors above are
canonical comparison pixels, not certified real-car mm errors. See ../references.md.
Model-space movements in mm are direct measurements independent of that caveat.

## Visual and technical verification

Before/after exact side, front three-quarter and rear three-quarter were rendered
with identical camera/focus/light settings using the existing Modeler renderer.
A cabin close-up is included. All were opened for visual review. The revised car
has a more forward cabin, clearer roof plateau, calmer side windows and a more
intentional roof/hatch break. Remaining: softened wheel-well shading, simple
lamp/door-shut detail and opaque glass without an interior. Overall recognition
still requires human assessment; no automatic resemblance approval is claimed.

Existing Blender gate, Modeler checks, closed-body manifold/winding/degeneracy/BVH
checks, actual GLB validator, Blender reimport and pinned Three.js loader pass.
7,758 triangles, 47 mesh nodes and 8 materials; previous checkpoint 7,822 triangles.
Canonical files remain ../build/model.blend and ../build/saab900-t16.glb.
No game integration, physics, XC70 or Volvo 240 asset change.

## Reproduce

Use the same Blender 4.3.2 / pinned Blender Modeler and pipeline requirements as
../README.md. Restore the baseline with Git (the parent commit of this refinement)
into a temporary .blend path; its SHA256 is in change-audit.json. Then:

1. Run `proportion_review.py` in Modeler script mode against the baseline into
   this folder's `before`; run `silhouette_render.py` with `before-config.json`.
2. Run the existing `model.py` through Modeler into ../build, then the same
   review script into `after` and the silhouette renderer with `after-config.json`.
3. Run `verify_silhouette.py` for each config/frame, adding `--baseline` for after.
4. Run `proportion_audit.py` with baseline path and this directory as script args.
5. Export through unchanged blender_import.py, validate.py, reimport_check.py.
6. Run `proportion_package.py` to produce the static page, comparison sheets and
   compact current source/model package. No rebuild is needed for report-only edits.

Source feature stations differ by anatomy before/after; both projected frames
are actual mesh intersections. Reference/control annotations and fixed comparison
regions are unchanged. Prior silhouette/hood reports remain historical snapshots.
