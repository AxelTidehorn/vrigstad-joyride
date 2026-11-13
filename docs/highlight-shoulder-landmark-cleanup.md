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

## Verification
- Real `index.html` rebuilt with map data + existing vehicle library; inline scripts parse.
- Exactly one final film render pass, no additional texture, library or draw pass.
- Compare screenshots from the **same camera, resolution and simulated frame**, especially pale facades and highlights at Torget.
- [ ] Validate no WebGL shader compile errors on Chromium/Edge.
- [ ] Inspect highlight RGB histogram versus `main`, and check that sky, white buildings and warm roofs retain detail.
- [ ] Confirm temporary study GLBs and floating labels no longer load or render.
- [ ] Confirm grain/mist remain unchanged and UI remains clean.
- [ ] Visually review several real map locations, then consider merge.

This PR is an **artstyle review iteration**, not a final locked palette.
