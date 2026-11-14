# Vehicle refinement round 2

Current review: [same-camera comparisons](index.html). All modelling, rendering,
source checks and exports executed headlessly in Codex with Blender 4.3.2 and
Blender Modeler `c8f245982108e2627972768d4311cbe172b58137`.
Work remains isolated in AxelTidehorn/vrigstad-joyride on
`experiment/vehicle-refinement-round2`. No Oliver repository, main, installed
vehicle asset, physics, traffic or game source was modified. Impala development
has not started; this delivery completes the preceding refinement task.

## Inventory and selected masters

Base commit: `744a986`. Latest first-round sources were frozen before editing:

| Vehicle | Latest source selected | Canonical master / GLB |
| --- | --- | --- |
| Saab 900 Classic T16 three-door | profile refinement `288a7fe`, branch tip `c130ae6` | `../saab900/build/model.blend`, `saab900-t16.glb` |
| Volvo 240 sedan | approved wheel-arch refinement `744a986` | `../volvo240/refinement/model.blend`, `review-only.glb` |
| XC70 P2 civil / police | shared-source block lamps / text removal `9590511`, tip `f064b57` | `../xc70p2/build/model.blend`, `xc70-civilian.glb`, `xc70-police.glb` |

Older `contrib/saab-900-geometry` (`296dde5`) and
`contrib/volvo-240-geometry` (`e583bf2`) were inspected. They predate and lack the
later experiment sources, so were not substituted. Current source regeneration
matches every edited master within 1 µm world-position tolerance, including
batched fixture geometry and hidden police equipment. Round-1 renders/reports
remain historical evidence; `round2/build/…/after` and summary.json describe the
current models. The master filenames are unchanged; no second authoring versions
are created. Frozen prior masters are recoverable from Git base `744a986`.

## Actual geometry changes

### Saab 900

The existing clamshell hood was raised locally: centreline +30 mm at Y=1.30 m,
+35 mm at 1.75 m, +25 mm at 2.10 m and +20 mm at the nose. The rear cowl starts
unchanged. A restrained shoulder ridge and supported pressed seams give the
hood a clearer boundary. New fitted rectangular lamp tops stay below actual
hood intersections, grille bezel, lens divisions and lower air dam improve
front identity. Detached old 1 mm seam bars were replaced with body-integrated
reveals. The established roof, cabin, hatch, glass and axle geometry are retained.

Existing Alexander Migl facelift three-door photos were reviewed again; their
exact year is unverified. The same Saab-Scania three-door brochure proxy was
compared with the existing silhouette tool, registered by wheel centres. IoU
0.91469 → 0.91542; regional hood mean absolute error 7.53 → 6.57 canonical px;
maximum local hood error remains 20 px. This is an uncertain pre-facelift drawing,
not exact 1988 metric approval. Factory-perfect nose/cowl form is not claimed.

### Volvo 240

The approved arch solution is retained: all 473 protected original well-region
vertices remain. The outer upper rail was raised into a straighter shoulder
ledge (up to 35 mm); this changes the steel volume, rather than merely its
shading. Supported shoulder, door, hood and trunk reveals define the planes.
The grille has an actual bezel, upright slats and diagonal; lamps have separate
fitted lens blocks, rear reverse lights and real bumper section grooves.
Roof, glazing, wheels, hub positions, wheelbase and body bounds remain unchanged.

### XC70 P2, both variants

The existing P2 estate retains its crown and primary proportions. Fender rails
rise a restrained 10 mm; pressed shoulder/door/hood divisions and fitted grille /
lamp frames define the surfaces. Rear glass changes from approximately
1315×365 to 1271×412 mm: aspect ratio 3.60 → 3.08. Its lower edge drops 47.6 mm;
upper edge changes under 1 mm. Front/rear reveals are 6 mm deep, and a real
painted land separates glass and the large block lamps. Hidden inner lamp walls
narrow away from glass; the rear-facing block form is retained.

The Volvo April 2003 manufacturer rear view and the 2006 facelift rear-right
photo both support a taller, less letterbox-like glazed area. Manual approximate
outer black-surround bounds in the manufacturer image are recorded in summary.json
and drawn on review/xc70-reference-study.png. This includes frit/seal scope and
is not an exact clear-aperture measurement. The 2006 photo has perspective. These
sources justify the direction and frame relation, not exact millimetre approval.
See existing `../xc70p2/references.md` for URLs, authors, licences and year limits.

## XC70 root cause and authoritative geometry

`../xc70p2/model.py` defines body sections, pillars, window openings/glass,
wheel wells and lamp housings **once**. `round2.py` applies shared local forms;
`variants.py` changes only paint/visibility. `review.py` saves two temporary
export snapshots from that one scene, then restores civilian mode in the master.
`--snapshots-only` skips redundant renders when only staging/verification changes.
`export.sh` invokes the existing unmodified exporter/validator/reimport/Three gates.
Civilian and police exports are separate files, not independent model definitions.

Measured root causes were 34 glass/tail-lamp BVH intersection candidates per side
and 488 nearly coincident/occluded sampled backing locations. There was one
shared glass mesh with eight panes, no duplicate police glass and no
police-equipment/glass intersections. Pane-wise PCA seating now leaves a positive
1.5 mm back gap, with 2.5 mm glass thickness outward only. Revised housing backs
clear the glass. After: zero lamp/glass intersection candidates; zero backing
coincidence samples; minimum sampled back clearance 1.4999 mm and exposed-glass
clearance 2.9255 mm. Transparent-background oblique/inside diagnostics are included;
inside views isolate glass and hide the closed opaque backing body.

