# Saab 900 Turbo 16 Classic, three-door, approximately 1988

Complete stylized production candidate. All Blender work runs in Codex; viewers
need only the hosted Safari review, not local Blender or software installation.

Canonical files: `model.py`, `parameters.json`, `build/model.blend`,
`build/saab900-t16.glb`. Blender collections: BODY, GLASS, PLASTIC_RUBBER, LIGHTS,
DETAILS, WHEELS. Pipeline names body/wheel_fl/fr/rl/rr and metre/+Y-front/Z-up
conventions remain intact. Separate lights, grille, badge, handle, wraparound
bumpers, mirror housings, moldings, hatch spoiler and wheel/rim masses use
restrained matte materials. The interior is intentionally absent.

## Existing workflow, reused

Reviewed Volvo `experiments/volvo240/model.py`, `refinement/model.blend`, its
three staged renderings, export and report. Its closed loft, recessed wheel-well
Boolean method, lathed wheels with hub pivots, fitted bumper sweeps and material
organization were useful. Its broad shoulder and glass shading needed care.

No Volvo sections or proportions were copied. Saab uses its own longitudinal
profiles, curved transverse crown, wedge nose, bowed windshield, long hatch,
long single side doors and quarterlights. `tools/vehicle_pipeline/authoring.py`
extracts the existing generic material/interpolation/group/sweep/detail builders
into a reusable helper; it does not replace export/validation. `review_stages.py`
uses Blender Modeler's fixed renderer and a body BVH audit. `reimport_check.py`
uses the repository's unchanged Blender quality gate on the actual exported GLB.

Three mandatory review stages were rendered and opened: A closed body only,
B body plus glazing, C complete vehicle, each at five consistent views. The
initial roof's high section was too short and its shoulder sections doubled back;
both were corrected. Later review found an unseated front molding endpoint,
degenerate micro-bevel triangles, and distracting glass normal interpolation.
Moldings now sample the body surface, micro-bevel widths respect component size,
and glazing uses restrained flat normals. Final files supersede intermediate
renders in this same build folder; no redundant model versions are retained.

## Reproduction (Codex/maintainer commands, not viewer setup)

Blender 4.3.2 verified. Blender Modeler pinned at
`c8f245982108e2627972768d4311cbe172b58137` in `/workspace/work/blender-modeler`.
The standard repository numpy/trimesh/networkx environment is used.

```sh
python3 /workspace/work/blender-modeler/scripts/bmod.py --model experiments/saab900/model.py --out experiments/saab900/build --mode none
python3 /workspace/work/blender-modeler/scripts/bmod.py --script tools/vehicle_pipeline/review_stages.py --blend experiments/saab900/build/model.blend --out experiments/saab900/build/review_log -- experiments/saab900/build
blender -b --python-exit-code 1 --python tools/vehicle_pipeline/blender_import.py -- --source experiments/saab900/build/model.blend --output experiments/saab900/build/saab900-t16.glb --previews experiments/saab900/build/repository_previews
python tools/vehicle_pipeline/validate.py experiments/saab900/build/saab900-t16.glb experiments/saab900/vehicle.json --report experiments/saab900/build/geometry.json
blender -b --python-exit-code 1 --python tools/vehicle_pipeline/reimport_check.py -- experiments/saab900/build/saab900-t16.glb
```

## Assessment and limits

Own visual assessment: a recognizable Classic 900 hatchback silhouette, long
hood, crowned roof, narrow cabin, sloping rear screen, blunt tapered nose,
wraparound bumper and simple three-spoke alloy cues. This is a complete stylized
model, not a claim of factory-exact surfacing or automatic appearance approval.
The reference photos have perspective and are not verified as model-year 1988.
See `references.md` for the source/market dimensional disagreement and assumptions.

Remaining compromises: simplified rear lamp contour, visible low-poly glass
faceting, soft shading around wheel wells, approximate door/hood shut lines,
stylized wheel spokes and emblem rather than exact production graphics. Glass
is opaque, seated over the closed body backing. Mounted component seating
intersections are intentional; the BVH body screen is not an exhaustive proof
that every component is collision-free. No glass is used to conceal body holes.

The 14,000-triangle experiment budget allows more curvature than Volvo while
remaining small for a web vehicle. The report lists actual triangles, nodes,
file size and measured Blender import time. Mesh count is a draw-call cost;
GPU FPS, several cars in-game and physical iPad Safari performance are not
verified and must not be inferred from the polygon budget or CPU import time.
No game integration, physics change, existing-model change or PR.
