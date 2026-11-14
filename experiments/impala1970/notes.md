# Modelling and critique log

## Inventory

Started from completed round-2 commit `ff6a0f1` on
`experiment/impala-1970-hardtop`, AxelTidehorn/vrigstad-joyride. Read agent,
architecture and pipeline instructions. Inspected latest 240, Saab and shared XC
sources/masters, exporter, strict raw-index validator, preview loader, wheel rig
and silhouette tools. Runtime retains older procedural cars; no production GLB
LOD or physics integration was invented. Modeler pinned at
`c8f245982108e2627972768d4311cbe172b58137`.

New Impala-specific loft, not another car's sections. Very long rear overhang,
low crown, narrowing cabin and coke-bottle shoulder. No large general body bevel
or subdivision. Rear inner pockets clear full tyres while lower outer openings
retain real quarter-panel thickness.

## A — Initial blockout / six actual clay views

1. Kept GM wheelbase, tracks and asymmetric overhangs; long full-size body reads well.
2. Pointed side-glass wedges were wrong. Sheared belt/roof stations produce true
   hardtop trapezoids, shorter rear openings and a falling lower glass line.
3. Diagonal glass artefacts came from separately triangulated nonplanar quads.
   Triangulated backing **before** extracting panes, preserving identical surfaces.
4. Closed duplicated lathe endpoint rings in the source, rather than repairing GLB.

Original blockout .blend and clay renders remain historical evidence. The sole
current authoring master is `build/model.blend`, reproduced by current source.

## B — Apertures and steel planes

1. Source inset frames, pane-wise 1.5 mm outward seating and 2.5 mm glass thickness.
   Genuine painted A/C structures; no fixed painted B pillar.
2. Physically split four door panes at a 4 mm join with slim chrome meeting sashes;
   six closed panes total. Closed steel backing remains uncut.
3. Raised hood/fender relief rails up to 22 mm. Supported shallow steel reveals
   define hood, deck, doors and lower sides; no floating body seam bars.
4. Limited aperture comparison improves. Perspective study, not full-car approval.

## C — Complete car / actual studio review

1. Four sealed beams, paired bezels, deep grille frame, six horizontal blades and
   upright supports; chrome bumpers with formed corner returns.
2. Six recessed rear sockets, four red / two clear middle reverse units, modest
   rear vertical and front amber markers.
3. Rocker chrome crossed tyres in the first complete view. Split it at both wells.
4. Plate and amber inserts were occluded behind chrome. Cut real plate, air-slot
   and lamp pockets; mounts enter backing; visible faces stay within bumper bounds.
5. Centreline rim origins tied the nearest-hub helper and parented right fixtures
   left. Shifted each fixture origin to its own hub without moving its mesh.
   Audit now checks all four rim/whitewall parents; actual GLB pose test follows.
6. The real Three loader exposed conservative oversized bounds on joined slanted
   trim (3.34 × 4.17 × 5.93 m), although actual vertex dimensions passed the strict
   validator. Baked fixture rotation/scale without moving geometry, before parenting.
   The independent actual-Three test now asserts the correct 2.21 × 1.397 × 5.486 m
   complete-car bounds. This prevents poor browser camera framing.
7. Front close-up exposed a hovering shoulder spear: the unclamped shoulder
   parameter no longer matched the actual lowered hood/fender sections. Reused
   the authoritative section function, ray-fitted its centres to actual steel and
   added adaptive stations only where a chord leaves the surface. The independent
   160-probe fit audit passes; no material or shading workaround.

## D — Budget and final appearance

Reduced tiny surround, whitewall and slot tessellation, keeping silhouette detail.
Same-material fixtures are batched separately from body. Broad pane normals avoid
thickness-wall rounding; matte glass suppresses inflated studio reflections.
Body paint has one independent material; other surfaces keep separate materials.

Remaining: simplified bumper/grille centre V, wheel-cover pattern, optical lens
details; script badges and registration lettering omitted. Full-car metric
silhouette verification lacks a suitable correct-variant reference. No physical
iPad GPU/FPS or in-game driving test is claimed.
