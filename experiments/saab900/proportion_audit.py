"""Measured source-shape and preservation audit for the existing Saab master."""
import sys,json,hashlib
from pathlib import Path
import bpy,bmesh,numpy as np
p=Path(__file__).resolve().parent;out=Path(sys.argv[2]);baseline=Path(sys.argv[1]);current={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
with bpy.data.libraries.load(str(baseline),link=False) as (src,dst):
 names=tuple(src.objects);dst.objects=list(names)
old={n:o for n,o in zip(names,dst.objects) if o and o.type=='MESH'}
def shape(o):return sorted(tuple(round(x,6) for x in v.co) for v in o.data.vertices)
def same(a,b):return shape(a)==shape(b) and tuple(a.location)==tuple(b.location) and tuple(a.rotation_euler)==tuple(b.rotation_euler) and tuple(a.scale)==tuple(b.scale)
adapted={'body','glass_envelope','trim_side','trim_side.001','mirror_housing','mirror_housing.001','trim_handle','trim_handle.001','trim_hatch_spoiler','trim_door_seam','trim_door_seam.001'}
unexpected=[n for n,o in current.items() if n not in adapted and (n not in old or not same(o,old[n]))]
removed=[n for n in old if n not in current];assert not unexpected and not removed,(unexpected,removed)
def bounds(o):
 a=np.array(shape(o));return np.stack([a.min(axis=0),a.max(axis=0)]).tolist()
assert bounds(old['body'])==bounds(current['body'])
def glass_planes(o):
 bm=bmesh.new();bm.from_mesh(o.data);remaining=set(bm.verts);result=[]
 while remaining:
  group={remaining.pop()};todo=list(group)
  while todo:
   v=todo.pop()
   for e in v.link_edges:
    other=e.other_vert(v)
    if other in remaining:remaining.remove(other);group.add(other);todo.append(other)
  a=np.array([tuple(v.co) for v in group]);centre=a.mean(axis=0)
  if abs(centre[0])>.5:
   _,_,vectors=np.linalg.svd(a-centre,full_matrices=False);errors=(a-centre)@vectors[-1]
   result.append(dict(centre_m=centre.tolist(),plane_rms_mm=float(np.sqrt(np.mean(errors**2))*1000),note='Includes both surfaces of the 6 mm solid glass; a planar pane has about 3 mm RMS.'))
 bm.free();return sorted(result,key=lambda v:tuple(v['centre_m']))
geometry=json.loads((out/'after/geometry-audit.json').read_text());assert geometry['nonmanifold_edges']==0 and geometry['inconsistent_edges']==0 and geometry['degenerate_faces']==0 and not geometry['self_intersection_candidates']
r=dict(baseline_blend_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),unchanged_components=[n for n in current if n not in adapted],adapted_components=sorted(adapted),unexpected_changes=unexpected,unexpected_removals=removed,body_bounds_identical=True,
 before_body_bounds=bounds(old['body']),after_body_bounds=bounds(current['body']),side_glass_before=glass_planes(old['glass_envelope']),side_glass_after=glass_planes(current['glass_envelope']),
 changes=dict(cowl_rear_station_y_before_m=.84,cowl_rear_station_y_after_m=1.,roof_front_station_y_before_m=.24,roof_front_station_y_after_m=.48,B_pillar_centre_y_before_m=-.49,B_pillar_centre_y_after_m=-.40,quarter_window_rear_y_before_m=-1.48,quarter_window_rear_y_after_m=-1.28,transverse_roof_crown_before_mm=47,transverse_roof_crown_after_mm=25),
 uncertainty='Direct model-coordinate changes are measured. Manufacturer sketch is pre-facelift and not a calibrated 1988 master; reference errors remain canonical pixels, not certified mm.')
(out/'change-audit.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
