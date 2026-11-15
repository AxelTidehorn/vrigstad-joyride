"""Compare the current master with the frozen prior master in world metres."""
from pathlib import Path
import sys,json,math,re,hashlib
import bpy,bmesh,numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
baseline=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]);bpy.context.view_layer.update()
current={o.name:o for o in bpy.context.scene.objects if o.type=='MESH'}
with bpy.data.libraries.load(str(baseline),link=False) as (src,dst):names=tuple(src.objects);dst.objects=list(names)
old={n:o for n,o in zip(names,dst.objects) if o and o.type=='MESH'}
def world(o):
    basis=Matrix.LocRotScale(o.location,o.rotation_euler.to_quaternion(),o.scale)
    return world(o.parent)@o.matrix_parent_inverse@basis if o.parent else basis
def points(o):return np.array([tuple(world(o)@v.co) for v in o.data.vertices])
def sorted_points(o):return sorted(tuple(round(c,6) for c in p) for p in points(o))
protected=[n for n in old if n.startswith(('wheel_','trim_rim','trim_spokes'))]
preserved={n:dict(geometry_preserved=n in current and sorted_points(current[n])==sorted_points(old[n]),hub_or_fixture_origin_delta_m=float((world(current[n]).translation-world(old[n]).translation).length)) for n in protected}
def material_values(objects):
    result={}
    for o in objects.values():
        for m in o.data.materials:
            bs=m.node_tree.nodes.get('Principled BSDF');result[re.sub(r'\.\d{3}$','',m.name)]={k:list(bs.inputs[k].default_value) if k=='Base Color' else float(bs.inputs[k].default_value) for k in ['Base Color','Roughness','Metallic','Transmission Weight']}
    return result
def tree(o):
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.transform(bm,matrix=world(o),verts=list(bm.verts));t=BVHTree.FromBMesh(bm);bm.free();return t
def measurements(objects):
    t=tree(objects['body'])
    def roof(x,y):
        hit=t.ray_cast(Vector((x,y,4)),Vector((0,0,-1)))
        if hit[0] is None:raise ValueError(f'No steel at {x,y}')
        return float(hit[0].z)
    def nose(x):return float(t.ray_cast(Vector((x,4,.69)),Vector((0,-1,0)))[0].y)
    def side(x):return t.ray_cast(Vector((x,0,.60)),Vector((-1 if x>0 else 1,0,0)))[0]
    # Identify the actual connected front pane; do not substitute a roof profile.
    o=objects['glass_envelope'];bm=bmesh.new();bm.from_mesh(o.data);remaining=set(bm.verts);angles=[]
    while remaining:
        component={remaining.pop()};todo=list(component)
        while todo:
            for e in todo.pop().link_edges:
                for v in e.verts:
                    if v in remaining:remaining.remove(v);component.add(v);todo.append(v)
        xyz=np.array([tuple(world(o)@v.co) for v in component]);c=xyz.mean(axis=0)
        if c[1]>.4 and abs(c[0])<.15:
            _,eig=np.linalg.eigh(np.cov(xyz.T));n=eig[:,0];angles.append(math.degrees(math.atan2(abs(n[1]),abs(n[2]))))
    bm.free()
    if len(angles)!=1:raise ValueError('Expected one front pane')
    steel=points(objects['body'])
    return dict(front_centre_y_m=nose(0),front_outboard_y_m=nose(.775),front_chevron_relief_m=nose(0)-nose(.775),hood_centre_z_m=roof(0,2.1),hood_channel_z_m=roof(.72,2.1),fender_crown_z_m=roof(.845,2.1),waist_width_at_y0_z060_m=float(side(3).x-side(-3).x),rear_deck_z_m=roof(0,-2.47),rear_haunch_z_m=roof(.82,-2.47),windscreen_angle_from_horizontal_deg=angles[0],body_xyz_bounds_m=[float(x) for x in steel.max(axis=0)-steel.min(axis=0)])
a,b=measurements(old),measurements(current)
report=dict(baseline_commit='6c7f32c783aa0923cb2f18836157a7ef1cccfc9b',baseline_blend_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),measurements={'before':a,'after':b,'difference':{k:b[k]-a[k] for k in a if isinstance(a[k],float)}},protected_wheel_nodes=preserved,materials_unchanged=material_values(old)==material_values(current),node_names_preserved=current.keys()==old.keys(),body_origin_preserved=list(world(current['body']).translation)==list(world(old['body']).translation),scope='Measurements are actual model geometry, not a metric verdict against perspective photographs.')
report['ok']=all(x['geometry_preserved'] and x['hub_or_fixture_origin_delta_m']<1e-6 for x in preserved.values()) and report['materials_unchanged'] and report['node_names_preserved'] and report['body_origin_preserved']
out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert report['ok'],report
