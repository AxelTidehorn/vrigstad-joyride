"""Publishable review artifacts from real Blender renders; no model/image generation."""
from pathlib import Path
import json,hashlib,struct,zipfile,shutil,re
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;ROOT=P.parents[1];BUILD=P/'build';OUT=P/'review';OUT.mkdir(exist_ok=True)
config=json.loads((P/'vehicles.json').read_text());font=ImageFont.truetype('DejaVuSans.ttf',25)
def read(p):return json.loads(Path(p).read_text())
def tile(path,size,crop=None):
    im=Image.open(path).convert('RGBA');bg=Image.new('RGBA',im.size,'#e9e6df');bg.alpha_composite(im)
    if crop:bg=bg.crop(crop)
    bg.thumbnail(size);return bg.convert('RGB')
def pair_sheet(files,target,title):
    sheet=Image.new('RGB',(1800,960),'#e9e6df');d=ImageDraw.Draw(sheet)
    for col,(label,file) in enumerate(files):sheet.paste(tile(file,(890,890)),(col*900,50));d.text((col*900+15,12),label+' / '+title,font=font,fill='#253d36')
    sheet.save(target,optimize=True)
metadata={'base_commit':'744a986','repository':'AxelTidehorn/vrigstad-joyride','branch':'experiment/vehicle-refinement-round2','game_integrated':False,'physical_ipad_or_browser_gpu_tested':False,'models':{},'tests':{},'inventory':{}}
for car,spec in config.items():
    folder=BUILD/car;prefix='shaded' if car=='xc70police' else 'clay';sheet=Image.new('RGB',(1800,1800),'#e9e6df');draw=ImageDraw.Draw(sheet)
    for row,view in enumerate(['side','front_three_quarter','rear_three_quarter']):
        for col,stage in enumerate(['before','after']):
            sheet.paste(tile(folder/stage/'views'/(prefix+'_'+view+'.png'),(890,550),(0,180,1100,1000)),(col*900,row*600+40));draw.text((col*900+15,row*600+10),stage.upper()+' / '+view.replace('_',' '),font=font,fill='#253d36')
    sheet.save(OUT/(car+'-before-after.png'),optimize=True)
    pair_sheet([(stage.upper(),folder/stage/'close'/(prefix+'_detail.png')) for stage in ['before','after']],OUT/(car+'-close.png'),spec['name'])
    if car.startswith('xc70'):
        pair_sheet([(stage.upper(),folder/stage/'windows'/(prefix+'_upper_windows.png')) for stage in ['before','after']],OUT/(car+'-windows.png'),'upper glazing / frames')
    glb=ROOT/spec['glb'];data=glb.read_bytes();size=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+size]);body=next(n for n in doc['nodes'] if n.get('name')=='body');material=doc['meshes'][body['mesh']]['primitives'][0]['material']
    geom_path=(ROOT/'experiments/saab900/build/geometry.json' if car=='saab900' else ROOT/'experiments/volvo240/refinement/glb_geometry.json' if car=='volvo240' else ROOT/'experiments/xc70p2/build'/('police' if car=='xc70police' else 'civilian')/'geometry.json')
    validation=read(geom_path);assert validation['ok'],validation
    quality=read(BUILD/('xc70p2' if car=='xc70police' else car)/'geometry.json');assert quality['ok'],quality
    pose=read(folder/'pose.json');assert pose['ok'],pose
    source=read(BUILD/('xc70p2' if car=='xc70police' else car)/'reproduction.json');assert source['ok'],source
    metadata['models'][car]={'name':spec['name'],'blend':spec['blend'],'glb':spec['glb'],'validation':validation,'source_quality':quality,'pose_test':pose,'reproduction':source,'gltf_materials':len(doc['materials']),'gltf_mesh_nodes':sum('mesh' in n for n in doc['nodes']),'gltf_primitives':sum(len(m['primitives']) for m in doc['meshes']),'body_material':doc['materials'][material]['name'],'body_colour_independently_editable':car!='xc70police' and not doc['materials'][material].get('pbrMetallicRoughness',{}).get('baseColorTexture'),'texture_images':len(doc.get('images',[])),'sha256_glb':hashlib.sha256(data).hexdigest()}
    if car!='xc70police':
        inv=read(P/'baseline-inventory'/(car+'.json'));metadata['inventory'][car]={'selected_blend_sha256':quality['baseline_sha256'],'body_triangles_before':inv['objects']['body']['triangles'],'source_branches':'Saab profile c130ae6 / Volvo arches 744a986 / XC70 block lamps f064b57; older contrib branches were inspected and not used'}
