"""Exact +X orthographic projection plus existing Modeler quality renders.
Run with bmod.py --script this.py --blend MODEL --out LOG -- OUTPUT CONFIG.
Configuration supplies vehicle-specific control stations; renderer is generic.
"""
import sys,json,math
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import render_views
out=Path(sys.argv[1]).resolve();out.mkdir(parents=True,exist_ok=True)
cfg=json.loads(Path(sys.argv[2]).read_text());spec=cfg['blender'];scene=bpy.context.scene
objects=[o for o in scene.objects if o.type=='MESH'];body=bpy.data.objects[spec['body_object']]
# Audit real geometry before creating any temporary cameras.
bm=bmesh.new();bm.from_mesh(body.data);bm.normal_update()
quality=dict(nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),inconsistent_edges=sum(not e.is_contiguous for e in bm.edges),degenerate_faces=sum(f.calc_area()<1e-10 for f in bm.faces),signed_volume_m3=bm.calc_volume(signed=True))
from mathutils.bvhtree import BVHTree
bm.faces.ensure_lookup_table();tree=BVHTree.FromBMesh(bm,epsilon=0)
quality['self_intersection_candidates']=[list(p) for p in sorted({tuple(sorted((a,b))) for a,b in tree.overlap(tree) if a!=b and not set(bm.faces[a].verts)&set(bm.faces[b].verts)})]
bm.free()
quality['triangles']=sum(len(o.data.loop_triangles) or sum(len(f.vertices)-2 for f in o.data.polygons) for o in objects)
quality['dimensions_m']=[max((o.matrix_world@v.co)[axis] for o in objects for v in o.data.vertices)-min((o.matrix_world@v.co)[axis] for o in objects for v in o.data.vertices) for axis in range(3)]
# Save vertex checksums for preserved components and actual longitudinal spine.
import hashlib
quality['component_sha256']={o.name:hashlib.sha256(json.dumps({'vertices':[list(v.co) for v in o.data.vertices],'matrix':[list(r) for r in o.matrix_world]},sort_keys=True).encode()).hexdigest() for o in objects if o.name not in ('body','glass_envelope')}
spine=sorted({(round(v.co.y,6),round(v.co.z,6)) for v in body.data.vertices if abs(v.co.x)<.00001 and v.co.z>.65})
quality['centreline_y_z_m']=spine
(out/'geometry-audit.json').write_text(json.dumps(quality,indent=2)+'\n')
# Standard quality views share explicit bounds across before/after.
focus=tuple(tuple(v) for v in spec['quality_focus'])
if not spec.get('skip_quality',False):
 render_views.run(str(out/'quality'),mode='clay',res=1200,color_by='material',views=[('side',90,0,True),('front_three_quarter',135,22,False)],focus=focus)
 render_views.run(str(out/'cowl'),mode='clay',res=1400,color_by='material',views=[('hood_windscreen',130,18,True)],focus=tuple(tuple(v) for v in spec['cowl_focus']))
# Silhouette excludes mirrors, lights, trims and bumpers on both sides of comparison.
for o in objects:o.hide_render=not (o.name==spec['body_object'] or o.name.startswith('wheel_'))
cam_data=bpy.data.cameras.new('silhouette_exact_ortho');cam=bpy.data.objects.new('silhouette_exact_ortho',cam_data);scene.collection.objects.link(cam)
cam.location=(10,0,.75);cam.rotation_euler=(Vector((0,0,.75))-cam.location).to_track_quat('-Z','Y').to_euler();cam_data.type='ORTHO';cam_data.ortho_scale=spec.get('orthographic_scale_m',5.4)
scene.camera=cam;scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
scene.display.shading.light='FLAT';scene.display.shading.show_shadows=False;scene.display.shading.show_cavity=False;scene.display.shading.show_object_outline=False
scene.render.filepath=str(out/'silhouette.png');bpy.context.view_layer.update();bpy.ops.render.render(write_still=True)
def project(p):
 v=world_to_camera_view(scene,cam,Vector(p));return [v.x*1800,(1-v.y)*800]
def top_at(y):
 candidates=[]
 for edge in body.data.edges:
  a,b=[body.matrix_world@body.data.vertices[i].co for i in edge.vertices]
  if max(abs(a.x),abs(b.x))>.0001:continue
  if min(a.y,b.y)-1e-7<=y<=max(a.y,b.y)+1e-7 and abs(a.y-b.y)>1e-8:
   candidates.append(a.z+(b.z-a.z)*(y-a.y)/(b.y-a.y))
 if not candidates:raise ValueError(f'No body centreline intersection at y={y}')
 return [0,y,max(candidates)]
quality['wheel_centres_world_m']={n:list(bpy.data.objects[n].location) for n in ['wheel_fl','wheel_fr','wheel_rl','wheel_rr']}
(out/'geometry-audit.json').write_text(json.dumps(quality,indent=2)+'\n')
points={name:project(top_at(y)) for name,y in spec.get('point_stations_y',{}).items()}
curves={name:[project(top_at(y)) for y in stations] for name,stations in spec.get('curve_stations_y',{}).items()}
for name,arch in spec.get('arch_curves',{}).items():
 centre=bpy.data.objects[arch['wheel_object']].location
 radius=arch['radius_m']
 selected=sorted({(round(v.co.y,6),round(v.co.z,6)) for v in body.data.vertices
   if abs(v.co.x)>arch['minimum_abs_x'] and v.co.z>=centre.z-1e-5
   and abs(math.hypot(v.co.y-centre.y,v.co.z-centre.z)-radius)<.0001})
 if len(selected)<5:raise ValueError(f'Cannot measure actual wheel-arch mesh vertices: {name}')
 curves[name]=[project((0,y,z)) for y,z in selected]
frame=dict(image='silhouette.png',mask=dict(mode='alpha',reviewed=True),orthographic=True,metric_reliable=True,
 front_wheel=project((bpy.data.objects['wheel_fl'].location+bpy.data.objects['wheel_fr'].location)/2),rear_wheel=project((bpy.data.objects['wheel_rl'].location+bpy.data.objects['wheel_rr'].location)/2),ground=project((0,0,0)),
 pixels_per_metre=1800/cam_data.ortho_scale,points=points,curves=curves,projection='camera +X, front +Y is image right, Z up; body plus four tyres only')
(out/'frame.json').write_text(json.dumps(frame,indent=2)+'\n')
print(json.dumps({'output':str(out),'geometry':quality|{'component_sha256':'see file','centreline_y_z_m':'see file'}}))
