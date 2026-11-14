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
                       back+P['c_pillar_width_y'], rr, -.96, -.87, -.23, -.16,
                       P['quarterlight_divider_y'],
                       P['quarterlight_divider_y']+P['quarterlight_divider_width'],
                       rf, rf+.045, cowl-.055, cowl,
                       1.42, 2.05, front-.13, front-.06, front]))
verts, faces, indices = [], [], []
for y in stations:
    w = W/2 * interp(y, [(rear,.94),(rear+.13,1),(-1.8,1),(1.8,1),(front-.13,.985),(front,.92)])
    top = interp(y, roof_profile)
    cabin = max(0, min(1, (top-.97)/(H-.025-.97)))
    roof_w = w*.83*(1-cabin) + P['roof_half_width']*cabin
    belt = min(P['belt_z'], top-.14)
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
        setback = .10 * end_factor
        yy = y-math.copysign(setback,y)
        verts.append((x,yy,z))
N = len(ring)
for i in range(len(stations)-1):
    mid = (stations[i]+stations[i+1])/2
    for j in range(N):
        faces.append((i*N+j, i*N+(j+1)%N, (i+1)*N+(j+1)%N, (i+1)*N+j))
        # Side glazing strips; pillars are material regions on the same mesh.
        divider = P['quarterlight_divider_y'] < mid < P['quarterlight_divider_y']+P['quarterlight_divider_width']
        side_window = j in (7,14) and back+P['c_pillar_width_y'] < mid < cowl-.055 and not (-.23 < mid < -.16 or divider)
        windscreen = (rf+.045 < mid < cowl-.055 or back+.055 < mid < rr) and 9 <= j <= 12
        indices.append(int(side_window or windscreen))
# Close each end with horizontal strips. Each strip is planar even where the
# integrated bumper projects past the upper fascia; a single cap n-gon was warped.
for i in (0,len(stations)-1):
    # Bottom centre, right/left bottom and next side level make a five-vertex
    # planar region. Fan it explicitly; the first three bottom vertices alone
    # are collinear and cannot form a valid cap triangle.
    for local in [(0,1,2),(0,2,N-2),(0,N-2,N-1)]:
        faces.append(tuple(i*N+j for j in local));indices.append(0)
    for j in range(2,11):
        cap=[i*N+j,i*N+(j+1),i*N+(N-j-1)%N,i*N+(N-j)%N]
        cap=list(dict.fromkeys(cap))
        faces.append(tuple(cap));indices.append(0)
body = mk.mesh_from_data('body', verts, faces)
body.data.materials.clear()
body.data.materials.append(clay)
# Separate seated glazing; closed body envelope remains underneath for game topology.
for poly,idx in zip(body.data.polygons,indices):poly.material_index=idx
bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
gv=[];gf=[]
for poly in body.data.polygons:
    idx=poly.material_index;poly.material_index=0
    if idx:
        start=len(gv)
        gv.extend([tuple(body.data.vertices[v].co) for v in poly.vertices])
        gf.append(tuple(range(start,len(gv))))
glazing=mk.mesh_from_data('glass_envelope',gv,gf)
glazing.data.materials.append(glass)
bm=bmesh.new();bm.from_mesh(glazing.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001)
bm.to_mesh(glazing.data);bm.free()
glazing.data.update()
for v in glazing.data.vertices:
    v.co.x*=1.010;v.co.y*=1.008
bpy.context.view_layer.objects.active=glazing
mod=glazing.modifiers.new('seated glazing thickness','SOLIDIFY');mod.thickness=.008;mod.offset=0
bpy.ops.object.modifier_apply(modifier=mod.name)

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
    if obj.name.startswith('wheel_'):
        colors=obj.data.color_attributes.new(name='ClayRegions',type='FLOAT_COLOR',domain='CORNER')
        for color in colors.data:
            color.color=tire.diffuse_color
    for poly in obj.data.polygons: poly.use_smooth=True
    obj['pilot_stage']='refinement; human visual approval pending'
body['construction']='closed longitudinal loft with four recessed Boolean wheel wells'
body['parameters']=json.dumps(P,sort_keys=True)
bpy.context.scene.unit_settings.system='METRIC'

# Logical Blender collections; pipeline mesh names stay lowercase and unchanged.
collections={}
for name in ['BODY','GLASS','PLASTIC & RUBBER','DETAILS','WHEELS']:
    c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);collections[name]=c

