"""Saab 900 round 3: glazing, lamps, bumpers, side cladding and mirrors, edited into the round-2 master in place.

Usage: python round3.py OUT.blend [IN.blend]   (Blender's Python, bpy only; see refinement/round3/README.md)
Idempotent: a master already carrying this revision is saved unchanged.
"""
from pathlib import Path
import sys, json, math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/vehicle_pipeline'))
import surface_refinement as S
from refine import Glazing, face_grid, glazing, material, mirrors, plate, solid, take_envelope

REVISION = 'saab900-r3'

# Glazing: black seals round every window and a black B-pillar, as in the photographs. The round-2 screen wraps round
# the A-pillars a little; the backlight (the hatch glass) keeps its size.
# The hatch glass is round-2's size but rounds onto the C-pillars, so it reads too big: 86 % across and up, bottom kept.
# The screen reaches the A-pillars and further down towards the cowl than round 2's, so the hood doesn't read as steep;
# Side windows, traced from the brochure's side view (silhouette/reference.png, 247.5 px/m from the wheels), turned
# black and white and the glass regions flood-filled, then read along the inside of the black seal lines (the seats'
# head restraints cut into the fill), in body metres (y, z). The screen wraps round the A-pillar, so the door window
# starts well behind round 2's; the quarter window's sill dips, then sweeps up round its tip into a rear edge that
# curves over to the top (the tip and the sill along the outer seal line, as marked up in review).
# The screen wraps round the A-pillars to just ahead of the door windows, one glass with one seal: its sides end on
# this line (y, z), a seal's width ahead of the door window's front edge.
SCREEN_PILLAR = [(0.548, 0.945), (0.367, 1.270)]
SCREEN_TOP_Z = 1.27   # the screen's top edge, its seal just under the door window's top (1.29 m), not up on the roof
DOOR_WINDOW = [(0.513, 0.940), (-0.356, 0.948), (-0.364, 1.305), (0.315, 1.293)]
QUARTER_WINDOW = [(-0.437, 0.955), (-0.62, 0.948), (-0.759, 0.941), (-0.92, 0.950), (-1.056, 0.970), (-1.155, 0.995),
                  (-1.192, 1.030), (-1.199, 1.064), (-1.174, 1.114), (-1.095, 1.158), (-0.957, 1.242), (-0.848, 1.299),
                  (-0.457, 1.301)]
GLAZING = Glazing(rubber='charcoal plastic rubber', screen_width=0.98, screen_height=1.14, screen_rings=6,
                  screen_deep_m=0.09, screen_even=True, screen_step=0.08, backlight_rings=2, backlight_width=0.86, backlight_height=0.86,
                  quarter_radius=0.06, side_outlines=[DOOR_WINDOW, QUARTER_WINDOW],
                  screen_wrap={'pillar': SCREEN_PILLAR, 'top_z': SCREEN_TOP_Z, 'radius': 0.10})
# (screen_deep_m: the screen is bowed 55 mm, its edges that far behind its middle; quarter_radius: the tip's)

# Cowl: against the brochure's side view (silhouette/reference.png, scaled to the wheelbase), round 2's hood rises
# 75 mm too high to the windscreen's base, so the hood reads steep and the screen short; the roof, the screen's top
# and the tail are within about 20 mm. The top of the car is lowered by COWL_DROP (y, metres down), fading to nothing
# below COWL_FROM_Z and over COWL_BLEND_M above it, and towards the shoulder, so the doors stay where they are.
COWL_DROP = [(0.48, 0.0), (0.93, 0.075), (1.02, 0.073), (1.43, 0.028), (1.82, 0.0)]
COWL_FROM_Z = 0.72
COWL_BLEND_M = 0.20
COWL_SHOULDER_X = 0.79          # the shoulder, where the hood's flat top falls to the doors' top (m)
COWL_SHOULDER_BLEND_M = 0.09    # fully lowered inboard of 0.70 m

# Nose: in the brochure drawing the body's nose (the lamps' faces) is 0.905 m ahead of the front axle and the bumper
# stands 0.135 m proud of it; round 2's nose reaches 0.98 m, nearly as far as its bumper. The body ahead of the front
# wheel arch is pressed back to NOSE_Y, and the bumper moves back BUMPER_BACK_M: 4.66 m long, against 4.687 documented.
NOSE_FROM_Y = 1.62
ROUND2_NOSE_Y = 2.24
NOSE_Y = 2.17
BUMPER_BACK_M = 0.02

