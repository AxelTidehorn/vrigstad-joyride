"""Mutation test: one edited rear-window source must propagate into both XC70 exports."""
from pathlib import Path
import sys,json,hashlib
import bpy
root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'experiments/xc70p2'));from variants import apply
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True);temp=Path(sys.argv[2]);temp.mkdir(parents=True,exist_ok=True)
canonical=root/'experiments/xc70p2/build/model.blend';disk_hash=hashlib.sha256(canonical.read_bytes()).hexdigest()
apply('civilian');shared=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render]
def signature():return hashlib.sha256(json.dumps({o.name:{'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(f.vertices) for f in o.data.polygons],'parent':o.parent.name if o.parent else None} for o in shared},sort_keys=True).encode()).hexdigest()
before=signature();changed=0
for name in ['body','glass_envelope']:
 for v in bpy.data.objects[name].data.vertices:
  if v.co.y<-2.08 and v.co.z>1.02 and abs(v.co.x)<.65:
   v.co.x*=1.002;changed+=1
apply('civilian');civil=signature();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str((temp/'civilian.blend').resolve()))
apply('police');police=signature();bpy.ops.wm.save_as_mainfile(filepath=str((temp/'police.blend').resolve()))
report={'ok':before!=civil and civil==police,'mutated_body_and_rear_glass_vertices':changed,'test_rear_aperture_x_scale':1.002,'unmodified_geometry_sha256':before,'civilian_mutated_sha256':civil,'police_mutated_sha256':police,'canonical_master_unchanged_on_disk':disk_hash==hashlib.sha256(canonical.read_bytes()).hexdigest(),'source':'One scene from model.py + round2.py; variants.apply changes only material/visibility. Temporary width perturbation is a test, not a delivered model correction.'}
(out/'architecture-mutation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report));assert report['ok'] and report['canonical_master_unchanged_on_disk']
