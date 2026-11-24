"""XC70 P2, redrawn: a low-poly quad cage of cross sections, subdivided (Catmull-Clark) into the body.

Usage: python redraw.py OUT.blend IN.blend   (IN: round 2's master, for its wheels and materials)
The cage's key sections are drawn below as (x, z) points from the middle of the floor out and up to the middle of the
roof (hood, tailgate); sections between them are interpolated along the car. Paint, black cladding and glass are faces
of the one cage, so they sit flush.
"""
from pathlib import Path
import sys, math
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/vehicle_pipeline'))
import shell
from refine import point_in, offset

K = 12   # points per half section
PLASTIC_OUT = 0.004   # the black zones' skin stands this far off the body
BODY_SUBD = 1   # subdivision levels of the cage: 1 for the game (2 gave 86,000 triangles for no visible gain)
REAR_BUMPER_TOP = 0.70   # the rear bumper's top along the side, from the arch back (the drawing)
CLAD_Z = 0.47   # the black lower cladding's top along the doors (the drawing's lower door line)

# key sections: y -> 12 (x, z) points: floor middle, floor edge, sill, cladding top, waist, shoulder, belt edge,
# then up the greenhouse (window bottom, window top, roof edge, roof, roof middle) or across the hood/tailgate
def body_sec(xw, zb, top, zs=0.96, zw=0.70, zc=CLAD_Z):
    """The lower body at full width xw from the floor zb to the shoulder at zs; `top` is the last 6 points. zc: the black
    cladding's top, zw: the waist (the bumpers' top at the ends)."""
    return [(0.0, zb), (xw - 0.10, zb), (xw - 0.02, zb + 0.07), (xw, zc), (xw + 0.01, zw), (xw - 0.02, zs)] + top


def nose(w, zb, zw, zs, hz, zc=None):
    """A section through the nose, w the half width there (the drawing's top view: it rounds off over its last 0.4 m),
    the bumper's top zw, the lamps' top zs, the hood's front at hz; everything across scales with w."""
    k = w / 0.90
    pts = body_sec(0.90, zb, hood(0.87, hz), zs=zs, zw=zw, zc=zc if zc else min(CLAD_Z, zw - 0.08))
    return [(x * k, z) for x, z in pts]

def belt_z(y):
    """The side windows' bottom edge: rising from 1.02 m at the A-pillar's foot to 1.12 m at the D-pillar (the drawing)."""
    return 1.02 + 0.10 * min(1.0, max(0.0, (0.80 - y) / 2.80))


SCREEN_WRAP = 0.075   # the windscreen's sides fall this far below its middle: curved round to the A-pillars
GH_TOP_X = 0.63    # the side glass's top edge (half width): the drawing's front, rear and top views lean the greenhouse
GH_ROOF_X = 0.535  # in from 0.83 m at the belt to a roof 1.07 m across
def cabin(xs, gw, roof, y, top=1.43):
    """Greenhouse over a shoulder at xs: the window from gw at belt_z(y) up and in to `top`, the roof at `roof`."""
    zb = belt_z(y)
    return [(xs - 0.03, zb - 0.04), (gw, zb), (GH_TOP_X - (0.835 - gw), top), (GH_ROOF_X - (0.835 - gw), roof - 0.022),
            (0.30, roof), (0.0, roof + 0.004)]


def gh_x(z):
    """The greenhouse's side (the A-pillar's outer edge) at height z: straight from the belt to the window's top."""
    return 0.835 + (GH_TOP_X - 0.835) * (z - 1.02) / (1.43 - 1.02)


def hood_sec(xw, zb, xs, hz):
    """A section ahead of the windscreen: the body, its shoulder just under the hood's edge, the hood at hz."""
    return body_sec(xw, zb, hood(xs, hz), zs=min(0.96, hz - 0.07))


def hood(xs, hz):
    """The hood at height hz (its middle), its edge rolling into the wing at xs."""
    return [(xs - 0.04, hz - 0.035), (xs - 0.12, hz - 0.006), (0.50, hz), (0.34, hz + 0.008), (0.17, hz + 0.012), (0.0, hz + 0.013)]


def screen(y, z):
    """A section through the windscreen: the side up to the window's bottom, then the A-pillar (on the leaning
    greenhouse) and across the glass at height z, which curves back hard towards the pillars (a wrapped screen)."""
    xp = gh_x(z)
    return body_sec(0.90, 0.21, cabin(0.87, 0.835, z, y)[:2] + [(xp, z - SCREEN_WRAP), (0.75 * xp, z - 0.35 * SCREEN_WRAP),
                                                                (0.42 * xp, z - 0.07 * SCREEN_WRAP), (0.0, z)])


# measured on the drawing (its side silhouette, sampled every 0.1 m; the roof under the rails at 1.515 m;, its side view scaled by the 2.76 m wheelbase): overhangs 0.93 m front,
# 1.04 m rear; the hood from 0.85 m at the lamps to 1.04 m at the cowl (y 1.05); the windscreen to the roof's front at
# y 0.15; the roof at 1.50 m; the tailgate falling from y -2.1 to a near-vertical rear face at -2.30
SECTIONS = [
    # the nose, rounded in plan as the drawing's top view (half widths 0.17, 0.40, 0.60, 0.78, 0.84 m at y 2.30, 2.27,
    # 2.21, 2.10, 2.00); the black bumper up to the lamps' foot (0.665 m), the lamps over it, the hood's front edge at 0.84 m
    (2.290, nose(0.30, 0.34, 0.56, 0.60, 0.62, zc=0.42)),
    (2.255, nose(0.46, 0.31, 0.66, 0.70, 0.72)),
    (2.190, nose(0.64, 0.30, 0.665, 0.75, 0.80)),
    (2.100, nose(0.79, 0.30, 0.67, 0.79, 0.860)),
    (2.000, nose(0.86, 0.29, 0.65, 0.82, 0.905)),
    (1.600, hood_sec(0.895, 0.21, 0.87, 1.005)),
    (1.250, hood_sec(0.90, 0.21, 0.87, 1.050)),
    (1.080, hood_sec(0.90, 0.21, 0.87, 1.068)),
    (0.900, screen(0.90, 1.185)),
    (0.600, screen(0.60, 1.345)),
    (0.350, screen(0.35, 1.452)),
    (0.150, body_sec(0.90, 0.21, cabin(0.87, 0.835, 1.505, 0.15))),
    (-0.600, body_sec(0.90, 0.21, cabin(0.87, 0.835, 1.515, -0.6))),
    (-1.600, body_sec(0.90, 0.21, cabin(0.87, 0.835, 1.515, -1.6))),
    (-2.050, body_sec(0.885, 0.27, cabin(0.86, 0.822, 1.505, -2.05), zw=REAR_BUMPER_TOP)),
    # (the floor rises behind the rear wheel, as the drawing: the bumper's underside sweeps up, not hanging low)
    # the rear: the cage runs on at full height past the car's end; rear_cut() then trims it with the tailgate's own
    # surface (and the bumper's), so the sides meet the rear in a sharp corner instead of the subdivision's cushion
    (-2.200, body_sec(0.87, 0.34, cabin(0.855, 0.815, 1.495, -2.2), zw=REAR_BUMPER_TOP)),
    (-2.330, body_sec(0.86, 0.39, cabin(0.85, 0.810, 1.485, -2.33), zw=REAR_BUMPER_TOP)),
    (-2.460, body_sec(0.85, 0.41, cabin(0.845, 0.805, 1.475, -2.46), zw=REAR_BUMPER_TOP)),
]
# materials by band (k from k0 to k1, between stations at y0..y1): the black plastic below the cladding line, the glass
CREASES = {3: 1.0, 5: 0.6, 7: 1.0, 8: 1.0, 9: 0.4}   # cladding top, shoulder, window bottom, window top, roof edge
END_CREASE = 0.6
REAR_CORNER_Y = -2.24     # the ring along the tailgate's edge, creased: the rear's corner sharp, not a cushion
REAR_CORNER_CREASE = 0.9
REAR_TURN_K = (7,)       # in the rear sections, the point where the side turns onto the tailgate
REAR_TURN_Y = -2.10
BLACK_BANDS = [(0, 3)]
BUMPER_Y = (1.78, -1.90)   # front: on under the flare, so no paint shows between the bumper and the flare   # the black bumpers: ahead of / behind these y, below the waist
BUMPERS = [((2.06, 3.0), 0.66), ((-3.0, -2.05), 0.70)]   # (y range, top z) of the black bumpers
FLARE_NORM = 1.45   # the black band round each opening reaches this far (the opening's superellipse norm)
FLARE_M = 0.025      # and stands this far proud at the opening                          # floor to the cladding's top, all along
WINDOWS = []   # side glass (face 7), between these y (the drawing)
GRILLE = (0.30, 0.655, 0.84, 0.035)   # half width, z0, z1, corner radius (the drawing's front view)
GRILLE_FRAME = 0.022
GRILLE_BARS = (6, 3)
GRILLE_BAR = 0.009
HEAD_X0 = 0.345                  # the lamps start just outside the grille
HEAD_LEN = 0.66                  # and run this far round the surface (m), onto the wing
HEAD_Z0 = (0.675, 0.715)         # bottom: at the grille, at the outer end
HEAD_Z1 = (0.835, 0.805)         # top
HEAD_CORNER = (0.55, 2.00)       # inside the front corner, for the lamps' profile round it
HEAD_AMBER_M = 0.13              # the amber indicator at the outer end
HEAD_PROJECTORS = [(0.20, 0.050), (0.38, 0.048)]   # the two round projectors: along the lamp (m), radius
HOOD_DOME = 0.012       # the middle of the hood swells this much more
HOOD_CREASE = ((2.17, 0.30), (1.12, 0.70))   # (y, half width) of each crease at its front and rear ends
HOOD_CREASE_W = 0.05   # the step's width (m)
HOOD_RISE = 0.018       # how far the middle stands above the sides of the hood
HOOD_SHUT = ((2.06, 0.70), (1.12, 0.79))   # (y, half width) of the hood's shut line at its front and rear
FRONT_BLACK_Y = 1.95
FRONT_SIDE_TOP = 0.64     # the front bumper's top along the side, behind its corner
# the side windows share one sill line and one top line (the drawing): bottom z = win_bot(y), top z = win_top(y)
win_bot = lambda y: 1.035 + 0.075 * (0.56 - y) / 2.61
win_top = lambda y: 1.405 + 0.025 * (0.56 - y) / 2.61
SIDE_WINDOWS = [   # (y, z): the front door's glass (its front edge the A-pillar), the rear door's, the quarter's
    [(0.56, win_bot(0.56)), (0.56, 1.15), (0.39, 1.256), (0.22, 1.331), (0.0, win_top(0.0)), (-0.245, win_top(-0.245)),
     (-0.20, win_bot(-0.20))],
    [(-0.36, win_bot(-0.36)), (-0.39, win_top(-0.39)), (-1.00, win_top(-1.00)), (-1.035, 1.30), (-1.02, win_bot(-1.02))],
    [(-1.26, win_bot(-1.26)), (-1.20, win_top(-1.20)), (-1.92, win_top(-1.92)), (-2.03, 1.37), (-2.05, win_bot(-2.05))],
]
WINDOW_FRAME = 0.028     # black round each window
WINDOW_SEAL = 0.012      # the seal's width outside the glass
PILLAR_BLOCKS = [[(-0.19, 1.02), (-0.355, 1.05), (-0.39, 1.43), (-0.24, 1.43)],      # the B-pillar, black
                 [(-1.02, 1.05), (-1.28, 1.09), (-1.21, 1.44), (-1.00, 1.44)]]       # the C-pillar
