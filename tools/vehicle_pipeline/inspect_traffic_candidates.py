"""Independent non-approval report for the generic Kenney review assets.

An import gate, not a certification of perfect body geometry or style.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
MODELS = ("sedan", "van", "tractor", "police")


def main():
    failed = False
    for name in MODELS:
        path = ROOT / "media" / "vehicles" / "traffic" / f"{name}.glb"
        scene = trimesh.load(path, force="scene", process=False)
        nodes = {}
        for node in scene.graph.nodes_geometry:
            matrix, geometry = scene.graph[node]
            mesh = scene.geometry[geometry].copy()
            mesh.apply_transform(matrix)
            nodes[node] = mesh
        if not nodes:
            print("ERROR", name, "no mesh nodes")
            failed = True
            continue
        wheels = [key for key in nodes if key.lower().startswith("wheel-")]
        body = [key for key in nodes if key.lower() == "body"]
        if len(wheels) != 4 or len(body) != 1:
            print("ERROR", name, "expected 4 named wheels and one body", list(nodes))
            failed = True
        if any((not np.isfinite(mesh.vertices).all()) or len(mesh.faces) == 0 for mesh in nodes.values()):
            print("ERROR", name, "invalid vertex data or no faces")
            failed = True
        bounds = scene.bounds
        if bounds is None or np.any(bounds[1] <= bounds[0]):
            print("ERROR", name, "invalid bounds")
            failed = True
        tris = sum(len(mesh.faces) for mesh in nodes.values())
        if tris > 10000:
            print("ERROR", name, "excessive triangle count", tris)
            failed = True
        if body:
            main_body = nodes[body[0]]
            # For review only: note any topology defects, never silently 'repair'.
            print(name, "triangles", tris, "bounds", np.round(bounds[1]-bounds[0], 3),
                  "body_watertight", main_body.is_watertight,
                  "body_components", len(main_body.split(only_watertight=False)),
                  "meshes", len(nodes))
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
