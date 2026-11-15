#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
vehicle_modeler="${BMOD:?Set BMOD to pinned blender-modeler scripts/bmod.py}"
vehicle_python="${VEHICLE_PYTHON:-python3}"
vehicle_dir=experiments/micra1995
python3 "$vehicle_modeler" --model "$vehicle_dir/model.py" --spec "$vehicle_dir/spec.json" --out "$vehicle_dir/build" --mode none
python3 "$vehicle_modeler" --script "$vehicle_dir/audit.py" --blend "$vehicle_dir/build/model.blend" --out "$vehicle_dir/build/audit-log" -- "$vehicle_dir/build/source-audit.json"
"$vehicle_python" -c 'import json; assert json.load(open("experiments/micra1995/build/source-audit.json"))["ok"]'
blender -b --python-exit-code 1 --python tools/vehicle_pipeline/blender_import.py -- --source "$vehicle_dir/build/model.blend" --output media/vehicles/micra-k11.glb --previews "$vehicle_dir/build/export-previews"
"$vehicle_python" tools/vehicle_pipeline/validate.py media/vehicles/micra-k11.glb "$vehicle_dir/vehicle.json" --report "$vehicle_dir/build/geometry.json"
python3 "$vehicle_modeler" --script experiments/round2/pose_audit.py --out "$vehicle_dir/build/pose-log" -- media/vehicles/micra-k11.glb "$vehicle_dir/build/pose.json"
"$vehicle_python" -c 'import json; assert json.load(open("experiments/micra1995/build/pose.json"))["ok"]'
python3 "$vehicle_modeler" --script "$vehicle_dir/review.py" --blend "$vehicle_dir/build/model.blend" --out "$vehicle_dir/build/render-log" -- "$vehicle_dir/build/views"
