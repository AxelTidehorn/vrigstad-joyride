"""The XC70's body shell, lofted from measured tables: smooth, closed, one mesh (round 3).

Round 2's shell (model.py's loft, triangulated, with the window frames, door gaps and arches cut into it) shows facets
and waves in reflections. This one is lofted through cross sections, each from the sill up the side to a top edge and
across the top, from the tables below, which were measured from round 2's shell (its side profile already matches the
manufacturer's side view), with the nose lifted and rounded after the photographs. Shut lines and glass go on top.
"""
import math
import bpy, bmesh
from mathutils import Vector

# ---------- the side profile: (y, z) along the top from the front face's foot over the roof to the rear's ----------
SILL_Z = 0.21
FRONT_Y, REAR_Y = 2.29, -2.29
# the front: a vertical face to 0.78 m, a tight convex turn (a quadratic Bezier) into the hood, which falls
# HOOD_FALL per metre forward of the cowl and curves down towards the front: round 2's nose, 6 cm higher (photographs)
NOSE_P = [(2.29, 0.78), (2.29, 0.888), (2.17, 0.920)]
HOOD = [(2.17, 0.920), (2.0, 0.936), (1.7, 0.958), (1.3, 0.990), (1.0, 1.020), (0.92, 1.034)]
# the windscreen, the roof (its crown) and the tailgate, measured on round 2's shell along the middle
GREENHOUSE = [(0.92, 1.034), (0.9, 1.055), (0.7, 1.163), (0.5, 1.2986), (0.3, 1.4011), (0.2, 1.438), (0.1, 1.4565),
              (-0.1, 1.475), (-0.5, 1.487), (-1.1, 1.4942), (-1.5, 1.49), (-1.9, 1.4785), (-2.0, 1.468), (-2.079, 1.46),
              (-2.169, 1.40), (-2.2003, 1.34), (-2.2318, 1.28), (-2.2556, 1.22), (-2.2756, 1.10), (-2.29, 1.04)]
# ---------- widths ----------
# half width at each height up to the belt, at the middle of the car (round 2's, which is the same all along)
WIDTH = [(0.21, 0.785), (0.26, 0.800), (0.32, 0.829), (0.38, 0.859), (0.44, 0.870), (0.50, 0.878), (0.56, 0.886),
         (0.62, 0.894), (0.68, 0.8995), (0.74, 0.8965), (0.80, 0.8935), (0.86, 0.8905), (0.92, 0.8875), (0.98, 0.869),
         (1.02, 0.852)]
BELT_Z = 1.02
BELT_BLEND = 0.05
GH_W0 = 0.838        # the greenhouse's half width at the belt (the pillars' outside, round 2's)
GH_SLOPE = 0.26      # its sides lean in this much per metre up
# plan: the ends round off as quarter ellipses (tangent to the end and the side): in by K x the width at the very end,
# over D metres back; the greenhouse's own (the windscreen's and tailgate glass's wrap) as an exponential
PLAN = {'front': (0.30, 0.42), 'rear': (0.055, 0.14)}
PLAN_K_GH, PLAN_D_GH = 0.25, 0.08
PLAN_DROP, PLAN_BLEND = 0.10, 0.12    # each section's top part takes the plan of PLAN_DROP below its top (see half_width)
# the edge where the top meets the sides: a broad roll over the hood and wings, the greenhouse's soft roof edge above
TOP_R, TOP_R_ROOF = 0.07, 0.08
EDGE_SOFT_Z = (1.04, 1.16)
CROWN_M = 0.012
EDGE_STEPS, TOP_STEPS, EDGE_HANDLE = 9, 8, 0.55
STATIONS = 230
DENSE_Y = [(-2.29, -1.95), (0.15, 1.0), (1.95, 2.29)]
UP = 18
COWL_SMOOTH = ((0.70, 1.05), (0.97, 1.12), 0.10, 10)   # y range, z range, fade (m), passes
# ---------- wheel openings: under round 2's arch mouldings (trim_arch) ----------
HUBS = [(1.37, 0.345), (-1.393, 0.345)]
ARCH_HALF_W, ARCH_TOP, ARCH_POWER, ARCH_DEPTH_X = 0.415, 0.415, 2.3, 0.62


def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def bezier2(p0, p1, p2, n):
    return [tuple((1 - t) ** 2 * a + 2 * t * (1 - t) * b + t * t * c for a, b, c in zip(p0, p1, p2))
            for t in [k / n for k in range(n + 1)]]


