# Chevrolet Impala 1970 — four-door hardtop

[Review gallery](index.html) · [Touch / paint viewer](preview.html) ·
[Six-view PNG](review/contact-sheet.png) · [Delivery ZIP](impala1970-delivery.zip)

New original **16439 Impala Sport Sedan** body on
`experiment/impala-1970-hardtop`, based on completed refinement round 2 (`ff6a0f1`).
Everything was generated, checked, exported and rendered in Codex with headless
Blender 4.3.2. Reviewers need only a browser. No existing car, game code, physics,
traffic, main or Oliver repository is changed. Human visual approval is pending.

## Delivered asset

- [`model.py`](model.py) + [`parameters.json`](parameters.json): original
  dimensioned Impala loft, inset frames, closed wheel wells, glass and fixtures.
- [`build/model.blend`](build/model.blend): current editable master, organised
  into BODY, GLASS, CHROME, RUBBER, LIGHTS, DETAILS and WHEELS collections.
- [`build/impala1970-hardtop.glb`](build/impala1970-hardtop.glb): GLB 2.0, metres,
  +Y up / −Z forward, one closed mesh `body`, four independent `wheel_fl/fr/rl/rr`
  hub nodes. Rims, whitewalls and slots are children of their own hubs; glass,
  lamps, bumpers and fixed trim follow body motion.
- [`review`](review/contact-sheet.png): exact side, front, rear, two three-quarter
  views, higher roof/hood view, front/rear close-ups, clay blockout/final, actual
  scale comparison with latest Saab 900 and 240, dimensions and reference study.
- [`references.md`](references.md), [`notes.md`](notes.md) and
  [`summary.json`](summary.json): primary sources, estimates, critique/fixes and
  independent machine-readable checks. Raw studio renders remain in `build/final`.

## Form and construction

The 5.486 m full-size car uses its own longitudinal and transverse sections:
long low hood, swept low hardtop, broad C pillars, long deck, coke-bottle shoulder,
shorter front / very long rear overhang and low rear wheel openings. No existing
vehicle body was stretched or copied. Steel is one consistently wound closed
volume, with recessed window backing and genuine wells. The rear full-size inner
tyre pocket intersects the lower outer opening, leaving substantial connected
quarter geometry above the tyre instead of a detached skirt.

No fixed painted B pillar: front/rear door glass is physically split by a 4 mm
meeting join and narrow bright sash. Hood/fender relief rails rise up to 22 mm;
shallow supported V-reveals are real body vertices. Four round sealed beams,
paired rectangular bezels, deep horizontal grille, formed chrome bumpers and
six vertical rear sockets establish 1970 identity. The two middle rear units
have separate neutral reverse-lens material. Bumper lamps, grille slot and plate
mounts have actual pockets. Rocker chrome stops at the wheel openings.

Reused `authoring.py` / `surface_refinement.py`, pinned Blender Modeler helpers,
unchanged repository exporter and raw-topology validator. No new model pipeline,
export repair or validator weakening. Fixture rotations are baked before parenting
so Three r128 bounds match real geometry. Stable window-edge ordering makes
independent source builds match within the existing 1 µm comparison tolerance.

## Dimensions and checks

| Property | Documented / model result |
| --- | --- |
| Wheelbase | 3.022600 m; actual hubs and GLB agree |
| Overall length | 5.486400 m |
| Design height | 1.397000 m |
| Body width | GM 2.026920 m; actual GLB 2.025600 m, 1.32 mm narrower |
| Width including mirrors | 2.210 m |
| Front / rear overhang | 0.949960 / 1.513840 m |
| Front / rear hub tracks | 1.610360 / 1.607820 m |
| Tyres | Estimated Ø0.700 × 0.210 m; 15-inch rim documented |
| Triangles / glTF mesh primitives | **19,604 / 27**, below 20,000 budget |
| Materials / textures | **12 / 0** |
| Actual GLB size | Approximately 0.7 MB |

[`source-audit.json`](build/source-audit.json): body one connected component,
0 nonmanifold/open edges, 0 inconsistent edges, 0 degenerates, positive volume,
0 nonadjacent BVH body self-intersection candidates. All component source meshes
are closed / consistently wound / nondegenerate. Glass is six closed panes,
0 glass/body surface intersections, minimum sampled signed backing clearance
**1.095 mm**; 0 tyre/body surface intersection candidates (small hidden axle-mount
stubs intentionally enter the inner wall). Headlamp tops are at 0.742 m, below
the front hood. Chrome moulding joints and lens ribs contain intentional seated
fixture overlaps; this is not an exhaustive proof of all-component collision freedom.
The shoulder moulding is ray-fitted to the actual steel, with adaptive support
stations only where a straight chord would leave the panel. Across 160 probes,
maximum axis-to-steel distance is 3.341 mm, below the four-sided strip's 4.243 mm
inscribed radius. This separately checks the front-fender trim seating that a
batched-fixture contact report could overlook.

