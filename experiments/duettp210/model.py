"""Original P210 EPA sections; existing Modeler, authoring and strict GLB pipeline."""
from pathlib import Path
import sys,json,math,os
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
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
anchors=sorted(set([a for a,b in P['profile']]+[a for a,b in P['fender_profile']]+P['side_window']+P['windshield']+[-.855,-.845]))
ys=sorted(anchors+[round(P['rear_end']+i*(P['nose_end']-P['rear_end'])/70,6) for i in range(1,70) if min(abs((P['rear_end']+i*(P['nose_end']-P['rear_end'])/70)-a) for a in anchors)>.025])
verts=[];faces=[];zones=[]
for y in ys:
 top=T.interp(y,P['profile']);ft=T.interp(y,P['fender_profile'])
 cab=P['cab_back']<y<P['cab_front']
 width=T.interp(y,[(-2.20,.78),(-1.7,.80),(-.6,.80),(.1,.80),(.7,.83),(1.1,.83),(1.48,.79),(1.72,.79)])
 if cab:
  belt=1.045;rw=.675
  half=[(0,.23),(.48,.23),(.70,.27),(.76,.43),(width,.64),(.99*width,.88),(.96*width,.99),(.93*width,1.025),(.91*width,belt),(.895*width,belt+.035),(rw,max(belt+.055,top-.225)),(.84*rw,top-.105),(.46*rw,top-.025),(0,top)]
 else:
  # Nonmonotonic upper cross-section forms real full-depth wings alongside
  # the narrow crowned bonnet (and alongside the narrow bed behind the cab).
  hw=min(.465,.67*width) if y>=P['cab_front'] else .655
  half=[(0,.23),(.48,.23),(.70,.27),(.78,.43),(width,.64),(.99*width,max(.69,ft-.12)),(.94*width,ft),(.84*width,ft+.045),(.72*width,ft-.005),(hw, min(ft-.025,top-.13)),(.97*hw,top-.09),(.80*hw,top-.035),(.43*hw,top-.006),(0,top)]
 if y<=P['cab_back']:
  # Retained Duett quarter-panel architecture: a broad near-planar wall
  # around an actual wheel opening, not a free-standing hot-rod mudguard.
  width=T.interp(y,[(-2.20,.78),(-1.5,.805),(-.86,.79)])
  top=P['bed_top'];bottom=.66
  half=[(0,bottom),(.46,bottom),(.66,bottom),(.735,.34),(width,.48),(width,.76),(.99*width,top-.07),(.97*width,top-.012),(.94*width,top+.002),(.915*width,top+.004),(.895*width,top),(.86*width,top),(.30,top),(0,top)]
 if cab and .03<=y<=.40:
  drop=T.interp(y,[(.03,.225),(.15,.080),(.40,.060)])
  half[10]=(.675,top-drop);half[11]=(.84*.675,top-drop*.40);half[12]=(.46*.675,top-drop*.08)
 if y>=P['cab_front']:
  bottom=T.interp(y,[(P['cab_front'],.23),(1.30,.23),(1.60,.32),(P['nose_end'],.39)])
  half[:4]=[(0,bottom),(.55*width,bottom),(.82*width,bottom+.035),(.96*width,max(.43,bottom+.06))]
 ring=half+[(-x,z) for x,z in half[-2:0:-1]]
 for j,(x,z) in enumerate(ring):
  yy=y
  if y>1.22:
   t=min(1,(y-1.22)/(P['nose_end']-1.22));t=t*t*(3-2*t)
   setback=T.interp(abs(x),[(0,0),(.42,.025),(.51,.085),(.64,.105),(.72,.145),(.83,.235)])
   # Three-lobed plan plus a rolled lower apron; this replaces the flat cap.
   yy-=t*(setback+.055*max(0,min(1,(.65-z)/.4)))
  # Lengthen door glass towards the cowl while the upper edge follows the roof.
  if cab and j in (8,9,len(ring)-9,len(ring)-8):yy=T.interp(y,[(-.86,-.86),(-.65,-.65),(.03,.32),(.50,.50)])
  verts.append((x,yy,z))
