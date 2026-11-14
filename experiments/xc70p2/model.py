"""Volvo XC70 P2 MY2005 shared civilian/police master; existing closed loft pipeline."""
import sys,json,math
from pathlib import Path
import bpy,bmesh
import modelkit as mk
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'tools/vehicle_pipeline'))
import authoring as T
P=json.loads((HERE/'parameters.json').read_text())
for name in ['BODY','GLASS','PLASTIC_RUBBER','LIGHTS','DETAILS','WHEELS','POLICE','POLICE_DECALS']:
 c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);T.collections[name]=c
paint=T.material('XC70 configurable silver',(.40,.43,.42));glass=T.material('opaque smoky glazing',(.105,.15,.17))
rubber=T.material('charcoal plastic rubber',(.045,.052,.052));alloy=T.material('satin alloy',(.42,.45,.44))
white=T.material('headlamp ivory',(.76,.77,.65));red=T.material('tail lamp red',(.40,.035,.025));amber=T.material('indicator amber',(.68,.28,.025))
# Existing P2 longitudinal architecture is preserved during detail correction.
profile=[(-2.29,1.05),(-2.26,1.23),(-2.15,1.49),(-2.03,1.515),(-1.80,1.53),(-1.2,1.54),(-.6,1.535),(-.1,1.52),(.20,1.49),(.39,1.38),(.65,1.19),(.82,1.06),(.84,1.06),(.90,1.055),(1.15,1.015),(1.5,.965),(1.90,.90),(2.15,.865),(2.29,.82)]
ys=sorted(set([y for y,z in profile]+[-2.278,-2.17,-2.12,-2.11,-1.28,-1.20,-.31,-.23,.76,2.24,-2.24]))
vertices=[];faces=[];zones=[]
# Thirteen half-section points create a bowed transverse roof rather than Volvo's flat roof.
for y in ys:
 top=T.interp(y,profile)
 top-=.045*max(0,min(1,(top-1.30)/.20))
 w=T.interp(y,[(-2.29,.83),(-2.05,.87),(-1.4,.90),(1.4,.90),(2.10,.85),(2.29,.81)])
 base=min(1.035,top-.08);belt=min(.94,base-.06)
 cabin=max(0,min(1,(top-1.06)/.43));rw=w*.90*(1-cabin)+.735*cabin
 half=[(0,.209),(w*.86,.209),(w*.96,.39),(w,.67),(w*.985,belt),(w*.94,base),
       (rw+(w*.94-rw)*.86,base+(top-.047-base)*.10),
       (rw+(w*.94-rw)*.10,base+(top-.047-base)*.90),
       (rw,top-.047),(rw*.73,top-.015),(rw*.38,top-.004),(0,top)]
 ring=half+[(-x,z) for x,z in half[-2:0:-1]]
 for x,z in ring:
  # Windshield's centre projects forward, making a subtle wraparound bow.
  bow=.025*(1-(abs(x)/max(w,.01))**2) if .39<=y<=.76 else 0
  vertices.append((x,y+bow,z))
N=len(ring)
for i in range(len(ys)-1):
 mid=(ys[i]+ys[i+1])/2
 for j in range(N):
  faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
  side=j in (6,15) and -2.11<mid<.76 and not (-1.28<mid<-1.20 or -.31<mid<-.23)
  screen_front=.20<mid<.76 and 8<=j<=13
  screen_rear=-2.278<mid<-2.12 and 8<=j<=13
  zones.append(2 if screen_front else 3 if screen_rear else int(side))
