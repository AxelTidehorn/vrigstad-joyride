"""Round 3: an upright greenhouse and the 240's large wrap-around lamps, edited on the round-2 master.

Usage (Blender as a module or `blender -b --python`): python round3.py OUT.blend [IN.blend]
Idempotent: a master already carrying `round3_shape_revision` is saved unchanged. Uses only bpy and the
shared surface_refinement helpers; it doesn't need Blender Modeler. Compared with the reference
photographs recorded in references.md (1990 240 GL, Vauxford, CC BY-SA 4.0; OSX, public domain).
"""
from pathlib import Path
import sys, json, math
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/vehicle_pipeline'))
import surface_refinement as S

REVISION = 'volvo240-r3'
# Greenhouse: the round-2 side glass leans in about 18 degrees, from 0.80 m at the glass base to 0.65 m at the roof
# edge, which reads narrow beside the photographs. Scaling x linearly with height straightens it to about 12 degrees
# (0.71 m at the roof edge). A linear ramp keeps the side a plane: an S-curve stands it upright at the top, and an
# upright side under a flat roof reads, in perspective, as leaning outwards.
ROOF_SCALE = 1.09
GLASS_BASE_Z = 0.94     # where the side glass starts (parameters.json window_base_z)
ROOF_Z = 1.43
CABIN_Y = (-1.42, 0.92)  # backlight base to cowl: only the greenhouse is widened
CABIN_X = 0.80           # nothing at the body's shoulder is touched
# Lamps, as plates projected onto the shell: (x0, x1, z0, z1) on the rear face, plus the corner wrap.
TAIL = (0.40, 0.79, 0.545, 0.735)   # just above the bumper (0.527 m), about twice as wide as tall, as in the rear photograph
TAIL_WRAP_Y = 0.075      # how far the tail lamp wraps forwards round the corner (m)
FRONT_AMBER = (0.745, 0.787, 0.615, 0.785)
# Tail lamp unit: a black bezel, an upper row (amber outer, small clear reversing lamp, red) over a red lower row,
# with dark horizontal ribs across the lenses, as on the 1990 240 in the photographs.
TAIL_BEZEL_M = 0.012      # bezel border round the lenses (m)
TAIL_SPLIT_Z = 0.645      # between the upper and lower rows (m)
TAIL_AMBER_W = 0.15       # the amber lens's width from the outer edge (m)
TAIL_CLEAR_W = 0.065      # the clear lens's width, inboard of the amber (m)
TAIL_RIB_PITCH = 0.028    # ribs across the red lenses (m)
TAIL_RIB_H = 0.005
# Wheels: the round-2 tyre's flat face is smoothed into its tread, so it shades like a ball, and its thin rim ring
# stands 7 mm proud of the tyre. Rebuilt simply: a flat-shaded sidewall, a chamfer, a round tread, and a shallow
# full wheel cover like the photographs' steel covers, at most 12 mm proud.
TYRE_R = 0.315
TYRE_HALF_W = 0.093       # half the tyre's width (m), as round 2
TYRE_CHAMFER = (0.018, 0.022)   # how far the shoulder rounds in from the tread and the face (m)
COVER_R = 0.205           # wheel cover radius (m)
COVER_DOME = 0.012        # the cover's centre stands this far out of the tyre face (m)
WHEEL_SEGMENTS = 24
STATIC_NAMES = {'matte charcoal rubber': 'trim_rubber', 'restrained wheel alloy': 'grille',
                'headlamp ivory': 'lamp_front_lenses'}
# Mirrors: round 2's are 23 cm long boxes along the car; a 240's housing is about 9 cm deep, 12 cm out, 11 cm tall.
MIRROR = (0.125, 0.09, 0.11)    # out from the door, along the car, tall (m)
MIRROR_AT = (0.79, 0.745, 1.035)  # inner face, centre along the car, centre height (m)
# Front spoiler: the shell's rounded underside shows below the black bumper like a tub; a 240 has a black lip there.
SPOILER = (0.75, 0.285, 0.392)  # half width, bottom and top (m), on the front face below the bumper