# Mirrors: round 2's were 23 cm long blocks; the photographs show small housings at the front of the door
MIRROR = (0.10, 0.12, 0.085)        # out from the door, along the car, tall (m)
MIRROR_AT = (0.775, 0.47, 0.985)    # inner face, centre along the car, centre height (m): the door's front corner

# Lamp units, x from the centre line (m), wrapping round the car's corner, whose shape changes with height: sharp
# low down at the rear, rounding off from 0.65 m higher up at the front. Each row of a unit follows that row's own
# profile, traced by a fan of rays from CORNER_C inside the corner, and its columns are spaced by distance along it.
CORNER_C = (0.60, 2.0)     # x, distance from the middle along the car (m)
# the lenses stand well clear of their bezel: round the corner the two are cast on different columns
BEZEL_PROUD = 0.004
LENS_PROUD = 0.013
BEZEL_M = 0.010            # black border round the lenses, and between them
# Front: a wide clear headlamp, and at the corner amber over a clear parking lamp, wrapping onto the wing
# The lamps and the grille fill the front face from the bumper to the hood's edge, as on the car, with no paint between
HEAD = (0.295, 0.515, 0.726, 0.66)   # x0, z0, z1, and its length round the surface from x0 (m)
HEAD_SPLIT_X = 0.53        # headlamp | corner lamps
HEAD_SPLIT_Z = 0.632       # clear parking lamp below, amber above
# Grille: as tall as the lamps, a chrome frame round three thick chrome slats on black, between the lamps; wider at
# the top than the bottom, and its top leaning forwards out of the face, as on the car
GRILLE = (0.255, 0.29, 0.515, 0.726)   # half width at the bottom and at the top, z0, z1 (m)
GRILLE_LEAN = 0.03                     # how far the top stands forward of the bottom (m)
GRILLE_FACE_Y = NOSE_Y                 # the front face behind it, flat there
GRILLE_FRAME_M = 0.016
GRILLE_SLATS = 3
GRILLE_SLAT_H = 0.026
# Rear: an inner red unit in two rows, and an outer unit, amber over red, wrapping round the corner
TAIL = (0.27, 0.555, 0.755, 0.62)
TAIL_SPLIT_X = 0.485       # inner | outer unit
TAIL_ROW_Z = 0.66          # the inner unit's two rows
TAIL_AMBER_Z = 0.675       # the outer unit: red below, amber above

# Bumpers and side cladding: dark grey, with a chrome strip, as on the T16 in the photographs
BUMPER_GREY = (.20, .21, .22)
BUMPER_STRIP = (0.443, 0.457)      # strip height on the bumpers (m)
CLADDING_Y = (-0.90, 0.90)         # between the wheel arches (m)
CLADDING_Z = (0.30, 0.47)          # the lower door panel, under the strip (m)
CLADDING_STRIP_H = 0.012


def profile(tree, sign, face, x0, z):
    """The surface at height z from x0 on the face round the corner to the side: (points, normals, arc lengths)."""
    cx, cy = CORNER_C
    rays = [((sign * (x0 + (cx - x0) * i / 20), face * 2.6, z), (0, -face, 0)) for i in range(20)]
    for a in range(3, 91, 3):
        d = Vector((sign * math.sin(math.radians(a)), face * math.cos(math.radians(a)), 0))
        rays.append((tuple(Vector((sign * cx, face * cy, z)) + d), tuple(-d)))
    pts, nrms, arc = [], [], []
    for start, ray in rays:
        hit, nrm = tree.ray_cast(Vector(start), Vector(ray))[:2]
        if hit is None or (pts and (hit - pts[-1]).length < 0.002):   # a repeat would fold the lens
            continue
        arc.append(arc[-1] + (hit - pts[-1]).length if pts else 0.0)
        pts.append(hit)
        nrms.append(nrm if nrm.dot(Vector(ray)) < 0 else -nrm)
    return pts, nrms, arc


