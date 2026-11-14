"""Bounded edit of existing 240 wheel wells; no replacement shell or wheel mesh."""
import math,json
import bpy,bmesh
from mathutils import Vector

def radius_on_profile(dy,dz,points):
    r=math.hypot(dy,dz)
    if r<1e-9:return 0
    direction=Vector((dy/r,dz/r))
    for a,b in zip(points,points[1:]+points[:1]):
        a=Vector(a);edge=Vector(b)-a
        cross=lambda u,v:u.x*v.y-u.y*v.x
        det=cross(direction,edge)
        if abs(det)<1e-9:continue
        distance=cross(a,edge)/det;fraction=cross(a,direction)/det
        if distance>=0 and -.00001<=fraction<=1.00001:return distance
    raise ValueError('Wheel-well profile has no ray intersection')

def refine(body,parameters):
    if body.get('arch_refinement')=='defined-240-v1':return
    settings=parameters.get('arch_refinement',{})
    bm=bmesh.new();bm.from_mesh(body.data);bm.normal_update()
    changed=0;profiles=[]
    for axle,yc in [('front',parameters['front_axle_y']),('rear',parameters['front_axle_y']-parameters['wheelbase'])]:
        # Angular shoulders, short flat crown and near-vertical lower legs.
        # Rear opening remains a little flatter, as on the existing reference.
        cap=settings.get(axle+'_crown',.355 if axle=='front' else .350)
        width=settings.get('half_width',.355);flat=settings.get('flat_half_span',.085)
        points=[(-width,-.15),(-width,.075),(-.305,.195),(-.225,.285),(-flat,cap),(flat,cap),(.225,.285),(.305,.195),(width,.075),(width,-.15)]
        profiles.append((yc,points))
        for v in bm.verts:
            x,y,z=v.co;dy=y-yc;dz=z-parameters['tire_radius'];r=math.hypot(dy,dz)
            if abs(x)<parameters['well_inner_x']-.00001 or r>parameters['arch_radius']+.08 or r<1e-7:continue
            # Propagate only into a narrow fender neighbourhood, leaving belt,
            # roof, greenhouse, ends and sill away from the opening untouched.
            weight=1 if r<=parameters['arch_radius'] else (parameters['arch_radius']+.08-r)/.08
            target=radius_on_profile(dy,dz,points)
            scale=1+(target/parameters['arch_radius']-1)*weight
            v.co.y=yc+dy*scale;v.co.z=z if abs(z-parameters['sill_z'])<.00001 else parameters['tire_radius']+dz*scale;changed+=1
    # Straighten redundant Boolean subdivisions after polygonal remapping.
    # The old circular cap tessellation would otherwise make zero-area ears.
    def local(v):return abs(v.co.x)>=parameters['well_inner_x']-.00001 and any(math.hypot(v.co.y-yc,v.co.z-parameters['tire_radius'])<parameters['arch_radius']+.081 for yc,_ in profiles)
    local_verts=[v for v in bm.verts if local(v)]
    local_edges=[e for e in bm.edges if all(local(v) for v in e.verts)]
    bmesh.ops.dissolve_limit(bm,angle_limit=.0001,verts=local_verts,edges=local_edges,use_dissolve_boundaries=False)
    bm.normal_update()
    rim_edges=[]
    for yc,points in profiles:
        for edge in bm.edges:
            if all(abs(v.co.x)>.70 and abs(math.hypot(v.co.y-yc,v.co.z-parameters['tire_radius'])-radius_on_profile(v.co.y-yc,v.co.z-parameters['tire_radius'],points))<.00002 for v in edge.verts):rim_edges.append(edge)
    # Retain the explicit polygonal opening as a hard connected edge.
    # Do not run a generic bevel over the old Boolean tessellation.
    bmesh.ops.remove_doubles(bm,verts=[v for v in bm.verts if local(v)],dist=.000005)
    bmesh.ops.dissolve_degenerate(bm,dist=.000005,edges=[e for e in bm.edges if all(local(v) for v in e.verts)])
    # Add an 8–15 mm connected reveal inside each well. This support loop keeps
    # the panel normal separate from the deeper cavity without splitting GLB vertices.
    for sign in [-1,1]:
        cavity=[f for f in bm.faces if all(local(v) for v in f.verts) and any(sign*v.co.x<.60 for v in f.verts) and any(sign*v.co.x>.80 for v in f.verts)]
        geom=set(cavity)
        for f in cavity:geom.update(f.edges);geom.update(f.verts)
        if geom:bmesh.ops.bisect_plane(bm,geom=list(geom),plane_co=(sign*.84,0,0),plane_no=(1,0,0),dist=1e-7,clear_inner=False,clear_outer=False)
    bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    for f in bm.faces:f.smooth=True
    for e in bm.edges:e.smooth=True
    bm.to_mesh(body.data);bm.free();body.data.update()
    # The existing validator requires indexed watertight GLB topology. One normal
    # per shared vertex preserves it; split sharp-edge normals would duplicate
    # indices at every crease. Favour the real outer panel at each opening edge.
    mesh=body.data;adjacent=[[] for _ in mesh.vertices]
    for f in mesh.polygons:
        for vi in f.vertices:adjacent[vi].append(f)
    normals=[]
    for v,fs in zip(mesh.vertices,adjacent):
        chosen=[f for f in fs if abs(f.normal.x)>.3] if abs(v.co.x)>.80 and v.co.z<.85 else []
        if chosen:
            normal=Vector()
            for f in chosen:
                ids=list(f.vertices);j=ids.index(v.index)
                a=mesh.vertices[ids[j-1]].co-v.co;b=mesh.vertices[ids[(j+1)%len(ids)]].co-v.co
                normal+=f.normal*a.angle(b,0)
            normals.append(tuple(normal.normalized()))
        else:normals.append(tuple(v.normal))
    mesh.normals_split_custom_set_from_vertices(normals)
    body['arch_refinement']='defined-240-v1'
    body['arch_refinement_parameters']=json.dumps(dict(front_crown_mm=settings.get('front_crown',.355)*1000,rear_crown_mm=settings.get('rear_crown',.350)*1000,reveal_support_x_m=.84,moved_existing_vertices=changed,arch_boundary_edges=len(set(rim_edges))))

    body['parameters']=json.dumps(parameters,sort_keys=True)
