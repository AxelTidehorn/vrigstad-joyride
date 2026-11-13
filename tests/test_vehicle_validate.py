import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "vehicle_pipeline"))
from validate import inspect


CONFIG = {
    "id": "test-car",
    "dimensions_m": {"length": 4.83, "width": 1.82, "height": 1.48},
    "wheelbase_m": 2.70,
    "triangle_budget": 3000,
}


def make_car(body=None):
    scene = trimesh.Scene()
    if body is None:
        body = trimesh.creation.box(extents=[1.78, 1.48, 4.83])
        body.apply_translation([0, 0.74, 0])
    scene.add_geometry(body, node_name="body", geom_name="body")
    for name, x, z in [
        ("wheel_fl", -.81, -1.4), ("wheel_fr", .81, -1.4),
        ("wheel_rl", -.81, 1.3), ("wheel_rr", .81, 1.3)
    ]:
        wheel = trimesh.creation.cylinder(radius=.32, height=.2, sections=24)
        wheel.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, [0, 1, 0]))
        wheel.apply_translation([x, .35, z])
        scene.add_geometry(wheel, node_name=name, geom_name=name)
    return scene


def run(scene, config=CONFIG):
    with tempfile.TemporaryDirectory() as directory:
        file = Path(directory) / "car.glb"
        file.write_bytes(scene.export(file_type="glb"))
        return inspect(file, config)


class VehicleValidatorTests(unittest.TestCase):
    def test_closed_car_passes(self):
        report = run(make_car())
        self.assertTrue(report["ok"], report["errors"])
        self.assertAlmostEqual(report["wheelbase_m"], 2.70, places=3)

    def test_hole_in_body_rejected(self):
        body = trimesh.creation.box(extents=[1.78, 1.48, 4.83])
        body.update_faces(np.arange(len(body.faces) - 1))
        body.remove_unreferenced_vertices()
        body.apply_translation([0, .74, 0])
        report = run(make_car(body))
        self.assertFalse(report["ok"])
        self.assertTrue(any("non-manifold" in e for e in report["errors"]))

    def test_disconnected_body_rejected(self):
        main = trimesh.creation.box(extents=[1.78, 1.48, 4.83])
        main.apply_translation([0, .74, 0])
        small = trimesh.creation.box(extents=[.04, .04, .04])
        small.apply_translation([0, 1.8, 0])
        report = run(make_car(trimesh.util.concatenate([main, small])))
        self.assertFalse(report["ok"])
        self.assertTrue(any("disconnected" in e for e in report["errors"]))

    def test_dimensions_wrong_rejected(self):
        config = {**CONFIG, "dimensions_m": {**CONFIG["dimensions_m"], "length": 5.8}}
        report = run(make_car(), config)
        self.assertFalse(report["ok"])
        self.assertTrue(any("length:" in e for e in report["errors"]))

    def test_missing_wheel_rejected(self):
        scene = make_car()
        scene.delete_geometry("wheel_fl")
        report = run(scene)
        self.assertFalse(report["ok"])
        self.assertTrue(any("Missing wheel" in e for e in report["errors"]))


if __name__ == "__main__":
    unittest.main()
