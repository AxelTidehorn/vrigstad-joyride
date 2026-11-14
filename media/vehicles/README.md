# Vehicle review — no viewer setup required

Hosted owner-private review:
https://vrigstad-240-review-179ef06.plushpangolin8.chatgpt.site

Open in Safari on iPad. One finger rotates, two fingers pinch to zoom. Buttons
provide equivalent zoom and fixed front/side/rear/top/three-quarter angles.
The view reserves room for the panels and adjusts to portrait/landscape.
The PNG sheet, reference comparison, model source, editable Blender file and
validation reports are under **Review sheets, files & findings**.

The initial static PNG is a loading poster/fallback; it is replaced by the GLB
only after the model is ready and a frame renders. A slow or failed film script
does not block model loading. A WebGL failure leaves the PNG links available.
No Blender, Python, npm or terminal is required on the user's device.

## Conventions and appearance

This extends the pre-existing Three.js r128/GLTFLoader preview. Runtime files
are vendored locally with their MIT licence; there are no CDN dependencies.
The experiment GLB is copied byte-for-byte from the reviewed `iter_02` export.
It uses authored metres and -Z forward, without model normalization. Existing
Kenney candidates keep their prior uniform 4.35 m review scale and rotation.
Camera fitting changes the camera, never stretches the Volvo.

Matte, nonmetallic materials and simple diffuse lighting suit the stylized
realism brief. The existing `src/visual/film-pipeline.js` is reused unchanged;
only preview grain/mist uniforms are restrained. Neutral clay removes the
creative grade. No game code, color grading, physics or current asset was edited.

**The new vehicle remains rejected and unapproved.** Blender source is closed,
but the GLB validator reports open/non-manifold edges and disconnected shells
in its raw attribute representation. Seven end-region overlap candidates remain.
The UI keeps those findings visible. An attractive preview does not clear them.

## Maintainer/Codex packaging and checks

All commands execute in the Codex environment, not on the viewer's device.

```sh
node --check media/vehicles/preview.js
node --test tests/vehicle-preview.mjs tests/vehicle-preview-boot.mjs
python3 tools/vehicle_pipeline/package_preview.py --dest /absolute/empty/output
```

The package contains static HTML/JS/CSS/GLB/PNG and the shared film script. Its
root `index.html` has a relative base path; it works under GitHub Pages project
prefixes as well as a site root. There is no server API, build tool or game
integration. `.nojekyll` is included. Native Sites hosting is separate from the
game and preserves owner-private access.

Checks completed: 8 gesture/camera/GLB loader tests and 3 startup/interaction
logic tests; all passed. Camera matrices were checked at 1024×768, 768×1024,
1366×1024 and 390×844. The actual pinned loader parsed the real GLB. Existing
vehicle-validator regression tests: 5 passed; the experiment itself still fails
validation as documented. Static project-prefix links, artifact hashes, exact
film-script copy and download ZIP were verified.

The startup tests use a small DOM/renderer stub with the real Three.js scene
graph, GLTFLoader, film script and GLB. They verify loading, transforms, gestures,
neutral/film switching and film-failure fallback. They do **not** exercise a GPU,
Safari or actual touch hardware. The environment did not expose its browser
control tool, so no physical iPad/Safari or browser screenshot suite is claimed.
The hosting service's automatically captured screenshot was opened separately.

## Existing traffic candidates and provenance

These are generic, unbranded **candidate assets**, not approved replacements for
Volvo 240, Saab 900, Saab 9-5, New Holland or John Deere. They demonstrate that
our project can consume separately authored GLBs. The viewer change does not
replace or spawn any of them in the game.

| File | Description | Status |
| --- | --- | --- |
| traffic/sedan.glb | Generic sedan | Candidate — no identity approval |
| traffic/van.glb | Generic van | Candidate — no identity approval |
| traffic/tractor.glb | Generic tractor | Candidate — no identity approval |
| traffic/police.glb | Generic police vehicle | Candidate — no identity approval |

All four are original **Kenney Car Kit 3.1**, **CC0 1.0 Universal** assets:
https://kenney.nl/assets/car-kit . They were obtained unchanged from the public
mirror https://github.com/Hidencod/tge-assets/tree/main/packs/car-kit on
2026-11-13; its README identifies the pack as Kenney CC0. The source models use
+Z forward; the viewer rotates them 180° around Y and scales uniformly for
comparison, without nonuniform stretching.

The traffic inspector's body topology findings are diagnostic, not approval.
The separate vehicle pipeline validator is the acceptance gate for finished hero
models, together with human silhouette review.

### Earlier hero-model research (no imports)

The previous candidate record named `Volvo 240 styled sedan car downloadable`
by Libau Media (reported CC BY, ~63.4k triangles, authorized download required):
https://sketchfab.com/3d-models/volvo-240-styled-sedan-car-downloadable-66697669831b47cea7874fc8c4544e74 .
This asset was not downloaded, incorporated into, or used to generate the new
parametric blockout. Its listing/licence would need re-verification before use.

No approved licensed Saab 900 Classic or 2002–2005 Saab 9-5 SportCombi mesh has
been imported. Do not substitute a 2011 NG 9-5 or a generic hatchback. Before
shipping any third-party CC BY asset, record its artist, source, licence and
changes in the repository's `LICENSE`.
