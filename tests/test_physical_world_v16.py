import math
import tempfile
import unittest
from pathlib import Path

from warsim.models import CareerProfile
from warsim.persistence import save_profile, load_profile
from warsim.physical_world import (
    PhysicalWorldState, advance_physical_world, cycle_weather, physical_world_to_dict,
    physical_world_from_dict, damage_world_pose, sky_colors,
)
from warsim.survivability import create_survivability
from warsim.openworld import LAYERS, SHIP_ORIGIN_X, SHIP_ORIGIN_Y


class PhysicalWorldV16Tests(unittest.TestCase):
    def test_weather_cycles_all_presets(self):
        s=PhysicalWorldState()
        seen=[]
        for _ in range(4):
            seen.append(s.weather_mode)
            cycle_weather(s)
        self.assertEqual(["CLEAR","OVERCAST","RAIN","STORM"], seen)
        self.assertEqual("CLEAR", s.weather_mode)

    def test_daylight_changes_between_noon_and_midnight(self):
        noon=PhysicalWorldState(); midnight=PhysicalWorldState()
        advance_physical_world(noon,1,12*60,3,0,{},True)
        advance_physical_world(midnight,1,0,3,0,{},True)
        self.assertGreater(noon.daylight, midnight.daylight)

    def test_storm_builds_rain_and_fog(self):
        s=PhysicalWorldState(weather_mode="STORM")
        for _ in range(10):
            advance_physical_world(s,.5,12*60,7,12,{},True)
        self.assertGreater(s.rain_intensity,.70)
        self.assertGreater(s.cloud_cover,.80)
        self.assertGreater(s.fog_density,.10)

    def test_hatch_visual_animates_toward_target(self):
        s=PhysicalWorldState(hatch_fraction={"H":1.0})
        advance_physical_world(s,.2,600,3,0,{"H":False},True)
        self.assertGreater(s.hatch_fraction["H"],0)
        self.assertLess(s.hatch_fraction["H"],1)
        for _ in range(10):
            advance_physical_world(s,.2,600,3,0,{"H":False},True)
        self.assertAlmostEqual(0.0,s.hatch_fraction["H"],places=3)

    def test_radar_rotates_only_when_operational(self):
        s=PhysicalWorldState()
        advance_physical_world(s,1,600,3,0,{},True)
        angle=s.radar_angle_deg
        self.assertGreater(angle,0)
        advance_physical_world(s,1,600,3,0,{},False)
        self.assertAlmostEqual(angle,s.radar_angle_deg,places=4)

    def test_propeller_animation_scales_with_speed(self):
        slow=PhysicalWorldState(); fast=PhysicalWorldState()
        advance_physical_world(slow,.5,600,3,0,{},True)
        advance_physical_world(fast,.5,600,3,25,{},True)
        self.assertGreater(fast.propeller_phase_deg,slow.propeller_phase_deg)

    def test_damage_pose_maps_inside_training_carrier(self):
        s=create_survivability()
        for comp in s.compartments.values():
            x,y,z=damage_world_pose(comp)
            self.assertGreaterEqual(x,SHIP_ORIGIN_X+4)
            self.assertLessEqual(x,SHIP_ORIGIN_X+245)
            self.assertGreaterEqual(y,SHIP_ORIGIN_Y+5)
            self.assertLessEqual(y,SHIP_ORIGIN_Y+30)
            self.assertAlmostEqual(LAYERS[comp.deck].floor_z,z)

    def test_sky_palette_changes_for_night(self):
        day=PhysicalWorldState(daylight=.9,cloud_cover=.1)
        night=PhysicalWorldState(daylight=.08,cloud_cover=.1)
        self.assertNotEqual(sky_colors(day),sky_colors(night))

    def test_physical_world_round_trip(self):
        s=PhysicalWorldState(weather_mode="RAIN",rain_intensity=.6,hatch_fraction={"A":.4},radar_angle_deg=123)
        r=physical_world_from_dict(physical_world_to_dict(s))
        self.assertEqual("RAIN",r.weather_mode)
        self.assertAlmostEqual(.4,r.hatch_fraction["A"])
        self.assertAlmostEqual(123,r.radar_angle_deg)

    def test_career_save_preserves_physical_snapshot(self):
        p=CareerProfile(name="V16 Tester")
        p.physical_world_snapshot=physical_world_to_dict(PhysicalWorldState(weather_mode="OVERCAST",fog_density=.21))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"career.json"
            save_profile(p,path)
            q=load_profile(path)
        self.assertIsNotNone(q)
        self.assertEqual("OVERCAST",q.physical_world_snapshot["weather_mode"])
        self.assertAlmostEqual(.21,q.physical_world_snapshot["fog_density"])


if __name__ == "__main__":
    unittest.main()