def group(obj,name,mat=None):
    for c in list(obj.users_collection):c.objects.unlink(obj)
    collections[name].objects.link(obj)
    if mat:
        obj.data.materials.clear();obj.data.materials.append(mat)
    return obj

group(body,'BODY');group(glazing,'GLASS')
rubber=material('matte charcoal rubber',(.055,.065,.065))
metal=material('restrained wheel alloy',(.38,.40,.39))
white=material('headlamp ivory',(.72,.73,.65))
red=material('tail lamp red',(.43,.055,.035))
for o in list(bpy.context.scene.objects):
    if o.name.startswith('wheel_'):
        group(o,'WHEELS',rubber)
        # Correct wheel pivots without moving the existing wheel surface.
        x=(-1 if o.name.endswith('l') else 1)*(P['front_track'] if '_f' in o.name else P['rear_track'])/2
        for v in o.data.vertices:v.co.x-=x
        o.location.x+=x

# Continuous swept bumper bands, with wraparound corners and a closed section.
# Front/rear shell y=2.31; inner bumper edge=2.285 gives a seated 25 mm overlap.
def band(name,path,z,height,depth,mat,collection):
    vertices=[]
    for i,(x,y) in enumerate(path):
        prev=path[max(0,i-1)];nxt=path[min(len(path)-1,i+1)]
        dx,dy=nxt[0]-prev[0],nxt[1]-prev[1];length=math.hypot(dx,dy)
        nx,ny=-dy/length,dx/length
        for side,h in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            vertices.append((x+nx*depth/2*side,y+ny*depth/2*side,z+h*height/2))
    faces=[]
    for i in range(len(path)-1):
        for j in range(4):faces.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
    faces.extend([(3,2,1,0),tuple((len(path)-1)*4+j for j in range(4))])
    o=group(mk.mesh_from_data(name,vertices,faces),collection,mat)
    bpy.context.view_layer.objects.active=o
    bevel=o.modifiers.new('small molded radii','BEVEL');bevel.width=.014;bevel.segments=2
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return o
for end,sign in [('front',1),('rear',-1)]:
    path=[(-.815,sign*1.96),(-.815,sign*2.22),(-.77,sign*2.34),(-.67,sign*2.36),(.67,sign*2.36),(.77,sign*2.34),(.815,sign*2.22),(.815,sign*1.96)]
    band('bumper_'+end,path,.455,.145,.10,rubber,'PLASTIC & RUBBER')
for sign in [-1,1]:
    band('trim_side_'+str(sign),[(sign*.851,-2.10),(sign*.858,-1.7),(sign*.858,1.7),(sign*.84,2.09)],.795,.027,.015,rubber,'PLASTIC & RUBBER')

# Small fitted character elements; no detached body panels.
def slab(name,dims,loc,mat,collection='DETAILS'):
    o=mk.box(name,dims,location=loc);group(o,collection,mat)
    bpy.context.view_layer.objects.active=o
    mod=o.modifiers.new('edge radius','BEVEL');mod.width=.008;mod.segments=1
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return o
slab('grille_front',(.65,.035,.22),(0,2.315,.695),rubber)
for sign in [-1,1]:
    slab('lamp_front_'+str(sign),(.40,.04,.22),(sign*.54,2.315,.695),white)
    slab('lamp_rear_'+str(sign),(.38,.04,.20),(sign*.56,-2.315,.675),red)
    for y in [.24,-.63]:slab('trim_handle',(.025,.145,.035),(sign*.85,y,.86),rubber,'PLASTIC & RUBBER')
    slab('mirror_housing',(.13,.24,.12),(sign*.85,.77,1.025),rubber,'PLASTIC & RUBBER')
for o in list(collections['WHEELS'].objects):
    sign=-1 if o.location.x<0 else 1
    rim=mk.cylinder('trim_rim_'+o.name,.205,.018,location=(o.location.x+sign*.091,o.location.y,o.location.z),rotation=(0,90,0),segments=20)
    group(rim,'WHEELS',metal)
# Ensure all meshes have portable triangles and consistent vertex normals.
for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    for f in o.data.polygons:f.use_smooth=True


for f in glazing.data.polygons:f.use_smooth=False

# Apply the same bounded wheel-well edit used on the existing Blender master.
import sys
sys.path.insert(0,str(HERE))
from refine_forms import refine
refine(body,P)

# Round 2 retains the approved arch solution and refines only adjacent panels/details.
from round2 import apply as apply_round2
apply_round2()
