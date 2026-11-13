# Residential Environment Overhaul – Swedish small-town streets (around 2000)

## Integration basis
- New PR from AxelTidehorn/vrigstad-joyride main **after PR #19 was merged**.
- The existing 1:1 Vrigstad map, collision system, road classes, driving,
  traffic, the latest film grade and Oliver's already integrated visual changes
  remain authoritative.
- In the playable game's own `src/game.html`, not a second test world.
- Debug-only `?neighborhood=off` bypasses the new static property landscape
  without changing the player's configuration UI.
- `?houses=legacy` continues to bypass the complete house catalogue.
  `?heights=original` still shows previous procedural house heights.

## Four reusable house models
`src/houses/house-library.mjs` keeps the original catalogue mesh/instance
architecture and now contains:
1. Older timber cottage: pitched roof, timber boards, visible trim,
   chimney, red/yellow/light variants.
2. 1960–70s villa: low roof, brick/mineral colours, broad ground-floor windows.
3. 1980s 1.5-storey house: modest tall gable, upper windows and timber siding.
4. **Historical two-storey farmhouse:** genuine second floor, two-tier
   window rhythm, deep Falu red, white windboards, brown gable roof, stone
   plinth, chimney, steps and an actual small porch structure.

The fourth type has three muted skins (two reds + occasional ochre).
Brighter brown weathered roof choices now occur more often on the generic
fallback buildings; existing catalogue skins have more period-specific brown
options. Timber panels remain substantial, not fine moiré stripes.

A two-storey house is considered **only** for a broad, taller residential
footprint (`b.h>=6.5` and area >=96 m²); a small single-storey shape cannot
accidentally receive it. This is a cautious heuristic, not verified storeys.
Irregular, steep, protected, central and larger/non-residential footprints
continue to use the original generator.

## Gardens, access and street frontage
`src/environment/residential-neighborhood.mjs` runs **once at scene creation**.
It receives entry coordinates from both the existing catalogue and the
fallback procedural doors. No guessing the entry side a second time.

- Footpath: one walk from the actual entrance to the nearest physically
  plausible road edge. Surface types: gravel, pavers, simple stone;
  strips are terrain-following and slightly raised.
- Driveway: optional, 2.7 m wide, beside selected houses; gravel, asphalt,
  or simple concrete. Only generated if the side-yard route is clear.
- Exclude impossible geometry: sites without nearby road, roads behind the
  entrance, steep transfers, obstructed paths, intersections through
  neighboring buildings or locations too close to protected landmarks.
- Fence, hedge, wall or low rail: conservative **road-frontage approximation**,
  not a claim to know the legal cadastral boundary. The boundary is parallel
  to the actual road segment and drawn only where not obstructed.
- **Gaps are calculated first** by intersecting the actual entrance walk and
  optional driveway with the frontage; segments are then never created over
  those gaps. No post-hoc invisible fence clipping.
- No driveways on all lots, some lots have no boundary, and others are left
  fully open. Deterministic coordinates/seed, independent of gameplay RNG.
- Existing collision shapes remain unchanged. New garden scenery is purely
  visual (non-colliding) in this PR, intentionally so traffic and driving do
  not change. A proper obstacle/collision design is future work.

## Vegetation
A small reusable instanced vegetation set: modest deciduous, mature deciduous,
fruit trees, and spruce. Irregular clustered leaf masses, branches and
different size families replace single green balls. Planting is calculated
from footprint rear extents, road and building clearance, terrain slope,
and proximity to other trees. Protected landmarks are kept open; many
lawns stay sparse. It is not a botanical simulation.

## Performance and fallback
- House variants are still shared `InstancedMesh` meshes, not hundreds of
  unique objects.
- One shared, vertex-coloured mesh batches all walks and drives.
- Fences, stone blocks and hedges are instanced, with one batch per component.
- Trees are instanced by family for trunk, branch and crown lobes.
- No runtime allocations in the game loop. No textures painted by hand, no
  post-processing changes, no new npm dependencies.
- Placement reports `window.__residentialStats` for visual-review automation
  (counts of walks, drives, boundaries and trees).
- The fallback building generator and original procedural roof/wall material
  path are untouched.

## Tests and limitations
- `node tools/check_house_catalog.mjs`: all 48 type/skin/entrance mesh
  combinations, triangle integrity and geographic selection.
- `node tools/check_residential_neighborhood.mjs`: deterministic artificial
  48-lot block used **only in the test harness**, verifying route generation,
  instanced geometry, boundaries and nonempty gaps. It is not in the game.
- Chromium workflow compares actual map-camera shots on the same simulated
  frame before/after at Torget and residential streets.
- The live map lacks cadastral lot extents and surveyed building heights.
  Property frontages therefore remain approximations, and the module must
  omit uncertain placements rather than assert exact boundaries.
- Close-up approval of windows/roof pitch/porch, slope handling, pathway
  joints, shadows and GPU cost is still necessary before a final merge.

## Additional checks before approval
- [ ] Road-connected walks end on real street edges and do not cross buildings
- [ ] Driveway/walk gaps are actually clear in white fences, hedges and walls
- [ ] Trees avoid carriageways, front doors and houses
- [ ] No double boundaries against neighbors or copied garden patterns
- [ ] Historical two-storey type reads distinctly from 80s and 70s villas
- [ ] Some lots remain open, special landmarks and safehouses unaffected
- [ ] Compare default and `?neighborhood=off` with the same game camera
- [ ] FPS and loading on real browser hardware

This is a visual/technical iteration, not a final map of actual properties.
