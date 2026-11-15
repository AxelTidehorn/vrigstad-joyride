"""Exercise actual GLB wheel steering/spin and body motion, without game physics."""
from pathlib import Path
import sys,json
import bpy
from mathutils import Vector
path=Path(sys.argv[1]).resolve();output=Path(sys.argv[2]);bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path));bpy.context.view_layer.update()
objects={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'};body=objects['body'];wheel=objects['wheel_fl']
probe_indices={}
for n,o in objects.items():
 if o.parent and o.parent.name.startswith('wheel_'):
  hub=o.parent.matrix_world.translation
  # A lathed hubcap's first vertex can be its centre pole, which should remain
  # stationary during spin. Choose one fixed off-axis probe before any posing.
  probe_indices[n]=max(range(len(o.data.vertices)),key=lambda i:((o.matrix_world@o.data.vertices[i].co-hub).y**2+(o.matrix_world@o.data.vertices[i].co-hub).z**2))
 else:probe_indices[n]=0
def point(o):return o.matrix_world@o.data.vertices[probe_indices[o.name]].co
before={n:point(o).copy() for n,o in objects.items()}
mounted=[o for o in objects.values() if o.parent==body];fixtures=[o for o in objects.values() if o.parent==wheel]
assert mounted and fixtures
hub=wheel.matrix_world.translation.copy();base=body.location.copy();body.location.z+=.015;bpy.context.view_layer.update()
body_motion=all(abs((point(o)-before[o.name]).z-.015)<1e-6 for o in mounted)
wheel_stable=all((point(objects[n])-before[n]).length<1e-7 for n in ['wheel_fl','wheel_fr','wheel_rl','wheel_rr'])
body.location=base;wheel.rotation_mode='XYZ';start=wheel.rotation_euler.copy();wheel.rotation_euler.z+=.20;bpy.context.view_layer.update()
steering=all((point(o)-before[o.name]).length>1e-5 for o in fixtures)
hub_stable=(wheel.matrix_world.translation-hub).length<1e-7
wheel.rotation_euler=start;wheel.rotation_euler.x+=.3;bpy.context.view_layer.update()
spin=all((point(o)-before[o.name]).length>1e-5 for o in fixtures)
report={'ok':body_motion and wheel_stable and steering and spin and hub_stable,'actual_glb':path.name,'body_mounted_meshes':len(mounted),'body_motion_carries_fixtures':body_motion,'wheel_geometry_independent_of_body_bob':wheel_stable,'steering_carries_rim_and_spokes':steering,'wheel_spin_carries_rim_and_spokes':spin,'wheel_hub_position_preserved':hub_stable,'scope':'Transient Blender pose test on actual exported hierarchy. No animation tracks, steering logic or game physics added; no in-game driving claim.'}
report['probe_method']='Fixed vertex chosen at maximum distance from wheel X axis before posing; centre poles cannot produce false spin failures'
output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert report['ok'],report
