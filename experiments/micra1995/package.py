"""Compose genuine matched renders; collect checks without inferring visual approval."""
from pathlib import Path
import json,hashlib,zipfile
from PIL import Image,ImageDraw,ImageFont,ImageOps
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'review';OUT.mkdir(exist_ok=True)
BG=(237,234,224);INK=(35,49,45)
def font(n):return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
def flat(path):
 im=Image.open(path).convert('RGBA');bg=Image.new('RGBA',im.size,(*BG,255));bg.alpha_composite(im);return bg.convert('RGB')
views=['side','front','rear','front_three_quarter','rear_three_quarter','high_three_quarter']
labels=['Exact side','Front','Rear','Front three-quarter','Rear three-quarter','High three-quarter']
canvas=Image.new('RGB',(1800,1700),BG);d=ImageDraw.Draw(canvas);d.text((26,18),'1995 NISSAN MICRA K11 · THREE DOORS',font=font(34),fill=INK)
for i,(name,label) in enumerate(zip(views,labels)):
 im=flat(HERE/f'build/views/shaded_{name}.png');im.save(OUT/f'{name}.png',optimize=True)
 crop=(0,240,1000,850) if name=='side' else (50,120,950,950)
 im=ImageOps.contain(im.crop(crop),(875,475));x=i%2*900;y=90+i//2*530;canvas.paste(im,(x+(900-im.width)//2,y+35));d.text((x+25,y),label,font=font(26),fill=INK)
d.text((26,1650),'Actual Blender renders · nominal 3.695 m long / 2.360 m wheelbase · human visual approval pending',font=font(22),fill=INK);canvas.save(OUT/'contact-sheet.png',optimize=True)
assert json.loads((HERE/'initial/views/cameras.json').read_text())==json.loads((HERE/'build/views/cameras.json').read_text())
canvas=Image.new('RGB',(1800,1750),BG);d=ImageDraw.Draw(canvas);d.text((26,18),'INITIAL → REFINED · SAME CAMERA, LIGHTING AND SCALE',font=font(29),fill=INK)
for row,name in enumerate(['side','front_three_quarter','rear_three_quarter']):
 for col,stage in enumerate(['initial','build']):
  im=flat(HERE/f'{stage}/views/shaded_{name}.png').crop((0,180,1000,900));im=ImageOps.contain(im,(875,475));x=900*col;y=95+row*530;canvas.paste(im,(x+(900-im.width)//2,y+42));d.text((x+25,y),('Before' if col==0 else 'After')+' · '+name.replace('_',' '),font=font(25),fill=INK)
canvas.save(OUT/'before-after.png',optimize=True)
checks={n:json.loads((HERE/f'build/{n}.json').read_text()) for n in ['geometry','source-audit','pose','reimport']}
assert all(x['ok'] for x in checks.values())
test_logs={'micra_driving':'micra-play-test.txt','game_smoke':'smoke-final-tests.txt','glb_integration':'integration-tests.txt','driving_regression':'driving-tests.txt','validator_unit':'validator-tests.txt'}
tests={k:(HERE/'build'/v).read_text() for k,v in test_logs.items()}
assert '1 passed' in tests['micra_driving'], 'Micra driving test not complete'
assert '5 passed' in tests['game_smoke'], 'Full game smoke tests not complete'
assert 'Vehicle GLB integration checks passed.' in tests['glb_integration']
assert 'checks passed.' in tests['driving_regression']
assert '\nOK' in tests['validator_unit']
summary={'vehicle':'1995 European Nissan Micra K11 three-door, pre-facelift','base_commit':'d5a2a68','branch':'experiment/micra-k11-1995','checks':checks,'tests':{k:{'passed':True,'log':'build/'+v} for k,v in test_logs.items()},'files_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'model.py',HERE/'parameters.json',HERE/'build/model.blend',ROOT/'media/vehicles/micra-k11.glb']},'reference_accuracy':'Perspective/manual shape review; no automatic IoU','human_visual_approval':'pending','physical_ipad_tested':False}
(HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
files=list(HERE.glob('*.py'))+list(HERE.glob('*.json'))+list(HERE.glob('*.md'))+[HERE/'build.sh',HERE/'index.html']+list(OUT.glob('*.png'))+list((HERE/'build').glob('*.json'))+list((HERE/'build').glob('*tests.txt'))+[HERE/'build/model.blend',ROOT/'media/vehicles/micra-k11.glb',ROOT/'LICENSE']
files += [ROOT/'tools/vehicle_pipeline'/n for n in ['authoring.py','surface_refinement.py','blender_import.py','reimport_check.py','validate.py','requirements.txt']]+[ROOT/'experiments/round2/pose_audit.py']
with zipfile.ZipFile(HERE/'micra1995-delivery.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in files:z.write(p,p.relative_to(ROOT))
print(json.dumps({'triangles':checks['geometry']['triangles'],'checks':'passed','zip_bytes':(HERE/'micra1995-delivery.zip').stat().st_size}))
