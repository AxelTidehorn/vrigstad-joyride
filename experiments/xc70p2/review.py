import sys,json,hashlib
from pathlib import Path
import bpy
import render_views
sys.path.insert(0,str(Path(__file__).resolve().parent));from variants import apply
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/vehicle_pipeline'))
from blender_import import body_quality_gate
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
views=[('side',90,0,True),('front_three_quarter',135,18,False),('rear_three_quarter',35,18,False),('front',180,0,True),('rear',0,0,True)]
report={}
# Software Cycles avoids driver-specific EEVEE surface noise; reuse Modeler cameras/light rig.
bpy.context.scene.cycles.samples=16;bpy.context.scene.cycles.use_denoising=False
render_views._eevee_id=lambda:setattr(bpy.context.scene.render,'engine','CYCLES')
for variant in ['civilian','police']:
 apply(variant)
 visible=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
 body_quality_gate(visible)
 render_views.run(str(out/variant),mode='clay',res=1100,color_by='material',views=views,focus=((-1.06,-2.42,0),(1.06,2.42,1.79)))
 # Workbench material colours do not show decals; shaded rendering verifies the UV livery.
 if variant=='police':render_views.run(str(out/'police_decor'),mode='shaded',res=1100,color_by='material',views=views,focus=((-1.06,-2.42,0),(1.06,2.42,1.79)))
 body=bpy.data.objects['body'];report[variant]={'body_sha256':hashlib.sha256(bytes(str([tuple(v.co) for v in body.data.vertices]),'utf8')).hexdigest(),'visible_meshes':len(visible),'triangles':sum(sum(len(f.vertices)-2 for f in o.data.polygons) for o in visible)}
 # Existing exporter takes visible meshes; use temporary variant snapshots for its unchanged CLI.
 bpy.ops.wm.save_as_mainfile(filepath=str(out/(variant+'.blend')))
apply('civilian');bpy.ops.wm.save_as_mainfile(filepath=str(out/'model.blend'))
report['same_body']=report['civilian']['body_sha256']==report['police']['body_sha256'];(out/'variants.json').write_text(json.dumps(report,indent=2))
