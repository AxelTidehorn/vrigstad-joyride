"""Original pre-facelift K11 three-door loft; shared authoring/export infrastructure."""
from pathlib import Path
import sys,json,math
import bpy,bmesh,numpy as np
from mathutils import Vector
import modelkit as mk
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools/vehicle_pipeline'))
import authoring as T
import surface_refinement as S
P=json.loads((HERE/'parameters.json').read_text())
for name in ['BODY','GLASS','PLASTIC_RUBBER','LIGHTS','DETAILS','WHEELS']:
 c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);T.collections[name]=c
paint=T.material('Micra configurable body paint',(.22,.49,.40));glass=T.material('smoky blue grey glass',(.075,.12,.14));rubber=T.material('weatherstrip rubber',(.025,.031,.032));tire=T.material('tire charcoal',(.022,.025,.026));rim=T.material('original grey wheel covers',(.39,.42,.41));head=T.material('headlamp ivory',(.65,.72,.69));red=T.material('red tail lenses',(.46,.028,.022));amber=T.material('amber indicators',(.80,.32,.045));plate=T.material('registration ivory',(.70,.72,.65))
for m in [paint,glass,head,red,amber]:m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.65
# Shape-specific sections: rounded hatch, high arched cabin, short drooping nose.
anchors=sorted(set([p[0] for p in P['roof'] if -1.78<=p[0]<=1.78]+[-1.78,1.78]+sum([P[k] for k in ['side_window_front','side_window_rear','windshield_range','backlight_range']],[])))
# An inset must have room on both sides of its boundary: near-duplicate
# stations create folded reveals even when the raw loft is manifold.
ys=sorted(anchors+[round(-1.78+i*3.56/56,7) for i in range(1,56) if min(abs((-1.78+i*3.56/56)-a) for a in anchors)>.028])
verts=[];faces=[];zones=[]
for y in ys:
 top=T.interp(y,P['roof']);w=T.interp(y,P['half_width']);cabin=max(0,min(1,(top-.95)/.40));rw=.83*w*(1-cabin)+P['roof_half_width']*cabin
 belt=min(.880,top-.045);shoulder=min(.85,belt-.05)
 half=[(0,.17),(.65*w,.17),(.86*w,.20),(.96*w,.30),(w,.53),(.997*w,shoulder-.10),(.98*w,shoulder-.025),(.955*w,shoulder),(.93*w,belt),(.88*w,belt+.06*(top-belt)),(rw,top-min(.065,(top-belt)*.5)),(.86*rw,top-.025),(.48*rw,top-.005),(0,top)]
 if y>1.4:
  t=min(1,(y-1.4)/.3)
  half[10]=(.94*w,half[10][1]*(1-t)+(top-.018)*t)
  half[11]=(.82*w,half[11][1]*(1-t)+(top-.008)*t)
 ring=half+[(-x,z) for x,z in half[-2:0:-1]]
 for j,(x,z) in enumerate(ring):
  belt_y=T.interp(y,P['window_belt_shear']) if j in (8,9,len(ring)-9,len(ring)-8) else y
  verts.append((x,belt_y,z))
N=len(ring)
for i in range(len(ys)-1):
 mid=(ys[i]+ys[i+1])/2
 for j in range(N):
  faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
  side=j in (9,N-10);zone=0
  if side and P['side_window_front'][0]<mid<P['side_window_front'][1]:zone=1
  if side and P['side_window_rear'][0]<mid<P['side_window_rear'][1]:zone=2
  if P['windshield_range'][0]<mid<P['windshield_range'][1] and 10<=j<=N-11:zone=3
  if P['backlight_range'][0]<mid<P['backlight_range'][1] and 10<=j<=N-11:zone=4
  zones.append(zone)
faces.extend([tuple(range(N-1,-1,-1)),tuple((len(ys)-1)*N+j for j in range(N))]);zones.extend([0,0])
body=T.group(mk.mesh_from_data('body',verts,faces),'BODY',paint)
for f,z in zip(body.data.polygons,zones):f.material_index=z
bm=bmesh.new();bm.from_mesh(body.data)
for zone in [1,2,3,4]:
 fs=[f for f in bm.faces if f.material_index==zone]
 res=bmesh.ops.inset_region(bm,faces=fs,thickness=.014,depth=-.012,use_even_offset=True,use_boundary=True)
 for f in res['faces']:f.material_index=0
# Round aperture corners in the existing solid frame. These new steel faces
# trim the opening itself; no overlapping rounded glass or cosmetic frame.
corner_verts=[]
for v in bm.verts:
 fs=[f for f in v.link_faces if f.material_index]
 es=[e for e in v.link_edges if any(f.material_index for f in e.link_faces) and any(not f.material_index for f in e.link_faces)]
 if fs and len(es)==2:
  a,b=[(e.other_vert(v).co-v.co).normalized() for e in es]
  if a.angle(b)<math.radians(140):corner_verts.append(v)
