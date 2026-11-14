# Reference record — 1990 civilian Volvo 240 sedan

Accessed 2026-11-13. No downloaded vehicle mesh, texture, police equipment or
photographic texture is used in the model. This is original parametric geometry.

## Verified dimensions

Primary source: Volvo's **1990 240 Owner's Manual, USA & Canada**, printed p. 98
(PDF page index 129, page 130 in a one-based PDF viewer):
https://volvotips.com/brochures/240-260/instruction-books/Volvo-240-owners-manual-USA-Canada-1990.pdf

| Property | Manual's metric value | Used, metres |
|---|---:|---:|
| Sedan length | 482 cm | 4.82 |
| Width | 171 cm | 1.71 |
| Height at curb weight | 143 cm | 1.43 |
| Wheelbase | 265 cm | 2.65 |
| Front track | 143 cm | 1.43 |
| Rear track | 136 cm | 1.36 |

The manual rounds centimetres and inches independently. These are the manual's
rounded metric values, not millimetre-accurate engineering measurements. Tight
validation tolerances test our generator against its chosen targets; they do not
increase the source's precision. Do not substitute the 245 wagon's length/height.
The manual's fully loaded ground clearance is not a body sill height.

## Photographs actually opened and visually inspected

Three matching views of a 1990 UK 240 GL 2.3, photographed 2018-09-06 by
**Vauxford**, CC BY-SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/ :

- Side: https://commons.wikimedia.org/wiki/File:1990_Volvo_240_GL_2.3_Side.jpg
- Front perspective: https://commons.wikimedia.org/wiki/File:1990_Volvo_240_GL_2.3_Front.jpg
- Rear perspective: https://commons.wikimedia.org/wiki/File:1990_Volvo_240_GL_2.3_Rear.jpg

Three-quarter front: 1990 Australian 240 GL sedan, photographed 2015-06-03 by
**OSX**, released to the public domain:
https://commons.wikimedia.org/wiki/File:1990_Volvo_240_GL_sedan_(2015-06-03)_01.jpg

`references/*_review.png` are reduced-resolution PNG copies, with no crop or
retouch. The standalone side comparison additionally crops, horizontally flips,
and resizes the side photograph; its photograph portion remains CC BY-SA 4.0.
Original authors do not endorse this experiment.

The front/rear photos are perspective views, not calibrated head-on orthographic
blueprints. Camera height, pitch, focal length and occlusion limit quantitative
silhouette comparisons. No claim of photogrammetric reconstruction is made.
US/Canada dimension targets and UK/Australian shape references are explicitly
mixed for this blockout. Market-specific bumper length is unresolved; this is
not yet an exact Swedish-market vehicle specification.

## Estimated shape parameters

All other `parameters.json` values are estimates: longitudinal axle offset
relative to body centre, tire radius/width, well depth and radius, sill/belt/window
heights, pillar widths, roof width and roof/cowl/backlight positions. For example,
`front_axle_y=1.42`, rear axle `-1.23` give the verified 2.65 m separation but their
individual body-relative offsets are estimated.

Visual cues used: long gently rising hood, short flat trunk, upright greenhouse,
broad C-pillars with small rear quarterlights, nearly horizontal beltline,
moderate tumblehome, narrow track, circular front wheel opening and a rear
opening whose real contour is less circular. Approximate side-photo landmarks
(at 1400 x 482 preview resolution) were front/rear wheel centres x≈283/1028,
cowl x≈450, roof front/rear x≈585/963, rear glass toe x≈1073. These are manually
read image coordinates, not verified dimensional measurements.
