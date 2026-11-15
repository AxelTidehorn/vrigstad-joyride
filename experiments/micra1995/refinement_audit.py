"""Measure pane shape independently of render shading, and freeze wheel geometry."""
import sys,json,math,hashlib,re
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector,Matrix

def world(o):
 m=Matrix.LocRotScale(o.location,o.rotation_euler.to_quaternion(),o.scale)
 return world(o.parent)@o.matrix_parent_inverse@m if o.parent else m

def pane_report(o):
 bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();todo=set(bm.verts);panes=[]
 while todo:
  pane={todo.pop()};stack=list(pane)
  while stack:
   for e in stack.pop().link_edges:
    for v in e.verts:
     if v in todo:todo.remove(v);pane.add(v);stack.append(v)
  xyz=np.array([tuple(world(o)@v.co) for v in pane]);c=xyz.mean(axis=0);fs=list({f for v in pane for f in v.link_faces})
  _,eig=np.linalg.eigh(np.cov(xyz.T));n=eig[:,0]
  if np.dot(n,[c[0],c[1],c[2]-.7])<0:n=-n
  broad=[f for f in fs if f.calc_area()>.00004 and np.dot(f.normal,n)>.25]
  angles=[math.degrees(math.acos(float(np.clip(np.dot(f.normal,n),-1,1)))) for f in broad]
  front_xyz=np.array([tuple(v.co) for f in broad for v in f.verts]);dist=(front_xyz-front_xyz.mean(axis=0))@n
  signature=[tuple(sorted(tuple(round(x,6) for x in v.co) for v in f.verts)) for f in fs]
  panes.append({'centre_m':c.tolist(),'vertices':len(pane),'triangles':len(fs),'visible_face_max_angle_from_PCA_deg':max(angles),'visible_sheet_PCA_max_residual_mm':float(np.max(abs(dist))*1000),'visible_sheet_PCA_rms_mm':float(np.sqrt(np.mean(dist*dist))*1000),'duplicate_faces':len(signature)-len(set(signature))})
 bm.free()
 rear=[p for p in panes if abs(p['centre_m'][0])<.1 and p['centre_m'][1]<-.9]
 assert len(panes)==6 and len(rear)==1
 return {'panes':panes,'rear':rear[0]}
current={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
baseline=Path(sys.argv[1]);out=Path(sys.argv[2])
with bpy.data.libraries.load(str(baseline),link=False) as (src,dst):names=tuple(src.objects);dst.objects=list(names)
old={n:o for n,o in zip(names,dst.objects) if o and o.type=='MESH'}
def cloud(o):return sorted(tuple(round(x,6) for x in world(o)@v.co) for v in o.data.vertices)
wheels={n:{'unchanged':cloud(o)==cloud(current[n]),'origin_delta_m':float((world(o).translation-world(current[n]).translation).length)} for n,o in old.items() if n.startswith(('wheel_','trim_rim_'))}
report={'baseline_commit':'9060015f15f6ae27ce96ef5e3c299e6c0e53b1fd','baseline_blend_sha256':hashlib.sha256(baseline.read_bytes()).hexdigest(),'before':pane_report(old['glass_envelope']),'after':pane_report(current['glass_envelope']),'protected_wheels':wheels,'units':'actual mesh metres/mm/degrees; not errors against photographs'}
def materials(objects):
 result={}
 for o in objects.values():
  for m in o.data.materials:
   bs=m.node_tree.nodes.get('Principled BSDF')
   result[re.sub(r'\.\d{3}$','',m.name)]={'colour':list(bs.inputs['Base Color'].default_value),'roughness':float(bs.inputs['Roughness'].default_value),'metallic':float(bs.inputs['Metallic'].default_value)}
 return result
report['materials_unchanged']=materials(old)==materials(current)
report['mesh_names_preserved']=old.keys()==current.keys()
report['ok']=all(x['unchanged'] and x['origin_delta_m']<1e-6 for x in wheels.values()) and report['after']['rear']['duplicate_faces']==0 and report['materials_unchanged'] and report['mesh_names_preserved']
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert report['ok']
