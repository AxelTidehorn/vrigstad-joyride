"""Shared mesh, material/visibility variants; safe to call on the master scene."""
from pathlib import Path
import bpy
HERE=Path(__file__).resolve().parent

def apply(name):
 body=bpy.data.objects['body'];civil=bpy.data.materials.get('XC70 configurable silver');police=bpy.data.materials.get('XC70 police white livery')
 if police is None:
  police=civil.copy();police.name='XC70 police white livery';bsdf=police.node_tree.nodes.get('Principled BSDF');tex=police.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(HERE/'police-livery.png'));tex.image.pack();police.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);police.diffuse_color=(.82,.84,.81,1)
 body.data.materials[0]=police if name=='police' else civil
 for col in ['POLICE','POLICE_DECALS']:
  for o in bpy.data.collections[col].objects:o.hide_render=name!='police';o.hide_viewport=name!='police'
 bpy.context.scene['variant']=name
