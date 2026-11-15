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
d.text((32,68),'Shape refinement · 5.486 m long · visual approval pending',font=font(24),fill=INK)
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
# Same fixed cameras / crop for both versions; never fit each car independently.
REVIEW=HERE/'shape-review'
assert json.loads((REVIEW/'before/cameras.json').read_text())==json.loads((REVIEW/'after/cameras.json').read_text())
provenance={'baseline_commit':'6c7f32c783aa0923cb2f18836157a7ef1cccfc9b','identical_camera_metadata':True,'before':{},'after':{}}
for folder in ['views','details','rear_detail']:
    for image in (REVIEW/'before'/folder).glob('shaded_*.png'):
        rel=f'experiments/impala1970/build/final/{folder}/{image.name}'
        old=subprocess.check_output(['git','show','6c7f32c:'+rel],cwd=ROOT)
        new_image=REVIEW/'after'/folder/image.name
        assert image.read_bytes()==old, f'Baseline render mismatch: {image}'
        assert new_image.read_bytes()==(HERE/'build/final'/folder/image.name).read_bytes(), f'Final render mismatch: {new_image}'
        provenance['before'][str(image.relative_to(REVIEW))]=hashlib.sha256(old).hexdigest()
        provenance['after'][str(new_image.relative_to(REVIEW))]=hashlib.sha256(new_image.read_bytes()).hexdigest()
