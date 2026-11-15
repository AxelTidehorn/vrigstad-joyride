#!/usr/bin/env python3
"""Fail closed when a changed vehicle model lacks inspectable reference evidence.

This checks evidence presence/structure, NOT photographic accuracy or human approval.
"""
import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL_PATHS = {"model.py", "parameters.json", "spec.json"}
REQUIRED_VIEWS = ("side", "front")
PNG_HEADER = bytes.fromhex("89504e470d0a1a0a")

def changed_files(base, head):
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{base}...{head}"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    return result.stdout.splitlines()

def targets(files):
    result = set()
    for name in files:
        parts = Path(name).parts
        if len(parts) >= 3 and parts[0] == "experiments":
            if parts[2] in MODEL_PATHS or (parts[2] == "build" and name.endswith(".glb")):
                result.add(parts[1])
        if name == "media/vehicles/micra-k11.glb":
            result.add("micra1995")
        if name == "media/vehicles/duett-p210-epa.glb":
            result.add("duettp210")
    return sorted(result)

def verify_asset(experiment):
    base = ROOT / "experiments" / experiment
    manifest = base / "reference-evidence.json"
    errors = []
    if not manifest.is_file():
        return [f"{experiment}: missing {manifest.relative_to(ROOT)}"]
    try:
        record = json.loads(manifest.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        return [f"{experiment}: invalid manifest: {exc}"]

    if record.get("schema_version") != 1:
        errors.append("schema_version must equal 1")
    if record.get("asset") != experiment:
        errors.append("asset must equal experiment directory")
    if not isinstance(record.get("variant"), str) or not record["variant"].strip():
        errors.append("variant is required")
    if record.get("human_visual_approval") not in ("pending", "approved", "rejected"):
        errors.append("human_visual_approval must be pending, approved or rejected")
    references = record.get("references", [])
    if not isinstance(references, list) or not references:
        errors.append("at least one traceable reference is required")
    else:
        for i, ref in enumerate(references):
            if not isinstance(ref, dict) or not str(ref.get("url", "")).startswith("https://"):
                errors.append(f"references[{i}] must have an HTTPS source URL")
            if not isinstance(ref, dict) or not ref.get("body_variant"):
                errors.append(f"references[{i}] must specify body_variant")

    comparisons = record.get("comparisons", {})
    if not isinstance(comparisons, dict):
        comparisons = {}
    for view in REQUIRED_VIEWS:
        entry = comparisons.get(view)
        if not isinstance(entry, dict):
            errors.append(f"{view}: missing comparison")
            continue
        for field in ("overlay_png", "measurements_json"):
            relative = entry.get(field)
            if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
                errors.append(f"{view}: invalid {field} relative path")
                continue
            path = (base / relative).resolve()
            if not path.is_relative_to(base.resolve()) or not path.is_file():
                errors.append(f"{view}: {field} not found: {relative}")
                continue
            if field == "overlay_png" and path.read_bytes()[:8] != PNG_HEADER:
                errors.append(f"{view}: overlay is not a PNG: {relative}")
            if field == "measurements_json":
                try:
                    metrics = json.loads(path.read_text(encoding="utf-8"))
                    if metrics.get("view") != view:
                        errors.append(f"{view}: measurements view mismatch")
                    landmarks = metrics.get("landmarks", [])
                    if not isinstance(landmarks, list) or len(landmarks) < 3:
                        errors.append(f"{view}: at least three measured landmarks required")
                    else:
                        for point in landmarks:
                            if not all(k in point for k in ("name", "reference_px", "model_px", "error_px")):
                                errors.append(f"{view}: incomplete landmark record")
                                break
                            if not isinstance(point["error_px"], (int, float)) or not math.isfinite(point["error_px"]):
                                errors.append(f"{view}: invalid landmark deviation")
                                break
                    if not metrics.get("registration_method") or not metrics.get("uncertainties"):
                        errors.append(f"{view}: registration and uncertainty must be disclosed")
                except (ValueError, OSError, AttributeError, TypeError) as exc:
                    errors.append(f"{view}: invalid measurements JSON: {exc}")
    return [f"{experiment}: {msg}" for msg in errors]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", required=True)
    args = parser.parse_args()
    changed = changed_files(args.base_ref, args.head_ref)
    models = targets(changed)
    if not models:
        print("No changed vehicle models. Evidence gate not applicable.")
        return 0
    failures = [err for model in models for err in verify_asset(model)]
    if failures:
        print("REFERENCE EVIDENCE GATE FAILED:", file=sys.stderr)
        for problem in failures:
            print(" - " + problem, file=sys.stderr)
        print("This gate verifies auditable evidence, not silhouette accuracy or approval.", file=sys.stderr)
        return 1
    print("Reference evidence present for: " + ", ".join(models))
    print("Human visual approval remains a separate requirement.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