SCREEN_Z = (1.10, 1.43)          # the windscreen's foot and top
SCREEN_PILLAR = 0.055            # its sides this far inside the greenhouse's
SCREEN_LINE = [(1.04, 1.13), (1.068, 1.08), (1.185, 0.90), (1.345, 0.60), (1.452, 0.35), (1.505, 0.15)]   # (z, y) along its middle
BULLBAR = (0.36, 0.30, 0.62, 0.10)   # half width, foot z, top z, how far it stands ahead of the bumper (m)
POLIS_TEXT = (0.05, 0.80, 0.26)    # y, z of its middle, letter size (m)
LIGHTBAR = (-0.25, 1.62)         # the police light bar: y, z of its base
POLICE_GRILLE_LAMP = (0.24, 0.70)
COWL_BOX = ((0.0, 0.55), (0.95, 1.25), (0.98, 1.12))   # the hood only: reaching the wing, it left a step in its shading   # where the hood meets the windscreen: smoothed
FRONT_BLACK_N = 0.55   # faces facing forward more than this (the hood's top stays paint)
FRONT_BLACK_Z = 0.86
FRONT_BLACK_LAMPS_Z = 0.78    # outboard, only up under the lamps (their tops meet the hood: no black above them)
FRONT_BLACK_GRILLE_X = 0.36   # round the grille, up to the hood
SKID_FRONT = (0.40, 0.37, 0.45)   # on the bumper's flat face: wider, it creased over its corners    # half width, z0, z1
PLATE_FRONT = (0.26, 0.47, 0.58)
CLADDING_Y = (0.90, -0.92)   # between the flares, its ends under them (further, they hung into the openings)
CLADDING_Z = (0.25, 0.53)
CLADDING_PROUD = 0.018
STRIP_Y = (0.84, -0.87)
FLARE_W = 0.34            # the flares reach this far beyond the opening (its size)
FLARE_FROM_DEG = -6       # from this far below the hub's level at each end: down to the sill and the bumper
ARCH_LIP_NORM = 1.10
FLARE_PROUD = 0.026   # over the cladding (0.018), which runs on under the flares
FLARE_LOW_Z = 0.30
MIRROR = (0.19, 0.24, 0.14)          # out from the door, along the car, tall (m)
MIRROR_AT = (0.82, 0.70, 1.085)      # inner face x, centre y, centre z
RAIL_Y = (0.10, -1.98)               # the roof rails' front and rear ends (the drawing's side view)
RAIL_X = 0.56
RAIL = (0.035, 0.028, 0.045)         # width, height, lift off the roof (m)
REAR_PROFILE = [(0.34, -2.20), (0.40, -2.33), (0.45, -2.385), (0.50, -2.405), (0.62, -2.405), (0.695, -2.40), (0.712, -2.385), (0.722, -2.33),
                (0.73, -2.305), (0.75, -2.302),   # the bumper's top: a level ledge the tailgate stands on
                (0.90, -2.294), (1.00, -2.285), (1.10, -2.276), (1.20, -2.257), (1.30, -2.22),
                (1.40, -2.182), (1.45, -2.154), (1.49, -2.11), (1.52, -2.05), (1.60, -1.90)]   # (z, y): the drawing
BUMPER_TOP_Z = 0.735
REAR_BOW = 0.04           # the tailgate's middle stands this far behind its corners
PLATE_REAR = (0.26, 0.835, 0.945)   # half width, z0, z1 on the tailgate, under the glass
SKID_REAR = (0.38, 0.47, 0.57)      # the silver skid plate on the bumper's upright face (lower, it stood off its curve)
REAR_GLASS = (0.655, 0.585, 1.03, 1.43)   # out to the lamps and up under the roof, as the photograph from behind   # half width at the bottom and the top, z0, z1
TAIL_Z = (0.75, 1.42)
TAIL_TIP = (1.30, 0.45)          # from this height the lamp narrows to this fraction at its top
TAIL_BANDS = [('clear', 0.75, 0.80), ('red', 0.80, 0.93), ('red', 0.93, 1.03), ('red', 1.03, 1.11), ('clear', 1.11, 1.20),
              ('red', 1.20, 1.42)]   # from the photograph: a narrow clear strip at the foot, a short clear block above the shoulder