# Glazing: black seals round every window, a black B-pillar and quarter divider, and side glass rebuilt with
# rounded upper corners and set a few millimetres behind its seal, as on a 240 GL.
SEAL_OUT = 0.016          # seal width outside the glass edge (m)
SEAL_OVERLAP = 0.006      # the seal laps over the glass edge, so no gap shows (m)
SEAL_PROUD = 0.019
GLASS_PROUD = 0.014       # glass stands this far off the shell (it bridges the shell's small bulges): 5 mm behind its seal
SIDE_TOP_RADIUS = 0.075   # rounded upper corners of the side glass (m)
SIDE_LOW_RADIUS = 0.015
SIDE_GLASS_PROUD = 0.005   # off its plane, which already sits on the shell's outermost point under it
SIDE_SEAL_PROUD = 0.009
SEAL_EDGE_PROUD = 0.003   # a side seal's outer edge, on the shell
SIDE_FACING_COS = math.cos(math.radians(35))   # side glass only over shell facing within 35 degrees of the side
# Glazing parts are cast onto the shell, which curves in at the A- and C-pillars and the roof; a flat window plane
# is only the fallback where a ray goes deeper than this behind it (into the cowl) (m)
DEEP_M = 0.04
SCREEN_RADIUS = 0.06      # windscreen and backlight corners (m)
# The round-2 backlight runs up to the roof's top edge and wraps onto the C-pillars; the photographs show a smaller
# glass with paint above it and the pillars beside it. Rebuilt smaller in its own plane, bottom edge kept.
BACKLIGHT_WIDTH = 0.88
SCREEN_WIDTH = 0.91   # of the round-2 screen's span, which wrapped round the A-pillars


SCREEN_GLASS_PROUD = 0.009   # nearer flush than the side glass: proud, the screen stands out past the A-pillars
SCREEN_SEAL_PROUD = 0.013
SCREEN_SEAL_EDGE = 0.003   # its outer edge: the seal slopes down to the paint, so its end shows no step from the side
BACKLIGHT_HEIGHT = 0.80
FRONT_WRAP_Y = 0.07
LENS_PROUD = 0.010       # a lens stands this far off the shell (m)
LENS_SINK = 0.004        # and reaches this far into it, so it reads seated, never floating


def widen(obj, mask=lambda p: True):
    mw, inv = obj.matrix_world, obj.matrix_world.inverted()
    moved = 0
    for v in obj.data.vertices:
        p = mw @ v.co
        if not (CABIN_Y[0] <= p.y <= CABIN_Y[1] and p.z > GLASS_BASE_Z and abs(p.x) < CABIN_X and mask(p)):
            continue
        s = min(1.0, (p.z - GLASS_BASE_Z) / (ROOF_Z - GLASS_BASE_Z))
        p.x *= 1 + (ROOF_SCALE - 1) * s
        v.co = inv @ p
        moved += 1
    obj.data.update()
    return moved


def material(name, rgb):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = .45
    return m


def plate(name, tree, grid, mat, collection, proud=LENS_PROUD):
    """A closed lens plate on the shell: each grid point is a (start, ray) cast onto the body and offset along the
    surface normal, front at +proud, back at -LENS_SINK, with the rim closed."""
    rows, cols = len(grid), len(grid[0])
    front, back = [], []
    for row in grid:
        for start, ray in row:
            hit = tree.ray_cast(Vector(start), Vector(ray))
            if hit[0] is None:
                raise RuntimeError(f'{name}: no shell under {tuple(round(c, 3) for c in start)}')
            loc, n = hit[0], hit[1]
            if n.dot(Vector(ray)) > 0:
                n = -n
            front.append(loc + n * proud)
            back.append(loc - n * LENS_SINK)
    verts = [tuple(v) for v in front + back]
    k = rows * cols
    idx = lambda r, c: r * cols + c
    faces = []
    for r in range(rows - 1):
        for c in range(cols - 1):
            a, b, d, e = idx(r, c), idx(r, c + 1), idx(r + 1, c + 1), idx(r + 1, c)
            faces.append((a, b, d, e))
            faces.append((k + e, k + d, k + b, k + a))
    rim = [idx(0, c) for c in range(cols)] + [idx(r, cols - 1) for r in range(1, rows)] + \
          [idx(rows - 1, c) for c in range(cols - 2, -1, -1)] + [idx(r, 0) for r in range(rows - 2, 0, -1)]
    for i in range(len(rim)):
        a, b = rim[i], rim[(i + 1) % len(rim)]
        faces.append((a, k + a, k + b, b))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def rear_grid(sign, x0, x1, z0, z1, wrap=0.0, n=(8, 4)):
    """Points behind the rear face, cast forwards (+Y); with `wrap`, the outer column continues round the corner,
    cast inwards from beside the car."""
    cols = []
    for i in range(n[0] + 1):
        cols.append(('rear', x0 + (x1 - x0) * i / n[0]))
    for i in range(1, 4 if wrap else 0):
        cols.append(('side', -2.31 + wrap * i / 3))
    grid = []
    for j in range(n[1] + 1):
        z = z0 + (z1 - z0) * j / n[1]
        row = []
        for kind, u in cols:
            row.append(((sign * u, -2.6, z), (0, 1, 0)) if kind == 'rear' else ((sign * 1.2, u, z), (-sign, 0, 0)))
        grid.append(row)
    return grid


# ---------- outlines: 2D polygons, rounded and offset, cast onto the shell ----------
def hull(points):
    pts = sorted(set((round(a, 5), round(b, 5)) for a, b in points))
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 1e-9:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 1e-9:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]   # counter-clockwise


