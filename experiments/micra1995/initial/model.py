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
ys=sorted(set([round(-1.78+i*3.56/56,7) for i in range(57)]+[p[0] for p in P['roof'] if -1.78<=p[0]<=1.78]+[-1.60,-1.40,-1.28,-.50,-.42,.30,.67,.79]))
verts=[];faces=[];zones=[]
for y in ys:
 top=T.interp(y,P['roof']);w=T.interp(y,P['half_width']);cabin=max(0,min(1,(top-.95)/.40));rw=.83*w*(1-cabin)+P['roof_half_width']*cabin
 belt=min(.945,top-.045);shoulder=min(.85,belt-.05)
 half=[(0,.17),(.65*w,.17),(.86*w,.20),(.96*w,.30),(w,.53),(.997*w,shoulder-.10),(.98*w,shoulder-.025),(.955*w,shoulder),(.93*w,belt),(.88*w,belt+.06*(top-belt)),(rw,top-.065),(.86*rw,top-.025),(.48*rw,top-.005),(0,top)]
 ring=half+[(-x,z) for x,z in half[-2:0:-1]]
 for x,z in ring:verts.append((x,y,z))
N=len(ring)
for i in range(len(ys)-1):
 mid=(ys[i]+ys[i+1])/2
 for j in range(N):
  faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
  side=j in (9,N-10);zone=0
  if side and -.40<mid<.67:zone=1
  if side and -1.40<mid<-.50:zone=2
  if .30<mid<.79 and 10<=j<=N-11:zone=3
  if -1.60<mid<-1.28 and 10<=j<=N-11:zone=4
  zones.append(zone)
faces.extend([tuple(range(N-1,-1,-1)),tuple((len(ys)-1)*N+j for j in range(N))]);zones.extend([0,0])
body=T.group(mk.mesh_from_data('body',verts,faces),'BODY',paint)
for f,z in zip(body.data.polygons,zones):f.material_index=z
bm=bmesh.new();bm.from_mesh(body.data)
for zone in [1,2,3,4]:
 fs=[f for f in bm.faces if f.material_index==zone]
 res=bmesh.ops.inset_region(bm,faces=fs,thickness=.014,depth=-.012,use_even_offset=True,use_boundary=True)
 for f in res['faces']:f.material_index=0
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
  profile=[(0,inside),(.22,inside),(.264,inside+.012),(.276,inside+.03),(.276,outside-.03),(.264,outside-.006),(.22,outside),(0,outside)]
  wheel=T.group(mk.lathe('wheel_'+axle+tag,profile,segments=32),'WHEELS',tire);wheel.rotation_euler.y=sign*math.pi/2;wheel.location=(0,y,.276)
  cover=T.group(mk.lathe('trim_rim_'+axle+tag,[(0,outside+.012),(.05,outside+.018),(.145,outside+.012),(.165,outside+.002),(0,outside)],segments=24),'WHEELS',rim);cover.rotation_euler.y=sign*math.pi/2;cover.location=(0,y,.276)
  for o in [wheel,cover]:
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
   for v in o.data.vertices:v.co.x-=hub
   o.location.x=hub
# Closed wraparound mouldings with restrained radii, following plan corners.
for sign in [-1,1]:
 path=[(-.755,sign*1.51),(-.73,sign*1.69),(-.60,sign*1.82),(-.3,sign*1.8075),(0,sign*1.8075),(.3,sign*1.8075),(.60,sign*1.82),(.73,sign*1.69),(.755,sign*1.51)]
 T.band('bumper_front' if sign>0 else 'bumper_rear',path,.43,.18,.08,rubber,'PLASTIC_RUBBER')
# Pre-facelift lamp outline: curved trapezoid, not round discs or facelift grille.
def lens(name,outline,mat,front=True):
 vv=[]
 for depth in [-.018,.014]:
  for x,z in outline:
   y=(1.80-.19*(abs(x)/.79)**2 if front else -1.79+.04*(abs(x)/.79)**2)
   vv.append((x,y+(depth if front else -depth),z))
 n=len(outline);ff=[tuple(range(n-1,-1,-1)),tuple(n+i for i in range(n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 return T.group(mk.mesh_from_data(name,vv,ff),'LIGHTS',mat)
for sign in [-1,1]:
 outline=[(.285,.595),(.305,.744),(.345,.782),(.565,.772),(.670,.735),(.675,.605),(.625,.575),(.34,.575)]
 lens('lamp_headlights',[(sign*x,z) for x,z in outline],head)
 lens('lamp_indicator',[(sign*x,z) for x,z in [(.64,.59),(.685,.61),(.69,.73),(.66,.74)]],amber)
 for z0,z1,m in [(.53,.62,red),(.62,.68,plate),(.68,.79,red),(.79,.85,amber)]:
  lens('lamp_tail',[(sign*x,z) for x,z in [(.61,z0),(.75,z0+.01),(.755,z1-.01),(.62,z1)]],m,False)
 T.slab('trim_handle',(.028,.11,.027),(sign*.785,-.29,.84),rubber)
 # Mirror on short anchored stalk.
 rod('mirror_stalk',(sign*.72,.57,.97),(sign*.83,.58,.98),.018,rubber)
 T.slab('mirror_housing',(.13,.15,.09),(sign*.83,.58,1.015),rubber)
 # Controlled short door pressing; a genuine groove in the steel.
 if sign>0:S.press_line(body,1,-.45,.005,.002,lambda p:abs(p.x)>.73 and .29<p.z<.91)
T.slab('grille_lower',(.65,.035,.085),(0,1.88,.43),rubber)
for x in [-.13,.13]:T.slab('grille_slot',(.20,.024,.032),(x,1.84,.67),rubber)
for y in [-1.81,1.84]:T.slab('plate_registration',(.29,.018,.075),(0,y,.54 if y>0 else .64),plate)
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
 o.data.normals_split_custom_set_from_vertices(normals)
bpy.context.view_layer.update();S.attach_wheel_fixtures();S.attach_body_fixtures()
body['authoritative_source']='experiments/micra1995/model.py + parameters.json';body['parameters']=json.dumps(P);bpy.context.scene.unit_settings.system='METRIC'
