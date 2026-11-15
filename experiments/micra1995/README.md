# Nissan Micra K11 — 1995 European three-door

[Six-view review](review/contact-sheet.png) · [Before / after](review/before-after.png) ·
[Branch game choice](../../index.html?vehicle=micra) · [GLB](../../media/vehicles/micra-k11.glb) ·
[Editable Blender master](build/model.blend) · [Delivery ZIP](micra1995-delivery.zip)

Original Micra-specific geometry on `experiment/micra-k11-1995`, based on fork main
`d5a2a68`. Latest Volvo/Saab/XC70 integration and Impala shape sources were inspected,
including PRs 53, 57–59. This uses the current installed Three r128 loader, not the
separate proposed r187 migration. Main and Oliver's repository are untouched.

## Construction and iteration

`model.py` and `parameters.json` define the authoritative body, apertures, wells,
lamps and fixtures. Headless Blender 4.3.2 / Blender Modeler generated, checked and
rendered all stages in Codex. The reviewer needs no Blender or local setup.
The shared authoring, pressed-reveal, material batching, fixture parenting,
exporter and strict validator are reused from the recent vehicle pipeline.
No old body was scaled or copied. The K11 has its own short drooping hood,
arched cabin, narrow body, small stock tyres and rounded hatch sections.

The steel is one closed mesh with inset closed backing behind six separate closed
glass panes. Integrated A/B/C pillars separate long front-door windows from the
shorter quarter windows. Boolean wheel wells have closed inner ends. Tyres and
wheel covers are attached to four hub-centred `wheel_fl/fr/rl/rr` nodes. Small
hidden axle shafts intentionally enter the well walls; the visible tyre clears.
Lamp shells are sampled against the actual steel and embedded 30 mm. Roof, hatch,
fenders and hood are continuous parts of the steel, not intersecting boxes.

Initial real renders exposed a low/narrow rear window, lamps disappearing beneath
the curved nose and overly long rear lamp wraps. The same source was corrected:

1. Enlarged the rear opening, raised the rear roof/hatch transition and made the
   windshield upper transition more upright while retaining the 1.430 m height.
2. Raised the short hood's front section, tessellated the actual irregular lamp
   outlines and fitted their surfaces to the nose. Corrected grille/plate seating.
3. Moved the B-pillar/door division rearward after inspecting a genuine three-door
   photograph, lengthening the front door and reducing the quarter window.
4. Narrowed rear lamp footprints so rear-facing rays cannot hit distant side
   panels and generate long spurious strips.
5. Removed near-duplicate loft stations at aperture boundaries: they were too
   close for the inset and caused small folded frames. Kept proper frame width;
   source self-intersection and glass fit checks now pass.

`initial/model.py`, `initial/parameters.json`, initial master and matching shaded
views preserve the actual first iteration, including its documented defects.
`build/` is the current master. Before/after uses identical cameras, materials,
physical framing and Cycles 16-sample lighting; package checks camera metadata.
The Workbench default camera labels have a different front convention; use the
explicitly named final studio views rather than interpreting its default labels.

## Dimensions and checks

Nominal standard-model dimensions: **3695 × 1585 × 1430 mm**, **2360 mm wheelbase**.
Actual GLB is approximately 3697.5 × 1585 × 1430 mm: the 2.5 mm bumper difference is
within the explicit 15 mm tolerance. Hub tracks 1360/1345 mm and tyres Ø552 ×155 mm
are estimates. [References](references.md) distinguish primary, secondary and
estimated data, including the 3705 mm Super S homologation trim difference.

Current quantitative results are in [summary.json](summary.json),
[GLB validation](build/geometry.json) and [source audit](build/source-audit.json).
The model has **15,988 triangles**, below the 20,000 budget, with **24 mesh primitives, nine
materials and no textures**. Source audit checks a single connected, consistently
wound closed steel shell, zero nonadjacent self-intersection candidates, zero
source glass/body intersections, positive sampled glass clearance and zero
visible tyre/body intersection candidates. Every component mesh is closed and
consistently wound. Intentional lens/trim seating overlaps remain; this is not an
exhaustive all-component collision proof.

Strict actual-GLB validation, Blender GLB reimport, and exported-hierarchy
steering/spin/body-motion probes are included. Node integration tests read the
actual installed GLB, four names and wheelbase. Validator unit tests and the
existing driving regression suite run without changing driving formulas.
The actual browser Micra entry/driving test passes (four loaded wheel nodes,
entry via E and over two metres of real driving) and its screenshot is in
`review/in-game.png`. Browser logs are retained in `build/*test*.txt`; earlier
failed navigation attempts and concurrent-run artifact errors are retained
separately from the final sequential runs.
`build/protected-files.json` checks existing four installed GLBs and driving code
byte-for-byte against the branch base. Physical iPad Safari FPS is unmeasured.

## Integration and selection

- `src/vehicles/vehicle-assets.mjs`: registers `micra`, GLB URL and visual tyre
  radius. Existing per-instance paint, visibility budgeting and named-wheel
  animation are used unchanged.
- `src/game.html`: registers Micra's name/palette and maps it to the existing FWD
  archetype. An intro link selects `?vehicle=micra`; that mode puts it in the
  nearest existing clear Torget showcase slot. Walk up, press E and drive normally.
  Default fleet layout and traffic distribution are unchanged.
- `TYPES.micra` reuses an existing compatible handling/fallback configuration;
  there are no verified Micra acceleration, engine, gearing or mass claims.
  No solver, transmission or physics parameter definitions were modified.
- Existing procedural geometry is only the loader's temporary failure fallback;
  it is not the Micra model source. The actual Micra render is the installed GLB.
- `index.html` is regenerated with `tools/build.py`, not manually edited.

## Visual assessment and remaining limits

The refined model has a rounder/higher hatch and cabin, correct three-door window
hierarchy, small wheels and the pre-facelift front layout. Main steel is coherent;
no major open seams are visible in the reviewed Blender angles. Silhouette and
curvature remain hand-interpreted from perspective references. No exact
orthographic reference was obtained and no automatic silhouette IoU is claimed.
Minor simplifications remain: squared lamp corner facets, plain wheel covers,
opaque glazing/no detailed interior, approximate bumper radii and simplified
rear lens divisions. Human review should focus on roof curvature, lamp outline
and rear-quarter proportions. This is a stylised game asset, not a factory CAD replica.

## Reproduction

Blender Modeler pinned to `c8f245982108e2627972768d4311cbe172b58137`:

```bash
BMOD=/workspace/work/blender-modeler/scripts/bmod.py \
VEHICLE_PYTHON=/workspace/work/venv/bin/python \
bash experiments/micra1995/build.sh
blender -b --python-exit-code 1 --python tools/vehicle_pipeline/reimport_check.py -- media/vehicles/micra-k11.glb
# Move the reimport report from media/vehicles/reimport.json to this build folder.
npm run test:vehicles
npm run test:driving
npm run test:e2e
python3 experiments/micra1995/package.py
```

`review.py` reuses Modeler's fixed renderer; `audit.py` reuses the recent source
geometry/fit checks. The delivery ZIP includes source, editable master, GLB,
checks, PNGs and shared helpers; it is not a separate modelling pipeline.