def simplify(poly, min_turn_deg=12):
    """Drops hull points where the outline barely turns, leaving its real corners."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b, c = Vector(poly[i - 1]), Vector(poly[i]), Vector(poly[(i + 1) % n])
        if (b - a).length < 1e-6 or (c - b).length < 1e-6:
            continue
        if math.degrees((b - a).angle(c - b)) >= min_turn_deg:
            out.append(poly[i])
    return out


def fillet(poly, radius_at, steps=4):
    """Rounds every corner of a counter-clockwise polygon with the radius `radius_at(corner)` gives."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b, c = Vector(poly[i - 1]), Vector(poly[i]), Vector(poly[(i + 1) % n])
        u, w = (a - b).normalized(), (c - b).normalized()
        half = u.angle(w) / 2
        r = radius_at(poly[i])
        t = min(r / math.tan(half), 0.45 * (a - b).length, 0.45 * (c - b).length)
        r = t * math.tan(half)
        p0, p1 = b + u * t, b + w * t
        centre = b + (u + w).normalized() * (r / math.sin(half))
        a0 = math.atan2(*(p0 - centre).yx)
        a1 = math.atan2(*(p1 - centre).yx)
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        # segments by how far the corner turns: a slight bend needs one, a right angle `steps`
        m = max(1, math.ceil(steps * abs(da) / (math.pi / 2)))
        for k in range(m + 1):
            ang = a0 + da * k / m
            out.append((centre.x + r * math.cos(ang), centre.y + r * math.sin(ang)))
    return out


def offset(poly, d):
    """Moves each point of a counter-clockwise polygon outwards by d (inwards for d < 0)."""
    out = []
    n = len(poly)
    for i in range(n):
        a, b, c = Vector(poly[i - 1]), Vector(poly[i]), Vector(poly[(i + 1) % n])
        e0, e1 = (b - a).normalized(), (c - b).normalized()
        n0, n1 = Vector((e0.y, -e0.x)), Vector((e1.y, -e1.x))
        m = (n0 + n1).normalized()
        k = max(m.dot(n0), 0.35)
        out.append(tuple(b + m * (d / k)))
    return out


def cast(tree, loop, to3, proud, sink=LENS_SINK, floor=None):
    """Each loop point placed on the surface: onto `tree` along its ray, or onto its fallback plane. With `floor` (the
    shell alone), the front is pushed out until it clears the shell by half of `proud`, so the body never shows
    through glass laid over a bulge."""
    front, back = [], []
    for p in loop:
        placed = to3(p)
        if placed[0] == 'plane':   # (marker, point, outward normal): straight onto a fitted plane
            front.append(placed[1] + placed[2] * proud)
            back.append(placed[1] - placed[2] * sink)
            continue
        start, ray, fallback = placed if len(placed) == 3 else (*placed, None)
        hit = tree.ray_cast(Vector(start), Vector(ray))
        if fallback and (hit[0] is None or (hit[0] - fallback[1]).dot(fallback[2]) < -DEEP_M):
            # missed the window, or went past it into the cowl or the cabin: stay on the window's plane
            front.append(fallback[1] + fallback[2] * proud)
            back.append(fallback[1] - fallback[2] * sink)
            continue
        if hit[0] is None:
            # a seal's outer edge can reach past the shell's silhouette at a corner (the cowl): land it from above
            ray = (0, 0, -1)
            hit = tree.ray_cast(Vector((start[0] * (0.65 if abs(start[0]) > 1 else 1), start[1], 2.5)), Vector(ray))
        if hit[0] is None:
            raise RuntimeError(f'no shell under {tuple(round(c, 3) for c in start)}')
        n = hit[1] if hit[1].dot(Vector(ray)) < 0 else -hit[1]
        front.append(hit[0] + n * proud)
        back.append(hit[0] - n * sink)
    if floor:
        for i, p in enumerate(loop):
            placed = to3(p)
            if placed[0] == 'plane':   # pushed out along the plane's normal where the shell bulges past it
                start, ray = placed[1] + placed[2] * 0.6, -placed[2]
            else:
                start, ray = Vector(placed[0]), Vector(placed[1]).normalized()
            under = floor.ray_cast(start, ray)[0]
            if under is None:
                continue
            clear = (under - front[i]).dot(ray)   # how far the front is outside the shell, along the ray
            if clear < proud / 2:
                front[i] -= ray * (proud / 2 - clear)
    return front, back


