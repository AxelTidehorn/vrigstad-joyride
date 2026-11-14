"""Local pressed sheet-metal features, compatible shared-vertex normals and fixtures.

Extends the existing Blender authoring tools; does not export or replace bodies.
"""
import math
import bpy,bmesh
from mathutils import Vector

def press_line(body,axis,value,width,depth,region,push_axis=0):
    """Closed V-reveal in the original mesh; region is a vehicle-supplied predicate."""
    bm=bmesh.new();bm.from_mesh(body.data)
    for plane in [value-width,value-width/2,value,value+width/2,value+width]:
        fs=[f for f in bm.faces if any(region(v.co) for v in f.verts) and min(v.co[axis] for v in f.verts)<=plane<=max(v.co[axis] for v in f.verts)]
        geom=set(fs)
        for f in fs:geom.update(f.edges);geom.update(f.verts)
        if geom:
            co=[0,0,0];co[axis]=plane;normal=[0,0,0];normal[axis]=1
            bmesh.ops.bisect_plane(bm,geom=list(geom),plane_co=co,plane_no=normal,dist=1e-7,clear_inner=False,clear_outer=False)
    moved=0
    for v in bm.verts:
        if region(v.co):
            factor=max(0,1-abs(v.co[axis]-value)/(width/2))
            if factor>1e-5:
                v.co[push_axis]-=depth*factor*float(region(v.co))*(1 if push_axis!=0 or v.co.x>0 else -1);moved+=1
    bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free();body.data.update()
    return moved

def panel_normals(body,side_limit=.8,belt=.9):
    """One corner-angle-weighted normal per vertex, retaining raw GLB watertightness."""
    mesh=body.data
    for face in mesh.polygons:face.use_smooth=True
    if 'sharp_edge' in mesh.attributes:mesh.attributes.remove(mesh.attributes['sharp_edge'])
    mesh.update();adjacent=[[] for _ in mesh.vertices]
    for face in mesh.polygons:
        for vi in face.vertices:adjacent[vi].append(face)
    normals=[]
    for v,fs in zip(mesh.vertices,adjacent):
        chosen=[f for f in fs if abs(f.normal.x)>.3] if abs(v.co.x)>side_limit and v.co.z<belt else []
        if chosen:
            n=Vector()
            for f in chosen:
                ids=list(f.vertices);i=ids.index(v.index);a=mesh.vertices[ids[i-1]].co-v.co;b=mesh.vertices[ids[(i+1)%len(ids)]].co-v.co;n+=f.normal*a.angle(b,0)
            normals.append(tuple(n.normalized()))
        else:normals.append(tuple(v.normal))
    mesh.normals_split_custom_set_from_vertices(normals)

def frame(name,width,height,depth,location,material,collection,thickness=.010):
    """Closed rectangular bezel in the X/Z plane, seated around a genuine component."""
    x,y,z=location;verts=[]
    for yy in [y-depth/2,y+depth/2]:
        for w,h in [(width/2,height/2),(width/2-thickness,height/2-thickness)]:
            verts.extend([(x-w,yy,z-h),(x+w,yy,z-h),(x+w,yy,z+h),(x-w,yy,z+h)])
    faces=[]
    for k in range(4):
        n=(k+1)%4
        faces.extend([(k,n,4+n,4+k),(8+k,12+k,12+n,8+n),(k,8+k,8+n,n),(4+k,4+n,12+n,12+k)])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);collection.objects.link(o);mesh.materials.append(material)
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free();return o

def merge_static(objects,name):
    """Batch only static equal-material fixtures; retain all existing wheel/light nodes."""
    objects=list(objects)
    if len(objects)<2:return objects[0] if objects else None
    materials={m for o in objects for m in o.data.materials}
    if len(materials)!=1:raise ValueError('Static batch must have one material')
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=objects[0];o.name=name;return o

def attach_wheel_fixtures():
    """Keep hub pivots and world positions; child fixtures follow future wheel rotation."""
    wheels=[bpy.data.objects[n] for n in ['wheel_fl','wheel_fr','wheel_rl','wheel_rr']]
    for o in list(bpy.context.scene.objects):
        if o.type=='MESH' and o.name.startswith(('trim_rim','trim_spoke')):
            center=o.matrix_world.translation
            wheel=min(wheels,key=lambda w:(w.matrix_world.translation-center).length)
            world=o.matrix_world.copy();o.parent=wheel;o.matrix_world=world

def clean_cut_slivers(obj,min_area=1e-10,merge_distance=.00004):
    """Resolve only newly invalid cut ears (<1e-10 m²), never repair open shells."""
    bm=bmesh.new();bm.from_mesh(obj.data)
    for _ in range(4):
        bad=[f for f in bm.faces if f.calc_area()<min_area]
        if not bad:break
        verts=list({v for f in bad for v in f.verts});edges=list({e for f in bad for e in f.edges})
        bmesh.ops.remove_doubles(bm,verts=verts,dist=merge_distance)
        bmesh.ops.dissolve_degenerate(bm,edges=[e for e in edges if e.is_valid],dist=merge_distance)
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()

def batch_wheel_spokes():
    """One rubber spoke mesh per wheel, keeping its animation parent and geometry."""
    for name in ['wheel_fl','wheel_fr','wheel_rl','wheel_rr']:
        wheel=bpy.data.objects[name]
        spokes=[o for o in wheel.children if o.type=='MESH' and o.name.startswith('trim_spoke')]
        if len(spokes)>1:merge_static(spokes,'trim_spokes_'+name[-2:])

def attach_body_fixtures():
    """Body motion carries glass/trim/lights; wheel pivots remain independent roots."""
    body=bpy.data.objects['body'];bpy.context.view_layer.update()
    for o in list(bpy.context.scene.objects):
        if o.type!='MESH' or o==body or o.name.startswith('wheel_'):continue
        if o.parent and o.parent.name.startswith('wheel_'):continue
        world=o.matrix_world.copy();o.parent=body;o.matrix_world=world
    bpy.context.view_layer.update()
