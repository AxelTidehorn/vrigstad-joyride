"""Technical construction helpers reused from the Volvo authoring workflow."""
import bpy,bmesh,math
import modelkit as mk
collections={}
def interp(y, knots):
    for (a, u), (b, v) in zip(knots, knots[1:]):
        if a <= y <= b:
            return u + (v-u)*(y-a)/(b-a)
    return knots[0][1] if y < knots[0][0] else knots[-1][1]

def material(name, rgb):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*rgb, 1)
    bsdf.inputs['Roughness'].default_value = .85
    return mat

def group(obj,name,mat=None):
    for c in list(obj.users_collection):c.objects.unlink(obj)
    collections[name].objects.link(obj)
    if mat:
        obj.data.materials.clear();obj.data.materials.append(mat)
    return obj

def band(name,path,z,height,depth,mat,collection):
    vertices=[]
    for i,(x,y) in enumerate(path):
        prev=path[max(0,i-1)];nxt=path[min(len(path)-1,i+1)]
        dx,dy=nxt[0]-prev[0],nxt[1]-prev[1];length=math.hypot(dx,dy)
        nx,ny=-dy/length,dx/length
        for side,h in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            vertices.append((x+nx*depth/2*side,y+ny*depth/2*side,z+h*height/2))
    faces=[]
    for i in range(len(path)-1):
        for j in range(4):faces.append((i*4+j,i*4+(j+1)%4,(i+1)*4+(j+1)%4,(i+1)*4+j))
    faces.extend([(3,2,1,0),tuple((len(path)-1)*4+j for j in range(4))])
    o=group(mk.mesh_from_data(name,vertices,faces),collection,mat)
    bpy.context.view_layer.objects.active=o
    bevel=o.modifiers.new('small molded radii','BEVEL');bevel.width=min(.014,height*.2,depth*.2,min(math.dist(a,b) for a,b in zip(path,path[1:]))*.2);bevel.segments=2
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    return o

def slab(name,dims,loc,mat,collection='DETAILS'):
    o=mk.box(name,dims,location=loc);group(o,collection,mat)
    bpy.context.view_layer.objects.active=o
    mod=o.modifiers.new('edge radius','BEVEL');mod.width=min(.008,min(dims)*.2);mod.segments=1
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return o
