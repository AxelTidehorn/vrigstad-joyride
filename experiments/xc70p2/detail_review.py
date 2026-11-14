"""Additional fixed-camera close-ups for this bounded glass/lamp correction."""
import sys
from pathlib import Path
import bpy
import render_views
sys.path.insert(0,str(Path(__file__).resolve().parent));from variants import apply
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
for variant in ['civilian','police']:
 apply(variant)
 render_views.run(str(out/variant/'glass_front'),mode='clay',color_by='material',res=1200,views=[('windscreen',135,13,True)],focus=((- .9,.18,1.02),(.9,.86,1.52)))
 render_views.run(str(out/variant/'tail_fit'),mode='clay',color_by='material',res=1200,views=[('tailglass_lamps',30,12,True)],focus=((- .90,-2.34,.82),(.90,-1.94,1.52)))
