# Micra K11 — comprehensive refinement of the existing 1995 three-door

[Six standard views](review/contact-sheet.png) ·
[Previous finished car → refined car](review/before-after.png) ·
[Rear-glass close comparison](review/backlight-before-after.png) ·
[Profile before](refinement/profile-before.png) / [after](refinement/profile-after.png) ·
[GLB](../../media/vehicles/micra-k11.glb) · [Blender](build/model.blend) ·
[Delivery ZIP](micra1995-delivery.zip)

Continues the existing Micra generator/master from **9060015** / PR #60 on
`experiment/micra-k11-refinement`. The latest finished geometry is the baseline,
not the old first blockout. Source, materials, wheel rig and export structure are
retained. No game, loader, physics or other vehicle source/asset was edited.
Everything was built, rendered and checked in Codex using headless Blender 4.3.2.
Human visual approval is pending; no local reviewer setup is needed for PNG review.

## What changed and why

- **Roof / side silhouette:** moved the upper front roof/windshield station from
  y = +0.38 to +0.05 m, ending the excessively long upper cabin. Reworked the
  descending windshield/hood and rear-hatch stations against a much better early
  three-door side photograph. Overall height stays 1.430 m. Side and lower body
  section widths are retained; this does not turn the whole car into a bubble.
- **Door and quarter glass:** changed the existing section positions into a
  swept opening: the door's upper front ends at the roof while its lower front
  meets the cowl. The prior longitudinal strips produced the wrong window
  architecture. B-pillar/door reveal now follows the near-side three-door
  reference. Quarter glass gains the appropriate raked rear boundary. The window belt is
  lowered 65 mm; handles and mirror mounts follow the corrected opening height.
  This increases the glass height without inflating the cabin. Small real
  corner bevels trim the aperture itself within the closed steel frame.
- **Rear hatch:** lowered the high blunt termination and corrected the slope
  between the roof, C-pillar and hatch. The basic rear volume stays simple and
  straight; it is not globally smoothed or subdivided. Rear corner width is
  slightly fuller, with fitted existing lamp volumes and bumper retained.
- **Rear glass root cause:** the old pane extended from y = −1.75 to −1.18 m,
  including the roof's changing direction. It contained no duplicate faces; it
  was a badly shaped single closed pane. The corrected aperture is confined to
  the hatch between −1.68 and −1.30 m. Geometry changes remove the roof wrap.
  Broad glass face normals are also calculated without the thin solidify walls
  pulling the visible surface normals sideways. No polygon offset or material
  change conceals the fault.
- **Front:** lower, more deliberately falling hood profile; fuller local nose
  corners; smaller irregular lamp outline and lens tops below the hood edge.
  Lamp patches remain fitted to the actual steel. Four real paired narrow grille
  recesses replace the two protruding black bars, matching the early front.
- **Wheel openings:** retained centres, stock tyres, original opening radius and
  well depths; added a local 4 mm, two-segment radius to the existing outer cut
  edges. No detached arch mouldings, suspension lowering or larger wheels.

At least two geometry correction stages were visually reviewed. The second
caught lenses spreading over the hood, incorrect grille depth and a still-high
rear upper outline. They were corrected in the same source, then rerendered.

## More rigorous side-reference comparison

[Reference sources and variant scope](references.md) include a newly inspected,
nearly side-on red early K11 three-door. Exact registration year is unverified;
use its common early shell, not trim claims. It remains a perspective photograph.

`refinement/profile-reference.json` records manual wheel centres and 13 upper
profile points, trace uncertainty about ±6 source pixels and wheel-anchor
uncertainty about ±4 pixels. `compare_profile.py` uses the existing generic
`silhouette_render.py` to sample the actual closed steel centreline. A single
uniform scale/rotation comes from the two wheel centres and 2.360 m wheelbase.
There is no anisotropic scaling or overlap optimisation. Photographs are linked,
not redistributed; the comparison PNGs contain geometric traces only.

| Estimated upper-profile sample deviation | Before | After |
| --- | ---: | ---: |
| Mean absolute, all points | 19.4 px | 4.4 px |
| Rear | 35.0 px | 0.7 px |
| Roof | 4.9 px | 6.0 px |
| Windshield transition | 23.7 px | 5.6 px |
| Hood / front | 18.7 px | 4.8 px |

These are **manual/perspective estimates in source-image pixels**, not factory
millimetre errors, a full silhouette mask or an IoU certificate. The small roof
score change is inside tracing uncertainty; it does not demonstrate a roof-height
regression or justify artificially raising the roof. Frontmost perspective bias
remains. Nominal dimensions take precedence over fitting photographic overhangs.
The shorter upper roof and corrected swept door opening are separately visible.

## Rear-glass investigation

