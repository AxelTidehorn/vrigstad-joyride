# Dynamic daylight and photographic glare (experimental)

This is an **art-direction experiment in AxelTidehorn's fork**, not an
upstream proposal or a realistic weather/astronomical simulation.

## Preview controls

- Default: static afternoon lighting at 15:30 with moving procedural clouds.
- `?time=13`: midday / stronger direct light.
- `?time=19`: low warm evening sunlight and potential camera glare.
- `?cycle=on`: simulated day moves continuously (24 h in about 12 minutes).
- `?daySpeed=2`: optional cycle speed multiplier.
- `?lighting=off`: retain the previous static sun/sky exposure.
- `?film=off`, `?grain=off`, `?mist=off`: existing independent comparisons.

## Implementation

`src/visual/daylight.mjs` provides pure, testable sun state and a Three.js
rendering adapter. It reuses the existing directional light, hemispherical fill,
film-sky shader and fullscreen pass; does not alter physics or UI. No new
third-party runtime dependencies.

The skydome shader includes inexpensive procedural cloud shapes; their coverage
changes slowly. Cloud shade is a **broad illustrative approximation** and is not
yet a matching projected world-space cloud shadow map. Camera-facing glare is
restricted to the framebuffer, never the DOM HUD.

Exposure is smoothly adapted to sunlight strength. The existing ACES grade,
film grain and mist stay intact.

## Review limitations

- First-pass aesthetics, not measured physically based exposure.
- Fixed solar arcs evoke Swedish summer but are not calibrated to latitude,
  real date or true north orientation.
- Clouds are sky-only, no volumetric lighting/occlusion.
- Glare visibility is not correctly depth-occluded by near geometry.
- Requires actual browser screenshots and GPU/mobile FPS review before merge.
- Check that evening/cloudy scenes remain readable, highlight clipping is
  dramatic *only when intended*, and that shadow cascades stay stable.

## Follow-up: strong time-of-day contrast

An art-direction correction after the first test looked almost identical
between 13:00 and 19:00. The sun arc now falls much faster in late afternoon;
direct sunlight, ambient fill and scene exposure decline more sharply.

**Important:** the custom sky is rendered with `toneMapped:false`, so scene
exposure alone cannot darken it. `uSkyBrightness` explicitly fades the sky
and clouds, while zenith, horizon and fog colours shift from blue through
warm dusk to dark blue. This keeps dusk from looking like noon with orange tint.

Test `?time=13`, `?time=17`, `?time=19`, `?time=20.5`, `?time=22`
in one street view. Browser WebGL and screenshot tests are still needed.

## Exposure balance follow-up

After visual review the 13:00 shot was overexposed and 20:30/22:00
became too dark to navigate. This change reduces peak sun intensity
and midday exposure; keeps residual skylight into twilight; and
strengthens cloud-cover attenuation of direct sunlight and glare.

Night is **not** made into fake daylight: 22:00 should remain dark,
but proper streetlights, building illumination and car headlights
will be needed for a playable nighttime mode. The sky renderer and
world exposure remain separately controlled.

Compare fixed camera views at `?time=13`, `?time=19`,
`?time=20.5`, and `?time=22`. Observe clipping in white
facades and roads, dimming under clouds, and dark-road visibility.
Numerical checks are not visual confirmation.