provenance['ok']=True
(REVIEW/'render-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
def pairs(filename,title,items,mode='shaded',body=False):
    sheet=Image.new('RGB',(1800,105+530*len(items)),BG);d=ImageDraw.Draw(sheet)
    d.text((28,12),title,font=font(28),fill=INK)
    d.text((28,55),'BEFORE · 6c7f32c',font=font(25),fill=INK)
    d.text((928,55),'AFTER · same cameras, scale, materials and lighting',font=font(23),fill=INK)
    for row,(folder,name,label) in enumerate(items):
        for col,version in enumerate(['before','after']):
            source=REVIEW/version/('body' if body else folder)/f'{mode}_{name}.png'
            im=flatten(source)
            # One shared crop per camera, applied equally to before and after.
            if folder=='views':
                crop=(0,280,1100,860) if name=='side' else ((180,150,920,1000) if name in ('front','rear') else (0,180,1100,950))
            else:crop=(0,100,1200,1080)
            im=ImageOps.contain(im.crop(crop),(875,470));y=100+530*row
            sheet.paste(im,(900*col+(900-im.width)//2,y+40))
            d.text((26+900*col,y),label,font=font(23),fill=INK)
    sheet.save(OUT/filename,optimize=True)
pairs('before-after.png','1970 IMPALA · SHAPE REFINEMENT', [('views',v,l) for v,l in [('side','Exact orthographic side'),('front_three_quarter','Front three-quarter'),('rear_three_quarter','Rear three-quarter')]])
pairs('ends-before-after.png','ORTHOGRAPHIC FRONT / REAR · SAME SCALE', [('views','front','Front'),('views','rear','Rear')])
pairs('fascia-before-after.png','FASCIA / QUARTERS · SAME FRAMING', [('details','front_detail','Hood channels, fender crowns and recessed V grille'),('rear_detail','rear_detail','Broad rear shoulders, lowered deck, returning bumper corners')])
pairs('body-before-after.png','STEEL + TYRES ONLY · GEOMETRY, WITHOUT GLASS OR CHROME', [('views',v,l) for v,l in [('side','Side'),('front','Front'),('rear','Rear'),('front_three_quarter','Front three-quarter')]],mode='clay',body=True)
pairs('blockout-final.png','PRIOR MASTER → REFINED MASTER · WORKBENCH CLAY', [('views',v,l) for v,l in [('side','Side'),('front_three_quarter','Front three-quarter'),('rear_three_quarter','Rear three-quarter')]],mode='clay')
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
for name in ['source-audit','geometry','reimport','three-loader','pose','paint-test','reproduction','existing-pose-regression','browser-preview']:
    checks[name]=json.loads((HERE/f'build/{name}.json').read_text());assert checks[name]['ok'],name
protected={}
for rel in ['experiments/saab900/build/model.blend','experiments/saab900/build/saab900-t16.glb','experiments/volvo240/refinement/model.blend','experiments/volvo240/refinement/review-only.glb','experiments/xc70p2/build/model.blend','experiments/xc70p2/build/xc70-civilian.glb','experiments/xc70p2/build/xc70-police.glb','src/vehicles/vehicle-library.mjs','src/game.html']:
    previous=subprocess.check_output(['git','show','6c7f32c:'+rel],cwd=ROOT);current=(ROOT/rel).read_bytes();protected[rel]={'unchanged':previous==current,'sha256':hashlib.sha256(current).hexdigest()}
assert all(x['unchanged'] for x in protected.values())
assert '5 passed' in (HERE/'build/e2e-tests.txt').read_text(), 'Game smoke tests incomplete or failed'
(HERE/'build/protected-files.json').write_text(json.dumps(protected,indent=2)+'\n')
fingerprints={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE/'model.py',HERE/'parameters.json',HERE/'build/model.blend',HERE/'build/impala1970-hardtop.glb']}
summary={'vehicle':'1970 Chevrolet Impala 16439 four-door hardtop','branch':'experiment/impala-1970-shape','base':'6c7f32c783aa0923cb2f18836157a7ef1cccfc9b','sha256':fingerprints,'verified':{k:checks[k] for k in checks},'reference_comparison':json.loads((OUT/'reference-comparison.json').read_text()),'render_provenance':provenance,'shape_preservation':json.loads((REVIEW/'preservation.json').read_text()),'protected_files':protected,'human_visual_approval':'pending','physical_ipad_safari_tested':False,'game_integration':False}
(HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
# A compact source/asset/review archive, not duplicate GLBs for each paint colour.
files=[p for p in HERE.glob('*') if p.suffix in ['.py','.json','.mjs','.js','.md','.html','.sh']]
compact_sheets=['ends-before-after.png','before-after.png','fascia-before-after.png','body-before-after.png','contact-sheet.png','blockout-final.png','fleet-scale.png','fleet-side-scale.png','dimensions.png','blockout-reference-overlay.png','final-reference-overlay.png','blockout-glass-deviation.png','final-glass-deviation.png']
compact_sheets += [f'{name}.png' for name in views]+['front_detail.png','rear_detail.png']
files += list((HERE/'references').glob('*'))+[OUT/x for x in compact_sheets]+list(OUT.glob('*.json'))
files += list(REVIEW.glob('*.json'))
files += [HERE/f'build/{x}' for x in ['model.blend','impala1970-hardtop.glb','report.json','report.txt','source-audit.json','geometry.json','reimport.json','three-loader.json','pose.json','paint-test.json','reproduction.json','existing-pose-regression.json','protected-files.json','validator-tests.txt','silhouette-tests.txt','shared-geometry-tests.txt','preview-tests.txt','e2e-tests.txt','browser-preview.json','browser-preview.png']]
files += [ROOT/'LICENSE',ROOT/'experiments/round2/pose_audit.py',ROOT/'experiments/round2/reproduction.py']
files += [ROOT/'tools/vehicle_pipeline'/x for x in ['authoring.py','surface_refinement.py','blender_import.py','validate.py','reimport_check.py','check_preview_glb.mjs','verify_silhouette.py','silhouette_render.py','requirements.txt','README.md']]
files += [ROOT/'media/vehicles/vendor'/x for x in ['three-r128.min.js','GLTFLoader-r128.js','THREE-LICENSE.txt']]
files += [ROOT/'media/vehicles/preview-controls.mjs',ROOT/'media/vehicles/preview.css',ROOT/'src/visual/film-pipeline.js']
with zipfile.ZipFile(HERE/'impala1970-delivery.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(set(files)):z.write(p,p.relative_to(ROOT))
print(json.dumps({'review':str(OUT),'zip_bytes':(HERE/'impala1970-delivery.zip').stat().st_size,'checks':'all passed'}))
