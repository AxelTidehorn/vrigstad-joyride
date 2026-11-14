"""Actual Blender GLB reimport with the existing vehicle body gate."""
import sys,json,time
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
from blender_import import body_quality_gate
path=Path(sys.argv[sys.argv.index('--')+1]).resolve()
bpy.ops.wm.read_factory_settings(use_empty=True)
start=time.perf_counter();bpy.ops.import_scene.gltf(filepath=str(path));elapsed=time.perf_counter()-start
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
body_quality_gate(objects)
report={'ok':True,'blender_version':bpy.app.version_string,'mesh_objects':len(objects),'materials':len(bpy.data.materials),'file_bytes':path.stat().st_size,'import_seconds':elapsed,'checks':'Reimported actual GLB and ran unchanged Blender body/wheel gate. This is not a browser FPS benchmark.'}
(path.parent/'reimport.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
