#!/usr/bin/env bash
set -euo pipefail
PYTHON=${PYTHON:-python3}
for variant in civilian police; do
 blender -b --python-exit-code 1 --python tools/vehicle_pipeline/blender_import.py -- --source "experiments/xc70p2/build/$variant.blend" --output "experiments/xc70p2/build/xc70-$variant.glb" --previews "experiments/xc70p2/build/$variant/repository_previews"
 "$PYTHON" tools/vehicle_pipeline/validate.py "experiments/xc70p2/build/xc70-$variant.glb" "experiments/xc70p2/$variant.json" --report "experiments/xc70p2/build/$variant/geometry.json"
 blender -b --python-exit-code 1 --python tools/vehicle_pipeline/reimport_check.py -- "experiments/xc70p2/build/xc70-$variant.glb"
 mv experiments/xc70p2/build/reimport.json "experiments/xc70p2/build/$variant/reimport.json"
 node tools/vehicle_pipeline/check_preview_glb.mjs "experiments/xc70p2/build/xc70-$variant.glb" "experiments/xc70p2/build/$variant/three-loader.json"
done
