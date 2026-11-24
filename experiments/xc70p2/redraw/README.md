# Volvo XC70 P2 — redrawn

Round 2's XC70 shell (a triangulated loft with the windows, gaps and arches cut into it) showed facets and waves, and
its front read as a wedge. This round draws the car again from the multi-view drawing of the P2 XC70 (side, top,
front and rear views in one scale) and the photographs in `../references.md`, keeping round 2's wheels, materials and
the civilian/police variants.

- `../redraw.py` builds the body as a low-poly quad cage of cross sections (key sections drawn in its `SECTIONS`,
  interpolated along the car), creased along the character lines and subdivided once. The rear is trimmed with its
  own surface (`rear_cut`), so the tailgate meets the sides in a sharp corner and stands on the bumper's ledge.
  The black plastic (bumpers, sills, flares' lips, the nose round the grille) is a skin 4 mm outside the body, so the
  body stays one closed, single-material shell the game paints. Glass, seals, lamps, grille, cladding, flares,
  mirrors, roof rails, plates and skid plates are cast onto it; the tail lamps are solids of their own that form the
  rear corners. The police equipment (light bar, grille lamps, bull bar with three lamps) is in the POLICE collection.
- `../shell.py`: the wheel openings (`cut_arches`, `wheel_wells`) the cage reuses.
- `../simplify.py`: planar decimation of the parts (never across a material, a sharp edge or a bend); the body and
  the glass are left as built.
- `../variants.py`: unchanged, except that the police's blue panels stay on the sides (not over the hood's edge).

Reproduce from the repository root, with Blender 5.3 as the `bpy` module:

```sh
python experiments/xc70p2/redraw.py /tmp/xc/model.blend experiments/xc70p2/build/model.blend
python experiments/xc70p2/simplify.py /tmp/xc/simp.blend /tmp/xc/model.blend 1.5
# then per variant (civilian, police): variants.apply(name), save, and export with tools/vehicle_pipeline/blender_import.py
```

`model.blend` here is the simplified master; `xc70-civilian.glb` and `xc70-police.glb` are its pipeline exports
(about 23,000 triangles; the glass is one `glass_envelope`). `review.png` shows both variants.
Known limits: flat lamp lenses; the hood keeps a faint unevenness near its front edge.
