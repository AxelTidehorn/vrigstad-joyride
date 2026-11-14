"""Saab 900 Classic Turbo 16, three-door; independent Saab profiles, existing pipeline."""
import sys,json,math
from pathlib import Path
import bpy,bmesh
import modelkit as mk
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'tools/vehicle_pipeline'))
import authoring as T
P=json.loads((HERE/'parameters.json').read_text())
for name in ['BODY','GLASS','PLASTIC_RUBBER','LIGHTS','DETAILS','WHEELS']:
 c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);T.collections[name]=c
paint=T.material('Saab warm silver',(.40,.43,.42));glass=T.material('opaque smoky glazing',(.105,.15,.17))
rubber=T.material('charcoal plastic rubber',(.045,.052,.052));alloy=T.material('satin alloy',(.42,.45,.44))
white=T.material('headlamp ivory',(.76,.77,.65));red=T.material('tail lamp red',(.40,.035,.025));amber=T.material('indicator amber',(.68,.28,.025))
# Own Saab longitudinal architecture: low wedge nose, short bowed roof, long hatch.
profile=[(-2.24,.78),(-2.10,.86),(-1.94,.94),(-1.70,1.05),(-1.42,1.18),(-1.10,1.33),(-.95,1.405),(-.75,1.416),(-.35,1.42),(.10,1.42),(.32,1.412),(.48,1.385),(.64,1.265),(.80,1.14),(.90,1.055),(.93,1.02),(.95,1.01),(1.00,1.01),(1.02,1.006),(1.30,.910),(1.75,.810),(2.10,.75),(2.24,.72)]
ys=sorted(set([y for y,z in profile]+[-.43,-.37,.86,-1.28,-1.18,2.18,-2.18]))
vertices=[];faces=[];zones=[]
# Thirteen half-section points create a bowed transverse roof rather than Volvo's flat roof.
for y in ys:
 top=T.interp(y,profile)
 w=T.interp(y,[(-2.24,.74),(-1.8,.82),(-1.25,.845),(1.30,.845),(2.05,.79),(2.24,.72)])
 base=min(.94,top-.095);belt=min(.81,base-.07)
 # Keep side glazing on a controlled longitudinal plane instead of wrapping with roof height.
 rw=min(w*.94,T.interp(y,[(-2.24,.68),(-1.94,.70),(-1.42,.66),(-.95,.66),(.48,.66),(.93,.76),(1.30,.77),(2.24,.66)]))
 half=[(0,.235),(w*.86,.235),(w*.96,.32),(w,.56),(w*.985,belt),(w*.94,base),
       (rw+(w*.94-rw)*.86,base+(top-.025-base)*.04),
       (rw+(w*.94-rw)*.10,base+(top-.025-base)*.90),
       (rw,top-.025),(rw*.73,top-.009),(rw*.38,top-.003),(0,top)]
 # Door and quarter glass share one plane instead of a height-driven wrap.
 if -1.28<=y<=.86:
  for index in [6,7]:
   _,z=half[index];half[index]=(.78-(z-.96)*.29,z)
 ring=half+[(-x,z) for x,z in half[-2:0:-1]]
 for x,z in ring:
  # Windshield's centre projects forward, making a subtle wraparound bow.
  bow_weight=1.0 if y<=.86 else max(0.,(.95-y)/.09)
  bow=.025*(1-(abs(x)/max(w,.01))**2)*bow_weight if .48<=y<=.95 else 0
  vertices.append((x,y+bow,z))
N=len(ring)
for i in range(len(ys)-1):
 mid=(ys[i]+ys[i+1])/2
 for j in range(N):
  faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
  side=j in (6,15) and -1.28<mid<.86 and not -.43<mid<-.37
  screen=(.48<mid<.90 or -1.94<mid<-.95) and 8<=j<=13
  zones.append(int(side or screen))
