# Final major volume correction

Baseline: afe08ea (PR #65), the latest finished Duett. `before/` preserves its exact rendered views and parameter file; package.py verifies those PNG bytes against Git. The older f6aaa2d comparison is historical, not this pass's baseline.

## Why the preceding form was wrong

The prior approach had approximately 1.46 m from cowl station to nose station, a 1.0575 m front overhang including bumper, a high wing crown, tall simple glass and separate high semicircular rear mudguard volumes. It therefore looked like an invented old pickup even after detail changes.

This pass uses new original-P210 evidence: the near-side auction photograph of a 1966 P210, linked in `profile-analysis.json`, plus the coherent orange TELE EPA photographed by Fmmattsson front/rear in 2014. The latter supplies conversion architecture; the original estate supplies front, door, A-pillar and quarter-panel characteristics. The earlier Hova black EPA is no longer the rear-wing master. These conversion schemes are not blended.

The original side photograph was manually anchored to both wheel centres and the manufacturer-verified 2.600 m wheelbase, with one rigid rotation and one scale. Its diagnostic points put the cowl near vehicle Y=.53 m and height 1.12 m, the wing crown near .87 m and door-glass upper edge near 1.46 m. The previous model's corresponding volumes were materially too long/high. Values from the photograph are estimates with perspective and manual-point uncertainty, not factory surface coordinates. No full silhouette IoU or photographic millimetre accuracy is claimed.

## Actual principal-volume changes

| Element | Previous source | Current source |
|---|---|---|
| Nose longitudinal station | +2.06 m | +1.72 m |
| Cowl station | +.60 m / 1.28 m crown | +.50 m / 1.155 m crown |
| Front-wing crown near axle (before crown offset) | 1.145 m | .940 m |
| Main bonnet longitudinal span | about 1.46 m | about 1.22 m |
| Roof maximum | 1.715 m | 1.750 m |
| Cab rear limit | -.72 m | -.86 m |
| Door aperture longitudinal stations | -.52 to +.30 m | -.65 to +.03 m, with lower A-pillar shear |
| Side roof-cap depth at aperture | .07 m | .225 m |
| Rear construction | narrow box with raised independent-looking mudguards | wide, mostly planar retained quarter panels |
| Rear wheel opening | circular cut | flattened crown with radiused/tapered shoulders, derived from P210 quarter |
| Bed clear width / length / depth | 1.14 / 1.31 / .29 m | 1.43 / 1.26 / .33 m |
| Overall including bumpers | 4.365 m | 4.100 m |

The front end is a three-lobed curved cap in plan with a rolled lower apron. The centre nose, wing noses and lower plate now have distinct fore/aft positions. This is a change in the underlying closed steel, not a different grille over a flat face. The lower apron is raised towards the nose to remove the old deep chin. The bumper follows the plan curve and has real mounting brackets.

Headlamp seats are fitted to the new lower/full wing caps; glass is angled with the wings. The steel immediately surrounding the lights was revised after the first full render showed an overly deep projecting socket. Indicators were lowered clear of the headlamp glass. Wipers and mirrors were seated to the changed cowl/door, not left at previous world coordinates.

Cab roof cross-sections now leave a rounded P210 roof cap above smaller side glass. The windscreen is a lower, wider curved panel with metal header above it, rather than a large pane running into the roof. The rear wall, rear window and bed front move together. The old rear humps are removed: rear openings are cut out of actual long quarter panels continuous with the converted car body. Inner bed walls/floor/gate and the wider load space remain real closed-volume geometry.

## Render-review sequence

A detail-free source stage was generated and rendered before final fitting (`study/views`): solid bonnet, wings, cab, quarter panels, open bed, wheels and glazing. It was compared against the original near-side photo and the orange EPA's two views. The same source was then corrected for front apron depth, windscreen header, rear opening profile and lamp seats, and the complete model rendered in all seven fixed standard views. No earlier render is substituted for a final image. Before/after uses identical cameras and lighting.

## Verification and remaining limits

Modeler and repository checks are collected under build/. The body must remain one closed/wound component with no degenerate faces or body self-intersection candidates; main glazing/steel and tyre/steel checks must pass. Nine configured bed probes must reach the actual .75 m floor. Pose and actual GLB reimport, Vehicle Lab r128 loader parsing and the game selection/entry/driving test are run on the final asset. `measurements.json` compares the actual old/new meshes and protects all four wheels/rims and material colours.

Game/registration/physics files and all other cars are byte-checked against afe08ea. No driving model, engine or gearbox is changed. The same public review URL is updated with the latest GLB and PNGs; native publishing success does not imply browser WebGL QA.

Remaining uncertainty: the orange conversion's cut dimensions, exact pressed radii and bumper offsets are not independently measured. The reference side photo has perspective; the model retains existing tyre size and hub spacing for compatibility, rather than claiming these are factory-certified. The silhouette and front are now based on specific evidence, but final recognition is a human judgement, not a consequence of a valid mesh. Physical iPad Safari, the interactive hosted Site browser and hardware FPS are unverified; user visual approval is pending.
