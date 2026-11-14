"""Before/after PNG comparison; update links without creating parallel models."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
p=Path(__file__).resolve().parent;b=p/'build';out=b/'detail-review';font=ImageFont.truetype('DejaVuSans.ttf',24)
for variant,stage,prefix in [('civilian','civilian','clay'),('police','police_decor','shaded')]:
 sheet=Image.new('RGB',(1800,1800),'#e9e6df');draw=ImageDraw.Draw(sheet)
 for row,view in enumerate(['side','front_three_quarter','rear_three_quarter']):
  for col,label in enumerate(['before','after']):
   file=out/'before'/(stage+'_'+view+'.png') if col==0 else b/stage/(prefix+'_'+view+'.png')
   im=Image.open(file).convert('RGBA');bg=Image.new('RGBA',im.size,'#e9e6df');bg.alpha_composite(im);im=bg.crop((0,220,1100,940));im.thumbnail((890,550));sheet.paste(im.convert('RGB'),(col*900,row*600+40));draw.text((col*900+15,row*600+10),variant.upper()+' '+label.upper()+' / '+view,font=font,fill='#253d36')
 sheet.save(out/(variant+'-before-after.png'))
r=json.loads((out/'audit.json').read_text());html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>XC70 · targeted detail correction</title><style>body{margin:0;background:#e9e6df;color:#253d36;font:18px system-ui}main{max-width:1500px;margin:auto;padding:24px}p{line-height:1.6;max-width:1000px}img{width:100%;height:auto}a{color:#24675f}nav a{display:inline-block;padding:12px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:700px){.pair{grid-template-columns:1fr}}</style><main><h1>XC70 P2 · glass, lamps and blue/white police paint</h1><p>Targeted correction of the existing shared-body master. Roof, wheelbase, ride height, wheels, bumpers, rails and lightbar retained. The JSON audit verifies unchanged bounds, central roof vertices and all preserved components.</p><nav><a href="../../index.html">Current variants and downloads</a><a href="audit.json">Geometry / preservation audit</a><a href="../../build/model.blend">Shared Blender</a></nav><p>Changes: seated full windshield; taller rear glass with thin upper/lower reveals; rear side glass extended 80 mm; shallow corner-conforming tail lenses; rectangular recessed headlamps; blue/white police paint only with full blue fender/quarter panels. POLIS lettering retained. Remaining: stylized opaque faceted glazing and simplified lamps. This is not a hollow manufactured tailgate; the closed body backing remains.</p>'''
for variant in ['civilian','police']:
 html+=f'<h2>{variant.title()} · before / after</h2><a href="{variant}-before-after.png"><img src="{variant}-before-after.png" alt="{variant} before after"></a><div class="pair">'
 for folder,file in [('glass_front','clay_windscreen.png'),('tail_fit','clay_tailglass_lamps.png')]:html+=f'<a href="{variant}/{folder}/{file}"><img src="{variant}/{folder}/{file}" alt="{variant} {folder}"></a>'
 html+='</div>'
html+='</main></html>';(out/'index.html').write_text(html)
