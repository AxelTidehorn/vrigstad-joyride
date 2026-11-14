"""Requested focused views and regression against the approved Blender checkpoint."""
import sys,json
from pathlib import Path
import bpy
import render_views
out=Path(sys.argv[1]).resolve()
render_views.run(str(out/'final_views'),mode='clay',res=1000,color_by='material',views=[('front_three_quarter',135,22,False),('side',90,0,True)])
render_views.run(str(out/'window_closeup'),mode='clay',res=1200,color_by='material',views=[('window_frame',130,12,True)],focus=((- .90,-1.55,.83),(.90,.91,1.44)))
render_views.run(str(out/'front_closeup'),mode='clay',res=1200,color_by='material',views=[('headlight_fit',155,16,True)],focus=((- .86,1.95,.42),(.86,2.34,.82)))
current={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
with bpy.data.libraries.load('/workspace/work/saab-approved.blend',link=False) as (src,dst):
 names=tuple(src.objects);dst.objects=list(names)
unchanged=[];unexpected=[]
for name,old in zip(names,dst.objects):
 if name not in current or old.type!='MESH':continue
 if name in ('body','grille') or name.startswith(('glass','lamp_head','lamp_indicator')):continue
 new=current[name]
 def points(o):return sorted(tuple(round(x,6) for x in v.co) for v in o.data.vertices)
 good=points(old)==points(new) and tuple(old.location)==tuple(new.location) and tuple(old.rotation_euler)==tuple(new.rotation_euler) and tuple(old.scale)==tuple(new.scale)
 (unchanged if good else unexpected).append(name)
report={'unchanged_components':unchanged,'unexpected_changes':unexpected,'pillar_construction':'12 mm inset border and 9 mm recessed window reveals are part of the one closed painted body; existing B gap retained and widened by frames. Glass thickness 6 mm; inner seating nominally 1 mm into backing, outer glass 4 mm below frame.', 'headlamp_top_rear_inner_outer_m':[.700,.652],'headlamp_top_front_inner_outer_m':[.692,.644],'hood_nose_height_m':.72,'note':'The backing under opaque glazing remains closed; no interior or sheet-thickness reconstruction.'}
(out/'final-change-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