TAIL_RIBS = [0.835, 0.87, 0.905, 0.99, 1.025, 1.115]   # darker red rows across the lens (its reflector rows)
TAIL_GAP = 0.035                 # between the glass's edge and the lamp
TAIL_LOW_FRONT_Y = -2.16        # the wide lower part's front edge on the side (y)
TAIL_HIGH_WRAP = 0.05          # the narrow upper part wraps this far onto the side (m)
TAIL_STEP = (1.03, 1.10)        # the shoulder between them (z)
TAIL_FRONT_Y = (-2.215, -2.10)   # the lamp's front edge on the side: a straight line from its foot to its top (the drawing)
TAIL_SIDE = (0.17, 0.05)         # how far forward along the side the lamp reaches: below the shoulder, above it (m)
TAIL_SHOULDER = (0.86, 1.20)     # its front edge sweeps back over this height
TAIL_CORNER_R = 0.018            # the lamp's corner: sharp, as the car's
TAIL_PROUD = 0.004               # where it meets the body, it stands this far off it
TAIL_SEAM = 0.003                # black seams between the bands (half height)
PILLARS = []   # black between the windows (B- and C-pillars); the D-pillar is body-coloured up to the lamp


def catmull(p0, p1, p2, p3, t):
    return tuple(0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)
                 for a, b, c, d in zip(p0, p1, p2, p3))


def stations(per_gap=7):
    """The key sections and per_gap interpolated ones between each pair (Catmull-Rom along the car, per point)."""
    keys = SECTIONS
    out = []
    for i in range(len(keys) - 1):
        a, b = keys[i], keys[i + 1]
        pa, pb = keys[max(0, i - 1)], keys[min(len(keys) - 1, i + 2)]
        for s in range(per_gap + 1):
            t = s / (per_gap + 1)
            y = a[0] + (b[0] - a[0]) * t
            pts = [catmull(pa[1][k], a[1][k], b[1][k], pb[1][k], t) for k in range(K)]
            out.append((y, pts, s == 0))
    out.append((keys[-1][0], keys[-1][1], True))
    return out


def build(collection, paint, black, glass):
    sts = stations()
    bm = bmesh.new()
    rings = []
    for y, pts, key in sts:
        ring = [bm.verts.new((x, y, z)) for x, z in pts]
        ring += [bm.verts.new((-x, y, z)) for x, z in reversed(pts[1:-1])]
        rings.append((y, ring))
    n = len(rings[0][1])
    for (ya, a), (yb, b) in zip(rings, rings[1:]):
        for k in range(n):
            f = bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
            kk = k if k < K - 1 else 2 * (K - 1) - 1 - k   # the band's index on the right half
            ym = (ya + yb) / 2
            mat = 0
            if any(k0 <= kk < k1 for k0, k1 in BLACK_BANDS):
                mat = 1
            elif kk < 4 and (ym > BUMPER_Y[0] or ym < BUMPER_Y[1]):   # the bumpers, on the cage: clean edges
                mat = 1
            elif kk == 7 and any(y1 < ym < y0 for y0, y1 in WINDOWS):
                mat = 2
            elif kk == 7 and any(y1 < ym < y0 for y0, y1 in PILLARS):
                mat = 1
            f.material_index = mat
    # the ends: the last rings capped
    for _, ring in (rings[0], rings[-1]):
        bm.faces.new(ring).material_index = 1   # the bumpers' faces
    # creases keep the character lines through the subdivision: along the car at these points of each section, and
    # round the end rings
    crease = bm.edges.layers.float.get('crease_edge') or bm.edges.layers.float.new('crease_edge')
    idx = {}
    for r, (_, ring) in enumerate(rings):
        for k, v in enumerate(ring):
            idx[v] = (r, k if k < K else 2 * (K - 1) - k)
    corner = min(range(len(rings)), key=lambda r: abs(rings[r][0] - REAR_CORNER_Y))
    for e in bm.edges:
        (ra, ka), (rb, kb) = idx[e.verts[0]], idx[e.verts[1]]
        if ka == kb and ra != rb:
            e[crease] = CREASES.get(ka, 0.0)
            # at the back the sections' upper points turn from the side onto the tailgate: crease that turn
            if ka in REAR_TURN_K and max(rings[ra][0], rings[rb][0]) < REAR_TURN_Y:
                e[crease] = 1.0
        elif ra == rb and ra in (0, len(rings) - 1):
            e[crease] = END_CREASE
        elif ra == rb and ra == corner and max(ka, kb) >= 2:
            e[crease] = REAR_CORNER_CREASE   # the tailgate's edge all round: a crisp corner from the side onto the rear
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new('body')
    bm.to_mesh(mesh)
    bm.free()
    for m in (paint, black, glass):
        mesh.materials.append(m)
    obj = bpy.data.objects.new('body', mesh)
    collection.objects.link(obj)
    sub = obj.modifiers.new('subd', 'SUBSURF')
    sub.levels = sub.render_levels = BODY_SUBD
    for p in mesh.polygons:
        p.use_smooth = True
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier='subd')
    smooth_region(obj, COWL_BOX)
    hood_creases(obj)
    rear_cut(obj, paint, black)
    # the wheel openings (shell's), the materials carried over from the nearest face of the uncut body
    before = obj.data.copy()
    tree = BVHTree.FromPolygons([v.co for v in before.vertices], [p.vertices for p in before.polygons])
    mats = [p.material_index for p in before.polygons]
    shell.cut_arches(obj)
    for m in (black, glass):
        obj.data.materials.append(m)
    for p in obj.data.polygons:
        p.material_index = mats[tree.find_nearest(p.center)[2]]
        # the bumpers: one black band round each end, its top a smooth function of which way the face looks (up to
        # the lamps on the front, down to the bumper's line along the side), so it turns the corner without a step
        c, n = p.center, p.normal
        if p.material_index != 2 and (c.y > BUMPER_Y[0] or c.y < BUMPER_Y[1]):
            front = c.y > 0
            side_top, end_top, ey = (FRONT_SIDE_TOP, FRONT_BLACK_LAMPS_Z, n.y) if front else (REAR_BUMPER_TOP, BUMPER_TOP_Z, -n.y)
            w = min(1.0, max(0.0, (ey - 0.25) / 0.55))
            top = side_top + (end_top - side_top) * w * w * (3 - 2 * w)
            if not front:   # at the back the bumper's top is the ledge, whichever way a face looks: rising to it smoothly
                u = min(1.0, max(0.0, (-2.0 - c.y) / 0.26))
                top = max(top, REAR_BUMPER_TOP + (BUMPER_TOP_Z + 0.008 - REAR_BUMPER_TOP) * u * u * (3 - 2 * u))
            if front and ey > FRONT_BLACK_N and abs(c.x) < FRONT_BLACK_GRILLE_X:
                top = FRONT_BLACK_Z   # round the grille, up to the hood
            if n.z < 0.6 or c.z < top:   # (not the hood's or the tailgate's top)
                p.material_index = 1 if c.z < top else (0 if p.material_index == 1 and c.z > CLAD_Z + 0.02 else p.material_index)
        # the lip of each wheel opening, under the flare's inner edge: black, so no paint shows between flare and well
        if abs(p.center.x) > 0.5 and min(shell.arch_norm(p.center.y, p.center.z, hy, hz) for hy, hz in shell.HUBS) < ARCH_LIP_NORM:
            p.material_index = 1
        # the side windows' black frames and the B- and C-pillars (the drawing): paint elsewhere on the greenhouse
        p.use_smooth = True
    bpy.data.meshes.remove(before)
    shell.wheel_wells(obj)
    split_plastic(obj, black)
    return obj


