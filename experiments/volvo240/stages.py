"""Fixed-stage reviews of the existing generated Blender scene."""
import sys,runpy
from pathlib import Path
import bpy
import render_views
import modelkit as mk
out=Path(sys.argv[1]).resolve()
runpy.run_path(str(Path(__file__).with_name('review.py')),run_name='__main__')
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
from mathutils import Vector
points=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
lo=Vector(tuple(min(p[i] for p in points) for i in range(3)))
hi=Vector(tuple(max(p[i] for p in points) for i in range(3)))
views=[('front',180,0,True),('side',90,0,True),('rear',0,0,True),('three_quarter',135,22,False)]
for stage,groups in [('body',['BODY']),('glass',['BODY','GLASS']),('complete',list(bpy.data.collections.keys()))]:
    for o in objects:o.hide_render=not any(c.name in groups for c in o.users_collection)
    render_views.run(str(out/stage),mode='clay',res=700,color_by='material',views=views,focus=(lo,hi))
for o in objects:o.hide_render=False
