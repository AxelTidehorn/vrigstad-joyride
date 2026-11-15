# Blender fleet maintenance

Scope: Volvo 240, Saab 900 Classic T16, XC70 P2 and police XC70 P2. The adapter
only changes visuals; the existing driving model, engines, transmissions,
suspension and drift behaviour are unchanged. XC70 uses the existing car model.
No Micra, Impala or Duett is included.

## Author, licence and source

Models by **Axel Tidehorn**, **CC BY 4.0**. Original generators: **MIT**.
See `LICENSE` for the full grant and attribution. The source contains original
geometry, not imported meshes or photograph textures. Reference photos and
manufacturer excerpts remain outside this contribution under their own terms.

The editable masters and generators are retained at this immutable source:
https://github.com/AxelTidehorn/vrigstad-joyride/tree/ff6a0f187add7bd9b7ba052f28bd0d67e534c33a

| Runtime file under `media/vehicles/` | Editable master at that revision | Generators |
| --- | --- | --- |
| `volvo240.glb` | `experiments/volvo240/refinement/model.blend` | `experiments/volvo240/model.py`, `refine_forms.py`, `round2.py` |
| `saab900-t16.glb` | `experiments/saab900/build/model.blend` | `experiments/saab900/model.py`, `round2.py` |
| `xc70-civilian.glb` | `experiments/xc70p2/build/model.blend` | `experiments/xc70p2/model.py`, `round2.py`, `variants.py` |
| `xc70-police.glb` | same XC70 master | same geometry; `variants.py` changes paint/equipment visibility |

Download that checkout (or its `experiments/round2/vehicle-round2.zip` package)
for editing. Keep the XC70 master shared: never independently edit the police
body. Original generator helpers live in `tools/vehicle_pipeline`; procedural
regeneration also uses the external MIT Blender Modeler helpers documented in
that source. Editing/exporting an existing master needs only Blender.

## Export from a master

Use Blender 4.3.2 or a compatible newer version. The checked-in GLBs remain the
reviewed Round 2 exports. The following route exports from the editable masters
and preserves named body/wheel hubs; it does not reconstruct geometry from GLB.
`SOURCE` below is the downloaded pinned source checkout, `DEST` this repository.

```sh
blender -b "$SOURCE/experiments/volvo240/refinement/model.blend" \
  --python "$DEST/tools/vehicles/export.py" -- "$DEST/.work/volvo240.glb"
blender -b "$SOURCE/experiments/saab900/build/model.blend" \
  --python "$DEST/tools/vehicles/export.py" -- "$DEST/.work/saab900-t16.glb"
VEHICLE_VARIANT_SOURCE="$SOURCE/experiments/xc70p2" \
  blender -b "$SOURCE/experiments/xc70p2/build/model.blend" \
  --python "$DEST/tools/vehicles/export.py" -- "$DEST/.work/xc70-civilian.glb" civilian
VEHICLE_VARIANT_SOURCE="$SOURCE/experiments/xc70p2" \
  blender -b "$SOURCE/experiments/xc70p2/build/model.blend" \
  --python "$DEST/tools/vehicles/export.py" -- "$DEST/.work/xc70-police.glb" police
```

Run the original source's topology/geometry gates (`tools/vehicle_pipeline`)
and inspect the exported models before replacing `media/vehicles/*.glb`.
Blender versions/export metadata can change binary bytes; assess geometry,
materials, hubs and visibility rather than expecting byte-identical exports.
Then run `npm run check`, `npm run test:vehicles`, `npm run build` and
`npm run test:e2e`. Commit generated HTML with the source changes.

## Serving and cost

`media/vehicles` is the **only tracked asset directory**. GitHub Pages serves it
beside the committed pages. The Vite media plugin serves those same files in
development and copies them to `dist/media/vehicles` (and trailer capture builds).
There is no second `src/public` source to drift out of sync. The E2E tests load
all four URLs in both Vite development and production preview.

Detailed cars are capped at 14 on desktop and **3 on coarse pointer devices**,
within 120 m, refreshed every 0.35 s. Procedural cars cover load failure,
distance and loading. Meshes and geometry are shared; per-car paint and beacon
materials are cloned and disposed with the car. These caps bound cost; they
are not evidence of a physical phone benchmark. Safari/iPad, mobile GPU timing,
long driving sessions and final human silhouette/livery approval remain open.
