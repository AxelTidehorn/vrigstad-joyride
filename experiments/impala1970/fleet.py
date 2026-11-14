"""Render any of the existing masters with one physical camera/light rig."""
import sys
from pathlib import Path
import bpy,render_views
out=Path(sys.argv[1])
bpy.context.scene.cycles.samples=16;bpy.context.scene.cycles.use_denoising=False
render_views._eevee_id=lambda:setattr(bpy.context.scene.render,'engine','CYCLES')
render_views.run(str(out),mode='shaded',res=1100,color_by='material',views=[('common',135,20,True),('side',90,0,True)],focus=((-1.15,-2.88,0),(1.15,2.88,1.65)))
