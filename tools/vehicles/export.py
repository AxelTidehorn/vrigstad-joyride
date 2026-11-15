"""Run inside Blender against a pinned editable master, not from a GLB import.
blender -b master.blend --python tools/vehicles/export.py -- output.glb [civilian|police]
XC70 variants.py must be next to the loaded master in its original source tree;
set VEHICLE_VARIANT_SOURCE to that directory when using build/model.blend.
"""
import os
import sys
from pathlib import Path
import bpy

args = sys.argv[sys.argv.index('--') + 1:]
if len(args) > 1:
    sys.path.insert(0, os.environ['VEHICLE_VARIANT_SOURCE'])
    from variants import apply
    apply(args[1])
bpy.context.view_layer.update()
bpy.ops.export_scene.gltf(
    filepath=str(Path(args[0]).resolve()), export_format='GLB',
    use_visible=True, export_apply=True, export_yup=True,
    export_extras=True,
)
