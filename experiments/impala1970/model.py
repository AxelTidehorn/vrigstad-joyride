"""Original 16439 hardtop geometry, built with the established Modeler pipeline.

X right / Y front / Z up. The steel is one closed loft; inset window backings
and recessed wells are part of that volume. No other vehicle's sections reused.
"""
import sys, json, math, os
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector
import modelkit as mk

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'tools/vehicle_pipeline'))
import authoring as T
import surface_refinement as S
P = json.loads((HERE / 'parameters.json').read_text())
STAGE = os.environ.get('IMPALA_STAGE', 'complete')
for name in ['BODY', 'GLASS', 'CHROME', 'RUBBER', 'LIGHTS', 'DETAILS', 'WHEELS']:
    c = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c); T.collections[name] = c
paint = T.material('Impala configurable body paint', (.068, .135, .092))
glass = T.material('smoky blue grey glass', (.085, .135, .16))
chrome = T.material('restrained satin chrome', (.49, .53, .52))
rubber = T.material('weatherstrip rubber', (.028, .033, .032))
tire = T.material('tire charcoal', (.037, .039, .038))
rim = T.material('period wheel covers', (.40, .43, .42))
whitewall = T.material('narrow ivory whitewall', (.70, .69, .59))
head = T.material('sealed beam ivory', (.72, .77, .69))
red = T.material('red tail lenses', (.48, .025, .018))
reverse = T.material('clear reverse lenses', (.30, .34, .32))
amber = T.material('amber parking lamps', (.73, .27, .018))
plate = T.material('registration ivory', (.73, .73, .66))
for mat, rough, metallic in [(paint,.66,.08),(chrome,.42,.70),(rim,.52,.5),(glass,.72,.00)]:
    bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=rough;bsdf.inputs['Metallic'].default_value=metallic

roof=P['roof_profile'];shoulders=P['shoulder_profile'];widths=P['half_width_profile']
base_profile=[(-2.67,.835),(-1.5,.99),(-.55,1.005),(.65,.90),(1.13,.887),(2.67,.755)]
def section_heights(y):
    top=T.interp(y,roof);base=min(T.interp(y,base_profile),top-.040)
    return top,base,min(T.interp(y,shoulders),base-.026)
ys=sorted(set([p[0] for p in roof] + [p[0] for p in widths] + [p[0] for p in shoulders] +
              [-1.57,-1.50,-1.11,-.98,-.55,-.15,-.142,-.138,-.13,.51,.56,1.045,1.075,2.60,-2.60]))
verts=[];faces=[];zones=[]
for y in ys:
    top,base,shoulder=section_heights(y);w=T.interp(y,widths)
    cabin=max(0,min(1,(top-1.00)/.35));rw=w*.875*(1-cabin)+P['roof_half_width']*cabin
    # Controlled coke-bottle shoulder; crown flattens toward the long hood/deck.
    half=[(0,.20),(.78*w,.20),(.90*w,.255),(.965*w,.37),
          (.995*w,min(.60,shoulder-.14)),(w,shoulder-.065),(.998*w,shoulder-.018),
          (.982*w,shoulder),(.94*w,base),
          (rw+(.94*w-rw)*.92,base+.045*(top-.025-base)),
          (rw+(.94*w-rw)*.08,base+.92*(top-.025-base)),
          (rw,top-.025),(.83*rw,top-.012),(.45*rw,top-.003),(0,top)]
    ring=half+[(-x,z) for x,z in half[-2:0:-1]]
    for j,(x,z) in enumerate(ring):
        if j in (12,len(ring)-12) and 1.13<y<2.67:
            z+=.022*min(1,(y-1.13)/.17,(2.67-y)/.17)
        # Windshield wrap is shallow and confined to that surface, not the hood.
        bow=.018*(1-(abs(x)/w)**2) if .56<=y<=1.045 else 0
        # Window-belt stations are sheared relative to the roof stations. This
        # makes a true hardtop trapezoid, instead of a pointed glass wedge that
        # follows the falling windshield/backlight envelope to its very end.
        belt_y=T.interp(y,[(-2.67,-2.67),(-1.60,-1.60),(-.55,-.90),(.65,1.045),(1.30,1.30),(2.67,2.67)]) if j in (8,9,len(ring)-9,len(ring)-8) else y
        verts.append((x,belt_y+bow,z))
