"""Package actual matched Blender renders and machine checks, without visual approval claims."""
from pathlib import Path
import json,hashlib,zipfile
from PIL import Image,ImageDraw,ImageFont,ImageOps
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'review';OUT.mkdir(exist_ok=True)
BG=(237,234,224);INK=(35,49,45)
def font(n):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
def flat(p):
 im=Image.open(p).convert('RGBA');bg=Image.new('RGBA',im.size,(*BG,255));bg.alpha_composite(im);return bg.convert('RGB')
views=['side','front','rear','front_three_quarter','rear_three_quarter','high_three_quarter','bed_overhead']
labels=['Exact orthographic side','Front','Rear','Front three-quarter','Rear three-quarter','High three-quarter','Open bed overhead']
canvas=Image.new('RGB',(1800,2230),BG);d=ImageDraw.Draw(canvas);d.text((24,20),'VOLVO DUETT P210 · EPA PICKUP',font=font(36),fill=INK)
for i,(n,label) in enumerate(zip(views,labels)):
 im=flat(HERE/f'build/views/shaded_{n}.png');im.save(OUT/f'{n}.png',optimize=True)
 bbox=Image.open(HERE/f'build/views/shaded_{n}.png').convert('RGBA').getchannel('A').getbbox()
 box=(max(0,bbox[0]-25),max(0,bbox[1]-25),min(1000,bbox[2]+25),min(1000,bbox[3]+25))
 im=ImageOps.contain(im.crop(box),(875,460));x=i%2*900;y=95+i//2*515;canvas.paste(im,(x+(900-im.width)//2,y+35));d.text((x+24,y),label,font=font(26),fill=INK)
d.text((24,2170),'Actual Cycles renders · 2.600 m wheelbase · conversion dimensions estimated · visual approval pending',font=font(23),fill=INK);canvas.save(OUT/'contact-sheet.png',optimize=True)
assert json.loads((HERE/'blockout/views/cameras.json').read_text())==json.loads((HERE/'build/views/cameras.json').read_text())
canvas=Image.new('RGB',(1800,1730),BG);d=ImageDraw.Draw(canvas);d.text((24,18),'FIRST BLOCKOUT → REFINED PICKUP · IDENTICAL CAMERAS',font=font(31),fill=INK)
for row,n in enumerate(['side','front_three_quarter','rear_three_quarter']):
 for col,stage in enumerate(['blockout','build']):
  im=ImageOps.contain(flat(HERE/f'{stage}/views/shaded_{n}.png').crop((0,150,1000,920)),(875,470));x=col*900;y=90+row*530;canvas.paste(im,(x+(900-im.width)//2,y+35));d.text((x+24,y),('Blockout' if col==0 else 'Final')+' · '+n.replace('_',' '),font=font(24),fill=INK)
canvas.save(OUT/'before-after.png',optimize=True)
checks={n:json.loads((HERE/f'build/{n}.json').read_text()) for n in ['source-audit','geometry','pose','reimport','protected-files']};assert all(a['ok'] for a in checks.values())
modeler=json.loads((HERE/'build/report.json').read_text());assert modeler['summary']['errors']==0 and modeler['summary']['warnings']==0
assert '5 passed' in (HERE/'build/smoke-tests.txt').read_text()
assert '1 passed' in (HERE/'build/play-tests.txt').read_text()
assert 'Vehicle GLB integration checks passed.' in (HERE/'build/integration-tests.txt').read_text()
assert 'checks passed.' in (HERE/'build/driving-tests.txt').read_text()
files=[HERE/'model.py',HERE/'parameters.json',HERE/'build/model.blend',ROOT/'media/vehicles/duett-p210-epa.glb']
summary={'vehicle':'Volvo Duett P210 EPA pickup','baseline':'5c84a17','branch':'experiment/duett-p210-epa','checks':checks,'modeler':modeler['summary'],'tests':{'duett_browser':'1 passed','default_game_map_smoke':'5 passed','validator_unit':'5 passed','vehicle_integration':'passed','driving_regression':'passed'},'blender_modeler_commit':'c8f245982108e2627972768d4311cbe172b58137','reference_comparison':'Manual visual comparison to same Hova EPA front/rear perspective photographs. No exact orthographic photo or automated IoU. See references.md.','visual_review':'All seven actual final Blender views inspected; user approval pending','physical_ipad_tested':False,'performance':'No hardware FPS benchmark; GLB 12,276 triangles, 25 meshes and 11 simple materials','files_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Duett P210 EPA review</title><style>body{margin:20px auto;max-width:1250px;padding:12px;background:#edeae0;color:#23312d;font:18px system-ui}img{max-width:100%;height:auto;border-radius:8px}a{color:#245c56}nav{display:flex;gap:20px;flex-wrap:wrap}</style><h1>Volvo Duett P210 EPA</h1><p>Original stylised pickup. Manufacturer-verified 2.600 m wheelbase; cab and bed dimensions are estimates. Visual approval pending.</p><nav><a href="../../media/vehicles/duett-p210-epa.glb">GLB</a><a href="build/model.blend">Blender</a><a href="duett-delivery.zip">Download package</a><a href="references.md">Reference notes</a></nav><h2>Seven final views</h2><a href="review/contact-sheet.png"><img src="review/contact-sheet.png" alt="Seven actual Blender views"></a><h2>Blockout and refinement</h2><a href="review/before-after.png"><img src="review/before-after.png" alt="Matched blockout and refined views"></a><p>12,276 triangles · 25 meshes · 11 materials. Geometry, GLB, hierarchy and browser driving checks passed. No physical iPad or hardware FPS benchmark.</p></html>'''
(HERE/'index.html').write_text(html)
files=list(HERE.glob('*.py'))+list(HERE.glob('*.json'))+list(HERE.glob('*.md'))+[HERE/'build.sh',HERE/'index.html']+list(OUT.glob('*.png'))+list((HERE/'build').glob('*.json'))+list((HERE/'build').glob('*tests.txt'))+[HERE/'build/model.blend',ROOT/'media/vehicles/duett-p210-epa.glb',ROOT/'LICENSE']
files += [ROOT/'tools/vehicle_pipeline'/n for n in ['authoring.py','surface_refinement.py','blender_import.py','reimport_check.py','validate.py','requirements.txt']]+[ROOT/'experiments/round2/pose_audit.py']
with zipfile.ZipFile(HERE/'duett-delivery.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(ROOT))
print(json.dumps({'ok':True,'package_bytes':(HERE/'duett-delivery.zip').stat().st_size}))
