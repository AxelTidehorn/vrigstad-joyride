"""Package the bounded block-lamp refinement with reproducible image comparisons."""
from pathlib import Path
import json,struct,shutil
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent;b=p/'build';out=b/'block-review';font=ImageFont.truetype('DejaVuSans.ttf',24)
def tile(path,box,crop=False):
 im=Image.open(path).convert('RGBA');bg=Image.new('RGBA',im.size,'#e9e6df');bg.alpha_composite(im)
 if crop:bg=bg.crop((0,220,1100,940))
 bg.thumbnail(box);return bg.convert('RGB')
for variant,stage,prefix in [('civilian','civilian','clay'),('police','police_decor','shaded')]:
 sheet=Image.new('RGB',(1800,1800),'#e9e6df');draw=ImageDraw.Draw(sheet)
 for row,view in enumerate(['side','front_three_quarter','rear_three_quarter']):
  for col,label in enumerate(['before','after']):
   file=out/'before'/(stage+'_'+view+'.png') if col==0 else b/stage/(prefix+'_'+view+'.png')
   sheet.paste(tile(file,(890,550),True),(col*900,row*600+40));draw.text((col*900+15,row*600+10),variant.upper()+' '+label.upper()+' / '+view.replace('_',' '),font=font,fill='#253d36')
 sheet.save(out/(variant+'-before-after.png'))
sheet=Image.new('RGB',(1800,960),'#e9e6df');draw=ImageDraw.Draw(sheet)
for col,(label,file) in enumerate([('BEFORE',out/'before/tail-closeup.png'),('AFTER',out/'civilian/tail_fit/clay_tailglass_lamps.png')]):
 sheet.paste(tile(file,(890,890)),(col*900,50));draw.text((col*900+20,12),label+' / rear lamp seating',font=font,fill='#253d36')
sheet.save(out/'tail-before-after.png')
# Inspect the exported glTF structure, not just Blender visibility settings.
export={}
for variant in ['civilian','police']:
 data=(b/('xc70-'+variant+'.glb')).read_bytes();size=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+size])
 labels=[x.get('name','') for key in ['nodes','meshes','materials','images'] for x in g.get(key,[])]
 assert not any('polis' in n.lower() for n in labels),labels
 assert not g.get('images'),g.get('images')
 export[variant]=dict(no_POLIS_nodes_or_materials=True,no_texture_images=True,triangles=json.loads((b/variant/'geometry.json').read_text())['triangles'])
shutil.copyfile(b/'detail-review/paint-audit.json',out/'paint-audit.json')
(out/'export-audit.json').write_text(json.dumps(export,indent=2)+'\n')
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>XC70 · block tail lamps</title><style>body{margin:0;background:#e9e6df;color:#253d36;font:18px system-ui}main{max-width:1600px;margin:auto;padding:24px}p{line-height:1.6;max-width:1050px}img{width:100%;height:auto}a{color:#24675f}nav a{display:inline-block;padding:12px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:700px){.pair{grid-template-columns:1fr}}</style><main><h1>XC70 P2 · integrated block tail lamps</h1><p>Latest refinement of the existing shared master. Flat rear-facing red/ivory blocks replace the narrow corner-wrapped lenses. The housings taper into the body, with most of their depth embedded. All POLIS lettering is removed; blue/white body paint, fully blue fender/quarter panels and lightbar remain.</p><nav><a href="../../index.html">Current models / downloads</a><a href="../../preview.html">Touch 3D viewer</a><a href="../../build/model.blend">Shared Blender master</a><a href="../../build/xc70-civilian.glb">Civilian GLB</a><a href="../../build/xc70-police.glb">Police GLB</a></nav><h2>Rear close-up · before / after</h2><a href="tail-before-after.png"><img src="tail-before-after.png" alt="Rear lamps before and after"></a><p>Same fixed camera and scale. Only the two rear-lamp meshes changed; four text meshes were removed. Body and glazing vertices, topology and transforms are identical to the previous master, as are wheels, bumpers, roof rails and police equipment. No general body rounding or smoothing change.</p>'''
for variant in ['civilian','police']:
 html+=f'<h2>{variant.title()} · before / after</h2><a href="{variant}-before-after.png"><img loading="lazy" src="{variant}-before-after.png" alt="{variant} side front and rear three-quarter before and after"></a>'
html+='''<h2>Verified results and limits</h2><p>Closed, consistently wound body and rear-lamp solids; no degenerate faces or BVH self-intersection candidates. Both GLBs pass repository validation, Blender reimport and the existing Three.js loader. The civilian and police cars share identical common geometry. Blue body vertex colours over both axles are verified in the export. No text nodes, texture images or yellow paint remain in the current GLBs. Physical iPad/Safari GPU performance is untested.</p><p>Remaining simplifications: opaque faceted glazing, broad bumper corners, soft wheel-arch shading and simplified lamp optics. The larger rear lights are a deliberate stylized block interpretation, not an exact manufactured lens reconstruction. Body geometry was preserved rather than broadly reworked.</p><nav><a href="audit.json">Geometry / preservation / seating audit</a><a href="paint-audit.json">Blue fender/quarter export audit</a><a href="export-audit.json">Export text-removal audit</a><a href="../shared-export-geometry.json">Common geometry proof</a><a href="../civilian/geometry.json">Civilian validation</a><a href="../police/geometry.json">Police validation</a></nav></main></html>'''
(out/'index.html').write_text(html)
print('Block refinement review and export audit ready')