for stage in ['before','after']:
    sheet=Image.new('RGB',(1800,1280),'#e9e6df');draw=ImageDraw.Draw(sheet)
    for i,(car,spec) in enumerate(config.items()):
        x=i%2*900;y=i//2*640
        # Identical crop/scale for every car. Common orthographic Cycles camera.
        sheet.paste(tile(BUILD/car/stage/'fleet/shaded_common.png',(890,580),(0,180,1100,1000)),(x,y+42));draw.text((x+15,y+10),spec['name'],font=font,fill='#253d36')
    sheet.save(OUT/('fleet-'+stage+'.png'),optimize=True)
for name in ['validator','silhouette','shared-geometry']:
    text=(P/(name+'-tests.txt')).read_text();metadata['tests'][name]={'passed':int(re.search(r'Ran (\d+) tests',text).group(1)),'ok':text.rstrip().endswith('OK')};assert metadata['tests'][name]['ok']
metadata['shared_xc70']=read(ROOT/'experiments/xc70p2/build/shared-export-geometry.json');assert metadata['shared_xc70']['ok']
metadata['source_mutation_test']=read(BUILD/'xc70p2/architecture-mutation.json');assert metadata['source_mutation_test']['ok']
metadata['mutation_export_test']=read(BUILD/'xc70p2/mutation-export-shared.json');assert metadata['mutation_export_test']['ok']
metadata['glass_before']=read(BUILD/'xc70p2/before-window-seating.json');metadata['glass_after']=read(BUILD/'xc70p2/after-window-seating.json')
assert not any(metadata['glass_after']['lamp_glass_intersection_candidates'].values())
assert metadata['glass_after']['back_surface_coincident_or_occluded_samples']==0
before=read(P/'baseline-inventory/xc70p2.json')['objects']['glass_envelope']['islands'];after=read(BUILD/'xc70p2/inventory-after.json')['objects']['glass_envelope']['islands']
def rear_dimensions(islands):
    bounds=next(i['bounds_m'] for i in islands if i['bounds_m'][1][1]<-2);width=bounds[0][1]-bounds[0][0];height=bounds[2][1]-bounds[2][0];return {'width_m':width,'height_m':height,'aspect_ratio_width_height':width/height,'lower_z_m':bounds[2][0],'upper_z_m':bounds[2][1]}
