"""Source-generated temporary master versus edited canonical master, in world metres."""
from pathlib import Path
import sys,json
import bpy,numpy as np
from mathutils import Matrix
bpy.context.view_layer.update();current={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
with bpy.data.libraries.load(str(Path(sys.argv[1]).resolve()),link=False) as (src,dst):names=tuple(src.objects);dst.objects=list(names)
other={n:o for n,o in zip(names,dst.objects) if o and o.type=='MESH'}
def world(o):
 basis=Matrix.LocRotScale(o.location,o.rotation_euler.to_quaternion(),o.scale)
 return world(o.parent)@o.matrix_parent_inverse@basis if o.parent else basis
def points(o,source):
 matrix=world(o)
 return np.array([tuple(matrix@v.co) for v in o.data.vertices])
errors={}
for n in sorted(current.keys()&other.keys()):
 a=points(current[n],False);b=points(other[n],True)
 if len(a)!=len(b):errors[n]={'vertex_counts':[len(a),len(b)]};continue
 # KD distance is invariant to harmless fixture join/index ordering.
 maximum=0
 for start in range(0,len(a),200):maximum=max(maximum,float(np.sqrt(((a[start:start+200,None,:]-b[None,:,:])**2).sum(axis=2)).min(axis=1).max()))
 if maximum>1e-6:errors[n]={'max_position_error_m':maximum}
report={'ok':not errors and current.keys()==other.keys(),'differences':errors,'meshes_compared':len(current),'missing_in_source':sorted(current.keys()-other.keys()),'extra_in_source':sorted(other.keys()-current.keys()),'world_position_tolerance_m':1e-6,'transform_method':'Compose saved local transforms and parent inverse for both scenes, including hidden police equipment; no reliance on unevaluated hidden matrix_world caches'}
Path(sys.argv[2]).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert report['ok'],report
