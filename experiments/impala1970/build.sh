#!/usr/bin/env bash
# Maintainer/Codex reproduction; reviewers use the hosted gallery without setup.
set -euo pipefail
cd "$(dirname "$0")/../.."
vehicle_modeler="${BMOD:?Set BMOD to the pinned blender-modeler scripts/bmod.py}"
vehicle_python="${VEHICLE_PYTHON:-python3}"
vehicle_dir=experiments/impala1970
python3 "$vehicle_modeler" --model "$vehicle_dir/model.py" --spec "$vehicle_dir/spec.json" --out "$vehicle_dir/build" --mode none
python3 "$vehicle_modeler" --script "$vehicle_dir/audit.py" --blend "$vehicle_dir/build/model.blend" --out "$vehicle_dir/build/audit-log" -- "$vehicle_dir/build/source-audit.json"
"$vehicle_python" -c 'import json; assert json.load(open("experiments/impala1970/build/source-audit.json"))["ok"]'
blender -b --python-exit-code 1 --python tools/vehicle_pipeline/blender_import.py -- --source "$vehicle_dir/build/model.blend" --output "$vehicle_dir/build/impala1970-hardtop.glb" --previews "$vehicle_dir/build/export-previews"
"$vehicle_python" tools/vehicle_pipeline/validate.py "$vehicle_dir/build/impala1970-hardtop.glb" "$vehicle_dir/vehicle.json" --report "$vehicle_dir/build/geometry.json"
blender -b --python-exit-code 1 --python tools/vehicle_pipeline/reimport_check.py -- "$vehicle_dir/build/impala1970-hardtop.glb"
node tools/vehicle_pipeline/check_preview_glb.mjs "$vehicle_dir/build/impala1970-hardtop.glb" "$vehicle_dir/build/three-loader.json"
node "$vehicle_dir/paint-test.mjs"
python3 "$vehicle_modeler" --script experiments/round2/pose_audit.py --out "$vehicle_dir/build/pose-log" -- "$vehicle_dir/build/impala1970-hardtop.glb" "$vehicle_dir/build/pose.json"
"$vehicle_python" -c 'import json; assert json.load(open("experiments/impala1970/build/pose.json"))["ok"]'
python3 "$vehicle_modeler" --script "$vehicle_dir/review.py" --blend "$vehicle_dir/build/model.blend" --out "$vehicle_dir/build/render-log" -- "$vehicle_dir/build/final" shaded
python3 "$vehicle_modeler" --script "$vehicle_dir/silhouette.py" --blend "$vehicle_dir/build/model.blend" --out "$vehicle_dir/build/final/silhouette-log" -- "$vehicle_dir/build/final/silhouette"
"$vehicle_python" "$vehicle_dir/compare_reference.py"
