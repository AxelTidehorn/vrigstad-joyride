"""Inspect actual GLB point colours in the requested full fender/quarter regions."""
from pathlib import Path
import struct,json
import numpy as np
p=Path(__file__).resolve().parent/'build'
def glb(file):
 raw=file.read_bytes();length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);offset=20+length;size=struct.unpack_from('<I',raw,offset)[0];return doc,raw[offset+8:offset+8+size]
def array(doc,data,index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];dtype={5126:'<f4',5121:'u1',5123:'<u2'}[a['componentType']];n={'VEC3':3,'VEC4':4}[a['type']];item=np.dtype(dtype).itemsize;stride=v.get('byteStride',n*item);offset=v.get('byteOffset',0)+a.get('byteOffset',0)
 x=np.ndarray((a['count'],n),dtype=dtype,buffer=data,offset=offset,strides=(stride,item)).astype(float)
 if a.get('normalized') and a['componentType']!=5126:x/=np.iinfo(np.dtype(dtype)).max
 return x
reports={}
for variant in ['civilian','police']:
 doc,data=glb(p/f'xc70-{variant}.glb');node=next(n for n in doc['nodes'] if n.get('name')=='body');primitive=doc['meshes'][node['mesh']]['primitives'][0];attrs=primitive['attributes'];positions=array(doc,data,attrs['POSITION'])
 if variant=='police':
  colors=array(doc,data,attrs['COLOR_0']);blue=(colors[:,2]>colors[:,0]+.05)&(colors[:,2]>colors[:,1]+.05)
  # Export orientation: X right, Y up, -Z forward.
  masks={'front_fender':(abs(positions[:,0])>.71)&(-positions[:,2]>1.)&(-positions[:,2]<1.7)&(positions[:,1]>.75)&(positions[:,1]<1.04),
         'rear_quarter':(abs(positions[:,0])>.71)&(-positions[:,2]<-1.21)&(-positions[:,2]>-1.9)&(positions[:,1]>.75)&(positions[:,1]<1.04)}
  for name,mask in masks.items():assert mask.any() and blue[mask].all(),name
  unique=np.unique(np.round(colors[:,:3],3),axis=0)
  assert len(unique)==2,unique
  assert not ((colors[:,0]>.2)&(colors[:,1]>.2)&(colors[:,2]<.1)).any(),'yellow found'
  reports[variant]={'blue_vertex_counts':{k:int(v.sum()) for k,v in masks.items()},'palette_linear_rgb':unique.tolist(),'yellow_vertices':0}
 else:
  reports[variant]={'body_vertex_colours_white':True if 'COLOR_0' not in attrs else bool(np.all(array(doc,data,attrs['COLOR_0'])[:,:3]>.99))}
  assert reports[variant]['body_vertex_colours_white']
(p/'detail-review/paint-audit.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))
