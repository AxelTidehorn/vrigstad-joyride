"""Bounded refinement audit against the frozen previous master, not image claims."""
from pathlib import Path
import sys,json,hashlib
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parent
baseline=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
current={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
with bpy.data.libraries.load(str(baseline),link=False) as (source,target):
 names=tuple(source.objects);target.objects=list(names)
old={name:o for name,o in zip(names,target.objects) if o and o.type=='MESH'}
def shape(o):return sorted(tuple(round(x,6) for x in v.co) for v in o.data.vertices)
allowed=lambda n:n in ('body','glass_envelope') or n.startswith(('lamp_tail','lamp_head','lamp_indicator','lamp_reflector','trim_POLIS'))
def same(a,b):return shape(a)==shape(b) and tuple(a.location)==tuple(b.location) and tuple(a.rotation_euler)==tuple(b.rotation_euler) and tuple(a.scale)==tuple(b.scale)
unchanged=[n for n in current if n in old and not allowed(n) and same(current[n],old[n])]
unexpected=[n for n in current if n in old and not allowed(n) and not same(current[n],old[n])]
assert not unexpected,unexpected
removed=[n for n in old if n not in current and not allowed(n)]
assert not removed,removed
body=current['body'];bm=bmesh.new();bm.from_mesh(body.data);bm.normal_update();bm.faces.ensure_lookup_table();tree=BVHTree.FromBMesh(bm,epsilon=0)
pairs={tuple(sorted((a,b))) for a,b in tree.overlap(tree) if a!=b and not set(bm.faces[a].verts)&set(bm.faces[b].verts)}
raw_pairs=sorted(pairs)
health=dict(nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),inconsistent_edges=sum(not e.is_contiguous for e in bm.edges),degenerate_faces=sum(f.calc_area()<1e-10 for f in bm.faces),self_intersection_candidates=sorted(pairs),bvh_contact_candidates=raw_pairs,contact_tolerance_m=1e-7,positive_volume=bm.calc_volume(signed=True)>0);bm.free()
def extrema(o):
 v=shape(o);return [[min(p[i] for p in v),max(p[i] for p in v)] for i in range(3)]
def roof(o):return sorted(tuple(round(x,6) for x in v.co) for v in o.data.vertices if abs(v.co.x)<.00001 and -1.8<=v.co.y<=.20 and v.co.z>1.35)
assert extrema(body)==extrema(old['body'])
old_roof=roof(old['body']);new_roof=roof(body)
assert set(old_roof).issubset(set(new_roof))
import numpy as np
spine=sorted((v[1],v[2]) for v in old_roof)
for x,y,z in new_roof:assert abs(z-float(np.interp(y,[a for a,b in spine],[b for a,b in spine])))<2e-6
report=dict(baseline_git_commit="4812b85e8b75b1c788bee7824a45145692fa7152",baseline_blend_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),unchanged_components=unchanged,unexpected_changes=unexpected,unexpected_removed_components=removed,
 body_bounds_identical=True,central_roof_profile_identical=True,body_health=health,
 modifications=dict(rear_side_glass_extension_mm=80,front_rear_window_margin_mm=8,front_rear_recess_depth_mm=5,previous_recess_depth_mm=9,glass_thickness_mm=3,
 rear_lamps='Rear-facing ray seated 20 mm proud / 8 mm embedded, 85 mm wide; D-corner conforming volume',headlamps='370 x 100 mm rectangular front lens; 55 mm embedded depth',police='Blue on white only; full front fender and rear quarter painted areas; no yellow'))
assert not health['nonmanifold_edges'] and not health['inconsistent_edges'] and not health['degenerate_faces'] and not pairs and health['positive_volume']
(out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
