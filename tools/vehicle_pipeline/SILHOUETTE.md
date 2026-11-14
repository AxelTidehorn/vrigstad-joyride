# Silhouette verification gate

This extends the existing Blender/Modeler authoring, renderer, exporter and GLB
validator. It does not replace them or integrate assets into the game.
Dependencies in `requirements.txt` are authoring-only: Pillow for image IO and
SciPy for contour distance transforms, connected components and erosion.

## Reproduce the Saab comparison

Commands from the repository root; `BMOD` is the checked-out
[Blender Modeler](https://github.com/calebrisc/blender-modeler) `scripts/bmod.py`.
The existing experiment pins Modeler commit `c8f245982108e2627972768d4311cbe172b58137`.
Blender 4.3.2 was actually executed headlessly; all PNGs were rendered and inspected.

```sh
python -m pip install -r tools/vehicle_pipeline/requirements.txt
python -m unittest discover -s tools/vehicle_pipeline -p 'test_verify_silhouette.py' -v
python "$BMOD" --script tools/vehicle_pipeline/silhouette_render.py \
  --blend experiments/saab900/silhouette/before/model.blend \
  --out experiments/saab900/silhouette/before/log -- \
  experiments/saab900/silhouette/before experiments/saab900/silhouette/saab900.json
python "$BMOD" --model experiments/saab900/model.py --out experiments/saab900/build --mode none
python "$BMOD" --script tools/vehicle_pipeline/silhouette_render.py \
  --blend experiments/saab900/build/model.blend \
  --out experiments/saab900/silhouette/after/log -- \
  experiments/saab900/silhouette/after experiments/saab900/silhouette/saab900.json
python tools/vehicle_pipeline/verify_silhouette.py \
  experiments/saab900/silhouette/saab900.json experiments/saab900/silhouette/before/frame.json \
  --out experiments/saab900/silhouette/before/comparison
python tools/vehicle_pipeline/verify_silhouette.py \
  experiments/saab900/silhouette/saab900.json experiments/saab900/silhouette/after/frame.json \
  --out experiments/saab900/silhouette/after/comparison \
  --baseline experiments/saab900/silhouette/before/comparison/report.json
python tools/vehicle_pipeline/silhouette_review.py experiments/saab900/silhouette
```

Run existing `blender_import.py`, `validate.py` and `reimport_check.py` afterwards
as documented in README and the Saab experiment. They remain independent gates.
When only comparison logic changes, run tests and `verify_silhouette.py` again;
existing PNGs/frame annotations suffice. Do not regenerate the model.

## Add the next vehicle

Copy the **configuration schema**, not the Saab's coordinates. Supply:

- `vehicle`, documented dimensions as `{value,status,source}` and uncertainties.
- `reference.image`, source URL/variant, `front_wheel`, `rear_wheel`, `ground`
  in source pixels. Front may face either direction. No anisotropic stretching.
- `reference.mask`: `alpha`, `manual_mask` with `path`, `manual_polygon` with
  `polygon`, or `background` with optional RGB-distance `threshold` (default 50).
  Mark `reviewed:true` only after visually reviewing the extracted mask. Background
  segmentation uses corner colour and largest foreground component; complex
  photos, shadows and disconnected objects require a manual mask. It never
  certifies an automatic mask by itself. Empty/constant alpha is an error;
  tiny/full/truncated/disconnected/unreviewed masks produce explicit warnings.
- `orthographic` and `metric_reliable` independently. A stylized technical drawing
  or a perspective photograph must not be promoted to a metric reference simply
  because its wheelbase is known. Millimetre error fields are emitted only for
  a reviewed, reliable orthographic reference. Otherwise results use canonical
  pixels and clearly marked wheelbase-scaled estimates.
- `points` and `curves` are named manual source-pixel annotations. Matching names
  in the rendered `frame.json` are projected from actual mesh geometry.
  The renderer takes `point_stations_y` and `curve_stations_y` from config;
  stations intersect the body's centreline edges. For off-centre features,
  supply actual projected feature coordinates in the model frame, never copies
  of reference annotations. `arch_curves` selects actual boolean-cut mesh
  vertices near a documented arch circle; missing samples cause an error.
- `regions` maps names to `[x_min,x_max,z_min,z_max]` in wheelbase-scaled metres,
  rear axle at x=0, ground z=0, front toward positive x. Choose regions with
  known physical meaning; see Saab's hood, windscreen, roof, rear, arches and
  underbody. Regions are configuration data, not code branches per vehicle.
- `mask_scope` explicitly records excluded mirrors, spoilers, bumpers or shadows.
- `blender` gives body object, fixed quality/close-up focus bounds and feature
  stations. Naming/axes follow the existing body/wheel convention, +Y forward,
  Z up. Silhouette camera is exactly +X, orthographic, no floor/shadow, RGBA.
  Same camera, lights and frame bounds are used before and after.

## Interpretation and limitations

Registration rotates/reflexes and **uniformly** scales using the two wheel
centres and documented wheelbase. Ground fixes only vertical position. There is
no iterative IoU fit, independent width/height fit or roof alignment. Anchors
necessarily match after registration: this is not evidence that the wheelbase
was correct. `pixels_per_metre` from the Blender camera independently checks the
actual wheel centres. Held-out wheel/feature points can detect displacement.

Global metrics: IoU, symmetric mean/max contour distance, length/height and
front/rear overhang differences. Region metrics include signed upper-envelope
height (positive means model too high), absolute/max height, symmetric regional
contour distances and lower-envelope underbody height. Wheel arches are measured
as internal annotated curves because tyres can obscure them in an outer mask.
Roof maximum position/extent and wheelbase-scaled bounds are included. Raster
bounds describe the configured mask scope, not necessarily bumper-to-bumper
length; use the unchanged GLB validator for full physical dimensions.

Control curves independently report height profiles, segment angles and turn
angles, exposing internal hood/cowl/glass breaks which IoU cannot establish.
Non-overlapping curve domains are flagged; they are not extrapolated or fitted.
Manual, automatically extracted and computed data are identified in JSON.

A large global overlap cannot approve a bad hood. Review local measurements,
internal curves, full side/three-quarter renders and actual reference photos.
Symmetric contour distance is sensitive to mask scope and residual ground errors.
The maximum can remain dominated by a different nose/bumper variant even after
mean hood error improves. No algorithm here detects every inter-component
intersection, proves year-specific authenticity or benchmarks iPad GPU FPS.

Outputs: source-aware contour overlay (red reference, cyan model), deviation map
(0–25+ canonical pixels), enlarged region PNGs, reports with baseline deltas,
independent calibration and uncertainty. `silhouette_review.py` assembles two
large before/after PNG sheets, the direct model-delta audit and a surface-profile
plot. `index.html` in the Saab experiment is a static, touch-friendly review page.
No local software is needed to inspect it.
