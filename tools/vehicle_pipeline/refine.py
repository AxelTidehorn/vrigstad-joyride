"""Shared steps for refining a round-2 vehicle master in place (bpy only, no Blender Modeler): glass and seals cast onto
the closed shell, lens plates, outlines, lathed parts, and folding the rebuilt glass back into `glass_envelope`.

Coordinates are Blender's: X lateral (+right), Y forward, Z up, metres. Each model's round script holds its own
numbers and passes them in; see experiments/volvo240/round3.py.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import bmesh
import bpy
from mathutils import Matrix, Vector

DEEP_M = 0.04            # a cast that lands this far behind its window's plane went past it (into the cowl, the cabin)
LENS_PROUD = 0.010       # a lens stands this far off the shell (m)
LENS_SINK = 0.004        # and reaches this far into it, so it reads seated, never floating


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


def plate(name, tree, grid, mat, collection, proud=LENS_PROUD, smooth=False):
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
    if smooth:   # a lens round a corner: smooth across it, sharp only at its rim
        for f in bm.faces:
            f.smooth = True
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.link_faces[0].normal.angle(e.link_faces[1].normal, 0) > math.radians(60):
                e.smooth = False
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return obj


def face_grid(sign, x0, x1, z0, z1, face, corner_y, wrap=0.0, n=(8, 4), far=2.6):
    """Points in front of the car's front (face +1) or rear (face -1), cast onto it along Y, x0..x1 from the centre on
    side `sign`; with `wrap`, the outer column continues round the corner, from `corner_y` towards the middle, cast
    inwards from beside the car."""
    cols = []
    for i in range(n[0] + 1):
        cols.append(('face', x0 + (x1 - x0) * i / n[0]))
    for i in range(1, 4 if wrap else 0):
        cols.append(('side', face * (corner_y - wrap * i / 3)))
    grid = []
    for j in range(n[1] + 1):
        z = z0 + (z1 - z0) * j / n[1]
        row = []
        for kind, u in cols:
            row.append(((sign * u, face * far, z), (0, -face, 0)) if kind == 'face' else ((sign * 1.2, u, z), (-sign, 0, 0)))
        grid.append(row)
    return grid


def mirrors(names, size, at):
    """Rebuilds each mirror housing as a box tapering towards its outer end, square to the car: `size` is (out from
    the door, along the car, tall), `at` is (inner face x, centre y, centre z), mirrored to each housing's side."""
    ox, oy, oz = size
    for name in names:
        o = bpy.data.objects[name]
        sign = -1 if (o.matrix_world @ o.data.vertices[0].co).x < 0 else 1
        x0, y, z = at
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
    return 'rebuilt: %.0f x %.0f x %.0f cm' % (ox * 100, oy * 100, oz * 100)


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


def resample(poly, step):
    """Splits every edge of a closed polygon longer than `step` evenly, so a long straight edge cast onto a curved
    surface follows it instead of cutting under it."""
    out = []
    for i in range(len(poly)):
        a, b = Vector(poly[i]), Vector(poly[(i + 1) % len(poly)])
        k = max(1, math.ceil((b - a).length / step))
        out += [tuple(a.lerp(b, j / k)) for j in range(k)]
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


def cast(tree, loop, to3, proud, sink=LENS_SINK, floor=None, deep=DEEP_M):
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
        if fallback and (hit[0] is None or (hit[0] - fallback[1]).dot(fallback[2]) < -deep):
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


def ring(name, tree, outer, inner, to3, proud, mat, collection, floor=None, outer_proud=None, outer_to3=None,
         deep=DEEP_M):
    """A closed band between two loops of the same length: a seal or a bezel. With `outer_proud`, its outer edge
    stands lower than its inner one, a bead sloping down to the paint; with `outer_to3`, that edge is placed its own
    way (on the shell, round glass laid on a plane)."""
    of, ob = cast(tree, outer, outer_to3 or to3, proud if outer_proud is None else outer_proud, floor=floor, deep=deep)
    inf, inb = cast(tree, inner, to3, proud, floor=floor, deep=deep)
    n = len(outer)
    verts = of + inf + ob + inb
    O, I, OB, IB = 0, n, 2 * n, 3 * n
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces += [(O + i, O + j, I + j, I + i), (OB + i, IB + i, IB + j, OB + j),
                  (O + i, OB + i, OB + j, O + j), (I + i, I + j, IB + j, IB + i)]
    return solid(name, verts, faces, mat, collection)


