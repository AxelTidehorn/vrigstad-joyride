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
from refine import LENS_PROUD, Glazing, face_grid, glazing, lathe, material, plate, take_envelope
from refine import mirrors as refine_mirrors

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
# rounded upper corners and set a few millimetres behind its seal, as on a 240 GL. The round-2 backlight runs up to the
# roof's top edge and wraps onto the C-pillars; the photographs show a smaller glass with paint above it and the pillars
# beside it. The round-2 screen wrapped round the A-pillars.
GLAZING = Glazing(rubber='matte charcoal rubber', screen_width=0.91, backlight_width=0.88, backlight_height=0.80)
FRONT_WRAP_Y = 0.07


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




def rear_grid(sign, x0, x1, z0, z1, wrap=0.0, n=(8, 4)):
    return face_grid(sign, x0, x1, z0, z1, face=-1, corner_y=2.31, wrap=wrap, n=n)




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
    report['mirrors'] = refine_mirrors(['mirror_housing', 'mirror_housing.001'], MIRROR, MIRROR_AT)


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
    made = glazing(tree, GLAZING)
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
    merged.remove(bpy.data.objects['glass_rebuilt'])
    take_envelope()
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