def outline():
    """(z, front y, rear y) rows, from the profile: each side of the roof's highest point inverted to y at height z."""
    prof = [(FRONT_Y, SILL_Z)] + bezier2(*NOSE_P, 12) + HOOD[1:] + GREENHOUSE[1:] + [(REAR_Y, SILL_Z)]
    peak = max(range(len(prof)), key=lambda i: prof[i][1])
    front, rear = prof[:peak + 1], prof[peak:][::-1]
    def y_at(side, z):
        for (ya, za), (yb, zb) in zip(side, side[1:]):
            if za <= z <= zb and zb > za:
                return ya + (yb - ya) * (z - za) / (zb - za)
        return side[-1][0]
    top = prof[peak][1]
    zs = sorted({round(SILL_Z + (top - SILL_Z) * k / 400, 5) for k in range(401)} | {p[1] for p in prof})
    return [(z, y_at(front, z), y_at(rear, z)) for z in zs]


OUTLINE = outline()


def interp(table, x):
    if x <= table[0][0]:
        return table[0][1]
    for a, b in zip(table, table[1:]):
        if x <= b[0]:
            return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])
    return table[-1][1]


def ends_at(z):
    z = min(max(z, OUTLINE[0][0]), OUTLINE[-1][0])
    lo, hi = 0, len(OUTLINE) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if OUTLINE[mid][0] <= z:
            lo = mid
        else:
            hi = mid
    a, b = OUTLINE[lo], OUTLINE[hi]
    t = 0.0 if b[0] == a[0] else (z - a[0]) / (b[0] - a[0])
    return a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t


def top_at(y):
    lo, hi = SILL_Z, OUTLINE[-1][0]
    for _ in range(32):
        mid = (lo + hi) / 2
        f, r = ends_at(mid)
        if r <= y <= f:
            lo = mid
        else:
            hi = mid
    return lo


def half_width(y, z, zt=None):
    f, r = ends_at(z)
    d = max(0.0, min(f - y, y - r))
    # the top part of each section takes the plan of PLAN_DROP below its top, blended in: measured at each height, the
    # nearly level hood's end runs back fast with height and folded the wing's corner
    d_body = d
    if zt is not None and z > zt - PLAN_DROP - PLAN_BLEND:
        f2, r2 = ends_at(zt - PLAN_DROP)
        u = smoothstep((z - (zt - PLAN_DROP - PLAN_BLEND)) / PLAN_BLEND)
        d_body = d + (max(0.0, min(f2 - y, y - r2)) - d) * u
    k, dd = PLAN['front' if y > 0 else 'rear']
    q = 1 - min(1.0, d_body / dd)
    body = interp(WIDTH, min(z, BELT_Z)) * (1 - k * (1 - math.sqrt(max(0.0, 1 - q * q))))
    cab = (GH_W0 - GH_SLOPE * max(0.0, z - BELT_Z)) * (1 - PLAN_K_GH * math.exp(-d / PLAN_D_GH))
    g = smoothstep((z - BELT_Z) / BELT_BLEND)
    return body + (cab - body) * g


def section_top(y):
    """Height, edge radius, softness, crown, the side's lean where the edge starts, and that height (see build)."""
    zt = top_at(y)
    soft = smoothstep((zt - EDGE_SOFT_Z[0]) / (EDGE_SOFT_Z[1] - EDGE_SOFT_Z[0]))
    rr = TOP_R + (TOP_R_ROOF - TOP_R) * soft
    rr = min(rr, 0.45 * half_width(y, zt - rr, zt), 0.45 * (zt - SILL_Z))
    crown = CROWN_M * (1 - soft)
    z0 = zt - rr - crown
    lean = half_width(y, z0 - 0.03, zt) - half_width(y, z0, zt)
    phi = min(1.2, max(0.0, math.atan2(lean, 0.03))) * (1 - soft)
    return zt, rr, soft, crown, phi, zt - crown - rr * (1 - math.sin(phi))


def edge_x(y):
    """Where the top's edge begins at y: the hood's shut line runs along it."""
    zt, rr, soft, crown, phi, zs = section_top(y)
    return half_width(y, zs, zt) - rr * math.cos(phi)