def lamp_grid(tree, sign, face, x0, z0, z1, length, n=(16, 1)):
    """Rays onto a lamp unit from x0 on the face, `length` metres round the surface: each row's columns evenly
    spaced along its own profile, each cast along that point's normal, so the lens can't fold at the corner."""
    grid = []
    for j in range(n[1] + 1):
        z = z0 + (z1 - z0) * j / n[1]
        pts, nrms, arc = profile(tree, sign, face, x0, z)
        row = []
        for i in range(n[0] + 1):
            s = length * i / n[0]
            k = max(1, next((k for k in range(1, len(arc)) if arc[k] >= s), len(arc) - 1))
            t = 0.0 if arc[k] == arc[k - 1] else min(1.0, (s - arc[k - 1]) / (arc[k] - arc[k - 1]))
            p, nrm = pts[k - 1].lerp(pts[k], t), nrms[k - 1].lerp(nrms[k], t).normalized()
            row.append((tuple(p + nrm * 0.05), tuple(-nrm)))
        grid.append(row)
    return grid


def lamp_unit(tree, sign, face, box, lenses, rubber, coll):
    """A black bezel over the whole unit and the lenses inset on it. `box` is (x0, z0, z1, length round the surface);
    each lens is (name, x0, x1 or None to run round the corner to the unit's end, less the bezel, z0, z1, material)."""
    x0, z0, z1, length = box
    made = [plate(f'lamp_bezel_{face}_{sign}', tree, lamp_grid(tree, sign, face, x0, z0, z1, length), rubber, coll,
                  proud=BEZEL_PROUD, smooth=True)]
    for name, a0, a1, c0, c1, mat in lenses:
        grid = face_grid(sign, a0, a1, c0, c1, face, 0.0, n=(6, 2)) if a1 else \
            lamp_grid(tree, sign, face, a0, c0, c1, length - (a0 - x0) - BEZEL_M)
        made.append(plate(f'{name}_{sign}', tree, grid, mat, coll, proud=LENS_PROUD, smooth=True))
    return made


def grille(tree, rubber, alloy, coll):
    """The grille as solid blocks on the front face, each following its lean and taper: a black backing, a chrome
    frame and the slats. (u, z): u from -1 to 1 across, at height z."""
    hw0, hw1, z0, z1 = GRILLE
    t = lambda z: (z - z0) / (z1 - z0)
    at = lambda u, z, out: (u * (hw0 + (hw1 - hw0) * t(z)), GRILLE_FACE_Y + GRILLE_LEAN * t(z) + out, z)
    def block(name, u0, u1, za, zb, out, mat):
        # its back sits in the face, so the leaning top shows a black side under it, not a gap
        verts = [at(u, z, d) for d in (out, -0.01) for z in (za, zb) for u in (u0, u1)]
        faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        return solid(name, verts, faces, mat, coll)
    fu = GRILLE_FRAME_M / hw0   # the frame's width across, as a fraction of the half width
    made = [block('grille_backing', -1, 1, z0, z1, 0.004, rubber)]
    # black on the face between the lamps, behind the tapered grille: no wedges of paint beside its narrower bottom
    made.append(plate('grille_surround', tree, face_grid(1, -HEAD[0], HEAD[0], z0, z1, 1, 0.0, n=(8, 2)), rubber, coll,
                      proud=0.003))
    made += [block('grille_frame_top', -1, 1, z1 - GRILLE_FRAME_M, z1, 0.012, alloy),
             block('grille_frame_bottom', -1, 1, z0, z0 + GRILLE_FRAME_M, 0.012, alloy),
             block('grille_frame_left', -1, -1 + fu, z0, z1, 0.012, alloy),
             block('grille_frame_right', 1 - fu, 1, z0, z1, 0.012, alloy)]
    gap = (z1 - z0 - 2 * GRILLE_FRAME_M - GRILLE_SLATS * GRILLE_SLAT_H) / (GRILLE_SLATS + 1)
    for k in range(GRILLE_SLATS):
        z = z0 + GRILLE_FRAME_M + gap * (k + 1) + GRILLE_SLAT_H * k
        made.append(block(f'grille_slat_{k}', -1 + fu, 1 - fu, z, z + GRILLE_SLAT_H, 0.009, alloy))
    return made


def drop_at(y):
    """COWL_DROP at y, linear between its stations, nothing outside them."""
    for (y0, d0), (y1, d1) in zip(COWL_DROP, COWL_DROP[1:]):
        if y0 <= y <= y1:
            return d0 + (d1 - d0) * (y - y0) / (y1 - y0)
    return 0.0


