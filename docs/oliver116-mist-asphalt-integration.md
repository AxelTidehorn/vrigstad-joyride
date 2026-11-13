# Oliver #116 + cinematic mist + asphalt wear – integration review

## Branch and source authority

- Integration branch based on **AxelTidehorn/vrigstad-joyride/main** at creation.
- Original upstream: **OliverRomhagen/vrigstad-joyride PR #116**
  (`6daaaa2cb72dafcc60b8892d7111cdd20cd09f97`).
- **Oliver's visual model concepts govern** additions where the fork lacks an
  implementation. When the fork already has newer, more detailed vehicle,
  facade or landmark features, preserve them instead of replacing them with
  upstream's older monolithic `game.html`.
- This is a selective, manually reconciled integration **not** a blind merge
  of PR #116. Original PR remains upstream and untouched.

## Merged from Oliver #116 into actual game
- Deterministic, instanced **spruce + birch** variations with individual
  crown/trunk meshes, bark and green tones; tree contact masks on existing
  ground texture. Existing seed for actual placement remains unchanged.
- Mottled ground, less uniform lawns, a soft gravel verge, shadowed footprint
  edges: adapted to fork's strong Classic Negative palette. Independent
  visual RNG avoids perturbing spawned cars/NPCs.
- Procedural Windows with crossbars, plinth, eave trim, chimney and darkened
  wall feet: ported **into the fork's current multi-material facade generator**
  instead of replacing it with upstream's much older one. Landmark/bespoke
  buildings remain individually controlled.
- Soft blob contact for humans/cars and vehicle height adjustment on raised
  road ribbons. These are small geometry/material helpers, not new dynamic
  lights.
- Oliver's bevelled profile, rounded wheels and glossy Phong fallback for
  `epa`, `polis`, `traktor`; preserve the fork's more detailed
  `volvo240`, `saab900`, `saab95Estate`, `newHollandT6`,
  `johnDeere6M` geometries.

## Not copied blindly
- Oliver #116's ACES + outputEncoding + sky dome **must not** be dropped on
  top of the existing film pipeline. It would cause conflicting film looks,
  two sky renderers and potential double colour conversion. Keep the
  already merged Classic Negative pipeline and stronger directional light
  as the single rendering authority.
- The fork's specialized facade materials, door placement, unique buildings,
  current vehicle library, road rendering and gameplay supersede older
  upstream generic code.
- Camera/world and NPC/traffic physics are not intentionally altered except
  vehicle vertical placement on the raised roadway as per Oliver #116.

## Mist/diffusion (in existing final-pass shader)
- Default `FILM_MIST_STRENGTH = 0.42` (subtle).
- `?mist=off`, `?mist=subtle`, `?mist=strong` for development comparisons.
- 8 extra texture taps **only when enabled**, no new render target or pass.
- Isolated bright highlights contribute a gentle warm halo; the mask
  suppresses broad white/sunlit areas using local highlight coverage.
- The picture retains full-resolution detail; **mist runs before strong grain**.
- HUD, menus, map and text remain normal DOM overlays and are never graded.
- LIMITATION: without per-material emission/specular buffers, purely screen-
  space brightness masking cannot perfectly distinguish every bright fascia
  edge from a genuine reflection. Review from normal driving distance.

## Asphalt / cracks
- More varied, subdued short and elongated patches aligned to the
  genuine map roads, **up to 220** deterministic repairs in the current map.
- Up to **350** groups of irregular hairline cracks. These sample the same
  terrain and road-lift rules as the asphalt, include small vertical clearance
  and use a separate thin line mesh. No new painted texture assets.
- Two patch tonal groups and low-opacity cracks; not decorative patterns.
- Limits and probability are inspectable in `roadRepairsAndCracks()` in
  `src/game.html`. One RNG-independent pass, no changes to road topology.
- Rendering cost: 2 batched patch meshes + 1 batched crack line mesh,
  plus modest extra geometry. Actual GPU cost requires measurement.

## Code checks
- Built `index.html` generated from current real Vrigstad map and
  current `src/vehicles/vehicle-library.mjs` with unmodified build protocol.
- All embedded inline JavaScript functions syntax-checked.
- One single existing final creative rendering pass; new mist is inside it.
- No changes to input, driving dynamics, map elevation, building polygons,
  traffic routes, or other developer's car-model sources.

## Required visual signoff before merge
- [ ] WebGL/Three.js compile check in Edge/Chrome desktop.
- [ ] Screenshot comparison before/after from Torget, a villagata,
      vegetated rural street and landmark/industrial region.
- [ ] Inspect white façades, window framing, eaves and bespoke buildings;
      confirm there are no doors blocked by window overlays.
- [ ] Inspect car tyre contact with raised and non-raised road surfaces,
      especially on slopes and at curbs.
- [ ] Check roadside greenery, tree shade, camera fog/horizon and FPS.
- [ ] Compare `?mist=off|subtle|strong` at **identical** camera positions;
      ensure big bright building edges do not develop a white halo.
- [ ] Compare `?grain=strong` and `?grain=off` to ensure mist is visible
      independently from grain.
- [ ] Inspect longer/sloping sections for floating cracks, patch overlap,
      aliasing and depth conflicts.
- [ ] Benchmark GPU and loading on real desktop/mobile devices.

**Status: visual experiment only. Do not merge until these checks have
been reviewed.**
