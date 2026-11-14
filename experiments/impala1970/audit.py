"""Source health and critical fit measurements, independent of export success."""
import sys,json,math,hashlib
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=Path(sys.argv[1]);out.parent.mkdir(parents=True,exist_ok=True)
bpy.context.view_layer.update()
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
def tree(o):
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.transform(bm,matrix=o.matrix_world,verts=list(bm.verts));bm.normal_update();return bm,BVHTree.FromBMesh(bm,epsilon=0)
def health(o):
    bm,t=tree(o);bm.faces.ensure_lookup_table()
    pairs={tuple(sorted((a,b))) for a,b in t.overlap(t) if a!=b and not set(bm.faces[a].verts)&set(bm.faces[b].verts)}
    remaining=set(bm.verts);islands=0
    while remaining:
        todo=[remaining.pop()];islands+=1
        while todo:
            for e in todo.pop().link_edges:
                for v in e.verts:
                    if v in remaining:remaining.remove(v);todo.append(v)
    r=dict(nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),inconsistent_edges=sum(not e.is_contiguous for e in bm.edges),degenerate_faces=sum(f.calc_area()<1e-10 for f in bm.faces),signed_volume_m3=bm.calc_volume(signed=True),connected_components=islands,self_intersection_candidates=len(pairs),sample_pairs=sorted(pairs)[:8],triangles=sum(len(f.verts)-2 for f in bm.faces));bm.free();return r
body=bpy.data.objects['body'];glass=bpy.data.objects['glass_envelope']
report={'source':'build/model.blend','body':health(body),'meshes':len(objects),'triangles':sum(sum(len(f.vertices)-2 for f in o.data.polygons) for o in objects),'materials':sorted({m.name for o in objects for m in o.data.materials}),'components':{o.name:health(o) for o in objects if o!=body}}
bm,bt=tree(body);gm,gt=tree(glass)
trim_clearances=[]
for path in json.loads(body['shoulder_trim_centrelines_m']):
    for a,b in zip(path,path[1:]):
        for t in [0,.25,.5,.75,1]:
            point=Vector(a).lerp(Vector(b),t);near=bt.find_nearest(point)
            trim_clearances.append(float(near[3]))
report['shoulder_moulding_fit']={'radius_m':.006,'maximum_centreline_to_steel_m':max(trim_clearances),'all_sampled_sections_seated':max(trim_clearances)<.0035,'samples':len(trim_clearances),'criterion':'3.5 mm maximum axis/steel distance, less than 4.24 mm inscribed radius of four-sided 6 mm trim'}
report['glass_body_surface_intersection_candidates']=len(bt.overlap(gt))
# Check positive sampled outward clearance, not just the absence of intersections.
clearances=[]
for v in gm.verts:
    nearest=bt.find_nearest(v.co)
    if nearest[0] is not None:clearances.append(float((v.co-nearest[0]).dot(nearest[1])))
report['glass_signed_backing_clearance_m']={'minimum':min(clearances),'maximum':max(clearances),'nonpositive_samples':sum(x<=0 for x in clearances)}
report['wheels']={}
for n in ['wheel_fl','wheel_fr','wheel_rl','wheel_rr']:
    o=bpy.data.objects[n];wm,wt=tree(o);p=o.matrix_world.translation
    # The small hidden axle mounting shaft intentionally enters the inner well
    # wall. The tyre surface itself must clear the closed body.
    fs=list(wm.faces);wm.faces.ensure_lookup_table();overlaps=bt.overlap(wt)
    tire_hits=[(a,b) for a,b in overlaps if max(math.hypot(v.co.y-p.y,v.co.z-p.z) for v in fs[b].verts)>.12]
    report['wheels'][n]={'hub_world_m':list(p),'parent':o.parent.name if o.parent else None,'tire_body_intersection_candidates':len(tire_hits),'fixtures':[x.name for x in o.children]};wm.free()
bm.free();gm.free()
coords=[o.matrix_world@v.co for o in objects for v in o.data.vertices]
report['overall_xyz_m']=[max(p[i] for p in coords)-min(p[i] for p in coords) for i in range(3)]
report['axle_distance_m']=bpy.data.objects['wheel_fl'].location.y-bpy.data.objects['wheel_rl'].location.y
report['body_paint_material_count']=len(body.data.materials)
report['wheel_fixtures_own_hub']=all(bpy.data.objects['trim_rim_'+tag].parent==bpy.data.objects['wheel_'+tag] and bpy.data.objects['trim_rim_whitewall_'+tag].parent==bpy.data.objects['wheel_'+tag] for tag in ['fl','fr','rl','rr'])
report['all_fixed_fixtures_follow_body']=all(o.parent==body or o.parent and o.parent.name.startswith('wheel_') for o in objects if o!=body and not o.name.startswith('wheel_'))
report['lamp_tops_z_m']=max((bpy.data.objects['lamp_headlights'].matrix_world@v.co).z for v in bpy.data.objects['lamp_headlights'].data.vertices)
report['ok']=not any(report['body'][k] for k in ['nonmanifold_edges','inconsistent_edges','degenerate_faces','self_intersection_candidates']) and report['body']['connected_components']==1 and report['body']['signed_volume_m3']>0 and report['glass_body_surface_intersection_candidates']==0 and report['glass_signed_backing_clearance_m']['nonpositive_samples']==0 and not any(w['tire_body_intersection_candidates'] for w in report['wheels'].values()) and report['all_fixed_fixtures_follow_body'] and all(not h['nonmanifold_edges'] and not h['inconsistent_edges'] and not h['degenerate_faces'] for h in report['components'].values())
report['ok']=report['ok'] and report['wheel_fixtures_own_hub'] and report['triangles']<=20000
report['ok']=report['ok'] and report['shoulder_moulding_fit']['all_sampled_sections_seated']
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='components'}));assert report['ok'],report