def solid(name, mesh_verts, faces, mat, collection):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(v) for v in mesh_verts], [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    # glass and seals follow a gently curved surface: shade them smooth so its facets don't show, sharp only at rims
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.link_faces[0].normal.angle(e.link_faces[1].normal, 0) > math.radians(45):
            e.smooth = False
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def ring(name, tree, outer, inner, to3, proud, mat, collection, floor=None, outer_proud=None, outer_to3=None):
    """A closed band between two loops of the same length: a seal or a bezel. With `outer_proud`, its outer edge
    stands lower than its inner one, a bead sloping down to the paint; with `outer_to3`, that edge is placed its own
    way (on the shell, round glass laid on a plane)."""
    of, ob = cast(tree, outer, outer_to3 or to3, proud if outer_proud is None else outer_proud, floor=floor)
    inf, inb = cast(tree, inner, to3, proud, floor=floor)
    n = len(outer)
    verts = of + inf + ob + inb
    O, I, OB, IB = 0, n, 2 * n, 3 * n
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces += [(O + i, O + j, I + j, I + i), (OB + i, IB + i, IB + j, OB + j),
                  (O + i, OB + i, OB + j, O + j), (I + i, I + j, IB + j, IB + i)]
    return solid(name, verts, faces, mat, collection)


def disc(name, tree, loop, to3, proud, mat, collection, rings=4, floor=None):
    """A closed plate over a convex loop (glass or a lens), cast onto the shell in concentric rings down to its
    centre, so a curved panel stays on the surface instead of sinking under it along the chord."""
    n = len(loop)
    cx = sum(p[0] for p in loop) / n
    cy = sum(p[1] for p in loop) / n
    loops = [[(cx + (p[0] - cx) * (1 - k / rings), cy + (p[1] - cy) * (1 - k / rings)) for p in loop] for k in range(rings)]
    front, back = [], []
    for lp in loops + [[(cx, cy)]]:
        f, b = cast(tree, lp, to3, proud, floor=floor)
        front += f
        back += b
    m = len(front)
    faces = []
    for k in range(rings):
        o, i = k * n, (k + 1) * n
        for t in range(n):
            u = (t + 1) % n
            if k < rings - 1:
                faces += [(o + t, o + u, i + u, i + t), (m + o + t, m + i + t, m + i + u, m + o + u)]
            else:
                faces += [(o + t, o + u, i), (m + o + t, m + i, m + o + u)]
    for t in range(n):
        u = (t + 1) % n
        faces.append((t, m + t, m + u, u))
    return solid(name, front + back, faces, mat, collection)


def side_plane(points, sign):
    """The plane x = a*y + b*z + c through the side glass points (least squares), as a placement for (y, z)."""
    n = len(points)
    sy = sum(p.y for p in points); sz = sum(p.z for p in points); sx = sum(p.x for p in points)
    syy = sum(p.y * p.y for p in points); szz = sum(p.z * p.z for p in points); syz = sum(p.y * p.z for p in points)
    sxy = sum(p.x * p.y for p in points); sxz = sum(p.x * p.z for p in points)
    from mathutils import Matrix
    m = Matrix(((syy, syz, sy), (syz, szz, sz), (sy, sz, n)))
    a, b, c = m.inverted() @ Vector((sxy, sxz, sx))
    normal = Vector((1, -a, -b)).normalized() * sign
    # sit the plane on the outermost points (the envelope slab's outer face, or the shell's bulge under the glass)
    c += max(sign * (p.x - (a * p.y + b * p.z + c)) for p in points) * sign
    return lambda q: ('plane', Vector((a * q[0] + b * q[1] + c, q[0], q[1])), normal)


def shell_under(tree, poly, sign, step=0.02, normals=False):
    """The shell's points under an outline in (y, z), cast in from the side on a grid (with their normals)."""
    ys = [q[0] for q in poly]; zs = [q[1] for q in poly]
    out = []
    y = min(ys) + step / 2
    while y < max(ys):
        z = min(zs) + step / 2
        while z < max(zs):
            if point_in(poly, (y, z)):
                hit, nrm = tree.ray_cast(Vector((sign * 1.2, y, z)), Vector((-sign, 0, 0)))[:2]
                if hit is not None:
                    out.append((hit, nrm) if normals else hit)
            z += step
        y += step
    return out


def clip(poly, window):
    """`poly` cut to the convex `window` (Sutherland-Hodgman); both counter-clockwise or both clockwise."""
    out = poly
    turn = sum(window[i - 1][0] * window[i][1] - window[i][0] * window[i - 1][1] for i in range(len(window)))
    for i in range(len(window)):
        a, b = window[i - 1], window[i]
        inside = lambda p: ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) * turn >= 0
        src, out = out, []
        for k in range(len(src)):
            p, q = src[k - 1], src[k]
            if inside(q) != inside(p):
                t = ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])) / \
                    ((b[1] - a[1]) * (q[0] - p[0]) - (b[0] - a[0]) * (q[1] - p[1]))
                out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
            if inside(q):
                out.append(q)
    return out


def point_in(poly, q):
    inside = False
    for i in range(len(poly)):
        (y0, z0), (y1, z1) = poly[i - 1], poly[i]
        if (z0 > q[1]) != (z1 > q[1]) and q[0] < y0 + (q[1] - z0) * (y1 - y0) / (z1 - z0):
            inside = not inside
    return inside