N=len(ring)
for i in range(len(ys)-1):
    mid=(ys[i]+ys[i+1])/2
    for j in range(N):
        faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
        # Continuous pillarless opening. Glass meeting strip is a separate sash,
        # not a fixed painted B-pillar. Broad real C pillar remains in the loft.
        side=j in (9,N-10) and -.55<mid<.65
        wind=.56<mid<1.045 and 11<=j<=N-12
        back=-1.57<mid<-.98 and 11<=j<=N-12
        zones.append(2 if wind else 3 if back else int(side))
faces += [tuple(range(N-1,-1,-1)),tuple((len(ys)-1)*N+j for j in range(N))];zones += [0,0]
body=T.group(mk.mesh_from_data('body',verts,faces),'BODY',paint)
for f,z in zip(body.data.polygons,zones):f.material_index=z
bm=bmesh.new();bm.from_mesh(body.data)
for zone in (1,2,3):
    res=bmesh.ops.inset_region(bm,faces=[f for f in bm.faces if f.material_index==zone],thickness=.009,depth=-.008,use_even_offset=True,use_boundary=True)
    for f in res['faces']:f.material_index=0
bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free();body.data.update()
# Extract exact aperture faces, retain a closed painted backing under every pane.
gv=[];gf=[];glass_boundaries=[]
for f in body.data.polygons:
    if f.material_index:
        start=len(gv);gv.extend(tuple(body.data.vertices[v].co) for v in f.vertices);gf.append(tuple(range(start,len(gv))))
    f.material_index=0
