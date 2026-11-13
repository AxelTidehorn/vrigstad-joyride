# Standalone photographic grain — upstream contribution candidate

Target baseline: OliverRomhagen/vrigstad-joyride `6466a2fec685bc1d8688704da3e96c6747c295c4`. PR base in the fork: `review/upstream-baseline-6466a2f`; head: `contrib/photographic-grain`. Related upstream [upstream #124](https://github.com/OliverRomhagen/vrigstad-joyride/issues/124) is open. This is not based on divergent fork main and does not close [upstream #124](https://github.com/OliverRomhagen/vrigstad-joyride/issues/124)'s hardware/mobile acceptance criteria.

## Selection and integration

Upstream already has ACES, an sRGB output, converted material colors, encoded-space fog and a gradient dome. It has no photographic grain or final scene post-pass. The source fork (`8d7198c`) combines grain with its film/daylight pipeline. Only the deterministic monochrome grain operation and intensity controls are selected here; no fork sky, lighting, palette, diffusion, models or gameplay are copied.

`src/visual/scene-finish.js` renders the existing scene into an RGBA8 target, with 4-sample WebGL2 MSAA (2 on coarse devices), then samples it in one raw display-space final shader. r128 scene shaders still perform ACES and the single sRGB transfer, now selected through the target's `sRGBEncoding`. r128 target storage remains RGBA8, not a hardware decoding sRGB texture. The final ShaderMaterial has no tone-mapping or encoding chunks. In particular, upstream's fog remains in the original encoded convention; switching the target to linear would change that fog/sky relationship.

`?grain=off` / `?grain=0` bypass the integration completely: direct original render, zero extra targets. Default and `?grain=subtle` use 0.62; strong uses 1.35; numeric values clamp to 0–2. Grain has a fixed framebuffer-space seed and identical RGB offsets, modulated to protect deep shadows and bright whites. DOM HUD/minimap/menus are composited afterwards. An explicit identity-target comparison in the review harness separates the integration cost from the arithmetic cost.

Changed production files: `src/visual/scene-finish.js`, small render/resize/hook wiring in `src/game.html`, source embedding in `tools/build.py`, regenerated `index.html`. The map is unchanged.

## Verification

See `docs/review-grain/results.json` and its screenshots. Review tooling freezes simulation/camera only inside browser responses, captures direct/identity/subtle/strong, and measures the **entire scene render plus integration** using disjoint timer queries where supported. Submission time, total draw calls and triangles are recorded too. Results are software SwiftShader, not representative desktop/phone GPU FPS. Pixel values are evidence for human inspection, never portable pixel-diff tests.

Rebuild: `python3 tools/build.py`. Existing suite: `npm run test:e2e`. Focused effect tests cover bypass, numeric strength and subtle selection. Normal suite uses upstream settings; the supplemental software configuration used for this environment is documented with the final results.

## Limits / migration

No real desktop GPU or phone is attached. MSAA/target memory and bandwidth may dominate arithmetic; measure before enabling by default upstream. At 1280×720, the requested RGBA8/depth target plus four-sample color/depth buffers is roughly 35 MiB (driver allocation may differ), beyond the original canvas buffers. WebGL1 uses a basic target with no target MSAA and needs separate visual review.

Open upstream [upstream #143](https://github.com/OliverRomhagen/vrigstad-joyride/pull/143)/#147 move the build to Vite and upgrade Three.js. This candidate deliberately targets current main. Port the module into the render layer after those merge and recheck color-space/target rules against the upgraded engine. Do not merge two scene-finish implementations if photographic grades are adopted too: combine their display-space functions in this one optional final pass. No WebGPU, Worker or OffscreenCanvas work is included.

## Reproducing the software review

Install the existing development dependencies and Chromium, then run:

```sh
python3 tools/build.py
node tools/run-software-smoke.cjs
node tools/review-rendering.cjs
```

The software smoke runner copies the repository's existing assertion bodies into `work/software-smoke`, changes only their import to a page fixture, and intercepts HTML responses to suppress WebGL submissions and repeated minimap texture drawing during **functional-only** smoke assertions. The functional profile also uses a 128-pixel ground texture to avoid large 2D raster work. Normal input, simulation, camera and DOM text/state updates continue; minimap pixel rendering is checked only in the separate real captures. These tests establish state/UI behavior, not shader compilation or rendered play, and their screenshots are not visual evidence. All actual rendering/shader verification is performed separately by the full-shadow browser review captures. CSS viewport remains 1280×720 at device scale 0.5; timeouts are longer. It does not change checked-in game sources or assertion bodies. `work/` is temporary review output. Full-shadow visual captures and measurements are a separate run at 960×540, with fixed-step simulation and a camera hook injected only into browser responses. Thus passing the reduced suite is not presented as default-resolution/shadow/mobile signoff. Keep the normal `npm run test:e2e` CI job too.

## Browser captures

Open an image to inspect the original capture.

| direct | identity | subtle |
| --- | --- | --- |
| [![direct](review-grain/direct.png)](review-grain/direct.png) | [![identity](review-grain/identity.png)](review-grain/identity.png) | [![subtle](review-grain/subtle.png)](review-grain/subtle.png) |

| strong |
| --- |
| [![strong](review-grain/strong.png)](review-grain/strong.png) |


## Measured integration cost in this environment

Four complete-frame disjoint timer-query samples per condition, 960×540, with actual upstream scene/shadows and identical frozen state:

| Path | Median reported GPU ms (SwiftShader) | Draw calls | Triangles |
| --- | ---: | ---: | ---: |
| Original direct (`grain=off`) | 2865.4 | 461 | 849676 |
| Target + identity final pass | 1680.2 | 462 | 849678 |
| Target + subtle grain | 1604.1 | 462 | 849678 |
| Target + strong grain | 1483.4 | 462 | 849678 |

Queries were available and non-disjoint in this run. These counterintuitive software results include different canvas/target resolve paths, cache/order effects and a small sample count. They **do not establish a speedup**, hardware equivalence or acceptable mobile cost. They do establish that the complete target/pass integration was measured rather than timing only the grain arithmetic. Re-run randomized/interleaved comparisons on representative hardware before adoption. Raw samples and CPU submission times are retained in the JSON.

## Final verification outcome

- Python build and all embedded JS syntax checks passed; data and `map.html` are unchanged from the exact upstream baseline.
- Actual full-shadow browser render review: direct, identity, subtle and strong captures, no shader/page/console errors. Complete-frame timer measurements are above.
- Functional replay: all four effect URL checks and all four game smoke cases passed. The map assertion initially failed in an early no-render fixture because camera matrices were not updated; that harness omission was corrected, and the unchanged map case then passed separately. No production map change was needed. All nine assertion cases have passing runs.
- The normal, uninstrumented upstream suite was also attempted on clean upstream: 3/5 passed; movement/car and kiosk cases timed out on this two-CPU SwiftShader environment. That run is not reported as green and is not attributed to the contribution. The final reduced functional control run on clean upstream passed all five cases.
- Hardware/phone performance, WebGL1 visual quality and long live driving remain unverified. Draft for maintainer review, not final issue closure.
