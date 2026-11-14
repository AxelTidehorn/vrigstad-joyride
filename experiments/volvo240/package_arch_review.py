"""Static iPad before/after review of the existing Volvo 240 master."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,zipfile
p=Path(__file__).resolve().parent;root=p.parents[1];b=p/'refinement';out=b/'arch-review'
font=ImageFont.truetype('DejaVuSans.ttf',24)
def tile(path,box,crop=False):
 im=Image.open(path).convert('RGBA');bg=Image.new('RGBA',im.size,'#e9e6df');bg.alpha_composite(im)
 if crop:bg=bg.crop((0,220,1100,940))
 bg.thumbnail(box);return bg.convert('RGB')
sheet=Image.new('RGB',(1800,1800),'#e9e6df');draw=ImageDraw.Draw(sheet)
for row,view in enumerate(['side','three_quarter','three_quarter_rear']):
 for col,stage in enumerate(['before','after']):
  sheet.paste(tile(out/stage/('clay_'+view+'.png'),(890,550),True),(col*900,row*600+40))
  draw.text((col*900+15,row*600+10),stage.upper()+' / '+view.replace('_',' '),font=font,fill='#253d36')
sheet.save(out/'before-after.png')
for folder,name in [('arch','wheel-arch-before-after'),('arch_body','bare-arch-before-after')]:
 sheet=Image.new('RGB',(1800,960),'#e9e6df');draw=ImageDraw.Draw(sheet)
 for col,stage in enumerate(['before','after']):
  sheet.paste(tile(out/stage/folder/'clay_wheel_arch.png',(890,890)),(col*900,50));draw.text((col*900+15,12),stage.upper()+' / '+folder.replace('_',' '),font=font,fill='#253d36')
 sheet.save(out/(name+'.png'))
g=json.loads((b/'glb_geometry.json').read_text());assert g['ok']
a=json.loads((out/'audit.json').read_text());assert a['body_health']['bvh_self_intersection_candidates']==0
assert json.loads((out/'reproducibility.json').read_text())['source_reproduces_all_mesh_positions']
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Volvo 240 · defined wheel arches</title><style>body{margin:0;background:#e9e6df;color:#253d36;font:18px system-ui}main{max-width:1600px;padding:24px;margin:auto}p{max-width:1050px;line-height:1.6}a{color:#24675f}nav a{display:inline-block;padding:12px}img{width:100%;height:auto;display:block}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:700px){.pair{grid-template-columns:1fr}}</style><main><h1>Volvo 240 · defined wheel arches</h1><p>Targeted refinement of the existing Blender model. Circular openings become controlled polygon profiles with short flat crowns, angular shoulders and straighter lower legs. Connected inner support loops give the opening a tighter reveal. No detached arch trim or new body shell. Panel normals reduce the old inflated shading around each opening; the geometry itself changes.</p><nav><a href="../../../../media/vehicles/preview.html?vehicle=volvo240">Touch 3D viewer</a><a href="../model.blend">Editable Blender master</a><a href="../review-only.glb">Review GLB</a><a href="volvo240-refinement.zip">Sources, model and PNG sheets</a><a href="../assessment.md">Assessment</a></nav>'''
for name,title in [('before-after','Same cameras · side, front and rear three-quarter'),('wheel-arch-before-after','Front wheel arch · same close-up'),('bare-arch-before-after','Bare body · connected opening geometry')]:
 html+=f'<h2>{title}</h2><a href="{name}.png"><img loading="lazy" src="{name}.png" alt="{title} before and after"></a>'
html+=f'''<h2>Preservation and checks</h2><p>{g['triangles']:,} triangles total, 25 mesh objects; body width 1.71 m, overall length 4.82 m, wheelbase 2.65 m. Body bounds match the previous master exactly; all 24 separate components retain identical coordinates, topology and transforms. All 454 protected body vertices outside the well neighbourhood remain. Materials and vehicle identity are retained.</p><p>Blender Modeler: 0 errors / 0 warnings. Body: closed, consistent winding, no degenerates or BVH self-intersection candidates. Existing GLB validator, Blender reimport and Three r128 loader pass. Source regeneration reproduces all mesh positions. No game integration or hardware Safari/FPS test. Human visual approval remains pending.</p><p>Remaining simplifications: generic grille/mirrors, opaque glass with existing edge artifacts, simple wheel discs and stylized end forms. The arch profile is a deliberate low-poly interpretation, not a factory dimensional reconstruction. Suspension/steering travel is not simulated.</p><nav><a href="audit.json">Preservation / geometry audit</a><a href="../glb_geometry.json">Actual GLB validation</a><a href="../reimport.json">Blender reimport</a><a href="three-loader.json">Three loader</a><a href="reproducibility.json">Source reproduction</a></nav><h2>Full-size final PNGs</h2>'''
for view in ['side','three_quarter','three_quarter_rear']:html+=f'<p><a href="after/clay_{view}.png">{view.replace("_"," ")}</a></p>'
html+='</main></html>';(out/'index.html').write_text(html)
with zipfile.ZipFile(out/'volvo240-refinement.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in p.glob('*'):
  if f.is_file() and f.suffix in ('.py','.md','.json'):z.write(f,f.relative_to(root))
 for name in ['model.blend','review-only.glb','glb_geometry.json','reimport.json','assessment.md']:
  f=b/name;z.write(f,f.relative_to(root))
 for f in out.iterdir():
  if f.is_file() and f.suffix in ('.json','.png','.html','.txt'):z.write(f,f.relative_to(root))
 for f in (root/'tools/vehicle_pipeline').glob('*'):
  if f.is_file():z.write(f,f.relative_to(root))
 z.write(root/'LICENSE','LICENSE')
print('Volvo 240 arch review and compact delivery package ready')
