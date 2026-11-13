# Experimental residential lot cells

Stacked on `feat/residential-neighborhood-overhaul`. This PR changes the
**visual plot-boundary placement** only; it does not create real property
boundaries, modify buildings, road data, or gameplay collisions.

- Computes finite nearest-house (Voronoi-style) cells for candidate residences.
- Clips cells against nearby mapped road widths plus a safety verge.
- Uses all eligible house sites for neighbour spacing, not just decorated ones.
- Replaces uniform road-frontage strips with optional cell-perimeter fences,
  hedges, railings and low stone walls.
- Calculates walk and driveway openings at intersections with each lot edge.
- De-duplicates nearby boundary pieces and skips building, road and steep-slope
  conflicts. Keeps the previous entrance/path geometry unchanged.
- Keeps garden-tree placements inside the estimated cell where one is available.
- `?plots=debug` shows cyan plot-cell outlines in the 3D game.
- `?neighborhood=off` still disables the entire residential layer.

This is deliberately **not a cadastral parcel model**. OSM lacks property
boundaries and cannot reliably identify every garage or auxiliary building.
House-centre bisectors may still produce implausible garden shapes around
outbuildings or unusual blocks. Real-street visual QA is needed before merge.

Checks: pure deterministic nearest-house / road clipping unit tests, existing
catalogue and neighbourhood tests, and browser screenshots from both modes
are recommended. Runtime WebGL/FPS verification is not implied by the tests.
