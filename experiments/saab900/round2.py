"""Second local refinement of the approved Classic three-door architecture."""
from pathlib import Path
import sys,json,math
import bpy
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/vehicle_pipeline'))
import authoring as T
import surface_refinement as S

def apply():
    body=bpy.data.objects['body']
    if body.get('round2_surface_revision')=='saab900-v1':return
    for name in ['BODY','GLASS','PLASTIC_RUBBER','LIGHTS','DETAILS','WHEELS']:T.collections[name]=bpy.data.collections[name]
    profile=json.loads(body['longitudinal_profile'])
    oldtop=lambda y:T.interp(y,profile)
    # The previous cabin/hatch and cowl are kept; only the low forward hood is raised.
    changed=0
    for v in body.data.vertices:
        x,y,z=v.co
        if 1.02<y<=2.241:
            h=oldtop(y);vertical=max(0,min(1,(z-(h-.16))/.10))
            rise=T.interp(y,[(1.02,0),(1.30,.030),(1.75,.035),(2.10,.025),(2.24,.020)])
            shoulder=.008*max(0,1-abs(abs(x)-.60)/.10)*max(0,min(1,(y-1.02)/.12))
            dz=(rise+shoulder)*vertical
            if dz>1e-8:v.co.z+=dz;changed+=1
    body.data.update()
    hood=lambda p:1.019<p.y<2.241 and p.z>oldtop(p.y)-.10 and abs(p.x)<.79
    for sign in [-1,1]:S.press_line(body,0,sign*.60,.008,.002,hood,push_axis=2)
    side=lambda p:abs(p.x)>.73 and .39<p.z<.94 and -1.90<p.y<1.95
    for y in [-.40,.86]:S.press_line(body,1,y,.006,.0025,side)
    S.press_line(body,2,.84,.010,.003,lambda p:abs(p.x)>.75 and -.6<p.y<1.48 and .81<p.z<.88)
    # Remove the obsolete detached 1 mm seam bars; the reveals now live in BODY.
    for o in list(bpy.context.scene.objects):
        if o.name.startswith('trim_door_seam'):bpy.data.objects.remove(o,do_unlink=True)
    # Broader rectangular lamp tops fit below the raised clamshell hood/fender edge.
    for o in bpy.context.scene.objects:
        if o.type=='MESH' and o.name.startswith('lamp_head'):
            for v in o.data.vertices:
                if v.co.z>.62:
                    target=T.interp(abs(v.co.x),[(.295,.724),(.645,.704)])+(.006 if v.co.y<2.23 else 0)
                    from mathutils import Vector
                    hit,point,normal,index=body.ray_cast(Vector((v.co.x,min(v.co.y,2.232),2)),Vector((0,0,-1)))
                    v.co.z=min(target,point.z-.006) if hit else target
    rubber=bpy.data.materials['charcoal plastic rubber'];alloy=bpy.data.materials['satin alloy'];white=bpy.data.materials['headlamp ivory']
    grille=bpy.data.objects['grille']
    for v in grille.data.vertices:v.co.z*=1.10
    S.frame('grille_frame',.535,.175,.018,(0,2.267,.635),alloy,T.collections['DETAILS'],.009)
    for sign in [-1,1]:T.slab('lamp_head_divider',(.008,.010,.115),(sign*.47,2.260,.635),white,'LIGHTS')
    T.band('trim_front_airdam',[(-.66,2.235),(-.59,2.27),(.59,2.27),(.66,2.235)],.330,.072,.060,rubber,'PLASTIC_RUBBER')
    S.merge_static([o for o in bpy.context.scene.objects if o.name.startswith('grille_bar')],'grille_bars')
    S.clean_cut_slivers(body)
    for n in ['bumper_front','bumper_rear']:S.clean_cut_slivers(bpy.data.objects[n])
    S.panel_normals(body,side_limit=.76,belt=.92)
    bpy.context.view_layer.update();S.attach_wheel_fixtures();S.batch_wheel_spokes();S.attach_body_fixtures()
    body['round2_surface_revision']='saab900-v1'
    body['round2_changes']=json.dumps({'hood_vertices_moved':changed,'hood_center_rise_mm':[0,30,35,25,20],'cabin_glass_and_roof_preserved':True,'door_reveals_mm':2.5,'hood_reveal_mm':3})

if __name__=='__main__':
    apply();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(Path(sys.argv[1]).resolve()))
