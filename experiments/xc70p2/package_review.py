"""Build static iPad review sheets and package from the existing pipeline outputs."""
from pathlib import Path
import json,zipfile,re,shutil
from PIL import Image,ImageDraw,ImageFont
p=Path(__file__).resolve().parent;root=p.parents[1];b=p/'build'
views=['side','front_three_quarter','rear_three_quarter','front','rear'];font=ImageFont.truetype('DejaVuSans.ttf',25)
sheet=Image.new('RGB',(1800,3100),'#e9e6df');draw=ImageDraw.Draw(sheet)
for col,variant in enumerate(['civilian','police']):
 for row,v in enumerate(views):
  f=b/('police_decor' if variant=='police' else 'civilian')/(('shaded_' if variant=='police' else 'clay_')+v+'.png')
  im=Image.open(f).convert('RGBA');bg=Image.new('RGBA',im.size,'#e9e6df');bg.alpha_composite(im);bg.convert('RGB').save(f)
  im=bg.crop((0,220,1100,940));im.thumbnail((890,570));sheet.paste(im.convert('RGB'),(col*900,row*620+40));draw.text((col*900+20,row*620+10),variant.upper()+' · '+v.replace('_',' '),font=font,fill='#243e38')
sheet.save(b/'variant-comparison.png')
# Existing touch viewer and controls, no game-code changes.
html=(root/'experiments/saab900/preview.html').read_text()
html=re.sub(r'<select id="vehicle">.*?</select>','<select id="vehicle"><option value="civilian">XC70 civilian</option><option value="police">XC70 Swedish police</option></select>',html,flags=re.S)
html=html.replace('experiments/volvo240/review-sheet.png','build/variant-comparison.png').replace('Complete Saab 900 Classic candidate.','XC70 P2 civilian and Swedish police candidates.').replace('Saab 900 Turbo 16','Volvo XC70 P2').replace('build/C_complete/clay_front_three_quarter.png','build/civilian/clay_front_three_quarter.png')
html=re.sub(r'<details>.*?</details>','<details><summary>Review files</summary><p><a href="index.html">Both variants, references and reports</a></p></details>',html,flags=re.S)
(p/'preview.html').write_text(html)
js=(root/'experiments/saab900/preview.js').read_text()
js=re.sub(r'const assets=\{.*?\};',"const assets={civilian:{file:'build/xc70-civilian.glb',rotation:0,length:null,label:'XC70 P2 civilian'},police:{file:'build/xc70-police.glb',rotation:0,length:null,label:'XC70 P2 Swedish police'}};",js,count=1,flags=re.S).replace("'saab900'","'civilian'")
(p/'preview.js').write_text(js)
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>XC70 P2 · civilian &amp; Swedish police</title><style>body{margin:0;background:#e9e6df;color:#243e38;font:18px system-ui}main{max-width:1500px;padding:22px;margin:auto}p{line-height:1.6;max-width:1000px}nav{display:flex;flex-wrap:wrap;gap:12px}a{color:#235f58}nav a{padding:13px;border:1px solid #8a9b91;border-radius:6px}img{width:100%;height:auto;display:block;margin:18px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:700px){.pair{grid-template-columns:1fr}}.note{padding:15px;border-left:4px solid #9b754d;background:#ded8c9}</style><main><h1>Volvo XC70 P2 · two shared-body variants</h1><p>MY2005–2006 civilian silver and a simplified Swedish police configuration. One closed body, one geometry source, variant paint and equipment. Five fixed views per car; tap any image for its full PNG.</p><nav><a href="preview.html">Touch 3D: rotate / zoom / fixed views</a><a href="build/model.blend">Shared Blender master</a><a href="build/xc70-civilian.glb">Civilian GLB</a><a href="build/xc70-police.glb">Police GLB</a><a href="build/xc70-delivery.zip">Source &amp; model package</a><a href="README.md">Report</a><a href="references.md">References / licences</a></nav><p class="note">Exact factory geometry and physical iPad GPU performance are unverified. The side reference has perspective and predates the facelift; police decoration is an approximate post-2005 scheme supported by later P2 service photos. No game integration. Known limits: simplified rear lamps/bumper corners, rear track equal to front, omitted crest/fleet codes/window strips, and some render noise.</p>'''
report=json.loads((b/'variants.json').read_text());html+='<p>'+' · '.join(f'{v}: {report[v]["triangles"]:,} triangles, {report[v]["visible_meshes"]} mesh nodes' for v in ['civilian','police'])+f'. Identical body hash: {report["same_body"]}.</p>'
for v in views:
 html+='<h2>'+v.replace('_',' ').title()+'</h2><div class="pair">'
 for variant in ['civilian','police']:
  path=('police_decor/shaded_' if variant=='police' else 'civilian/clay_')+v+'.png';html+=f'<section><h3>{variant.title()}</h3><a href="build/{path}"><img loading="lazy" src="build/{path}" alt="{variant} {v}"></a></section>'
 html+='</div>'
html+='<h2>Reference-based silhouette comparison</h2><p>Uniform wheel-centre registration at 2763 mm wheelbase. IoU 0.897 → 0.914, roof mean profile error 12.70 → 0.76 canonical pixels; hood 6.50 px unchanged. Rear residual is reported separately. No exact millimetre verdict from this photographic proxy.</p><div class="pair">'
for stage in ['baseline','silhouette']:html+=f'<section><h3>{stage}</h3><a href="build/{stage}/comparison/overlay.png"><img loading="lazy" src="build/{stage}/comparison/overlay.png" alt="{stage} overlay"></a><a href="build/{stage}/comparison/deviation.png"><img loading="lazy" src="build/{stage}/comparison/deviation.png" alt="{stage} deviation"></a><a href="build/{stage}/comparison/report.json">JSON measurements</a></section>'
html+='</div><nav><a href="build/variant-comparison.png">PNG review sheet</a><a href="build/variants.json">Shared geometry proof</a><a href="build/civilian/geometry.json">Civilian geometry</a><a href="build/police/geometry.json">Police geometry</a></nav><h2>Reference evidence</h2><p>Volvo technical study excerpts; Bull-Doser public-domain front photographs; Ethan Llamas rear photo (CC BY-SA 4.0); Per Enström / Plrk police reference (CC BY-SA 4.0). Details and source links in the reference register.</p>'
for name in ['side.png','front.jpg','rear.png','rear-three-quarter.jpg','police-new.jpg']:html+=f'<img loading="lazy" src="references/{name}" alt="Reference {name}">'
html+='</main></html>';(p/'index.html').write_text(html)
with zipfile.ZipFile(b/'xc70-delivery.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(p.rglob('*')):
  if f.is_file() and f.suffix not in ('.zip','.blend1','.pyc') and '__pycache__' not in f.parts and f.name not in ('civilian.blend','police.blend'):z.write(f,f.relative_to(root))
 for f in (root/'tools/vehicle_pipeline').glob('*'):
  if f.is_file():z.write(f,f.relative_to(root))
 z.write(root/'LICENSE','LICENSE')
print('XC70 review, PNG sheet and package ready')