The unchanged [`GLB validator`](build/geometry.json), actual
[`Blender reimport`](build/reimport.json), pinned
[`Three r128 loader`](build/three-loader.json),
[`transient pose test`](build/pose.json),
[`independent source regeneration`](build/reproduction.json) and
[`per-instance paint test`](build/paint-test.json) pass. Actual Three bounds are
2.210 × 1.397 × 5.4864 m. The pose probe now chooses a fixed off-axis vertex:
a lathed hubcap centre pole must remain stationary during spin, so the old
first-vertex probe was unsuitable. Existing 240/Saab/XC exports are regression
checked with the improved probe without changing their assets.

Five validator tests, 11 numerical silhouette tests and six shared-geometry tests
pass. `build/protected-files.json` verifies existing masters, exports and game
sources against base commit `ff6a0f1`. No physical iPad/Safari FPS or in-game driving
test was available; this delivery prepares an asset for subsequent approved integration.

## Reference verification and remaining limits

The manufacturer labels the correct hardtop in 1970 brochure pages 16–17. Primary
GM Sport Sedan dimensions constrain scale and axles. Other body variants are
explicitly excluded from cabin decisions. See [reference scope](references.md).

No complete reliable orthographic 16439 side source was obtained. The snowy,
cropped DanTD photo cannot verify hood/roof/overhang outer contours. Therefore
**no full-car silhouette IoU or exact contour millimetre approval is claimed**.
The existing silhouette algorithms were run on its visible **side-glass aperture
only**, uniformly registered by wheel centres and ground: glass IoU 0.514 → 0.705,
mean contour distance 31.34 → 13.79 canonical px. These perspective estimates
support the aperture correction; they do not certify the car. Both overlays,
deviation maps and explicit uncertainty are in
[`reference-comparison.json`](review/reference-comparison.json).

Visually reviewed six final views and detail views show the intended full-size
mass, pillarless four-door glass, tucked rear wheels and correct major lamp
configuration. Remaining simplifications: bumper/grille central V is restrained,
hood/quarter curves remain hand-authored estimates, hubcap slots and lens optics
are simplified, script emblems and plate lettering omitted. Glass is opaque;
no interior, opening doors or animation tracks. Better clean hardtop orthographic
reference would justify a subsequent small shape pass; no major new silhouette
change is warranted from the snow-covered photo alone.

## Paint and review

The existing Three touch preview supplies rotation, pinch / button zoom, fixed
orthographic cameras, neutral materials and Joyride's film treatment. It renders
on demand, limits pixel ratio and keeps a PNG fallback. Six period-inspired
colours are stored in `paint-presets.json`, not six duplicated GLBs.
`paint.mjs` clones only each instance's body material; actual-GLB tests verify that
another car, chrome, glass, lights and wheels retain their colours. Names are
period-correct, RGB values are approximations rather than calibrated paint chips.
The future vehicle-loader adapter can call `applyBodyPaint(instance, hex)`;
game spawning and runtime integration are intentionally not wired here.

## Reproduction in the Codex / maintainer environment

Blender 4.3.2; repository vehicle-pipeline Python requirements; external
[Blender Modeler](https://github.com/calebrisc/blender-modeler) pinned to
`c8f245982108e2627972768d4311cbe172b58137`. Use its documented check/render workflow;
the repository's +Y-forward convention overrides its default −Y-forward convention.
No local software is required from the reviewer.

```bash
BMOD=/workspace/work/blender-modeler/scripts/bmod.py \
VEHICLE_PYTHON=/workspace/work/venv/bin/python \
bash experiments/impala1970/build.sh
```

`fleet.py` renders any of the latest existing masters with the same physical focus
bounds/camera/light rig. `package.py` composes genuine renders and assembles the
review ZIP after asserting every check. The historical `build/blockout/model.blend`
is retained for comparison; current source reproduces the final master.
When only comparison logic changes, rerun `compare_reference.py` / `package.py`
without rebuilding the car. The static gallery uses relative links and existing
vendored Three libraries, so it is compatible with static hosting / GitHub Pages.
