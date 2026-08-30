import unittest
import math
import tempfile
from pathlib import Path

from warsim.ship_physics import (
    create_ship_physics, cast_off, secure_to_berth, set_engine_order, set_rudder,
    advance_ship_physics, toggle_anchor, training_depth_m, player_motion_modifiers,
    sync_operational_damage,
)
from warsim.walkship import create_shipboard_walk_state
from warsim.models import CareerProfile
from warsim.persistence import save_profile, load_profile


class ShipPhysicsV09Tests(unittest.TestCase):
    def test_moored_ship_cannot_accept_engine_order(self):
        s=create_ship_physics()
        msg=set_engine_order(s,1.0)
        self.assertIn("moored",msg.lower())
        self.assertEqual(0.0,s.engine_order)

    def test_cast_off_accelerates_ship(self):
        s=create_ship_physics(); ok,_=cast_off(s); self.assertTrue(ok)
        set_engine_order(s,1.0)
        for _ in range(1200): advance_ship_physics(s,.1)
        self.assertGreater(s.speed_knots,5.0)
        self.assertGreater(s.distance_nm,0.1)

    def test_rudder_changes_heading_only_meaningfully_with_way_on(self):
        s=create_ship_physics(); cast_off(s); set_engine_order(s,1.0)
        for _ in range(1500): advance_ship_physics(s,.1)
        h=s.heading_deg; set_rudder(s,30)
        for _ in range(500): advance_ship_physics(s,.1)
        delta=abs(((s.heading_deg-h+180)%360)-180)
        self.assertGreater(delta,2.0)
        self.assertLess(s.turning_radius_nm,999)

    def test_current_changes_course_over_ground(self):
        s=create_ship_physics(); cast_off(s); s.current_speed_knots=3.0; s.current_to_deg=0
        set_engine_order(s,.5)
        for _ in range(800): advance_ship_physics(s,.1)
        self.assertNotAlmostEqual(s.course_over_ground_deg,s.heading_deg,delta=.5)

    def test_sea_state_generates_roll_pitch_and_balance_load(self):
        s=create_ship_physics(); cast_off(s); s.sea_state=7; set_engine_order(s,.5)
        peaks=[]
        for _ in range(500):
            advance_ship_physics(s,.05); peaks.append(abs(s.roll_deg)+abs(s.pitch_deg))
        self.assertGreater(max(peaks),2.0)
        self.assertGreater(s.balance_load,0.0)
        mul,_=player_motion_modifiers(s); self.assertLessEqual(mul,1.0)

    def test_anchor_rejects_high_speed_then_stops_low_speed(self):
        s=create_ship_physics(); cast_off(s); s.speed_knots=5.0
        ok,_=toggle_anchor(s); self.assertFalse(ok)
        s.speed_knots=2.0; ok,_=toggle_anchor(s); self.assertTrue(ok)
        s.engine_order=0
        for _ in range(800): advance_ship_physics(s,.1)
        self.assertLess(abs(s.speed_knots),.5)

    def test_charted_shoal_can_ground_ship(self):
        self.assertLess(training_depth_m(2.8,1.8),8.0)
        s=create_ship_physics(); cast_off(s); s.east_nm=2.8; s.north_nm=1.8; s.speed_knots=8
        advance_ship_physics(s,.1)
        self.assertTrue(s.grounded)
        self.assertTrue(s.collision_alarm)

    def test_mooring_requires_home_and_low_speed(self):
        s=create_ship_physics(); cast_off(s); s.east_nm=.2
        ok,_=secure_to_berth(s); self.assertFalse(ok)
        s.east_nm=0; s.speed_knots=.2
        ok,_=secure_to_berth(s); self.assertTrue(ok); self.assertTrue(s.moored)

    def test_equipment_faults_reduce_control_integrity(self):
        s=create_ship_physics(); walk=create_shipboard_walk_state()
        walk.equipment_runtime["ENG_CONSOLE"].fault="SIMULATED"
        walk.equipment_runtime["HELM"].fault="SIMULATED"
        sync_operational_damage(s,walk)
        self.assertLess(s.propulsion_integrity,100)
        self.assertLess(s.steering_integrity,100)

    def test_new_ship_navigation_profile_fields_round_trip(self):
        p=CareerProfile(ship_nav_east_nm=1.25, ship_nav_north_nm=-.5, ship_heading_deg=231.0,
                        ship_speed_knots=12.4, ship_engine_order=.67, ship_rudder_deg=-10,
                        ship_moored=False, ship_sea_state=6, player_world_x=93.0, player_world_y=21.0,
                        player_world_z=8.02, player_world_yaw=1.2)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"career.json"
            save_profile(p,path); loaded=load_profile(path)
        self.assertAlmostEqual(loaded.ship_nav_east_nm,1.25)
        self.assertFalse(loaded.ship_moored)
        self.assertEqual(loaded.ship_sea_state,6)
        self.assertAlmostEqual(loaded.player_world_x,93.0)
        self.assertAlmostEqual(loaded.player_world_yaw,1.2)


if __name__ == "__main__": unittest.main()