def split_plastic(obj, black):
    """The game paints the body one colour and the pipeline needs it one closed shell: the black zones are copied
    PLASTIC_OUT outside it as their own object (trim_body_plastic), and the body is all paint."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    keep = [f for f in bm.faces if f.material_index != 0]
    out = bmesh.new()
    vmap = {}
    for f in keep:
        vs = []
        for v in f.verts:
            if v not in vmap:
                n = sum((g.normal for g in v.link_faces), Vector())
                vmap[v] = out.verts.new(v.co + (n.normalized() if n.length else v.normal) * PLASTIC_OUT)
            vs.append(vmap[v])
        g = out.faces.new(vs)
        g.smooth = f.smooth
    for e in out.edges:   # keep the body's sharp edges (the rear corner)
        e.smooth = True
    for f in bm.faces:
        f.material_index = 0
    bm.to_mesh(obj.data)
    bm.free()
    while len(obj.data.materials) > 1:
        obj.data.materials.pop()
    mesh = bpy.data.meshes.new('trim_body_plastic')
    out.to_mesh(mesh)
    out.free()
    mesh.materials.append(black)
    o = bpy.data.objects.new('trim_body_plastic', mesh)
    obj.users_collection[0].objects.link(o)
    o.parent = obj


def front_parts(body, black):
    """Headlamps and grille, cast onto the nose from in front (the drawing's front view and the photographs): a chrome
    framed egg-crate grille with the diagonal and badge; long lamps from the grille round the corner onto the wing, a round
    projector in the clear lens and the amber indicator at the outer end."""
    from refine import disc, ring, offset, resample, fillet, plate, profile, material
    bpy.context.view_layer.update()
    tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    coll = body.users_collection[0]
    chrome = material('grille chrome', (.56, .57, .59))   # darker than the skid plates: it reads as chrome in shade
    ivory = bpy.data.materials['headlamp ivory']
    bowl = material('headlamp reflector', (.80, .81, .82))
    amber = bpy.data.materials['indicator amber']
    ahead = lambda q: ((q[0], 3.0, q[1]), (0, -1, 0))
    made = []
    # ---------- grille ----------
    hw, z0, z1, r = GRILLE
    box = resample(fillet([(-hw, z0), (hw, z0), (hw, z1), (-hw, z1)], lambda c: r, steps=5), 0.03)
    made.append(disc('grille_backing', tree, box, ahead, 0.006, black, coll, rings=3, floor=tree))
    made.append(ring('grille_frame', tree, offset(box, 0.004), offset(box, -GRILLE_FRAME), ahead, 0.013, chrome, coll, floor=tree))
    f, b = GRILLE_FRAME, GRILLE_BAR
    bar = lambda name, pts: plate(name, tree, [[ahead(p) for p in row] for row in pts], chrome, coll, proud=0.010)
    nv, nh = GRILLE_BARS
    for i in range(1, nv + 1):
        x = -hw + f + 2 * (hw - f) * i / (nv + 1)
        made.append(bar(f'grille_bar_v{i}', [[(x - b / 2, z0 + f + (z1 - z0 - 2 * f) * k / 4) for k in range(5)],
                                             [(x + b / 2, z0 + f + (z1 - z0 - 2 * f) * k / 4) for k in range(5)]]))
    for j in range(1, nh + 1):
        z = z0 + f + (z1 - z0 - 2 * f) * j / (nh + 1)
        made.append(bar(f'grille_bar_h{j}', [[(-hw + f + 2 * (hw - f) * k / 10, z - b / 2) for k in range(11)],
                                             [(-hw + f + 2 * (hw - f) * k / 10, z + b / 2) for k in range(11)]]))
    # the diagonal, lower left to upper right, a little proud of the bars
    a, c = Vector((-hw + f, z0 + f)), Vector((hw - f, z1 - f))
    nrm = Vector((-(c - a).y, (c - a).x)).normalized() * 0.011
    line = [a + (c - a) * k / 10 for k in range(11)]
    made.append(plate('grille_diagonal', tree, [[ahead(tuple(p - nrm)) for p in line], [ahead(tuple(p + nrm)) for p in line]],
                      chrome, coll, proud=0.015))
    zc = (z0 + z1) / 2
    badge = [(0.032 * math.cos(t), zc + 0.032 * math.sin(t)) for t in [i * math.pi / 8 for i in range(16)]]
    made.append(disc('grille_badge', tree, badge, ahead, 0.026, chrome, coll, rings=1))
    # ---------- headlamps ----------
    cache = {}
    def at(sign, s_, z):
        key = (sign, round(z, 3))
        if key not in cache:
            cache[key] = profile(tree, sign, 1, HEAD_X0, key[1], HEAD_CORNER)
        pts, nrms, arc = cache[key]
        k = max(1, next((k for k in range(1, len(arc)) if arc[k] >= s_), len(arc) - 1))
        t = 0.0 if arc[k] == arc[k - 1] else min(1.0, (s_ - arc[k - 1]) / (arc[k] - arc[k - 1]))
        p, n = pts[k - 1].lerp(pts[k], t), nrms[k - 1].lerp(nrms[k], t).normalized()
        return (tuple(p + n * 0.05), tuple(-n))
    def hz(s_, v):   # the lamp's height at s_ along it, v from its bottom (0) to its top (1)
        u = min(1.0, max(0.0, s_ / HEAD_LEN))
        zb = HEAD_Z0[0] + (HEAD_Z0[1] - HEAD_Z0[0]) * u
        zt = HEAD_Z1[0] + (HEAD_Z1[1] - HEAD_Z1[0]) * u ** 1.5
        return zb + (zt - zb) * v
    def grid(sign, s0, s1, v0, v1, n):
        return [[at(sign, s0 + (s1 - s0) * i / n[0], hz(s0 + (s1 - s0) * i / n[0], v0 + (v1 - v0) * j / n[1]))
                 for i in range(n[0] + 1)] for j in range(n[1] + 1)]
    e = 0.012 / (HEAD_Z1[0] - HEAD_Z0[0])
    split = HEAD_LEN - HEAD_AMBER_M
    for sign in (-1, 1):
        made.append(plate(f'lamp_head_bezel_{sign}', tree, grid(sign, 0.0, HEAD_LEN, 0.0, 1.0, (20, 4)), black, coll, proud=0.004, smooth=True))
        made.append(plate(f'lamp_head_{sign}', tree, grid(sign, 0.012, split - 0.006, e, 1 - e, (16, 4)), ivory, coll, proud=0.012, smooth=True))
        made.append(plate(f'lamp_indicator_{sign}', tree, grid(sign, split + 0.006, HEAD_LEN - 0.012, e, 1 - e, (5, 4)), amber, coll,
                          proud=0.012, smooth=True))
        # the lens's insides, after the photographs: a chrome reflector bowl round each of two projectors, a dark band
        # along the lens's foot
        made.append(plate(f'lamp_head_inner_{sign}', tree, grid(sign, 0.03, split - 0.03, 0.10, 0.24, (12, 1)), black, coll,
                          proud=0.0135, smooth=True))
        for k, (s_, rr) in enumerate(HEAD_PROJECTORS):
            zc = hz(s_, 0.55)
            loop = lambda f: [(s_ + f * rr * math.cos(t), zc + f * rr * math.sin(t)) for t in [i * math.pi / 10 for i in range(20)]]
            made.append(disc(f'lamp_bowl_{sign}_{k}', tree, loop(1.0), lambda q, sg=sign: at(sg, q[0], q[1]), 0.0135, bowl, coll,
                             rings=2))
            made.append(ring(f'lamp_projector_{sign}_{k}', tree, loop(0.62), loop(0.42), lambda q, sg=sign: at(sg, q[0], q[1]), 0.016,
                             chrome, coll))
    for o in made:
        o.parent = body
    # the silver lower lip across the bumper and the plate above it (the photographs)
    silver = material('skid plate silver', (.70, .71, .72))
    white = material('registration plate', (.92, .92, .89))
    rect = lambda hw, z0, z1, r: resample(fillet([(-hw, z0), (hw, z0), (hw, z1), (-hw, z1)], lambda c: r, steps=4), 0.03)
    for name, (hw, z0, z1), proud, mat in [('trim_skid_front', SKID_FRONT, 0.012, silver), ('plate_front', PLATE_FRONT, 0.008, white)]:
        o = disc(name, tree, rect(hw, z0, z1, 0.03), ahead, proud, mat, coll, rings=5, floor=tree)
        o.parent = body
        made.append(o)
    return made


def rear_y(z):
    """The rear's surface in side view at height z (the drawing's silhouette): the bumper low, the tailgate above it,
    falling forward to the roof."""
    pts = REAR_PROFILE
    if z <= pts[0][0]:
        return pts[0][1]
    for (za, ya), (zb, yb) in zip(pts, pts[1:]):
        if z <= zb:
            return ya + (yb - ya) * (z - za) / (zb - za)
    return pts[-1][1]


def rear_cut(obj, paint, black):
    """Trims the cage's rear with the tailgate's surface: flat across with a slight bow in plan, the bumper's corners
    rounded below its top (the drawing's top view). Faces the cut makes are paint above the bumper, black on it."""
    bm = bmesh.new()
    zs = [0.0] + [0.20 + 1.45 * k / 80 for k in range(81)] + [1.9]
    xs = [-1.3 + 2.6 * k / 52 for k in range(53)]
    def y_at(x, z):
        u = min(1.0, abs(x) / 0.86)
        if z < BUMPER_TOP_Z:   # the bumper: its corners round off in plan
            # rounded in plan, but never forward of a ledge under the tailgate and lamps: they stand on it at the corners too
            return min(rear_y(z) + 0.13 * u ** 4 + REAR_BOW * u * u, rear_y(BUMPER_TOP_Z + 0.02) + REAR_BOW * u * u - 0.035)
        return rear_y(z) + REAR_BOW * u * u
    grid = [[bm.verts.new((x, y_at(x, z), z)) for x in xs] for z in zs]
    front = [[bm.verts.new((x, 3.5, z)) for x in xs] for z in zs]
    nz, nx = len(zs), len(xs)
    for j in range(nz - 1):
        for i in range(nx - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            bm.faces.new((front[j][i + 1], front[j][i], front[j + 1][i], front[j + 1][i + 1]))
    for j in range(nz - 1):   # the sides
        for i in (0, nx - 1):
            bm.faces.new((grid[j][i], grid[j + 1][i], front[j + 1][i], front[j][i]))
    for j in (0, nz - 1):     # bottom and top
        for i in range(nx - 1):
            bm.faces.new((grid[j][i + 1], grid[j][i], front[j][i], front[j][i + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cutter = bpy.data.objects.new('rear_cutter', bpy.data.meshes.new('rear_cutter'))
    bm.to_mesh(cutter.data)
    bm.free()
    bpy.context.scene.collection.objects.link(cutter)
    m = obj.modifiers.new('rear', 'BOOLEAN')
    m.operation, m.object, m.solver = 'INTERSECT', cutter, 'EXACT'
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier='rear')
    bpy.data.objects.remove(cutter)
    mesh = obj.data
    while len(mesh.materials) > 3:
        mesh.materials.pop()
    for p in mesh.polygons:
        c = p.center
        if c.y < -2.0 and p.normal.y < -0.55:   # the new rear faces
            p.material_index = 1 if c.z < BUMPER_TOP_Z else 0
        p.use_smooth = True
    for e in mesh.edges:
        e.use_edge_sharp = False
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    for e in bm.edges:   # shade the cut's edge sharp: the corner (only there: elsewhere it left hard-edged patches)
        e.smooth = not (len(e.link_faces) == 2 and e.verts[0].co.y < -2.0 and e.calc_face_angle(0) > math.radians(35))
    bm.to_mesh(mesh)
    bm.free()


def hood_creases(obj):
    """The P2's hood: a raised middle between two creases running from the grille's top corners back and out to the
    windscreen's corners (the drawing's front view, the photographs), and a soft power dome along the middle. Every
    weight is a smooth function of position and of how upward the surface faces, so the hood stays one clean surface."""
    (y0, x0), (y1, x1) = HOOD_CREASE
    ss = lambda t: (lambda c: c * c * (3 - 2 * c))(min(1.0, max(0.0, t)))
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    lift = {}
    for v in bm.verts:
        p = v.co
        if not (y1 - 0.25 < p.y < y0 + 0.2 and p.z > 0.75):
            continue
        up = ss((v.normal.z - 0.55) / 0.3)           # only the hood's top, fading out where it turns down
        along = ss((p.y - (y1 - 0.20)) / 0.25) * ss((y0 + 0.12 - p.y) / 0.22)
        t = min(1.0, max(0.0, (p.y - y1) / (y0 - y1)))
        xc = x1 + (x0 - x1) * t
        step = ss((xc - abs(p.x)) / HOOD_CREASE_W + 0.5)
        dome = math.cos(min(1.0, abs(p.x) / xc) * math.pi / 2) ** 2
        lift[v] = (HOOD_RISE * step + HOOD_DOME * dome) * up * along
    for v, d in lift.items():
        v.co.z += d
    bm.to_mesh(obj.data)
    bm.free()


def side_windows():
    """The side windows as (y, z) outlines, front to back, counter-clockwise, corners rounded (the drawing's side view)."""
    from refine import fillet, resample
    out = []
    for w in SIDE_WINDOWS:
        poly = w if sum((b[0] - a[0]) * (b[1] + a[1]) for a, b in zip(w, w[1:] + w[:1])) < 0 else w[::-1]
        out.append(resample(fillet(poly, lambda c: 0.05 if c[1] > 1.3 else 0.02, steps=5), 0.03))
    return out


def side_glass(body, glass, black):
    """Glass in each side window, cast onto the greenhouse from beside the car, with a black seal round it."""
    from refine import disc, ring, offset
    bpy.context.view_layer.update()
    tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    coll = body.users_collection[0]
    made = []
    for sign in (-1, 1):
        onto = lambda q, s_=sign: ((s_ * 1.5, q[0], q[1]), (-s_, 0, 0))
        for k, poly in enumerate(side_windows()):
            made.append(disc(f'glass_side_{sign}_{k}', tree, offset(poly, -0.002), onto, 0.004, glass, coll, rings=3, floor=tree))
            # the black frame round the glass: a band of its own, so its edge is the outline's, smooth
            made.append(ring(f'trim_frame_side_{sign}_{k}', tree, offset(poly, WINDOW_FRAME), offset(poly, -0.004), onto, 0.006, black,
                             coll, floor=tree, outer_proud=0.003))
        for k, block in enumerate(PILLAR_BLOCKS):   # the B- and C-pillars, black between the frames
            made.append(disc(f'trim_pillar_{sign}_{k}', tree, block if sign > 0 else block, onto, 0.005, black, coll, rings=2,
                             floor=tree))
    for o in made:
        o.parent = body
    return made


def windscreen(body, glass, black):
    """The windscreen: one glass from the cowl to the roof's front edge, between the A-pillars (the drawing's front
    view), laid on the cage's screen along its normal, with a thin black seal."""
    from refine import disc, ring, offset, resample, fillet
    bpy.context.view_layer.update()
    tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    coll = body.users_collection[0]
    z0, z1 = SCREEN_Z
    half = lambda z: gh_x(z) - SCREEN_PILLAR
    poly = [(-half(z0), z0), (half(z0), z0), (half(z1), z1), (-half(z1), z1)]
    poly = resample(fillet(poly, lambda c: 0.07 if c[1] > z0 + 0.01 else 0.04, steps=6), 0.035)
    def y_screen(z):
        pts = SCREEN_LINE
        for (za, ya), (zb, yb) in zip(pts, pts[1:]):
            if za <= z <= zb:
                return ya + (yb - ya) * (z - za) / (zb - za)
        return pts[0][1] if z < pts[0][0] else pts[-1][1]
    def onto(q):
        x, z = q
        dy = (y_screen(z + 0.01) - y_screen(z - 0.01)) / 0.02   # dy/dz up the glass
        n = Vector((0, 1, -dy)).normalized()
        if n.z < 0:
            n = -n
        base = Vector((x, y_screen(z), z))
        return (tuple(base + n * 0.6), tuple(-n))
    made = [disc('glass_screen', tree, offset(poly, -0.002), onto, 0.006, glass, coll, rings=6, floor=tree),
            ring('trim_seal_screen', tree, offset(poly, 0.012), offset(poly, -0.005), onto, 0.008, black, coll, floor=tree,
                 outer_proud=0.002)]
    for o in made:
        o.parent = body
    return made


def police_parts(body, black):
    """The police equipment (shown by variants.apply('police')): a light bar on two feet on the roof rails, three blue
    modules on it, two blue lamps low in the grille. Names as the game expects."""
    bpy.context.view_layer.update()
    tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    coll = bpy.data.collections['POLICE']
    alloy = bpy.data.materials['satin alloy']
    blue = bpy.data.materials['police blue lenses']
    def box(name, centre, size, mat):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co = Vector((centre[0] + v.co.x * size[0], centre[1] + v.co.y * size[1], centre[2] + v.co.z * size[2]))
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=min(size) * 0.18, segments=2, affect='EDGES')
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        for f in mesh.polygons:
            f.use_smooth = True
        mesh.materials.append(mat)
        o = bpy.data.objects.new(name, mesh)
        coll.objects.link(o)
        o.parent = body
        return o
    y, z = LIGHTBAR
    for k, sx in enumerate((-1, 1)):
        box('trim_police_mount' + ('' if k == 0 else '.001'), (sx * RAIL_X, y, z - 0.035), (0.05, 0.12, 0.05), black)
    box('trim_lightbar_base', (0.0, y, z), (1.20, 0.26, 0.04), alloy)
    for k, x in enumerate((-0.40, 0.0, 0.40)):
        box('lamp_blue_module' + ('' if k == 0 else f'.{k:03d}'), (x, y, z + 0.07), (0.38, 0.24, 0.10), blue)
    for k, sx in enumerate((-1, 1)):
        x, zz = sx * POLICE_GRILLE_LAMP[0], POLICE_GRILLE_LAMP[1]
        h = tree.ray_cast(Vector((x, 3.0, zz)), Vector((0, -1, 0)))[0]
        box('lamp_police_grille' + ('' if k == 0 else '.001'), (x, h.y + 0.012, zz), (0.07, 0.03, 0.035), blue)


def police_front_and_text(body, black):
    """The police car's bull bar with three round extra lamps on it (the photograph), and POLIS on each front door."""
    bpy.context.view_layer.update()
    tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    coll = bpy.data.collections['POLICE']
    alloy = bpy.data.materials['satin alloy']
    blue = bpy.data.materials['police blue lenses']
    face = lambda x, z: tree.ray_cast(Vector((x, 3.0, z)), Vector((0, -1, 0)))[0].y
    def tube(name, pts, r, mat, collection):
        cu = bpy.data.curves.new(name, 'CURVE')
        cu.dimensions = '3D'
        sp = cu.splines.new('POLY')
        sp.points.add(len(pts) - 1)
        for p_, q in zip(sp.points, pts):
            p_.co = (*q, 1.0)
        cu.bevel_depth, cu.bevel_resolution, cu.use_fill_caps = r, 3, True
        o = bpy.data.objects.new(name, cu)
        collection.objects.link(o)
        mesh = bpy.data.meshes.new_from_object(o.evaluated_get(bpy.context.evaluated_depsgraph_get()))
        bpy.data.objects.remove(o)
        bpy.data.curves.remove(cu)
        for f in mesh.polygons:
            f.use_smooth = True
        while mesh.uv_layers:   # plain position and normal only, so the parts merge (tools/vehicle-parts.ts)
            mesh.uv_layers.remove(mesh.uv_layers[0])
        mesh.materials.append(mat)
        ob = bpy.data.objects.new(name, mesh)
        collection.objects.link(ob)
        ob.parent = body
        return ob
    # the bar: up from the bumper's foot each side, forward and over, a crossbar at the lamps
    hx, z0, z1, out = BULLBAR
    y0 = face(hx, z0 + 0.04)
    pts = [(-hx, y0 - 0.02, z0), (-hx, y0 + out, z0 + 0.06), (-hx * 0.9, y0 + out + 0.03, z1 - 0.04), (-hx * 0.75, y0 + out + 0.03, z1),
           (hx * 0.75, y0 + out + 0.03, z1), (hx * 0.9, y0 + out + 0.03, z1 - 0.04), (hx, y0 + out, z0 + 0.06), (hx, y0 - 0.02, z0)]
    tube('trim_police_bullbar', pts, 0.022, alloy, coll)
    # three round lamps on it: a black pot, a blue lens
    for k, x in enumerate((-0.21, 0.0, 0.21)):
        yc, zc = y0 + out + 0.08, z1 + 0.085
        for name, r, depth, mat, dy in (('trim_police_lamp_pot', 0.085, 0.07, black, 0.0), ('trim_police_lamp_lens', 0.07, 0.012, blue, 0.04)):
            bm = bmesh.new()
            bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r, radius2=r, depth=depth)
            for v in bm.verts:
                v.co = Vector((x + v.co.x, yc + dy + v.co.z, zc + v.co.y))
            mesh = bpy.data.meshes.new(f'{name}_{k}')
            bm.to_mesh(mesh)
            bm.free()
            mesh.materials.append(mat)
            o = bpy.data.objects.new(f'{name}_{k}', mesh)
            coll.objects.link(o)
            o.parent = body
        tube(f'trim_police_lamp_stem_{k}', [(x, yc - 0.02, z1), (x, yc - 0.02, zc - 0.06)], 0.012, alloy, coll)


def wheels():
    """Five double spokes in silver on a dark disc, as the car's alloys (round 2's were a silver disc with dark bars)."""
    alloy = bpy.data.materials['satin alloy']
    black = bpy.data.materials['charcoal plastic rubber']
    for tag in ('fl', 'fr', 'rl', 'rr'):
        rim, old = bpy.data.objects[f'trim_rim_{tag}'], bpy.data.objects[f'trim_spokes_{tag}']
        rim.data.materials[0] = black
        mw = old.matrix_world
        ps = [mw @ v.co for v in old.data.vertices]
        xo = max(ps, key=lambda p: abs(p.x)).x   # the spokes' outer face
        sign = 1 if xo > 0 else -1
        cy = (min(p.y for p in ps) + max(p.y for p in ps)) / 2
        cz = (min(p.z for p in ps) + max(p.z for p in ps)) / 2
        bm = bmesh.new()
        def quad_prism(pts2):   # (y, z) outline, extruded 2 cm into the wheel
            top = [bm.verts.new((xo, cy + a, cz + b)) for a, b in pts2]
            bot = [bm.verts.new((xo - sign * 0.02, cy + a, cz + b)) for a, b in pts2]
            bm.faces.new(top)
            bm.faces.new(bot[::-1])
            n = len(pts2)
            for i in range(n):
                bm.faces.new((top[i], bot[i], bot[(i + 1) % n], top[(i + 1) % n]))
        R0, R1, RR = 0.055, 0.19, 0.215
        for k in range(10):   # five pairs
            a = 2 * math.pi * (k // 2) / 5 + (0.13 if k % 2 else -0.13)
            w0, w1 = 0.016, 0.026
            d, nrm = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
            quad_prism([(d[0] * R0 + nrm[0] * w0, d[1] * R0 + nrm[1] * w0), (d[0] * R1 + nrm[0] * w1, d[1] * R1 + nrm[1] * w1),
                        (d[0] * R1 - nrm[0] * w1, d[1] * R1 - nrm[1] * w1), (d[0] * R0 - nrm[0] * w0, d[1] * R0 - nrm[1] * w0)])
        ring = lambda r: [(r * math.cos(t), r * math.sin(t)) for t in [2 * math.pi * i / 40 for i in range(40)]]
        quad_prism(ring(R0 + 0.004))   # the hub
        for i in range(40):            # the rim's outer lip, as quads
            t0, t1 = 2 * math.pi * i / 40, 2 * math.pi * (i + 1) / 40
            quad_prism([(R1 * math.cos(t0), R1 * math.sin(t0)), (RR * math.cos(t0), RR * math.sin(t0)),
                        (RR * math.cos(t1), RR * math.sin(t1)), (R1 * math.cos(t1), R1 * math.sin(t1))])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        mesh = bpy.data.meshes.new(old.data.name)
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(alloy)
        mesh.transform(mw.inverted())
        old_mesh, old.data = old.data, mesh
        bpy.data.meshes.remove(old_mesh)


def smooth_region(obj, box, passes=8, fade=0.08):
    """Laplacian smoothing inside box ((x0, x1), (y0, y1), (z0, z1)), fading out over `fade`: evens waves the cage's
    interpolation leaves (the cowl)."""
    (x0, x1), (y0, y1), (z0, z1) = box
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    def w(p):
        d = math.hypot(max(x0 - abs(p.x), abs(p.x) - x1, 0.0), math.hypot(max(y0 - p.y, p.y - y1, 0.0), max(z0 - p.z, p.z - z1, 0.0)))
        return max(0.0, 1 - d / fade)
    vs = [(v, w(v.co)) for v in bm.verts]
    vs = [(v, k) for v, k in vs if k > 0 and not v.is_boundary]
    for _ in range(passes):
        moved = [v.co + (sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges) - v.co) * 0.5 * k for v, k in vs]
        for (v, _), c in zip(vs, moved):
            v.co = c
    bm.to_mesh(obj.data)
    bm.free()


def side_parts(body, black):
    """Black moulded flares round the wheel openings, the door mirrors and the roof rails (the photographs and the
    drawing's side and top views)."""
    from refine import plate, solid, material
    bpy.context.view_layer.update()
    tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    coll = body.users_collection[0]
    made = []
    # ---------- flares: a band from just outside each opening's edge out to FLARE_W, round from sill to sill ----------
    for hy, hz in shell.HUBS:
        for sign in (-1, 1):
            rows = []
            for scale in (1.02, 1.0 + FLARE_W):
                row = []
                for k in range(41):
                    t = math.radians(FLARE_FROM_DEG + (180 - 2 * FLARE_FROM_DEG) * k / 40)
                    c, s_ = math.cos(t), math.sin(t)
                    yy = hy + scale * shell.ARCH_HALF_W * math.copysign(abs(c) ** (2 / shell.ARCH_POWER), c)
                    zz = hz + scale * shell.ARCH_TOP * math.copysign(abs(s_) ** (2 / shell.ARCH_POWER), s_)
                    row.append(((sign * 1.3, yy, max(zz, FLARE_LOW_Z)), (-sign, 0, 0)))   # not below the body's floor
                rows.append(row)
            made.append(plate(f'trim_flare_{sign}_{hy}', tree, rows, black, coll, proud=FLARE_PROUD, smooth=True))
    # ---------- the hood's shut lines: along each wing top from the lamp's outer top to the windscreen's corner ----------
    gap = material('shut line', (.07, .08, .08))
    (ya, xa), (yb, xb) = HOOD_SHUT
    for sign in (-1, 1):
        pts = [(xa + (xb - xa) * k / 30, ya + (yb - ya) * k / 30) for k in range(31)]
        rows = [[((sign * (x + d), y, 3.0), (0, 0, -1)) for x, y in pts] for d in (-0.003, 0.003)]
        made.append(plate(f'shut_hood_{sign}', tree, rows, gap, coll, proud=0.0015))
    # ---------- the lower door cladding: a moulded panel standing proud between the flares, its top edge rounded ----------
    y0, y1 = CLADDING_Y
    for sign in (-1, 1):
        ys = [y1 + (y0 - y1) * k / 40 for k in range(41)]
        zs = [CLADDING_Z[0] + (CLADDING_Z[1] - CLADDING_Z[0]) * j / 6 for j in range(7)]
        rows = [[((sign * 1.3, y, z), (-sign, 0, 0)) for y in ys] for z in zs]
        made.append(plate(f'trim_cladding_{sign}', tree, rows, black, coll, proud=CLADDING_PROUD, smooth=True))
        # a satin strip along its top, as on the car, ending under the flares
        ys_strip = [STRIP_Y[1] + (STRIP_Y[0] - STRIP_Y[1]) * k / 40 for k in range(41)]
        rows = [[((sign * 1.3, y, z), (-sign, 0, 0)) for y in ys] for z in (CLADDING_Z[1] - 0.045, CLADDING_Z[1] - 0.03)]
        made.append(plate(f'trim_cladding_strip_{sign}', tree, rows, material('satin alloy', (.62, .63, .64)), coll,
                          proud=CLADDING_PROUD + 0.003))
    # ---------- mirrors: rounded housings on the door's front corner ----------
    ox, oy, oz = MIRROR
    x0, y, z = MIRROR_AT
    for sign in (-1, 1):
        bm = bmesh.new()
        ret = bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=9, radius=1.0)
        for v in ret['verts']:
            v.co.x = max(v.co.x, -0.4)
            v.co = Vector((sign * (x0 + ox * (v.co.x + 0.4) / 1.4), y + oy / 2 * v.co.y - 0.04 * (v.co.x + 0.4),
                           z + oz / 2 * v.co.z))
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            f.smooth = True
        mesh = bpy.data.meshes.new(f'mirror_{sign}')
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(black)
        o = bpy.data.objects.new(f'mirror_{sign}', mesh)
        coll.objects.link(o)
        made.append(o)
    # ---------- roof rails: a bar along each roof edge, on a foot at each end ----------
    y0, y1 = RAIL_Y
    w, h, lift = RAIL
    for sign in (-1, 1):
        verts, faces = [], []
        n = 40
        for k in range(n + 1):
            yy = y1 + (y0 - y1) * k / n
            hit = tree.ray_cast(Vector((sign * RAIL_X, yy, 3.0)), Vector((0, 0, -1)))[0]
            zr = hit.z if hit else 1.5
            u = min(k, n - k) / n   # the ends come down onto the roof: its feet
            zb = zr + lift * min(1.0, u / 0.04) if u < 0.04 else zr + lift
            zb = zr + 0.004 if k in (0, n) else zb
            x = sign * RAIL_X
            verts += [(x - w / 2, yy, zb), (x + w / 2, yy, zb), (x + w / 2, yy, max(zb, zr + lift) + h), (x - w / 2, yy, max(zb, zr + lift) + h)]
        for k in range(n):
            a, b = 4 * k, 4 * (k + 1)
            for i in range(4):
                faces.append((a + i, a + (i + 1) % 4, b + (i + 1) % 4, b + i))
        faces += [(3, 2, 1, 0), (4 * n, 4 * n + 1, 4 * n + 2, 4 * n + 3)]
        made.append(solid(f'trim_roof_rail_{sign}', verts, faces, black, coll))
    for o in made:
        o.parent = body
    return made


def rear_parts(body, glass, black, red, amber):
    """The tailgate glass and the tall tail lamps down the rear corners, cast onto the subdivided body from behind
    (the drawing's rear view: glass from 1.02 to 1.44 m, its top corners rounded; lamps from 0.80 to 1.42 m)."""
    from refine import disc, ring, offset, resample, fillet, lamp_grid, plate, material
    clear = material('reverse lamp clear', (.90, .91, .92))
    bpy.context.view_layer.update()
    tree = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
    coll = body.users_collection[0]
    behind = lambda q: ((q[0], -3.0, q[1]), (0, 1, 0))
    w0, w1, z0, z1 = REAR_GLASS
    poly = [(-w0, z0), (w0, z0), (w1, z1), (-w1, z1)]
    poly = resample(fillet(poly, lambda c: 0.05 if c[1] > z0 + 0.01 else 0.025, steps=6), 0.04)
    made = [disc('glass_rear', tree, offset(poly, -0.002), behind, 0.006, glass, coll, rings=5, floor=tree),
            ring('trim_seal_rear', tree, offset(poly, 0.012), offset(poly, -0.005), behind, 0.008, black, coll, floor=tree,
                 outer_proud=0.002)]
    # the lamps: a solid of their own that IS the rear corner. Round 2's and the cage's corner is rounded (the
    # subdivision's), so a lens laid on it reads as a stripe on a cushion; here each row of the lamp is a section in plan:
    # flat across the rear from beside the glass to a sharp corner (radius TAIL_CORNER_R), then flat forward along the
    # side. Where it meets the body (its inner edge on the rear, its front edge on the side) it sits on the body's
    # surface; at the corner it stands out of the rounded body, so the corner is the lamp's. Bands by height.
    def edge(z):   # the lamp's inner edge: just outside the glass, or the tailgate's edge below it
        w0, w1, g0, g1 = REAR_GLASS
        t = min(1.0, max(0.0, (z - g0) / (g1 - g0)))
        return w0 + (w1 - w0) * (z - g0) / (g1 - g0) + TAIL_GAP   # one straight line beside the glass, down to the foot
    def side_len(z):   # how far forward along the side the lamp reaches
        u = min(1.0, max(0.0, (z - TAIL_SHOULDER[0]) / (TAIL_SHOULDER[1] - TAIL_SHOULDER[0])))
        top = min(1.0, max(0.0, (z - TAIL_TIP[0]) / (TAIL_Z[1] - TAIL_TIP[0])))
        return (TAIL_SIDE[0] + (TAIL_SIDE[1] - TAIL_SIDE[0]) * u * u * (3 - 2 * u)) * (1 - top * top)
    def hit(start, ray):
        h = tree.ray_cast(Vector(start), Vector(ray))[0]
        return h
    def section(z):
        """The lamp's outer surface at height z, (x, y) from its inner edge on the rear round the corner to its front."""
        xe = edge(z)
        h = hit((xe, -3.0, z), (0, 1, 0))
        while h is None or h.y > -2.0:   # under the roof's edge the rear is narrower than the glass's line: step in
            xe -= 0.005
            h = hit((xe, -3.0, z), (0, 1, 0))
        yr = h.y - TAIL_PROUD          # the rear face, where the lamp starts
        # as the car's: a wide lower part, its front edge on the side straight up, then a short shoulder and a narrow
        # upper part, straight too, wrapping only a little round the corner
        u = min(1.0, max(0.0, (z - TAIL_STEP[0]) / (TAIL_STEP[1] - TAIL_STEP[0])))
        u = u * u * (3 - 2 * u)
        L = max(0.012, (TAIL_LOW_FRONT_Y - yr) * (1 - u) + TAIL_HIGH_WRAP * u)
        hs = hit((2.0, yr + max(L, 0.01), z), (-1, 0, 0))
        xs = (hs.x if hs else xe + 0.05) + TAIL_PROUD                # the side, where the lamp ends
        xs = max(xs, xe + 0.03)
        r = min(TAIL_CORNER_R, 0.45 * (xs - xe), 0.45 * max(L, 0.002))
        pts = [(xe + (xs - r - xe) * k / 6, yr) for k in range(7)]
        pts += [(xs - r + r * math.sin(a), yr + r - r * math.cos(a)) for a in [math.pi / 2 * k / 4 for k in range(1, 4)]]
        pts += [(xs, yr + r + max(0.0, L - r) * k / 4 + 0.0005 * k) for k in range(5)]   # always 15 points a row
        return pts
    def mat_at(z):
        for zz in [TAIL_Z[0]] + [b[2] for b in TAIL_BANDS[:-1]]:
            if abs(z - zz) < TAIL_SEAM:
                return 2
        for name, z0, z1 in TAIL_BANDS:
            if z0 <= z <= z1:
                return 1 if name == 'clear' else (3 if any(abs(z - r_) < 0.005 for r_ in TAIL_RIBS) else 0)
        return 0
    zs = sorted({round(TAIL_Z[0] + (TAIL_Z[1] - TAIL_Z[0]) * k / 70, 4) for k in range(71)} |
                {round(z + d, 4) for z in [b[1] for b in TAIL_BANDS] + TAIL_RIBS for d in (-TAIL_SEAM, TAIL_SEAM, -0.005, 0.005)
                 if TAIL_Z[0] <= z + d <= TAIL_Z[1]})
    dark = material('tail lamp dark red', (.42, .05, .06))
    for sign in (-1, 1):
        bm = bmesh.new()
        rows = []
        for z in zs:
            sec = section(z)
            front = [bm.verts.new((sign * x, y, z)) for x, y in sec]
            # the back: 4 cm into the body, square to each face
            back = [bm.verts.new((sign * (x - (0.04 if i >= 7 else 0.0)), y + (0.04 if i < 7 else 0.0), z)) for i, (x, y) in enumerate(sec)]
            rows.append((z, front, back))
        n = len(rows[0][1])
        assert all(len(r[1]) == n for r in rows), 'lamp rows differ in length'
        for (za, fa, ba), (zb, fb, bb) in zip(rows, rows[1:]):
            m = mat_at((za + zb) / 2)
            for i in range(n - 1):
                f = bm.faces.new((fa[i], fa[i + 1], fb[i + 1], fb[i]) if sign > 0 else (fa[i + 1], fa[i], fb[i], fb[i + 1]))
                f.material_index = m
                bm.faces.new((ba[i + 1], ba[i], bb[i], bb[i + 1]) if sign > 0 else (ba[i], ba[i + 1], bb[i + 1], bb[i])).material_index = 2
            for i, j in ((0, 0), (n - 1, n - 1)):
                bm.faces.new((fa[i], fb[i], bb[i], ba[i])).material_index = 2
        for _, f_, b_ in (rows[0], rows[-1]):
            for i in range(n - 1):
                bm.faces.new((f_[i], f_[i + 1], b_[i + 1], b_[i])).material_index = 2
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            f.smooth = True
        for e in bm.edges:
            e.smooth = not (len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(40))
        mesh = bpy.data.meshes.new(f'lamp_tail_{sign}')
        bm.to_mesh(mesh)
        bm.free()
        for mm in (red, clear, black, dark):
            mesh.materials.append(mm)
        o = bpy.data.objects.new(f'lamp_tail_{sign}', mesh)
        coll.objects.link(o)
        made.append(o)
    # the registration plate in a black recess on the tailgate, the silver skid plate low in the bumper
    silver = material('skid plate silver', (.70, .71, .72))
    white = material('registration plate', (.92, .92, .89))
    rect = lambda hw, z0, z1, r: resample(fillet([(-hw, z0), (hw, z0), (hw, z1), (-hw, z1)], lambda c: r, steps=4), 0.03)
    hw, z0, z1 = PLATE_REAR
    made.append(disc('trim_plate_recess', tree, rect(hw + 0.03, z0 - 0.025, z1 + 0.025, 0.03), behind, 0.003, black, coll,
                     rings=2, floor=tree))
    made.append(disc('plate_rear', tree, rect(hw, z0, z1, 0.008), behind, 0.007, white, coll, rings=1, floor=tree))
    hw, z0, z1 = SKID_REAR
    made.append(disc('trim_skid_rear', tree, rect(hw, z0, z1, 0.03), behind, 0.006, silver, coll, rings=5, floor=tree))
    for x in (-0.18, -0.06, 0.06, 0.18):   # its four small black studs (the photograph)
        made.append(disc(f'trim_skid_stud_{x}', tree, rect(0.018, z0 + 0.035, z0 + 0.05, 0.005), lambda q, x=x: ((q[0] + x, -3.0, q[1]),
                                                                                                        (0, 1, 0)),
                         0.013, black, coll, rings=1))
    for o in made:
        o.parent = body
    return made


def zones(obj):
    """Black plastic where the car has it: the bumpers (low on the ends, up to the lamps' foot) and a band round each
    wheel opening, standing a little proud as the moulded flares do."""
    mesh = obj.data
    flare = set()
    for p in mesh.polygons:
        c = p.center
        if abs(c.x) > 0.5:
            r = min(shell.arch_norm(c.y, c.z, hy, hz) for hy, hz in shell.HUBS)
            if r < FLARE_NORM and c.z > 0.20:
                p.material_index = 1
                flare.update(p.vertices)
        for (y0, y1), ztop in BUMPERS:
            if y0 <= c.y <= y1 and c.z < ztop:
                p.material_index = 1
    for i in flare:
        v = mesh.vertices[i]
        r = min(shell.arch_norm(v.co.y, v.co.z, hy, hz) for hy, hz in shell.HUBS)
        out = FLARE_M * max(0.0, 1 - (r - 1) / (FLARE_NORM - 1)) ** 0.5 if r >= 1 else FLARE_M
        if abs(v.co.x) > 0.6:
            v.co.x += math.copysign(out, v.co.x)
    mesh.update()


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    bpy.ops.wm.open_mainfile(filepath=str(Path(args[1]).resolve()))
    keep = {n for n in bpy.data.objects.keys() if n.startswith(('wheel_', 'trim_rim', 'trim_spokes'))}
    for o in list(bpy.data.objects):
        if o.name not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
    paint = bpy.data.materials['XC70 configurable silver']
    black = bpy.data.materials['charcoal plastic rubber']
    glass = bpy.data.materials['opaque smoky glazing']
    coll = bpy.data.collections.get('BODY') or bpy.context.scene.collection
    body = build(coll, paint, black, glass)
    front_parts(body, black)
    windscreen(body, glass, black)
    side_glass(body, glass, black)
    police_parts(body, black)
    police_front_and_text(body, black)
    wheels()
    side_parts(body, black)
    rear_parts(body, glass, black, bpy.data.materials['tail lamp red'], bpy.data.materials['indicator amber'])
    # all the glass one object, as the other cars' glass_envelope: one draw call instead of eight
    panes = [o for o in bpy.data.objects if o.name.startswith('glass_')]
    with bpy.context.temp_override(active_object=panes[0], selected_editable_objects=panes):
        bpy.ops.object.join()
    panes[0].name = panes[0].data.name = 'glass_envelope'
    for o in bpy.data.objects:
        if o.name in keep and o.parent is None:   # the rims and spokes stay on their wheels
            mw = o.matrix_world.copy()
            o.parent = body
            o.matrix_world = mw
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(args[0]).resolve()))