faces += [tuple(range(N-1,-1,-1)),tuple((len(ys)-1)*N+j for j in range(N))];zones += [0,0]
body=T.group(mk.mesh_from_data('body',vertices,faces),'BODY',paint)
# Store glazing labels before triangulating; both surfaces derive from identical triangles.
for f,zone in zip(body.data.polygons,zones):f.material_index=zone
bm=bmesh.new();bm.from_mesh(body.data)
# Preserve existing side reveals; thinner front/rear reveals are real body geometry.
for zone,margin,depth in [(1,.012,-.009),(2,.008,-.005),(3,.008,-.005)]:
 window_faces=[f for f in bm.faces if f.material_index==zone]
 result=bmesh.ops.inset_region(bm,faces=window_faces,thickness=margin,depth=depth,use_even_offset=True,use_boundary=True)
 for f in result['faces']:f.material_index=0
 if zone==3:
  # Narrow only the recessed opening; retain the roof/top outline and thin upper edge.
  inner_verts={v for f in bm.faces if f.material_index==3 for v in f.verts}
  for v in inner_verts:v.co.x*=.89
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
for v in bm.verts:v.co+=v.normal*.0015
bm.to_mesh(glazing.data);bm.free()
bpy.context.view_layer.objects.active=glazing
mod=glazing.modifiers.new('seated glass','SOLIDIFY');mod.thickness=.003;mod.offset=0;bpy.ops.object.modifier_apply(modifier=mod.name)
for axle,y in [('f',P['front_axle_y']),('r',P['front_axle_y']-P['wheelbase'])]:
 for side,sign in [('l',-1),('r',1)]:
  inner=.65
  cut=mk.cylinder('_well',P['arch_radius'],.9,location=(sign*(inner+.45),y,.345),rotation=(0,90,0),segments=48)
  bpy.context.view_layer.objects.active=body
  mod=body.modifiers.new('recessed wheel well','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)
  center=sign*.8055
  profile_w=[(0,inner-.02),(.12,inner-.02),(.12,.69),(.32,.69),(.345,.70),(.345,.91),(.32,.925),(0,.925)]
  wheel=mk.lathe('wheel_'+axle+side,profile_w,segments=40);wheel.rotation_euler.y=sign*math.pi/2;wheel.location=(0,y,.345)
  T.group(wheel,'WHEELS',rubber);bpy.context.view_layer.objects.active=wheel;wheel.select_set(True);body.select_set(False);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);wheel.select_set(False)
  for v in wheel.data.vertices:v.co.x-=center
  wheel.location.x=center
  rim=mk.cylinder('trim_rim_'+axle+side,.215,.020,location=(center+sign*.129,y,.345),rotation=(0,90,0),segments=24);T.group(rim,'WHEELS',alloy)
  # Restrained six-spoke period alloy, openings in front of the rim face.
  for angle in range(0,360,60):
   a=math.radians(angle)
   o=T.slab('trim_spoke',(.024,.12,.035),(center+sign*.145,y+math.cos(a)*.115,.345+math.sin(a)*.115),rubber,'WHEELS');o.rotation_euler.x=a
# Solid swept cladding following arch curvature, seated into the outer steel shell.
for sign in [-1,1]:
 for yc in [P['front_axle_y'],P['front_axle_y']-P['wheelbase']]:
  vv=[];ff=[]
  for i in range(25):
   a=math.pi*i/24
   for x,r in [(.866,.390),(.93,.390),(.93,.457),(.866,.457)]:vv.append((sign*x,yc+math.cos(a)*r,.345+math.sin(a)*r))
  for i in range(24):
   for j in range(4):ff.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
  ff += [(3,2,1,0),(96,97,98,99)]
  T.group(mk.mesh_from_data('trim_arch',vv,ff),'PLASTIC_RUBBER',rubber)
 T.band('trim_sill',[(sign*.875,y) for y in [-2.02,-1.8,-.9,0,.8,1.8,2.02]],.445,.20,.07,rubber,'PLASTIC_RUBBER')
 T.slab('mirror_housing',(.17,.25,.14),(sign*.925,.72,1.10),rubber,'PLASTIC_RUBBER')
 for y in [.15,-.80]:T.slab('trim_handle',(.03,.17,.035),(sign*.858,y,1.025),alloy)
 # Longitudinal roof rail with two planted feet.
 for y in [-1.85,.1]:T.slab('trim_rail_foot',(.075,.15,.08),(sign*.69,y,1.49),rubber,'PLASTIC_RUBBER')
 T.band('trim_roof_rail',[(sign*.69,-1.92),(sign*.69,-1.80),(sign*.69,-.15),(sign*.69,.10)],1.545,.035,.045,rubber,'PLASTIC_RUBBER')
for label,sgn in [('front',1),('rear',-1)]:
 T.band('bumper_'+label,[(-.87,sgn*1.99),(-.91,sgn*2.18),(-.86,sgn*2.30),(-.72,sgn*2.32),(.72,sgn*2.32),(.86,sgn*2.30),(.91,sgn*2.18),(.87,sgn*1.99)],.535,.27,.093,rubber,'PLASTIC_RUBBER')
 T.slab('trim_skid_'+label,(.98,.055,.105),(0,sgn*2.344,.425),alloy)
 T.slab('plate_'+label,(.44,.024,.10),(0,sgn*2.3545,.615),white)