N=len(ring)
for i in range(len(ys)-1):
 mid=(ys[i]+ys[i+1])/2
 for j in range(N):
  faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j));zone=0
  if j in (9,N-10) and P['side_window'][0]<mid<P['side_window'][1]:zone=1
  if P['windshield'][0]<mid<P['windshield'][1] and 10<=j<=N-11:zone=2
  if -.855<mid<-.845 and 10<=j<=N-11:zone=3
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
# Small actual steel/glass aperture radii, solved at shared frame corners.
corner_verts=[]
for v in bm.verts:
 es=[e for e in v.link_edges if any(f.material_index for f in e.link_faces) and any(not f.material_index for f in e.link_faces)]
 if len(es)==2 and any(f.material_index for f in v.link_faces):
  a,b=[(e.other_vert(v).co-v.co).normalized() for e in es]
  if a.angle(b)<math.radians(140):corner_verts.append(v)
if corner_verts:bmesh.ops.bevel(bm,geom=corner_verts,offset=.018,segments=3,affect='VERTICES',clamp_overlap=True,material=0)
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
 bm=bmesh.new();bm.from_mesh(cutter.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cutter.data);bm.free()
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
  if axle=='f':
   cutter=mk.cylinder('_wheel_well',.39,.65,location=(sign*.765,y,P['tire_radius']),rotation=(0,90,0),segments=40)
  else:
   # Original Duett quarter opening: broad flat crown, radiused shoulders
   # and tapered lower ends; no free-standing semicircular fender silhouette.
   outline=[(-.43,-.10),(.43,-.10),(.43,.25),(.405,.43),(.365,.59),(.32,.665),(.26,.705),(.20,.720),(-.20,.720),(-.26,.705),(-.32,.665),(-.365,.59),(-.405,.43),(-.43,.25)]
   n=len(outline);vv=[(sign*.765+x,y+dy,z) for x in [-.325,.325] for dy,z in outline]
   ff=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
   cutter=mk.mesh_from_data('_duett_quarter_opening',vv,ff)
  cut(cutter,'closed full-depth wheel well')
  hub=sign*P['track']/2;inside=P['track']/2-P['tire_width']/2;outside=P['track']/2+P['tire_width']/2
  profile=[(0,.42),(.06,.42),(.06,inside),(.265,inside),(.317,inside+.012),(.335,inside+.035),(.335,outside-.035),(.317,outside-.008),(.265,outside),(0,outside)]
  for name,pr,mat in [('wheel_'+axle+tag,profile,rubber),('trim_rim_'+axle+tag,[(0,outside+.018),(.08,outside+.027),(.19,outside+.012),(.215,outside),(0,outside)],rim)]:
   o=T.group(mk.lathe(name,pr,segments=32),'WHEELS',mat);o.rotation_euler.y=sign*math.pi/2;o.location=(0,y,.335)
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
   for v in o.data.vertices:v.co.x-=hub
   o.location.x=hub
# Real rear axle hangers join the thin load-bed floor to the hub height.
# They are unioned into the existing one-body construction, not floating struts.
for sign in [-1,1]:
 hanger=mk.box('_rear_frame_hanger',(.09,.16,.38),location=(sign*.44,-1.5,.49))
 bpy.context.view_layer.objects.active=body;m=body.modifiers.new('connected rear chassis hanger','BOOLEAN');m.operation='UNION';m.solver='EXACT';m.object=hanger;bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(hanger,do_unlink=True)
