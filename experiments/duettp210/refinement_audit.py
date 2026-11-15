"""Compare the delivered mesh to the actual previous finished Duett, in metres."""
import bpy,bmesh,sys,json,hashlib,re
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
baseline=Path(sys.argv[1]);out=Path(sys.argv[2]);current={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
def world(o):
 m=Matrix.LocRotScale(o.location,o.rotation_euler.to_quaternion(),o.scale)
 return world(o.parent)@o.matrix_parent_inverse@m if o.parent else m
def cloud(o):return sorted(tuple(round(x,6) for x in world(o)@v.co) for v in o.data.vertices)
with bpy.data.libraries.load(str(baseline),link=False) as (src,dst):names=tuple(src.objects);dst.objects=list(names)
old={n:o for n,o in zip(names,dst.objects) if o and o.type=='MESH'}
wheel_names=[n for n in old if n.startswith(('wheel_','trim_rim_'))]
protected={n:{'geometry_identical':cloud(old[n])==cloud(current[n]),'origin_delta_m':(world(old[n]).translation-world(current[n]).translation).length} for n in wheel_names}
def surface(o):
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.transform(bm,matrix=world(o),verts=list(bm.verts));t=BVHTree.FromBMesh(bm);bm.free();return t
def measurements(objects):
 body=objects['body'];tree=surface(body);pts=cloud(body)
 hood=[]
 for y in [.78,1.,1.3,1.6,1.83,2.]:
  p=tree.ray_cast(Vector((0,y,3)),Vector((0,0,-1)))[0];hood.append({'y_m':y,'height_m':None if p is None else p.z})
 return {'body_bounds_m':{'min':[min(p[i] for p in pts) for i in range(3)],'max':[max(p[i] for p in pts) for i in range(3)]},'hood_centre_samples':hood,'body_triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'parameters':json.loads(body['parameters'])}
def materials(objects):
 result={}
 for o in objects.values():
  for m in o.data.materials:
   b=m.node_tree.nodes.get('Principled BSDF');result[re.sub(r'\.\d{3}$','',m.name)]={'colour':list(b.inputs['Base Color'].default_value),'roughness':float(b.inputs['Roughness'].default_value),'metallic':float(b.inputs['Metallic'].default_value)}
 return result
report={'materials_unchanged':materials(old)==materials(current),'baseline_commit':'f6aaa2d','baseline_blend_sha256':hashlib.sha256(baseline.read_bytes()).hexdigest(),'before':measurements(old),'after':measurements(current),'protected_wheels':protected,'units':'actual Blender mesh metres, not error against photographs','ok':all(p['geometry_identical'] and p['origin_delta_m']<1e-6 for p in protected.values())}
report['ok']=report['ok'] and report['materials_unchanged']
out.parent.mkdir(exist_ok=True,parents=True);out.write_text(json.dumps(report,indent=2)+'\n');assert report['ok'];print(json.dumps({'ok':True,'protected_wheels':len(protected)}))