def disc(name, tree, loop, to3, proud, mat, collection, rings=4, floor=None, deep=DEEP_M, normal=None):
    """A closed plate over a convex loop (glass or a lens), cast onto the shell in concentric rings down to its
    centre, so a curved panel stays on the surface instead of sinking under it along the chord."""
    n = len(loop)
    cx = sum(p[0] for p in loop) / n
    cy = sum(p[1] for p in loop) / n
    loops = [[(cx + (p[0] - cx) * (1 - k / rings), cy + (p[1] - cy) * (1 - k / rings)) for p in loop] for k in range(rings)]
    front, back = [], []
    for lp in loops + [[(cx, cy)]]:
        f, b = cast(tree, lp, to3, proud, floor=floor, deep=deep)
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
    obj = solid(name, front + back, faces, mat, collection)
    if normal is not None:
        even(obj.data, normal)
    return obj


def even(mesh, normal):
    """Shades a plate's faces as if flat across `normal`: a curved glass then reads one even tone, as glass does,
    instead of showing the rings it is cast in. Faces facing away get -normal; the rim keeps its own."""
    normal = Vector(normal).normalized()
    loops = []
    for p in mesh.polygons:
        d = p.normal.dot(normal)
        n = normal if d > 0.5 else -normal if d < -0.5 else p.normal
        loops += [tuple(n)] * p.loop_total
    mesh.normals_split_custom_set(loops)


def side_plane(points, sign):
    """The plane x = a*y + b*z + c through the side glass points (least squares), as a placement for (y, z)."""
    n = len(points)
    sy = sum(p.y for p in points); sz = sum(p.z for p in points); sx = sum(p.x for p in points)
    syy = sum(p.y * p.y for p in points); szz = sum(p.z * p.z for p in points); syz = sum(p.y * p.z for p in points)
    sxy = sum(p.x * p.y for p in points); sxz = sum(p.x * p.z for p in points)
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

@dataclass
class Glazing:
    """One model's glazing numbers (m): see glazing()."""
    rubber: str                         # the seals' material
    seal_out: float = 0.016             # seal width outside the glass edge
    seal_overlap: float = 0.006         # the seal laps over the glass edge, so no gap shows
    seal_proud: float = 0.019
    glass_proud: float = 0.014          # glass stands this far off the shell, 5 mm behind its seal
    screen_radius: float = 0.06         # windscreen and backlight corners
    screen_width: float = 1.0           # of the round-2 screen's span
    screen_height: float = 1.0          # of the round-2 screen's height, top edge kept
    screen_glass_proud: float = 0.009
    screen_seal_proud: float = 0.013
    screen_seal_edge: float = 0.003     # the screen seal's outer edge: it slopes down to the paint
    screen_deep_m: float = DEEP_M       # a cast this far behind the screen's plane went past it: kept on the plane
    screen_even: bool = False          # shade the screen and backlight one even tone (see even())
    screen_step: float | None = None   # split the screen's and backlight's edges to this length (m), for a curved screen
    screen_wrap: dict | None = None    # {'pillar': [(y, z), ...], 'depth', 'top_z', 'radius' (m)}: the screen wraps round the A-pillars
    backlight_rings: int | None = None  # rings for the backlight, if not screen_rings
    screen_rings: int = 2               # concentric rings the screen and backlight are cast in: more for a curved screen
    backlight_width: float = 1.0        # of the round-2 backlight, about its centre
    backlight_height: float = 1.0       # of the round-2 backlight, bottom edge kept
    side_top_radius: float = 0.075      # rounded upper corners of the side glass
    side_low_radius: float = 0.015
    quarter_radius: float | None = None  # the rearmost side window's lower rear corner, swept round
    side_glass_proud: float = 0.005     # off its plane, which already sits on the shell's outermost point under it
    side_seal_proud: float = 0.009
    side_seal_edge: float = 0.003       # a side seal's outer edge, on the shell
    side_facing_deg: float = 35         # side glass only over shell facing within this of the side
    side_min_x: float = 0.6             # an envelope island further out than this is a side window
    side_outlines: list | None = None   # drawn side windows, front to back, each a convex (y, z) outline: replace round 2's
    side_wrap: list | None = None       # a (y, z) outline of the screen's wrap seen from the side, cast onto the shell


