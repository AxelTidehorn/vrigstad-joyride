"""Compatibility adapter: Modeler checks/rendering plus existing repository export.

No geometry is authored here. Run via bmod.py --script on a generated .blend.
Pass -- <absolute iteration directory>. Fixed +Y-front views override Modeler's -Y.
"""
import sys
import json
import math
from pathlib import Path
import bpy
import bmesh
from mathutils.bvhtree import BVHTree
import render_views

out=Path(sys.argv[1]).resolve()
out.mkdir(parents=True,exist_ok=True)
views=[('front',180,0,True),('side',90,0,True),('rear',0,0,True),('top',180,90,True),
       ('three_quarter',135,22,False),('three_quarter_left',-135,22,False),
       ('three_quarter_rear',35,22,False),('low_front',160,6,False)]
def clay_regions(scene):
    scene.display.shading.color_type='VERTEX'
# Renderer's fixed cameras and sheet builder are reused unchanged. A documented
# Workbench setting displays the body's single-material vertex color regions.
bpy.app.handlers.render_pre.append(clay_regions)
try:
    render_views.run(str(out),mode='clay',res=700,color_by='material',views=views)
finally:
    bpy.app.handlers.render_pre.remove(clay_regions)
body=bpy.data.objects['body']
bm=bmesh.new();bm.from_mesh(body.data);bm.faces.ensure_lookup_table()
tree=BVHTree.FromBMesh(bm,epsilon=0)
pairs=tree.overlap(tree)
# Adjacent triangles share vertices and are intentionally in contact.
nonadjacent=sorted({tuple(sorted((a,b))) for a,b in pairs if a!=b and
                   not set(bm.faces[a].verts).intersection(bm.faces[b].verts)})
co=[tuple(v.co) for v in bm.verts]
symmetry=max(min(sum((a-b)**2 for a,b in zip((-x,y,z),q)) for q in co)**.5 for x,y,z in co)
report=dict(body_vertices=len(bm.verts),body_triangles=len(bm.faces),
            boundary_or_nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),
            inconsistent_winding_edges=sum(not e.is_contiguous for e in bm.edges),
            degenerate_triangles=sum(f.calc_area()<=1e-10 for f in bm.faces),
            signed_volume_m3=bm.calc_volume(signed=True),
            nonadjacent_bvh_overlap_pairs=len(nonadjacent),
            overlap_pairs=nonadjacent,
            max_mirror_vertex_distance_m=symmetry,
            caveat='BVH screening is not an exhaustive solid/solid self-intersection proof.')
bm.free()
(out/'supplemental_geometry.json').write_text(json.dumps(report,indent=2)+'\n')
print('SUPPLEMENTAL',json.dumps(report))
