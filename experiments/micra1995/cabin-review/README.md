# Roof and side-window refinement

Baseline: ee321f829aca8d8fb867c7aeee40af7837dfecdd, compact-nose correction / PR #62. The comparison uses its actual final renders, with identical fixed cameras, lighting and scale. No older prototype was used.

## Reference-based findings

The near-side red early European three-door photograph linked in references.md shows a near-level roof centre, rounded quarter-window corners and a moderately tall but not full-height glass band. The previous mesh had a 12–15 mm crown fall from the maximum towards neighbouring centre stations, very small corner fillets, and about 422/428 mm front/quarter glass height. The photograph has perspective and its exact year is unverified; the 1995 FIA and Wikimedia photographs corroborate the pre-facelift three-door shell. These are qualitative contour observations, not orthographic millimetre reference measurements.

## Changes to the existing source

Roof stations y=-1.05/-0.20/+0.05 m changed from 1.418/1.415/1.365 to 1.427/1.427/1.375 m. Centre y=-.55 remains 1.430 m. This fills the shallow fall either side of the crown instead of lowering the car; the curved transverse roof, forward slope and rear slope remain.

The *steel* aperture sill is raised 18 mm locally, leaving the shoulder below it unchanged. Glazing is extracted from the resulting inset faces, not scaled independently. Measured final glass heights are 410.0 mm (door) and 411.1 mm (quarter), versus 422.1/427.5 mm before. B-pillar longitudinal boundaries and aperture lengths are unchanged.

Real segmented corner fillets replace the previous three-segment treatment. A requested 45 mm offset with five segments is clamped by local topology; it is not a claim of a uniform physical 45 mm radius. The shared rear roof/backlight junction retains a smaller 25 mm, three-segment fillet and is solved together to prevent intersecting reveals. The quarter pane retains its sloping C-pillar edge. Rounding is intentionally restrained and remains visibly simplified, especially at that upper rear corner.

Experimental larger/unclamped radii produced local intersections or notches and were rejected. They are not in the delivered model. The final solution was rendered again after restoring the valid local treatment.

## Verification

See measurements.json and build/source-audit.json. One connected, closed, consistently wound body; zero degenerate faces or body self-intersection candidates, zero glass/body surface intersections, positive glass backing clearance. Six separate closed glass panes. Wheels, wheel origins, materials, mesh names and front fixtures compare unchanged against the actual baseline Blender file. The hood parameters, axle distance, total length and maximum height are unchanged. Existing GLB exporter, validator, pose test and Blender reimport run unchanged. 18,716 triangles, 24 meshes, 9 materials.

Exact side, front/rear three-quarter and remaining standard views were actually rendered with Cycles and inspected. Current Micra browser selection/entry/driving log is build/cabin-play-tests.txt; generic vehicle asset checks are build/integration-tests.txt. Physical iPad Safari and a frame-rate benchmark were not performed. No game, registration or physics source changes.

## Remaining limitations

The corner roundings are a modest improvement, not a calibrated reproduction of the reference radii. The C-pillar upper corner is still rather polygonal in close view; a larger radius would require a more involved local topology revision than this conservative pass. No automatic photo IoU or photographic millimetre accuracy is claimed. User visual approval remains pending.
