import json, unittest
from pathlib import Path
from types import SimpleNamespace
from warsim.config import VERSION
from warsim.seamless3d import SeamlessOpenWorld3DApp

ROOT=Path(__file__).resolve().parents[1]
AS=ROOT/'assets3d'
MAN=AS/'Enterprise_CV6_1942_Midway_manifest.json'
HIST=ROOT/'historical_data'/'enterprise_1942_reconstruction_v27.json'
UE=ROOT/'ue5'/'WarSimulatorUE5'

class EnterpriseReconstructionV27Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads(MAN.read_text(encoding='utf-8'))
        cls.h=json.loads(HIST.read_text(encoding='utf-8'))
        cls.parts=cls.m['parts']
    def test_01_version(self): self.assertEqual('2.7.0',VERSION)
    def test_02_runtime_asset_is_substantial(self): self.assertGreater((AS/'Enterprise_CV6_1942_Midway.glb').stat().st_size,1_000_000)
    def test_03_editable_asset_is_substantial(self): self.assertGreater((AS/'Enterprise_CV6_1942_Midway_EDITABLE.glb').stat().st_size,1_000_000)
    def test_04_editable_component_density(self): self.assertGreaterEqual(self.m['geometry']['editable_objects'],1400)
    def test_05_triangle_density(self): self.assertGreaterEqual(self.m['geometry']['triangles'],40000)
    def test_06_runtime_group_budget(self): self.assertLessEqual(self.m['geometry']['runtime_groups'],60)
    def test_07_full_scale_bounds(self):
        b=self.m['geometry']['bounds_m']; self.assertGreaterEqual(b[1][0]-b[0][0],251.0); self.assertGreater(b[1][1]-b[0][1],35.0)
    def test_08_three_elevators(self): self.assertEqual(3,len([k for k in self.parts if k.endswith('_Platform') and k.startswith('Elevator_')]))
    def test_09_period_radar_and_director(self):
        self.assertTrue(any(k.startswith('CXAM1') for k in self.parts)); self.assertIn('Mk33_Director_House',self.parts)
    def test_10_crane_searchlights_loudspeakers(self):
        self.assertIn('AircraftCrane_Boom',self.parts); self.assertGreaterEqual(len([k for k in self.parts if k.startswith('Searchlight_')]),4); self.assertGreaterEqual(len([k for k in self.parts if k.startswith('Loudspeaker_')]),4)
    def test_11_period_weapon_targets(self):
        self.assertEqual(8,len([k for k in self.parts if k.startswith('5in38_') and k.endswith('_Base')]))
        self.assertEqual(4,len([k for k in self.parts if k.startswith('1p1_quad_') and k.endswith('_Base')]))
        self.assertEqual(30,len([k for k in self.parts if k.startswith('Oerlikon20_') and k.endswith('_Pedestal')]))
    def test_12_human_scale_deck_detail(self):
        self.assertGreaterEqual(len([k for k in self.parts if k.startswith('TieDown_')]),80); self.assertTrue(any(k.startswith('HoseReel_') for k in self.parts)); self.assertTrue(any(k.startswith('SafetyNetDiag') for k in self.parts))
    def test_13_hull_detail(self):
        self.assertTrue(any(k.startswith('HullLongSeam_') for k in self.parts)); self.assertTrue(any(k.startswith('GalleryScupper_') for k in self.parts)); self.assertTrue(any(k.startswith('HawsePipe_') for k in self.parts))
    def test_14_island_access_detail(self): self.assertGreaterEqual(len([k for k in self.parts if k.startswith('IslandDoor_')]),4)
    def test_15_exterior_streaming_modules(self):
        for n in self.m['exterior_modules']: self.assertGreater((AS/'modules'/n).stat().st_size,20_000,n)
    def test_16_interior_streaming_modules(self):
        for n in self.m['interior_modules']: self.assertGreater((AS/'interiors'/n).stat().st_size,25_000,n)
    def test_17_pbr_maps(self):
        tex=AS/'textures'
        for n in ('cv6_1942_flightdeck_albedo.png','cv6_1942_flightdeck_normal.png','cv6_1942_flightdeck_roughness.png','cv6_1942_hull_albedo.png','cv6_1942_hull_normal.png','cv6_1942_hull_roughness.png'): self.assertTrue((tex/n).exists(),n)
    def test_18_unreal_imports_all_modules(self):
        s=(UE/'Content'/'Python'/'import_enterprise.py').read_text(encoding='utf-8');
        for n in ('CV6_HullDeck_Hangar.glb','CV6_Island.glb','CV6_Weapons_Fittings.glb','CV6_DeckAircraft.glb','Enterprise_CV6_1942_Bridge_Interior.glb'): self.assertIn(n,s)
        self.assertIn('Nanite',s); self.assertIn('CTF_USE_COMPLEX_AS_SIMPLE',s)
    def test_19_unreal_physical_ship_actors(self):
        for n in ('CV6WatertightDoorActor.h','CV6CompartmentVolume.h','EnterpriseCV6Actor.h'): self.assertTrue((UE/'Source'/'WarSimulatorUE5'/n).exists(),n)
    def test_20_unreal_modular_actor(self):
        s=(UE/'Source'/'WarSimulatorUE5'/'EnterpriseCV6Actor.h').read_text();
        for n in ('HullDeckHangar','IslandExterior','WeaponsFittings','DeckAircraft','HangarInterior','BridgeInterior','CICInterior','EngineeringInterior'): self.assertIn(n,s)
    def test_21_historical_boundary(self): self.assertGreaterEqual(len(self.h['reconstruction_only']),8)
    def test_22_source_set(self): self.assertGreaterEqual(len(self.h['primary_reference_set']),5)
    def test_23_d_key_regression(self):
        fake=SimpleNamespace(keys=set(),overlay=None); fake._interact=lambda:None; fake._set_message=lambda *a,**k:None
        SeamlessOpenWorld3DApp._key_down(fake,SimpleNamespace(keysym='d')); self.assertIn('d',fake.keys); self.assertIsNone(fake.overlay)
    def test_24_cutaway_preview_exists(self): self.assertGreater((AS/'Enterprise_CV6_1942_InteriorModules_preview.png').stat().st_size,100_000)

if __name__=='__main__': unittest.main()
