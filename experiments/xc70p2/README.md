# Volvo XC70 P2, MY2005 civilian / Swedish police

One procedural authoring source and **one shared body**, with material/visibility
variants. No game or physics integration. Existing Volvo 240 and Saab assets are
unchanged. Blender 4.3.2 executed headlessly in Codex; all five fixed views per
variant were rendered and visually opened. No viewer-side local software needed.

## Construction and reproduction

`model.py` uses the established `authoring.py` / Blender Modeler mesh helpers:
a closed, capped, longitudinal loft with XC70-specific sections, Boolean recessed
wheel wells, inset painted window frames and seated opaque glass islands.
A/B/C/D pillars have real painted width. No body panels are floating slabs.
Independent closed arch moldings follow the wheel-well curve; swept bumpers
wrap to the sides. Tall D-pillar lamps, grille/diagonal, rails, handles and wheels
are separate genuine components. Body/rim materials remain independently editable.

`variants.py` changes only paint/livery and POLICE/POLICE_DECALS visibility.
No duplicated base shell. The body paint material and ray-cast seated alpha vinyl
markings are authored originals; reference photographs are not used as textures.
Blue light modules have distinct objects/material and emission strength zero,
ready for later animation. No flashing or gameplay logic is added.

Use the same pinned Blender Modeler checkout as the Saab experiment. From root:

```sh
python "$BMOD" --model experiments/xc70p2/model.py --out experiments/xc70p2/build --mode none
python "$BMOD" --script experiments/xc70p2/review.py --blend experiments/xc70p2/build/model.blend --out experiments/xc70p2/build/review_log -- experiments/xc70p2/build
PYTHON=python3 experiments/xc70p2/export.sh
python "$BMOD" --script tools/vehicle_pipeline/silhouette_render.py --blend experiments/xc70p2/build/model.blend --out experiments/xc70p2/build/silhouette/log -- experiments/xc70p2/build/silhouette experiments/xc70p2/silhouette.json
python tools/vehicle_pipeline/verify_silhouette.py experiments/xc70p2/silhouette.json experiments/xc70p2/build/silhouette/frame.json --out experiments/xc70p2/build/silhouette/comparison --baseline experiments/xc70p2/build/baseline/comparison/report.json
python experiments/xc70p2/package_review.py
```

The editable master `build/model.blend` contains both configurations, opening in
civilian mode; call `variants.apply('police')` to expose equipment and paint.
Intermediate `civilian.blend` and `police.blend` are export staging snapshots,
not separate authoring sources. The download contains only the shared master.
Workbench shows materials and solid form; Cycles shows livery/alpha textures
using the same Modeler cameras and light rig. This Blender build lacks the
OpenImageDenoise backend, so Cycles uses 16 samples without denoising; some fine
render noise remains. The exported materials are simple matte glTF materials.

## Measurements / verification

Documented targets: 4733 mm length, 2763 mm wheelbase, 1860 mm width including
XC cladding, 1562 mm unladen height and 209 mm clearance. Actual exported length
is 4743 mm (10 mm over due to fitted bumper sweep), height 1562.5 mm civilian /
1745 mm with lightbar. Steel shell width is 1800 mm, arch-cladding envelope
1860 mm; mirrors span 2020 mm. Validator metadata explicitly uses steel width
because its unchanged width check measures `body` alone. Axle/tyre radius .345 m
and clearance are real mesh dimensions. Rear track is simplified to front
1611 mm instead of documented 1548 mm; this is a known deviation, not a verified
factory suspension reconstruction. Wheelbase is exactly 2763 mm.

The actual reference-based silhouette tool ran. Axle registration uses uniform
scaling and ground, no independently stretched images. Initial IoU 0.8968 becomes
0.9142. Roof mean absolute profile error 12.70 becomes 0.76 canonical px; hood
stays 6.50 px, with the nose preserved. Rear improves but retains 40.21 px regional
envelope error: end shape/bumper mask scope and pre-facelift photography limit
that comparison. It is not masked by the global score. Exact year-specific
millimetre approval remains unavailable; reports set metric_geometry_verified=false.
See `references.md` and before/after overlay, heatmap, local crops and JSON.

`build/variants.json` proves identical body coordinate hashes. Body manifold,
winding, degeneracy and BVH self-intersection screens pass. Each actual GLB is
validated, imported in Blender and parsed with the existing pinned Three.js
GLTFLoader. Node's bitmap adapter supplies PNG dimensions for structural parsing;
Pillow and Blender independently decode the packed PNGs. This is not a browser
texture-upload or physical Safari/GPU test. Detailed results are linked below
on the static review page. The 11 silhouette numerical tests are retained.

## Visual assessment and remaining deviations

Recognizable long P2 estate profile, restrained wedge hood, separate windshield
plane, tall rear lights, lifted tyres and dark XC arch/cladding mass. Roof and
rims improved after the first review. Final side/front/rear and both three-quarter
views were inspected; remaining style compromises include broad bumper corners,
soft wheel-well shading, simplified rear lamp contours, six-spoke wheel graphics
and flat opaque glazing without an interior. Fine door/tailgate shut lines are
simplified; this is stylized game geometry, not an exact factory body model.

The current police paint is blue on white, as requested in the targeted correction.
It supersedes the earlier blue/yellow experiment. Full front-fender and rear-quarter
areas are blue; doors, hood centre and tailgate centre stay white for readable POLIS.
Paint follows body point colours, avoiding projected texture streaks. The old
police-livery.png is a blue/white palette/reference swatch, not the current body shader.
Crest, fleet numbers and extra equipment remain omitted; lightbar geometry is unchanged.

Polygon counts and mesh counts are in `build/variants.json` and both geometry
reports. Draw-call cost remains material; no several-car FPS target, physical
Safari performance or human visual approval is established by these checks.
No model is installed in the game. Review the hosted PNGs and existing touch
viewer before any integration.

## Targeted detail correction

See [before/after detail review](build/detail-review/index.html) and its audit.json.
Front/rear reveal depth is reduced from 9 to 5 mm, upper/lower border 12 to 8 mm;
rear side glass is extended 80 mm. The rear glass has a lateral painted frame to
keep its sides clear of the thin tail lenses. The actual connected backing and
reveal surfaces changed, not merely shading. The closed-body convention remains;
"thinner tailgate" here means the visible opening/reveal, not a hollow stamped shell.
Headlamps are rectangular 370×100 mm fronts with 55 mm depth. Rear lenses have
28 mm total depth across the actual corner surface. Mounted seating overlaps
with the body are intentional; no general bevel or body reshaping was introduced.

The audit compares frozen previous-master geometry against the updated master;
all preserved components, body bounds and protected central roof coordinates
match exactly. Canonical filenames and export pipeline are unchanged.

Paint boundaries use geometry-preserving support cuts and a shared point colour
attribute. They do not create detached decals or separate body panels. The
actual exported COLOR_0 palette and blue coverage over both axles are checked
by detail_export_audit.py. Civilian point colours remain white.

To rerun the preservation audit, restore the prior master from Git commit
4812b85e8b75b1c788bee7824a45145692fa7152, then pass its absolute path and
`experiments/xc70p2/build/detail-review` as arguments to `detail_audit.py` through
Blender Modeler script mode. `detail_review.py` creates close-ups; run
`detail_package.py` before `package_review.py` to refresh comparison sheets.
The existing export.sh and verify_variants.py still apply without structural changes.
