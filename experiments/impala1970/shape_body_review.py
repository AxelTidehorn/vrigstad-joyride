"""Steel and tyre views through the existing fixed Modeler renderer."""
from pathlib import Path
import sys,bpy,render_views
for o in bpy.context.scene.objects:
    if o.type=='MESH':o.hide_render=o.name!='body' and not o.name.startswith('wheel_')
render_views.run(sys.argv[1],mode='clay',res=1100,color_by='material',views=[('side',90,0,True),('front',180,0,True),('rear',0,0,True),('front_three_quarter',135,20,False)],focus=((-1.15,-2.88,0),(1.15,2.88,1.65)))
