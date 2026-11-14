"""Assemble reproducible before/after PNG sheets and the model-delta audit.
Usage: python silhouette_review.py experiment/silhouette
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

def run(root):
    root=Path(root);font=ImageFont.truetype('DejaVuSans.ttf',23)
    items=[('quality/clay_side.png','Side'),('quality/clay_front_three_quarter.png','Front three-quarter'),('cowl/clay_hood_windscreen.png','Hood / cowl / windshield')]
    for name,items2 in [('comparison-sheet',items),('contour-sheet',[('comparison/overlay.png','Contour overlay'),('comparison/deviation.png','Deviation map')])]:
        width=1800;rowheight=760 if name=='comparison-sheet' else 440
        sheet=Image.new('RGB',(width,70+rowheight*len(items2)),'#efeee8');d=ImageDraw.Draw(sheet)
        for col,stage in enumerate(['before','after']):
            d.text((col*900+25,20),stage.upper(),font=font,fill='#203d39')
            for row,(path,title) in enumerate(items2):
                im=Image.open(root/stage/path).convert('RGB');im.thumbnail((890,rowheight-45))
                x=col*900+(900-im.width)//2;y=70+row*rowheight
                sheet.paste(im,(x,y+35));d.text((col*900+20,y),title,font=font,fill='#203d39')
        sheet.save(root/(name+'.png'))
    audits={n:json.loads((root/n/'geometry-audit.json').read_text()) for n in ['before','after']}
    b,a=audits['before'],audits['after']
    report={'preserved_components':[n for n,h in a['component_sha256'].items() if b['component_sha256'].get(n)==h],
      'adapted_components':[n for n,h in a['component_sha256'].items() if b['component_sha256'].get(n)!=h],
      'adaptation_reason':'Only side trim seating changes with adjacent upper front fender; thickness/style unchanged.',
      'dimensions_before_m':b['dimensions_m'],'dimensions_after_m':a['dimensions_m'],
      'geometry_before':{k:v for k,v in b.items() if k in ('nonmanifold_edges','inconsistent_edges','degenerate_faces','self_intersection_candidates','signed_volume_m3','triangles')},
      'geometry_after':{k:v for k,v in a.items() if k in ('nonmanifold_edges','inconsistent_edges','degenerate_faces','self_intersection_candidates','signed_volume_m3','triangles')},
      'model_changes_units':'mm below are direct Blender measurements, NOT exact errors against the uncertain drawing'}
    def spine(a):
        points={}
        for y,z in a['centreline_y_z_m']:points[y]=max(z,points.get(y,-1))
        return sorted(points.items())
    bs,aas=spine(b),spine(a)
    def height(s,y):return float(np.interp(y,[p[0] for p in s],[p[1] for p in s]))
    stations=[2.10,1.75,1.30,.95,.84,.82,.795,.755,.625,.445,.295]
    report['centreline_height_changes']=[dict(y_m=y,before_m=height(bs,y),after_m=height(aas,y),raise_mm=(height(aas,y)-height(bs,y))*1000) for y in stations]
    report['roof_rear_centreline_identical']=dict((y,z) for y,z in bs if y<=.295)==dict((y,z) for y,z in aas if y<=.295)
    report['front_centreline_identical']=dict((y,z) for y,z in bs if y>=2.1)==dict((y,z) for y,z in aas if y>=2.1)
    report['wheel_centres_identical']=b['wheel_centres_world_m']==a['wheel_centres_world_m']
    report['cowl_sections']={}
    for label,s in [('before',bs),('after',aas)]:
        report['cowl_sections'][label]={}
        for name,ys in [('hood',[.86,.95]),('cowl',[.818,.838]),('windscreen_lower',[.635,.70])]:
            report['cowl_sections'][label][name+'_angle_deg']=math.degrees(math.atan2(height(s,ys[1])-height(s,ys[0]),ys[1]-ys[0]))
    (root/'change-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    # Actual geometry profile diagram exposes the surface sections independently of shading.
    canvas=Image.new('RGB',(1600,700),'#f7f5ee');draw=ImageDraw.Draw(canvas)
    def xy(y,z):return (180+(1.6-y)*900,600-(z-.75)*1100)
    for label,s,color in [('BEFORE',bs,'#cf3652'),('AFTER',aas,'#008fa8')]:
        points=[xy(y,z) for y,z in s if .45<=y<=1.75]
        draw.line(points,fill=color,width=5)
    draw.text((30,20),'ACTUAL BLENDER GEOMETRY | red before / cyan after | local profile, not reference truth',font=font,fill='black')
    for y,z,text in [(.84,1.010,'rear hood / cowl'),(.755,1.035,'windshield base')]:
        x,yy=xy(y,z);draw.ellipse((x-6,yy-6,x+6,yy+6),fill='black');draw.text((x-100,yy+35),text,font=font,fill='black')
    canvas.save(root/'surface-breaks.png')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory');args=p.parse_args();print(json.dumps(run(args.directory),indent=2))
