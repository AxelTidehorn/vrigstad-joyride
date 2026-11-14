"""Generic fixed-camera staged review, using Blender Modeler's existing renderer."""
import sys,json
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import render_views
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
points=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
lo=tuple(min(p[i] for p in points) for i in range(3));hi=tuple(max(p[i] for p in points) for i in range(3))
views=[('side',90,0,True),('front',180,0,True),('rear',0,0,True),('front_three_quarter',135,22,False),('rear_three_quarter',35,22,False)]
for stage,groups in [('A_body',['BODY']),('B_glass',['BODY','GLASS']),('C_complete',None)]:
 for o in objects:o.hide_render=groups is not None and not any(c.name in groups for c in o.users_collection)
 render_views.run(str(out/stage),mode='clay',res=800,color_by='material',views=views,focus=(lo,hi))
for o in objects:o.hide_render=False
body=bpy.data.objects['body'];bm=bmesh.new();bm.from_mesh(body.data);bm.faces.ensure_lookup_table()
tree=BVHTree.FromBMesh(bm,epsilon=0)
pairs=sorted({tuple(sorted((a,b))) for a,b in tree.overlap(tree) if a!=b and not set(bm.faces[a].verts)&set(bm.faces[b].verts)})
r=dict(boundary_or_nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),inconsistent_winding_edges=sum(not e.is_contiguous for e in bm.edges),degenerate_faces=sum(f.calc_area()<1e-10 for f in bm.faces),signed_volume_m3=bm.calc_volume(signed=True),nonadjacent_overlap_candidates=pairs,collections={c.name:[o.name for o in c.objects] for c in bpy.data.collections},caveat='BVH screen does not prove absence of every inter-component intersection; mounted seating contacts are intentional.')
bm.free();(out/'supplemental.json').write_text(json.dumps(r,indent=2)+'\n')
