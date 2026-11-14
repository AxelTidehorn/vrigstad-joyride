"""Shared P2 pressed planes and details. Variant paint/equipment live in variants.py."""
from pathlib import Path
import sys,json,math
import bpy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/vehicle_pipeline'))
import authoring as T
import surface_refinement as S

def apply():
    body=bpy.data.objects['body']
    if body.get('round2_surface_revision')=='xc70p2-v1':return
    for name in ['BODY','GLASS','PLASTIC_RUBBER','LIGHTS','DETAILS','WHEELS','POLICE','POLICE_DECALS']:T.collections[name]=bpy.data.collections[name]
    P=json.loads(Path(__file__).with_name('parameters.json').read_text());axles=[P['front_axle_y'],P['front_axle_y']-P['wheelbase']]
    # P2 uses a restrained crowned fender rail, rather than the 240's flat ledge.
    profile=json.loads(body['longitudinal_profile'])
    for v in body.data.vertices:
        x,y,z=v.co
        if .90<y<2.20 and abs(x)>.72:
            top=T.interp(y,profile)
            factor=max(0,min(1,(z-(top-.15))/.07))*max(0,min(1,(y-.90)/.20,(2.20-y)/.15))
            v.co.z+=.010*factor
    body.data.update()
    clear_arch=lambda p:all(math.hypot(p.y-y,p.z-.345)>.48 for y in axles)
    side=lambda p:abs(p.x)>.76 and .60<p.z<1.01 and -2.08<p.y<2.12 and clear_arch(p)
    for y in [-1.20,-.27,.78]:S.press_line(body,1,y,.006,.0025,side)
    S.press_line(body,2,.965,.010,.0035,side)
    hood=lambda p:.86<p.y<2.24 and abs(p.x)<.81 and p.z>.78
    for sign in [-1,1]:S.press_line(body,0,sign*.57,.008,.003,hood,push_axis=2)
    # Tailgate divisions stop before the actual rear window/reveal geometry.
    S.press_line(body,2,.91,.008,-.003,lambda p:p.y<-2.20 and abs(p.x)<.65 and .86<p.z<.96,push_axis=1)
    alloy=bpy.data.materials['satin alloy'];rubber=bpy.data.materials['charcoal plastic rubber'];white=bpy.data.materials['headlamp ivory']
    S.frame('grille_frame',.61,.205,.018,(0,2.326,.735),alloy,T.collections['DETAILS'],.012)
    # Avoid 7 separate draw calls for the existing same-material slats.
    S.merge_static([o for o in bpy.context.scene.objects if o.name.startswith('grille_slats')],'grille_slats')
    for sign in [-1,1]:S.frame('lamp_head_frame',.38,.112,.014,(sign*.525,2.304,.725),rubber,T.collections['LIGHTS'],.007)
    for name,depth in [('bumper_front',.003),('bumper_rear',-.003)]:
        S.press_line(bpy.data.objects[name],2,.555,.008,depth,lambda p:abs(p.y)>2.28 and abs(p.x)<.69,push_axis=1)
    S.clean_cut_slivers(body,min_area=1e-9,merge_distance=.00008)
    for n in ['bumper_front','bumper_rear']:S.clean_cut_slivers(bpy.data.objects[n])
    # Livery is point colour data. Remove the unused legacy loop UV atlas,
    # whose independently interpolated cut corners otherwise split GLB indices.
    for layer in list(body.data.uv_layers):body.data.uv_layers.remove(layer)
    S.panel_normals(body,side_limit=.82,belt=1.035)
    bpy.context.view_layer.update();S.attach_wheel_fixtures();S.batch_wheel_spokes();S.attach_body_fixtures()
    body['round2_surface_revision']='xc70p2-v1'
    body['round2_architecture']='model.py defines BODY, GLASS, lamp mounting and all shared parts once; round2.py applies shared features; variants.py changes paint and equipment visibility only'
    bpy.data.objects['glass_envelope']['seating']='Pane-wise PCA outward translation 1.5 mm; solidify 2.5 mm outward only; no coplanar backing face'
    body['round2_changes']=json.dumps({'rear_glass_lower_station_y_m':-2.286,'rear_clear_aperture_half_width_limit_m':.635,'front_rear_reveal_depth_mm':6,'door_reveal_mm':2.5,'front_fender_rail_lift_mm':10,'shared_tail_lamp_back_inner_wall_narrows_away_from_glass':True})
