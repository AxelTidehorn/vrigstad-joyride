# Saab 900 Classic Turbo 16 three-door — reference and assumptions

Target: approximately 1988, facelifted Classic 900 three-door hatch, not NG900,
not 9000, not a sedan or convertible. No imported 3D mesh or photo texture.

Documented dimensional targets: length 4.680 m; body width 1.690 m; height 1.420 m;
wheelbase 2.517 m. The Dutch manufacturer brochure indexed as TECHNISCHE
SPECIFICATIES 1988 lists 4680/1420/2517 and a 1755 width drawing; a direct PDF
fetch was denied (403), so its drawing was not visually inspected:
https://900classic.nl/pdf/brochure56_saab-900_1987.pdf

Supporting model-specific datasheets:
https://www.automobile-catalog.com/car/1988/3024665/saab_900_turbo.html
(1988 North America three-door: 4687 x 1690 x 1420 mm).
https://www.automobile-catalog.com/car/1986/3024335/saab_900_turbo_16_s_catalyst.html
(phase-II European T16S, 1986–mid-1988: width 1695, height 1405, wheelbase 2517).
These secondary sources and the indexed brochure are not a factory engineering
drawing verification. The chosen 4680/1690/1420 envelope is a documented nominal
Classic T16 target, not an exact promise of Swedish 1988 T16S ride height or trim.
The 7 mm market length variation and 15 mm sport-suspension height variation
remain explicit. No dimensions are inferred from photographic pixels.

Photographs actually downloaded and visually inspected: Alexander Migl,
CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/), photographed
26 October 2025. Their exact model year and wheel originality are unverified.
They show the relevant facelifted Classic three-door Turbo architecture:
https://commons.wikimedia.org/wiki/File:Saab_900_(first_generation)_three-door_hatchback_Turbo_DSC_2936.jpg
https://commons.wikimedia.org/wiki/File:Saab_900_(first_generation)_three-door_hatchback_Turbo_DSC_2938.jpg
`front.png` is the rear three-quarter source photograph; `rear.png` is the front
three-quarter source photograph (download naming retained). Copies are resized
PNG conversions only. No endorsement. Photo licence stays CC BY-SA 4.0.

No calibrated orthographic source was obtained. Lens/perspective limits are
recorded rather than treating the photographs as blueprints. Rounded screen,
sloping nose, long clamshell hood, short bowed roof, narrow cabin, long sloping
hatch, tapered rear lamp locations and wraparound bumpers informed the profiles.

Estimated parameters: axle placement relative to body centre (front +1.260,
rear -1.257 m), track 1.43 m, tire radius .305 m, arch radius .350 m, cabin
stations, transverse roof crown, 55 mm windshield bow, lamp/trim sizes, glass
seating and alloy approximation. Tire choice, badge graphic and spoiler are
stylized assumptions; there is no interior. Glass is opaque stylized geometry
seated over the closed body envelope; this is not manufactured sheet-metal
thickness or a hollow cabin reconstruction.

## Hood correction / silhouette verification references

- Saab workshop manual, **Technical Data / General 010-1**, 1979–1988 compilation:
  <https://z90.pl/saab/pdf/SAAB%20900%2079-88/0%20-%20Technical%20Data.pdf>.
  Inspected page lists wheelbase **2517 mm**, hatchback length **4687 mm**
  (sedan 4680), body width **1690 mm**, nominal height **1419 mm**.
  Its dimension illustration depicts a four-door sedan: **not used as the
  hatchback silhouette**. Existing model length 4680 and height 1420 retained;
  7 mm length discrepancy is documented, not silently stretched away.
- Saab-Scania AB, Danish **Saab 900/900i**, copyright 1985, 1986 range:
  <https://motorarkiv.dk/brochurer/SAAB_900_og_900i_1985.pdf>.
  Rear cover has a genuine three-door Classic 900 illustration. Its small,
  undimensioned pre-facelift side drawing is the manually traced silhouette
  **proxy**, not an exact 1988 Turbo 16 engineering master. Nearby dimensioned
  side figures are five-door; do not conflate them with this three-door image.
  Crop in `silhouette/reference.png`: render PDF page 23 to width 4800 with
  `pdftoppm`, crop `(2510,330,3130,620)`, resize 1240×580. Axle points and manual
  contour/control curves are committed in `silhouette/saab900.json`.
  Original illustration © Saab-Scania AB 1985, reproduced here solely as a
  small technical review excerpt; no game-asset licence or public-domain claim.
- Existing Alexander Migl front three-quarter photograph (`references/rear.png`,
  filename inherited) reviewed again for facelift hood crown, cowl separation
  and headlamp seating. CC BY-SA 4.0, source URLs above. Perspective photo is
  qualitative evidence; exact year and millimetre geometry are unverified.

The proxy has roughly 2–5 source-pixel tracing uncertainty plus unknown drawing
stylization and facelift differences. Reports explicitly keep
`metric_geometry_verified:false`; exact geometric millimetre errors cannot be
certified. Millimetre **changes within the Blender model** are separately measured
from real mesh coordinates and do not imply exact agreement with the real car.
