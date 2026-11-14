"""Apply the same source refinement directly to the latest editable Blender file."""
from pathlib import Path
import sys,json
import bpy
here=Path(__file__).resolve().parent;sys.path.insert(0,str(here))
from refine_forms import refine
refine(bpy.data.objects['body'],json.loads((here/'parameters.json').read_text()))
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(Path(sys.argv[1]).resolve()))
