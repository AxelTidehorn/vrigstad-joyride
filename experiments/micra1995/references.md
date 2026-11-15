# Reference scope — 1995 European Micra K11, three doors

Inspected 15 November 2026. No AI images or imported car meshes were used.
Reference photographs/scans are linked, not redistributed with the model.

1. [Nissan / JAF FIA A-5546 homologation form](https://www.kitsdefibra.com/pdf/ficha-homologacion-fia-nissan-micra-1_3-super-s-k11-grupo-a-numero-5546.pdf), JAF approval October 1995, FIA valid January 1996, Micra 1.3 Super S K11. Pages 1–2 were downloaded and visually inspected: genuine three-door front/rear three-quarter photographs and measured dimensions. This is the pre-facelift shell, but a Super S trim, not the standard L/LX bumper specification. The actual page-2 scan says **3705 mm**, despite search-engine/OCR text sometimes reporting 3695. It lists width **1585**, wheelbase **2360**, front/rear overhang **715/630 mm**, all ±1%. Use shell/glazing/axle relationships; exclude fog lamps and trim-specific equipment.
2. [1995 European Micra 1.0 L specification](https://www.automobile-catalog.com/car/1995/2197175/nissan_micra_1_0_l.html): secondary model-specific source, three-door phase-I hatch; **3695 × 1585 × 1430 mm**. These standard-model nominal dimensions define this build. The rear overhang becomes approximately 620 mm with the common 715 mm front allocation; that allocation is an estimate for this trim, not an independent factory confirmation.
3. [1995 (M) Nissan Micra L](https://commons.wikimedia.org/wiki/File:1995_(M)_Nissan_Micra_L.jpg), Aboutdamnavantime.wiki, CC BY 4.0. Downloaded and visually inspected: correct three-door door length, small rear quarter window, curved roof and pre-facelift front. It is perspective, not orthographic. Motivated moving the door division rearward and reducing the quarter aperture.
4. [1995 Nissan Micra L 1.0 Front](https://commons.wikimedia.org/wiki/File:1995_Nissan_Micra_L_1.0_Front.jpg), Vauxford, CC BY-SA 4.0. Downloaded and inspected: **five-door**, therefore only the shared pre-facelift headlights, paired narrow slots, hood and bumper are used. Its door/glazing layout is excluded.
5. [1994 Micra Wave three-door rear](https://www.flickr.com/photos/128691640@N04/35780627113), Nivek.Old.Gold: supplemental rear/hatch reference, linked only. FIA page 1 is the primary inspected rear photograph.

No suitable exact orthographic three-door photograph was obtained. Manual silhouette comparison used the actual fixed side and three-quarter renders against these references. No automated IoU or millimetre photographic contour accuracy is claimed. Perspective photos cannot independently verify the wheelbase.

Estimated geometry: profile stations, transverse crown, panel seams, lamp boundaries,
wheel opening radii, hub tracks 1360/1345 mm, tyres Ø552 × 155 mm and 13-inch wheel
cover proportions. They are plausible stock proportions, not calibrated factory
surface data. Roof, nose, hatch and aperture shape were refined visually. Paint is
period-inspired turquoise green, not a measured Nissan paint chip.

## Comprehensive refinement: improved side source

[Near-side early K11 three-door at Nissan Autoparts](https://www.nissan-autoparts.nl/c-4276469/nissan-micra-k11-augustus-1992-november-2002/),
[original red-car photograph](https://cdn.myonlinestore.eu/9494fdab-6be1-11e9-a722-44a8421b9960/slideshow/en_US_857992_full.jpg).
Downloaded and visually inspected. It shows the correct long three-door door,
rear quarter aperture, raked A-pillar and simple two-box mass. Registration year
is not independently verified; use the shared early shell, not trim-specific
claims. This is much closer to a side view than the original research photos,
but remains perspective and is not a manufacturer orthographic drawing.

The manually traced upper profile and wheel centres are in
`refinement/profile-reference.json`. Exact Blender side projections use the
existing `silhouette_render.py`; only wheel centres define uniform registration.
No anisotropic image scaling, overlap fitting or whole-mask IoU is used. The
comparison reports estimated source-photo pixels, not verified millimetres.
Manual trace uncertainty is approximately ±6 pixels and wheel anchors ±4 pixels.
The apparent photographic overhangs differ from nominal measurements; that
perspective bias is not used to move the hubs. Photograph linked, not redistributed.
