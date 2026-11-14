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
        assert page.count('/*VEHICLE_MODELS*/') == 1
        models = open(os.path.join(root, 'src', 'vehicles', 'vehicle-library.mjs'), encoding='utf-8').read()
        models = re.sub(r'(?m)^export\s+', '', models)
        models = 'const VEHICLE_MODELS = (() => {\n' + models + '\nreturn {createVehicleGeometry};\n})();\n'
        page = page.replace('/*VEHICLE_MODELS*/', models)
        assert page.count('/*GLB_VEHICLE_ASSETS*/') == 1
        asset_loader = open(os.path.join(root, 'src', 'vehicles', 'vehicle-assets.mjs'), encoding='utf-8').read()
        asset_loader = re.sub(r'(?m)^export\s+', '', asset_loader)
        asset_loader = 'const VEHICLE_ASSETS = (() => {\n' + asset_loader + '\nreturn {createVehicleAssets};\n})();\n'
        page = page.replace('/*GLB_VEHICLE_ASSETS*/', asset_loader)
        assert page.count('/*DRIVING_PHYSICS*/') == 1
        physics = open(os.path.join(root, 'src', 'physics', 'driving-v4.mjs'), encoding='utf-8').read()
        physics = re.sub(r'(?m)^export\s+', '', physics)
        physics = 'const DRIVING_PHYSICS = (() => {\n' + physics + '\nreturn {newCar,stepCar,VEHICLE_PRESETS};\n})();\n'
        page = page.replace('/*DRIVING_PHYSICS*/', physics)
        assert page.count('/*BODY_MOTION*/') == 1
        motion = open(os.path.join(root, 'src', 'physics', 'body-motion.mjs'), encoding='utf-8').read()
        motion = re.sub(r'(?m)^export\s+', '', motion)
        motion = 'const BODY_MOTION = (() => {\n' + motion + '\nreturn {createBodyMotion,stepBodyMotion};\n})();\n'
        page = page.replace('/*BODY_MOTION*/', motion)
        assert page.count('/*HOUSE_MODELS*/') == 1
        houses = open(os.path.join(root, 'src', 'houses', 'house-library.mjs'), encoding='utf-8').read()
        houses = re.sub(r'(?m)^export\s+', '', houses)
        houses = 'const HOUSE_LIBRARY = (() => {\n' + houses + '\nreturn {HOUSE_TYPES, houseSkin, footprintRect, createHouseGeometry};\n})();\n'
        page = page.replace('/*HOUSE_MODELS*/', houses)
        assert page.count('/*RESIDENTIAL_ENVIRONMENT*/') == 1
        env = open(os.path.join(root, 'src', 'environment', 'residential-neighborhood.mjs'), encoding='utf-8').read()
        env = re.sub(r'(?m)^export\s+', '', env)
        env = 'const RESIDENTIAL_ENV = (() => {\n' + env + '\nreturn {createResidentialNeighborhood};\n})();\n'
        page = page.replace('/*RESIDENTIAL_ENVIRONMENT*/', env)
        assert page.count('/*FILM_PIPELINE*/') == 1
        film = open(os.path.join(root, 'src', 'visual', 'film-pipeline.js'), encoding='utf-8').read()
        page = page.replace('/*FILM_PIPELINE*/', film)
        assert page.count('/*DAYLIGHT_CONTROLLER*/') == 1
        daylight = open(os.path.join(root, 'src', 'visual', 'daylight.mjs'), encoding='utf-8').read()
        daylight = re.sub(r'(?m)^export\s+', '', daylight)
        daylight = 'const DAYLIGHT = (() => {\n' + daylight + '\nreturn {daylightState, createDaylightController};\n})();\n'
        page = page.replace('/*DAYLIGHT_CONTROLLER*/', daylight)
        assert page.count('/*NIGHT_LIGHTING*/') == 1
        night = open(os.path.join(root,'src','visual','night-lighting.mjs'),encoding='utf-8').read()
        night = re.sub(r'(?m)^export\s+', '', night)
        night = 'const NIGHT_LIGHTING = (() => {\n' + night + '\nreturn {windowSites,createWindowLighting,createVehicleLighting};\n})();\n'
        page = page.replace('/*NIGHT_LIGHTING*/', night)
        for marker,filename,exports in [('STREET_LIGHTING','street-lighting.mjs','streetlightLevel, placeStreetlights, createStreetLighting'),('VISUAL_LAB','visual-lab.js',None)]:
            assert page.count('/*'+marker+'*/') == 1
            code = open(os.path.join(root,'src','visual',filename),encoding='utf-8').read()
            if exports:
                code = re.sub(r'(?m)^export\s+', '', code)
                code = 'const '+marker+' = (() => {\n'+code+'\nreturn {'+exports+'};\n})();\n'
            page = page.replace('/*'+marker+'*/',code)
    open(os.path.join(root, out), 'w', encoding='utf-8').write(HEAD + page.replace('/*DATA*/', blob) + '</body>\n</html>\n')
    print('built', out)
