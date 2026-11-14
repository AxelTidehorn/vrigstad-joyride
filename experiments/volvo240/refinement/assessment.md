# Volvo 240 refinement — visual approval pending

Only one original Blender vehicle exists: the parametric Volvo 240. The four
Kenney traffic GLBs are imported candidates and were not remodeled. Continued
editing the existing model.py and parameters.json; preserved all original iter_00
through iter_02 files and references. No game source or current traffic asset changed.

Preserved wheelbase, track, cabin/hood proportions and real dimension envelope.
Repaired re-entrant sheet-metal end sections and separated the bumper envelope
from the painted body. Added BODY, GLASS, PLASTIC & RUBBER, DETAILS and WHEELS
collections while retaining pipeline-compatible body/wheel names. Glass is an
opaque stylized seated envelope over a closed body backing, not a hollow interior
or manufactured sheet-metal thickness reconstruction. Bumpers are continuous
closed sweeps with wraparound corners; no overlapping body boxes. Trim, basic
lamp/grille masses, mirrors, handles and low-sided wheel discs are separate.
Wheel origins now lie at their hubs.

Body topology and BVH screening show no boundary, winding, degenerate-face or
nonadjacent overlap findings. The existing unmodified GLB validator passes.
No exhaustive all-component intersection proof is claimed. Intended mounted
component/body overlaps remain. Nearest mirrored-vertex distance is sensitive
to asymmetric Boolean triangulation and is not a surface-symmetry measurement.

Three fixed-framing sheets show body only, body+glass and complete vehicle:
front | side | rear | three-quarter. Opened the sheets and compared with the
existing Vauxford side/front/rear reference photographs. Long hood, upright cabin,
narrow wheels, broad bumpers and simple rectangular lighting improve recognition.
Remaining shortcomings: broad/soft shoulder shading, angular roof corners,
rear arches still circular, simplistic mirror housings and grille, and glazing
edge/shading treatment needs human review. Body end forms remain simplified.
Do not add further cosmetics before deciding on these primary forms.

The GLB is review-only, not a final approved game asset. Human visual approval
and actual iPad Safari hardware testing remain pending. Existing raw topology
checks passing do not establish Volvo identity. PNGs provide device-independent
comparison. All Blender generation, rendering and checking ran in Codex.
