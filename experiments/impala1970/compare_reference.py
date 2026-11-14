"""Limited glass-region comparison using the existing silhouette algorithms."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/vehicle_pipeline'))
import verify_silhouette as V
here=Path(__file__).resolve().parent;cfg=V.read_json(here/'silhouette.json');out=here/'review';out.mkdir(exist_ok=True)
reference=cfg['reference'];ri,rm,rw=V.extract(reference,here);rt=V.registration(reference,3.0226);background,ref=V.normalize(ri,rm,rt)
results={}
font=ImageFont.truetype('DejaVuSans.ttf',22)
for stage in ['blockout','final']:
    folder=here/'build'/stage/'silhouette';mf=V.read_json(folder/'glass-frame.json');mi,mm,mw=V.extract(mf,folder);mt=V.registration(mf,3.0226);_,mod=V.normalize(mi,mm,mt)
    gm,lm,distance=V.compare(ref,mod,cfg['regions'])
    # Do not label aperture bounds as vehicle length or overhang errors.
    metrics={k:gm[k] for k in ['iou','mean_contour_distance_px','max_contour_distance_px']}
    results[stage]={'side_glass_aperture_only':metrics,'regions':lm,'independent_render_wheelbase_m':float(np.linalg.norm(np.array(mf['front_wheel'])-mf['rear_wheel'])/mf['pixels_per_metre'])}
    rgb=(np.array(background.convert('RGB'))*.57+100).clip(0,255).astype('uint8');rc=V.contour(ref);mc=V.contour(mod)
    from scipy.ndimage import binary_dilation
    rgb[binary_dilation(rc)]=(226,65,72);rgb[binary_dilation(mc)]=(0,155,185)
    im=Image.fromarray(rgb);d=ImageDraw.Draw(im);d.rectangle((0,0,1600,88),fill='white')
    d.text((20,10),f'{stage.upper()} | SIDE GLASS ONLY | red: manual photo trace; cyan: actual mesh',font=font,fill='black')
    d.text((20,45),'Perspective / snow / cropped car: no full-car silhouette verdict and no verified mm errors',font=font,fill='black')
    credit='Photo: DanTD / Wikimedia Commons, CC BY-SA 4.0 | York and Bridge Streets-2 | manual trace + overlay adaptation'
    small=ImageFont.truetype('DejaVuSans.ttf',17);d.rectangle((0,620,1600,650),fill='white');d.text((20,627),credit,font=small,fill='black');im.save(out/f'{stage}-reference-overlay.png')
    crop=im.crop((440,150,1230,370));panel=Image.new('RGB',(1580,480),'white');panel.paste(crop.resize((1580,440)),(0,0));ImageDraw.Draw(panel).text((15,449),credit,font=small,fill='black');panel.save(out/f'{stage}-glass-detail.png')
    hm=np.full((650,1600,3),245,dtype='uint8');hm[ref^mod]=(240,208,150)
    for y,x in np.argwhere(mc):
        t=min(1,distance[y,x]/25);hm[max(0,y-2):y+3,max(0,x-2):x+3]=(int(255*t),int(160*(1-t)),50)
    heat=Image.fromarray(hm);ImageDraw.Draw(heat).text((20,20),'SIDE GLASS ONLY | green: 0 px; red: 25+ canonical px | uncertain perspective reference',font=font,fill='black');heat.save(out/f'{stage}-glass-deviation.png')
report={'vehicle':cfg['vehicle'],'reference':reference,'mask_scope':cfg['mask_scope'],'uncertainties':cfg['uncertainties'],'method':'Existing verify_silhouette.extract / registration / normalize / compare. Uniform axle / ground registration; no overlap fitting.','units':'canonical pixels at 280 px/m; estimates only','full_car_silhouette':{'verified':False,'iou':None,'reason':'No trustworthy complete orthographic 16439 reference was obtained; cropped snowy photograph cannot establish global body proportions.'},'stages':results}
(out/'reference-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(results,indent=2))
