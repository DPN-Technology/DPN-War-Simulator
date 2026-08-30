import json, struct, unittest
from pathlib import Path
from types import SimpleNamespace

from warsim.config import VERSION
from warsim.seamless3d import SeamlessOpenWorld3DApp

ROOT=Path(__file__).resolve().parents[1]
ASSET=ROOT/'assets3d'/'Enterprise_CV6_1942_Midway.glb'
EDIT=ROOT/'assets3d'/'Enterprise_CV6_1942_Midway_EDITABLE.glb'
MANIFEST=ROOT/'assets3d'/'Enterprise_CV6_1942_Midway_manifest.json'
REF=ROOT/'historical_data'/'enterprise_1942_visual_v26.json'
UE=ROOT/'ue5'/'WarSimulatorUE5'

class EnterpriseVisualV26Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.man=json.loads(MANIFEST.read_text(encoding='utf-8'))
        cls.ref=json.loads(REF.read_text(encoding='utf-8'))

    def test_01_version(self): self.assertGreaterEqual(tuple(map(int,VERSION.split('.'))),(2,6,0))
    def test_02_runtime_glb_exists(self): self.assertGreater(ASSET.stat().st_size,150_000)
    def test_03_editable_glb_exists(self): self.assertGreater(EDIT.stat().st_size,200_000)
    def test_04_glb_magic(self): self.assertEqual(b'glTF',ASSET.read_bytes()[:4])
    def test_05_full_scale_bounds(self):
        b=self.man['geometry']['bounds_m']; self.assertGreaterEqual(b[1][0]-b[0][0],251.0); self.assertGreater(b[1][1]-b[0][1],31.0)
    def test_06_runtime_drawcall_grouping(self): self.assertLessEqual(self.man['geometry'].get('runtime_groups', self.man['geometry'].get('runtime_material_groups',99)),60)
    def test_07_editable_parts(self): self.assertGreaterEqual(self.man['geometry']['editable_objects'],450)
    def test_08_triangle_budget(self): self.assertGreater(self.man['geometry']['triangles'],11000)
    def test_09_three_elevators(self):
        self.assertTrue(all(any(k.startswith(f'Elevator_{i}_') for k in self.man['parts']) for i in (1,2,3)))
    def test_10_midway_period_features(self):
        parts=self.man['parts']; self.assertTrue(any(k.startswith('CXAM1') for k in parts)); self.assertTrue(any(k.startswith('AircraftCrane') or k.startswith('Aircraft_Crane') for k in parts))
    def test_11_period_armament_counts(self):
        parts=self.man['parts']
        self.assertEqual(8,len([k for k in parts if k.startswith('5in38_') and k.endswith('_Base')]))
        self.assertEqual(4,len([k for k in parts if k.startswith('1p1_quad_') and k.endswith('_Base')]))
        self.assertEqual(30,len([k for k in parts if k.startswith('Oerlikon20_') and k.endswith('_Pedestal')]))
    def test_12_reference_period_lock(self): self.assertIn('Midway',self.ref['target'])
    def test_13_pbr_texture_pack(self):
        tex=ROOT/'assets3d'/'textures';
        for n in ('flight_deck_albedo.png','flight_deck_roughness.png','flight_deck_normal.png','hull_bluegray_albedo.png','hull_roughness.png'): self.assertTrue((tex/n).exists(),n)
    def test_14_ue5_project_exists(self): self.assertTrue((UE/'WarSimulatorUE5.uproject').exists())
    def test_15_ue5_gpu_settings(self):
        ini=(UE/'Config'/'DefaultEngine.ini').read_text(encoding='utf-8'); self.assertIn('r.Nanite.ProjectEnabled=1',ini); self.assertIn('r.DynamicGlobalIlluminationMethod=1',ini); self.assertIn('PCD3D_SM6',ini)
    def test_16_ue5_first_person_d_binding(self):
        ini=(UE/'Config'/'DefaultInput.ini').read_text(encoding='utf-8'); self.assertIn('AxisName="MoveRight",Scale=1.000000,Key=D',ini)
    def test_17_ue5_save_bridge(self): self.assertTrue((UE/'Source'/'WarSimulatorUE5'/'WarSimStateBridge.cpp').exists())
    def test_18_legacy_d_key_still_movement_only(self):
        fake=SimpleNamespace(keys=set(),overlay=None); fake._interact=lambda:None; fake._set_message=lambda *a,**k:None
        SeamlessOpenWorld3DApp._key_down(fake,SimpleNamespace(keysym='d')); self.assertIn('d',fake.keys); self.assertIsNone(fake.overlay)
    def test_19_unreal_build_script(self): self.assertTrue((ROOT/'BUILD_UE5_WINDOWS.bat').exists())
    def test_20_visual_reference_boundaries(self): self.assertGreater(len(self.ref['reconstruction_only']),4)

if __name__=='__main__': unittest.main()
