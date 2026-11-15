"""Consistent fixed cameras, scale and lighting for both actual model iterations."""
import sys,json
from pathlib import Path
import bpy,render_views
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
bpy.context.scene.cycles.samples=16;bpy.context.scene.cycles.use_denoising=False
render_views._eevee_id=lambda:setattr(bpy.context.scene.render,'engine','CYCLES')
views=[('side',90,0,True),('front',180,0,True),('rear',0,0,True),('front_three_quarter',135,18,False),('rear_three_quarter',35,18,False),('high_three_quarter',135,38,True)]
render_views.run(str(out),mode='shaded',res=1000,color_by='material',views=views,focus=((-1,-2.05,0),(1,2.05,1.53)))
(out/'cameras.json').write_text(json.dumps({'views':views,'focus':[[-1,-2.05,0],[1,2.05,1.53]],'renderer':'Cycles16'},indent=2))
