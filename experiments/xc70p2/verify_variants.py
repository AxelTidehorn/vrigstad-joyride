"""Verify every shared component in the actual exports, not only the main body."""
from pathlib import Path
import sys,json
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p.parents[1]/'tools/vehicle_pipeline'))
from compare_shared_geometry import compare
report=compare(p/'build/xc70-civilian.glb',p/'build/xc70-police.glb')
(p/'build/shared-export-geometry.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report|{'identical_geometry':'see JSON'}));assert report['ok'],report
