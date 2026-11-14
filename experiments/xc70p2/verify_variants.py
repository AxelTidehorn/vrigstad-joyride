"""Assert shared geometry in the actual two GLBs, independent of Blender source."""
from pathlib import Path
import json,hashlib
import numpy as np
import trimesh
p=Path(__file__).resolve().parent/'build'
def nodes(file):
 s=trimesh.load(file,force='scene',process=False);out={}
 for name in s.graph.nodes_geometry:
  matrix,key=s.graph[name];mesh=s.geometry[key].copy();mesh.apply_transform(matrix);out[name]=mesh
 return out
c=nodes(p/'xc70-civilian.glb');pol=nodes(p/'xc70-police.glb')
def canonical(mesh):return np.unique(np.round(mesh.vertices,6),axis=0)
common=sorted(c.keys()&pol.keys());different=[n for n in common if not np.array_equal(canonical(c[n]),canonical(pol[n]))]
assert not different,different
assert all(n in common for n in ['body','glass_envelope','wheel_fl','wheel_fr','wheel_rl','wheel_rr'])
arch=np.vstack([m.vertices for n,m in c.items() if n.startswith('trim_arch')])
report=dict(ok=True,common_meshes=len(common),identical_geometry=common,differences=different,
 police_only=sorted(pol.keys()-c.keys()),cladding_width_m=float(np.ptp(arch[:,0])),
 body_sha256=hashlib.sha256(canonical(c['body']).tobytes()).hexdigest(),
 texture_verification='Packed PNG images independently decoded in Pillow and actual Blender reimport; Node loader checks scene structure only')
(p/'shared-export-geometry.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report|{'identical_geometry':'see JSON'},indent=2))