def stations():
    dens = lambda y: 1 + 2 * any(a <= y <= b for a, b in DENSE_Y)
    fine = [REAR_Y + (FRONT_Y - REAR_Y) * k / 4000 for k in range(4001)]
    cum = [0.0]
    for a, b in zip(fine, fine[1:]):
        cum.append(cum[-1] + dens((a + b) / 2) * (b - a))
    ys, j = [], 0
    for k in range(STATIONS):
        target = cum[-1] * k / (STATIONS - 1)
        while j < len(cum) - 2 and cum[j + 1] < target:
            j += 1
        t = (target - cum[j]) / max(1e-12, cum[j + 1] - cum[j])
        ys.append(fine[j] + (fine[j + 1] - fine[j]) * min(1.0, t))
    return ys


def section(y):
    """One cross section's right half, (x, z) from the sill to the middle of the top."""
    zt, rr, soft, crown, phi, zs_top = section_top(y)
    cab = [SILL_Z + (BELT_Z - SILL_Z) * (0.5 - 0.5 * math.cos(math.pi * k / 12)) for k in range(13)]
    cab += [BELT_Z + 0.004] + [BELT_Z + 0.004 + (zs_top - BELT_Z - 0.004) * math.sin(math.pi / 2 * k / UP) for k in range(1, UP + 1)]
    even = [SILL_Z + (zs_top - SILL_Z) * (0.5 - 0.5 * math.cos(math.pi * k / (13 + UP))) for k in range(14 + UP)]
    t = smoothstep((zs_top - BELT_Z - 0.02) / 0.12)
    zs = [e + (c - e) * t for e, c in zip(even, cab)]
    side = [(half_width(y, z, zt), z) for z in zs]
    w0 = side[-1][0]
    xe, ze = w0 - rr * math.cos(phi), zs_top - rr * math.sin(phi)
    m = EDGE_STEPS + TOP_STEPS
    for k in range(1, m + 1):
        if k <= EDGE_STEPS:
            # a cubic from the side, along its lean, to the level top
            u = k / EDGE_STEPS
            p0, p3 = (w0, zs_top), (xe, ze + rr)
            p1 = (w0 - EDGE_HANDLE * rr * math.sin(phi), zs_top + EDGE_HANDLE * rr * math.cos(phi))
            p2 = (xe + EDGE_HANDLE * rr, ze + rr)
            b = [(1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u * u * (1 - u), u ** 3]
            cx = sum(c * q[0] for c, q in zip(b, (p0, p1, p2, p3)))
            cz = sum(c * q[1] for c, q in zip(b, (p0, p1, p2, p3)))
        else:
            u = 1 - (k - EDGE_STEPS) / TOP_STEPS
            cx, cz = xe * u, zt - crown * u * u
        a = math.pi / 2 * k / m
        side.append((cx + (w0 * math.cos(a) - cx) * soft, cz + (zt - rr + rr * math.sin(a) - cz) * soft))
    side[-1] = (0.0, side[-1][1])
    return side


def build(obj):
    """Replaces obj's mesh with the lofted shell, its wheel openings cut with black wells; returns the face count."""
    verts, faces, loops = [], [], []
    for y in stations():
        side = section(y)
        loop = [len(verts)]
        verts.append((0.0, y, SILL_Z))
        for x, z in side:
            loop.append(len(verts))
            verts.append((x, y, z))
        for x, z in reversed(side[:-1]):
            loop.append(len(verts))
            verts.append((-x, y, z))
        loops.append(loop)
    n = len(loops[0])
    for a, b in zip(loops, loops[1:]):
        for k in range(n):
            faces.append((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    faces.append(tuple(loops[0]))
    faces.append(tuple(reversed(loops[-1])))
    mesh = bpy.data.meshes.new('body')
    mesh.from_pydata(verts, [], faces)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    for m in obj.data.materials:
        mesh.materials.append(m)
    old, obj.data = obj.data, mesh
    bpy.data.meshes.remove(old)
    mesh.name = 'body'
    smooth_cowl(obj)
    cut_arches(obj)
    wells = wheel_wells(obj)
    reshade(obj)
    return len(obj.data.polygons), wells


def smooth_cowl(obj):
    """Where the wing's edge, the greenhouse's soft one and the belt meet at the A-pillar's foot, neighbouring sections
    sample the side differently and ripple: smoothed there, fading out over COWL_SMOOTH's fade."""
    (y0, y1), (z0, z1), fade, passes = COWL_SMOOTH
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    def weight(p):
        if abs(p.x) < 0.45:
            return 0.0
        return max(0.0, 1 - math.hypot(max(y0 - p.y, p.y - y1, 0.0), max(z0 - p.z, p.z - z1, 0.0)) / fade)
    vs = [(v, weight(v.co)) for v in bm.verts]
    vs = [(v, w) for v, w in vs if w > 0 and not v.is_boundary]
    for _ in range(passes):
        moved = [v.co + (sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges) - v.co) * 0.5 * w
                 for v, w in vs]
        for (v, _), c in zip(vs, moved):
            v.co = c
    bm.to_mesh(obj.data)
    bm.free()


def arch_norm(y, z, hy, hz):
    dz = z - hz
    return abs((y - hy) / ARCH_HALF_W) ** ARCH_POWER + abs(dz / (ARCH_TOP if dz > 0 else ARCH_HALF_W)) ** ARCH_POWER


def cut_arches(obj):
    bm = bmesh.new()
    n = 56
    for hy, hz in HUBS:
        for sign in (-1, 1):
            ring = []
            for k in range(n):
                t = 2 * math.pi * k / n
                c, s_ = math.cos(t), math.sin(t)
                ring.append((hy + ARCH_HALF_W * math.copysign(abs(c) ** (2 / ARCH_POWER), c),
                             hz + (ARCH_TOP if s_ > 0 else ARCH_HALF_W) * math.copysign(abs(s_) ** (2 / ARCH_POWER), s_)))
            va = [bm.verts.new((sign * ARCH_DEPTH_X, a, b)) for a, b in ring]
            vb = [bm.verts.new((sign * 1.3, a, b)) for a, b in ring]
            bm.faces.new(va)
            bm.faces.new(vb[::-1])
            for k in range(n):
                bm.faces.new((va[k], va[k - 1], vb[k - 1], vb[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cutter = bpy.data.objects.new('arch_cutter', bpy.data.meshes.new('arch_cutter'))
    bm.to_mesh(cutter.data)
    bm.free()
    bpy.context.scene.collection.objects.link(cutter)
    m = obj.modifiers.new('arches', 'BOOLEAN')
    m.operation, m.object, m.solver = 'DIFFERENCE', cutter, 'EXACT'
    mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
    obj.modifiers.remove(m)
    old, obj.data = obj.data, mesh
    for mat in old.materials:
        mesh.materials.append(mat)
    for f in mesh.polygons:
        f.material_index = 0
    mesh.name = old.name
    bpy.data.meshes.remove(old)
    bpy.data.objects.remove(cutter)


def wheel_wells(obj):
    """The openings' walls, copied 2 mm inside as one black object (the shell stays closed)."""
    def on_cutter(f):
        c, cap = f.calc_center_median(), abs(f.normal.x) > 0.9
        if abs(c.x) < ARCH_DEPTH_X - 0.002 or not (cap or abs(f.normal.x) < 0.3):
            return False
        for hy, hz in HUBS:
            r = arch_norm(c.y, c.z, hy, hz)
            if r < 1.02 and (r > 0.98 and not cap or cap and abs(abs(c.x) - ARCH_DEPTH_X) < 0.002):
                return True
        return False
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    keep = [f for f in bm.faces if on_cutter(f)]
    out = bmesh.new()
    vmap = {}
    for f in keep:
        vs = []
        for v in f.verts:
            if v not in vmap:
                vmap[v] = out.verts.new(v.co)
            vs.append(vmap[v])
        out.faces.new(vs)
    for v, w in vmap.items():
        nrm = sum((f.normal for f in v.link_faces if f in keep), Vector())
        if nrm.length:
            w.co = v.co + nrm.normalized() * 0.002
    bm.free()
    mesh = bpy.data.meshes.new('trim_wheel_wells')
    out.to_mesh(mesh)
    out.free()
    mat = bpy.data.materials.get('charcoal plastic rubber')
    mesh.materials.append(mat)
    well = bpy.data.objects.new('trim_wheel_wells', mesh)
    obj.users_collection[0].objects.link(well)
    well.parent = obj
    return len(keep)


def reshade(obj, sharp_deg=50):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.normal_update()
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = not (len(e.link_faces) == 2 and
                        e.link_faces[0].normal.angle(e.link_faces[1].normal, 0) > math.radians(sharp_deg))
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