if corner_verts:bmesh.ops.bevel(bm,geom=corner_verts,offset=.025,segments=3,affect='VERTICES',clamp_overlap=True,material=0)
bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
gv=[];gf=[]
for f in body.data.polygons:
 if f.material_index:
  start=len(gv);gv.extend(tuple(body.data.vertices[v].co) for v in f.vertices);gf.append(tuple(range(start,len(gv))))
 f.material_index=0
glazing=T.group(mk.mesh_from_data('glass_envelope',gv,gf),'GLASS',glass)
bm=bmesh.new();bm.from_mesh(glazing.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.normal_update();remaining=set(bm.verts);edges=[]
while remaining:
 pane={remaining.pop()};todo=list(pane)
 while todo:
  for e in todo.pop().link_edges:
   for v in e.verts:
    if v in remaining:remaining.remove(v);pane.add(v);todo.append(v)
 xyz=np.array([tuple(v.co) for v in pane]);center=xyz.mean(axis=0);_,eig=np.linalg.eigh(np.cov(xyz.T));normal=Vector(eig[:,0])
 if normal.dot(Vector((center[0],center[1],center[2]-.7)))<0:normal=-normal
 for f in {f for v in pane for f in v.link_faces}:
  if f.normal.dot(normal)<0:f.normal_flip()
 for v in pane:v.co+=normal*.003
 for e in {e for v in pane for e in v.link_edges if len(e.link_faces)==1}:edges.append([tuple(v.co+normal*.002) for v in e.verts])
bm.to_mesh(glazing.data);bm.free();bpy.context.view_layer.objects.active=glazing
mod=glazing.modifiers.new('seated closed glass','SOLIDIFY');mod.thickness=.002;mod.offset=1;bpy.ops.object.modifier_apply(modifier=mod.name)
def cut(target,cutter,label):
 bpy.context.view_layer.objects.active=target;m=target.modifiers.new(label,'BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cutter,do_unlink=True)
def rod(name,a,b,r,mat):
 a,b=Vector(a),Vector(b);o=mk.cylinder(name,r,(b-a).length,location=(a+b)/2,segments=6);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return T.group(o,'DETAILS',mat)
for a,b in edges:rod('trim_glass_seal',a,b,.005,rubber)
for axle,y,track in [('f',P['front_axle_y'],P['front_track']),('r',P['front_axle_y']-P['wheelbase'],P['rear_track'])]:
 for tag,sign in [('l',-1),('r',1)]:
  cut(body,mk.cylinder('_well',.315,.48,location=(sign*.745,y,.276),rotation=(0,90,0),segments=32),'closed wheel well')
  hub=sign*track/2;inside=track/2-.0775;outside=track/2+.0775
  profile=[(0,.49),(.055,.49),(.055,inside),(.22,inside),(.264,inside+.012),(.276,inside+.03),(.276,outside-.03),(.264,outside-.006),(.22,outside),(0,outside)]
  wheel=T.group(mk.lathe('wheel_'+axle+tag,profile,segments=32),'WHEELS',tire);wheel.rotation_euler.y=sign*math.pi/2;wheel.location=(0,y,.276)
  cover=T.group(mk.lathe('trim_rim_'+axle+tag,[(0,outside+.012),(.05,outside+.018),(.145,outside+.012),(.165,outside+.002),(0,outside)],segments=24),'WHEELS',rim);cover.rotation_euler.y=sign*math.pi/2;cover.location=(0,y,.276)
  for o in [wheel,cover]:
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
   for v in o.data.vertices:v.co.x-=hub
   o.location.x=hub
# A small real radius at the outside of each existing well cut. Leave hub
# centres, opening radius and inner tyre clearance unchanged.
bm=bmesh.new();bm.from_mesh(body.data)
arch_edges=[]
for e in bm.edges:
 if all(abs(v.co.x)>.72 and v.co.z>.205 for v in e.verts):
  for yc in [P['front_axle_y'],P['front_axle_y']-P['wheelbase']]:
   if all(abs(math.hypot(v.co.y-yc,v.co.z-.276)-.315)<.001 for v in e.verts):arch_edges.append(e);break
if arch_edges:bmesh.ops.bevel(bm,geom=arch_edges,offset=.004,segments=2,affect='EDGES',clamp_overlap=True)
bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
# Closed wraparound mouldings with restrained radii, following plan corners.
for sign in [-1,1]:
 path=[(-.755,sign*1.51),(-.73,sign*1.69),(-.60,sign*1.78),(-.3,sign*1.8025),(0,sign*1.8075),(.3,sign*1.8025),(.60,sign*1.78),(.73,sign*1.69),(.755,sign*1.51)]
 T.band('bumper_front' if sign>0 else 'bumper_rear',path,.43,.18,.08,rubber,'PLASTIC_RUBBER')
# Pre-facelift lamp outline: curved trapezoid, not round discs or facelift grille.
# Actual pre-facelift grille apertures; backings seat against the cavity walls.
for x in [-.15,.15]:
 for z in [.630,.679]:cut(body,mk.box('_grille_cut',(.24,.20,.032),location=(x,1.80,z)),'recessed grille slot')
from mathutils.bvhtree import BVHTree
bm=bmesh.new();bm.from_mesh(body.data);skin=BVHTree.FromBMesh(bm);bm.free()
def lens(name,outline,mat,front=True):
 # Subdivide the actual outline before sampling the steel: a single nonplanar
 # n-gon chord can disappear beneath a curved nose even if every corner seats.
 bm=bmesh.new();vs=[bm.verts.new((x,0,z)) for x,z in outline];bm.faces.new(vs)
 bmesh.ops.triangulate(bm,faces=list(bm.faces))
 bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=5,use_grid_fill=True)
 bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.verts.ensure_lookup_table();bm.verts.index_update()
 pts=[tuple(v.co) for v in bm.verts];ff=[tuple(v.index for v in f.verts) for f in bm.faces];boundary=[tuple(v.index for v in e.verts) for e in bm.edges if len(e.link_faces)==1];bm.free()
 vv=[]
 for depth in [-.030,.016]:
  for x,_,z in pts:
   hit=skin.ray_cast(Vector((x,3 if front else -3,z)),Vector((0,-1 if front else 1,0)))[0]
   if hit is None:raise ValueError(f'Lamp outside steel: {name} {x,z}')
   vv.append((x,hit.y+(depth if front else -depth),z))
 n=len(pts);faces=[tuple(reversed(f)) for f in ff]+[tuple(v+n for v in f) for f in ff]+[(a,b,b+n,a+n) for a,b in boundary]
 return T.group(mk.mesh_from_data(name,vv,faces),'LIGHTS',mat)

for sign in [-1,1]:
 outline=[(.335,.595),(.337,.720),(.363,.752),(.570,.750),(.665,.720),(.675,.605),(.648,.578),(.365,.578)]
 lens('lamp_headlights',[(sign*x,z-.035) for x,z in outline],head)
 lens('lamp_indicator',[(sign*x,z-.035) for x,z in [(.648,.587),(.697,.602),(.698,.716),(.67,.737)]],amber)
 for z0,z1,m in [(.53,.62,red),(.62,.68,plate),(.68,.79,red),(.79,.85,amber)]:
  lens('lamp_tail',[(sign*x,z) for x,z in [(.58,z0),(.70,z0+.01),(.705,z1-.01),(.59,z1)]],m,False)
 T.slab('trim_handle',(.028,.11,.027),(sign*.785,-.32,.73),rubber)
 # Mirror on short anchored stalk.
 rod('mirror_stalk',(sign*.67,.70,.89),(sign*.83,.70,.94),.018,rubber)
 T.slab('mirror_housing',(.13,.15,.09),(sign*.83,.70,.975),rubber)
 # Controlled short door pressing; a genuine groove in the steel.
 if sign>0:S.press_line(body,1,-.48,.005,.002,lambda p:abs(p.x)>.73 and .29<p.z<.91)
T.slab('grille_lower',(.65,.07,.085),(0,1.815,.43),rubber)
for x in [-.15,.15]:
 for z in [.630,.679]:T.slab('grille_slot',(.235,.024,.028),(x,1.708,z),rubber)
for y in [-1.81,1.81]:T.slab('plate_registration',(.29,.070,.075),(0,y,.54 if y>0 else .64),plate)
# Batch by shared material while preserving the one-body / four-hub contract.
for m in [red,plate,amber]:S.merge_static([o for o in list(bpy.context.scene.objects) if o.type=='MESH' and o.name.startswith('lamp_tail') and o.data.materials[0]==m],'lamp_taillights_'+m.name.split()[0])
for prefix,name in [('trim_glass_seal','trim_window_seals'),('lamp_headlights','lamp_headlights'),('lamp_indicator','lamp_indicators'),('trim_handle','trim_handles'),('mirror_stalk','mirror_stalks'),('mirror_housing','mirror_housings'),('grille_slot','grille_slots'),('plate_registration','plate_registration')]:S.merge_static([o for o in list(bpy.context.scene.objects) if o.type=='MESH' and o.name.startswith(prefix)],name)
for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 S.clean_cut_slivers(o,min_area=1e-10,merge_distance=.000015)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update();normals=[tuple(v.normal) for v in bm.verts];bm.to_mesh(o.data);bm.free();o.data.update()
 for f in o.data.polygons:f.use_smooth=True
 while o.data.uv_layers:o.data.uv_layers.remove(o.data.uv_layers[0])
 # Shared vertex normals prevent hard-edge glTF splits opening raw topology.
 if o==glazing:
  adj=[[] for _ in o.data.vertices]
  for f in o.data.polygons:
   for vi in f.vertices:adj[vi].append(f)
  smooth=[]
  for vi,fs in enumerate(adj):
   broad=[f for f in fs if f.area>.00004]
   n=sum((f.normal*f.area for f in broad),Vector())
   smooth.append(tuple(n.normalized()) if n.length>1e-8 else normals[vi])
  o.data.normals_split_custom_set_from_vertices(smooth)
 else:o.data.normals_split_custom_set_from_vertices(normals)
bpy.context.view_layer.update();S.attach_wheel_fixtures();S.attach_body_fixtures()
body['authoritative_source']='experiments/micra1995/model.py + parameters.json';body['parameters']=json.dumps(P);bpy.context.scene.unit_settings.system='METRIC'