def lower_cowl(obj):
    """Lowers the top of `obj` by COWL_DROP. Where the body moves, its corner normals are rebuilt from the faces round
    each moved vertex; elsewhere it keeps its own (its sharp edges)."""
    mesh = obj.data
    mw, inv = obj.matrix_world, obj.matrix_world.inverted()
    old, moved = corner_normals(mesh), set()
    for v in mesh.vertices:
        p = mw @ v.co
        # only inboard of the shoulder (the hood, the cowl, the screen's base): the shoulder and the doors stay
        inboard = min(1.0, max(0.0, (COWL_SHOULDER_X - abs(p.x)) / COWL_SHOULDER_BLEND_M))
        d = drop_at(p.y) * inboard * min(1.0, max(0.0, (p.z - COWL_FROM_Z) / COWL_BLEND_M))
        if d > 1e-6:
            p.z -= d
            v.co = inv @ p
            moved.add(v.index)
    renormal(mesh, moved, old)
    return len(moved)


def renormal(mesh, moved, old):
    """After moving `moved` vertices: their corner normals rebuilt from the faces round them; the rest keep `old`."""
    if old is not None:
        mesh.update()
        around = [Vector() for _ in mesh.vertices]
        for f in mesh.polygons:
            for vi in f.vertices:
                around[vi] += f.normal * f.area
        loops = [around[l.vertex_index].normalized() if l.vertex_index in moved else old[l.index] for l in mesh.loops]
        mesh.normals_split_custom_set([tuple(n) for n in loops])
    mesh.update()


def corner_normals(mesh):
    return [tuple(c.vector) for c in mesh.corner_normals] if mesh.has_custom_normals else None


def shorten_nose():
    """Moves the nose back to NOSE_Y: everything ahead of NOSE_FROM_Y (just ahead of the front wheel arch) is pressed
    together along the car, the body and the parts on it alike, and the bumper moves back by BUMPER_BACK_M."""
    k = (NOSE_Y - NOSE_FROM_Y) / (ROUND2_NOSE_Y - NOSE_FROM_Y)
    for name in ['body', 'trim_front_airdam', 'badge_front']:
        obj = bpy.data.objects[name]
        mesh, mw, inv = obj.data, obj.matrix_world, obj.matrix_world.inverted()
        old, moved = corner_normals(mesh), set()
        for v in mesh.vertices:
            p = mw @ v.co
            if p.y > NOSE_FROM_Y:
                p.y = NOSE_FROM_Y + (p.y - NOSE_FROM_Y) * k
                v.co = inv @ p
                moved.add(v.index)
        renormal(mesh, moved, old)
    bpy.data.objects['bumper_front'].location.y -= BUMPER_BACK_M


def remove(names):
    for name in names:
        o = bpy.data.objects.get(name)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)


