# Current status: round 2

Current master/export include the subsequent body-plane, grille/lamp and hierarchy
refinements. See [round-2 assessment](../../round2/README.md) and
[comparisons](../../round2/index.html#volvo240). The wheel-arch report below is
archived first-round evidence; those approved opening profiles remain preserved.

---

# Volvo 240 — defined wheel arches, visual approval pending

Continued directly from the latest `refinement/model.blend`, frozen from parent
commit `f064b57`, rather than the original clay checkpoints or game geometry.
All Blender editing, rendering, validation and export ran headlessly in Codex.

The existing circular well boundaries now follow short flat crowns, angular
shoulders and straighter lower legs. Front crown is 355 mm above the axle, rear
350 mm, compared with the original 365 mm circular radius. Polygon half-width is
355 mm and flat crown half-span 85 mm. These are documented stylized choices,
not verified factory wheel-arch dimensions. Existing reference photographs remain
in `references/` with attribution in `references.md`; no new image source is used.

312 existing local body vertices move; redundant coplanar circular subdivisions
are dissolved and connected support loops are added at X ±0.84 m inside the wells.
These create a short, controlled reveal. No detached fender lip, floating panel,
replacement body, general bevel or subdivision is introduced. One normal per
shared vertex, weighted by exterior corner angles, controls the side-panel
shading while retaining the existing validator's indexed watertight GLB contract.
Normals are supplementary: the opening outline and support geometry actually change.

All 24 separate components retain identical coordinates, topology and transforms:
glass, wheels, rims, bumpers, lamps, mirrors, handles, grille and side trim. All
454 protected body vertices outside the local well region remain. Body bounds
are exactly unchanged: 1710 mm steel width, 4620 mm painted-shell length and
270–1430 mm body Z range. Overall fitted length stays 4820 mm; wheelbase 2650 mm,
track and wheel pivots remain unchanged. Materials retain the established matte style.

Final side, front-three-quarter, rear-three-quarter and complete/bare-body arch
close-ups were rendered from identical before/after cameras. The new opening reads
more deliberately polygonal and the side is less inflated around it. Roof and
hood remain the established 240 architecture. Remaining simplifications: opaque
glass and its existing edge artifacts, generic grille/mirror masses, simple wheel
discs and approximate nose/tail forms. No new cosmetic parts were added.

Verification: Blender Modeler 0 errors / 0 warnings; connected body with 0
nonmanifold edges, 0 inconsistent edges, 0 degenerates, positive volume and 0
nonadjacent BVH self-intersection candidates. Body has 1862 triangles; entire GLB
6162 triangles / 25 mesh objects, versus 5828 before (+334). Unchanged GLB
validator, actual Blender reimport and existing Three r128 loader pass. Source
regeneration reproduces positions/transforms for all 25 meshes. BVH is a screening
check, not exhaustive all-component collision proof. Steering/suspension travel,
physical iPad Safari performance and human appearance approval are not claimed.

Canonical editable master and export names are preserved. Historical iter_00–02
files are untouched; Git retains the preceding working master. No Saab, XC70,
game physics, runtime source or installed vehicle asset was changed.

Current same-camera comparisons and downloads:
https://vrigstad-240-review-179ef06.plushpangolin8.chatgpt.site/refinement/