glazing=T.group(mk.mesh_from_data('glass_envelope',gv,gf),'GLASS',glass)
bm=bmesh.new();bm.from_mesh(glazing.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.normal_update()
# Each disconnected pane gets a constant outward seating vector; never expand
# glass about world origin (that breaks cowl/pillar fit).
remaining=set(bm.verts)
while remaining:
    pane={remaining.pop()};todo=list(pane)
    while todo:
        v=todo.pop()
        for e in v.link_edges:
            a=e.other_vert(v)
            if a in remaining:remaining.remove(a);pane.add(a);todo.append(a)
    xyz=np.array([tuple(v.co) for v in pane]);center=xyz.mean(axis=0)
    _,eig=np.linalg.eigh(np.cov(xyz.T));normal=Vector(eig[:,0])
    if normal.dot(Vector((center[0],center[1],center[2]-.7)))<0:normal=-normal
    for f in {f for v in pane for f in v.link_faces}:
        if f.normal.dot(normal)<0:f.normal_flip()
    for v in pane:v.co+=normal*.0015
    # Save true aperture edge chains for fitted metal/rubber surrounds later.
    for e in {e for v in pane for e in v.link_edges if len(e.link_faces)==1}:
        glass_boundaries.append([tuple(v.co+normal*.0025) for v in e.verts])
bm.to_mesh(glazing.data);bm.free()
bpy.context.view_layer.objects.active=glazing
mod=glazing.modifiers.new('seated glass thickness','SOLIDIFY');mod.thickness=.0025;mod.offset=1;bpy.ops.object.modifier_apply(modifier=mod.name)

def difference(target,cut,name):
    bpy.context.view_layer.objects.active=target
    m=target.modifiers.new(name,'BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cut
    bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cut,do_unlink=True)

# Separate front/rear door panes; the closed backing remains uncut. Narrow
# meeting sashes hide only the intended 4 mm door-glass join, not body defects.
difference(glazing,mk.box('_door_glass_join',(2.3,.004,.60),location=(0,P['glass_meeting_y'],1.20)),'hardtop glass meeting gap')

for axle,y in [('f',P['front_axle_y']),('r',P['front_axle_y']-P['wheelbase'])]:
    for side,sign in [('l',-1),('r',1)]:
        inner=P['well_inner_x']
        if axle=='f':
            cut=mk.cylinder('_well',P['front_arch_radius'],.8,location=(sign*(inner+.4),y,.35),rotation=(0,90,0),segments=36)
            difference(body,cut,'integrated front wheel well')
        else:
            # Full inner tyre clearance with a lower outer quarter opening.
            # The steel above the wheel is real thickness, not a floating skirt.
            cut=mk.cylinder('_pocket',.414,.35,location=(sign*(inner+.175),y,.35),rotation=(0,90,0),segments=36)
            difference(body,cut,'hidden rear tyre clearance')
            cut=mk.cylinder('_arch',1,.55,location=(sign*1.225,y,.35),rotation=(0,90,0),segments=36)
            for v in cut.data.vertices:v.co.x*=P['rear_arch_z_radius'];v.co.y*=P['rear_arch_y_radius']
            difference(body,cut,'low rear quarter opening')
        track=P['front_track'] if axle=='f' else P['rear_track'];center=sign*track/2
        inside=track/2-P['tire_width']/2;outside=track/2+P['tire_width']/2
        profile=[(0,inner-.018),(.10,inner-.018),(.10,inside),(.318,inside),(.35,inside+.025),(.35,outside-.025),(.322,outside),(0,outside)]
        wheel=mk.lathe('wheel_'+axle+side,profile,segments=36);wheel.rotation_euler.y=sign*math.pi/2;wheel.location=(0,y,.35);T.group(wheel,'WHEELS',tire)
        bpy.ops.object.select_all(action='DESELECT');wheel.select_set(True);bpy.context.view_layer.objects.active=wheel;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
        for v in wheel.data.vertices:v.co.x-=center
        wheel.location.x=center
        cover=mk.lathe('trim_rim_'+axle+side,[(0,outside+.016),(.045,outside+.021),(.055,outside+.014),(.125,outside+.010),(.132,outside+.014),(.155,outside+.010),(.18,outside+.004),(.191,outside),(0,outside)],segments=24)
        cover.rotation_euler.y=sign*math.pi/2;cover.location=(0,y,.35);T.group(cover,'WHEELS',rim)
        ring=mk.lathe('trim_rim_whitewall_'+axle+side,[(.286,outside-.001),(.296,outside-.001),(.296,outside+.002),(.286,outside+.002),(.286,outside-.001)],segments=24)
        ring.rotation_euler.y=sign*math.pi/2;ring.location=(0,y,.35);T.group(ring,'WHEELS',whitewall)
        # Put fixture origins at their own hub before the common nearest-hub
        # attachment helper runs. A centreline origin otherwise ties left/right.
        for fixture in (cover,ring):
            bpy.ops.object.select_all(action='DESELECT');fixture.select_set(True);bpy.context.view_layer.objects.active=fixture;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
            for v in fixture.data.vertices:v.co.x-=center
            fixture.location.x=center
        if STAGE=='complete':
            for k in range(8):
                a=k*math.tau/8
                slot=T.group(mk.box('trim_spoke_cover_slot',(.008,.012,.030),location=(sign*(outside+.011),y+math.sin(a)*.158,.35+math.cos(a)*.158)),'WHEELS',rubber)
                slot.rotation_euler.x=-a

def rod(name,a,b,r,mat,collection='CHROME',segments=6):
    a,b=Vector(a),Vector(b);o=mk.cylinder(name,r,(b-a).length,location=(a+b)/2,segments=segments)
    o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return T.group(o,collection,mat)

if STAGE=='complete':
    # Stable fixture order also fixes the first joined rod's basis. Otherwise
    # unordered BMesh edge sets introduce ~1 µm float differences between builds.
    glass_boundaries.sort(key=lambda edge:tuple(sorted(tuple(round(c,7) for c in p) for p in edge)))
    for edge in glass_boundaries:
        a,b=sorted(edge);rod('trim_window_surround',a,b,.0045,chrome,segments=4)
    # Slender meeting sash carried by the door glass; no painted B pillar.
    y=P['glass_meeting_y'];top=T.interp(y,roof)
    for sign in [-1,1]:
        rod('trim_glass_meeting_sash',(sign*.918,y,.966),(sign*.792,y,top-.058),.006,chrome)
    # Steel pressings are actual support cuts in the single body, never seam bars.
    side=lambda p: abs(p.x)>.91 and .34<p.z<.95
    for y in [1.045,-.14,-1.43]:S.press_line(body,1,y,.0035,.0016,side)
    S.press_line(body,2,.72,.004,.0013,lambda p: abs(p.x)>.945 and abs(p.y)<2.54)
    for y in [1.15,-1.67]:S.press_line(body,1,y,.0035,.0018,lambda p: abs(p.x)<.85 and p.z>.85,push_axis=2)
    for x in [-.75,.75]:S.press_line(body,0,x,.004,.002,lambda p: 1.18<p.y<2.58 and p.z>.79,push_axis=2)
    # Chrome fender spear and rocker trim follow the original shoulder/width curve.
    from mathutils.bvhtree import BVHTree
    bm=bmesh.new();bm.from_mesh(body.data);skin=BVHTree.FromBMesh(bm,epsilon=0);bm.free()
    trim_paths=[]
    trim_ys=sorted(set([-2.53,2.50]+[y for y,z in widths+shoulders+base_profile if -2.53<y<2.50]))
    for sign in [-1,1]:
        def fitted_point(y):
            z=section_heights(y)[2]-.025
            hit=skin.ray_cast(Vector((sign*3,y,z)),Vector((-sign,0,0)))
            if hit[0] is None:raise ValueError('Shoulder moulding has no actual steel support')
            return (hit[0].x+sign*.002,y,z)
        def fit_segment(a,b,level=0):
            # Add geometry only where a chord would leave the actual panel.
            gap=max(skin.find_nearest(Vector(a).lerp(Vector(b),t))[3] for t in [.25,.5,.75])
            if gap<.0035:return [a,b]
            if level>=7:raise ValueError('Shoulder moulding cannot follow steel')
            m=fitted_point((a[1]+b[1])/2)
            return fit_segment(a,m,level+1)[:-1]+fit_segment(m,b,level+1)
        line=[]
        for a,b in zip(trim_ys,trim_ys[1:]):
            fitted=fit_segment(fitted_point(a),fitted_point(b))
            line.extend(fitted if not line else fitted[1:])
        trim_paths.append(line)
        for a,b in zip(line,line[1:]):rod('trim_shoulder_spear',a,b,.006,chrome,segments=4)
        for y in [.08,-1.02]:
            x=sign*T.interp(y,widths)*.996;z=T.interp(y,shoulders)-.12
            T.slab('trim_handle_socket',(.018,.16,.045),(x,y,z),rubber,'DETAILS')
            T.slab('trim_door_handle',(.027,.13,.018),(x+sign*.009,y,z+.010),chrome,'CHROME')
        T.slab('lamp_tail_marker',(.016,.036,.124),(sign*T.interp(-2.51,widths)*.995,-2.51,.62),red,'LIGHTS')
        T.slab('lamp_front_marker',(.016,.085,.037),(sign*T.interp(2.42,widths)*.995,2.42,.58),amber,'LIGHTS')
        rear_axle=P['front_axle_y']-P['wheelbase']
        for a,b in [(-2.40,rear_axle-.45),(rear_axle+.45,P['front_axle_y']-.43),(P['front_axle_y']+.43,2.38)]:
            T.band('trim_rocker',[(sign*T.interp(y,widths)*.918,y) for y in [a,(a+b)/2,b]],.286,.025,.014,chrome,'CHROME')
        # Door-mounted period mirror, modest scale and supported stem.
        rod('mirror_stem',(sign*.91,.82,.98),(sign*1.035,.81,1.055),.012,chrome)
        T.slab('mirror_housing',(.10,.12,.065),(sign*1.055,.80,1.07),chrome,'CHROME')
    # Chrome bumpers have depth, tucked corner returns and original nominal ends.
    for label,sign,z,h in [('front',1,.425,.19),('rear',-1,.475,.245)]:
        path=[(-.965,sign*2.42),(-.992,sign*2.59),(-.968,sign*2.674),(-.83,sign*2.6932),(0,sign*2.6932),(.83,sign*2.6932),(.968,sign*2.674),(.992,sign*2.59),(.965,sign*2.42)]
        bumper=T.band('bumper_'+label,path,z,h,.10,chrome,'CHROME')
        # Lamps, air slot and plates sit in real bumper pockets. Merely placing
        # shallow inserts behind the chrome would leave them fully occluded.
        plate_z=.31 if label=='front' else .478
        difference(bumper,mk.box('_plate_pocket',(.36,.15,.15),location=(0,sign*2.725,plate_z)),'recessed registration mount')
        if label=='front':
            difference(bumper,mk.box('_air_pocket',(.98,.15,.070),location=(0,2.725,.435)),'lower grille opening')
            for x in [-.805,.805]:
                difference(bumper,mk.box('_amber_pocket',(.185,.15,.080),location=(x,2.725,.422)),'parking lamp pocket')
        if label=='rear':
            for x in [-.895,-.755,-.615,.615,.755,.895]:
                cut=mk.box('_lamp_pocket',(.102,.125,.177),location=(x,-2.708,.482));difference(bumper,cut,'recessed tail lamp socket')
                middle=abs(abs(x)-.755)<.01;mat=reverse if middle else red;name='lamp_reverse' if middle else 'lamp_tail'
                T.slab(name,(.089,.093,.161),(x,-2.6855,.482),mat,'LIGHTS')
                for dx in [-.023,0,.023]:T.slab(name+'_flute',(.004,.006,.145),(x+dx,-2.733,.482),mat,'LIGHTS')
    # Four round sealed beams in paired rectangular housings. All below hood.
    for sign in [-1,1]:
        S.frame('trim_headlamp_bezel',.404,.205,.046,(sign*.775,2.674,.660),chrome,T.collections['CHROME'],.012)
        T.slab('grille_lamp_recess',(.38,.023,.181),(sign*.775,2.671,.660),rubber,'DETAILS')
        for x in [.677,.873]:
            cyl=mk.cylinder('lamp_head',.082,.025,location=(sign*x,2.698,.660),rotation=(90,0,0),segments=24);T.group(cyl,'LIGHTS',head)
            # Physical reflector bezel ring surrounding each lens.
            r=mk.lathe('trim_lamp_ring',[(.083,-.008),(.091,-.008),(.091,.008),(.083,.008),(.083,-.008)],segments=24,location=(sign*x,2.694,.660),rotation=(90,0,0));T.group(r,'CHROME',chrome)
            bm=bmesh.new();bm.from_mesh(r.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(r.data);bm.free()
        T.slab('lamp_parking',(.175,.065,.066),(sign*.805,2.703,.422),amber,'LIGHTS')
    S.frame('grille_frame',1.13,.219,.048,(0,2.680,.651),chrome,T.collections['CHROME'],.011)
    T.slab('grille_backing',(1.108,.028,.200),(0,2.675,.651),rubber,'DETAILS')
    for z in [.568,.603,.638,.673,.708,.743]:
        T.band('grille_horizontal',[(-.548,2.701),(0,2.715),(.548,2.701)],z,.008,.012,chrome,'CHROME')
    for x in [-.40,-.20,0,.20,.40]:T.slab('grille_upright',(.007,.010,.19),(x,2.707,.651),chrome,'CHROME')
    # Thin lower air slot and correctly recessed number plates, no texture assets.
    T.slab('grille_lower',(.96,.070,.055),(0,2.699,.435),rubber,'DETAILS')
    for sign,z in [(1,.31),(-1,.478)]:
        T.slab('plate_mount',(.34,.080,.140),(0,sign*2.690,z),rubber,'DETAILS')
        T.slab('plate_registration',(.315,.010,.128),(0,sign*2.731,z),plate,'DETAILS')
    # Batch same-material fixed fixtures, preserving glass, body and wheel rigs.
    for prefix,name in [('trim_window_surround','trim_window_surrounds'),('trim_shoulder_spear','trim_shoulder_spears'),('trim_door_handle','trim_handles'),('lamp_head','lamp_headlights'),('lamp_tail','lamp_taillights'),('lamp_reverse','lamp_reverse_units'),('grille_horizontal','grille_blades'),('grille_upright','grille_supports'),('trim_lamp_ring','trim_lamp_rings')]:
        S.merge_static([o for o in list(bpy.context.scene.objects) if o.type=='MESH' and o.name.startswith(prefix)],name)
    S.merge_static([o for o in list(T.collections['CHROME'].objects) if not o.name.startswith('bumper_')],'trim_body_chrome')
    S.merge_static([o for o in list(T.collections['DETAILS'].objects) if o.data.materials[0]==rubber],'trim_seals_and_recesses')
    S.merge_static([o for o in list(T.collections['DETAILS'].objects) if o.data.materials[0]==plate],'plate_registration')
    S.merge_static([o for o in list(T.collections['LIGHTS'].objects) if o.data.materials[0]==amber],'lamp_parking')
    body['shoulder_trim_centrelines_m']=json.dumps(trim_paths)

# Portable triangulation and shared body normals keep raw exported body closed.
for obj in [o for o in bpy.context.scene.objects if o.type=='MESH']:
    bm=bmesh.new();bm.from_mesh(obj.data)
    if obj.name.startswith(('trim_rim_whitewall','trim_lamp_ring')):bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
    bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
    for f in obj.data.polygons:f.use_smooth=obj in (body,glazing) or obj.name.startswith(('wheel_','trim_rim','lamp_head'))
    obj['asset_status']='original Impala 16439; visual approval pending'
# Joining slanted rods retains the first rod's local basis. Bake that basis
# without moving vertices: Three r128 otherwise transforms an oversized local
# bounding box and frames a 4 m tall car despite correct world-space geometry.
for obj in [o for o in bpy.context.scene.objects if o.type=='MESH']:
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
S.clean_cut_slivers(body,min_area=1e-9,merge_distance=.00008)
while body.data.uv_layers:body.data.uv_layers.remove(body.data.uv_layers[0])
S.panel_normals(body,side_limit=.93,belt=.98)
# Glass thickness walls must not pull broad pane normals sideways and create
# inflated reflections. Average only the actual pane faces at each vertex.
mesh=glazing.data;adj=[[] for _ in mesh.vertices]
for f in mesh.polygons:
    for vi in f.vertices:adj[vi].append(f)
normals=[]
for loop in mesh.loops:
    fs=adj[loop.vertex_index];large=[f for f in fs if f.area>.00004]
    n=sum((f.normal*f.area for f in large),Vector())
    normals.append(tuple(n.normalized()) if n.length>.000001 else tuple(mesh.vertices[loop.vertex_index].normal))
mesh.normals_split_custom_set(normals)
bpy.context.view_layer.update();S.attach_wheel_fixtures();S.batch_wheel_spokes();S.attach_body_fixtures()
body['construction']='original longitudinal loft, recessed apertures, full inner rear well and lower outer quarter opening'
body['parameters']=json.dumps(P,sort_keys=True)
body['authoritative_source']='experiments/impala1970/model.py + parameters.json'
bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=1
