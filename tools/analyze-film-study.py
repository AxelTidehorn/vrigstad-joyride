"""Descriptive screenshot measurements, not a renderer pixel-regression test.

Requires Pillow for development only. Regions intentionally exclude DOM overlays.
"""
from pathlib import Path
from PIL import Image, ImageChops, ImageStat
import json
out=Path('docs/film-study')
results={}
for site in ['torget','residential','rural','industrial']:
    base=Image.open(out/f'{site}-negative.png').convert('RGB').crop((0,230,1280,720))
    rows={}
    for preset in ['off','chrome','negative','gold','portra']:
        image=Image.open(out/f'{site}-{preset}.png').convert('RGB')
        scene=image.crop((0,230,1280,720))
        pixels=list(scene.getdata())
        lum=sorted(.2126*r+.7152*g+.0722*b for r,g,b in pixels)
        rows[preset]={
            'scene_mean_absolute_RGB_difference_from_negative':round(sum(ImageStat.Stat(ImageChops.difference(base,scene)).mean)/3,3),
            'scene_any_channel_255_percent':round(100*sum(max(p)==255 for p in pixels)/len(pixels),4),
            'scene_black_RGB_percent':round(100*sum(max(p)==0 for p in pixels)/len(pixels),4),
            'scene_luma_p01':round(lum[len(lum)//100],2),
            'scene_luma_p99':round(lum[len(lum)*99//100],2),

        }
    results[site]=rows
(out/'image-analysis.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
