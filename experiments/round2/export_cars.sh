#!/usr/bin/env bash
# Batch adapter around the unchanged exporter, validator, reimport and Three loader.
set -euo pipefail
PYTHON=${PYTHON:-python3}
for car in saab900 volvo240; do
 if [ "$car" = saab900 ]; then
  folder=experiments/saab900/build
  output=$folder/saab900-t16.glb
  config=experiments/saab900/vehicle.json
  report=$folder/geometry.json
 else
  folder=experiments/volvo240/refinement
  output=$folder/review-only.glb
  config=experiments/volvo240/vehicle.json
  report=$folder/glb_geometry.json
 fi
 blender -b --python-exit-code 1 --python tools/vehicle_pipeline/blender_import.py -- --source "$folder/model.blend" --output "$output" --previews "$folder/repository_previews"
 "$PYTHON" tools/vehicle_pipeline/validate.py "$output" "$config" --report "$report"
 blender -b --python-exit-code 1 --python tools/vehicle_pipeline/reimport_check.py -- "$output"
 node tools/vehicle_pipeline/check_preview_glb.mjs "$output" "experiments/round2/build/$car/three-loader.json"
done
