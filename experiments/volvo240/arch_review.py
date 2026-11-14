"""Fixed framing for before/after review, independent of changing arch geometry."""
from pathlib import Path
import sys
import bpy,render_views
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
focus=((- .93,-2.43,0),(.93,2.43,1.44))
render_views.run(str(out),mode='clay',res=1100,color_by='material',views=[('side',90,0,True),('three_quarter',135,22,False),('three_quarter_rear',35,22,False)],focus=focus)
close=((.50,.94,.24),(.89,1.90,.86))
render_views.run(str(out/'arch'),mode='clay',res=1100,color_by='material',views=[('wheel_arch',112,12,True)],focus=close)
for o in bpy.context.scene.objects:
 if o.type=='MESH':o.hide_render=o.name!='body'
render_views.run(str(out/'arch_body'),mode='clay',res=1100,color_by='material',views=[('wheel_arch',112,12,True)],focus=close)
for o in bpy.context.scene.objects:
 if o.type=='MESH':o.hide_render=False
