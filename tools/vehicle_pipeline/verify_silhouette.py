"""Axle-registered silhouette and annotated-curve comparison; no fitted proportions.

Usage: python verify_silhouette.py CONFIG MODEL_FRAME --out DIRECTORY [--baseline REPORT]
Frame coordinates are image pixels; regions use metres from the rear axle/ground.
Only similarity registration from wheel centres is allowed. Source calibration is
checked independently: registration itself cannot validate its own axle anchors.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps
from scipy import ndimage as ndi

SIZE = (1600, 650)
PPM = 280.0
ORIGIN = np.array([470., 565.])


def read_json(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError(f'Missing configuration or annotation: {path}')
    return json.loads(path.read_text())


def extract(frame, root):
    path = root / frame['image']
    if not path.is_file():
        raise ValueError(f'Missing reference/render image: {path}')
    im = Image.open(path).convert('RGBA')
    mode = frame['mask']['mode']
    warnings = []
    if mode == 'alpha':
        alpha = np.asarray(im)[..., 3]
        if alpha.min() == alpha.max():
            raise ValueError('Alpha mask is constant: transparent orthographic render required')
        mask = alpha > 127
    elif mode == 'manual_polygon':
        layer = Image.new('L', im.size)
        ImageDraw.Draw(layer).polygon([tuple(p) for p in frame['mask']['polygon']], fill=255)
        mask = np.asarray(layer) > 127
    elif mode == 'manual_mask':
        mp = root / frame['mask']['path']
        if not mp.is_file():
            raise ValueError(f'Missing manual mask: {mp}')
        layer = Image.open(mp).convert('L')
        if layer.size != im.size:
            raise ValueError('Manual mask and source image dimensions differ')
        mask = np.asarray(layer) > 127
    elif mode == 'background':
        rgb = np.asarray(im)[..., :3].astype(float)
        corners = np.array([rgb[0,0], rgb[-1,0], rgb[0,-1], rgb[-1,-1]])
        bg = np.median(corners, axis=0)
        mask = np.linalg.norm(rgb-bg, axis=2) > frame['mask'].get('threshold', 50)
        labels, n = ndi.label(mask)
        if n:
            counts = np.bincount(labels.ravel()); counts[0] = 0
            mask = ndi.binary_fill_holes(labels == counts.argmax())
        warnings.append('Automatic background segmentation requires explicit human mask review; shadows may survive')
    else:
        raise ValueError(f'Unknown mask mode: {mode}')
    coverage = float(mask.mean())
    if coverage < .005 or coverage > .95:
        warnings.append('INVALID mask coverage (empty, tiny or full-frame)')
    if mask[0].any() or mask[-1].any() or mask[:,0].any() or mask[:,-1].any():
        warnings.append('Mask touches image border: possible truncation')
    if not frame['mask'].get('reviewed', False):
        warnings.append('UNREVIEWED mask; reference geometry is not verified')
    if not mask.any():
        raise ValueError('Empty silhouette mask')
    labels, n = ndi.label(mask)
    substantial = sum(v > mask.sum()*.02 for v in np.bincount(labels.ravel())[1:])
    if substantial > 1:
        warnings.append(f'Mask has {substantial} disconnected substantial components')
    return im, mask, warnings


def registration(frame, wheelbase):
    rear = np.array(frame['rear_wheel'], float)
    front = np.array(frame['front_wheel'], float)
    delta = front-rear
    distance = float(np.linalg.norm(delta))
    if distance < 10 or wheelbase <= 0:
        raise ValueError('Wheel centres or documented wheelbase are invalid')
    u = delta/distance
    down = np.array([-u[1], u[0]])
    if down[1] < 0:
        down *= -1
    scale = PPM*wheelbase/distance
    a = np.stack([u, down])*scale
    ground = np.array(frame['ground'], float)
    # Wheel line controls rotation; ground controls vertical origin only.
    offset = ORIGIN - a@rear
    offset[1] = ORIGIN[1] - (a@ground)[1]
    return a, offset, distance/wheelbase


def points_transform(points, transform):
    a, b, _ = transform
    return np.asarray(points)@a.T+b


def normalize(image, mask, transform):
    a,b,_ = transform
    inv = np.linalg.inv(a)
    coeff = tuple(inv[0])+(-float((inv@b)[0]),)+tuple(inv[1])+(-float((inv@b)[1]),)
    mask_image = Image.fromarray(mask.astype('uint8')*255)
    normalized = mask_image.transform(SIZE, Image.Transform.AFFINE, coeff, Image.Resampling.NEAREST)
    bg = image.transform(SIZE, Image.Transform.AFFINE, coeff, Image.Resampling.BILINEAR)
    return bg, np.asarray(normalized)>127


def contour(mask):
    return mask & ~ndi.binary_erosion(mask)


def bbox(mask):
    y,x = np.nonzero(mask)
    return [int(x.min()),int(y.min()),int(x.max()),int(y.max())]


def envelope(mask, lower=False):
    result = np.full(mask.shape[1], np.nan)
    for x in np.flatnonzero(mask.any(axis=0)):
        yy = np.flatnonzero(mask[:,x]); result[x] = yy[-1] if lower else yy[0]
    return result


def region_box(region):
    x0,x1,z0,z1 = region
    return [int(ORIGIN[0]+x0*PPM),int(ORIGIN[1]-z1*PPM),int(ORIGIN[0]+x1*PPM),int(ORIGIN[1]-z0*PPM)]


def compare(ref, model, regions):
    rc, mc = contour(ref), contour(model)
    dr, dm = ndi.distance_transform_edt(~rc), ndi.distance_transform_edt(~mc)
    distances = np.r_[dr[mc],dm[rc]]
    rb,mb = bbox(ref),bbox(model)
    global_metrics = dict(iou=float((ref&model).sum()/(ref|model).sum()),
        mean_contour_distance_px=float(distances.mean()), max_contour_distance_px=float(distances.max()),
        length_difference_px=(mb[2]-mb[0])-(rb[2]-rb[0]),
        height_difference_px=(mb[3]-mb[1])-(rb[3]-rb[1]),
        front_overhang_difference_px=mb[2]-rb[2],rear_overhang_difference_px=rb[0]-mb[0],
        reference_bbox=rb,model_bbox=mb)
    rt,mt,rl,ml = envelope(ref),envelope(model),envelope(ref,True),envelope(model,True)
    local = {}
    for name, region in regions.items():
        x0,y0,x1,y1 = region_box(region)
        xs = np.arange(max(0,x0),min(SIZE[0],x1))
        good = np.isfinite(rt[xs]) & np.isfinite(mt[xs])
        good &= (rt[xs]>=y0)&(rt[xs]<=y1)&(mt[xs]>=y0)&(mt[xs]<=y1)
        signed = rt[xs[good]]-mt[xs[good]] # positive: model too high
        local[name] = dict(samples=int(good.sum()),
            signed_height_mean_px=float(signed.mean()) if len(signed) else None,
            absolute_height_mean_px=float(np.abs(signed).mean()) if len(signed) else None,
            max_absolute_height_px=float(np.abs(signed).max()) if len(signed) else None)
        region_r=rc[max(0,y0):min(SIZE[1],y1),max(0,x0):min(SIZE[0],x1)]
        region_m=mc[max(0,y0):min(SIZE[1],y1),max(0,x0):min(SIZE[0],x1)]
        dd=dr[max(0,y0):min(SIZE[1],y1),max(0,x0):min(SIZE[0],x1)][region_m]
        ee=dm[max(0,y0):min(SIZE[1],y1),max(0,x0):min(SIZE[0],x1)][region_r]
        all_d=np.r_[dd,ee]
        local[name]['mean_contour_distance_px']=float(all_d.mean()) if len(all_d) else None
        local[name]['max_contour_distance_px']=float(all_d.max()) if len(all_d) else None
        if name == 'underbody':
            ss=rl[xs]-ml[xs];ss=ss[np.isfinite(ss)]
            local[name]['lower_edge_signed_mean_px']=float(ss.mean()) if len(ss) else None
    return global_metrics,local,dr


def annotated_metrics(reference, model, rt, mt):
    out = {'points':{},'curves':{},'provenance':'Reference annotations are manual; model annotations are projected geometry'}
    for name,p in reference.get('points',{}).items():
        if name not in model.get('points',{}):
            out['points'][name]={'missing_model_point':True};continue
        rp=points_transform([p],rt)[0];mp=points_transform([model['points'][name]],mt)[0]
        out['points'][name]=dict(dx_px=float(mp[0]-rp[0]),height_difference_px=float(rp[1]-mp[1]),distance_px=float(np.linalg.norm(mp-rp)))
    for name,points in reference.get('curves',{}).items():
        if name not in model.get('curves',{}):
            out['curves'][name]={'missing_model_curve':True};continue
        r=points_transform(points,rt);m=points_transform(model['curves'][name],mt)
        r=r[np.argsort(r[:,0])];m=m[np.argsort(m[:,0])]
        lo,hi=max(r[0,0],m[0,0]),min(r[-1,0],m[-1,0])
        if hi<=lo:
            out['curves'][name]={'no_shared_longitudinal_domain':True,'endpoint_distances_px':np.linalg.norm(r[[0,-1]]-m[[0,-1]],axis=1).tolist()}
            continue
        xx=np.linspace(lo,hi,100)
        diff=np.interp(xx,r[:,0],r[:,1])-np.interp(xx,m[:,0],m[:,1])
        def angles(p):
            v=np.diff(p,axis=0)
            return np.degrees(np.arctan2(-v[:,1],v[:,0])).tolist()
        out['curves'][name]=dict(signed_height_mean_px=float(diff.mean()),absolute_height_mean_px=float(np.abs(diff).mean()),
            max_absolute_height_px=float(np.abs(diff).max()),reference_segment_angles_deg=angles(r),model_segment_angles_deg=angles(m),
            reference_turn_angles_deg=np.diff(angles(r)).tolist(),model_turn_angles_deg=np.diff(angles(m)).tolist())
    return out


def analyze(config_path, model_path, out_path, baseline=None):
    cp,mp=Path(config_path).resolve(),Path(model_path).resolve()
    cfg=read_json(cp);model=read_json(mp);reference=cfg['reference'];wb=cfg['dimensions']['wheelbase_m']['value']
    ri,rm,rw=extract(reference,cp.parent);mi,mm,mw=extract(model,mp.parent)
    rt,mt=registration(reference,wb),registration(model,wb)
    bg,ref=normalize(ri,rm,rt);_,mod=normalize(mi,mm,mt)
    gm,lm,distance=compare(ref,mod,cfg['regions'])
    annotations=annotated_metrics(reference,model,rt,mt)
    warnings=rw+mw+cfg.get('uncertainties',[])
    if not reference.get('orthographic') or not reference.get('metric_reliable'):
        warnings.append('REFERENCE NOT METRIC-VERIFIED: no exact millimetre geometric verdict is permitted')
    extents={}
    for name,mask in [('reference',ref),('model',mod)]:
        bb=bbox(mask);top=envelope(mask);minimum=np.nanmin(top)
        roof_x=np.flatnonzero(top<=minimum+3)
        extents[name]=dict(length_wheelbase_scaled_m=(bb[2]-bb[0])/PPM,height_wheelbase_scaled_m=(bb[3]-bb[1])/PPM,
            front_overhang_wheelbase_scaled_m=(bb[2]-ORIGIN[0]-wb*PPM)/PPM,rear_overhang_wheelbase_scaled_m=(ORIGIN[0]-bb[0])/PPM,
            roof_highest_x_from_rear_axle_m=[float((roof_x.min()-ORIGIN[0])/PPM),float((roof_x.max()-ORIGIN[0])/PPM)])
    scale_check={}
    for label,frame,tr in [('reference',reference,rt),('model',model,mt)]:
        if 'pixels_per_metre' in frame:
            actual=np.linalg.norm(np.array(frame['front_wheel'])-frame['rear_wheel'])/frame['pixels_per_metre']
            scale_check[label]=dict(independent_wheelbase_m=float(actual),error_m=float(actual-wb),scale_error_fraction=float(tr[2]/frame['pixels_per_metre']-1))
            if abs(actual-wb)>.01:
                warnings.append(f'{label}: independent camera calibration detects wheelbase/scale mismatch')
    reliable=bool(reference.get('orthographic') and reference.get('metric_reliable') and reference['mask'].get('reviewed') and not rw)
    report=dict(vehicle=cfg['vehicle'],reference_information={k:v for k,v in reference.items() if k not in ('mask','curves','points')},
        dimensions=cfg['dimensions'],normalization=dict(method='uniform similarity from rear/front wheel centres; ground fixes vertical position; no overlap fitting',
        canonical_pixels_per_metre=PPM,reference_source_pixels_per_metre=rt[2],model_source_pixels_per_metre=mt[2],independent_calibration=scale_check),
        global_metrics=gm,local_metrics=lm,internal_annotations=annotations,derived_extents=extents,
        data_quality=dict(metric_geometry_verified=reliable,reference_mask_reviewed=reference['mask'].get('reviewed',False),
            units='canonical pixels; divide by 280 for wheelbase-scaled metres (estimates unless metric_geometry_verified)',warnings=warnings,
            included=cfg.get('mask_scope'),anchor_caveat='Registration forces axle anchors to agree. Only independent calibration or held-out points can verify axle placement.'),
        largest_local_deviations=sorted([dict(region=k,**v) for k,v in lm.items() if v['max_absolute_height_px'] is not None],key=lambda a:a['max_absolute_height_px'],reverse=True))
    if reliable:
        report['global_metrics_mm']={k.replace('_px','_mm'):v/PPM*1000 for k,v in gm.items() if k.endswith('_px')}
    if baseline:
        old=read_json(baseline)
        report['before_after']={'before_iou':old['global_metrics']['iou'],'after_iou':gm['iou'],
          'local_absolute_height_change_px':{k:v['absolute_height_mean_px']-old['local_metrics'][k]['absolute_height_mean_px'] for k,v in lm.items() if v['absolute_height_mean_px'] is not None and old['local_metrics'][k]['absolute_height_mean_px'] is not None}}
    out=Path(out_path);out.mkdir(parents=True,exist_ok=True)
    # The normalized source is retained behind the contours; never resize each car independently.
    grey=np.asarray(bg.convert('RGB')).copy();grey=(grey*.32+165).clip(0,255).astype('uint8')
    rc,mc=contour(ref),contour(mod)
    rgb=grey.copy();rgb[ndi.binary_dilation(rc)]=(235,58,83);rgb[ndi.binary_dilation(mc)]=(0,150,190)
    overlay=Image.fromarray(rgb);draw=ImageDraw.Draw(overlay)
    font=ImageFont.truetype('DejaVuSans.ttf',23)
    draw.rectangle((0,0,1600,76),fill='white');draw.text((20,8),'REFERENCE: RED   MODEL: CYAN | axle / ground registration | no proportion fitting',font=font,fill='black')
    draw.text((20,40),'Metric reference' if reliable else 'UNCERTAIN REFERENCE: comparative estimates, not verified millimetre errors',font=font,fill='black')
    for frame,tr,color in [(reference,rt,'red'),(model,mt,'blue')]:
        for pts in frame.get('curves',{}).values():
            pts=points_transform(pts,tr);draw.line([tuple(p) for p in pts],fill=color,width=2)
    overlay.save(out/'overlay.png')
    heat=np.full((SIZE[1],SIZE[0],3),245,dtype='uint8')
    heat[ref^mod]=(240,200,130)
    for y,x in np.argwhere(mc):
        t=min(1,distance[y,x]/25);heat[max(0,y-2):y+3,max(0,x-2):x+3]=(int(255*t),int(160*(1-t)),50)
    hm=Image.fromarray(heat);ImageDraw.Draw(hm).text((20,15),'Green: 0 px  >  red: 25+ px | tan: mask disagreement | canonical pixels',font=font,fill='black');hm.save(out/'deviation.png')
    for name,region in cfg['regions'].items():
        if name in ('hood','windscreen','roof','rear'):
            crop=ImageOps.contain(overlay.crop(tuple(region_box(region))),(1200,650))
            panel=Image.new('RGB',(1240,710),'white');panel.paste(crop,((1240-crop.width)//2,50))
            ImageDraw.Draw(panel).text((20,12),name.upper()+' | red reference / cyan model | uncertain proxy',font=font,fill='black')
            panel.save(out/f'region-{name}.png')
    (out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config');parser.add_argument('model_frame');parser.add_argument('--out',required=True);parser.add_argument('--baseline');parser.add_argument('--require-metric-reference',action='store_true')
    args=parser.parse_args()
    try:
        report=analyze(args.config,args.model_frame,args.out,args.baseline)
        if args.require_metric_reference and not report['data_quality']['metric_geometry_verified']:
            parser.exit(3,'Reference is not metric-verified; see generated report warnings.\n')
        print(json.dumps({'iou':report['global_metrics']['iou'],'quality':report['data_quality']},indent=2))
    except (ValueError,KeyError,OSError) as exc:
        parser.exit(2,f'Silhouette verification failed: {exc}\n')
