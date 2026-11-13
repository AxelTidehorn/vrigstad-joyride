"""Blender 4.x+ headless import/export stage for game-ready vehicle assets.

Run with: blender -b --python tools/vehicle_pipeline/blender_import.py -- \
    --source path/to/saab95.blend --output assets/vehicles/saab95.glb \
    --previews build/vehicle-previews/saab95

Input uses Blender coordinates: X lateral (+right), Y forward, Z up, metres.
Blender's glTF exporter maps +Y forward to glTF -Z forward.
This script refuses open or disconnected bodies instead of overlaying panels.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--previews", type=Path, required=True)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])


def load_source(path: Path):
    if not path.is_file():
        raise FileNotFoundError(path)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    suffix = path.suffix.lower()
    if suffix == ".blend":
        bpy.ops.wm.open_mainfile(filepath=str(path.resolve()))
    elif suffix in (".glb", ".gltf"):
        bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    elif suffix == ".fbx":
        bpy.ops.import_scene.fbx(filepath=str(path.resolve()))
    elif suffix == ".obj":
        bpy.ops.wm.obj_import(filepath=str(path.resolve()))
    else:
        raise ValueError("Supported inputs: .blend, .glb, .gltf, .fbx, .obj")


def body_quality_gate(mesh_objects):
    names = {obj.name.lower(): obj for obj in mesh_objects}
    if len([name for name in names if name == "body"]) != 1:
        raise ValueError("One mesh object must be named exactly 'body'")
    body = names["body"]
    bm = bmesh.new()
    bm.from_mesh(body.data)
    try:
        bm.normal_update()
        open_edges = sum(1 for edge in bm.edges if not edge.is_manifold)
        if open_edges:
            raise ValueError(
                f"body: {open_edges} boundary/non-manifold edges. "
                "Repair the shell; do not overlay panels."
            )
        bad_faces = sum(1 for face in bm.faces if face.calc_area() <= 1e-10)
        if bad_faces:
            raise ValueError(f"body: {bad_faces} zero-area faces")
        remaining = set(bm.faces)
        components = 0
        while remaining:
            components += 1
            stack = [remaining.pop()]
            while stack:
                face = stack.pop()
                for edge in face.edges:
                    for connected in edge.link_faces:
                        if connected in remaining:
                            remaining.remove(connected)
                            stack.append(connected)
        if components != 1:
            raise ValueError(f"body: {components} separate disconnected shells. Merge into one solid.")
        signed_volume = bm.calc_volume(signed=True)
        if signed_volume * (1 if body.matrix_world.determinant() > 0 else -1) <= 0:
            raise ValueError("body: face winding is inverted or body has no positive volume")
    finally:
        bm.free()
    required = {"wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"}
    absent = required - names.keys()
    if absent:
        raise ValueError("Missing required wheel objects: " + ", ".join(sorted(absent)))


def vehicle_bounds(objects):
    points = [obj.matrix_world @ Vector(vertex) for obj in objects for vertex in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    return low, high


def render_reviews(mesh_objects, destination: Path):
    # Review in Blender's original Z-up coordinates, before glTF conversion.
    destination.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    low, high = vehicle_bounds(mesh_objects)
    center = (low + high) / 2
    diagonal = (high - low).length
    distance = max(6, diagonal * 1.6)
    camera_data = bpy.data.cameras.new("QA camera")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(high.x - low.x, high.y - low.y, high.z - low.z) * 1.5
    cam = bpy.data.objects.new("QA camera", camera_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.render.film_transparent = True
    scene.render.resolution_x, scene.render.resolution_y = 1000, 650
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    views = {
        "front": Vector((0, 1, .15)),
        "side": Vector((1, 0, .12)),
        "rear": Vector((0, -1, .15)),
        "three_quarter": Vector((1, 1, .55)).normalized(),
    }
    for name, direction in views.items():
        cam.location = center + direction * distance
        cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str((destination / f"{name}.png").resolve())
        bpy.ops.render.render(write_still=True)


def main():
    args = arguments()
    load_source(args.source)
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render]
    if not objects:
        raise ValueError("No visible mesh objects")
    body_quality_gate(objects)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(
        filepath=str(args.output.resolve()),
        export_format="GLB",
        export_yup=True,
        use_selection=True,
        export_cameras=False,
        export_lights=False,
    )
    render_reviews(objects, args.previews)
    print("EXPORTED", args.output, "PREVIEWS", args.previews)


if __name__ == "__main__":
    main()
