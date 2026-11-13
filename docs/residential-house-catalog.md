# Residential house catalogue (pilot)

The playable world now supports **three finished, reusable low-poly house mesh archetypes** in `src/houses/house-library.mjs`:

| Archetype | Form | Current skins |
|---|---|---|
| `cottage` | Older Swedish gable-roof timber house, vertical siding, white trim, chimney | red, yellow, cream |
| `bungalow` | Low 1960–70s villa with hipped roof, brickwork and broad windows | mexi, brick, ochre |
| `villa80` | 1½-storey 1980s house, pitched roof, upper gable windows, panelled walls | red, green, cream |

Each prototype is baked into a single colored triangle mesh **once per type/skin/entrance orientation**.
Instances share the same geometry and material; there is not a complete mesh or material per OSM building.
The source is editable JS geometry; these are not Blender-authored GLBs or surveyed models of particular real houses.

## Placement rules

The game takes existing OSM building polygons and calculates a minimum-area oriented rectangular envelope.
A catalogue model can replace the generic box only if:
- the building is not special/landmark (`k !== 0`, `b.facade === 'bespoke'`, or area >450 m²);
- a pitched-roof profile is available, area is at least 52 m², rectangle fit >=96.5%, width >=6.5 m and length <=18.2 m;
- the site is not steep (>1.25 m change across its vertices);
- the model requires less than the allowed 0.82–1.35 horizontal scale and unequal axis scaling stays <=0.19;
- it is outside the protected 75 m area around Torget and is not one of the three safehouses.

Among fitting ordinary buildings, 40% are selected using a stable footprint hash. The type and
color family are deterministic; this does **not** change the gameplay seeded RNG sequence.
The house is rotated to the footprint axis. The entrance is one of four pre-authored door
orientations chosen from the existing road-facing wall detection.

All original building collision polygons are retained. Buildings not selected continue
through the existing procedural roof/facade/detail renderer. Major landmarks and custom
art assets remain available for manual modelling.

## Test and review

Run `node tools/check_house_catalog.mjs` to check all 36 template/skin/door geometries
for non-finite data and degenerate triangles, plus rotated footprint calculations and
deterministic catalogue selection on the provided map. Then run `python3 tools/build.py`
before committing source edits; the standalone `index.html` is checked in.

In the playable game, use `?houses=legacy` to compare the old buildings without the
catalogue (no new settings UI). The `?heights=original` study also disables catalogue
replacement so the original height comparison remains meaningful.

The first obvious trial instances can be found south of Torget near map coordinates
`x≈17, z≈−69` and `x≈51, z≈−64`. These are approximate map coordinates, not
verified real-world address labels.

**Not yet verified:** real WebGL appearance, perceived modelling quality, clipping at
doorsteps and eaves, lighting-dependent color differences and GPU performance. Review
in the actual driving game before increasing the replacement percentage.
