"""Tests for required reference evidence; no Blender or network dependency."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools/vehicle_pipeline/reference_gate.py"
spec = importlib.util.spec_from_file_location("reference_gate", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class ReferenceEvidenceGateTests(unittest.TestCase):
    def test_changed_model_detection(self):
        self.assertEqual(gate.targets(["experiments/duettp210/model.py"]), ["duettp210"])
        self.assertEqual(gate.targets(["media/vehicles/micra-k11.glb"]), ["micra1995"])
        self.assertEqual(gate.targets(["docs/vehicle-reference-verification.md"]), [])

    def test_missing_manifest_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = gate.ROOT
            gate.ROOT = Path(tmp)
            try:
                result = gate.verify_asset("duettp210")
                self.assertTrue(any("missing" in x for x in result))
            finally:
                gate.ROOT = old

    def test_realistic_minimum_evidence_and_missing_front(self):
        with tempfile.TemporaryDirectory() as tmp:
            old = gate.ROOT
            gate.ROOT = Path(tmp)
            try:
                base = Path(tmp) / "experiments" / "micra1995"
                (base / "review").mkdir(parents=True)
                source = {
                    "schema_version":1, "asset":"micra1995",
                    "variant":"K11 3 door pre-facelift", "human_visual_approval":"pending",
                    "references":[{"url":"https://example.org/original","body_variant":"K11 3 door"}],
                    "comparisons":{}
                }
                for view in ("side", "front"):
                    (base / "review" / f"{view}.png").write_bytes(gate.PNG_HEADER + b"placeholder")
                    metrics = {
                        "view":view, "registration_method":"wheel and width anchors",
                        "uncertainties":["uncalibrated perspective"],
                        "landmarks":[{"name":name, "reference_px":[0,0], "model_px":[1,1], "error_px":1.4} for name in ("a","b","c")],
                    }
                    (base / "review" / f"{view}.json").write_text(json.dumps(metrics))
                    source["comparisons"][view] = {
                        "overlay_png":f"review/{view}.png",
                        "measurements_json":f"review/{view}.json",
                    }
                (base / "reference-evidence.json").write_text(json.dumps(source))
                self.assertEqual(gate.verify_asset("micra1995"), [])
                del source["comparisons"]["front"]
                (base / "reference-evidence.json").write_text(json.dumps(source))
                self.assertTrue(any("front" in x for x in gate.verify_asset("micra1995")))
            finally:
                gate.ROOT = old

if __name__ == "__main__":
    unittest.main()
