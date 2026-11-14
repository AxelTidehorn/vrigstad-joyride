# Saab 900: silhouette verification and targeted hood correction

Both requested deliveries are implemented: a reusable verifier with numerical
tests, and a changed, rendered, reviewed and exported Saab mesh. The latest
pre-edit checkpoint is `86ad3de`, not the original first blockout. `before/model.blend`
and `before/model.py` freeze that exact starting asset; `../build/model.blend`
and `../build/saab900-t16.glb` remain the canonical updated files.

## Result

| Check | Before | After |
|---|---:|---:|
| Global IoU against uncertain manufacturer proxy | 0.8901 | 0.8998 |
| Hood upper-profile mean absolute error, canonical px | 13.25 | 6.04 |
| Independent annotated hood-curve mean absolute error, px | 12.09 | 5.26 |
| Hood maximum vertical error, px | 28 | 28 |
| Roof mean absolute error, px | 7.43 | 7.43 |
| Rear mean absolute error, px | 4.19 | 4.19 |
| Triangles | 7,610 | 7,822 |
| Body open / inconsistent edges, degenerate faces | 0 / 0 / 0 | 0 / 0 / 0 |
| Body non-adjacent BVH overlap candidates | 0 | 0 |

The unchanged maximum hood error is concentrated near the nose, where the
pre-facelift proxy differs from the facelift asset. A better mean is not exact
real-car certification. Windscreen placement remains visibly different from this
small proxy (after mean 29.89 px); no larger cabin/roof redesign was authorized.
The preserved roof and rear also have residual discrepancies. See source notes.

Actual mesh changes, in model metres (independent of reference-image uncertainty):
hood at y=.95 rises from .890 to .986 (+96 mm); at y=1.30 from .850 to .910
(+60 mm); at y=1.75 from .800 to .810 (+10 mm). Nose at y=2.10 stays .750.
At the hood rear station y=.84, height rises from .950 to 1.010 (+60 mm).
The rear hood's local angle toward the front changes from -28.61° to -12.53°:
this removes the old steep sag into the low middle hood and produces a more
uniform wedge. Across y=.84–2.10 the hood now falls about 260 mm toward the nose,
versus 200 mm before. This is a redistribution, not a rigid whole-hood lift.

Actual cowl spine y=.818–.838 is now horizontal, versus -28.61° before. The lower
windscreen remains a separate sloping section. Close support sections at the
short cowl break retain a sharp physical change in slope without a large fillet,
bevel or subdivision; smooth per-vertex shading avoids unnecessary triangle
faceting. The windshield bow fades out before the cowl, avoiding reversed
longitudinal loops. Adjacent fender surfaces use the same closed loft, and the
lower glazing follows its seated body backing.

The body remains one closed connected shell. All 43 non-body/non-glass component
checksums except the two side moldings are unchanged. The moldings were reseated
on the changed fender surface; section/style are preserved. Wheels, wheelbase,
bumper, lights, grille, doors/decor and rear parts are unchanged. Roof/rear and
nose centreline vertices are identical. GLB validator: no errors/warnings,
47 mesh nodes, 8 materials, 4.680 m long, 1.690 m body width (1.750 m with mirrors),
1.420 m high and 2.517 m wheelbase. Actual Blender reimport and pinned Three.js
GLTFLoader parsing pass. Blender Modeler reports 0 errors and 0 warnings.

## Visual review and limits

Side, front three-quarter and cowl close-ups were actually rendered headlessly
and opened before and after. The hood now has a more coherent forward-falling
surface and the short cowl creates a readable break at the windshield base.
Front lamps remain below the tapered hood contour. No disconnected hood panel,
black disguise or material-only fix was introduced. Remaining compromises:
slightly soft fender shading, simplified lamp/indicator shapes, opaque faceted
windows, and cabin/reference disagreements documented above.

Reference: a real manufacturer three-door illustration, copyright 1985, for
1986 pre-facelift 900/900i; exact 1988 T16 front and calibrated full-body contour
were **not found**. The workshop manual independently supports 2517/1690/1419 mm
and hatchback 4687 mm. The existing 4680 mm model length is preserved. Reports
explicitly set `metric_geometry_verified:false`. Exact reference mm errors and
factory-correct cowl/hood heights cannot be accepted from this proxy. Model-space
changes in mm are genuine measurements; they are not reference accuracy claims.
A qualitative facelift Turbo front-three-quarter photo was also inspected.
No AI imagery was used. See [sources](../references.md).

## Verification coverage

- Exact orthographic RGBA side render; same quality cameras before/after: done.
- Axle/ground uniform registration, independent calibration: done.
- Alpha, manual-mask/polygon, guarded background segmentation: implemented.
- Global/local contour metrics, signed profiles, points/curves and turn angles:
  done; front arch curve extracted from actual cut-mesh vertices.
- Overlay, deviation maps, four region enlargements, before/after JSON: done.
- Eleven numerical tests including all seven requested scenarios: pass.
- Five unchanged GLB validator regression tests: pass.
- Existing preview suite: 11/11 pass. Initial runs exposed a timing race in the
  film-success test: the offscreen film render already contains the body before
  the visible frame hides the fallback. Its wait now checks that visible-frame
  condition before asserting it. No preview or game product code changed.
- Physical iPad Safari / GPU performance and exact year-specific metric
  reference approval: not verified. The static page/PNGs need no local setup.

## Files and reproduction

[Pipeline instructions](../../../tools/vehicle_pipeline/SILHOUETTE.md).
`saab900.json` contains all vehicle-specific annotations, regions and provenance;
comparison code has no Saab coordinates. `tests.txt` records test output.
`change-audit.json` records actual component hashes, preserved areas, heights
and section angles. `surface-breaks.png` plots direct mesh profiles.
`comparison-sheet.png` and `contour-sheet.png` are iPad-readable PNG sheets.
`package_review.py` rebuilds this static review page and the download package.
Existing earlier `build/final-change-audit.json` and `final_review.py` describe
the previous window/headlamp refinement; use this folder for the new hood audit.

No game code, physics, Volvo asset or legacy Three.js car geometry changed.
Work remains isolated on `experiment/saab900-silhouette`; human visual approval
and any game integration remain separate.
