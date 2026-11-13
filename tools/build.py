"""Builds the two standalone pages (index.html = game, map.html = 3D map) from src/ and data/raw/."""
import json, os, subprocess, sys, re

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(root, 'data', 'vrigstad.json')
subprocess.run([sys.executable, os.path.join(root, 'tools', 'process.py'), os.path.join(root, 'data', 'raw'), data_path], check=True)

data = json.load(open(data_path, encoding='utf-8'))
order = ['Vrigstad Kyrka', 'Torget', 'Vrigstad Värdshus', 'Slättsjön', 'Lundholmssjön', 'Vrigstadsån']
data['labels'].sort(key=lambda l: order.index(l['t']) if l['t'] in order else 99)
blob = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
assert '</script' not in blob

HEAD = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        '<style>body{margin:0;font:14px system-ui,sans-serif}[hidden]{display:none!important}</style>\n</head>\n<body>\n')
for src, out in (('game.html', 'index.html'), ('map.html', 'map.html')):
    page = open(os.path.join(root, 'src', src), encoding='utf-8').read()
    assert page.count('/*DATA*/') == 1
    if src == 'game.html':
        for marker,filename,exports in [('DAYLIGHT','daylight.mjs','VRIGSTAD, DEFAULT_SOLAR_DATE, solarPosition, weatherCoverage, daylightState, createSolarClock, createDaylightController'),('STREET_LIGHTING','street-lighting.mjs','streetlightLevel,placeStreetlights,createStreetLighting'),('VISUAL_LAB','visual-lab.js',None)]:
            assert page.count('/*'+marker+'*/') == 1
            code=open(os.path.join(root,'src','visual',filename),encoding='utf-8').read()
            if exports:
                code=re.sub(r'(?m)^export\s+','',code)
                code='const '+marker+'=(()=>{\n'+code+'\nreturn {'+exports+'};})();\n'
            page=page.replace('/*'+marker+'*/',code)
    open(os.path.join(root, out), 'w', encoding='utf-8').write(HEAD + page.replace('/*DATA*/', blob) + '</body>\n</html>\n')
    print('built', out)
