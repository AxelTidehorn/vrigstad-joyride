# Vehicle review assets — unbranded traffic

These four **candidate assets** are NOT approved as replacements for Volvo 240,
Saab 900, Saab 9-5, New Holland or John Deere. They are generic traffic vehicles
provided to prove that our project can consume real, separately-authored GLBs.

| File | Description | Status |
| --- | --- | --- |
| traffic/sedan.glb | Generic sedan | Candidate — unreviewed visually |
| traffic/van.glb | Generic van | Candidate — unreviewed visually |
| traffic/tractor.glb | Generic tractor | Candidate — unreviewed visually |
| traffic/police.glb | Generic police vehicle | Candidate — unreviewed visually |

All four are original **Kenney Car Kit 3.1** assets, **CC0 1.0 Universal**:
https://kenney.nl/assets/car-kit

The files here were obtained unchanged from the public GLB mirror
https://github.com/Hidencod/tge-assets/tree/main/packs/car-kit
on 2026-11-13; its README identifies the pack as Kenney CC0.

**No game vehicle is replaced or spawned by this PR.** Use
`media/vehicles/preview.html` (via an HTTP server) to inspect each model
before committing any gameplay integration. Models have a source +Z forward
axis; the viewer rotates them 180 degrees around Y and scales them uniformly
for comparison, rather than hiding distorted proportions with nonuniform scaling.

The review inspector checks GLB mesh counts, wheels, finite positions and polygon
budgets. Its body-topology output is diagnostic, not proof of approval.
The stricter body validator in the separate vehicle pipeline PR is the acceptance
gate for finished hero models.

## Actual Swedish hero vehicles

- **Volvo 240**: pursue a real reusable 3D asset. Best current model candidate
  `Volvo 240 styled sedan car downloadable` by Libau Media
  (CC BY; ~63.4k triangles; requires authorized download):
  https://sketchfab.com/3d-models/volvo-240-styled-sedan-car-downloadable-66697669831b47cea7874fc8c4544e74
- **Saab 900 Classic** and **Saab 9-5 SportCombi 2002–2005**:
  no approved licensed game-ready meshes have been imported.
  Do not substitute a 2011 NG 9-5 model or a generic hatchback.

Before shipping third-party CC BY assets, record artist name, source, license,
and changes in the repository's `LICENSE`.