# Rear glass seats on a true vertical rear wall, with its own volumetric frame.
# Its lower edge is above the bed rail; rounded corners are genuine geometry.
rear_y=P['rear_window_y']
rounded_box('trim_rear_window_frame',(.86,.014,.285),(0,rear_y,1.43),rubber,'RUBBER',.055)
rounded_box('glass_rear',(.805,.008,.235),(0,rear_y-.010,1.43),glass,'GLASS',.048)
rounded_box('trim_bed_floor',(1.40,P['bed_front']-P['bed_rear']-.07,.014),(0,(P['bed_front']+P['bed_rear'])/2,P['bed_floor']+.008),bedmat,'BED',.006)
if STAGE!='blockout':
 # A smaller rounded opening is actually recessed into the nose steel.
 cutter=rounded_box('_grille_recess',(P['grille_width'],.16,P['grille_height']),(0,1.685,.715),rubber,'CHROME',.105)
 cut(cutter,'rounded grille recess')
 rounded_box('grille_backing',(P['grille_width']-.008,.016,P['grille_height']-.008),(0,1.608,.715),rubber,'CHROME',.10)
 # Rounded ring follows the curved front plate; the back is embedded in steel.
 def rounded_outline(w,h,r):
  pts=[]
  for cx,cz,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
   for i in range(7):
    a=math.radians(start+i*15);pts.append((cx+r*math.cos(a),.715+cz+r*math.sin(a)))
  dense=[]
  for a,b in zip(pts,pts[1:]+pts[:1]):
   for j in range(4):dense.append((a[0]+(b[0]-a[0])*j/4,a[1]+(b[1]-a[1])*j/4))
  return dense
 outer=rounded_outline(.935,.305,.105);inner=rounded_outline(.87,.24,.080);vv=[]
 for back in [False,True]:
  for outline in [outer,inner]:
   for x,z in outline:vv.append((x,1.73-.12*(x/.83)**2-(.055 if back else 0),z))
 n=len(outer);ff=[]
 for i in range(n):
  j=(i+1)%n
  ff.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
 T.group(mk.mesh_from_data('grille_surround',vv,ff),'CHROME',chrome)
 for x in [i*.075 for i in range(-5,6)]:
  h=.212 if abs(x)<.30 else .168
  rounded_box('grille_bar',(.013,.070,h),(x,1.63,.715),chrome,'CHROME',.005)
 for sign in [-1,1]:
  # Recesses and annular sockets replace the former protruding cylinders.
  xc=sign*.640;zc=.775
  bm=bmesh.new();bm.from_mesh(body.data);skin=BVHTree.FromBMesh(bm);bm.free()
  centre_hit=skin.ray_cast(Vector((xc,3,zc)),Vector((0,-1,0)))[0]
  if centre_hit is None:raise ValueError('Missing headlamp seat')
  lamp_y=centre_hit.y
  outer_y=[]
  for i in range(40):
   x=xc+.124*math.cos(i*math.tau/40);z=zc+.124*math.sin(i*math.tau/40);hit=skin.ray_cast(Vector((x,3,z)),Vector((0,-1,0)))[0]
   if hit is None:raise ValueError("Lamp surround outside wing")
   outer_y.append(hit.y+.005)
  cut(mk.cylinder('_lamp_socket',.116,.30,location=(xc,lamp_y-.05,zc),rotation=(90,0,0),segments=40),'recessed headlamp socket')
  vv=[]
  for radius,depth,conform in [(.124,0,True),(.108,lamp_y-.010,False),(.124,-.050,True),(.108,lamp_y-.060,False)]:
   vv.extend((xc+radius*math.cos(i*math.tau/40),(outer_y[i] if conform else -sign*.40*radius*math.cos(i*math.tau/40))+depth,zc+radius*math.sin(i*math.tau/40)) for i in range(40))
  ff=[]
  for i in range(40):
   j=(i+1)%40
   ff.extend([(i,j,40+j,40+i),(80+i,120+i,120+j,80+j),(i,80+i,80+j,j),(40+i,40+j,120+j,120+i)])
  T.group(mk.mesh_from_data('trim_head_bezel',vv,ff),'LIGHTS',chrome)
  T.group(mk.cylinder('lamp_headlights',.106,.013,location=(xc,lamp_y-.018,zc),rotation=(90,0,-sign*22),segments=40),'LIGHTS',head)
  indicator_hit=skin.ray_cast(Vector((sign*.69,3,.585)),Vector((0,-1,0)))[0]
  if indicator_hit is None:raise ValueError('Indicator outside nose')
  o=T.group(mk.cylinder('lamp_front_indicator',.040,.030,location=(sign*.69,indicator_hit.y+.005,.585),rotation=(90,0,0),segments=16),'LIGHTS',amber)
  rounded_box('lamp_tail',(.10,.040,.13),(sign*.69,-2.187,.85),red,'LIGHTS',.032)
  rounded_box('trim_door_handle',(.035,.15,.03),(sign*.780,-.48,.96),chrome,'DETAILS',.012)
  rounded_box('mirror_mount',(.17,.045,.035),(sign*.735,.20,1.025),chrome,'DETAILS',.008)
  rounded_box('mirror_stalk',(.025,.04,.16),(sign*.79,.20,1.105),chrome,'DETAILS',.008)
  rounded_box('mirror_housing',(.035,.13,.15),(sign*.805,.20,1.23),chrome,'DETAILS',.03)
  rounded_box('trim_running_board',(.12,.78,.045),(sign*.78,-.20,.36),rubber,'DETAILS',.02)
  # Door pressing sits in the existing steel instead of a panel overlay.
  S.press_line(body,1,-.70,.006,.002,lambda p:abs(p.x)>.70 and .47<p.z<1.08)
 for sign in [-1,1]:rounded_box('trim_front_bumper_bracket',(.045,.20,.035),(sign*.36,1.68,.47),chrome,'DETAILS',.008)
 T.band('bumper_front',[(-.79,1.52),(-.68,1.68),(-.40,1.74),(0,1.765),(.40,1.74),(.68,1.68),(.79,1.52)],.47,.09,.055,chrome,'CHROME')
 T.group(mk.cylinder('trim_rear_axle',.045,1.12,location=(0,-1.5,.335),rotation=(0,90,0),segments=12),'DETAILS',rubber)
 # Four millimetres of real tailgate relief, with a closed inner backing.
 cut(rounded_box('_tailgate_relief',(1.24,.024,.27),(0,-2.208,.905),rubber,'BED',.035),'tailgate pressing')
 for sign in [-1,1]:
  T.band('trim_bed_rail',[(sign*.750,-2.135),(sign*.750,-.905)],P['bed_top']+.008,.025,.030,bedmat,'BED')
  rounded_box('trim_gate_hinge',(.11,.03,.025),(sign*.47,-2.209,.779),chrome,'DETAILS',.008)
  rounded_box('trim_bumper_mount',(.04,.15,.17),(sign*.47,-2.21,.635),chrome,'DETAILS',.008)
 T.band('bumper_rear',[(-.75,-2.20),(-.60,-2.26),(0,-2.28),(.60,-2.26),(.75,-2.20)],.57,.07,.055,chrome,'CHROME')
 rounded_box('plate_registration',(.25,.025,.085),(.39,-2.206,.81),plate,'DETAILS',.01)
 # LGF triangle: red border, orange centre, both closed and mounted to rear gate.
 def triangle(name,w,h,y,z,mat):
  vv=[(-w/2,y,z-h/2),(w/2,y,z-h/2),(0,y,z+h/2),(-w/2,y+.014,z-h/2),(w/2,y+.014,z-h/2),(0,y+.014,z+h/2)]
  return T.group(mk.mesh_from_data(name,vv,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)]),'DETAILS',mat)
 triangle('trim_lgf_border',.30,.26,-2.21,.90,red);triangle('trim_lgf_orange',.225,.185,-2.219,.90,orange)
 for sign in [-1,1]:
  bm=bmesh.new();bm.from_mesh(body.data);skin=BVHTree.FromBMesh(bm);bm.free();ends=[]
  for x,z in [(sign*.06,1.245),(sign*.30,1.345)]:
   hit=skin.ray_cast(Vector((x,3,z)),Vector((0,-1,0)))[0]
   if hit is None:raise ValueError('Wiper outside windshield')
   ends.append(Vector((x,hit.y+.008,z)))
  a,b=ends;o=T.group(mk.cylinder('trim_wiper',.006,(b-a).length,location=(a+b)/2,segments=6),'DETAILS',rubber);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
