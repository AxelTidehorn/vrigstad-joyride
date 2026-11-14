"""Strict source health, protected geometry and wheel hierarchy verification."""
from pathlib import Path
import json,sys,hashlib,math
import bpy,bmesh
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
key=sys.argv[1];baseline=Path(sys.argv[2]);out=Path(sys.argv[3]);out.mkdir(parents=True,exist_ok=True)
bpy.context.view_layer.update();current={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
with bpy.data.libraries.load(str(baseline),link=False) as (src,dst):names=tuple(src.objects);dst.objects=list(names)
old={n:o for n,o in zip(names,dst.objects) if o and o.type=='MESH'}
def coords(o,previous=False):
 m=Matrix.LocRotScale(o.location,o.rotation_euler.to_quaternion(),o.scale) if previous else o.matrix_world
 return sorted(tuple(round(x,6) for x in m@v.co) for v in o.data.vertices)
def health(o):
 bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();bm.faces.ensure_lookup_table();tree=BVHTree.FromBMesh(bm,epsilon=0)
 pairs={tuple(sorted((a,b))) for a,b in tree.overlap(tree) if a!=b and not set(bm.faces[a].verts)&set(bm.faces[b].verts)}
 h=dict(nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),inconsistent_edges=sum(not e.is_contiguous for e in bm.edges),degenerate_faces=sum(f.calc_area()<1e-10 for f in bm.faces),bvh_self_intersection_candidates=len(pairs),positive_volume=bm.calc_volume(signed=True)>0,triangles=len(bm.faces),worst_pairs=list(sorted(pairs))[:20]);bm.free();return h
body=current['body'];h=health(body)
# Write failure evidence before rejecting, rather than hiding it behind a zero-error summary.
report={'vehicle':key,'baseline_sha256':hashlib.sha256(baseline.read_bytes()).hexdigest(),'body_health':h,'source_geometry_changed':coords(body)!=coords(old['body'],True)}
new=set(coords(body));protected=[]
for v in old['body'].data.vertices:
 x,y,z=v.co
 if key=='volvo240':keep=abs(x)>=.5699 and any(math.hypot(y-a,z-.315)<.405 for a in [1.42,-1.23])
 elif key=='saab900':keep=z>1.05 and -1.94<y<.98
 else:keep=z>1.46 and y>-2.10
 if keep:protected.append(tuple(round(a,6) for a in v.co))
report['protected_original_vertices']=len(protected);report['missing_protected_vertices']=[p for p in protected if p not in new]
report['wheels']={}
for n in ['wheel_fl','wheel_fr','wheel_rl','wheel_rr']:
 same=coords(current[n])==coords(old[n],True)
 report['wheels'][n]={'world_geometry_preserved':same,'hub_location':list(current[n].matrix_world.translation)}
fixtures=[o for n,o in current.items() if n.startswith(('trim_rim','trim_spoke'))]
report['wheel_fixtures_parented']=all(o.parent and o.parent.name.startswith('wheel_') for o in fixtures)
def maximum_world_difference(a,b):
 def raw(o,previous):
  m=Matrix.LocRotScale(o.location,o.rotation_euler.to_quaternion(),o.scale) if previous else o.matrix_world
  return np.array([tuple(m@v.co) for v in o.data.vertices])
 x=raw(a,False);y=raw(b,True)
 return float(np.sqrt(((x[:,None,:]-y[None,:,:])**2).sum(axis=2)).min(axis=1).max())
def fixture_points(objects,previous):
 rows=[]
 for o in objects:
  m=Matrix.LocRotScale(o.location,o.rotation_euler.to_quaternion(),o.scale) if previous else o.matrix_world
  rows.extend(tuple(m@v.co) for v in o.data.vertices)
 return np.array(rows)
a=fixture_points(fixtures,False);b=fixture_points([o for n,o in old.items() if n.startswith(('trim_rim','trim_spoke'))],True)
report['fixture_max_world_difference_m']=float(np.sqrt(((a[:,None,:]-b[None,:,:])**2).sum(axis=2)).min(axis=1).max())
report['fixture_world_geometry_preserved']=report['fixture_max_world_difference_m']<.000001
report['glass_world_geometry_preserved']=coords(current['glass_envelope'])==coords(old['glass_envelope'],True)
def box(o,previous=False):
 co=coords(o,previous);return [[min(p[i] for p in co),max(p[i] for p in co)] for i in range(3)]
report['old_body_bounds_m']=box(old['body'],True);report['body_bounds_m']=box(body)
report['mesh_objects']=len(current);report['triangles']=sum(sum(len(f.vertices)-2 for f in o.data.polygons) for o in current.values() if not o.hide_render)
report['ok']=not any(h[k] for k in ['nonmanifold_edges','inconsistent_edges','degenerate_faces','bvh_self_intersection_candidates']) and h['positive_volume'] and not report['missing_protected_vertices'] and all(v['world_geometry_preserved'] for v in report['wheels'].values()) and report['fixture_world_geometry_preserved'] and report['wheel_fixtures_parented'] and report['old_body_bounds_m']==report['body_bounds_m']
(out/'geometry.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert report['ok'],report
