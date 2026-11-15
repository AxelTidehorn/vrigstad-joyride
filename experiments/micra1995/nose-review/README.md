# Compact nose correction

Baseline: 5ad10ae (latest finished PR #61 refinement), not the first prototype. Before images are retained byte-for-byte and package.py verifies their provenance and matched cameras.

The long straight descending hood was replaced by a flatter main span and a short rounded-down nose cap, by editing the existing loft stations. At longitudinal y=1.12/1.50/1.75/1.8475 m, crown heights changed from .870/.780/.725/.700 to .905/.885/.845/.800 m. Cowl .68/.955 and station .9/.925 are unchanged. Main span .9–1.5 now descends about 3.8° rather than 13.6°. This is a model control-profile measurement, not a measured reference angle. Lamps and indicators are raised 55 mm and fitted by the existing surface method.

Physical length 3.695 m, wheelbase 2.360 m and axle positions are unchanged; visual shortening comes from the blunter, flatter profile. Cabin, roof, wheels, rear and glass definitions are preserved. No physics or loader changes.

Reference: https://www.nissan-autoparts.nl/c-4276469/nissan-micra-k11-augustus-1992-november-2002/ (early red three-door near-side photograph; exact year not independently verified). This photograph has perspective and is not a manufacturer orthographic drawing. Side and front-three-quarter Blender renders were actually inspected. No exact reference millimetre deviation or new silhouette IoU is claimed. Earlier upper-profile scores refer to the previous refinement and are historical, not evidence for this hood change.

Current checks: one connected body, zero nonmanifold/inconsistently wound edges, zero degenerate faces and self-intersection candidates; repository GLB validator and Blender GLB reimport pass. 17,316 triangles, 24 mesh objects, 9 materials; 342,408-byte GLB. Existing vehicle integration checks pass, and Playwright Micra selection/entry/driving passes with the new GLB. Physical iPad Safari performance has not been tested.

Result: the side profile no longer has the pronounced single-plane wedge; front is less pointed. Remaining simplified lamp contours and grille are intentionally retained, and recognition remains a human visual judgement. User visual approval is pending.