def islands(obj):
    """The glass envelope's separate windows: lists of face indices, each a closed slab."""
    mesh = obj.data
    link = {}
    for f in mesh.polygons:
        for k in f.edge_keys:
            link.setdefault(k, []).append(f.index)
    seen, out = set(), []
    for f in mesh.polygons:
        if f.index in seen:
            continue
        stack, isl = [f.index], []
        while stack:
            i = stack.pop()
            if i in seen:
                continue
            seen.add(i)
            isl.append(i)
            for k in mesh.polygons[i].edge_keys:
                stack += [j for j in link[k] if j not in seen]
        out.append(isl)
    return out


def glazing(tree, body, report):
    glass = bpy.data.objects['glass_envelope']
    mw = glass.matrix_world
    shell = tree   # the shell is closed under every window: the new glass and seals are cast onto it
    rubber = bpy.data.materials['matte charcoal rubber']
    glass_mat = glass.data.materials[0]
    coll = glass.users_collection[0]
    made, side_faces = [], []
    sides = {-1: [], 1: []}
    for isl in islands(glass):
        pts = [mw @ glass.data.vertices[v].co for i in isl for v in glass.data.polygons[i].vertices]
        xs = [p.x for p in pts]
        if min(abs(x) for x in xs) > 0.6:   # a side window: rebuilt below
            sign = 1 if xs[0] > 0 else -1
            sides[sign].append(pts)
            side_faces += isl
            continue
        # windscreen or backlight: its outline in the plane across its mean normal
        # the envelope is a closed slab, so its face normals cancel: take the plane's slope from the points instead
        # (the long axis of their spread in the y-z plane; the glass is symmetric across x)
        centre = sum(pts, Vector()) / len(pts)
        cyy = sum((p.y - centre.y) ** 2 for p in pts)
        czz = sum((p.z - centre.z) ** 2 for p in pts)
        cyz = sum((p.y - centre.y) * (p.z - centre.z) for p in pts)
        ang = 0.5 * math.atan2(2 * cyz, cyy - czz)
        n = Vector((0, -math.sin(ang), math.cos(ang)))
        if n.dot(Vector((0, centre.y, 0.5))) < 0:   # outwards: forwards-up for the screen, rearwards-up for the backlight
            n = -n
        u = Vector((1, 0, 0))
        v = n.cross(u).normalized()
        poly = simplify(hull([((p - centre).dot(u), (p - centre).dot(v)) for p in pts]))
        poly = fillet(poly, lambda c: SCREEN_RADIUS)
        to3 = lambda q, c=centre, u=u, v=v, n=n: (tuple(c + u * q[0] + v * q[1] + n * 0.6), tuple(-n))
        # Neither the screen nor the backlight is kept: round 2 laid each as a flat sheet over the closed shell, wrapping
        # round onto the A- and C-pillars, where it stood out past them. Each is cast anew onto the shell: the screen
        # a little narrower, so it stays on the shell's front; the backlight smaller, as in the photographs (88 % as
        # wide, 80 % as tall, bottom edge kept). Where a seal's edge reaches past the shell's rounded edge, it stays on
        # the window's plane, set on the shell under the glass, rather than landing low on the pillar's side.
        side_faces += isl
        depth = sorted((hit - centre).dot(n) for hit in (tree.ray_cast(Vector(to3(q)[0]), Vector(to3(q)[1]))[0] for q in poly)
                       if hit is not None)
        sit = depth[len(depth) // 2]
        placed = lambda q, c=centre, u=u, v=v, n=n, sit=sit: (*to3(q), ('plane', c + u * q[0] + v * q[1] + n * sit, n))
        raw = simplify(hull([((p - centre).dot(u), (p - centre).dot(v)) for p in pts]))
        if centre.y > 0:
            name = 'screen'
            small = [(q[0] * SCREEN_WIDTH, q[1]) for q in raw]
        else:
            name = 'backlight'
            bottom = min(q[1] for q in raw) if v.z > 0 else max(q[1] for q in raw)
            small = [(q[0] * BACKLIGHT_WIDTH, bottom + (q[1] - bottom) * BACKLIGHT_HEIGHT) for q in raw]
        small = fillet(small, lambda c: SCREEN_RADIUS)
        gp, sp, op = (SCREEN_GLASS_PROUD, SCREEN_SEAL_PROUD, SCREEN_SEAL_EDGE) if name == 'screen' else (GLASS_PROUD, SEAL_PROUD, None)
        made.append(disc(f'glass_{name}', tree, offset(small, -0.002), placed, gp, glass_mat, coll, rings=2, floor=shell))
        made.append(ring(f'trim_seal_{name}', tree, offset(small, SEAL_OUT), offset(small, -SEAL_OVERLAP), placed,
                         sp, rubber, coll, floor=shell, outer_proud=op))
    # drop the old glass from the envelope
    bm = bmesh.new()
    bm.from_mesh(glass.data)
    bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in side_faces], context='FACES')
    bm.to_mesh(glass.data)
    bm.free()
    for sign, wins in sides.items():
        boxes = []
        planes = []
        wins = sorted(wins, key=lambda ps: -max(p.y for p in ps))   # front door, rear door, quarter
        # one straight belt line under all three, as on the car: the highest of their round-2 bottoms
        belt = max(min(p.z for p in ps) for ps in wins)
        print('side window bottoms', sign, [round(min(p.z for p in ps), 4) for ps in wins], 'belt', round(belt, 4))
        for pts in wins:
            poly = simplify(hull([(p.y, max(p.z, belt)) for p in pts]))
            # the round-2 outline reaches round onto the A- and C-pillars' rounded corners, where the shell faces forwards
            # or back: a flat glass there stands out past them. Keep the part over shell that faces the side, its seal too
            wide = offset(poly, 0.05)
            side = [h for h, nrm in shell_under(tree, wide, sign, normals=True) if abs(nrm.x) > SIDE_FACING_COS]
            poly = simplify(clip(poly, offset(simplify(hull([(h.y, h.z) for h in side])), -SEAL_OUT)))
            # each glass is flat (so it can't crease), on the plane that fits the shell under it best
            plane = side_plane(shell_under(tree, poly, sign), sign)
            to3 = lambda q, pl=plane: pl(q)
            planes.append(to3)
            ztop = max(q[1] for q in poly)
            poly = fillet(poly, lambda c, t=ztop: SIDE_TOP_RADIUS if c[1] > t - 0.05 else SIDE_LOW_RADIUS)
            k = len(made)
            made.append(disc(f'glass_side_{sign}_{k}', tree, offset(poly, -0.002), to3, SIDE_GLASS_PROUD, glass_mat, coll,
                             rings=1, floor=shell))   # flat: one ring is enough
            # the seal slopes from the glass down onto the shell, which falls away from the glass's plane at its edges
            made.append(ring(f'trim_seal_side_{sign}_{k}', tree, offset(poly, SEAL_OUT), offset(poly, -SEAL_OVERLAP), to3,
                             SIDE_SEAL_PROUD, rubber, coll, floor=shell, outer_proud=SEAL_EDGE_PROUD,
                             outer_to3=lambda q, s=sign: ((s * 1.2, q[0], q[1]), (-s, 0, 0))))
            boxes.append((min(p.y for p in pts), max(p.y for p in pts), min(p.z for p in pts), max(p.z for p in pts)))
        # the black B-pillar and the divider before the quarter window fill the gaps between the seals
        for k, ((f0, f1, fz0, fz1), (r0, r1, rz0, rz1), label) in enumerate([(boxes[0], boxes[1], 'b_pillar'), (boxes[1], boxes[2], 'quarter_divider')]):
            to3 = planes[k + 1]   # on the plane of the window behind it
            y0, y1 = r1 - 0.004, f0 + 0.004
            z0, z1 = max(fz0, rz0) - 0.01, min(fz1, rz1) - 0.004
            rect = [(y0, z0), (y1, z0), (y1, z1), (y0, z1)]
            made.append(disc(f'trim_{label}_{sign}', tree, rect, to3, SIDE_SEAL_PROUD - 0.001, rubber, coll, rings=1, floor=shell))
    return made


