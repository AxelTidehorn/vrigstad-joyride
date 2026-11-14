"""Shared mesh, material/visibility variants; safe to call on the master scene."""
from pathlib import Path
import bpy
HERE=Path(__file__).resolve().parent

def apply(name):
 body=bpy.data.objects['body'];civil=bpy.data.materials.get('XC70 configurable silver');police=bpy.data.materials.get('XC70 police white livery')
 if police is None:
  police=civil.copy();police.name='XC70 police white livery';bsdf=police.node_tree.nodes.get('Principled BSDF')
  color=police.node_tree.nodes.new('ShaderNodeVertexColor');color.layer_name='VariantPaint'
  police.node_tree.links.new(color.outputs['Color'],bsdf.inputs['Base Color']);police.diffuse_color=(.82,.84,.81,1)
 # Point colours avoid UV projection across the hood/tailgate producing stray triangles.
 # Every face meeting a vertex gets the same colour, preserving the closed GLB shell.
 colors=body.data.color_attributes.get('VariantPaint')
 if colors is None:colors=body.data.color_attributes.new(name='VariantPaint',type='BYTE_COLOR',domain='POINT')
 for v in body.data.vertices:
  x,y,z=v.co
  panel=abs(x)>=.6999 and ((y>=.8399 and .64<=z<=1.16) or (y<=-1.20 and .64<=z<=1.09))
  colors.data[v.index].color_srgb=(31/255,85/255,149/255,1) if name=='police' and panel else ((229/255,231/255,227/255,1) if name=='police' else (1,1,1,1))
 body.data.materials[0]=police if name=='police' else civil
 for col in ['POLICE','POLICE_DECALS']:
  for o in bpy.data.collections[col].objects:o.hide_render=name!='police';o.hide_viewport=name!='police'
 bpy.context.scene['variant']=name