metadata['rear_aperture']={'before':rear_dimensions(before),'after':rear_dimensions(after),'reference':'Volvo April 2003 near-rear manufacturer view plus Ethan Llamas 2006 facelift rear-three-quarter photo; existing licensed reference register','reference_outer_glazed_assembly_approx_bounds_px':[128,100,774,323],'reference_image_size_px':[900,795],'reference_scope_uncertainty':'Approximate manual outer black-surround extent (~10px boundary uncertainty), includes frit/seal scope. Not a calibrated clear-aperture dimension; 2006 photo is perspective. No exact mm accuracy claim. Existing pane was too letterbox-like; increased height and an actual painted land beside the lamp are justified by both references.'}
# Reference study image: visible bounds are explicitly approximate, not a generated mask.
im=Image.open(ROOT/'experiments/xc70p2/references/rear.png').convert('RGB');d=ImageDraw.Draw(im);d.rectangle((128,100,774,323),outline='#d78732',width=4);d.text((130,330),'Approximate outer glazed assembly / not clear-aperture CAD',fill='#73491d');im.save(OUT/'xc70-reference-study.png',optimize=True)
metadata['saab_silhouette']={s:read(BUILD/'saab900/silhouette'/s/'comparison/report.json') for s in ['before','after']}
(P/'summary.json').write_text(json.dumps(metadata,indent=2)+'\n')
changes={
 'saab900':('Forward hood raised 20–35 mm with a defined clamshell shoulder; original cowl, cabin and hatch retained. Pressed hood/door reveals, broader fitted lamp tops, grille bezel and lower air dam.','Cabin/roof/glass and wheel geometry retained. Remaining: simplified corner markers, trim, opaque glazing and a residual stylized cowl corner.'),
 'volvo240':('Outer upper rail raised into a flatter shoulder ledge (up to 35 mm); straight pressed shoulder and door lines, actual hood/trunk reveals, new grille slats/diagonal, split lamp lenses and bumper sections.','All 473 protected original well-region vertices remain. Roof, glass, wheelbase and wheel positions retained. Remaining: simple wheel discs, mirror masses and glazing edge artifacts.'),
 'xc70p2':('Restrained P2 fender crown, pressed shoulder/door/hood divisions, grille/lamp frames and defined bumper sections. Taller rear aperture, revised reveal and positive glass backing clearance. Block tail lamps retain their front volume; hidden inner walls clear the glass.','Same single source as police. Roof/axles and primary estate proportions retained. Remaining: approximate pillar/bumper forms, opaque glass, simplified lamp optics and the existing track simplification.'),
 'xc70police':('Same geometry changes as civilian automatically. Blue/white paint and full blue fender/quarter areas retained, no POLIS text. Lightbar and grille modules retain their names/materials.','All 55 shared mesh nodes match, including every window and both multi-material tail lamps. No independent police body. Physical iPad GPU performance and game-driving behaviour remain untested.')}
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Vrigstad Joyride · vehicle refinement round 2</title><style>body{margin:0;background:#e9e6df;color:#253d36;font:18px system-ui}main{max-width:1600px;margin:auto;padding:24px}h1{font-size:clamp(28px,4vw,46px)}p{max-width:1100px;line-height:1.6}a{color:#24675f}nav{display:flex;flex-wrap:wrap;gap:10px}nav a{padding:12px;border:1px solid #a3ada2;border-radius:6px}img{width:100%;height:auto;display:block;margin:16px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}.note{border-left:4px solid #ad854c;padding:14px;background:#e0dacd}table{border-collapse:collapse;width:100%;font-size:16px}td,th{text-align:left;padding:12px;border-bottom:1px solid #b9c1b5}section{margin:48px 0}summary{cursor:pointer;padding:15px}@media(max-width:750px){.pair{grid-template-columns:1fr}main{padding:16px}table{font-size:14px}}</style><main><h1>Vehicle refinement · round 2</h1><p>Three existing Blender bodies, four exports. Geometry and component quality refined from the latest first-round masters. No game integration. Left = before, right = after; cameras and lighting are fixed within each comparison. Tap PNGs to inspect at full resolution.</p><nav><a href="#saab900">Saab 900</a><a href="#volvo240">Volvo 240</a><a href="#xc70p2">XC70 civilian</a><a href="#xc70police">XC70 police</a><a href="vehicle-round2.zip">Sources, models &amp; PNG sheets</a><a href="README.md">Construction / reproduction</a><a href="summary.json">All measurements (JSON)</a></nav><h2>Fleet · identical physical scale, camera and lighting</h2><p>All four cells use the same orthographic Cycles camera, world bounds, lights and pixel scale. No per-car fit-to-frame scaling.</p><details><summary>First-round fleet for comparison</summary><a href="review/fleet-before.png"><img loading="lazy" src="review/fleet-before.png" alt="First-round fleet at common scale"></a></details><a href="review/fleet-after.png"><img src="review/fleet-after.png" alt="Refined fleet at identical scale"></a><table><tr><th>Export</th><th>Triangles</th><th>glTF primitives</th><th>Wheelbase</th><th>Validation</th></tr>'''
for car,m in metadata['models'].items():
    v=m['validation'];html+=f'<tr><td>{m["name"]}</td><td>{v["triangles"]:,}</td><td>{m["gltf_primitives"]}</td><td>{v["wheelbase_m"]:.3f} m</td><td>Pass</td></tr>'
html+='</table><p class="note">Passing geometry is not an appearance approval. No physical Safari/GPU or in-game driving test. Glazing remains opaque; no interior is modelled. Existing procedural game cars, physics, traffic and main are unchanged.</p>'
for car,spec in config.items():
    beforeafter,remaining=changes[car];folder=BUILD/car;prefix='shaded' if car=='xc70police' else 'clay';viewer='../saab900/preview.html' if car=='saab900' else '../../media/vehicles/preview.html?vehicle=volvo240' if car=='volvo240' else '../xc70p2/preview.html?vehicle='+('police' if car=='xc70police' else 'civilian')
    html+=f'<section id="{car}"><h2>{spec["name"]}</h2><p>{beforeafter}</p><nav><a href="{viewer}">Touch 3D viewer</a><a href="../../{spec["blend"]}">Editable Blender</a><a href="../../{spec["glb"]}">GLB export</a></nav><a href="review/{car}-before-after.png"><img loading="lazy" src="review/{car}-before-after.png" alt="{car} same-camera side front and rear three-quarter before after"></a><a href="review/{car}-close.png"><img loading="lazy" src="review/{car}-close.png" alt="{car} detail before after"></a><p>{remaining}</p><p>Full final PNGs: '
    for view in ['side','front_three_quarter','rear_three_quarter']:html+=f'<a href="build/{car}/after/views/{prefix}_{view}.png">{view.replace("_"," ")}</a> · '
    shared='xc70p2' if car=='xc70police' else car
    html+=f'<a href="build/{shared}/geometry.json">source geometry / preservation</a> · <a href="build/{car}/pose.json">actual GLB pose test</a> · <a href="build/{shared}/reproduction.json">source reproduction</a></p>'
    if car.startswith('xc70'):html+=f'<a href="review/{car}-windows.png"><img loading="lazy" src="review/{car}-windows.png" alt="{car} oblique upper glazing and frames before after"></a>'
    html+='</section>'
r=metadata['rear_aperture'];before=r['before'];after=r['after'];g=metadata['glass_after']
html+=f'''<section><h2>XC70 · shared architecture and window correction</h2><p><code>model.py</code> owns body, openings, glass and lamps once. <code>round2.py</code> adds shared form refinements. <code>variants.py</code> changes paint and equipment visibility. The existing review/export process produces both GLBs from that one master.</p><p>Every one of the 55 common mesh nodes matches in the actual exports. A temporary 0.2% rear-aperture width mutation was applied once to the shared scene, exported twice and compared: both exports received identical geometry. The delivered master was not changed by the test.</p><p>Rear glass: {before['width_m']*1000:.0f} × {before['height_m']*1000:.0f} mm → {after['width_m']*1000:.0f} × {after['height_m']*1000:.0f} mm; width/height {before['aspect_ratio_width_height']:.2f} → {after['aspect_ratio_width_height']:.2f}. Lower edge drops {1000*(before['lower_z_m']-after['lower_z_m']):.1f} mm; upper edge is essentially retained. Both the manufacturer rear view and 2006 facelift photo support a taller, less letterbox-like aperture. The photo’s black surround includes frit/seals, so its boundaries are not an exact clear-glass CAD measurement.</p><p>Found causes: 34 glass/tail-lamp intersection candidates per side and near-coplanar glass backing. Corrected by narrowing the hidden inner housing wall, defining a painted land beside the glass, and using pane-wise outward seating with positive back clearance. Now 0 lamp/glass intersection candidates, 0 back-face coincidence samples, minimum backing clearance {g['minimum_backing_clearance_mm']:.2f} mm. No police equipment/glass intersections were found; there was no duplicate police glazing.</p><nav><a href="../xc70p2/build/shared-export-geometry.json">Actual export equality</a><a href="build/xc70p2/architecture-mutation.json">Shared-source mutation</a><a href="build/xc70p2/mutation-export-shared.json">Mutation export equality</a><a href="build/xc70p2/before-window-seating.json">Before seating</a><a href="build/xc70p2/after-window-seating.json">After seating</a></nav><div class="pair"><a href="review/xc70-reference-study.png"><img loading="lazy" src="review/xc70-reference-study.png" alt="Volvo manufacturer rear reference, approximate black-surround bounds"></a><a href="../xc70p2/references/rear-three-quarter.jpg"><img loading="lazy" src="../xc70p2/references/rear-three-quarter.jpg" alt="Ethan Llamas 2006 XC70 rear-right reference"></a></div><p>Inside diagnostics below isolate the shared glass and hide the opaque backing body. These inspect pane orientation/edges and do not depict a finished interior.</p><div class="pair">'''
for view in ['inside_rear','inside_side']:html+=f'<a href="build/xc70police/after/{view}.png"><img loading="lazy" src="build/xc70police/after/{view}.png" alt="Shared glazing {view} diagnostic"></a>'
html+='</div></section><section><h2>Saab · silhouette guardrail</h2>'
s0=metadata['saab_silhouette']['before'];s1=metadata['saab_silhouette']['after'];html+=f'<p>Existing wheel-centre-normalized verifier rerun against the same manufacturer three-door illustration proxy: IoU {s0["global_metrics"]["iou"]:.4f} → {s1["global_metrics"]["iou"]:.4f}; regional hood mean absolute error {s0["local_metrics"]["hood"]["absolute_height_mean_px"]:.2f} → {s1["local_metrics"]["hood"]["absolute_height_mean_px"]:.2f} canonical pixels. Maximum local error remains 20 px. This is a pre-facelift stylized drawing, not exact 1988 T16 metric approval; the real facelift photograph remains the front-volume reference.</p><div class="pair">'
for stage in ['before','after']:
    base=f'build/saab900/silhouette/{stage}/comparison';html+=f'<div><h3>{stage.title()}</h3><a href="{base}/overlay.png"><img loading="lazy" src="{base}/overlay.png" alt="Saab {stage} reference overlay"></a><a href="{base}/report.json">JSON and uncertainty</a></div>'
html+='</div></section><section><h2>Checks and limits</h2><p>All bodies are closed and consistently wound, with positive volume, no degenerates or nonadjacent BVH self-intersection candidates. All four GLBs pass the unchanged repository validator, actual Blender reimport and existing Three r128 parser. Transient pose tests verify independent wheel hubs, rim/spoke steering and spin, and body-mounted glass/lights/trim following body motion. These are structural tests, not new driving behaviour.</p><p>5 vehicle validator tests, 11 silhouette numerical tests and 6 shared-geometry regression tests pass. Civilian body paint remains independently editable. Blue light names/materials remain separate; POLIS lettering and yellow paint are absent. No LOD or several-car GPU benchmark was added. Factory-perfect dimensions, exhaustive all-component collision proof and human visual approval are not claimed.</p><nav><a href="validator-tests.txt">Vehicle tests</a><a href="silhouette-tests.txt">Silhouette tests</a><a href="shared-geometry-tests.txt">Shared geometry tests</a><a href="../saab900/references.md">Saab references</a><a href="../volvo240/references.md">240 references</a><a href="../xc70p2/references.md">XC70 references / licences</a></nav><p>Reference images: original manufacturer technical-study excerpts; Alexander Migl / Vauxford / Ethan Llamas under their recorded CC BY-SA licences; Bull-Doser public domain. No reference photograph is embedded in a game model or used as a texture. Full attribution and source limits remain in each reference register.</p></section></main></html>'
(P/'index.html').write_text(html)
# One compact source/model package. Full PNGs remain available on the review page.
with zipfile.ZipFile(P/'vehicle-round2.zip','w',zipfile.ZIP_DEFLATED) as z:
    def add(f):z.write(f,f.relative_to(ROOT))
    for car,spec in config.items():
        if car=='xc70police':continue
        modeldir=(ROOT/spec['blend']).parents[1]
        for f in modeldir.glob('*'):
            if f.is_file() and f.suffix in ('.py','.json','.md'):add(f)
        add(ROOT/spec['blend'])
    for spec in config.values():add(ROOT/spec['glb'])
    for f in P.glob('*'):
        if f.is_file() and f.suffix in ('.py','.json','.md','.sh','.txt','.html'):add(f)
    for f in OUT.glob('*.png'):add(f)
    for f in (P/'baseline-inventory').glob('*.json'):add(f)
    for f in BUILD.rglob('*.json'):
        if not any(x.endswith('-log') for x in f.parts):add(f)
    for f in (ROOT/'tools/vehicle_pipeline').glob('*'):
        if f.is_file():add(f)
    add(ROOT/'LICENSE')
# Exact small static publication set; do not copy unused raw sheets to hosting.
manifest=set([P/'index.html',P/'summary.json',P/'README.md',P/'vehicle-round2.zip'])
manifest.update(P.glob('*-tests.txt'));manifest.update(OUT.glob('*.png'))
for car,spec in config.items():
    manifest.update([ROOT/spec['blend'],ROOT/spec['glb']])
    prefix='shaded' if car=='xc70police' else 'clay'
    manifest.update((BUILD/car/'after/views').glob(prefix+'_*.png'))
    manifest.add(BUILD/car/'pose.json')
    shared='xc70p2' if car=='xc70police' else car
    for name in ['geometry.json','reproduction.json']:manifest.add(BUILD/shared/name)
for name in ['architecture-mutation','mutation-export-shared','before-window-seating','after-window-seating']:manifest.add(BUILD/'xc70p2'/(name+'.json'))
for view in ['inside_rear','inside_side']:manifest.add(BUILD/'xc70police/after'/(view+'.png'))
for stage in ['before','after']:
    for name in ['overlay.png','report.json']:manifest.add(BUILD/'saab900/silhouette'/stage/'comparison'/name)
manifest.add(ROOT/'experiments/xc70p2/build/shared-export-geometry.json')
(P/'hosting-manifest.json').write_text(json.dumps([str(f.relative_to(ROOT)) for f in sorted(manifest)],indent=2)+'\n')
print(json.dumps({'review':'experiments/round2/index.html','zip_mb':round((P/'vehicle-round2.zip').stat().st_size/1e6,2),'hosting_files':len(manifest),'hosting_bytes_mb':round(sum(f.stat().st_size for f in manifest)/1e6,2)}))
