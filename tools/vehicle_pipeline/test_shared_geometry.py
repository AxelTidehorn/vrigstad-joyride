"""Actual binary GLB fixtures cover shared multi-material lamps and wheel hierarchy."""
import json,struct,tempfile,unittest
from pathlib import Path
from compare_shared_geometry import compare

def fixture(path,change=None):
    points=struct.pack('<9f',0,0,0,1,0,0,0,1,0);indices=struct.pack('<3H',0,1,2);binary=points+indices+b'\0\0'
    names=['body','glass_envelope','wheel_fl','wheel_fr','wheel_rl','wheel_rr','lamp_tail','trim_rim_fl']
    nodes=[{'name':n,'mesh':0} for n in names];nodes[2]['children']=[7];nodes[6]['mesh']=1
    doc={'asset':{'version':'2.0'},'buffers':[{'byteLength':len(binary)}],'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':36},{'buffer':0,'byteOffset':36,'byteLength':6}],'accessors':[{'bufferView':0,'componentType':5126,'count':3,'type':'VEC3'},{'bufferView':1,'componentType':5123,'count':3,'type':'SCALAR'}],'nodes':nodes,'meshes':[{'primitives':[{'attributes':{'POSITION':0},'indices':1,'material':0}]},{'primitives':[{'attributes':{'POSITION':0},'indices':1,'material':0},{'attributes':{'POSITION':0},'indices':1,'material':1}]}],'materials':[{'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1]}},{}],'scenes':[{'nodes':list(range(7))}],'scene':0}
    if change:change(doc)
    text=json.dumps(doc).encode();text+=b' '*((-len(text))%4)
    data=struct.pack('<III',0x46546c67,2,12+8+len(text)+8+len(binary))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(binary),0x004e4942)+binary;path.write_bytes(data)

class SharedGeometryTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.a=Path(self.temp.name)/'a.glb';self.b=Path(self.temp.name)/'b.glb';fixture(self.a)
    def tearDown(self):self.temp.cleanup()
    def test_material_change_and_multimaterial_lamp_pass(self):
        fixture(self.b,lambda d:d['materials'][0]['pbrMetallicRoughness'].update(baseColorFactor=[0,0,1,1]));r=compare(self.a,self.b);self.assertTrue(r['ok']);self.assertIn('lamp_tail',r['identical_geometry'])
    def test_changed_glass_fails(self):
        fixture(self.b,lambda d:d['nodes'][1].update(translation=[.01,0,0]));self.assertEqual(compare(self.a,self.b)['differences'],['glass_envelope'])
    def test_changed_multimaterial_lamp_fails(self):
        fixture(self.b,lambda d:d['nodes'][6].update(translation=[0,.02,0]));self.assertEqual(compare(self.a,self.b)['differences'],['lamp_tail'])
    def test_missing_lamp_fails(self):
        fixture(self.b,lambda d:d['nodes'][6].pop('mesh'));self.assertIn('lamp_tail',compare(self.a,self.b)['missing_in_police'])
    def test_rim_parent_regression_fails(self):
        fixture(self.b,lambda d:d['nodes'][2].pop('children'));self.assertIn('trim_rim_fl',compare(self.a,self.b)['differences'])
    def test_unexpected_independent_variant_mesh_fails(self):
        fixture(self.b,lambda d:d['nodes'].append({'name':'independent_police_glass','mesh':0}));self.assertFalse(compare(self.a,self.b)['ok'])

if __name__=='__main__':unittest.main()
