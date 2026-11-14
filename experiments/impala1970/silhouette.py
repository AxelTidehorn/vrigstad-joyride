"""Vehicle wrapper around the existing orthographic renderer, not a new pipeline.

Also renders the real side-pane geometry alone for a limited, non-metric photo
comparison. The cropped snowy photo cannot verify a complete vehicle silhouette.
"""
import sys,runpy,json
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
root=Path(__file__).resolve().parents[2];out=Path(sys.argv[1]);config=Path(__file__).with_name('silhouette.json')
sys.argv=[str(root/'tools/vehicle_pipeline/silhouette_render.py'),str(out),str(config)]
runpy.run_path(sys.argv[0],run_name='__main__')
scene=bpy.context.scene
for o in scene.objects:
    if o.type=='MESH':o.hide_render=False
scene.render.filepath=str(out/'full-vehicle.png');bpy.ops.render.render(write_still=True)
glass=bpy.data.objects['glass_envelope'];bm=bmesh.new();bm.from_mesh(glass.data)
remaining=set(bm.verts);keep=set()
while remaining:
    component={remaining.pop()};todo=list(component)
    while todo:
        for e in todo.pop().link_edges:
            for v in e.verts:
                if v in remaining:remaining.remove(v);component.add(v);todo.append(v)
    xyz=np.array([tuple(glass.matrix_world@v.co) for v in component]);center=xyz.mean(axis=0)
    _,eig=np.linalg.eigh(np.cov(xyz.T))
    if center[0]>.65 and abs(eig[0,0])>.7:keep.update(component)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v not in keep],context='VERTS')
if not bm.faces:raise ValueError('No actual right-side pane components found')
bm.to_mesh(glass.data);bm.free()
for o in bpy.context.scene.objects:
    if o.type=='MESH':o.hide_render=o!=glass
scene=bpy.context.scene;scene.render.filepath=str(out/'side-glass.png');bpy.ops.render.render(write_still=True)
frame=json.loads((out/'frame.json').read_text());frame['image']='side-glass.png';frame['projection']='actual right-side door glass only, same exact +X camera and physical scale'
(out/'glass-frame.json').write_text(json.dumps(frame,indent=2)+'\n')