# Profile-fitted front light lenses and the inset P2 grille.
for sign in [-1,1]:
 vv=[(sign*x,y,z) for x,y,z in [(.34,2.300,.675),(.71,2.300,.675),(.71,2.300,.775),(.34,2.300,.775)]]
 vv+= [(x,y-.055,z) for x,y,z in vv]
 ff=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
 T.group(mk.mesh_from_data('lamp_head',vv,ff),'LIGHTS',white)
 T.slab('lamp_indicator',(.065,.045,.085),(sign*.76,2.290,.718),amber,'LIGHTS')
 for x in [.47,.65]:
  T.group(mk.cylinder('lamp_reflector',.044,.014,location=(sign*x,2.307,.725),rotation=(90,0,0),segments=12),'LIGHTS',alloy)
 # Large rear-facing block housings: broad flat faces, deep embedded volume.
 # There is no surface-wrapped ribbon or side-facing lens extension.
 zs=[.80,.98,1.08,1.18,1.28,1.405];vv=[];ff=[];mi=[]
 for z in zs:
  outer=T.interp(z,[(.80,.84),(.98,.81),(1.08,.79),(1.18,.775),(1.28,.77),(1.405,.735)])
  width=T.interp(z,[(.80,.16),(.98,.15),(1.18,.13),(1.28,.115),(1.405,.085)])
  front=T.interp(z,[(.80,-2.304),(.98,-2.304),(1.18,-2.276),(1.28,-2.232),(1.405,-2.151)])
  for x,y in [(outer-width,front),(outer,front),(outer-.055,front+.24),(outer-width-.055,front+.24)]:vv.append((sign*x,y,z))
 for j in range(len(zs)-1):
  zone=1 if 1.08<=(zs[j]+zs[j+1])/2<1.18 else 0
  for k in range(4):ff.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k));mi.append(zone)
 ff += [(3,2,1,0),tuple((len(zs)-1)*4+i for i in range(4))];mi += [0,0]
 lens=T.group(mk.mesh_from_data('lamp_tail',vv,ff),'LIGHTS',red);lens.data.materials.append(white)
 for face,index in zip(lens.data.polygons,mi):face.material_index=index
T.slab('grille',(.60,.05,.20),(0,2.29,.735),rubber)
for x in [-.24,-.16,-.08,0,.08,.16,.24]:T.slab('grille_slats',(.018,.025,.17),(x,2.321,.735),alloy)
diag=T.slab('grille_diagonal',(.63,.025,.023),(0,2.34,.735),alloy);diag.rotation_euler.y=math.radians(18)
T.slab('badge_volvo',(.075,.03,.07),(0,2.349,.735),rubber)
# Geometry-preserving support cuts place sharp paint boundaries on the shared shell.
# No duplicated faces/material seams: both variants retain one closed body mesh.
# Split paint boundaries only after the window reveals have been constructed.
# Near-coincident source sections would fold a 12 mm window inset back on itself.
bm=bmesh.new();bm.from_mesh(body.data)
for axis,value in [(0,.70),(0,.6995),(0,-.70),(0,-.6995),(1,-1.20),(1,-1.1995),(1,.84),(1,.8395),(2,1.09),(2,1.0905)]:
 normal=[0,0,0];normal[axis]=1;point=[0,0,0];point[axis]=value
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=point,plane_no=normal,dist=1e-7,use_snap_center=False,clear_inner=False,clear_outer=False)
bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
# UV atlas gives police graphics a seated surface, without detached decal panels.
uv=body.data.uv_layers.new(name='variant_livery')
for f in body.data.polygons:
 c=f.center
 for li in f.loop_indices:
  v=body.data.vertices[body.data.loops[li].vertex_index].co
  u=(v.y+2.4)/4.8
  uv.data[li].uv=(u,v.z/1.8 if abs(v.x)>.70 else .98)
# Police equipment has explicit separate names/materials; no animation logic.
blue=T.material('police blue lenses',(.018,.12,.65))
blue.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(.018,.12,.65,1)
blue.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=0
for x in [-.48,.48]:T.slab('trim_police_mount',(.085,.23,.12),(x,-.20,1.54),rubber,'POLICE')
T.slab('trim_lightbar_base',(1.20,.30,.045),(0,-.20,1.615),alloy,'POLICE')
for x in [-.43,0,.43]:
 lamp=T.slab('lamp_blue_module',(.38,.29,.11),(x,-.20,1.69),blue,'POLICE');lamp['animation_channel']='blue_emission_future'
for sign in [-1,1]:
 T.slab('lamp_police_grille',(.06,.04,.045),(sign*.24,2.33,.69),blue,'POLICE')
# Police text is intentionally absent; preserve only blue/white paint and equipment.
for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 for f in o.data.polygons:f.use_smooth=o.name=='body' or o.name.startswith('wheel_')
 o['asset_status']='XC70 P2 MY2005; human visual review pending'
for col in ['POLICE','POLICE_DECALS']:
 for o in T.collections[col].objects:o.hide_render=True;o.hide_viewport=True
body['shared_variants']='civilian and police use this identical single mesh'
bpy.context.scene.unit_settings.system='METRIC'
