# Volvo Duett P210 EPA pickup

Original conversion-specific model built on the established Blender Modeler → repository exporter → actual GLB validator pipeline. Authoring X right, Y forward, Z up; exported Y-up / -Z-forward, metres.

## Build

Verified with Blender 4.3.2, calebrisc/blender-modeler commit `c8f245982108e2627972768d4311cbe172b58137`, and tools/vehicle_pipeline/requirements.txt. No new runtime dependency.

```bash
BMOD=/path/to/blender-modeler/scripts/bmod.py VEHICLE_PYTHON=/path/to/python bash experiments/duettp210/build.sh
blender -b --python-exit-code 1 --python tools/vehicle_pipeline/reimport_check.py -- media/vehicles/duett-p210-epa.glb
python3 tools/build.py
npm run test:vehicles
npm run test:driving
npx playwright test tests/e2e/duett.spec.js
python3 experiments/duettp210/package.py
```

`model.py` is the single authoritative source, controlled by `parameters.json`. Unique P210 sections include the narrow domed bonnet and pronounced rolled front wings, short cab, almost vertical rear wall and rear fender volumes. The steel is one continuous loft, with an actual boolean bed cavity and closed wheel-well cuts. The cab was not produced by deleting a wagon roof. Glazing derives from inset steel faces; rear glazing has a seated closed frame on the new rear wall. Bed side walls, gate, floor, inner walls and wing attachments are part of that one closed body. The darker bed-floor liner is a separate physical component in contact with its floor.

Collections: BODY, GLASS, BED, CHROME, RUBBER, LIGHTS, DETAILS, WHEELS. Exactly four hub-centred wheel_* objects with rim fixtures; all other components follow body. Static detail meshes are batched by material. Eleven simple materials; only the body paint is recoloured by the unchanged adapter. No texture images.

## Visual iteration

The first actual blockout and its seven fixed views are retained under `blockout/`. Inspection identified a windshield/cab front that was too raked and modern compared with the Hova conversion. The existing source was changed: roof leading stations raised 30/80 mm, windshield base moved rearward from .68 to .60 m, side-glass front bottom pulled back from .59 to .50 m, windshield upper/lower range .30–.55 m. Peak roof remains 1.70 m and axles are unchanged. Final full renders use identical cameras and focus bounds.

Additional checks rejected intersecting cowl sections, an incorrect initial bed subtraction, face-offset glass fragments and a collapsing thin grille bevel. Delivered source corrects the actual geometry: continuous cowl sections, common pane normal offset and extruded rounded detail outlines. No failed iteration is exported as the final model. The initial raw blockout is development evidence, not an approved game asset.

The final seven views, including the open-bed overhead, were visually inspected. Main remaining uncertainties are the uncalibrated EPA cab/bed dimensions and simplified wing/roof corner treatment, window seals, grille and standard hub covers. The result is a stylised interpretation of the selected conversion, not an exact replica or legal EPA certification. Human visual approval remains pending.

## Integration

New `duett` entry in src/vehicles/vehicle-assets.mjs, with its own GLB, radius and type/name/colour palette. It uses the existing EPA TYPES fallback and handling values unchanged and the shared RWD physics class. These are temporary compatible settings, not measured Duett performance. The physics, engine and transmission modules are unchanged. All existing vehicle assets remain byte-identical.

Choose it with `index.html?vehicle=duett` or the intro link. Only this explicit selection changes the nearest Torget showcase slot; the default four-car lineup is unchanged. No default traffic distribution or existing EPA vehicle replacement is made.

## Validation limits

See build/report.txt (Modeler), source-audit.json, geometry.json, pose.json, reimport.json and integration/play/driving test logs. Audit verifies closed body, winding, degenerate faces, self-intersection candidates, wheel/tyre clearance, glass seating, hierarchy, dimensions, polygon budget and nine vertical open-bed probes. Intersections between deliberately joined separate detail components are reported as candidates; a renderer and the fixed views are also necessary. No physical iPad Safari or hardware FPS benchmark has been performed.

Final regression result: five game/map smoke tests, the dedicated Duett selection/entry/driving test, five validator unit tests, vehicle GLB integration checks and V4 driving regression all pass.
