# Volvo 240 — round 3: greenhouse, glazing, lamps, wheels and mirrors

`experiments/volvo240/round3.py` edits the round-2 master in place (`refinement/model.blend`) and is idempotent:
a master carrying `round3_shape_revision = volvo240-r3` is saved unchanged. It needs only Blender's Python (`bpy`)
and the shared, bpy-only `tools/vehicle_pipeline/surface_refinement.py`, not Blender Modeler. Compared with the
photographs recorded in `references.md`:

- **Greenhouse:** the round-2 side glass leans in about 18 degrees (0.80 m from the centre line at the glass base,
  0.65 m at the roof edge), which reads narrow beside the photographs. x is scaled linearly with height above the
  glass base (1.09 at the roof), so the side stays a plane at about 12 degrees, 0.71 m at the roof edge. Only
  vertices above 0.94 m, between the backlight base and the cowl, and inboard of the shoulder (|x| < 0.80 m) move,
  in the body and the glass envelope alike; custom normals are rebuilt with `surface_refinement.panel_normals`.
  Roof height (1.43 m), wheel wells, shoulder and length are unchanged.
- **Glazing:** black seals round every window (16 mm outside the glass, lapping 6 mm over it), a black B-pillar and
  quarter divider as on a 240 GL. The side glass is rebuilt with rounded upper corners (75 mm). The round-2
  outline reached round onto the A- and C-pillars' rounded corners, where the shell faces forwards or back; each
  window is cut back to the shell that faces within 35 degrees of the side, its seal included. Each glass is flat (it
  can't crease), on the plane that fits the shell under it, set on the shell's outermost point there and 5 mm off it.
  Its seal slopes from 9 mm proud at the glass down to 3 mm on the shell, so where the shell falls away from the
  glass's plane the seal meets the paint instead of standing out past the pillars. All three windows have one
  straight bottom edge at the highest of the round-2 bottoms (0.98 m), so the belt line runs straight from the A- to
  the C-pillar, as on the car.
- **Windscreen and backlight:** round 2 laid each as a flat sheet over the closed shell, wrapping round onto the A-
  and C-pillars, where it stood out past them (a separate plate at the C-pillar, a spike at the top of the A-pillar
  seen from the side). Both go, and new glass with its own seal is cast onto the shell. The screen is 91 % as wide,
  so it stays on the shell's front, sits nearer flush (glass 9 mm, seal 13 mm proud), and its seal slopes down to 3 mm
  at its outer edge, so its end shows no step against the roof. The backlight is smaller, as in the photographs:
  88 % as wide and 80 % as tall, bottom edge kept. Where a seal's edge reaches past the shell's rounded edge, it stays
  on the window's plane. The paint round both is the shell itself. All the glass is now one mesh, still named
  `glass_envelope`, which the pipeline's tools key on.
- **Tail lamps:** the 1990 unit, 0.40–0.79 m from the centre and 0.545–0.735 m high, just above the bumper,
  wrapping 75 mm round the corner: a black bezel, an upper row (amber outer, a small clear reversing lamp, red) over
  a red lower row, and darker red ribs across the red lenses.
- **Front:** amber corner indicators beside the headlamps, wrapping 70 mm onto the wings, and a black lip under the
  front bumper, where the shell's rounded underside otherwise shows like a tub.
- **Wheels:** the round-2 tyre's flat face was smoothed into its tread, so it shaded like a ball, and its rim ring
  stood 7 mm proud. Each tyre is rebuilt in place (same object, name, hub and position): a flat face, a chamfered
  shoulder and a round tread, sharp between them; and a shallow full wheel cover, 0.205 m radius, at most 12 mm
  proud, like the photographs' steel covers.
- **Mirrors:** round 2's were 23 cm boxes along the car; now 12.5 cm out, 9 cm along and 11 cm tall, tapering, on
  the door below the A-pillar.
- **Draw calls (#408 in the game repository):** every static part, round 2's included, is merged into one mesh per
  material (`trim_rubber`, `grille`, `lamp_front_lenses`, `lamp_indicators`, `lamp_rear_red`, `lamp_rear_ribs`,
  `lamp_rear_reverse`). The body (the game paints it), the glass (`glass_envelope`; the game cracks it) and the four
  wheels with their covers (they spin) stay apart: 17 draw calls, against 31 before. Rounded corners get segments by
  how far they turn, the flat side glass is a single fan, and the tyres have 24 segments, not 28.

Reproduce from the repository root, with Blender 5.3 as the `bpy` module (or `blender -b --python`):

```sh
python experiments/volvo240/round3.py /tmp/r3/model.blend path/to/round-2/model.blend
python -c "import bpy,sys,runpy; sys.argv=['x','--','--source','/tmp/r3/model.blend','--output','/tmp/r3/review-only.glb','--previews','/tmp/r3/previews']; runpy.run_path('tools/vehicle_pipeline/blender_import.py',run_name='__main__')"
npx gltfpack -i /tmp/r3/review-only.glb -o /tmp/r3/volvo240.glb -c -kn -km -noq   # the game's GLB
```

The round-2 master is `refinement/model.blend` at this repository's parent revision `ff6a0f1`; on the round-3
master the script saves the file unchanged.

Review image: `compare.png`, three.js renders of the delivered game GLB, round 2 above and round 3 below. The
exporter's own previews need a GPU context and weren't rendered headless. Re-exporting the unchanged round-2 master
with Blender 5.3 and gltfpack 1.3.0 (`-c -kn -km -noq`) reproduced the delivered game GLB geometry exactly (31 of 31
meshes, 0 mm), so the Blender version change doesn't move geometry.

Result: 17 mesh nodes and draw calls (31 before), 9 materials (6), 12,996 triangles (9,812), 1.830 × 1.433 × 4.820 m
over the mirrors (unchanged), delivered (compressed) 183,840 bytes (136,696). The triangles round 3 adds are mostly
the seals and the tail lamps' ribs; the body is round 2's 5,400.

Not in round 3 (the game repository's issue #407): the grey lower side moulding, one-piece headlamps, crisper
body creases (tried as angle-based sharp shading; not adopted yet).
