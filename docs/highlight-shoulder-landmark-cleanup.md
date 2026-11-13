# Highlight shoulder and temporary landmark cleanup

## Scope
This PR is a narrowly scoped follow-up to the already merged artstyle and Oliver #116 integration. It is based on **current fork main**, not an unmerged dependency or the older PR #17 branch.

## Changes
- `renderer.toneMappingExposure`: **1.13 → 1.03**.
- Replaces the formerly negligible `-0.010` upper highlight trim with a **luminance-weighted, chroma-preserving shoulder**.
  - `shoulder = smoothstep(0.59, 0.95, luminance)`
  - `rgb *= 1.0 - 0.092 * shoulder`
  - Brightest surfaces lose up to 9.2% of their post-grade display RGB intensity, while dark tones are almost unchanged. Unlike per-channel clipping or additive grey, the RGB ratios are maintained.
- Existing Classic Negative color grade, selective mist, Strong Grain, sun direction/shadow maps and DOM HUD remain intact.
- Removes the **temporary GLB study lineup** near Torget (SportRingen, Napoli, Qstar, Sågverket), its floating labels, and the now-unused external GLTFLoader script. These studies had placeholder placements and were not verified matches to the actual buildings. Their `media/*.glb` files remain in the repository for later use.
- **Mapped 1:1 terrain, buildings, landmark footprints, geographic data, gameplay and NPC/traffic rules are untouched.** Special building colors and procedural facade systems remain.

## Reversible building-height experiment
The geographic source (`tools/process.py`) currently estimates generic
building wall height **only from footprint area**:
- footprints below 40 m² → 2.8 m walls
- 40–150 m² → 5.5 m walls
- 150–400 m² → 6.5 m walls
- 400–1500 m² → 8.0 m walls
- larger → 9.0 m walls

A further roof rise of up to 5 m is added by `roofParts`. These values
explain why otherwise ordinary houses look oversized.

This PR tests more plausible, **not surveyed**, generic wall heights and
gable rises in the live scene. `?heights=original` restores the old
geometry exactly. The trial is the default while this PR is reviewed.
No dedicated menu, new dependency, alternative world or changes to map data.

| Old wall height | New trial wall height | New roof cap | Building count | Mean original → trial total height* |
|---:|---:|---:|---:|---|
| 2.8 m | 2.75 m | 2.85 m | 53 | 4.4 → 3.7 m |
| 5.5 m | 3.15 m | 2.85 m | 424 | 8.1 → 4.7 m |
| 6.5 m | 4.55 m | 3.20 m | 333 | 9.0 → 6.2 m |
| 8.0 m | 5.95 m | 3.55 m | 56 | 11.1 → 8.1 m |
| 9.0 m | 7.90 m | 3.80 m | 11 | 11.3 → 9.6 m |

*The calculation uses `b.h` and gable rise only, without extra elevation
differences along sloping footprints. The actual roof is sloped and may have
locally lower edges. These are approximate class summaries, not surveyed heights.

The height adjustment respects the footprint shapes, doors, window geometry,
roof geometry, roof shingles, chimneys and existing facade materials. Only
the `b.k===0` generic buildings are adjusted (877 buildings). The
special/landmark types `b.k===1/2` (5 buildings) remain unchanged, and
the four unverified GLB landmark studies remain disabled.

Important limitation: floor counts and real building heights are not stored
in the present map. Footprint area does not reliably imply a floor count.
Several houses may now look *too low*. This is why the test needs user-facing
before-and-after screenshots from the same camera pose and must remain Draft.

## Verification
- Real `index.html` rebuilt with map data + existing vehicle library; inline scripts parse.
- Exactly one final film render pass, no additional texture, library or draw pass.
- Compare screenshots from the **same camera, resolution and simulated frame**, especially pale facades and highlights at Torget.
- [ ] Compare default scaled houses vs `?heights=original` at Torget and at
      least one villa street. Check that garages, one-storey homes and
      two/three-storey buildings do not become unnaturally short.
- [ ] Check roof/wall junctions, roof pitch, corners, window sill and door
      positions after changing wall/roof height.
- [ ] Validate no WebGL shader compile errors on Chromium/Edge.
- [ ] Inspect highlight RGB histogram versus `main`, and check that sky, white buildings and warm roofs retain detail.
- [ ] Confirm temporary study GLBs and floating labels no longer load or render.
- [ ] Confirm grain/mist remain unchanged and UI remains clean.
- [ ] Visually review several real map locations, then consider merge.

This PR is an **artstyle review iteration**, not a final locked palette.
