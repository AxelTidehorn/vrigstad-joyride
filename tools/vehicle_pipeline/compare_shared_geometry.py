"""Compare every common GLB mesh, including multi-material lamps and hierarchy.

Unlike loader-generated primitive names, original glTF node names are stable.
Colours/materials may differ; triangles, world transforms and wheel parents may not.
"""
from pathlib import Path
import argparse,json,struct,hashlib
import numpy as np

def mesh_nodes(path):
    raw=Path(path).read_bytes()
    if raw[:4]!=b'glTF':raise ValueError('Expected a binary GLB')
    doc=None;binary=None;offset=12
    while offset<len(raw):
        size,kind=struct.unpack_from('<II',raw,offset);chunk=raw[offset+8:offset+8+size];offset+=8+size
        if kind==0x4e4f534a:doc=json.loads(chunk)
        elif kind==0x004e4942:binary=chunk
    if doc is None or binary is None:raise ValueError('Missing GLB JSON or BIN chunk')
    def accessor(index):
        a=doc['accessors'][index]
        if 'sparse' in a:raise ValueError('Sparse accessor unsupported in vehicle exporter output')
        v=doc['bufferViews'][a['bufferView']];dtype={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']];n={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']];item=np.dtype(dtype).itemsize
        return np.ndarray((a['count'],n),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',n*item),item)).copy()
    parents={c:i for i,n in enumerate(doc['nodes']) for c in n.get('children',[])};matrices={}
    def world(i):
        if i in matrices:return matrices[i]
        node=doc['nodes'][i]
        if 'matrix' in node:m=np.array(node['matrix']).reshape(4,4).T
        else:
            x,y,z,w=node.get('rotation',[0,0,0,1]);m=np.eye(4)
            m[:3,:3]=np.array([[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w],[2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w],[2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y]])@np.diag(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0])
        matrices[i]=world(parents[i])@m if i in parents else m;return matrices[i]
    nodes={}
    for i,node in enumerate(doc['nodes']):
        if 'mesh' not in node:continue
        name=node.get('name',str(i))
        if name in nodes:raise ValueError('Duplicate mesh node '+name)
        triangles=[];points=[]
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            if primitive.get('mode',4)!=4:raise ValueError('Vehicle primitive must contain triangles')
            xyz=accessor(primitive['attributes']['POSITION']);xyz=(np.column_stack((xyz,np.ones(len(xyz))))@world(i).T)[:,:3];xyz=np.round(xyz,6);points.extend(xyz.tolist())
            indices=accessor(primitive['indices']).reshape(-1) if 'indices' in primitive else np.arange(len(xyz))
            for t in xyz[indices.reshape(-1,3)]:
                t=[tuple(p) for p in t];k=min(range(3),key=lambda j:t[j]);triangles.append(tuple(t[k:]+t[:k]))
        parent=doc['nodes'][parents[i]].get('name') if i in parents else None
        canonical=tuple(sorted(triangles));nodes[name]={'sha256':hashlib.sha256(repr(canonical).encode()).hexdigest(),'triangles':len(canonical),'parent':parent,'points':points}
    return nodes

def compare(civilian,police):
    c=mesh_nodes(civilian);p=mesh_nodes(police);missing=sorted(c.keys()-p.keys());different=sorted(n for n in c.keys()&p.keys() if c[n]['sha256']!=p[n]['sha256'] or c[n]['parent']!=p[n]['parent'])
    required=['body','glass_envelope','wheel_fl','wheel_fr','wheel_rl','wheel_rr']
    absent=[n for n in required if n not in c or n not in p]
    extras=sorted(p.keys()-c.keys());unexpected=[n for n in extras if not n.startswith(('lamp_blue_module','lamp_police_grille','trim_lightbar_base','trim_police_mount'))]
    fixtures=[n for n in c if n.startswith(('trim_rim','trim_spoke'))];unparented=[n for n in fixtures if not (c[n]['parent'] or '').startswith('wheel_')]
    arch=[point[0] for n,v in c.items() if n.startswith('trim_arch') for point in v['points']]
    return dict(ok=not (missing or different or absent or unexpected or unparented),common_meshes=len(c.keys()&p.keys()),identical_geometry=sorted(n for n in c.keys()&p.keys() if n not in different),differences=different,missing_in_police=missing,missing_required=absent,police_only=extras,unexpected_variant_geometry=unexpected,wheel_fixtures_without_wheel_parent=unparented,cladding_width_m=max(arch)-min(arch) if arch else None,body_sha256=c.get('body',{}).get('sha256'),method='Original glTF node names; every primitive triangle in world metres, cyclic winding retained; parent hierarchy compared. Materials/colour attributes intentionally excluded.')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('civilian',type=Path);parser.add_argument('police',type=Path);parser.add_argument('--report',type=Path,required=True);args=parser.parse_args();report=compare(args.civilian,args.police);args.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));return 0 if report['ok'] else 1
if __name__=='__main__':raise SystemExit(main())