def apply():
    body = bpy.data.objects['body']
    if body.get('round3_shape_revision') == REVISION:
        return None
    assert body.matrix_world.is_identity   # the tree below is in body space, which is then world space
    report = {'cowl_vertices_lowered': [lower_cowl(bpy.data.objects[n]) for n in ('body', 'glass_envelope')]}
    shorten_nose()   # after the cowl: its stations are measured on round 2's body
    report['mirrors'] = mirrors(['mirror_housing', 'mirror_housing.001'], MIRROR, MIRROR_AT)
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(body, deps)
    rubber = bpy.data.materials[GLAZING.rubber]
    ivory = bpy.data.materials['headlamp ivory']
    amber = bpy.data.materials['indicator amber']
    red = bpy.data.materials['tail lamp red']
    alloy = bpy.data.materials['satin alloy']
    grey = material('bumper grey', BUMPER_GREY)
    coll = bpy.data.collections.get('LIGHTS') or bpy.context.scene.collection

    made = glazing(tree, GLAZING)

    # ---------- lamps: the round-2 lamps were flat blocks, the indicators boxes standing out at the corners ----------
    remove(['lamp_head', 'lamp_head.001', 'lamp_head_divider', 'lamp_head_divider.001', 'lamp_indicator',
            'lamp_indicator.001', 'lamp_tail', 'lamp_tail.001', 'lamp_tail_indicator', 'lamp_tail_indicator.001'])
    b = BEZEL_M
    for sign in [-1, 1]:
        x0, z0, z1, _ = HEAD
        made += lamp_unit(tree, sign, 1, HEAD, [
            ('lamp_head', x0 + b, HEAD_SPLIT_X - b / 2, z0 + b, z1 - b, ivory),
            ('lamp_parking', HEAD_SPLIT_X + b / 2, None, z0 + b, HEAD_SPLIT_Z - b / 2, ivory),
            ('lamp_indicator', HEAD_SPLIT_X + b / 2, None, HEAD_SPLIT_Z + b / 2, z1 - b, amber),
        ], rubber, coll)
        x0, z0, z1, _ = TAIL
        made += lamp_unit(tree, sign, -1, TAIL, [
            ('lamp_tail_inner_low', x0 + b, TAIL_SPLIT_X - b / 2, z0 + b, TAIL_ROW_Z - b / 2, red),
            ('lamp_tail_inner_high', x0 + b, TAIL_SPLIT_X - b / 2, TAIL_ROW_Z + b / 2, z1 - b, red),
            ('lamp_tail_outer', TAIL_SPLIT_X + b / 2, None, z0 + b, TAIL_AMBER_Z - b / 2, red),
            ('lamp_tail_indicator', TAIL_SPLIT_X + b / 2, None, TAIL_AMBER_Z + b / 2, z1 - b, amber),
        ], rubber, coll)

    # ---------- grille: round 2's was a small dark box with thin bars, reading as a Volvo's ----------
    remove(['grille', 'grille_bars', 'grille_frame'])
    made += grille(tree, rubber, alloy, coll)
    badge = bpy.data.objects['badge_front']   # forward onto the grille's leaning face, at the badge's height
    badge.location.y += GRILLE_LEAN * (badge.location.z - GRILLE[2]) / (GRILLE[3] - GRILLE[2]) + 0.012

    # ---------- bumpers: dark grey with a chrome strip, wrapping round to the wheel arches ----------
    for name, face in [('bumper_front', 1), ('bumper_rear', -1)]:
        bumper = bpy.data.objects[name]
        bumper.data.materials[0] = grey
        btree = BVHTree.FromObject(bumper, deps)
        for sign in [-1, 1]:
            grid = face_grid(sign, 0.0, 0.78, *BUMPER_STRIP, face, 2.22, wrap=0.27, n=(8, 1))
            made.append(plate(f'trim_bumper_strip_{face}_{sign}', btree, grid, alloy, coll, proud=0.004))

    # ---------- side cladding: the lower door panel between the arches, grey under a chrome strip ----------
    remove(['trim_side', 'trim_side.001'])   # a black line high on the doors, which the photographs don't show
    remove(['trim_hatch_spoiler'])           # the Turbo's wing: not wanted on the game's car
    y0, y1 = CLADDING_Y
    z0, z1 = CLADDING_Z
    for sign in [-1, 1]:
        side = lambda zs, n=12: [[((sign * 1.2, y0 + (y1 - y0) * i / n, z), (-sign, 0, 0)) for i in range(n + 1)] for z in zs]
        made.append(plate(f'trim_cladding_{sign}', tree, side([z0, (z0 + z1) / 2, z1]), grey, coll, proud=0.006))
        made.append(plate(f'trim_cladding_strip_{sign}', tree, side([z1, z1 + CLADDING_STRIP_H]), alloy, coll, proud=0.008))

    # ---------- the new parts, one mesh per material, and the glass back into glass_envelope ----------
    by_mat = {}
    for o in made:
        by_mat.setdefault(o.data.materials[0].name, []).append(o)
    for mat, objs in by_mat.items():
        o = S.merge_static(objs, 'glass_rebuilt' if mat == bpy.data.objects['glass_envelope'].data.materials[0].name
                           else 'round3_' + mat.replace(' ', '_'))
        o.parent = body
    take_envelope()
    report['parts'] = sorted(o.name for o in body.children)
    body['round3_shape_revision'] = REVISION
    body['round3_changes'] = json.dumps(report)
    return report


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    out = Path(args[0]).resolve()
    if len(args) > 1:
        bpy.ops.wm.open_mainfile(filepath=str(Path(args[1]).resolve()))
    print('round3', json.dumps(apply()))
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
