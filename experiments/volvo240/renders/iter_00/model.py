"""1990 Volvo 240 sedan clay blockout. Run through Blender Modeler bmod.py.

Vehicle convention overrides Modeler's default: X right, +Y front, Z up, metres.
The body is a closed longitudinal loft. Glazing uses faces of that same shell.
Four exact Boolean wheel wells keep continuous recessed walls, never fake panels.
"""
import modelkit as mk
import bpy
import bmesh
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = json.loads((HERE / 'parameters.json').read_text())


def interp(y, knots):
    for (a, u), (b, v) in zip(knots, knots[1:]):
        if a <= y <= b:
            return u + (v-u)*(y-a)/(b-a)
    return knots[0][1] if y < knots[0][0] else knots[-1][1]


def material(name, rgb):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = .85
    return mat


clay = material('body clay', (.56, .55, .51))
glass = material('glazing envelope clay', (.19, .23, .25))
tire = material('wheel clay', (.27, .27, .26))
# Parameter-derived silhouette stations; no post-build stretch to target dimensions.
L, W, H = P['length'], P['width'], P['height']
rear, front = -L/2, L/2
cowl, rf, rr, back = [P[k] for k in
                         ('cowl_y', 'roof_front_y', 'roof_rear_y', 'backlight_base_y')]
roof_profile = [(rear, .87), (rear+.13, .92), (back, .965),
                (rr, H-.025), (rf, H-.025), (cowl, .97), (front-.13, .87), (front, .82)]
# Extra stations at the B-pillar and quarterlight boundary split glazing in-mesh.
stations = sorted(set([rear, rear+.06, rear+.13, -1.9, back, back+.055,
                       rr, -.96, -.87, -.23, -.16, rf, cowl-.055, cowl,
                       1.42, 2.05, front-.13, front-.06, front]))
verts, faces, indices = [], [], []
for y in stations:
    w = W/2 * interp(y, [(rear,.94),(rear+.13,1),(-1.8,1),(1.8,1),(front-.13,.985),(front,.92)])
    top = interp(y, roof_profile)
    cabin = max(0, min(1, (top-.97)/(H-.025-.97)))
    roof_w = w*.83*(1-cabin) + P['roof_half_width']*cabin
    belt = P['belt_z']
    base = min(P['window_base_z'], top-.045)
    # Positive-X half, bottom centre to roof centre. Mirror shares centre vertices.
    half = [(0,P['sill_z']), (w*.87,P['sill_z']), (w*.95,.31), (w,.49),
            (w,belt), (w*.985,base-.03), (w*.94,base),
            (roof_w+(w*.94-roof_w)*.91,base+(top-base)*.09),
            (roof_w+(w*.94-roof_w)*.10,base+(top-base)*.90),
            (roof_w,top), (roof_w*.80,top+.016), (0,top+.025)]
    ring = half + [(-x,z) for x,z in half[-2:0:-1]]
    for j,(x,z) in enumerate(ring):
        # Bumper-volume extremities and upper nose/tail set-back are in the loft.
        end_factor = max(0, (abs(y)-(L/2-.13))/.13)
        setback = .09 * end_factor if z > .70 else 0
        yy = y-math.copysign(setback,y)
        verts.append((x,yy,z))
N = len(ring)
for i in range(len(stations)-1):
    mid = (stations[i]+stations[i+1])/2
    for j in range(N):
        faces.append((i*N+j, i*N+(j+1)%N, (i+1)*N+(j+1)%N, (i+1)*N+j))
        # Side glazing strips; pillars are material regions on the same mesh.
        side_window = j in (7,14) and back+.055 < mid < cowl-.055 and not -.23 < mid < -.16
        windscreen = (rf < mid < cowl-.055 or back+.055 < mid < rr) and 9 <= j <= 12
        indices.append(int(side_window or windscreen))
faces.extend([tuple(range(N-1,-1,-1)), tuple((len(stations)-1)*N+j for j in range(N))])
indices.extend([0,0])
body = mk.mesh_from_data('body', verts, faces)
body.data.materials.clear()
body.data.materials.append(clay)
body.data.materials.append(glass)
for poly, idx in zip(body.data.polygons,indices):
    poly.material_index = idx

# Recess wells only from the outside to an inner wall. Body retains its centre spine.
rear_axle = P['front_axle_y']-P['wheelbase']
for axle, y in [('f', P['front_axle_y']), ('r', rear_axle)]:
    for side, sign in [('l',-1), ('r',1)]:
        inner = P['well_inner_x']
        cutter = mk.cylinder('_well', P['arch_radius'], 1.4-inner,
                             location=(sign*(1.4+inner)/2,y,P['tire_radius']),
                             rotation=(0,90,0), segments=48)
        bpy.context.view_layer.objects.active=body
        mod=body.modifiers.new('integrated wheel well','BOOLEAN')
        mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cutter,do_unlink=True)
        track=P['front_track'] if axle=='f' else P['rear_track']
        # A plain wheel envelope with central hub extending into the well wall.
        # This is an attachment interface, not a tire/body intersection workaround.
        outer=track/2+P['tire_width']/2
        inside=track/2-P['tire_width']/2
        profile=[(0,inner-.025),(.09,inner-.025),(.09,inside),
                 (P['tire_radius']-.025,inside), (P['tire_radius'],inside+.022),
                 (P['tire_radius'],outer-.022), (P['tire_radius']-.025,outer),(0,outer)]
        # mk.lathe revolves about Z; rotate Z to signed lateral X and apply rotation.
        wheel=mk.lathe('wheel_'+axle+side,profile,segments=48)
        wheel.rotation_euler[1]=sign*math.pi/2
        wheel.location=(0,y,P['tire_radius'])
        wheel.data.materials.append(tire)
        bpy.context.view_layer.objects.active=wheel
        wheel.select_set(True);body.select_set(False)
        bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
        wheel.select_set(False)

# Triangulation makes n-gon Boolean output portable and geometry checks unambiguous.
for obj in list(bpy.context.scene.objects):
    if obj.type!='MESH': continue
    bm=bmesh.new();bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(obj.data);bm.free();obj.data.update()
    obj['pilot_stage']='clay blockout; not approved for game integration'
body['construction']='closed longitudinal loft with four recessed Boolean wheel wells'
body['parameters']=json.dumps(P,sort_keys=True)
bpy.context.scene.unit_settings.system='METRIC'
