"""Fixed Modeler studio views; same physical framing at every modelling stage."""
import sys,json
from pathlib import Path
import bpy,render_views
out=Path(sys.argv[1]);mode=sys.argv[2] if len(sys.argv)>2 else 'shaded'
views=[('side',90,0,True),('front',180,0,True),('rear',0,0,True),('front_three_quarter',135,20,False),('rear_three_quarter',35,20,False),('high_three_quarter',135,42,True)]
bpy.context.scene.cycles.samples=16;bpy.context.scene.cycles.use_denoising=False
render_views._eevee_id=lambda:setattr(bpy.context.scene.render,'engine','CYCLES')
focus=((-1.15,-2.88,0),(1.15,2.88,1.65))
render_views.run(str(out/'views'),mode=mode,res=1100,color_by='material',views=views,focus=focus)
if mode=='shaded':
    render_views.run(str(out/'details'),mode=mode,res=1200,color_by='material',views=[('front_detail',140,22,True)],focus=((-1.06,1.0,.20),(1.06,2.79,1.03)))
    render_views.run(str(out/'rear_detail'),mode=mode,res=1200,color_by='material',views=[('rear_detail',30,22,True)],focus=((-1.05,-2.79,.20),(1.05,-1.5,1.01)))
(out/'cameras.json').write_text(json.dumps({'focus_m':focus,'views':views,'renderer':'Modeler Workbench clay or Cycles16 matte shaded','front':'+Y','units':'m'},indent=2))
