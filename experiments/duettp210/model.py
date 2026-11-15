"""Original P210 EPA sections; existing Modeler, authoring and strict GLB pipeline."""
from pathlib import Path
import sys,json,math,os
import bpy,bmesh,numpy as np
from mathutils import Vector
import modelkit as mk
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools/vehicle_pipeline'))
import authoring as T
import surface_refinement as S
P=json.loads((HERE/'parameters.json').read_text());STAGE=os.environ.get('DUETT_STAGE','complete')
for name in ['BODY','GLASS','BED','CHROME','RUBBER','LIGHTS','DETAILS','WHEELS']:
 c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c);T.collections[name]=c
paint=T.material('Duett configurable body paint',(.27,.48,.45));glass=T.material('Duett smoky glazing',(.075,.12,.135));rubber=T.material('aged charcoal rubber',(.028,.032,.032));chrome=T.material('restrained satin chrome',(.48,.52,.50));rim=T.material('ivory steel wheels',(.64,.65,.56));bedmat=T.material('darker bed floor',(.14,.25,.23));head=T.material('headlamp ivory',(.76,.77,.66));red=T.material('tail red',(.48,.028,.018));amber=T.material('indicator amber',(.75,.27,.03));orange=T.material('LGF fluorescent orange',(.9,.18,.025));plate=T.material('registration ivory',(.7,.7,.61))
for m,rough,metal in [(paint,.72,.03),(chrome,.45,.65),(rim,.73,.12),(glass,.66,0)]:
 bs=m.node_tree.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
anchors=sorted(set([a for a,b in P['profile']]+[a for a,b in P['fender_profile']]+P['side_window']+P['windshield']+[-.475,-.485]))
ys=sorted(anchors+[round(-2.10+i*4.16/70,6) for i in range(1,70) if min(abs((-2.10+i*4.16/70)-a) for a in anchors)>.025])
verts=[];faces=[];zones=[]
for y in ys:
 top=T.interp(y,P['profile']);ft=T.interp(y,P['fender_profile'])
 cab=-.50<y<.60
 width=T.interp(y,[(-2.1,.76),(-1.7,.83),(-.6,.80),(.1,.80),(.8,.83),(1.5,.83),(1.9,.76),(2.06,.65)])
 if cab:
  belt=1.045;rw=.645
  half=[(0,.23),(.48,.23),(.70,.27),(.76,.43),(width,.64),(.99*width,.88),(.96*width,.99),(.93*width,1.025),(.91*width,belt),(.895*width,belt+.035),(rw,max(belt+.07,top-.07)),(.84*rw,top-.025),(.46*rw,top-.004),(0,top)]
 else:
  # Nonmonotonic upper cross-section forms real full-depth wings alongside
  # the narrow crowned bonnet (and alongside the narrow bed behind the cab).
  hw=min(.50,.67*width) if y>=.60 else .655
  half=[(0,.23),(.48,.23),(.70,.27),(.78,.43),(width,.64),(.99*width,max(.69,ft-.12)),(.94*width,ft),(.84*width,ft+.025),(.72*width,ft-.005),(hw, min(ft-.025,top-.13)),(.97*hw,top-.09),(.80*hw,top-.035),(.43*hw,top-.006),(0,top)]
 if y<=-.50:
  half[8:]=[(.78*width,top-.012),(.72*width,top),(.66*width,top),(.53*width,top),(.30*width,top),(0,top)]
 ring=half+[(-x,z) for x,z in half[-2:0:-1]]
 for j,(x,z) in enumerate(ring):
  yy=y
  if y>1.70:yy-=.085*(abs(x)/.83)**2*min(1,(y-1.7)/.36)
  # Lengthen door glass towards the cowl while the upper edge follows the roof.
  if cab and j in (8,9,len(ring)-9,len(ring)-8):yy=T.interp(y,[(-.50,-.50),(-.32,-.32),(.30,.50),(.60,.60)])
  verts.append((x,yy,z))
N=len(ring)
for i in range(len(ys)-1):
 mid=(ys[i]+ys[i+1])/2
 for j in range(N):
  faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j));zone=0
  if j in (9,N-10) and P['side_window'][0]<mid<P['side_window'][1]:zone=1
  if P['windshield'][0]<mid<P['windshield'][1] and 10<=j<=N-11:zone=2
  if -.485<mid<-.475 and 10<=j<=N-11:zone=3
  zones.append(zone)
faces.extend([tuple(range(N-1,-1,-1)),tuple((len(ys)-1)*N+j for j in range(N))]);zones.extend([0,0])
body=T.group(mk.mesh_from_data('body',verts,faces),'BODY',paint)
# The converted rear wall is deliberately almost vertical. Rear window uses
# a seated lens on that solid wall rather than a rearward sloping wagon roof.
for f,z in zip(body.data.polygons,zones):f.material_index=z if z!=3 else 0
bm=bmesh.new();bm.from_mesh(body.data)
for zone in [1,2]:
 fs=[f for f in bm.faces if f.material_index==zone]
 res=bmesh.ops.inset_region(bm,faces=fs,thickness=.022,depth=-.014,use_even_offset=True,use_boundary=True)
 for f in res['faces']:f.material_index=0
bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
# Extract exactly the triangulated inset surfaces, then offset/solidify a
# controlled 3 mm: no independent floating window geometry.
gv=[];gf=[]
for f in body.data.polygons:
 if f.material_index:
  start=len(gv);gv.extend(tuple(body.data.vertices[v].co) for v in f.vertices);gf.append(tuple(range(start,len(gv))))
 f.material_index=0
windows=T.group(mk.mesh_from_data('glass_envelope',gv,gf),'GLASS',glass)
bm=bmesh.new();bm.from_mesh(windows.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6);bm.normal_update();remaining=set(bm.verts)
while remaining:
 pane={remaining.pop()};todo=list(pane)
 while todo:
  for e in todo.pop().link_edges:
   for v in e.verts:
    if v in remaining:remaining.remove(v);pane.add(v);todo.append(v)
 xyz=np.array([tuple(v.co) for v in pane]);c=xyz.mean(axis=0);_,eig=np.linalg.eigh(np.cov(xyz.T));n=Vector(eig[:,0])
 if n.dot(Vector((c[0],c[1],c[2]-.7)))<0:n=-n
 for f in {f for v in pane for f in v.link_faces}:
  if f.normal.dot(n)<0:f.normal_flip()
 for v in pane:v.co+=n*.003
bm.to_mesh(windows.data);bm.free();
bpy.context.view_layer.objects.active=windows;m=windows.modifiers.new('closed seated panes','SOLIDIFY');m.thickness=.002;m.offset=1;bpy.ops.object.modifier_apply(modifier=m.name)
def cut(cutter,label):
 print('CUT START',label,len(body.data.polygons));bpy.context.view_layer.objects.active=body;m=body.modifiers.new(label,'BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(cutter,do_unlink=True);print('CUT END',label,len(body.data.polygons));assert len(body.data.polygons)>0,label
def rounded_box(name,dims,loc,mat,collection='DETAILS',radius=.025):
 # Extruded rounded X/Z outline: thin glazing and grille backing must not
 # collapse when their corner radius exceeds half their mounting depth.
 w,d,h=dims;r=min(radius,w*.45,h*.45);outline=[]
 for cx,cz,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
  for i in range(5):
   a=math.radians(start+i*90/4);outline.append((cx+r*math.cos(a),cz+r*math.sin(a)))
 n=len(outline);vv=[(x+loc[0],y+loc[1],z+loc[2]) for y in [-d/2,d/2] for x,z in outline]
 ff=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 return T.group(mk.mesh_from_data(name,vv,ff),collection,mat)
# Open-topped cavity cut into the actual connected solid rear, not a capped box.
cut(mk.box('_bed_cavity',(2*P['bed_inner_half_width'],P['bed_front']-P['bed_rear'],2),location=(0,(P['bed_front']+P['bed_rear'])/2,P['bed_floor']+1)),'open bed cavity')
for axle,y in [('f',P['front_axle_y']),('r',P['front_axle_y']-P['wheelbase'])]:
 for tag,sign in [('l',-1),('r',1)]:
  cut(mk.cylinder('_wheel_well',.39,.65,location=(sign*.765,y,P['tire_radius']),rotation=(0,90,0),segments=40),'closed full-depth wheel well')
  hub=sign*P['track']/2;inside=P['track']/2-P['tire_width']/2;outside=P['track']/2+P['tire_width']/2
  profile=[(0,.42),(.06,.42),(.06,inside),(.265,inside),(.317,inside+.012),(.335,inside+.035),(.335,outside-.035),(.317,outside-.008),(.265,outside),(0,outside)]
  for name,pr,mat in [('wheel_'+axle+tag,profile,rubber),('trim_rim_'+axle+tag,[(0,outside+.018),(.08,outside+.027),(.19,outside+.012),(.215,outside),(0,outside)],rim)]:
   o=T.group(mk.lathe(name,pr,segments=32),'WHEELS',mat);o.rotation_euler.y=sign*math.pi/2;o.location=(0,y,.335)
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
   for v in o.data.vertices:v.co.x-=hub
   o.location.x=hub
# Rear glass seats on a true vertical rear wall, with its own volumetric frame.
# Its lower edge is above the bed rail; rounded corners are genuine geometry.
rear_y=-.490
rounded_box('trim_rear_window_frame',(1.01,.030,.37),(0,rear_y,1.365),rubber,'RUBBER',.055)
rounded_box('glass_rear',(.935,.018,.295),(0,rear_y-.018,1.365),glass,'GLASS',.048)
rounded_box('trim_bed_floor',(1.10,1.45,.014),(0,-1.285,P['bed_floor']+.008),bedmat,'BED',.006)
if STAGE!='blockout':
 # Grille is an inset curved surround with individual bars, not a flat image.
 rounded_box('grille_backing',(1.06,.065,.27),(0,2.035,.805),rubber,'CHROME',.085)
 for sign in [-1,1]:
  for zz in [.68,.93]:T.band('grille_surround',[(sign*.50,2.045),(sign*.30,2.07),(0,2.078)],zz,.022,.024,chrome,'CHROME')
  rounded_box('grille_end',(.025,.028,.20),(sign*.515,2.04,.807),chrome,'CHROME',.01)
 for x in [i*.07 for i in range(-6,7)]:rounded_box('grille_bar',(.014,.022,.225),(x,2.078-.06*abs(x),.805),chrome,'CHROME',.005)
 for sign in [-1,1]:
  # Cylinders point forward (+Y) and intersect the wing by their seated backs.
  for name,rad,depth,y,mat in [('trim_head_bezel',.119,.065,1.915,chrome),('lamp_headlights',.102,.045,1.955,head)]:
   o=T.group(mk.cylinder(name,rad,depth,location=(sign*.655,y,.93),rotation=(90,0,0),segments=32),'LIGHTS',mat)
  o=T.group(mk.cylinder('lamp_front_indicator',.040,.030,location=(sign*.69,1.93,.68),rotation=(90,0,0),segments=16),'LIGHTS',amber)
  rounded_box('lamp_tail',(.12,.055,.17),(sign*.735,-2.075,.79),red,'LIGHTS',.032)
  rounded_box('trim_door_handle',(.035,.15,.03),(sign*.780,-.24,.95),chrome,'DETAILS',.012)
  rounded_box('mirror_mount',(.17,.045,.035),(sign*.735,.48,1.125),chrome,'DETAILS',.008)
  rounded_box('mirror_stalk',(.025,.04,.16),(sign*.79,.48,1.19),chrome,'DETAILS',.008)
  rounded_box('mirror_housing',(.035,.13,.15),(sign*.805,.48,1.32),chrome,'DETAILS',.03)
  # Door pressing sits in the existing steel instead of a panel overlay.
  S.press_line(body,1,-.37,.006,.002,lambda p:abs(p.x)>.70 and .47<p.z<1.08)
 T.band('bumper_front',[(-.79,1.92),(-.67,2.08),(-.4,2.12),(0,2.13),(.4,2.12),(.67,2.08),(.79,1.92)],.47,.09,.055,chrome,'CHROME')
 T.band('bumper_rear',[(-.75,-2.10),(-.60,-2.16),(0,-2.18),(.60,-2.16),(.75,-2.10)],.44,.07,.055,chrome,'CHROME')
 rounded_box('plate_registration',(.31,.03,.10),(.30,-2.105,.64),plate,'DETAILS',.01)
 # LGF triangle: red border, orange centre, both closed and mounted to rear gate.
 def triangle(name,w,h,y,z,mat):
  vv=[(-w/2,y,z-h/2),(w/2,y,z-h/2),(0,y,z+h/2),(-w/2,y+.014,z-h/2),(w/2,y+.014,z-h/2),(0,y+.014,z+h/2)]
  return T.group(mk.mesh_from_data(name,vv,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)]),'DETAILS',mat)
 triangle('trim_lgf_border',.37,.32,-2.11,.89,red);triangle('trim_lgf_orange',.285,.235,-2.119,.89,orange)
 for sign in [-1,1]:T.band('trim_wiper',[(sign*.07,.655),(sign*.31,.515)],1.30,.012,.012,rubber,'DETAILS')
# Batch details by material while preserving exact body/hub naming.
for prefix in ['grille_','lamp_','trim_','mirror_']:
 for mat in list(bpy.data.materials):
  objs=[o for o in list(bpy.context.scene.objects) if o.type=='MESH' and o.name.startswith(prefix) and o.data.materials and o.data.materials[0]==mat and not o.name.startswith('trim_rim_')]
  if len(objs)>1:S.merge_static(objs,prefix+mat.name.split()[0].lower())
for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 S.clean_cut_slivers(o,min_area=1e-10,merge_distance=.00001)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update();normals=[tuple(v.normal) for v in bm.verts];bm.to_mesh(o.data);bm.free()
 for f in o.data.polygons:f.use_smooth=True
 while o.data.uv_layers:o.data.uv_layers.remove(o.data.uv_layers[0])
 o.data.normals_split_custom_set_from_vertices(normals)
bpy.context.view_layer.update();S.attach_wheel_fixtures();S.attach_body_fixtures()
body['authoritative_source']='experiments/duettp210/model.py + parameters.json';body['parameters']=json.dumps(P);bpy.context.scene.unit_settings.system='METRIC'
