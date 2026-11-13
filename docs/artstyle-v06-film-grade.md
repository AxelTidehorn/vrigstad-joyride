# Artstyle v0.6 – Cinematic Film Color Overhaul

## Intent
Vrigstad Joyride as a Swedish small town photographed on colour negative film.
**Classic Negative** is the principal reference. **Classic Chrome** informs the
restrained neutrals but is not shipped as a second selectable look.
Not an exact simulation of Fujifilm proprietary transforms.

## Scope
- Changed `src/game.html` palette and lighting **in the playable Vrigstad map**.
- New `src/visual/film-pipeline.js`, embedded by the existing Python build
  into standalone `index.html` (no runtime extra HTTP requests or dependencies).
- No map, asset geometry, vehicle dynamics, traffic, spawning or input changes.
- Keeps existing facade type selection, roofs, corner boards, doors, landmarks,
  patched roads and procedural asphalt.

## Pipeline / r128 colour notes
1. Render scene once into a **linear 8-bit target** with Three r128's
   **ACESFilmicToneMapping**, exposure 1.29. This compresses highlights *before*
   the 8-bit intermediate. The intermediate texture encoding is explicitly linear.
2. Shader samples the intermediate and applies a **single linear-to-sRGB
   transfer**, followed by a photo-inspired contrast curve, selective olive-green
   damping, blue separation and subtle warm highlights/cool shadows. Final shader
   emits display-ready sRGB without `<encodings_fragment>` or a second tonemap.
3. The sky gradient shader writes linear values without automatic tonemapping,
   matching legacy r128 fog (fog is applied **after** tonemapping in the built-in
   Lambert shader). The sky follows the camera. Sun is warmer and stronger while
   the hemisphere fill is reduced/cooler.
4. Generated canvas textures for terrain and asphalt explicitly declare
   `THREE.sRGBEncoding`. This fixes their previous interpretation as linear.
   Some *legacy vertex and direct hex colours* remain in the r128/legacy colour
   conventions; a future engine-colour migration should explicitly harmonize
   those instead of silently adding a second transfer.
5. Query `?film=off` temporarily bypasses only the creative grade **within the
   same render pipeline** for matched capture. It does not disable the new
   lighting or palette and is not a player settings feature.

## Artistic changes
- Sky: deeper blue upper hemisphere, neutral warm grey-blue horizon, fog matched.
- Environment: darker olive/forest foliage, more muted grass family, richer
  water blue, clearer road/soil/building separation.
- Architecture: stronger pigment on red facades, warm ochre yellows, natural
  mineral off-whites and neutral roof tones. Building-specific facade overrides
  are intact.
- Asphalt: blue-neutral road base and slightly different band for repairs;
  procedural noise remains intact.

## Why no heavy composer / LUT?
One fullscreen triangle-equivalent quad after the existing scene render is enough
to apply a coherent transform. No multipass bloom/SSAO, no imported library, no
network-hosted LUT. It adds one full-screen pass and one colour+depth target at the
active drawing-buffer resolution. The performance cost is **not yet benchmarked**.

## Regression / review checklist (draft)
- [ ] Run in Edge/Chrome WebGL; verify no shader compile errors.
- [ ] Capture *identical* camera poses in real Vrigstad:
  Torget, a street with red/ochre/light houses, wooded road/green,
  and a larger landmark or industrial building.
- [ ] Compare default vs `?film=off` at each pose for the creative pass,
  and compare main vs branch for the complete visual overhaul.
- [ ] Check sky-fog horizon (no sharp seam), white facade highlight texture,
  red timber, dark glass/vehicle paint, and vegetation shadow detail.
- [ ] Check asphalt patch visibility, speedometer/HUD unaffected.
- [ ] Measure frame time and memory on desktop + a midrange mobile.
- [ ] If texture gamma/materials look washed out, correct the source-side
  r128 colour conversion instead of layering additional tone curves.

## Development collision to track
Upstream OliverRomhagen/vrigstad-joyride **PR #116** independently adds ACES,
sky and colour-management changes in `src/game.html`. This v0.6 branch is based
strictly on AxelTidehorn's current main. The approaches overlap: **do not blindly
merge both renderer implementations**. Reconcile at the renderer/palette layer
before any upstream contribution.

## Validation completed
- Embedded `index.html` generated with current map and vehicle library.
- JavaScript parsed successfully for all inline game scripts.
- Build script uses exactly one film placeholder; normal gameplay callbacks
  and simulation functions remain in the source.
- No full-browser screenshot or GPU frame-time benchmark available in the
  authoring environment; PR intentionally remains **Draft**.
