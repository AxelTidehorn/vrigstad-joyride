"""Simplifies the redrawn XC70 for the game: every mesh's nearly coplanar faces merged (planar decimation, never across
a material border or a sharp edge), so the dense subdivided shell and the cast plates keep their shape and outlines
with far fewer triangles. Usage: python simplify.py OUT.blend IN.blend [ANGLE_DEG]"""
import sys, math
from pathlib import Path
import bpy

def simplify(angle_deg=1.5):
    """Parts: planar (nearly coplanar faces merged, never across a material border, a sharp edge or a bend). The body and
    the glass and plates, curved or cast in dense rings: edge collapse (COLLAPSE) only for the flat plates; the body comes light from BODY_SUBD."""
    before = after = 0
    for o in bpy.data.objects:
        if o.type != 'MESH' or not o.data.polygons or o.name == 'body' or o.name.startswith('glass_'):
            continue   # the body comes light from BODY_SUBD and carries the livery's vertex colours; glass dents when thinned
        before += sum(len(p.vertices) - 2 for p in o.data.polygons)
        m = o.modifiers.new('simplify', 'DECIMATE')
        ratio = COLLAPSE.get(o.name.split('_')[0])
        if ratio:
            m.decimate_type, m.ratio, m.use_symmetry, m.symmetry_axis = 'COLLAPSE', ratio, o.name == 'body', 'X'
        else:
            m.decimate_type, m.angle_limit = 'DISSOLVE', math.radians(angle_deg)
            m.delimit = {'MATERIAL', 'SHARP', 'NORMAL'}
        o.modifiers.new('tris', 'TRIANGULATE')
        bpy.context.view_layer.objects.active = o
        for name in ('simplify', 'tris'):
            bpy.ops.object.modifier_apply(modifier=name)
        after += len(o.data.polygons)
    return before, after


COLLAPSE = {'plate': 0.3}   # (collapsing the body smeared the police livery's vertex colours; the glass dented)


if __name__ == '__main__':
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    bpy.ops.wm.open_mainfile(filepath=str(Path(args[1]).resolve()))
    for o in bpy.data.objects:
        o.hide_set(False); o.hide_viewport = False
    print('simplify', simplify(float(args[2]) if len(args) > 2 else 1.2))
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(args[0]).resolve()))