`refinement_audit.py` independently measures the six actual closed panes before
and after, without relying on shading. Results: [panes.json](refinement/panes.json).
The rear pane's largest visible face angle from its best-fit plane decreases from
**41.9° to 19.8°**, RMS plane residual **40.8 → 16.1 mm**, peak residual
**106.6 → 30.3 mm**. These measure the actual mesh's curvature, not accuracy
against a factory plane. Some curvature is intentional. Duplicate-face count is
zero in both versions; source glass/body intersection count is zero after.

Rear, rear three-quarter and high rear close-ups were visually inspected. The
backlight is now coherent across those views, with a consistent lower edge and
no stripe caused by a patch of roof inside the pane. Close-up corners and seals
remain simplified low-poly geometry; exhaustive optical/factory curvature
accuracy is not claimed.

## Dimensions and compatibility

**2.360 m wheelbase; body width 1.585 m; height 1.430 m; actual total length
3.6975 m** versus nominal standard-trim 3.695 m (within the unchanged 15 mm gate).
Actual front/rear overhangs are approximately **717.5 / 620.0 mm**.
The frequently quoted 715 + 2360 + 630 mm sums to **3705**, the Super S
homologation trim length. These cannot all simultaneously sum to 3695 mm.
The standard-trim rear allocation is about 620 mm. Hubs were not moved to fit
this ambiguity or perspective photographs. All four tyres and four wheel-cover
meshes/origins are unchanged against the frozen prior master within 1 µm.

**17,316 triangles, 24 glTF mesh primitives, nine materials, no textures.**
The source remains editable/reproducible through the same `model.py`, parameter
file, BODY/GLASS/PLASTIC_RUBBER/LIGHTS/DETAILS/WHEELS collections and GLB exporter.
Paint/material values and four `wheel_fl/fr/rl/rr` names are retained. The current
asset replaces only `media/vehicles/micra-k11.glb` on this isolated branch.

The existing game choice (`?vehicle=micra`, or the intro link), independent paint,
steering/spin, body-motion and compatible FWD configuration are unchanged.
No new handling, engine, gearbox or measured-performance values were introduced.

## Checks and delivery

- Modeler geometry check: zero errors/warnings.
- One closed connected consistently wound body; no degenerate faces, open edges
  or nonadjacent self-intersection candidates.
- Six closed panes, zero glass/body intersections, minimum sampled positive
  backing clearance approximately **2.08 mm**; zero visible tyre/body hits.
- Strict actual GLB validator, actual Blender GLB reimport and exported hierarchy
  steering/spin/body-motion checks pass. Intentional trim/lens seating overlaps
  remain; not an exhaustive all-fixture collision certificate.
- Actual installed-GLB integration tests, validator unit tests and existing
  driving regression tests. Current browser suite covers Micra load/entry/driving
  and five ordinary game/map smoke tests. The final window-height revision is
  additionally rechecked in `build/refinement-window-play-tests.txt`; suite log in
  `build/refinement-browser-tests.txt` and status in `summary.json`. That initial
  run passed five cases; the existing default-game driving case exceeded its
  120-second total runner limit. It passed in isolation with a 240-second runner
  limit and unchanged assertions; see `build/refinement-retry-tests.txt`.
- `refinement/panes.json` proves wheel preservation; `build/protected-files.json`
  checks the other four installed GLBs and physics. No game source was changed.
- Before images are hash-checked against baseline 9060015. Both six-view sets use
  identical camera metadata, lighting, materials and framing. Rear-glass detail
  views also share a fixed camera rig. The old `initial/` directory is historical
  development and is not the baseline of this refinement.

Remaining limits: approximate corner/lamp curves and lens divisions, plain wheel
covers, opaque glass without detailed interior, perspective/manual side reference,
and no physical iPad Safari FPS measurement. This pass improves shape and fixes
the backlight; it does not claim a perfect factory surface or human approval.

## Reproduce

Pinned Blender Modeler: `c8f245982108e2627972768d4311cbe172b58137`.

```bash
BMOD=/workspace/work/blender-modeler/scripts/bmod.py \
VEHICLE_PYTHON=/workspace/work/venv/bin/python \
bash experiments/micra1995/build.sh
```

`review.py OUTPUT glass` runs the two extra backlight cameras through the same
renderer. For the comparison, extract `build/model.blend` from commit 9060015
outside the checkout, run `refinement_audit.py OLD_BLEND OUTPUT_JSON` in the
existing Modeler script workflow, and render that master with `review.py`.
`compare_profile.py` first writes `refinement/ortho-config.json`; render both
masters with `tools/vehicle_pipeline/silhouette_render.py`, then rerun the compare
script. It can rerun comparison logic without regenerating the model.
`package.py` asserts current reports/tests, checks baseline-image provenance and
packages source, master, GLB, PNGs and JSON evidence. See the script paths and
parameter/config JSON for exact inputs; no new general model pipeline.