def glazing(tree, g: Glazing):
    """Rebuilds every window of `glass_envelope` onto the closed shell (`tree`, the body alone):

    - the windscreen and the backlight, cast onto the shell with a seal; round 2 laid each as a flat sheet over the shell,
      wrapping round onto the pillars, where it stood out past them;
    - the side windows, each flat on the plane that fits the shell under it, cut back to the shell that faces the side,
      with one straight belt line, rounded upper corners and a seal sloping down onto the shell;
    - a black pillar filling the gap between each side window and the next.

    Returns the new objects; the old glass is deleted from the envelope (see take_envelope())."""
    glass = bpy.data.objects['glass_envelope']
    mw = glass.matrix_world
    shell = tree   # the shell is closed under every window: the new glass and seals are cast onto it
    rubber = bpy.data.materials[g.rubber]
    glass_mat = glass.data.materials[0]
    coll = glass.users_collection[0]
    made, side_faces = [], []
    sides = {-1: [], 1: []}
    for isl in islands(glass):
        pts = [mw @ glass.data.vertices[v].co for i in isl for v in glass.data.polygons[i].vertices]
        xs = [p.x for p in pts]
        if min(abs(x) for x in xs) > g.side_min_x:   # a side window: rebuilt below
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
        poly = fillet(poly, lambda c: g.screen_radius)
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
            # screen_height above 1 reaches the bottom edge further down towards the cowl, the top edge kept
            top = max(q[1] for q in raw) if v.z > 0 else min(q[1] for q in raw)
            small = [(q[0] * g.screen_width, top + (q[1] - top) * g.screen_height) for q in raw]
        else:
            name = 'backlight'
            bottom = min(q[1] for q in raw) if v.z > 0 else max(q[1] for q in raw)
            small = [(q[0] * g.backlight_width, bottom + (q[1] - bottom) * g.backlight_height) for q in raw]
        small = fillet(small, lambda c: g.screen_radius)
        if g.screen_step:
            small = resample(small, g.screen_step)
        if name == 'screen' and g.screen_wrap:
            made += wrapped_screen(tree, g, small, placed, centre, n, v, glass_mat, rubber, coll)
            continue
        gp, sp, op = (g.screen_glass_proud, g.screen_seal_proud, g.screen_seal_edge) if name == 'screen' else (g.glass_proud, g.seal_proud, None)
        rings = g.backlight_rings if name == 'backlight' and g.backlight_rings else g.screen_rings
        made.append(disc(f'glass_{name}', tree, offset(small, -0.002), placed, gp, glass_mat, coll, rings=rings,
                         floor=shell, deep=g.screen_deep_m, normal=n if g.screen_even else None))
        made.append(ring(f'trim_seal_{name}', tree, offset(small, g.seal_out), offset(small, -g.seal_overlap), placed,
                         sp, rubber, coll, floor=shell, outer_proud=op, deep=g.screen_deep_m))
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
        if g.side_outlines:   # drawn outlines (y, z) instead of round 2's glass, the same on both sides
            wins = [[Vector((sign * g.side_min_x, y, z)) for y, z in poly] for poly in g.side_outlines]
        wins = sorted(wins, key=lambda ps: -max(p.y for p in ps))   # front to back
        # one straight belt line under them all, as on the car: the highest of their round-2 bottoms
        belt = max(min(p.z for p in ps) for ps in wins)
        for pts in wins:
            # round 2's glass: its bottom lifted to the belt; drawn outlines are taken as drawn
            poly = hull([(p.y, p.z if g.side_outlines else max(p.z, belt)) for p in pts])
            if not g.side_outlines:   # round 2's glass: only its real corners; a drawn outline keeps its curves
                poly = simplify(poly)
            # the round-2 outline reaches round onto the A- and C-pillars' rounded corners, where the shell faces forwards
            # or back: a flat glass there stands out past them. Keep the part over shell that faces the side, its seal too
            if not g.side_outlines:
                wide = offset(poly, 0.05)
                side = [h for h, nrm in shell_under(tree, wide, sign, normals=True)
                        if abs(nrm.x) > math.cos(math.radians(g.side_facing_deg))]
                poly = simplify(clip(poly, offset(simplify(hull([(h.y, h.z) for h in side])), -g.seal_out)))
            # each glass is flat (so it can't crease), on the plane that fits the shell under it best
            plane = side_plane(shell_under(tree, poly, sign), sign)
            to3 = lambda q, pl=plane: pl(q)
            planes.append(to3)
            ztop = max(q[1] for q in poly)
            if g.quarter_radius and pts is wins[-1]:   # the rearmost window: its lower rear corner sweeps round
                ymid = (min(q[0] for q in poly) + max(q[0] for q in poly)) / 2
                poly = fillet(poly, lambda c, t=ztop, m=ymid: g.side_top_radius if c[1] > t - 0.05 else
                              g.quarter_radius if c[0] < m else g.side_low_radius)
            else:
                poly = fillet(poly, lambda c, t=ztop: g.side_top_radius if c[1] > t - 0.05 else g.side_low_radius)
            k = len(made)
            made.append(disc(f'glass_side_{sign}_{k}', tree, offset(poly, -0.002), to3, g.side_glass_proud, glass_mat, coll,
                             rings=1, floor=shell))   # flat: one ring is enough
            # the seal slopes from the glass down onto the shell, which falls away from the glass's plane at its edges
            made.append(ring(f'trim_seal_side_{sign}_{k}', tree, offset(poly, g.seal_out), offset(poly, -g.seal_overlap), to3,
                             g.side_seal_proud, rubber, coll, floor=shell, outer_proud=g.side_seal_edge,
                             outer_to3=lambda q, s=sign: ((s * 1.2, q[0], q[1]), (-s, 0, 0))))
            boxes.append((min(p.y for p in pts), max(p.y for p in pts), min(p.z for p in pts), max(p.z for p in pts)))
        # a black pillar fills the gap between the seals of each window and the next (the B-pillar, a quarter divider)
        for k, ((f0, f1, fz0, fz1), (r0, r1, rz0, rz1)) in enumerate(zip(boxes, boxes[1:])):
            label = 'b_pillar' if k == 0 else f'divider_{k}'
            to3 = planes[k + 1]   # on the plane of the window behind it
            y0, y1 = r1 - 0.004, f0 + 0.004
            z0, z1 = max(fz0, rz0) - 0.01, min(fz1, rz1) - 0.004
            rect = [(y0, z0), (y1, z0), (y1, z1), (y0, z1)]
            made.append(disc(f'trim_{label}_{sign}', tree, rect, to3, g.side_seal_proud - 0.001, rubber, coll, rings=1, floor=shell))
        if g.side_wrap:
            # the screen's wrap seen from the side, ahead of the A-pillar: cast onto the shell, which turns there from
            # the side to the front, so it follows it instead of standing out as a flat glass would
            poly = fillet(g.side_wrap, lambda c: g.side_low_radius)
            onto = lambda q, s=sign: ((s * 1.2, q[0], q[1]), (-s, 0, 0))
            made.append(disc(f'glass_wrap_{sign}', tree, offset(poly, -0.002), onto, g.side_glass_proud, glass_mat, coll,
                             rings=3, floor=shell))
            made.append(ring(f'trim_seal_wrap_{sign}', tree, offset(poly, g.seal_out), offset(poly, -g.seal_overlap), onto,
                             g.side_seal_proud, rubber, coll, floor=shell, outer_proud=g.side_seal_edge))
    return made


