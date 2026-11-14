"""Read-only inventory of existing Blender authoring masters."""
import sys,json,hashlib
from pathlib import Path
import bpy,bmesh
out=Path(sys.argv[1]);out.parent.mkdir(parents=True,exist_ok=True)
def bounds(points):return [[min(p[i] for p in points),max(p[i] for p in points)] for i in range(3)]
report={'objects':{},'collections':[c.name for c in bpy.data.collections]}
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 mesh=o.data;bm=bmesh.new();bm.from_mesh(mesh);bm.normal_update()
 remaining=set(bm.verts);islands=[]
 while remaining:
  verts={remaining.pop()};todo=list(verts)
  while todo:
   v=todo.pop()
   for e in v.link_edges:
    other=e.other_vert(v)
    if other in remaining:remaining.remove(other);verts.add(other);todo.append(other)
  islands.append({'vertices':len(verts),'bounds_m':bounds([tuple(v.co) for v in verts])})
 co=[tuple(v.co) for v in mesh.vertices]
 report['objects'][o.name]={'vertices':len(co),'triangles':sum(len(f.vertices)-2 for f in mesh.polygons),'bounds_m':bounds(co),'location':list(o.location),'sha256':hashlib.sha256(json.dumps(co).encode()).hexdigest(),'materials':[m.name if m else None for m in mesh.materials],'islands':islands,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-10 for f in bm.faces)}
 bm.free()
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report['objects'][k] for k in ['body','glass_envelope']}))
