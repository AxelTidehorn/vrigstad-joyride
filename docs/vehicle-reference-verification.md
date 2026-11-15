# Vehicle appearance verification gate

This is a **fail-closed evidence check**, not an AI self-assessment of visual similarity.

When a PR changes a vehicle generator (model.py, parameters.json or spec.json)
or its installed GLB, it must include
`experiments/<vehicle>/reference-evidence.json` and the evidence it names.

For **each** of the exact side and front views, supply:
- A PNG overlay of the actual Blender model and traced/registered real-car reference.
- JSON with at least three named reference/model landmarks, their offsets,
  registration method, and uncertainty. Prefer more landmarks: wheel centres,
  bonnet profile, windshield base/top, roof, wings, front and rear extremities.
- Source URLs with body variant and year scope. Use a single real EPA conversion
  as primary for the converted rear; distinguish its estimated modifications
  from verified stock P210 facts.

The overlay may contain traced points and model contours rather than redistributed
copyrighted photographs. An estimated perspective-photo comparison must be labelled
as such; it must **not** be called an orthographic or millimetre-accurate check.

Example manifest:
```json
{
  "schema_version": 1,
  "asset": "duettp210",
  "variant": "P210 converted EPA, short cab, integral open bed",
  "human_visual_approval": "pending",
  "references": [{"url": "https://commons.wikimedia.org/wiki/File:Duett-EPA.jpg", "body_variant": "actual Hova Duett EPA conversion"}],
  "comparisons": {
    "side": {"overlay_png": "reference-review/side.png", "measurements_json": "reference-review/side.json"},
    "front": {"overlay_png": "reference-review/front.png", "measurements_json": "reference-review/front.json"}
  }
}
```

Each measurements file has:
```json
{
  "view": "side",
  "registration_method": "wheel centres, uniform scale; perspective estimate",
  "uncertainties": ["source perspective; +/-6 px manual trace uncertainty"],
  "landmarks": [
    {"name": "front wheel", "reference_px": [100,200], "model_px": [100,200], "error_px": 0},
    {"name": "rear wheel", "reference_px": [300,200], "model_px": [300,200], "error_px": 0},
    {"name": "roof top", "reference_px": [180,60], "model_px": [181,64], "error_px": 4.12}
  ]
}
```
The example is *schema guidance only*, not actual measurement evidence.
Do not copy fabricated measurements into a real vehicle report.

Run CI gate with:
```bash
python tools/vehicle_pipeline/reference_gate.py --base-ref BASE_SHA --head-ref HEAD_SHA
```

**Limitations:** CI validates that evidence files exist and have a minimally
auditable structure. It does not verify image truthfulness, photographic perspective
calibration, or design quality. The PR reviewer must inspect the image overlays and
approve or reject shape. A green CI check does **not** grant human visual approval.
The branch protection/ruleset must require the status check to make it blocking
before merge; otherwise GitHub may allow merging despite failure.

**Current state:** Micra already has a useful but partial measured upper-side
comparison in `experiments/micra1995/refinement`. It does not satisfy the
two-view gate yet. Duett has documented references and 7-view renderings but
no demonstrated measured front+side comparison against real references.
Do not fabricate or relabel existing model-only measurements as source comparison.
These assets remain pending reference review until genuine evidence is produced.
