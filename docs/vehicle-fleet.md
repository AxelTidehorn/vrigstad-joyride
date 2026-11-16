# Complete Blender vehicle fleet

Select the parked Torget car with `?vehicle=volvo240`, `saab900`, `xc70`,
`xc70-police`, `impala1970`, `micra-k11` or `duett-epa`. Start and use the
normal movement/E controls. The HUD uses the model name. No query keeps every
existing archetype and the original traffic distribution. Unknown IDs retain
the original procedural car. Models do not define dynamics: mappings reuse
Volvo/Saab/passenger-car, police and EPA simulation. They are not calibrated
real-world handling specifications. No experimental drivetrain is included.

## Registry and lifecycle

`src/game/render/vehicle-registry.ts` declares stable IDs, names, paths, archetypes,
wheel radius/base, node mappings, units/axes and source revisions. Register a new
model there and provide its GLB under `src/public/media/vehicles`. The registry is also the single authoritative source/provenance register.
`test:vehicles` checks all real files through Three's GLTFLoader and validates
wheel locations and plausible bounds.

`createVehicleVisuals` owns rendering state independently from simulation. Call
`attach(car,id,fallback)` after adding a car, `sync(car)` after positioning it,
`update(focus,dt)` once per frame and `dispose(car)` on removal. `addCar` accepts
an optional sixth asset-ID argument; existing spawn code does not select assets.
No new input or vehicle physics rules are introduced.

Loading is lazy inside the 120 m/8 desktop or 3 coarse-device detail budget.
Templates and geometry/materials are cached and shared; instance transforms are
cloned. Authored paint is preserved on load. `paint(car,color)` clones only that
instance's civilian body materials; police livery is protected. Owned material
clones are disposed with the visual; shared cached resources live for the page.
Failures are reported as `failed`, retain the procedural fallback and never
pretend the detailed asset loaded. Removed cars ignore pending asynchronous work.

Wheel travel derives from rendered movement, using -Z forward and metre units;
front steering derives from heading/distance and verified wheelbase. Teleports
larger than 20 m do not spin wheels. Police beacons use existing emissive meshes;
no point lights/shadows are added for them. Coarse detailed meshes do not cast
additional shadows. The read-only game hook exposes the selected car's actual
loading/fallback/detail and wheel state for tests.

## Sources and regeneration

All models: Axel Tidehorn, CC BY 4.0. Original generators: MIT, explicitly
authorized by the author. See LICENSE. No photographs or third-party car meshes
are embedded. Reference images/manufacturer documents keep their original terms;
they are not included in this contribution. No manufacturer endorsement is implied.

Immutable sources in `https://github.com/AxelTidehorn/vrigstad-joyride/tree/<SHA>`:

| Models | Source revision | Editable master | Generator |
| --- | --- | --- | --- |
| Volvo 240 | ff6a0f187add7bd9b7ba052f28bd0d67e534c33a | experiments/volvo240/refinement/model.blend | experiments/volvo240/model.py, refine_forms.py, round2.py |
| Saab 900 | same Round 2 revision | experiments/saab900/build/model.blend | experiments/saab900/model.py, round2.py |
| Both XC70s | same Round 2 revision | experiments/xc70p2/build/model.blend | experiments/xc70p2/model.py, round2.py, variants.py |
| Impala | 46fa31e (full SHA in vehicle-registry.ts) | experiments/impala1970/build/model.blend | experiments/impala1970/model.py |
| Micra | 5c84a17 (full SHA in vehicle-registry.ts) | experiments/micra1995/build/model.blend | experiments/micra1995/model.py |
| Duett | 2be04e6 (full SHA in vehicle-registry.ts) | experiments/duettp210/build/model.blend | experiments/duettp210/model.py |

Download the pinned source tree; do not regenerate from an earlier blockout.
The source experiment READMEs document external Blender Modeler helpers and
source generation. Existing editable masters can be exported with Blender's
GLB exporter: metres, Y-up, apply modifiers, visible objects only, preserve node
names and wheel hub pivots. XC70 variants share one master; `variants.py` changes
paint/equipment visibility rather than authoring a second body. Source geometry
must pass the original experiment's topology/pose gates before replacing an export.
Blender 4.3.2 authored the supplied exports. Re-export bytes can vary by version.

Measured full-model bounds (including trim), metres, X width × Y height × Z length:
240 1.830×1.433×4.820; Saab 1.750×1.420×4.680; XC70 2.020×1.563×4.743;
police 2.020×1.745×4.743; Impala 2.210×1.397×5.486;
Micra 1.790×1.430×3.698; Duett 1.680×1.750×4.100.
Hub wheelbases are 2.650, 2.517, 2.763, 2.763, 3.0226, 2.360 and 2.600 m.

## Delivery and checks

Vite copies the only tracked GLBs from `src/public` to `dist/media/vehicles`.
Relative URLs work under a GitHub Pages project/preview prefix. Until #167 lands,
`tools/build.mjs` also makes an ignored root media copy for committed-page smoke
serving; no second tracked asset directory exists. When root builds are retired, first ensure Pages deploys the full dist tree
including external assets before dropping this compatibility copy. #167 remains open on the implementation base.

Run `npm run check`, `npm run test:vehicles`, `npm run build`, `npm run test:e2e`.
The production build, actual asset parsing, gameplay/fallback and WebGL checks
are automated; images are review artifacts, never pixel-diff tests.
The current upstream preview workflow explicitly excludes fork PRs; a maintainer
must opt into hosting a trusted build if a public playable preview is wanted.

## Visual verification limits

Geometric parsing is not reference approval. Round 2 retains the existing Saab
silhouette comparison against an uncertain brochure proxy (recorded IoU ~0.9154),
protected Volvo arch checks and shared XC70 export/pose checks. Impala and Micra
sources retain their source-specific reference/refinement evidence but explicitly
say human approval is pending. Duett final-pass measurements use wheel-anchored
photographs and perspective estimates, not a completed full silhouette IoU or
factory surface accuracy. All original reference registers/review reports remain
available in the pinned trees. This integration makes no new real-world visual
approval claim. Physical mobile/Safari performance, final silhouette/livery
approval and traffic placement decisions remain for human review.

Collision envelopes remain those of existing archetypes, not model-specific
body geometry. Large models can therefore visually overhang their collision
shape. Physics/collision calibration is a separate gameplay decision.
