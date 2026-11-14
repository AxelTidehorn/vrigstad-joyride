"""Check source regeneration against the directly refined editable master."""
from pathlib import Path
import sys,json,bpy
current={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
with bpy.data.libraries.load(str(Path(sys.argv[1]).resolve()),link=False) as (src,dst):
 names=tuple(src.objects);dst.objects=list(names)
regenerated={n:o for n,o in zip(names,dst.objects) if o and o.type=='MESH'}
def shape(o):return sorted(tuple(round(x,6) for x in v.co) for v in o.data.vertices),tuple(o.location),tuple(o.rotation_euler),tuple(o.scale)
assert set(current)==set(regenerated)
diff=[n for n in current if shape(current[n])!=shape(regenerated[n])]
report=dict(source_reproduces_all_mesh_positions=not diff,differences=diff,meshes_compared=len(current))
assert not diff,report
Path(sys.argv[2]).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
