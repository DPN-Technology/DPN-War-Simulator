import inspect
import unittest
from types import SimpleNamespace

from warsim.air_wing import (
    create_air_wing, cycle_squadron, cycle_mission_type, adjust_sortie_size,
    plan_selected_mission, launch_selected_mission, advance_air_wing,
    recover_selected_mission, service_selected_squadron,
    air_wing_to_dict, air_wing_from_dict, STATUS_AIRBORNE,
)
from warsim.models import CareerProfile
from warsim.openworld import all_static_interactions
from warsim.seamless3d import SeamlessOpenWorld3DApp


class AirWingV15Tests(unittest.TestCase):
    def test_01_air_group_has_squadrons_and_individual_aircraft(self):
        s=create_air_wing(1234)
        self.assertEqual(set(s.squadrons), {"VF6","VB6","VS6","VT6"})
        self.assertEqual(len(s.aircraft), 42)
        self.assertEqual(len(s.aircrew), 42)

    def test_02_squadron_and_mission_selection(self):
        s=create_air_wing()
        self.assertEqual(s.selected_squadron,"VF6")
        self.assertEqual(cycle_squadron(s).key,"VB6")
        self.assertEqual(cycle_mission_type(s),"SCOUT")
        self.assertEqual(adjust_sortie_size(s,3),7)

    def test_03_cap_requires_fighter_squadron(self):
        s=create_air_wing(); s.selected_squadron="VB6"; s.selected_mission_type="CAP"
        ok,msg=plan_selected_mission(s,0,0,90)
        self.assertFalse(ok); self.assertIn("fighter",msg.lower())

    def test_04_plan_spots_individual_aircraft(self):
        s=create_air_wing(); s.selected_sortie_size=6
        ok,msg=plan_selected_mission(s,0,0,90)
        self.assertTrue(ok)
        m=s.missions[s.selected_mission]
        self.assertEqual(len(m.aircraft_keys),6)
        self.assertTrue(all(s.aircraft[k].deck=="FLIGHT" for k in m.aircraft_keys))

    def test_05_launch_requires_wind_over_deck(self):
        s=create_air_wing(); plan_selected_mission(s,0,0,90)
        ok,msg=launch_selected_mission(s,4.0,12.0,True)
        self.assertFalse(ok); self.assertIn("wind",msg.lower())

    def test_06_launch_consumes_fuel_and_sets_airborne(self):
        s=create_air_wing(); plan_selected_mission(s,0,0,90)
        fuel=s.aviation_fuel_units
        ok,_=launch_selected_mission(s,18.0,20.0,True)
        self.assertTrue(ok); self.assertLess(s.aviation_fuel_units,fuel)
        m=s.missions[s.selected_mission]
        self.assertTrue(all(s.aircraft[k].status==STATUS_AIRBORNE for k in m.aircraft_keys))

    def test_07_airborne_mission_progresses_and_returns(self):
        s=create_air_wing(); plan_selected_mission(s,0,0,90); launch_selected_mission(s,18,20,True)
        m=s.missions[s.selected_mission]
        advance_air_wing(s,m.planned_minutes*.75*60,0,0,3)
        self.assertEqual(m.status,"RETURNING")
        self.assertGreater(m.distance_nm,0)

    def test_08_scout_generates_role_limited_report(self):
        s=create_air_wing(); s.selected_squadron="VS6"; s.selected_mission_type="SCOUT"; s.selected_sortie_size=4
        self.assertTrue(plan_selected_mission(s,0,0,0)[0]); self.assertTrue(launch_selected_mission(s,16,18,True)[0])
        m=s.missions[s.selected_mission]
        advance_air_wing(s,m.planned_minutes*.45*60,0,0,3)
        self.assertGreaterEqual(s.scout_reports,1)

    def test_09_recovery_returns_aircraft_to_hangar(self):
        s=create_air_wing(); plan_selected_mission(s,0,0,90); launch_selected_mission(s,18,20,True)
        m=s.missions[s.selected_mission]; advance_air_wing(s,m.planned_minutes*.75*60,0,0,3)
        ok,_=recover_selected_mission(s,18,True)
        self.assertTrue(ok); self.assertEqual(m.status,"COMPLETE")
        self.assertTrue(all(s.aircraft[k].deck=="HANGAR" for k in m.aircraft_keys))

    def test_10_service_repairs_aircraft(self):
        s=create_air_wing(); key=s.squadrons["VF6"].aircraft_keys[0]
        s.aircraft[key].condition=70; before=s.aircraft[key].condition
        ok,_=service_selected_squadron(s)
        self.assertTrue(ok); self.assertGreater(s.aircraft[key].condition,before)

    def test_11_air_wing_roundtrip_persistence(self):
        s=create_air_wing(); s.selected_sortie_size=7; plan_selected_mission(s,2,3,80)
        r=air_wing_from_dict(air_wing_to_dict(s))
        self.assertEqual(r.selected_sortie_size,7)
        self.assertEqual(len(r.aircraft),42)
        self.assertEqual(len(r.missions),1)

    def test_12_physical_air_group_rooms_exist(self):
        actions=[p.action for p in all_static_interactions()]
        self.assertGreaterEqual(actions.count("air_wing_console"),2)

    def test_13_profile_backward_compatible_air_wing_fields(self):
        p=CareerProfile.from_dict({"name":"Legacy","campaign_missions_completed":3})
        self.assertEqual(p.air_wing_snapshot,{})
        self.assertEqual(p.air_wing_missions_completed,0)

    def test_14_d_key_is_reserved_for_strafe_not_global_overlay(self):
        fake=SimpleNamespace(keys=set(),overlay=None)
        event=SimpleNamespace(keysym="d")
        SeamlessOpenWorld3DApp._key_down(fake,event)
        self.assertIn("d",fake.keys)
        self.assertIsNone(fake.overlay)

    def test_15_damage_control_global_shortcut_moved_to_f6(self):
        src=inspect.getsource(SeamlessOpenWorld3DApp._key_down)
        self.assertIn('key == "f6"',src)
        self.assertNotIn('elif key == "d":\n            self.overlay = "survivability_dc"',src)

    def test_16_advanced_geometry_helpers_present(self):
        for name in ("_add_cylinder","_add_console_model","_add_humanoid","_add_aircraft_model","_add_ship_model","_collect_detail_geometry"):
            self.assertTrue(hasattr(SeamlessOpenWorld3DApp,name),name)


if __name__ == '__main__':
    unittest.main()
