"""Verify the bounded lamp/text edit against a frozen, previous XC70 master."""
from pathlib import Path
import sys,json,hashlib
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
baseline=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
current={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
with bpy.data.libraries.load(str(baseline),link=False) as (source,target):
 names=tuple(source.objects);target.objects=list(names)
old={n:o for n,o in zip(names,target.objects) if o and o.type=='MESH'}
def shape(o):
 return (tuple(tuple(v.co) for v in o.data.vertices),tuple(tuple(f.vertices) for f in o.data.polygons),tuple(o.location),tuple(o.rotation_euler),tuple(o.scale))
changed=sorted(n for n in current if n in old and shape(current[n])!=shape(old[n]))
removed=sorted(set(old)-set(current));added=sorted(set(current)-set(old))
assert changed==['lamp_tail','lamp_tail.001'],changed
assert removed and all(n.startswith('trim_POLIS') for n in removed),removed
assert not added,added
health={}
for name in ['body','lamp_tail','lamp_tail.001']:
 bm=bmesh.new();bm.from_mesh(current[name].data);bm.normal_update();bm.faces.ensure_lookup_table()
 tree=BVHTree.FromBMesh(bm,epsilon=0)
 pairs={tuple(sorted((a,b))) for a,b in tree.overlap(tree) if a!=b and not set(bm.faces[a].verts)&set(bm.faces[b].verts)}
 h=dict(nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),inconsistent_edges=sum(not e.is_contiguous for e in bm.edges),degenerate_faces=sum(f.calc_area()<1e-10 for f in bm.faces),bvh_self_intersection_candidates=len(pairs),positive_volume=bm.calc_volume(signed=True)>0)
 assert h==dict(nonmanifold_edges=0,inconsistent_edges=0,degenerate_faces=0,bvh_self_intersection_candidates=0,positive_volume=True),(name,h)
 health[name]=h;bm.free()
seating=[];lamp=current['lamp_tail'];body=current['body']
# Each row has a flat rear-facing lens and a deep embedded back face.
for i in range(0,len(lamp.data.vertices),4):
 points=[v.co for v in lamp.data.vertices[i:i+4]]
 low=min(v.x for v in points[:2]);high=max(v.x for v in points[:2]);front=min(v.y for v in points);back=max(v.y for v in points);z=points[0].z
 samples=[]
 for t in [.1,.5,.9]:
  x=low+(high-low)*t
  hit,p,normal,index=body.ray_cast(Vector((x,-3,z)),Vector((0,1,0)))
  assert hit and front<p.y<back,(z,x,front,tuple(p),back)
  samples.append(dict(x_m=x,body_y_m=p.y,exposed_depth_mm=1000*(p.y-front),embedded_depth_mm=1000*(back-p.y)))
 seating.append(dict(z_m=z,width_mm=1000*(high-low),housing_depth_mm=1000*(back-front),samples=samples))
report=dict(baseline_git_commit='c130ae6577e19c1bf39e24c0d82c662f3f4ac973',baseline_blend_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),changed_geometry=changed,removed_text_objects=removed,added_objects=added,unchanged_components=sorted(n for n in current if n not in changed),body_and_glass_exactly_preserved=True,wheels_roof_ride_height_preserved=True,health=health,lamp_row_seating=seating,scope='Flat rear-facing block lamps with tapered width, 240 mm housing depth; intentional body seating. No side wrap or floating lens. Geometry checks do not constitute factory authenticity or human approval.')
(out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
