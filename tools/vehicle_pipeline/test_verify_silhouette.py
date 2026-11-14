"""Controlled numerical tests, independent of Blender and the Saab asset."""
import json,tempfile,unittest
from pathlib import Path
import numpy as np
from PIL import Image
from verify_silhouette import compare,registration,extract,annotated_metrics,PPM,ORIGIN,normalize

class SilhouetteTests(unittest.TestCase):
    def setUp(self):
        self.ref=np.zeros((650,1600),bool)
        self.ref[320:530,250:1300]=True
        self.ref[190:320,550:1000]=True
        self.regions={'hood':[-.7,2.9,0,1.5],'roof':[.3,1.8,.9,1.5]}
        # Explicit disjoint ROIs: hood lies to the right of the cabin.
        self.regions['hood']=[2.,2.9,0,1.5]
    def metrics(self,m):return compare(self.ref,m,self.regions)
    def test_identical(self):
        a,b,_=self.metrics(self.ref.copy());self.assertEqual(a['iou'],1);self.assertEqual(a['max_contour_distance_px'],0)
    def test_high_hood(self):
        m=self.ref.copy();m[300:320,1035:1280]=True
        self.assertGreater(self.metrics(m)[1]['hood']['signed_height_mean_px'],15)
    def test_low_hood(self):
        m=self.ref.copy();m[320:340,1035:1280]=False
        self.assertLess(self.metrics(m)[1]['hood']['signed_height_mean_px'],-15)
    def test_wheel_held_out(self):
        f=dict(rear_wheel=[100,300],front_wheel=[600,300],ground=[100,360])
        r=dict(points={'wheel_check':[600,300]});m=dict(points={'wheel_check':[620,300]})
        result=annotated_metrics(r,m,registration(f,2.5),registration(f,2.5))
        self.assertAlmostEqual(result['points']['wheel_check']['dx_px'],28)
    def test_independent_scale(self):
        f=dict(rear_wheel=[100,300],front_wheel=[600,300],ground=[100,360],pixels_per_metre=220)
        tr=registration(f,2.5)
        self.assertAlmostEqual(tr[2]/f['pixels_per_metre']-1,-1/11)
    def test_hood_and_roof_independent(self):
        bad=self.ref.copy();bad[320:350,1035:1280]=False
        good=self.ref.copy();good[170:190,560:960]=True
        a=self.metrics(bad)[1];b=self.metrics(good)[1]
        self.assertLess(b['hood']['absolute_height_mean_px'],a['hood']['absolute_height_mean_px'])
        self.assertGreater(b['roof']['absolute_height_mean_px'],a['roof']['absolute_height_mean_px'])
    def test_bad_mask(self):
        with tempfile.TemporaryDirectory() as d:
            Image.new('RGBA',(100,100),'white').save(Path(d)/'image.png')
            f={'image':'image.png','mask':{'mode':'manual_polygon','polygon':[[1,1],[2,1],[1,2]]}}
            self.assertTrue(any('INVALID' in w for w in extract(f,Path(d))[2]))
            f['mask']={'mode':'alpha'}
            with self.assertRaisesRegex(ValueError,'constant'):extract(f,Path(d))
    def test_pipeline_warns_about_bad_scale_and_unreviewed_reference(self):
        from verify_silhouette import analyze
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            Image.fromarray(self.ref.astype('uint8')*255).save(root/'mask.png')
            im=Image.new('RGBA',(1600,650),'white');im.putalpha(Image.fromarray(self.ref.astype('uint8')*255));im.save(root/'source.png')
            frame=dict(image='source.png',mask=dict(mode='alpha',reviewed=False),rear_wheel=[470,480],front_wheel=[1170,480],ground=[470,565],pixels_per_metre=300,orthographic=True,metric_reliable=True)
            config=dict(vehicle='synthetic',reference=frame,dimensions={'wheelbase_m':{'value':2.5}},regions=self.regions)
            (root/'config.json').write_text(json.dumps(config));(root/'frame.json').write_text(json.dumps(frame))
            r=analyze(root/'config.json',root/'frame.json',root/'out')
            self.assertFalse(r['data_quality']['metric_geometry_verified'])
            self.assertTrue(any('mismatch' in w for w in r['data_quality']['warnings']))
            self.assertEqual(r['global_metrics']['iou'],1)
            self.assertTrue((root/'out/overlay.png').is_file())
            self.assertAlmostEqual(r['normalization']['independent_calibration']['model']['independent_wheelbase_m'],700/300)
    def test_missing_reference(self):
        with self.assertRaisesRegex(ValueError,'Missing'):extract({'image':'no-such-image'},Path('/tmp'))
    def test_reproducible(self):
        self.assertEqual(self.metrics(self.ref)[0],self.metrics(self.ref)[0])
    def test_uniform_registration_rotation_and_flip(self):
        f=dict(rear_wheel=[700,200],front_wheel=[200,200],ground=[700,260])
        tr=registration(f,2.5)
        p=np.array(f['front_wheel'])@tr[0].T+tr[1]
        self.assertAlmostEqual(p[0],ORIGIN[0]+PPM*2.5)
        self.assertAlmostEqual(np.linalg.det(tr[0]),-(PPM/200)**2)

if __name__=='__main__':unittest.main()
