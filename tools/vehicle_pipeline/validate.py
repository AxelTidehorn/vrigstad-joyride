"""Validate game-ready GLB vehicles. Reject broken geometry, do not auto-repair.

Requires trimesh and numpy. The main painted body must be one closed solid.
Glass, trim, wheels and lamps are allowed as named independent mesh objects.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import trimesh

REQUIRED_WHEELS = {"wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"}
ALLOWED_PREFIXES = (
    "body", "wheel_", "glass", "lamp", "light", "trim", "interior",
    "mirror", "grille", "plate", "badge", "bumper"
)


def _mesh_nodes(scene):
    """Yield world-space GLB meshes in glTF Y-up coordinates."""
    for name in scene.graph.nodes_geometry:
        transform, geometry_name = scene.graph.get(name)
        mesh = scene.geometry[geometry_name].copy()
        mesh.apply_transform(transform)
        yield name, mesh


def inspect(path: Path, config: dict) -> dict:
    errors, warnings = [], []
    scene = trimesh.load(path, force="scene", process=False)
    nodes = list(_mesh_nodes(scene))
    if not nodes:
        return {"ok": False, "errors": ["No mesh nodes in GLB"], "warnings": [], "meshes": 0}

    names = [n.lower() for n, _ in nodes]
    bodies = [(n, m) for n, m in nodes if n.lower() == "body"]
    if len(bodies) != 1:
        errors.append(f"Expected exactly one mesh node named 'body', found {len(bodies)}")
    wheels = {n.lower(): m for n, m in nodes if n.lower() in REQUIRED_WHEELS}
    missing = REQUIRED_WHEELS - wheels.keys()
    if missing:
        errors.append("Missing wheel mesh nodes: " + ", ".join(sorted(missing)))
    if len(wheels) != sum(n in REQUIRED_WHEELS for n in names):
        errors.append("Duplicate wheel names")

    for name, mesh in nodes:
        if not name.lower().startswith(ALLOWED_PREFIXES):
            errors.append(f"Unexpected mesh '{name}'; assign a recognized part name")
        if not np.isfinite(mesh.vertices).all():
            errors.append(f"{name}: non-finite coordinates")
        if len(mesh.faces) == 0 or len(mesh.vertices) < 3:
            errors.append(f"{name}: empty mesh")
            continue
        if (mesh.area_faces < 1e-10).any():
            errors.append(f"{name}: degenerate triangles")
        if name.lower() == "body":
            if not mesh.is_watertight:
                errors.append("body: has open/non-manifold edges")
            if not mesh.is_winding_consistent:
                errors.append("body: inconsistent face winding")
            if len(mesh.split(only_watertight=False)) != 1:
                errors.append("body: disconnected shells/panels")
            if mesh.volume <= 0:
                errors.append("body: normals inward or non-positive signed volume")

    bounds = scene.bounds
    if bounds is None:
        errors.append("No scene bounds")
        extents = [0., 0., 0.]
    else:
        extents = (bounds[1] - bounds[0]).tolist()
    # Vehicle body width excludes external mirrors.
    body_width = float(bodies[0][1].extents[0]) if bodies else extents[0]
    actual = dict(width=body_width, height=extents[1], length=extents[2])
    expected = config.get("dimensions_m", {})
    tolerances = config.get("tolerance_m", {"length": 0.10, "width": 0.10, "height": 0.10})
    for axis in ("length", "width", "height"):
        if axis not in expected:
            errors.append(f"Metadata missing dimensions_m.{axis}")
        else:
            delta = abs(actual[axis] - expected[axis])
            if delta > tolerances.get(axis, 0.10):
                errors.append(
                    f"{axis}: {actual[axis]:.3f}m vs expected {expected[axis]:.3f}m "
                    f"(delta {delta:.3f}m)"
                )

    wheelbase = None
    if not missing:
        centers = {name: mesh.bounds.mean(axis=0) for name, mesh in wheels.items()}
        # GLB: -Z forward, +X right, +Y up.
        for name, c in centers.items():
            if name in ("wheel_fl", "wheel_fr") and c[2] >= 0:
                errors.append(f"{name} is not in front (-Z)")
            if name in ("wheel_rl", "wheel_rr") and c[2] <= 0:
                errors.append(f"{name} is not in rear (+Z)")
            if name in ("wheel_fl", "wheel_rl") and c[0] >= 0:
                errors.append(f"{name} is not on left (-X)")
            if name in ("wheel_fr", "wheel_rr") and c[0] <= 0:
                errors.append(f"{name} is not on right (+X)")
        front_z = (centers["wheel_fl"][2] + centers["wheel_fr"][2]) / 2
        rear_z = (centers["wheel_rl"][2] + centers["wheel_rr"][2]) / 2
        wheelbase = float(rear_z - front_z)
        desired = config.get("wheelbase_m")
        if desired is None:
            errors.append("Metadata missing wheelbase_m")
        elif abs(wheelbase - desired) > config.get("wheelbase_tolerance_m", 0.055):
            errors.append(f"wheelbase: {wheelbase:.3f}m vs expected {desired:.3f}m")
        for name, mesh in wheels.items():
            dims = mesh.extents
            if min(dims[1], dims[2]) < 0.20 or max(dims) > 1.30:
                errors.append(f"{name}: implausible wheel geometry {dims.round(3).tolist()}")

    if bodies:
        bodybounds = bodies[0][1].bounds
        clearance = float(config.get("detail_clearance_m", 0.40))
        for name, mesh in nodes:
            if name.lower() == "body":
                continue
            center = mesh.bounds.mean(axis=0)
            if np.any(center < bodybounds[0] - clearance) or np.any(center > bodybounds[1] + clearance):
                errors.append(f"{name}: appears detached from body bounding volume")

    report = {
        "ok": not errors, "model": config.get("id"), "errors": errors,
        "warnings": warnings, "meshes": len(nodes),
        "triangles": int(sum(len(mesh.faces) for _, mesh in nodes)),
        "dimensions_m": {k: round(v, 4) for k, v in actual.items()},
        "wheelbase_m": None if wheelbase is None else round(wheelbase, 4)
    }
    limit = config.get("triangle_budget")
    if limit is not None and report["triangles"] > limit:
        report["errors"].append(f"Triangle budget exceeded: {report['triangles']} > {limit}")
        report["ok"] = False
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("glb", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    config = json.loads(args.manifest.read_text(encoding="utf-8"))
    report = inspect(args.glb, config)
    data = json.dumps(report, indent=2, ensure_ascii=False)
    print(data)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(data + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
