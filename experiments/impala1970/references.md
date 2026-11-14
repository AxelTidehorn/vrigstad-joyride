# Chevrolet Impala 1970 reference study

Target: **16439 Impala four-door Sport Sedan**, Chevrolet's pillarless hardtop.
Not the 163/16469 pillared sedan, Caprice 16639, two-door Sport/Custom Coupe,
or the larger 1971 generation. Accessed 14 November 2026.

## Primary specifications

[GM Heritage 1970 Chevrolet vehicle information kit](https://www.gm.com/content/dam/company/no_search/heritage-archive-docs/vehicle-information-kits/chevrolet/1970-Chevrolet.pdf),
published September 1969. PDF page 3 / printed GENERAL–2 identifies model 16439.
PDF page 20 / printed DIMENSIONS AND WEIGHTS–3 gives the **Sport Sedan** column.
The scanned table was rendered and visually read; OCR alone was not trusted.
Conversion is exactly 0.0254 metres per inch.

| Dimension | Factory inches | Metres | Status |
| --- | ---: | ---: | --- |
| Wheelbase | 119.0 | 3.02260 | Documented |
| Bumper-to-bumper length | 216.0 | 5.48640 | Documented |
| Maximum body / front fender width | 79.8 | 2.02692 | Documented, excludes mirrors |
| Rear fender width | 79.6 | 2.02184 | Documented |
| Sport Sedan design height | 55.0 | 1.39700 | Documented nominal height |
| Front overhang | 37.4 | 0.94996 | Documented |
| Rear overhang | 59.6 | 1.51384 | Documented |
| Front track | 63.4 | 1.61036 | Documented |
| Rear track | 63.3 | 1.60782 | Documented |
| Hood length, centreline | 59.8 | 1.51892 | Documented |
| Hood rear above ground | 39.3 | 0.99822 | Documented Sport Sedan |
| Standard tyre designation | G78–15 | 0.381 rim diameter | Documented Impala / Caprice footnote |

The later 121.5-inch wheelbase is **not** used. The table's H125/H126 lamp-to-ground
definitions were not established as lamp centres, so they are not used that way.
The generic AMA key-sheet illustration on PDF page 96 defines measurements; it
is not an exact 16439 drawing.

## Manufacturer visual evidence

[1970 full-size Chevrolet brochure](https://oldcarbrochures.org/United%20States/Chevrolet/1970-Chevrolet/1970%20Chevrolet%20Full%20Size/index.html):

- **Pages 16–17, “Chevrolet Impala Sport Sedan”**: correct hardtop front
  three-quarter, thin bright door-glass meeting strip, broad C pillar, four round
  lamps, horizontal grille, longitudinal hood/fender relief and amber bumper lamps.
- Pages 14–15 explicitly show the **ordinary four-door Sedan**. Its roof and
  framed door openings are excluded from hardtop shape decisions.
- Pages 10–11 Custom Coupe / 12–13 Sport Coupe: common 1970 fascia and six
  vertical rear units only. Roof, doors and cabin lengths are excluded.
- Pages 12–13 list the period colour names used for approximate paint presets.
- Pages 4–5 show a **Caprice Coupe**, not a side blueprint for this model.

[Dealer album, printed page 22](https://oldcarbrochures.org/United%20States/Chevrolet/1970-Chevrolet/1970-Chevrolet-Dealer-album1/slides/1970_Chevrolet_Dealer_Album-01-22.html)
confirms trim-line lamp differences and optional wheel covers. Its Impala side
silhouette is a coupe and is not used to set the hardtop cabin. Manufacturer scans
are linked for technical study; no scan pixels are distributed as model textures
and no reusable game-asset licence is claimed for the brochures.

## Photographs and scope

Exact file pages, photographers, licences and scope: [sources.json](references/sources.json).
The resized photographs are reference-only; no external 3D mesh or photo texture
is used in the vehicle.

- DanTD's **York and Bridge Streets** sequence explicitly identifies a 1970
  Impala Sports Sedan. It supplies correct hardtop side glass and front/rear
  three-quarter context. CC BY-SA 4.0. The side image is elevated perspective,
  cropped at both ends and snow-covered: it cannot establish the complete exterior
  silhouette. A Mercury wheel cover and damaged headlamp alignment are excluded.
- AlfvanBeem's `pic-001` through `pic-007`, CC0: front, near-side and rear detail
  evidence. This car has the **ordinary Sedan greenhouse**, so only shared fascia,
  hood relief, lower sheetmetal, wheel openings, bumpers and lights are used.
  Four round sealed beams; three vertical bumper sockets per side, clear middle
  reverse units; vertical rear-quarter markers. No hardtop roof is inferred.

## Estimates and verification limit

Tyres are estimated at 700 mm diameter / 210 mm width. Loaded radius, pressure,
spring loading and trim mass are unknown. Roof stations, glass corners, section
crown, wheel-opening curvature, bumper sections and lamp centres are visual
estimates constrained by primary dimensions. Mirrors are simplified period-style
fittings, not option-code-verified. Wheel covers approximate a period full-cover
family; their simplified eight-slot pattern is not a factory-exact hubcap.

No clean dimensioned orthographic **16439** side reference was obtained. Existing
silhouette algorithms are used only for an **explicitly limited side-glass study**.
Whole-car IoU / exact contour millimetre certification is unavailable, rather
than populated with another body variant. `silhouette.json` records a manual
six-point aperture trace, wheel centres, ground and uncertainties.
`compare_reference.py` calls existing extraction, registration, normalization and
contour comparison, without independently stretching images. All results are
canonical-pixel estimates. Overall dimensions are independently checked against
the factory table; six actual renders are manually compared with the correct
manufacturer three-quarter image.
