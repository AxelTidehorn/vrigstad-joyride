"""Package genuine Blender renders; no synthetic or generated reference images."""
from pathlib import Path
import json,hashlib,subprocess,zipfile
from PIL import Image,ImageDraw,ImageFont,ImageOps
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'review';OUT.mkdir(exist_ok=True)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def font(n):return ImageFont.truetype(FONT,n)
BG=(237,234,224);INK=(35,49,45)
def flatten(path):
    im=Image.open(path).convert('RGBA');bg=Image.new('RGBA',im.size,(*BG,255));bg.alpha_composite(im);return bg.convert('RGB')
views=['side','front','rear','front_three_quarter','rear_three_quarter','high_three_quarter']
labels=['Exact orthographic side','Front','Rear','Front three-quarter','Rear three-quarter','High three-quarter']
for name in views:
    im=flatten(HERE/f'build/final/views/shaded_{name}.png');im.save(OUT/f'{name}.png',optimize=True)
sheet=Image.new('RGB',(1800,1740),BG);d=ImageDraw.Draw(sheet)
d.text((32,22),'1970 CHEVROLET IMPALA · 16439 FOUR-DOOR HARDTOP',font=font(31),fill=INK)
d.text((32,68),'Original low-poly body · 5.486 m long · visual approval pending',font=font(24),fill=INK)
for i,(name,label) in enumerate(zip(views,labels)):
    x=(i%2)*900;y=118+(i//2)*532;im=flatten(OUT/f'{name}.png').resize((875,875))
    # Consistent per-view presentation crop, never used to alter vehicle metrics.
    if name=='side':im=im.crop((0,280,875,660))
    elif name in ('front','rear'):im=im.resize((520,520)).crop((0,15,520,505))
    elif name=='high_three_quarter':im=im.resize((650,650)).crop((0,90,650,580))
    else:im=im.crop((0,200,875,700))
    sheet.paste(im,(x+(900-im.width)//2,y+36));d.text((x+26,y),label,font=font(25),fill=INK)
d.text((32,1695),'Blender / Modeler studio · metres, no game integration · see reference and geometry limits in report',font=font(20),fill=INK)
sheet.save(OUT/'contact-sheet.png',optimize=True)
for folder,name in [('details','front_detail'),('rear_detail','rear_detail')]:
    src='front_detail' if folder=='details' else 'rear_detail'
    flatten(HERE/f'build/final/{folder}/shaded_{src}.png').save(OUT/f'{name}.png',optimize=True)
# Genuine identical-mode, identical-camera before/after, first blockout vs final.
sheet=Image.new('RGB',(1800,1100),BG);d=ImageDraw.Draw(sheet)
d.text((26,15),'BLOCKOUT → FINAL · same Workbench cameras, lights and scale',font=font(29),fill=INK)
angles=['side','front_three_quarter','rear_three_quarter']
for row,(folder,label) in enumerate([('blockout','A · initial blockout'),('final-clay','D · completed geometry')]):
    y=75+row*500;d.text((26,y),label,font=font(25),fill=INK)
    for col,name in enumerate(angles):
        im=flatten(HERE/f'build/{folder}/views/clay_{name}.png').crop((0,280,1100,860));im=im.resize((595,314));sheet.paste(im,(col*600,y+70))
sheet.save(OUT/'blockout-final.png',optimize=True)
# Common real-world camera bounds, not an auto-fit per vehicle.
cars=[('impala1970','Chevrolet Impala 1970 · 5.486 m'),('volvo240','Volvo 240 · 4.82 m'),('saab900','Saab 900 · 4.68 m')]
for view,filename,crop in [('common','fleet-scale.png',(0,285,1100,850)),('side','fleet-side-scale.png',(0,365,1100,755))]:
    height=crop[3]-crop[1];canvas=Image.new('RGB',(1140,105+3*(height+60)),BG);draw=ImageDraw.Draw(canvas)
    draw.text((26,16),'SAME PHYSICAL SCALE · same camera and studio lights',font=font(26),fill=INK)
    draw.text((26,55),'No vehicle is resized to match another. Existing 240 / Saab masters unchanged.',font=font(20),fill=INK)
    for i,(key,label) in enumerate(cars):
        im=flatten(HERE/f'build/fleet/{key}/shaded_{view}.png').crop(crop);y=105+i*(height+60);draw.text((26,y),label,font=font(25),fill=INK);canvas.paste(im,(20,y+45))
    canvas.save(OUT/filename,optimize=True)
# Visible reference provenance; no GM brochure scan is redistributed.
refs=[('hardtop-side.jpg','16439 hardtop · glass only; cropped / snow / perspective'),('hardtop-front.jpg','16439 hardtop · cabin context; damaged lamp excluded'),('front-three-quarter.jpg','Sedan · shared hood / grille only; roof excluded'),('rear.jpg','Sedan · shared 1970 bumper lights only; roof excluded')]
canvas=Image.new('RGB',(1600,1260),BG);draw=ImageDraw.Draw(canvas)
draw.text((25,15),'REFERENCE SCOPE · correct hardtop cabin / shared fascia details',font=font(28),fill=INK)
for i,(file,label) in enumerate(refs):
    x=(i%2)*800;y=75+(i//2)*550;im=ImageOps.contain(Image.open(HERE/'references'/file).convert('RGB'),(775,470));canvas.paste(im,(x+(800-im.width)//2,y+45));draw.text((x+20,y),label,font=font(18),fill=INK)
draw.text((25,1195),'Hardtop photos: DanTD, CC BY-SA 4.0. Blue Sedan photos: AlfvanBeem, CC0. Resized / combined study.',font=font(20),fill=INK)
draw.text((25,1223),'Composite CC BY-SA 4.0 · source file-page URLs and exclusions: references/sources.json and references.md',font=font(20),fill=INK)
canvas.save(OUT/'reference-views.png',optimize=True)
# Factory dimensional rails over the exact same full-vehicle orthographic image.
im=flatten(HERE/'build/final/silhouette/full-vehicle.png');canvas=Image.new('RGB',(1800,1000),BG);canvas.paste(im,(0,0));draw=ImageDraw.Draw(canvas)
draw.rectangle((0,0,1800,115),fill=BG);draw.text((32,20),'FACTORY DIMENSIONS / MODEL PLACEMENT',font=font(32),fill=INK)
draw.text((32,66),'GM 1970 Chevrolet · Sport Sedan column · independent scale, no silhouette fitting',font=font(24),fill=INK)
frame=json.loads((HERE/'build/final/silhouette/frame.json').read_text());front,rear=frame['front_wheel'][0],frame['rear_wheel'][0];ppm=frame['pixels_per_metre'];low=rear-1.51384*ppm;high=front+.94996*ppm
def rail(x0,x1,y,label):
    draw.line((x0,y,x1,y),fill=INK,width=3)
    for x in [x0,x1]:draw.line((x,y-12,x,y+12),fill=INK,width=3)
    box=draw.textbbox((0,0),label,font=font(24));draw.text(((x0+x1-box[2])/2,y+14),label,font=font(24),fill=INK)
rail(low,high,795,'5.4864 m total length');rail(rear,front,705,'3.0226 m wheelbase');rail(low,rear,705,'1.5138 m rear');rail(front,high,705,'0.9500 m front')
draw.text((32,880),'Height: 1.397 m   Body width: 2.0269 m   Tracks: 1.6104 / 1.6078 m',font=font(27),fill=INK)
draw.text((32,930),'Documented nominal dimensions. Curves / tyre overall diameter are estimates; this is not an exact reference-contour certificate.',font=font(23),fill=INK)
canvas.save(OUT/'dimensions.png',optimize=True)
# Freeze independent checks, never turn a missing/failed result into approval.
checks={}
for name in ['source-audit','geometry','reimport','three-loader','pose','paint-test','reproduction','existing-pose-regression']:
    checks[name]=json.loads((HERE/f'build/{name}.json').read_text());assert checks[name]['ok'],name
protected={}
for rel in ['experiments/saab900/build/model.blend','experiments/saab900/build/saab900-t16.glb','experiments/volvo240/refinement/model.blend','experiments/volvo240/refinement/review-only.glb','experiments/xc70p2/build/model.blend','experiments/xc70p2/build/xc70-civilian.glb','experiments/xc70p2/build/xc70-police.glb','src/vehicles/vehicle-library.mjs','src/game.html']:
    previous=subprocess.check_output(['git','show','ff6a0f1:'+rel],cwd=ROOT);current=(ROOT/rel).read_bytes();protected[rel]={'unchanged':previous==current,'sha256':hashlib.sha256(current).hexdigest()}
assert all(x['unchanged'] for x in protected.values())
(HERE/'build/protected-files.json').write_text(json.dumps(protected,indent=2)+'\n')
fingerprints={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'model.py',HERE/'parameters.json',HERE/'build/model.blend',HERE/'build/impala1970-hardtop.glb']}
summary={'vehicle':'1970 Chevrolet Impala 16439 four-door hardtop','branch':'experiment/impala-1970-hardtop','base':'ff6a0f1','sha256':fingerprints,'verified':{k:checks[k] for k in checks},'reference_comparison':json.loads((OUT/'reference-comparison.json').read_text()),'protected_files':protected,'human_visual_approval':'pending','physical_ipad_safari_tested':False,'game_integration':False}
(HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
# A compact source/asset/review archive, not duplicate GLBs for each paint colour.
files=[p for p in HERE.glob('*') if p.suffix in ['.py','.json','.mjs','.js','.md','.html','.sh']]
compact_sheets=['contact-sheet.png','blockout-final.png','fleet-scale.png','fleet-side-scale.png','dimensions.png','blockout-reference-overlay.png','final-reference-overlay.png','blockout-glass-deviation.png','final-glass-deviation.png']
files += list((HERE/'references').glob('*'))+[OUT/x for x in compact_sheets]+list(OUT.glob('*.json'))
files += [HERE/'build/blockout/model.blend']
files += [HERE/f'build/{x}' for x in ['model.blend','impala1970-hardtop.glb','report.json','report.txt','source-audit.json','geometry.json','reimport.json','three-loader.json','pose.json','paint-test.json','reproduction.json','existing-pose-regression.json','protected-files.json','validator-tests.txt','silhouette-tests.txt','shared-geometry-tests.txt']]
files += [ROOT/'LICENSE',ROOT/'experiments/round2/pose_audit.py',ROOT/'experiments/round2/reproduction.py']
files += [ROOT/'tools/vehicle_pipeline'/x for x in ['authoring.py','surface_refinement.py','blender_import.py','validate.py','reimport_check.py','check_preview_glb.mjs','verify_silhouette.py','silhouette_render.py','requirements.txt','README.md']]
files += [ROOT/'media/vehicles/vendor'/x for x in ['three-r128.min.js','GLTFLoader-r128.js','THREE-LICENSE.txt']]
files += [ROOT/'media/vehicles/preview-controls.mjs',ROOT/'media/vehicles/preview.css',ROOT/'src/visual/film-pipeline.js']
with zipfile.ZipFile(HERE/'impala1970-delivery.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(set(files)):z.write(p,p.relative_to(ROOT))
print(json.dumps({'review':str(OUT),'zip_bytes':(HERE/'impala1970-delivery.zip').stat().st_size,'checks':'all passed'}))
