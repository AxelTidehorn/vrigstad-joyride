"""Package the existing pipeline results, no modelling or publishing side effects."""
from pathlib import Path
import zipfile,json
here=Path(__file__).resolve().parent;car=here.parent;root=car.parents[1]
a=json.loads((here/'after/comparison/report.json').read_text());b=json.loads((here/'before/comparison/report.json').read_text())
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Saab 900 · hood verification</title><style>body{margin:0;background:#efeee8;color:#263d36;font:17px system-ui}main{max-width:1500px;margin:auto;padding:24px}h1{font-size:clamp(28px,4vw,44px)}p{max-width:1000px;line-height:1.6}a{color:#24635c}nav{display:flex;gap:12px;flex-wrap:wrap}nav a{padding:12px 15px;border:1px solid #9caea4;border-radius:7px;text-decoration:none}img{width:100%;height:auto;display:block}figure{margin:25px 0}figcaption{padding:8px 0;font-size:17px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}table{border-collapse:collapse;width:min(100%,950px);margin:24px 0}th,td{text-align:left;padding:13px;border-bottom:1px solid #c4cec5}.note{border-left:4px solid #aa7645;padding:12px 20px;background:#e6dfcf}.pair h3{margin-bottom:6px}@media(max-width:700px){main{padding:14px}.pair{grid-template-columns:1fr}table{font-size:14px}th,td{padding:9px}}</style><main><h1>Saab 900 Classic · hood &amp; cowl</h1><p>Measured before/after refinement of the latest Blender model. Rear hood raised into a coherent forward-falling wedge. A short geometric cowl replaces the rounded transition. Roof, rear, wheelbase and nose are preserved.</p><nav><a href="../preview.html">Rotate / zoom in 3D</a><a href="../build/model.blend">Updated Blender</a><a href="../build/saab900-t16.glb">Updated GLB</a><a href="saab900-silhouette-delivery.zip">Files &amp; scripts ZIP</a><a href="README.md">Full report</a><a href="../references.md">Sources</a></nav><p class="note">The real manufacturer drawing is a small 1985 pre-facelift three-door reference, not an exact 1988 T16 blueprint. Contour errors are comparison pixels, not verified millimetres. The later facelift photograph is qualitative evidence. No local Blender or other software is required. Physical iPad Safari FPS is untested.</p>'''
html+='<table><tr><th>Measurement</th><th>Before</th><th>After</th></tr>'
for title,v,w in [('Global IoU',b['global_metrics']['iou'],a['global_metrics']['iou']),('Hood mean absolute profile error (px)',b['local_metrics']['hood']['absolute_height_mean_px'],a['local_metrics']['hood']['absolute_height_mean_px']),('Hood maximum profile error (px)',b['local_metrics']['hood']['max_absolute_height_px'],a['local_metrics']['hood']['max_absolute_height_px']),('Roof mean absolute profile error (px)',b['local_metrics']['roof']['absolute_height_mean_px'],a['local_metrics']['roof']['absolute_height_mean_px'])]:
 html+=f'<tr><td>{title}</td><td>{v:.3f}</td><td>{w:.3f}</td></tr>'
html+='</table><p>7,822 triangles · 47 meshes · 8 materials. Body and GLB checks pass. Eleven numerical silhouette tests and five validator tests pass. All eleven preview tests pass; a test-only offscreen/visible-frame timing race was corrected.</p>'
for title,path in [('Side view','quality/clay_side.png'),('Front three-quarter','quality/clay_front_three_quarter.png'),('Hood / windshield base','cowl/clay_hood_windscreen.png'),('Contour overlay — red reference, cyan model','comparison/overlay.png'),('Deviation map — green 0 px, red 25+ px','comparison/deviation.png')]:
 html+=f'<h2>{title}</h2><div class="pair">'
 for stage in ['before','after']:html+=f'<section><h3>{stage.upper()}</h3><a href="{stage}/{path}"><img loading="lazy" src="{stage}/{path}" alt="{stage} {title}"></a></section>'
 html+='</div>'
html+='<h2>Physical surface sections</h2><p>Direct mesh profile, independent of materials or shading. Rear hood and short cowl have separate slopes; cyan is the updated mesh. These are real model changes, not claims of exact reference dimensions.</p><a href="surface-breaks.png"><img loading="lazy" src="surface-breaks.png" alt="Actual Blender surface profiles"></a><h2>Region checks</h2>'
for region in ['hood','windscreen','roof','rear']:
 html+=f'<details><summary>{region.title()} — before / after</summary><div class="pair">'
 for stage in ['before','after']:html+=f'<a href="{stage}/comparison/region-{region}.png"><img loading="lazy" src="{stage}/comparison/region-{region}.png" alt="{stage} {region}"></a>'
 html+='</div></details>'
html+='<h2>Review sheets and machine-readable evidence</h2><nav>'
for path,label in [('comparison-sheet.png','PNG: model comparison'),('contour-sheet.png','PNG: contour comparison'),('before/comparison/report.json','Before JSON'),('after/comparison/report.json','After JSON'),('change-audit.json','Model change audit'),('tests.txt','Numerical tests'),('saab900.json','Vehicle configuration')]:html+=f'<a href="{path}">{label}</a>'
html+='</nav><h2>Reference</h2><p>Saab-Scania AB, 1985, Danish Saab 900/900i brochure rear-cover three-door illustration. Small technical review excerpt; no game-asset licence claimed. Manual mask excludes mirrors, bumper extensions and spoiler. Perspective photographs are in the source notes.</p><img loading="lazy" src="reference.png" alt="Manufacturer three-door reference, pre-facelift"><p>The comparison still shows differences around the windscreen and nose; exact year-specific accuracy remains unverified. No game integration or Volvo changes.</p></main></html>'
(here/'index.html').write_text(html)
with zipfile.ZipFile(here/'saab900-silhouette-delivery.zip','w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted(here.rglob('*')):
  if f.is_file() and f.suffix not in ('.zip','.pyc') and '__pycache__' not in f.parts:z.write(f,f.relative_to(root))
 for name in ['model.py','parameters.json','vehicle.json','README.md','references.md','build/model.blend','build/saab900-t16.glb','build/geometry.json','build/reimport.json','build/report.json','build/supplemental.json','build/three-loader.json']:
  f=car/name;z.write(f,f.relative_to(root))
 for f in sorted((root/'tools/vehicle_pipeline').glob('*')):
  if f.is_file():z.write(f,f.relative_to(root))
 z.write(root/'LICENSE','LICENSE')
print('Static review and source package updated')
