# Blender vehicles on Oliver's r187 architecture

This changeset is **stacked on V4 driving**. The base is Oliver's open
Three.js r187 upgrade (#147), which itself depends on Vite/TypeScript (#143).

## Boundaries

- `src/game/sim/driving-v4.mjs` owns calculations for engine, automatic
  transmission, wheel grip and vehicle motion. It has no THREE or DOM imports.
- `src/game/render/body-motion.mjs` models only visual roll, pitch and heave.
  It does not change physical collisions or terrain contact.
- `src/game/render/vehicle-assets.mjs` is the GLTFLoader adapter. The four
  GLBs are renderer assets, not input to vehicle physics.
- `src/game/main.ts` remains a legacy bridge. When Oliver splits the game
  into sim/render/input modules, move each integration point to its matching
  boundary rather than pulling THREE dependencies into simulation.

## Assets and distribution

The GLBs were generated in Blender in the contributor fork and updated in
the second refinement round (experiment branch `experiment/vehicle-refinement-round2`).
The editable masters and generators stay in that experimental branch.
For upstream inclusion, the contributor and maintainer should confirm asset
ownership and distribution permission explicitly; this note is not a license grant.

While GitHub Pages serves committed root-level `index.html`, the files live
in both `media/vehicles/` (production root) and
`src/public/media/vehicles/` (Vite development and dist output). This is a
temporary duplicate for the deployment transition. Once #45 publishes `dist/`
directly, consolidate to a single source in Vite public assets and update the
URL strategy.

The loader uses the Three.js r187 package via
`three/addons/loaders/GLTFLoader.js`, not the old r128 CDN global.

## Model contract

Four types: `volvo`, `saab`, `xc70`, `polis`.

Each GLB must contain a `body` node and the four separate wheel nodes
`wheel_fl`, `wheel_fr`, `wheel_rl`, `wheel_rr`. Civic car instances get
independent body material clones for colour variation; police decoration and
blue light emissive materials are kept separate. Named wheel nodes are
detached from the leaning body rig, allowing steering and travel without
tilting the contact patches.

A maximum of 14 nearby cars display the detailed GLB at a time. Distant
vehicles use the procedural fallback. The current loader still clones
templates for hidden cars; this needs memory/FPS profiling on iPad.

## Gameplay and known limitations

V4 dynamics runs for a driven player car and police pursuit. Civilian
path-following traffic still uses the prior kinematic movement. Collision
separation remains an arcade approximation (not a per-model collision hull):
the long Impala and other future vehicles will need model-size-aware bounds.
Do not claim physically calibrated powertrains.

The stage has passed headless Chromium Playwright integration on the combined
review branch. Safari/iPad actual performance, glare, display accuracy and
visual appearance still require manual review.

## Verification

Run `npm ci`, `npm run check`, `npm run data`, `npm run build`,
`npm run test:driving`, `npm run test:vehicles`, `npm run test:e2e`.
Do not manually edit generated `index.html`. Build it through Vite.
