"""Measure actual exposed glazing/body clearance and lamp/glass intersections."""
import sys,json
from pathlib import Path
import bpy,bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
body=bpy.data.objects['body'];glass=bpy.data.objects['glass_envelope'];dep=bpy.context.evaluated_depsgraph_get();tree=BVHTree.FromObject(body,dep,epsilon=0)
# Use the outer skin normal relative to the car, testing face interiors as well
# as centroids. Thin shell back faces are deliberately excluded from this sample.
mesh=glass.data;mesh.calc_loop_triangles()
bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table();remaining=set(bm.verts);pane_normals={}
while remaining:
 vs={remaining.pop()};todo=list(vs)
 while todo:
  v=todo.pop()
  for e in v.link_edges:
   other=e.other_vert(v)
   if other in remaining:remaining.remove(other);vs.add(other);todo.append(other)
 points=np.array([tuple(v.co) for v in vs]);center=points.mean(axis=0);_,eigenvectors=np.linalg.eigh(np.cov(points.T));normal=Vector(eigenvectors[:,0]);radial=Vector((center[0],center[1],center[2]-.7))
 if normal.dot(radial)<0:normal=-normal
 for v in vs:pane_normals[v.index]=normal
bm.free();samples=[];back_samples=[]
for face in mesh.polygons:
 c=face.center;n=pane_normals[face.vertices[0]]
 facing=face.normal.dot(n)
 if abs(facing)<=.75:continue
 co=[mesh.vertices[i].co for i in face.vertices]
 if len(co)!=3:continue
 for weights in [(1/3,1/3,1/3),(.6,.2,.2),(.2,.6,.2),(.2,.2,.6)]:
  p=sum((v*w for v,w in zip(co,weights)),Vector());hit,normal,index,distance=tree.ray_cast(p+n*.1,-n,.3)
  if hit is not None:(samples if facing>0 else back_samples).append({'glass_face':face.index,'point':list(p),'body_clearance_mm':1000*(distance-.1)})
# Coincidence is reported separately; this is not a silent tolerance pass.
negative=[s for s in samples if s['body_clearance_mm']<-.05]
near=[s for s in samples if s['body_clearance_mm']<=.05]
gtree=BVHTree.FromObject(glass,dep,epsilon=0)
pairs={o.name:len(gtree.overlap(BVHTree.FromObject(o,dep,epsilon=0))) for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('lamp_tail')}
report={'back_surface_samples':len(back_samples),'minimum_backing_clearance_mm':min((s['body_clearance_mm'] for s in back_samples),default=None),'back_surface_coincident_or_occluded_samples':sum(s['body_clearance_mm']<=.05 for s in back_samples),'outer_glass_samples':len(samples),'glass_occluded_by_body_samples':len(negative),'coincident_or_occluded_samples':len(near),'minimum_clearance_mm':min((s['body_clearance_mm'] for s in samples),default=None),'lamp_glass_intersection_candidates':pairs,'worst_samples':sorted(samples,key=lambda s:s['body_clearance_mm'])[:12],'scope':'Outer faces selected by each connected pane PCA normal (dot > .75), excluding shell side walls; triangle-interior rays. Intended glass backing remains a closed body, not an interior reconstruction. BVH intersections are candidates.'}
# Check police equipment in world coordinates, even when hidden in the master.
for o in bpy.data.collections['POLICE'].objects:o.hide_viewport=False
bpy.context.view_layer.update()
def world_tree(o):return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(f.vertices) for f in o.data.polygons],epsilon=0)
world_glass=world_tree(glass)
report['police_equipment_glass_intersection_candidates']={o.name:len(world_glass.overlap(world_tree(o))) for o in bpy.data.collections['POLICE'].objects if o.type=='MESH'}
Path(sys.argv[1]).parent.mkdir(parents=True,exist_ok=True)
Path(sys.argv[1]).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