# Batch details by material while preserving exact body/hub naming.
for prefix in ['grille_','lamp_','trim_','mirror_']:
 for mat in list(bpy.data.materials):
  objs=[o for o in list(bpy.context.scene.objects) if o.type=='MESH' and o.name.startswith(prefix) and o.data.materials and o.data.materials[0]==mat and not o.name.startswith('trim_rim_')]
  if len(objs)>1:S.merge_static(objs,prefix+mat.name.split()[0].lower())
for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 S.clean_cut_slivers(o,min_area=1e-10,merge_distance=.00001)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.normal_update();normals=[]
 for v in bm.verts:
  caps=[f for f in v.link_faces if abs(f.normal.y)>.90] if o.name.startswith(('lamp_head','glass_rear')) else []
  n=sum((f.normal*f.calc_area() for f in caps),Vector()) if caps else v.normal.copy()
  normals.append(tuple(n.normalized()) if n.length>1e-8 else tuple(v.normal))
 bm.to_mesh(o.data);bm.free()
 for f in o.data.polygons:f.use_smooth=True
 while o.data.uv_layers:o.data.uv_layers.remove(o.data.uv_layers[0])
 o.data.normals_split_custom_set_from_vertices(normals)
bpy.context.view_layer.update();S.attach_wheel_fixtures();S.attach_body_fixtures()
body['authoritative_source']='experiments/duettp210/model.py + parameters.json';body['parameters']=json.dumps(P);bpy.context.scene.unit_settings.system='METRIC'