def tail_lamp(tree, sign, red, amber, clear, rubber, coll):
    """The 1990 tail lamp: a black bezel over the whole unit, the lenses inset in two rows, ribs across them."""
    x0, x1, z0, z1 = TAIL
    b = TAIL_BEZEL_M
    made = [plate(f'lamp_rear_bezel_{sign}', tree, rear_grid(sign, x0, x1, z0, z1, TAIL_WRAP_Y), rubber, coll, proud=0.006)]
    xa = x1 - TAIL_AMBER_W
    xc = xa - TAIL_CLEAR_W
    lens = LENS_PROUD
    rows = [('lamp_rear_red_low', (x0 + b, x1 - b, z0 + b, TAIL_SPLIT_Z - b / 2), red, TAIL_WRAP_Y - b),
            ('lamp_rear_red_high', (x0 + b, xc - b / 2, TAIL_SPLIT_Z + b / 2, z1 - b), red, 0.0),
            ('lamp_rear_reverse', (xc + b / 2, xa - b / 2, TAIL_SPLIT_Z + b / 2, z1 - b), clear, 0.0),
            ('lamp_rear_indicator', (xa + b / 2, x1 - b, TAIL_SPLIT_Z + b / 2, z1 - b), amber, TAIL_WRAP_Y - b)]
    for name, (a0, a1, c0, c1), mat, wrap in rows:
        made.append(plate(f'{name}_{sign}', tree, rear_grid(sign, a0, a1, c0, c1, wrap, n=(6, 2)), mat, coll, proud=lens))
    # ribs: a darker red pressed across the red lenses only, so the amber and clear lenses stay clean
    rib_mat = material('tail lamp red rib', (.36, .05, .04))
    ribs = []
    z = z0 + b + TAIL_RIB_PITCH * 0.6
    while z < z1 - b - TAIL_RIB_H:
        low = z + TAIL_RIB_H < TAIL_SPLIT_Z - b / 2
        high = z > TAIL_SPLIT_Z + b / 2
        if low or high:
            a1, wrap = (x1 - b, TAIL_WRAP_Y - b) if low else (xc - b / 2, 0.0)
            ribs.append(plate(f'lamp_rear_rib_{sign}', tree, rear_grid(sign, x0 + b, a1, z, z + TAIL_RIB_H, wrap, n=(4, 1)),
                              rib_mat, coll, proud=lens + 0.0015))
        z += TAIL_RIB_PITCH
    made.append(S.merge_static(ribs, f'lamp_rear_ribs_{sign}'))
    return made



