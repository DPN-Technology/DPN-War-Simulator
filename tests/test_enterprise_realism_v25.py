import math, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace

from warsim.models import CareerProfile
from warsim.persistence import save_profile, load_profile
from warsim.openworld import (
    LAYERS, CONNECTORS, CAMERA_HEIGHT, SHIP_ORIGIN_X, SHIP_ORIGIN_Y,
    SHIP_LENGTH_M, SHIP_WIDTH_M, SHIP_CENTER_X, SHIP_CENTER_Y,
    SHIP_ELEVATORS, SHIP_ISLAND_CENTER, layer_walkable,
)
from warsim.seamless3d import SHIP_EQUIPMENT_WORLD, SHIP_HATCH_WORLD, SeamlessOpenWorld3DApp
from warsim.firstperson3d import FirstPerson3DApp
from warsim.physical_world import damage_world_pose
from warsim.survivability import create_survivability

class EnterpriseRealismV25Tests(unittest.TestCase):
    def test_01_real_scale_carrier_dimensions(self):
        self.assertEqual(245, SHIP_LENGTH_M)
        self.assertEqual(30, SHIP_WIDTH_M)
        self.assertAlmostEqual(SHIP_ORIGIN_X+122.5, SHIP_CENTER_X)
        self.assertAlmostEqual(SHIP_ORIGIN_Y+15.0, SHIP_CENTER_Y)

    def test_02_all_ship_layers_span_full_length(self):
        for key in ("LOWER","ENGINEERING","HANGAR","FLIGHT","ISLAND","BRIDGE"):
            self.assertEqual(245, LAYERS[key].width, key)
            self.assertEqual(30, LAYERS[key].height, key)

    def test_03_flight_deck_has_large_walkable_area(self):
        self.assertGreater(sum(row.count('.') for row in LAYERS['FLIGHT'].grid), 5800)

    def test_04_hangar_is_long_narrow_carrier_space(self):
        # Centerline is open through the sourced ~166 m hangar envelope.
        for lx in (40,60,100,140,180,200):
            self.assertTrue(layer_walkable('HANGAR',SHIP_ORIGIN_X+lx+.2,SHIP_ORIGIN_Y+15.2),lx)

    def test_05_three_elevators_connect_hangar_and_flight(self):
        self.assertEqual(3,len(SHIP_ELEVATORS))
        for lx,ly in SHIP_ELEVATORS:
            self.assertTrue(layer_walkable('HANGAR',SHIP_ORIGIN_X+lx+.2,SHIP_ORIGIN_Y+ly+.2))
            self.assertTrue(layer_walkable('FLIGHT',SHIP_ORIGIN_X+lx+.2,SHIP_ORIGIN_Y+ly+.2))

    def test_06_island_is_starboard_and_aft_of_midships(self):
        ix,iy=SHIP_ISLAND_CENTER
        self.assertGreater(ix,SHIP_LENGTH_M*.6)
        self.assertGreater(iy,SHIP_WIDTH_M*.65)

    def test_07_connectors_reachable_after_rescale(self):
        for key,c in CONNECTORS.items():
            self.assertTrue(layer_walkable(c.from_layer,c.x,c.y),key+' from')
            self.assertTrue(layer_walkable(c.to_layer,c.x,c.y),key+' to')

    def test_08_equipment_reachable_after_rescale(self):
        for key,(layer,lx,ly) in SHIP_EQUIPMENT_WORLD.items():
            self.assertTrue(layer_walkable(layer,SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly),key)

    def test_09_hatches_reachable_after_rescale(self):
        for key,(layer,lx,ly) in SHIP_HATCH_WORLD.items():
            self.assertTrue(layer_walkable(layer,SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly),key)

    def test_10_damage_mapping_uses_full_ship_footprint(self):
        state=create_survivability()
        xs=[]; ys=[]
        for comp in state.compartments.values():
            x,y,_=damage_world_pose(comp); xs.append(x); ys.append(y)
            self.assertGreaterEqual(x,SHIP_ORIGIN_X)
            self.assertLessEqual(x,SHIP_ORIGIN_X+SHIP_LENGTH_M)
            self.assertGreaterEqual(y,SHIP_ORIGIN_Y)
            self.assertLessEqual(y,SHIP_ORIGIN_Y+SHIP_WIDTH_M)
        self.assertGreater(max(xs)-min(xs),80)

    def test_11_profile_layout_version_roundtrip(self):
        p=CareerProfile(name='V25',ship_layout_version=2,player_world_x=SHIP_CENTER_X)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'career.json'; save_profile(p,path); q=load_profile(path)
        self.assertEqual(2,q.ship_layout_version)
        self.assertAlmostEqual(SHIP_CENTER_X,q.player_world_x)

    def test_12_d_key_still_only_strafes(self):
        fake=SimpleNamespace(keys=set(),overlay=None)
        fake._interact=lambda:None; fake._set_message=lambda *a,**k:None
        SeamlessOpenWorld3DApp._key_down(fake,SimpleNamespace(keysym='d'))
        self.assertIn('d',fake.keys); self.assertIsNone(fake.overlay)

    def test_13_near_plane_clips_instead_of_dropping_face(self):
        fake=SimpleNamespace(x=0.0,y=0.0,z=1.7,yaw=0.0,pitch=0.0,render_distance=30.0)
        faces=[]
        # Two vertices are behind/inside near plane; old renderer dropped the entire face.
        verts=[(-.20,-1,0.0),(.25,-1,0.0),(.25,1,2.0),(-.20,1,2.0)]
        FirstPerson3DApp._add_face(fake,faces,verts,'#888888','',1280,720)
        self.assertGreaterEqual(len(faces),1)
        self.assertGreaterEqual(len(faces[0][1]),6)

    def test_14_old_profile_default_marks_migration_needed(self):
        self.assertEqual(1,CareerProfile().ship_layout_version)

    def test_15_full_scale_ship_is_over_three_times_old_prototype(self):
        self.assertGreater(SHIP_LENGTH_M/72.0,3.3)

if __name__=='__main__': unittest.main()