Every one of the 55 common original glTF mesh nodes matches between actual
exports, including multi-material lamps and parent hierarchy. The verifier uses
original node names, not random primitive-split names assigned by a loader.
A temporary 0.2% rear-aperture width mutation was applied once to body/glass,
exported twice through the existing CLI and compared: both received identical
geometry. The delivered master was unchanged by that test. Reports are in
`build/xc70p2/architecture-mutation.json` and `mutation-export-shared.json`.
Blue/white point colours, full blue fender/quarter fields, blue light materials
and relevant light node names remain. No yellow paint or POLIS text is restored.

## Shared technical architecture and verification

`tools/vehicle_pipeline/surface_refinement.py` extends the established authoring
helpers with local supported V-reveals, closed bezels, fixture batching and
shared-vertex normals. It does not replace body generation or export.
Sliver cleanup is limited to newly invalid cut ears, before export; no open-shell
repair, validator weakening or post-export welding is used. The unused XC body
UV atlas was removed because paint is point-colour data; tiny interpolated loop
UV differences otherwise duplicated GLB indices at the new cuts.

Steering/spin fixtures are children of the four existing hub nodes. Same-material
spokes are batched per wheel (XC70 24 spoke nodes → 4; Saab 12 → 4). Glass, lights,
bumpers and other fixed fixtures are children of body, allowing body motion while
wheel pivots remain independent. Node names wheel_fl/fr/rl/rr, orientation (-Z
forward / +Y up in GLB), metres and independently editable body materials remain.
Transient pose tests on the actual reimported GLBs check wheel spin, steering,
body motion and fixed hub positions; they add no animation or driving logic.

| Export | Triangles | glTF primitives | Wheelbase | Gates |
| --- | ---: | ---: | ---: | --- |
| Saab 900 | 9612 | 39 | 2.517 m | Pass |
| Volvo 240 | 10436 | 31 | 2.650 m | Pass |
| XC70 civilian | 14134 | 57 | 2.763 m | Pass |
| XC70 police | 14486 | 65 | 2.763 m | Pass |

All source bodies: closed, connected, consistently wound, positive volume,
0 degenerates and 0 nonadjacent BVH self-intersection candidates. Body bounds and
wheel geometry remain. Actual GLBs pass the unchanged repository validator,
Blender reimport and pinned Three r128 loader. Five existing validator tests,
11 silhouette numerical tests and six new shared-geometry regression tests pass.
The common fleet sheets use identical orthographic camera, focus bounds, Cycles
lights, sample count and pixel scale for every car. No independently fitted
model scaling was applied. Individual neutral comparisons use identical
before/after cameras and rendering mode (police shaded to show true paint).

## Reproduction

Commands are for Codex/maintainers; reviewers need only the hosted page.
Use the pinned Blender Modeler path as BMOD and the existing Python environment
with vehicle-pipeline requirements. No new game runtime dependency is introduced.

```sh
# Saab/240: edit the latest frozen first-round master directly.
python "$BMOD" --script experiments/saab900/round2.py \
  --blend /path/to/first-round-saab.blend --out /tmp/saab-edit --check -- \
  experiments/saab900/build/model.blend
python "$BMOD" --script experiments/volvo240/round2.py \
  --blend /path/to/first-round-240.blend --out /tmp/240-edit --check -- \
  experiments/volvo240/refinement/model.blend
# Same helpers are called by the existing model.py sources for full regeneration.
# XC70 window topology changes are in its existing single generator:
python "$BMOD" --model experiments/xc70p2/model.py --out experiments/xc70p2/build --mode none
python "$BMOD" --script experiments/xc70p2/review.py \
  --blend experiments/xc70p2/build/model.blend --out /tmp/xc70-staging -- \
  experiments/xc70p2/build --snapshots-only
PYTHON=python3 experiments/round2/export_cars.sh
PYTHON=python3 experiments/xc70p2/export.sh
python experiments/xc70p2/verify_variants.py
python experiments/xc70p2/detail_export_audit.py
# Review accepts vehicle key, output folder and the actual master selected by caller.
python "$BMOD" --script experiments/round2/review.py \
  --blend experiments/saab900/build/model.blend --out /tmp/review -- \
  saab900 experiments/round2/build/saab900/after
python experiments/round2/package.py
```

`quality.py` accepts vehicle key, frozen baseline and report directory;
`reproduction.py` accepts a source-generated temporary master and JSON output;
`seat_audit.py` accepts its JSON output; `pose_audit.py` accepts actual GLB + JSON.
`architecture_audit.py` accepts report directory + temporary snapshot directory.
The temporary mutation GLBs must then be compared with compare_shared_geometry.py.
No mutation assets or duplicate authoring masters are delivered.
For packaging, first-round inventory JSONs are committed in `baseline-inventory/`;
no temporary baseline workspace is required to rebuild the gallery. Raw renders and all reports are
retained in Git; the compact ZIP includes current sources/masters/GLBs and sheets.
Older per-model packaging scripts describe archived review stages and should
not be rerun to overwrite historical comparison imagery with current models.

## Remaining limits

Geometry and visual identity are different gates. Human appearance approval is
pending. Glass remains opaque; the closed body backing is not a hollow interior.
Mirrors, cowl corners, lamp optics and end forms remain stylized. The XC70 rear
track remains simplified to its front track. BVH/ray sampling is not exhaustive
collision proof. Physical iPad Safari, several-car FPS, LODs and game-driving
behaviour were not tested or introduced. `src/vehicles/vehicle-library.mjs` remains
the older procedural runtime; these GLBs were tested through the existing review
loader and are not installed in the game.
