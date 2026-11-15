# Major geometry refinement — previous finished Duett to current

Baseline is f6aaa2d (PR #64), not the older blockout. `before/views` and `before/parameters.json` are the actual finished asset's committed files; package.py checks camera identity and image bytes against that commit.

## Reference analysis

The same paired Hova EPA photographs by Liftarn remain authoritative for the conversion. See references.md. Original P210 evidence supplies the curved single windscreen and 2600 mm wheelbase; cab cut, rear wall, bed and mudguard proportions are conversion estimates. Low-poly simplification is a separate art choice. No exact orthographic reference or calibrated photo IoU is available.

Before changing source, the previous exact Blender side/front/rear views were compared against these perspective photographs. The main departures were a very broad rectangular grille, projecting cylindrical lamps, insufficiently separated wing/bonnet volumes, a cab that was too short and square, very thick bed sides blended into weak rear wings, and a large continuous rear sheet. Small details could not fix those volumes.

## Delivered geometry changes

* The 1.06 m grille backing becomes an 0.88 m rounded opening actually cut into the nose. Its closed backing, smaller curved chrome ring and eleven bars sit in a recess. The ring's straight spans are sampled too, so their chords cannot disappear behind crowned steel.
* Both headlights have true circular cavities and annular sockets. Outer socket fronts are fitted by rays to the actual wing surfaces. Thin 13 mm glass units replace the previous 45 mm cylinders. Lens cap normals are corrected after the physical recess; they do not substitute for it.
* Bonnet sections are narrower transversely and more crowned longitudinally. Front wing crowns rise about 50–100 mm depending on station, and end in full, rounded lamp-supporting noses. Hood and wing changes are part of the same connected steel mesh.
* Cab rear wall moves back approximately 220 mm; the roof gets a longer, rounded rear transition and a modest 15 mm crown increase, to 1.715 m. Window apertures derive from inset steel with small segmented corner radii. The smaller rear pane/frame sits on the new rear wall with much less visual thickness.
* Bed box sides are approximately 60 mm thick above a real cavity. The straight box is separated from distinct rolled rear mudguards. Interior is 1.31 × 1.14 m, floor 0.75 m, nominal rail height 1.04 m (0.29 m depth). These are conversion estimates, not factory dimensions.
* The gate has a true shallow pressing, visible rim and small hinges; lamps and LGF are smaller and seated to the new gate. The broad low rear undertray is replaced by a thin load floor and connected chassis hangers. A rear axle beam and bumper mounts attach the existing wheels and bumper naturally. Running boards support the wing-to-door transition.

Wheelbase, hubs, tyres and rim geometry are preserved exactly. Body paint, glass and detail material colours remain unchanged. Game, registration, loader, physics, engine/transmission sources and all other car GLBs are byte-identical to the baseline.

## Required second review and correction

The first combined pass was rendered in seven views (`pass1/views`). It exposed chrome ring spans hidden by the curved front plate, headlamp socket edges mismatched to the wings, and a large underside sheet in rear view. The same source was corrected: denser fitted ring, ray-fitted sockets, fuller wing ends, thin rear floor and real frame hangers. Indicators were seated to the new nose surface. Final seven views were rendered again and inspected. Failed intermediate geometry is not delivered as a final export.

## Verified / limits

See build/source-audit.json, geometry.json, pose.json, reimport.json, preview-loader.json and refinement/measurements.json. Body is one closed consistently wound component, with no degenerates or body self-intersection candidates. Main glass/steel surface intersections and tyre/body intersections are zero. Nine bed rays are derived from the configured interior (not old hardcoded cab coordinates) and all reach the real floor. Modeler reports zero errors/warnings. Existing strict GLB validator and pose/reimport gates pass. The actual final asset passes game selection/entry/driving and GLB integration checks.

The exact r128 GLTFLoader used by Vehicle Lab also parses the final GLB in Node; four hubs, dimensions and independent paint are checked. Managed Site browser infrastructure (`cua_repl.js`) is unavailable here, so interactive Site WebGL QA and physical iPad Safari/FPS remain unverified. No alternative website browser-control path was used. Game browser testing is separately documented.

Remaining: roof/wing corner radii, EPA dimensions and stock wheel details remain stylised estimates; there is no detailed interior, working tailgate, legal EPA certification or physical performance calibration. Deliberate component mounting overlaps exist; body/tyre/glass checks are not a universal intersection proof. User visual approval remains pending.
