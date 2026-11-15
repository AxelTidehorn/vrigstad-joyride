"""Wheel-registered manual upper-profile check; uses existing ortho renderer frames."""
from pathlib import Path
import json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent;OUT=HERE/'refinement'
r=json.loads((OUT/'profile-reference.json').read_text());f=np.array(r['front_wheel_px'],float);b=np.array(r['rear_wheel_px'],float);forward=(f-b)/np.linalg.norm(f-b);up=np.array([forward[1],-forward[0]]);scale=np.linalg.norm(f-b)/r['wheelbase_m'];ref=np.array(r['upper_trace_px'],float)
stations=[r['rear_axle_y_m']+float(np.dot(p-b,forward))/scale for p in ref]
cfg={'blender':{'body_object':'body','skip_quality':True,'quality_focus':[[-1,-2.05,0],[1,2.05,1.53]],'orthographic_scale_m':4.2,'curve_stations_y':{'upper_profile':stations}}}
(OUT/'ortho-config.json').write_text(json.dumps(cfg,indent=2)+'\n')
paths={stage:OUT/stage/'ortho/frame.json' for stage in ['before','after']}
if not all(p.exists() for p in paths.values()):print('Prepared exact ortho config. Render both masters, then rerun.');raise SystemExit(0)
BG=(237,234,224);INK=(35,49,45);font=lambda n:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
report={'reference':r,'scale_source_px_per_m':scale,'registration':'one uniform rotation / scale from wheel centres; no fitting','units':'source photo pixels; manual/perspective estimates, not validated millimetres','stages':{}}
regions={'rear':range(0,3),'roof':range(3,7),'windshield_transition':range(7,10),'hood_front':range(10,13)}
for stage,path in paths.items():
 frame=json.loads(path.read_text());curve=frame['curves']['upper_profile'];rb=np.array(frame['rear_wheel']);ppm=frame['pixels_per_metre'];projected=[]
 for x,y in curve:
  dy=(x-rb[0])/ppm;dz=(rb[1]-y)/ppm;projected.append(b+scale*(dy*forward+dz*up))
 projected=np.array(projected);dev=(projected-ref)@up
 report['stages'][stage]={'signed_height_source_px':dev.tolist(),'mean_absolute_height_source_px':float(np.mean(abs(dev))),'regions':{name:{'mean_absolute_height_source_px':float(np.mean(abs(dev[list(ids)]))),'mean_signed_height_source_px':float(np.mean(dev[list(ids)]))} for name,ids in regions.items()}}
 im=Image.new('RGB',(1800,960),BG);d=ImageDraw.Draw(im);color=(190,94,40) if stage=='before' else (27,112,88)
 d.text((30,20),'K11 UPPER PROFILE · '+stage.upper()+' · WHEEL-REGISTERED',font=font(29),fill=INK)
 d.text((30,65),'Black: manual reference trace. Colour: actual Blender profile. Perspective estimates; no IoU / metric approval.',font=font(21),fill=INK)
 point=lambda p:(round(70+p[0]*2),round(80+p[1]*2))
 d.line([point(p) for p in ref],fill=(45,48,45),width=5);d.line([point(p) for p in projected],fill=color,width=5)
 for a,c in zip(ref,projected):d.line([point(a),point(c)],fill=color,width=2);x,y=point(c);d.ellipse((x-5,y-5,x+5,y+5),fill=color)
 for p in [b,f]:x,y=point(p);d.ellipse((x-9,y-9,x+9,y+9),outline=INK,width=3)
 for i,(name,value) in enumerate(report['stages'][stage]['regions'].items()):d.text((35+i*440,845),name.replace('_',' ')+': '+str(round(value['mean_absolute_height_source_px'],1))+' px',font=font(22),fill=INK)
 d.text((35,905),'No photograph redistributed. Manual trace +/-6 px; wheel anchors +/-4 px. Source / limitations in profile-reference.json.',font=font(21),fill=INK)
 im.save(OUT/f'profile-{stage}.png',optimize=True)
(OUT/'profile-comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['stages'],indent=2))
