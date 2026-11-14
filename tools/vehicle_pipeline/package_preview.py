"""Package the existing vehicle viewer and reviewed checkpoint for static hosting.

This copies reviewed artifacts without rerunning or repairing the vehicle model.
Maintainer/Codex use only: users review the hosted page without local software.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CHECKPOINT = ROOT / 'experiments/volvo240'
MEDIA = ROOT / 'media/vehicles'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_checkpoint():
    source = CHECKPOINT / 'renders/iter_02'
    dest = MEDIA / 'experiments/volvo240'
    dest.mkdir(parents=True, exist_ok=True)
    files = {
        source/'volvo240.glb': 'volvo240.glb',
        source/'model.blend': 'model.blend',
        source/'clay_sheet.png': 'review-sheet.png',
        source/'glb_geometry.json': 'geometry.json',
        source/'supplemental_geometry.json': 'supplemental.json',
        source/'export_diagnostic.json': 'export-diagnostic.json',
        CHECKPOINT/'side_comparison.png': 'side-comparison.png',
        CHECKPOINT/'references.md': 'references.md',
        CHECKPOINT/'notes.md': 'notes.md',
        CHECKPOINT/'model.py': 'model.py',
        CHECKPOINT/'parameters.json': 'parameters.json',
        CHECKPOINT/'assessment.json': 'assessment.json',
        CHECKPOINT/'spec.json': 'spec.json',
        CHECKPOINT/'vehicle.json': 'vehicle.json',
        ROOT/'LICENSE': 'LICENSE.txt',
    }
    for view in ('front', 'side', 'rear', 'top', 'three_quarter'):
        files[source/f'clay_{view}.png'] = view+'.png'
    for src, name in files.items():
        shutil.copy2(src, dest/name)
    assert sha256(source/'volvo240.glb') == sha256(dest/'volvo240.glb')
    metadata = {
        'source_checkpoint': 'experiments/volvo240/renders/iter_02',
        'correction_cycles': 2,
        'game_ready': False,
        'art_direction': 'stylized realism; matte clay; simplified materials; restrained reflections',
        'source_glb_sha256': sha256(source/'volvo240.glb'),
        'published_glb_sha256': sha256(dest/'volvo240.glb'),
        'files': {name: sha256(dest/name) for name in files.values()},
    }
    (dest/'manifest.json').write_text(json.dumps(metadata, indent=2)+'\n')
    # No executable is required to view the page; this optional download preserves
    # the editable source, Blender file, PNGs, provenance and rejected GLB evidence.
    with zipfile.ZipFile(dest/'volvo240-review.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted(list(files.values())+['manifest.json']):
            z.write(dest/name, name)
    return dest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', type=Path, help='Empty static output folder (optional)')
    args = parser.parse_args()
    checkpoint = package_checkpoint()
    if not args.dest:
        print('Packaged checkpoint:', checkpoint)
        return
    dest = args.dest.resolve()
    if dest.exists() and any(dest.iterdir()):
        parser.error('Static destination must be empty; preserve prior deployments.')
    dest.mkdir(parents=True, exist_ok=True)
    for path in ('preview.html', 'preview.js', 'preview.css', 'preview-controls.mjs'):
        target = dest/'media/vehicles'/path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(MEDIA/path, target)
    for path in ('traffic', 'vendor', 'experiments/volvo240'):
        shutil.copytree(MEDIA/path, dest/'media/vehicles'/path)
    target = dest/'src/visual/film-pipeline.js'
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT/'src/visual/film-pipeline.js', target)
    assert sha256(target) == sha256(ROOT/'src/visual/film-pipeline.js')
    html = (MEDIA/'preview.html').read_text()
    (dest/'index.html').write_text(html.replace('<head>', '<head>\n<base href="./media/vehicles/">', 1))
    (dest/'.nojekyll').write_text('')
    shutil.copy2(ROOT/'LICENSE', dest/'LICENSE.txt')
    (dest/'README.txt').write_text(
        'Vrigstad Joyride vehicle review. Static HTML/JS/GLB/PNG, no server API or build step.\n'
        'This directory can be served at any GitHub Pages project prefix unchanged.\n'
        'All runtime files are same-origin. No Blender or local setup is required for viewers.\n'
        'The experimental GLB is an unapproved, rejected checkpoint; see the in-page findings.\n')
    print('Static review ready:', dest)


if __name__ == '__main__':
    main()