faces += [tuple(range(N-1,-1,-1)),tuple((len(ys)-1)*N+j for j in range(N))];zones += [0,0]
body=T.group(mk.mesh_from_data('body',vertices,faces),'BODY',paint)
# Store glazing labels before triangulating; both surfaces derive from identical triangles.
for f,zone in zip(body.data.polygons,zones):f.material_index=zone
bm=bmesh.new();bm.from_mesh(body.data)
window_faces=[f for f in bm.faces if f.material_index==1]
# Inset the contiguous window regions, leaving painted, volumetric reveal frames
# in the original connected body. No separate pillar overlays or black disguises.
result=bmesh.ops.inset_region(bm,faces=window_faces,thickness=.012,depth=-.009,use_even_offset=True,use_boundary=True)
for f in result['faces']:f.material_index=0
bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
gv=[];gf=[]
for f in body.data.polygons:
 zone=f.material_index;f.material_index=0
 if zone:
  start=len(gv)
  for vi in f.vertices:
   p=body.data.vertices[vi].co;gv.append(tuple(p))
  gf.append(tuple(range(start,len(gv))))
glazing=T.group(mk.mesh_from_data('glass_envelope',gv,gf),'GLASS',glass)
bm=bmesh.new();bm.from_mesh(glazing.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bm.normal_update()
from mathutils import Vector
for f in bm.faces:
    c=f.calc_center_median()
    if f.normal.dot(Vector((c.x,c.y,c.z-.6)))<0:f.normal_flip()
bm.normal_update()
for v in bm.verts:v.co+=v.normal*.002
bm.to_mesh(glazing.data);bm.free()
bpy.context.view_layer.objects.active=glazing
mod=glazing.modifiers.new('seated glass','SOLIDIFY');mod.thickness=.006;mod.offset=0;bpy.ops.object.modifier_apply(modifier=mod.name)
for axle,y in [('f',P['front_axle_y']),('r',P['front_axle_y']-P['wheelbase'])]:
 for side,sign in [('l',-1),('r',1)]:
  inner=.565
  cut=mk.cylinder('_well',P['arch_radius'],.9,location=(sign*(inner+.45),y,.305),rotation=(0,90,0),segments=48)
  bpy.context.view_layer.objects.active=body
  mod=body.modifiers.new('recessed wheel well','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
  center=sign*.715
  profile_w=[(0,inner-.02),(.09,inner-.02),(.09,.6175),(.28,.6175),(.305,.638),(.305,.792),(.28,.8125),(0,.8125)]
  wheel=mk.lathe('wheel_'+axle+side,profile_w,segments=40);wheel.rotation_euler.y=sign*math.pi/2;wheel.location=(0,y,.305)
  T.group(wheel,'WHEELS',rubber);bpy.context.view_layer.objects.active=wheel;wheel.select_set(True);body.select_set(False);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);wheel.select_set(False)
  for v in wheel.data.vertices:v.co.x-=center
  wheel.location.x=center
  rim=mk.cylinder('trim_rim_'+axle+side,.206,.020,location=(center+sign*.091,y,.305),rotation=(0,90,0),segments=24);T.group(rim,'WHEELS',alloy)
  # Three dark inset spoke fields suggest the Saab three-spoke alloy without fine tessellation.
  for angle in [0,120,240]:
   a=math.radians(angle)
   o=T.slab('trim_spoke',(.022,.12,.055),(center+sign*.104,y+math.cos(a)*.095,.305+math.sin(a)*.095),rubber,'WHEELS');o.rotation_euler.x=a
# Full-length integrated bumper sweep: a tapered centre and curved returning corners.
for name,sgn in [('front',1),('rear',-1)]:
 path=[(-.80,sgn*1.93),(-.80,sgn*2.15),(-.75,sgn*2.25),(-.64,sgn*2.29),(.64,sgn*2.29),(.75,sgn*2.25),(.80,sgn*2.15),(.80,sgn*1.93)]
 T.band('bumper_'+name,path,.435,.145,.10,rubber,'PLASTIC_RUBBER')
# Seat side moldings on the actual Saab section at their own height.
def skin_x(y,z):
    samples=[]
    for i,yy in enumerate(ys):
        half=vertices[i*N:i*N+12]
        found=half[-1][0]
        for a,b in zip(half,half[1:]):
            if a[2]<=z<=b[2] and b[2]>a[2]:
                found=a[0]+(b[0]-a[0])*(z-a[2])/(b[2]-a[2]);break
        samples.append((yy,found))
    return T.interp(y,samples)
for sign in [-1,1]:
    path=[(sign*(skin_x(y,.74)+.003),y) for y in [-1.93,-1.70,-1.3,-.65,0,.73,.95,1.3,1.75,1.99]]
    T.band('trim_side',path,.74,.012,.009,rubber,'PLASTIC_RUBBER')
    T.slab('mirror_housing',(.13,.23,.105),(sign*.81,.85,1.04),rubber,'PLASTIC_RUBBER')
    T.slab('trim_handle',(.028,.15,.035),(sign*.805,-.24,.91),rubber,'DETAILS')
    # A fitted six-face lamp wedge: top slopes down with the hood toward the nose.
    # Rear top .704 at y=2.205; front top .685 at y=2.255. Body hood at nose .72.
    lx=sign*.47;w=.35
    lv=[(lx+dx,y,z) for dx,y,z in [(-w/2,2.205,.555),(w/2,2.205,.555),(w/2,2.255,.555),(-w/2,2.255,.555),(-w/2,2.205,.704),(w/2,2.205,.704),(w/2,2.255,.685),(-w/2,2.255,.685)]]
    # Slope the top across the width as well as in depth to stay below the tapered hood.
    lv=[(x,y, (.692 if abs(x)<.47 else .644)+(.008 if y<2.23 else 0)) if i>=4 else (x,y,z) for i,(x,y,z) in enumerate(lv)]
    lf=[(3,2,1,0),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
    T.group(mk.mesh_from_data('lamp_head',lv,lf),'LIGHTS',white)
    T.slab('lamp_indicator',(.11,.06,.10),(sign*.748,2.195,.605),amber,'LIGHTS')
    T.slab('lamp_tail',(.285,.045,.19),(sign*.59,-2.235,.655),red,'LIGHTS')
    T.slab('lamp_tail_indicator',(.10,.05,.09),(sign*.70,-2.225,.71),amber,'LIGHTS')
T.slab('grille',(.52,.045,.15),(0,2.24,.625),rubber)
for z in [.595,.635,.675]:T.slab('grille_bar',(.49,.018,.014),(0,2.266,z),alloy)
T.slab('plate_rear',(.35,.03,.095),(0,-2.255,.62),rubber)
# Fitted narrow rubber spoiler across the long hatch; part of Turbo identity.
T.band('trim_hatch_spoiler',[(-.71,-1.88),(0,-1.94),(.71,-1.88)],.975,.055,.075,rubber,'PLASTIC_RUBBER')
# Subtle single long-door shut lines, seated against the existing shell.
for sign in [-1,1]:
 T.band('trim_door_seam',[(sign*.84,-.40),(sign*.84,-.40+.001)],.55,.29,.004,rubber,'DETAILS')
for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 for f in o.data.polygons:f.use_smooth=o.name=='body' or o.name.startswith('wheel_')
 # Close cowl support sections preserve the physical slope break without faceting.
 o['review_status']='Saab 900 T16 profile refinement; reference uncertainty documented; human approval pending'
body['construction']='Saab-specific bowed roof and continuous hatch loft; closed recessed wheel wells'
body['parameters']=json.dumps(P)
body['longitudinal_profile']=json.dumps(profile)
body['cowl_construction']='Short cowl y .95-1.00; defined hood crease; windshield bow tapers to zero before cowl, no bevel/subdivision'
bpy.context.scene.unit_settings.system='METRIC'

ink=T.material('emblem blue grey',(.035,.065,.09))
emblem=mk.cylinder('badge_front',.023,.008,location=(0,2.263,.67),rotation=(90,0,0),segments=12);T.group(emblem,'DETAILS',ink)

# Closed glazing islands must retain outward winding after thin-shell creation.
bm=bmesh.new();bm.from_mesh(glazing.data);bm.normal_update()
remaining=set(bm.faces)
while remaining:
    faces={remaining.pop()};todo=list(faces)
    while todo:
        face=todo.pop()
        for e in face.edges:
            for f in e.link_faces:
                if f in remaining:remaining.remove(f);faces.add(f);todo.append(f)
    volume=sum(f.verts[0].co.dot(f.verts[i].co.cross(f.verts[i+1].co))/6 for f in faces for i in range(1,len(f.verts)-1))
    if volume<0:
        for f in faces:f.normal_flip()
bm.to_mesh(glazing.data);bm.free()
