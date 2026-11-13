"""Reproduce one requested blockout revision using the two existing pipelines.

Usage: python run.py --modeler /path/to/blender-modeler --out /path/to/new/review
This never changes parameters, integrates assets, or runs correction cycles.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PIN = 'c8f245982108e2627972768d4311cbe172b58137'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--modeler', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--blender', default='blender')
    args = parser.parse_args()
    modeler, out = args.modeler.resolve(), args.out.resolve()
    if out.exists() and any(out.iterdir()):
        parser.error('Use a new or empty output directory; preserve reviewed iterations.')
    actual = subprocess.check_output(['git', '-C', str(modeler), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != PIN:
        parser.error(f'Expected Blender Modeler {PIN}; found {actual}')
    out.mkdir(parents=True, exist_ok=True)
    bmod = [sys.executable, str(modeler/'scripts/bmod.py'), '--blender', args.blender]
    # Save the exact source and parameters that produced this run.
    for file in ('model.py', 'parameters.json', 'spec.json', 'vehicle.json', 'review.py'):
        shutil.copy2(HERE/file, out/file)
    stages = []

    def run(name, cmd):
        with (out/(name+'.log')).open('w') as stream:
            result = subprocess.run(cmd, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
        stages.append({'stage': name, 'exit_code': result.returncode})
        (out/'run_status.json').write_text(json.dumps(stages, indent=2)+'\n')
        return result.returncode

    if run('build', bmod+['--model', str(HERE/'model.py'), '--spec', str(HERE/'spec.json'),
                         '--out', str(out), '--mode', 'none']):
        return 1
    if run('review', bmod+['--script', str(HERE/'review.py'), '--blend', str(out/'model.blend'),
                          '--out', str(out/'review_log'), '--', str(out)]):
        return 1
    if run('export', [args.blender, '-b', '--python-exit-code', '1', '--python',
                      str(ROOT/'tools/vehicle_pipeline/blender_import.py'), '--',
                      '--source', str(out/'model.blend'), '--output', str(out/'volvo240.glb'),
                      '--previews', str(out/'repository_previews')]):
        return 1
    validator_status = run('validate', [sys.executable, str(ROOT/'tools/vehicle_pipeline/validate.py'),
                                       str(out/'volvo240.glb'), str(HERE/'vehicle.json'),
                                       '--report', str(out/'glb_geometry.json')])
    supplemental = json.loads((out/'supplemental_geometry.json').read_text())
    supplemental_rejected = any(supplemental[k] for k in (
        'boundary_or_nonmanifold_edges', 'inconsistent_winding_edges',
        'degenerate_triangles', 'nonadjacent_bvh_overlap_pairs'))
    # Never promote Modeler's zero-error summary over the stricter vehicle checks.
    return int(bool(validator_status or supplemental_rejected))


if __name__ == '__main__':
    sys.exit(main())
