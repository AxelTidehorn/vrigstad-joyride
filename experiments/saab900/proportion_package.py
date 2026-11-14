"""Package existing Blender pipeline results for the private static review page."""
from pathlib import Path
import json,zipfile
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent;root=p.parents[1];r=p/'proportion-review';b=p/'build'
views=['side','front_three_quarter','rear_three_quarter'];font=ImageFont.truetype('DejaVuSans.ttf',25)
sheet=Image.new('RGB',(1800,1900),'#e9e6df');d=ImageDraw.Draw(sheet)
for row,view in enumerate(views):
 for col,stage in enumerate(['before','after']):
  file=r/stage/'views'/('clay_'+view+'.png');im=Image.open(file).convert('RGBA');bg=Image.new('RGBA',im.size,'#e9e6df');bg.alpha_composite(im);im=bg.crop((0,260,1200,1000));im.thumbnail((890,560));sheet.paste(im.convert('RGB'),(col*900,row*630+45));d.text((col*900+20,row*630+10),stage.upper()+' / '+view.replace('_',' '),font=font,fill='#243e38')
sheet.save(r/'before-after.png')
records={s:json.loads((r/s/'comparison/report.json').read_text()) for s in ['before','after']}
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Saab 900 · profile refinement</title><style>body{margin:0;background:#e9e6df;color:#243e38;font:18px system-ui}main{max-width:1500px;padding:24px;margin:auto}p{max-width:1000px;line-height:1.6}a{color:#24685e}nav a{display:inline-block;padding:12px}img{width:100%;height:auto}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}table{border-collapse:collapse;max-width:100%;margin:25px 0}td,th{padding:12px;border-bottom:1px solid #aebbb2;text-align:left}.note{padding:15px;border-left:4px solid #98734b;background:#e0dbcf}@media(max-width:700px){.pair{grid-template-columns:1fr}main{padding:14px}td,th{padding:8px;font-size:15px}}</style><main><h1>Saab 900 Classic · profile refinement</h1><p>The existing hood-corrected model, refined in place. Cabin and windscreen moved forward; longer, calmer roof; defined roof/hatch break; shorter quarter glass and planar side windows. Same wheels, wheelbase, nose and overall dimensions.</p><nav><a href="../preview.html">Touch 3D viewer</a><a href="../build/model.blend">Updated Blender</a><a href="../build/saab900-t16.glb">Updated GLB</a><a href="../build/saab900-delivery.zip">Source &amp; model package</a><a href="README.md">Full report</a><a href="../references.md">Sources</a><a href="before-after.png">PNG comparison sheet</a><a href="change-audit.json">Direct geometry audit</a></nav><p class="note">Real references, no AI image target. The manufacturer sketch is a small pre-facelift illustration; exact 1988 metric shape approval is unavailable. Errors below are comparison pixels, not verified millimetres. Hood error rises slightly while windscreen, roof and rear improve. Human recognition judgement remains essential.</p>'''
html+='<table><tr><th>Measurement</th><th>Before</th><th>After</th></tr>'
for label,key in [('Global IoU',None),('Hood profile error (px)','hood'),('Windscreen profile error (px)','windscreen'),('Roof profile error (px)','roof'),('Rear profile error (px)','rear')]:
 values=[records[s]['global_metrics']['iou'] if key is None else records[s]['local_metrics'][key]['absolute_height_mean_px'] for s in ['before','after']];html+=f'<tr><td>{label}</td><td>{values[0]:.3f}</td><td>{values[1]:.3f}</td></tr>'
html+='</table><p>7,758 triangles · 47 meshes · 8 materials. Closed-body/normal/degeneracy/BVH checks and actual GLB export/reimport pass. Side-glass planarity is measured from real vertices; the shape change is not simulated by materials. Remaining compromises: wheel-well smoothing, simplified lamp/seam details, opaque glazing. No game integration or physical iPad FPS claim.</p>'
for view in views:
 html+='<h2>'+view.replace('_',' ').title()+'</h2><div class="pair">'
 for stage in ['before','after']:html+=f'<section><h3>{stage.upper()}</h3><a href="{stage}/views/clay_{view}.png"><img src="{stage}/views/clay_{view}.png" alt="{stage} {view}"></a></section>'
 html+='</div>'
html+='<h2>Cabin / windshield / side-glass mass</h2><div class="pair">'
for stage in ['before','after']:html+=f'<a href="{stage}/cabin/clay_cabin.png"><img loading="lazy" src="{stage}/cabin/clay_cabin.png" alt="{stage} cabin"></a>'
html+='</div><h2>Wheelbase-registered reference comparisons</h2><p>Red: manual real-reference contour. Cyan: actual orthographic Blender silhouette. Same registration and regions before/after.</p><div class="pair">'
for stage in ['before','after']:
 html+=f'<section><h3>{stage.upper()}</h3><a href="{stage}/comparison/overlay.png"><img loading="lazy" src="{stage}/comparison/overlay.png" alt="{stage} overlay"></a><a href="{stage}/comparison/deviation.png"><img loading="lazy" src="{stage}/comparison/deviation.png" alt="{stage} deviations"></a><a href="{stage}/comparison/report.json">JSON measurements</a></section>'
html+='</div><h2>Reference evidence</h2><p>Saab-Scania manufacturer illustration, copyright 1985, small technical-review excerpt; Alexander Migl / Wikimedia Commons front three-quarter, CC BY-SA 4.0. Full source register linked above. The photograph checks facelift form qualitatively; perspective is not used as exact geometry.</p><img loading="lazy" src="../silhouette/reference.png" alt="Real manufacturer three-door sketch"><img loading="lazy" src="../references/rear.png" alt="Real facelift Turbo reference"></main></html>'
(r/'index.html').write_text(html)
# Keep the established entry points pointing at the current review without changing viewer code.
for file in ['index.html','preview.html']:
 f=p/file;s=f.read_text();marker='proportion-review/index.html'
 if marker not in s:
  if file=='index.html':s=s.replace('<nav>','<nav><a href="proportion-review/index.html">Current profile · before / after</a>',1)
  else:s=s.replace('<summary>Filer, jämförelser och rapport</summary>','<summary>Filer, jämförelser och rapport</summary><p><a href="proportion-review/index.html">Current Saab profile · before / after</a></p>',1)
 s=s.replace('7 822','7 758');f.write_text(s)
with zipfile.ZipFile(b/'saab900-delivery.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in ['model.py','parameters.json','vehicle.json','README.md','references.md','proportion_review.py','proportion_audit.py','proportion_package.py','build/model.blend','build/saab900-t16.glb','build/geometry.json','build/reimport.json','build/three-loader.json','build/report.json']:
  f=p/name;z.write(f,f.relative_to(root))
 for f in r.rglob('*'):
  rel=f.relative_to(r).as_posix()
  chosen=f.suffix in ('.json','.md','.html','.txt') or rel=='before-after.png' or '/views/clay_' in rel or rel.endswith(('comparison/overlay.png','comparison/deviation.png'))
  if f.is_file() and '__pycache__' not in f.parts and chosen:z.write(f,f.relative_to(root))
 for f in (root/'tools/vehicle_pipeline').glob('*'):
  if f.is_file():z.write(f,f.relative_to(root))
 z.write(p/'silhouette/reference.png','experiments/saab900/silhouette/reference.png')
 z.write(root/'LICENSE','LICENSE')
print('Current Saab profile review and compact model/source package ready')