def lathe(name, profile, segments, mat, collection, flat_edges=()):
    """A closed solid of revolution about the local x axis: `profile` is a loop of (a, r) points, a along the axis.
    Edges between profile points listed in `flat_edges` (index pairs) are shaded flat, the rest smooth."""
    verts, faces = [], []
    n = len(profile)
    for k in range(segments):
        t = 2 * math.pi * k / segments
        for a, r in profile:
            verts.append((a, r * math.cos(t), r * math.sin(t)))
    for k in range(segments):
        k1 = (k + 1) % segments
        for i in range(n):
            j = (i + 1) % n
            faces.append((k * n + i, k * n + j, k1 * n + j, k1 * n + i))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    # sharp where the profile turns by more than 40 degrees: a flat face and a round tread, not a ball
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.link_faces[0].normal.angle(e.link_faces[1].normal, 0) > math.radians(40):
            e.smooth = False
    for f in bm.faces:
        f.smooth = True
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def wheels(report):
    """Rebuilds each tyre and its cover in place: same objects, names, hubs and positions."""
    for side in ['fl', 'fr', 'rl', 'rr']:
        wheel = bpy.data.objects['wheel_' + side]
        out = -1 if wheel.matrix_world.translation.x < 0 else 1   # the outer face is towards the outside
        w, r = TYRE_HALF_W, TYRE_R
        ca, cr = TYRE_CHAMFER
        # (a along the axle from the outer face, r): hub hole, face, shoulder, tread, shoulder, inner face
        prof = [(out * w, COVER_R - 0.02), (out * w, r - cr), (out * (w - ca), r), (-out * (w - ca), r),
                (-out * w, r - cr), (-out * w, 0.09), (-out * (w + 0.06), 0.09), (-out * (w + 0.06), COVER_R - 0.02)]
        tyre = lathe('tyre_tmp', prof, WHEEL_SEGMENTS, wheel.data.materials[0], wheel.users_collection[0])
        old = wheel.data
        wheel.data = tyre.data
        wheel.data.name = 'wheel_' + side
        bpy.data.objects.remove(tyre, do_unlink=True)
        bpy.data.meshes.remove(old)
        rim = bpy.data.objects['trim_rim_wheel_' + side]
        mat = rim.data.materials[0]
        coll = rim.users_collection[0]
        bpy.data.objects.remove(rim, do_unlink=True)
        # a shallow dish: flush with the face at its edge, its centre COVER_DOME out, its back inside the tyre
        cover = [(out * (w + 0.001), COVER_R), (out * (w + COVER_DOME * 0.6), COVER_R * 0.75),
                 (out * (w + COVER_DOME), COVER_R * 0.18), (out * (w + COVER_DOME), 0.0), (out * (w - 0.02), 0.0),
                 (out * (w - 0.02), COVER_R)]
        rim = lathe('trim_rim_wheel_' + side, cover, WHEEL_SEGMENTS, mat, coll)
        rim.parent = wheel
        rim.matrix_parent_inverse.identity()
        rim.location = (0, 0, 0)
    report['wheels'] = 'rebuilt: flat face, round tread, full cover'


def mirrors(report):
    """Smaller housings, square to the car, touching the door below the A-pillar."""
    ox, oy, oz = MIRROR
    for name in ['mirror_housing', 'mirror_housing.001']:
        o = bpy.data.objects[name]
        sign = -1 if (o.matrix_world @ o.data.vertices[0].co).x < 0 else 1
        x0, y, z = MIRROR_AT
        # slightly narrower at the outer end, as a housing tapers
        pts = []
        for xo, taper in [(0.0, 1.0), (ox, 0.82)]:
            for dy in [-oy / 2, oy / 2]:
                for dz in [-oz / 2, oz / 2]:
                    pts.append((sign * (x0 + xo), y + dy * taper, z + dz * taper))
        faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(pts, [], faces)
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(o.data.materials[0])
        old = o.data
        o.data = mesh
        o.matrix_world = o.matrix_world.Identity(4) if o.parent is None else o.parent.matrix_world.inverted()
        bpy.data.meshes.remove(old)
    report['mirrors'] = 'rebuilt: %.0f x %.0f x %.0f cm' % (ox * 100, oy * 100, oz * 100)


