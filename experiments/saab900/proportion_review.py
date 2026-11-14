"""Fixed before/after views through the existing Blender Modeler renderer."""
import sys
from pathlib import Path
import render_views
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
focus=((- .9,-2.35,0),(.9,2.35,1.5))
render_views.run(str(out/'views'),mode='clay',res=1200,color_by='material',views=[('side',90,0,True),('front_three_quarter',135,22,False),('rear_three_quarter',35,22,False)],focus=focus)
render_views.run(str(out/'cabin'),mode='clay',res=1200,color_by='material',views=[('cabin',130,15,True)],focus=((- .87,-1.65,.82),(.87,1.05,1.45)))
