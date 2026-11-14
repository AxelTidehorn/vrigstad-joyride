"""Geometry/preservation checks against the latest frozen Volvo 240 master."""
from pathlib import Path
import bpy,bmesh,json,sys,hashlib,math
from mathutils.bvhtree import BVHTree
baseline=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
current={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
with bpy.data.libraries.load(str(baseline),link=False) as (source,target):
 names=tuple(source.objects);target.objects=list(names)
old={n:o for n,o in zip(names,target.objects) if o and o.type=='MESH'}
def points(o):return [tuple(v.co) for v in o.data.vertices]
def shape(o):return (points(o),[tuple(f.vertices) for f in o.data.polygons],tuple(o.location),tuple(o.rotation_euler),tuple(o.scale))
assert set(current)==set(old)
unchanged=[n for n in current if n!='body' and shape(current[n])==shape(old[n])]
assert len(unchanged)==len(current)-1
body=current['body'];bm=bmesh.new();bm.from_mesh(body.data);bm.normal_update();bm.faces.ensure_lookup_table()
tree=BVHTree.FromBMesh(bm,epsilon=0)
pairs={tuple(sorted((a,b))) for a,b in tree.overlap(tree) if a!=b and not set(bm.faces[a].verts)&set(bm.faces[b].verts)}
health=dict(nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),inconsistent_edges=sum(not e.is_contiguous for e in bm.edges),degenerate_faces=sum(f.calc_area()<1e-10 for f in bm.faces),bvh_self_intersection_candidates=len(pairs),positive_volume=bm.calc_volume(signed=True)>0,body_triangles=len(bm.faces))
bm.free()
assert not any(health[k] for k in ['nonmanifold_edges','inconsistent_edges','degenerate_faces','bvh_self_intersection_candidates']) and health['positive_volume'],health
P=json.loads(Path(__file__).with_name('parameters.json').read_text())
def protected(v):
 x,y,z=v
 return abs(x)<P['well_inner_x']-.0001 or all(math.hypot(y-a,z-P['tire_radius'])>P['arch_radius']+.081 for a in [P['front_axle_y'],P['front_axle_y']-P['wheelbase']])
rounded=lambda v:tuple(round(x,6) for x in v)
newpoints={rounded(v) for v in points(body)}
protected_points=[v for v in points(old['body']) if protected(v)]
missing=[v for v in protected_points if rounded(v) not in newpoints]
assert not missing,missing[:10]
def bounds(o):return [[min(v[i] for v in points(o)),max(v[i] for v in points(o))] for i in range(3)]
assert bounds(body)==bounds(old['body']),(bounds(body),bounds(old['body']))
report=dict(baseline_git_commit='f064b57',baseline_blend_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),unchanged_components=unchanged,protected_body_vertices_preserved=len(protected_points),missing_protected_vertices=len(missing),old_body_bounds_m=bounds(old['body']),new_body_bounds_m=bounds(body),body_health=health,refinement=json.loads(body['arch_refinement_parameters']),caveat='BVH is a numerical screen, not exhaustive component solid-intersection proof. Intentional mounted overlaps remain.')
(out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
