"""Same fixed Modeler cameras before/after, common physical framing across cars."""
from pathlib import Path
import sys,json,math
import bpy,render_views
from mathutils import Vector
root=Path(__file__).resolve().parents[2];key=sys.argv[1];out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
spec=json.loads(Path(__file__).with_name('vehicles.json').read_text())[key]
if key.startswith('xc70'):
 sys.path.insert(0,str(root/'experiments/xc70p2'));from variants import apply
 apply('police' if key=='xc70police' else 'civilian')
# Existing Modeler studio and cameras; common scene dimensions give identical scale.
focus=((-1.09,-2.60,0),(1.09,2.60,1.80))
mode='shaded' if key=='xc70police' else 'clay'
bpy.context.scene.cycles.samples=16;bpy.context.scene.cycles.use_denoising=False
render_views._eevee_id=lambda:setattr(bpy.context.scene.render,'engine','CYCLES')
render_views.run(str(out/'views'),mode=mode,res=1100,color_by='material',views=[('side',90,0,True),('front_three_quarter',135,20,False),('rear_three_quarter',35,20,False)],focus=focus)
az,el=spec['close_angle'];render_views.run(str(out/'close'),mode=mode,res=1200,color_by='material',views=[('detail',az,el,True)],focus=tuple(tuple(v) for v in spec['close_focus']))
# One genuinely identical light/material/render setup for the fleet comparison.
render_views.run(str(out/'fleet'),mode='shaded',res=1100,color_by='material',views=[('common',135,20,True)],focus=focus)
if key.startswith('xc70'):
 render_views.run(str(out/'windows'),mode=mode,res=1200,color_by='material',views=[('upper_windows',135,42,True)],focus=((-1.02,-2.25,.90),(1.02,.88,1.59)))
 # Diagnostic view through glass from inside; opaque body intentionally hidden.
 hidden={o:o.hide_render for o in bpy.context.scene.objects if o.type=='MESH'}
 for o in hidden:o.hide_render=o.name!='glass_envelope'
 scene=bpy.context.scene;camdata=bpy.data.cameras.new('interior_glass_diagnostic');cam=bpy.data.objects.new('interior_glass_diagnostic',camdata);scene.collection.objects.link(cam)
 for label,position,target in [('inside_rear',(0,-1.15,1.20),(0,-2.3,1.24)),('inside_side',(0,-.3,1.18),(.8,-.45,1.18))]:
  cam.location=position;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='PERSP';camdata.lens=22;scene.camera=cam;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.color_type='MATERIAL';scene.render.resolution_x=1100;scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.render.film_transparent=True;scene.render.filepath=str(out/(label+'.png'));bpy.ops.render.render(write_still=True)
 for o,state in hidden.items():o.hide_render=state
print(json.dumps({'vehicle':key,'fixed_focus':focus,'side_orthographic':True,'mode':mode,'fleet_renderer':'Cycles16, common fixed orthographic camera and light rig'}))