def spoiler(tree, rubber, coll):
    hw, z0, z1 = SPOILER
    grid = [[((x, 2.8, z), (0, -1, 0)) for x in [-hw + 2 * hw * i / 12 for i in range(13)]] for z in [z0, (z0 + z1) / 2, z1]]
    return plate('trim_front_spoiler', tree, grid, rubber, coll, proud=0.008)


def apply(body_tree_owner='body'):
    body = bpy.data.objects[body_tree_owner]
    if body.get('round3_shape_revision') == REVISION:
        return None
    report = {}
    # ---------- greenhouse ----------
    report['body_vertices_widened'] = widen(body)
    report['glass_vertices_widened'] = widen(bpy.data.objects['glass_envelope'])
    mirrors(report)
    wheels(report)
    S.panel_normals(body, side_limit=.80, belt=.95)
    bpy.context.view_layer.update()

    # ---------- lamps ----------
    deps = bpy.context.evaluated_depsgraph_get()
    tree = BVHTree.FromObject(body, deps)
    # the tree is in the body's local space, which is world space: the body sits at the origin unrotated
    assert body.matrix_world.is_identity
    red = bpy.data.materials['tail lamp red']
    # clear and cool, not the headlamps' ivory, which is too close to the paint to read on the rear face
    clear = material('reverse lamp clear', (.93, .95, .97))
    amber = material('indicator amber', (.85, .42, .05))
    lights = bpy.data.collections.get('DETAILS') or bpy.context.scene.collection
    rubber = bpy.data.materials['matte charcoal rubber']
    for name in ['lamp_rear_-1', 'lamp_rear_1', 'lamp_rear_reverse', 'lamp_rear_reverse.001']:
        o = bpy.data.objects.get(name)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
    made = glazing(tree, body, report)
    made.append(spoiler(tree, rubber, lights))
    for sign in [-1, 1]:
        made += tail_lamp(tree, sign, red, amber, clear, rubber, lights)
        # front corner: amber beside the headlamp, wrapping onto the wing
        x0, x1, z0, z1 = FRONT_AMBER
        grid = []
        for j in range(3):
            z = z0 + (z1 - z0) * j / 2
            row = [((sign * (x0 + (x1 - x0) * i / 2), 2.7, z), (0, -1, 0)) for i in range(3)]
            row += [((sign * 1.2, 2.31 - FRONT_WRAP_Y * i / 3, z), (-sign, 0, 0)) for i in range(1, 4)]
            grid.append(row)
        made.append(plate(f'lamp_front_indicator_{sign}', tree, grid, amber, lights))
    # one mesh per material for everything this round adds
    by_mat = {}
    for o in made:
        by_mat.setdefault(o.data.materials[0].name, []).append(o)
    names = {'matte charcoal rubber': 'trim_rubber', 'glazing envelope clay': 'glass_rebuilt',
             'tail lamp red': 'lamp_rear_red', 'tail lamp red rib': 'lamp_rear_ribs', 'indicator amber': 'lamp_indicators',
             'reverse lamp clear': 'lamp_rear_reverse'}
    merged = []
    for mat, objs in by_mat.items():
        o = S.merge_static(objs, names.get(mat, 'round3_' + mat.replace(' ', '_')))
        o.parent = body
        merged.append(o)
    # every round-2 window is rebuilt, so the new glass becomes the envelope's mesh: the pipeline keys on that name
    envelope = bpy.data.objects['glass_envelope']
    rebuilt = bpy.data.objects['glass_rebuilt']
    mesh = rebuilt.data.copy()
    mesh.transform(envelope.matrix_world.inverted() @ rebuilt.matrix_world)
    old_mesh, envelope.data = envelope.data, mesh
    mesh.name = old_mesh.name
    bpy.data.meshes.remove(old_mesh)
    merged.remove(rebuilt)
    bpy.data.objects.remove(rebuilt)
    # then every static part, round 2's too, is one mesh per material (#408): the body, its glass and the wheels with
    # their covers stay apart (the game paints the body, cracks the glass and spins the wheels)
    static = {}
    for o in body.children:
        if o.type == 'MESH' and o.name != 'glass_envelope':
            static.setdefault(o.data.materials[0].name, []).append(o)
    merged = [S.merge_static(objs, STATIC_NAMES.get(mat, objs[0].name)) for mat, objs in sorted(static.items())]
    report['added_meshes'] = sorted(o.name for o in merged)
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
