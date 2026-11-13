# Driving feel follow-up after V4

The original V4 implementation entered `main` via PR #36. This follow-up is deliberately separate.

## Player feedback to preserve
- All vehicles remain automatic; no manual controls.
- Controlled, easy-to-recover drifting is part of the arcade character.
- Volvo 240 was effectively trapped in 2nd gear; Saab would not reach 4th.
- Acceleration/top-speed behavior felt too abrupt for a real road network.
- Cars need mass and some visible body movement when turning and braking.

## Changes to review
- Upper gears use reachable engine-speed thresholds with enough downshift hysteresis.
- Lower startup converter boost and a speed-dependent force taper make acceleration progressive.
- Spring-damped *visual* body roll, pitch and heave are applied to a child body rig, leaving the collision body, tire calculations, terrain alignment and flat contact shadow untouched.
- The V3 direct-force comparison switch remains available.

## Validation
The pure-JS vehicle test covers shift reachability with game-scaled power, and spring motion convergence.
The browser build and e2e suite must pass on this new PR head. Review driving on the actual Vrigstad roads:
1. 30–90 km/h city/road acceleration and shift cadence for Volvo and Saab.
2. Gentle sway on curves, body movement on grass, pitch on braking and settling after steering release.
3. Drift initiation/recovery unchanged from the approved V3 feel.
4. No detached wheel/body geometry; no invisible collision geometry change.

Note: this is not true four-corner suspension or a measured model-year powertrain.
