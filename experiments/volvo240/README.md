# Volvo 240 clay experiment — review required, NOT game ready

Isolated branch: `experiment/volvo-240-clay-blockout`.
Base: `AxelTidehorn/vrigstad-joyride` commit
`8d7198c3f81361c964cf3e0f988e84584dcd761e`.

Blender **4.3.2** ran headlessly and produced real images. No installation was
needed. This work stops after the initial blockout and **two correction cycles**.
No PR, integration, physics change or existing car asset change was made.

Open `renders/iter_02/model.blend`. Source is `model.py` plus `parameters.json`.
The body is an editable triangulated mesh generated from a parametric loft;
change the source parameters to regenerate the loft rather than hand-editing an
export. Parameter/source snapshots for earlier iterations are alongside their
renders. See `references.md` for sources, licences, uncertainties and dimensions;
`notes.md` for the visual review and remaining errors.

## Reproduce a single run

From the repository root, using a Python virtual environment:

```sh
python3 -m venv work/vehicle-venv
work/vehicle-venv/bin/pip install -r tools/vehicle_pipeline/requirements.txt
# External modelling/check/render helpers; keep this separate from the game.
git clone https://github.com/calebrisc/blender-modeler.git work/blender-modeler
git -C work/blender-modeler checkout c8f245982108e2627972768d4311cbe172b58137
work/vehicle-venv/bin/python experiments/volvo240/run.py \
  --modeler work/blender-modeler --out work/volvo240-review
```

Requires Blender 4.2+ on PATH (repository exporter needs 4.x+). For another binary,
pass `--blender /absolute/path/to/blender`. The pinned upstream Modeler scripts
remain unchanged. A successful generation is not an approval: **the supplied
final source is expected to produce a rejected GLB and return a nonzero status**.
`run.py` preserves stage logs, checks supplemental findings and invokes the
repository exporter/validator without repairing the result.

The exact commands used for the saved runs are in `notes.md`. Existing regression
checks: `python -m unittest discover -s tests -p 'test_vehicle_*.py' -v` (5 passed).
The orchestration wrapper was syntax/help checked; the saved iterations were
run with the individual documented commands, not rerun through the wrapper after
the correction limit.

## Existing pipeline reuse and compatibility

- Read `AGENTS.md`, `ARCHITECTURE.md`, vehicle pipeline README and game README.
- Inspected and used `tools/vehicle_pipeline/blender_import.py` unchanged: strict
  Blender body gate, GLB export with `export_yup=True`, four repository previews.
- Used `tools/vehicle_pipeline/validate.py` unchanged with `vehicle.json`. No
  asset stretch, validator weakening or post-export geometry repair.
- Used Blender Modeler `bmod.py`, `modelkit.py`, `check_geometry.py` and
  `render_views.py`; followed its SKILL.md and techniques reference. Pin above.
- `review.py` is a small camera/color adapter and extra audit, not an alternative
  exporter. Modeler defaults to -Y front; the repository requires **+Y front**,
  +X vehicle right and +Z up, in metres. The adapter keeps repository coordinates.
  All four wheel names follow the repository requirement.
- `media/vehicles/preview.html` was inspected. It assumes Kenney +Z-forward
  sources, rotates them and normalizes length to 4.35 m; loading this experiment
  there unchanged would misrepresent scale/orientation. It remains untouched.
  Existing exporter previews supply the repository's review path instead.
- Repository front/side/rear previews are slightly elevated. Additional Modeler
  front/side/rear/top views are true orthographic; three-quarter views use a
  fixed 50 mm perspective camera. Cameras/framing are identical across revisions.

The eight-view sheet has FRONT | SIDE | REAR | TOP on row 1, and right front
three-quarter | left front three-quarter | rear three-quarter | low front on row 2.
Modeler's sheet builder has no labels; this order is recorded here explicitly.

Clay colors distinguish the glazing envelope and wheel masses only. No textures,
lighting presentation pass, lamps, trim, police equipment or cosmetic detailing.
Vertex colors keep glazing within the connected closed body and one GLB material.
Four lathed wheel envelopes include small hub extensions into the inner well
walls (25 mm nominal attachment overlap); the tread clears the 365 mm radius
wheel well by 50 mm nominal radially. Full suspension and inner fenders are not
modeled. Wheel origin placement still needs a runtime animation review.

The `.blend` is inspectable. The `.glb` is retained **only as rejected validation
evidence**. Neither is approved for integration or a recognizable-Volvo claim.

The unchanged repository Workbench preview uses material diffuse colors and does
not display the shader's vertex-color glazing. Use `clay_*.png` from the Modeler
adapter for the readable glazing envelope; use `repository_previews/` as the
unaltered pipeline render evidence. No presentation shaders were substituted.
