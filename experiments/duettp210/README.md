# Volvo Duett P210 EPA pickup — refined

The latest source continues directly from the finished afe08ea model. See [final-pass/README.md](final-pass/README.md) for the final volume analysis and rendered review stages, corrections, verified results and limitations; [references.md](references.md) records the primary orange TELE conversion and original near-side P210 reference and factory wheelbase.

Build with the existing Blender 4.3.2 / calebrisc/blender-modeler c8f245982108e2627972768d4311cbe172b58137 workflow:

```bash
BMOD=/path/to/blender-modeler/scripts/bmod.py VEHICLE_PYTHON=/path/to/python bash experiments/duettp210/build.sh
blender -b --python-exit-code 1 --python tools/vehicle_pipeline/reimport_check.py -- media/vehicles/duett-p210-epa.glb
node experiments/duettp210/preview-check.mjs
npm run test:vehicles
npx playwright test tests/e2e/duett.spec.js
python3 experiments/duettp210/package.py
```

The existing model.py + parameters.json remains authoritative, with the same collections, body/four-hub naming, paint separation and strict exporter. One closed loft contains the revised cab, bonnet, wings, real bed cavity and connected frame. No game architecture or physics changes. The registered `duett` still uses temporary existing EPA handling, not measured P210 dynamics.

`index.html` is the seven-view review gallery; `preview.html` reuses the established Three r128 touch-orbit/fixed-camera viewer and existing optional Joyride film pass. It needs only static hosting, with the repository-relative assets supplied in the delivery ZIP. The user needs no Blender or local software. The hosted Site packages exactly the same GLB, PNGs and downloads.

`final-pass/before` preserves the previous finished renders and parameters. The original blockout is historical development evidence, not the comparison baseline. All original other cars and physics/game sources are protected by byte checks. Final user visual approval is pending; physical iPad Safari and Site browser WebGL QA have not been performed.

Hosted review: https://vrigstad-duett-epa-preview.plushpangolin8.chatgpt.site

The optional comparison audit expects the actual previous Blender file, extracted from `afe08ea:experiments/duettp210/build/model.blend`, and is invoked through Modeler with `--script experiments/duettp210/refinement_audit.py --blend experiments/duettp210/build/model.blend -- /path/to/before.blend experiments/duettp210/final-pass/measurements.json afe08ea`. Package provenance checks require the fork checkout and its Git history; the current generator/export itself does not depend on the previous model.
