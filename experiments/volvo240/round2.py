"""Defined 240 panel planes and fixtures, retaining approved wheel-well geometry."""
from pathlib import Path
import sys,math,json
import bpy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/vehicle_pipeline'))
import authoring as T
import surface_refinement as S

def apply():
    body=bpy.data.objects['body']
    if body.get('round2_surface_revision')=='volvo240-v1':return
    P=json.loads(Path(__file__).with_name('parameters.json').read_text())
    for target,source in [('BODY','BODY'),('GLASS','GLASS'),('PLASTIC_RUBBER','PLASTIC & RUBBER'),('LIGHTS','DETAILS'),('DETAILS','DETAILS'),('WHEELS','WHEELS')]:T.collections[target]=bpy.data.collections[source]
    axles=[P['front_axle_y'],P['front_axle_y']-P['wheelbase']]
    # Raise only the outer upper rail into a flatter steel shoulder ledge.
    # The original cabin/glass and approved wells remain outside this edit.
    rear=-P['length']/2;front=P['length']/2
    roof_profile=[(rear,.87),(rear+.13,.92),(P['backlight_base_y'],.965),(P['roof_rear_y'],P['height']-.025),(P['roof_front_y'],P['height']-.025),(P['cowl_y'],.97),(front-.13,.87),(front,.82)]
    shoulder_moved=0
    for v in body.data.vertices:
        x,y,z=v.co
        if not -2.22<y<2.22:continue
        top=T.interp(y,roof_profile);base=min(P['window_base_z'],top-.045)
        width=P['width']/2*T.interp(y,[(rear,.94),(rear+.13,1),(-1.8,1),(1.8,1),(front-.13,.985),(front,.92)])
        if abs(abs(x)-width*.985)<.004 and abs(z-(base-.03))<.012:
            v.co.z=min(.932,top-.04);shoulder_moved+=1
    body.data.update()
    clear_arch=lambda p:all(math.hypot(p.y-y,p.z-P['tire_radius'])>P['arch_radius']+.041 for y in axles)
    side=lambda p:abs(p.x)>.72 and .38<p.z<.95 and -2.22<p.y<2.22 and clear_arch(p)
    # The straight shoulder and four-door divisions are pressed into the shell.
    S.press_line(body,2,.865,.012,.003,side)
    for y in [-1.05,-.20,.77]:S.press_line(body,1,y,.006,.0025,side)
    for y in [-2.20,2.20]:S.press_line(body,1,y,.008,.003,side)
    hood=lambda p:.95<p.y<2.20 and p.z>.84 and abs(p.x)<.77
    trunk=lambda p:-2.21<p.y<-1.46 and p.z>.84 and abs(p.x)<.77
    for sign in [-1,1]:
        S.press_line(body,0,sign*.61,.007,.0025,hood,push_axis=2)
        S.press_line(body,0,sign*.60,.006,.003,trunk,push_axis=2)
    S.press_line(body,1,-2.12,.006,.003,trunk,push_axis=2)
    rubber=bpy.data.materials['matte charcoal rubber'];alloy=bpy.data.materials['restrained wheel alloy'];white=bpy.data.materials['headlamp ivory']
    S.frame('grille_frame',.66,.23,.018,(0,2.338,.695),alloy,T.collections['DETAILS'],.011)
    bars=[]
    for x in [-.27,-.2025,-.135,-.0675,0,.0675,.135,.2025,.27]:bars.append(T.slab('grille_slats',(.014,.016,.18),(x,2.342,.695),alloy))
    diag=T.slab('grille_diagonal',(.61,.018,.018),(0,2.354,.695),alloy);diag.rotation_euler.y=math.radians(19);bars.append(diag)
    S.merge_static(bars,'grille_slats_and_diagonal')
    for o in list(bpy.context.scene.objects):
        if o.name.startswith('lamp_front_'):
            o.data.materials.clear();o.data.materials.append(rubber)
            sign=-1 if o.location.x<0 else 1
            lenses=[]
            for offset in [-.093,.093]:lenses.append(T.slab('lamp_front_lens',(.166,.018,.164),(sign*.54+offset,2.342,.695),white,'LIGHTS'))
            S.merge_static(lenses,'lamp_front_lenses_'+str(sign))
    for sign in [-1,1]:T.slab('lamp_rear_reverse',(.105,.014,.067),(sign*.49,-2.338,.679),white,'LIGHTS')
    for name,depth in [('bumper_front',.003),('bumper_rear',-.003)]:
        bumper=bpy.data.objects[name]
        # Sweeps were authored in world coordinates with identity object transform.
        S.press_line(bumper,2,.455,.008,depth,lambda p:abs(p.y)>2.30 and abs(p.x)<.64,push_axis=1)
    S.clean_cut_slivers(body)
    for n in ['bumper_front','bumper_rear']:S.clean_cut_slivers(bpy.data.objects[n])
    S.panel_normals(body,side_limit=.80,belt=.95)
    bpy.context.view_layer.update();S.attach_wheel_fixtures();S.batch_wheel_spokes();S.attach_body_fixtures()
    body['round2_surface_revision']='volvo240-v1'
    body['round2_changes']=json.dumps({'approved_arch_profile_unchanged':True,'outer_shoulder_vertices_raised':shoulder_moved,'maximum_shoulder_lift_mm':35,'shoulder_reveal_depth_mm':4,'door_reveal_depth_mm':2.5,'hood_lid_reveals_mm':3.5,'new_grille_and_split_lenses':True})

if __name__=='__main__':
    apply();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(Path(sys.argv[1]).resolve()))
