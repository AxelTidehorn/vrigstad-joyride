# Saab 900 — round 3: glazing, nose, lamps, grille and trim

`experiments/saab900/round3.py` edits the round-2 master in place (`build/model.blend`) with Blender's Python only,
using the shared `tools/vehicle_pipeline/refine.py` (also used by the Volvo 240's round 3, whose output it reproduces
byte for byte). It is idempotent: a master carrying `round3_shape_revision = saab900-r3` is saved unchanged.

Checked against the brochure side view (`../silhouette/reference.png`, scaled to the 2.517 m wheelbase, turned black
and white and its glass regions flood-filled) and the photographs in `../references.md`:

- **Cowl:** round 2's hood rose 75 mm too high to the windscreen's base, so the hood read steep and the screen short.
  The top of the car is lowered there, fading out towards the nose, the roof and the shoulder: the hood now follows
  the drawing within 10 mm from nose to screen.
- **Nose:** the body ahead of the front wheel arch is pressed back 70 mm, so the bumper stands about 150 mm proud of
  the grille, as in the drawing; 4.66 m long against 4.687 m documented.
- **Windscreen:** one glass curving from the front round both A-pillars to the door windows, its top edge at 1.27 m,
  under the door windows' top, rounded at its corners, with one seal round it (`refine.wrapped_screen`).
- **Side windows:** traced from the drawing: the door window starts behind the A-pillar; the quarter window's sill
  dips, then sweeps up round its tip into a rear edge curving over to the top. A black B-pillar between them.
- **Backlight:** 86 % of round 2's across and up, bottom kept, cast onto the shell with a seal.
- **Lamps:** the lamps and grille fill the front from the bumper to the hood's edge; the corner lamps (amber over
  a clear parking lamp) and the outer tail lamps (amber over red) wrap round the corners in a black bezel.
- **Grille:** a chrome frame round three thick chrome slats on black, wider at the top and leaning forward.
- **Trim:** dark grey bumpers with a chrome strip, grey lower-door cladding under a chrome strip; the high black side
  line, the turbo's hatch wing and round 2's long mirror blocks are gone (small mirrors on the door's front corner).

Reproduce from the repository root, with Blender 5.3 as the `bpy` module:

```sh
python experiments/saab900/round3.py /tmp/r3/model.blend path/to/round-2/build/model.blend
python -c "import bpy,sys,runpy; sys.argv=['x','--','--source','/tmp/r3/model.blend','--output','/tmp/r3/saab900-t16.glb','--previews','/tmp/r3/previews']; runpy.run_path('tools/vehicle_pipeline/blender_import.py',run_name='__main__')"
```

The round-2 master is `build/model.blend` at this repository's revision `ff6a0f1`. `build/saab900-t16.glb` is the
export above; the game merges its parts per material and compresses it (`npm run compress:vehicles`).

Review image: `compare.png`, three.js renders of the game's GLB, round 2 above and round 3 below.

Result in the game: 13 draw calls (12 before), 15,244 triangles (7,980), 242,100 bytes delivered (154,152).

Not done: the wheels, the registration plate, the backlight's own curve.