def wrapped_screen(tree, g, outline, placed, centre, n, v, glass_mat, rubber, coll):
    """One screen curving from the front round both A-pillars to the door windows, as on a Saab 900.

    It is laid out round an axis behind the screen that leans with it (along `v`): a point (u, s) is s up that axis and
    u = 0.8 m x the angle round it from straight ahead, and its ray runs in towards the axis, square to it, so the
    front rays are the plain screen's (along -n) and the side rays run in from the side. The glass is a grid in (u, s)
    inside the hull of the plain screen's outline and the A-pillar line (`screen_wrap['pillar']`, (y, z) points);
    each row's distance from the axis is smoothed, so the shell's small bumps under the glass don't show, and pushed
    out wherever the shell would come through. A seal runs round its whole edge."""
    R0 = 0.8
    x = Vector((1, 0, 0))
    a = v.normalized()
    P0 = centre - n * g.screen_wrap.get('depth', 0.45)
    w = lambda u: n * math.cos(u / R0) + x * math.sin(u / R0)

    def to_us(p):
        d = p - P0
        s = d.dot(a)
        r = d - a * s
        return (math.atan2(r.dot(x), r.dot(n)) * R0, s)

    def shell_at(u, s):
        base, d = P0 + a * s, w(u)
        return tree.ray_cast(base + d * 3, -d)[0]

    def reach(u, s):
        """The shell's distance from the axis at (u, s), or None."""
        hit = shell_at(u, s)
        return None if hit is None else (hit - P0 - a * s).dot(w(u))

    top = g.screen_wrap.get('top_z')   # a straight top edge at this height
    pts = []
    for q in outline:
        for _ in range(8):   # with `top_z`, a point landing above it slides down the glass (along v) until it doesn't
            start, ray = placed(q)[:2]
            hit = tree.ray_cast(Vector(start), Vector(ray))[0]
            if hit is None or top is None or hit.z <= top + 1e-4:
                break
            q = (q[0], q[1] - (hit.z - top) / v.z)
        if hit is not None:
            pts.append(to_us(hit))
    for sign in (-1, 1):
        for y, z in g.screen_wrap['pillar']:
            hit = tree.ray_cast(Vector((sign * 1.2, y, z)), Vector((-sign, 0, 0)))[0]
            if hit is None:
                raise RuntimeError(f'no A-pillar under {(y, z)}')
            pts.append(to_us(hit))
    bound = fillet(simplify(hull(pts)), lambda c: g.screen_radius)

    def span(u):
        cuts = []
        for k in range(len(bound)):
            (u0, s0), (u1, s1) = bound[k - 1], bound[k]
            if (u0 - u) * (u1 - u) <= 0 and u0 != u1:
                cuts.append(s0 + (s1 - s0) * (u - u0) / (u1 - u0))
        return min(cuts), max(cuts)

    NU, NS = 96, 16
    umin, umax = min(q[0] for q in bound) + 1e-3, max(q[0] for q in bound) - 1e-3
    us = [umin + (umax - umin) * i / NU for i in range(NU + 1)]
    grid = []   # grid[i][j] = (u, s)
    def lower(u, s_in, s_out):
        """From s_out, above `top`, back towards s_in until the shell there is at `top` (bisection)."""
        for _ in range(20):
            mid = (s_in + s_out) / 2
            h = shell_at(u, mid)
            if h is not None and h.z > top:
                s_out = mid
            else:
                s_in = mid
        return s_in

    ends = []
    for u in us:
        s0, s1 = span(u)
        if top is not None:   # each column's top end cut down to `top` round the corner too, not just at the front
            hi, lo = (s0, s1) if a.z < 0 else (s1, s0)
            h = shell_at(u, hi)
            if h is not None and h.z > top:
                hi = lower(u, lo, hi)
            s0, s1 = (hi, lo) if a.z < 0 else (lo, hi)
        ends.append((s0, s1))
    if top is not None:
        # the cut follows the shell's bumps at the A-pillar's top: smooth its line round the corner
        k = 0 if a.z < 0 else 1   # which end of a column is its top
        line = [e[k] for e in ends]
        for _ in range(12):
            line = [line[0]] + [(line[i - 1] + 2 * line[i] + line[i + 1]) / 4 for i in range(1, len(line) - 1)] + [line[-1]]
        ends = [(t, e[1]) if k == 0 else (e[0], t) for t, e in zip(line, ends)]
        # the cut outline, rounded again as one shape: its top meets the pillar line in a corner, which would show as a
        # notch in the seal, and its corners take the wrap's own radius
        cut = [(u, e[0]) for u, e in zip(us, ends)] + [(u, e[1]) for u, e in reversed(list(zip(us, ends)))]
        bound = fillet(simplify(cut, min_turn_deg=4), lambda c: g.screen_wrap.get("radius", g.screen_radius))   # not a hull: the cut top dips
        umin, umax = min(q[0] for q in bound) + 1e-3, max(q[0] for q in bound) - 1e-3
        us = [umin + (umax - umin) * i / NU for i in range(NU + 1)]
        ends = [span(u) for u in us]
    for u, (s0, s1) in zip(us, ends):
        grid.append([(u, s0 + (s1 - s0) * j / NS) for j in range(NS + 1)])
    hits = [[shell_at(*grid[i][j]) for j in range(NS + 1)] for i in range(NU + 1)]
    raw = [[None if hits[i][j] is None else (hits[i][j] - P0 - a * grid[i][j][1]).dot(w(grid[i][j][0]))
            for j in range(NS + 1)] for i in range(NU + 1)]
    for i in range(NU + 1):   # a miss takes its column neighbour's
        for j in range(NS + 1):
            if raw[i][j] is None:
                raw[i][j] = next(raw[i][k] for k in sorted(range(NS + 1), key=lambda k: abs(k - j)) if raw[i][k] is not None)
    r = [row[:] for row in raw]
    for _ in range(4):   # smooth along the rows (round the car), then up the columns
        r = [[r[i][j] if i in (0, NU) else (r[i - 1][j] + 2 * r[i][j] + r[i + 1][j]) / 4 for j in range(NS + 1)]
             for i in range(NU + 1)]
    for _ in range(1):
        r = [[r[i][j] if j in (0, NS) else (r[i][j - 1] + 2 * r[i][j] + r[i][j + 1]) / 4 for j in range(NS + 1)]
             for i in range(NU + 1)]
    gp = g.screen_glass_proud
    # clear of the shell's highest point round each node, so a crease between the rays (the A-pillar's) can't show
    # (along its row only: up the column the next row can land on the roof's edge, further out, and lift the glass)
    # (the neighbours' hits measured along this node's own ray: round the corner their rays point elsewhere)
    def peak_at(i, j):
        base, d = P0 + a * grid[i][j][1], w(grid[i][j][0])
        near = [hits[k][j] for k in range(max(0, i - 2), min(NU, i + 2) + 1) if hits[k][j] is not None]
        return max([raw[i][j]] + [(h - base).dot(d) for h in near])
    peak = [[peak_at(i, j) for j in range(NS + 1)] for i in range(NU + 1)]
    front = [[max(r[i][j] + gp, peak[i][j] + gp / 2) for j in range(NS + 1)] for i in range(NU + 1)]
    # built on a coarser grid than it is measured on: every fourth row (round the car it needs every column), each node clear of the
    # highest point in its cell, plus the chord's sag round the tightest corner (3 mm)
    DU, DS = 1, 4
    keep_i, keep_j = list(range(0, NU + 1, DU)), list(range(0, NS + 1, DS))
    cell = lambda i, j, t: max(t[k][l] for k in range(max(0, i - DU + 1), min(NU, i + DU - 1) + 1)
                               for l in range(max(0, j - DS + 1), min(NS, j + DS - 1) + 1))
    front = [[cell(i, j, front) + 0.003 for j in keep_j] for i in keep_i]
    peak = [[cell(i, j, peak) for j in keep_j] for i in keep_i]
    grid = [[grid[i][j] for j in keep_j] for i in keep_i]
    NU, NS = len(keep_i) - 1, len(keep_j) - 1
    pos = lambda u, s, d: P0 + a * s + w(u) * d
    idx = lambda i, j: i * (NS + 1) + j
    m = (NU + 1) * (NS + 1)
    verts = [pos(*grid[i][j], front[i][j]) for i in range(NU + 1) for j in range(NS + 1)]
    verts += [pos(*grid[i][j], front[i][j] - gp - LENS_SINK) for i in range(NU + 1) for j in range(NS + 1)]
    faces = []
    for i in range(NU):
        for j in range(NS):
            q = (idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1))
            faces += [q, tuple(m + k for k in reversed(q))]
    loop = [(i, 0) for i in range(NU + 1)] + [(NU, j) for j in range(1, NS + 1)] + \
           [(i, NS) for i in range(NU - 1, -1, -1)] + [(0, j) for j in range(NS - 1, 0, -1)]
    for k in range(len(loop)):
        p, q = idx(*loop[k]), idx(*loop[(k + 1) % len(loop)])
        faces.append((p, m + p, m + q, q))
    made = [solid('glass_screen', verts, faces, glass_mat, coll)]

    # the seal round the edge: its inner edge laps over the glass, its outer edge lands on the shell, kept near the
    # glass's distance where a ray past the edge would land far off (on the hood beyond the cowl)
    L = [grid[i][j] for i, j in loop]
    N = len(L)
    area = sum(L[k - 1][0] * L[k][1] - L[k][0] * L[k - 1][1] for k in range(N))
    outs = []
    for k in range(N):   # the edge's outward direction over a few nodes either side, so a short grid step can't tilt it
        t = Vector((L[(k + 3) % N][0] - L[k - 3][0], L[(k + 3) % N][1] - L[k - 3][1])).normalized()
        outs.append(Vector((t.y, -t.x)) if area > 0 else Vector((-t.y, t.x)))
    ro = []
    for k, (i, j) in enumerate(loop):
        u, s = grid[i][j]
        r_ = reach(u + outs[k].x * g.seal_out, s + outs[k].y * g.seal_out)
        ro.append(peak[i][j] if r_ is None else min(max(r_, peak[i][j] - 0.03), peak[i][j] + 0.01))
    for _ in range(3):   # where the seal's outer edge lands on the shell, smoothed along the edge
        ro = [(ro[k - 1] + 2 * ro[k] + ro[(k + 1) % N]) / 4 for k in range(N)]
    of, inf, ob, inb = [], [], [], []
    for k, (i, j) in enumerate(loop):
        u, s = grid[i][j]
        uo, so = u + outs[k].x * g.seal_out, s + outs[k].y * g.seal_out
        ui, si = u - outs[k].x * g.seal_overlap, s - outs[k].y * g.seal_overlap
        of.append(pos(uo, so, ro[k] + g.screen_seal_edge))
        ob.append(pos(uo, so, ro[k] - LENS_SINK))
        inf.append(pos(ui, si, front[i][j] + g.screen_seal_proud - gp / 2))
        inb.append(pos(ui, si, front[i][j] - gp - LENS_SINK))
    n_ = len(loop)
    O, I, OB, IB = 0, n_, 2 * n_, 3 * n_
    faces = []
    for k in range(n_):
        l = (k + 1) % n_
        faces += [(O + k, O + l, I + l, I + k), (OB + k, IB + k, IB + l, OB + l),
                  (O + k, OB + k, OB + l, O + l), (I + k, I + l, IB + l, IB + k)]
    made.append(solid('trim_seal_screen', of + inf + ob + inb, faces, rubber, coll))
    return made


def take_envelope(glass_name='glass_rebuilt'):
    """Every round-2 window is rebuilt, so the merged new glass becomes `glass_envelope`'s mesh: the pipeline and the game
    key on that name."""
    envelope = bpy.data.objects['glass_envelope']
    rebuilt = bpy.data.objects[glass_name]
    mesh = rebuilt.data.copy()
    mesh.transform(envelope.matrix_world.inverted() @ rebuilt.matrix_world)
    old_mesh, envelope.data = envelope.data, mesh
    mesh.name = old_mesh.name
    bpy.data.meshes.remove(old_mesh)
    bpy.data.objects.remove(rebuilt)
