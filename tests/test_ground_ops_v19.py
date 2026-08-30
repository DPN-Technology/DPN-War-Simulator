import tempfile
import unittest
from pathlib import Path

from warsim.ground_ops import (
    create_ground_ops, accept_selected_mission, order_selected_unit_to_mission,
    order_selected_vehicle_to_mission, launch_amphibious_group, service_selected_airfield,
    add_air_support, advance_ground_ops, ground_ops_to_dict, ground_ops_from_dict,
    enter_training_vehicle, exit_training_vehicle, toggle_drive_engine, adjust_drive_throttle,
    advance_training_vehicle,
)
from warsim.campaign import create_campaign
from warsim.models import CareerProfile
from warsim.persistence import save_profile, load_profile
from warsim.openworld import all_static_interactions, LAYERS, world_walkable, CAMERA_HEIGHT


class GroundOpsV19Tests(unittest.TestCase):
    def test_01_ground_world_has_units_airfields_and_amphibious_force(self):
        s=create_ground_ops()
        self.assertGreaterEqual(len(s.units),4)
        self.assertGreaterEqual(len(s.airfields),2)
        self.assertGreaterEqual(len(s.amphibious),1)
        self.assertGreaterEqual(len(s.missions),4)

    def test_02_accept_ground_mission(self):
        s=create_ground_ops(); ok,msg=accept_selected_mission(s)
        self.assertTrue(ok); self.assertEqual(s.active_mission.status,'ACTIVE'); self.assertIn('ACCEPTED',msg)

    def test_03_ground_unit_moves_to_mission(self):
        s=create_ground_ops(); accept_selected_mission(s); ok,_=order_selected_unit_to_mission(s); self.assertTrue(ok)
        u=s.selected_unit; before=((u.east_nm-s.active_mission.target_east_nm)**2+(u.north_nm-s.active_mission.target_north_nm)**2)**.5
        advance_ground_ops(s,3600)
        after=((u.east_nm-s.active_mission.target_east_nm)**2+(u.north_nm-s.active_mission.target_north_nm)**2)**.5
        self.assertLess(after,before)

    def test_04_ground_vehicle_dispatch_and_supply_delivery(self):
        s=create_ground_ops(); s.selected_mission_index=2; accept_selected_mission(s)
        s.selected_vehicle_index=0; ok,_=order_selected_vehicle_to_mission(s); self.assertTrue(ok)
        v=s.selected_vehicle; v.east_nm=s.active_mission.target_east_nm-.05; v.north_nm=s.active_mission.target_north_nm
        before=s.supplies_delivered; advance_ground_ops(s,120)
        self.assertGreater(s.supplies_delivered,before)

    def test_05_airfield_service_uses_campaign_stock(self):
        s=create_ground_ops(); c=create_campaign(); s.selected_airfield_index=1
        a=s.selected_airfield; a.aviation_fuel=20; before=c.bases['FORWARD'].aviation_fuel
        ok,_=service_selected_airfield(s,c)
        self.assertTrue(ok); self.assertGreater(a.aviation_fuel,20); self.assertLess(c.bases['FORWARD'].aviation_fuel,before)

    def test_06_air_support_points_integrate_with_ground_ops(self):
        s=create_ground_ops(); msg=add_air_support(s,18,'test sortie')
        self.assertEqual(s.air_support_points,18); self.assertIn('air-support',msg)

    def test_07_airfield_defense_requires_air_support_for_progress(self):
        s=create_ground_ops(); accept_selected_mission(s); m=s.active_mission
        u=s.selected_unit; u.east_nm,u.north_nm=m.target_east_nm,m.target_north_nm; u.status='ON STATION'
        advance_ground_ops(s,600); self.assertEqual(0,m.progress_minutes)
        add_air_support(s,20); advance_ground_ops(s,600); self.assertGreater(m.progress_minutes,0)

    def test_08_amphibious_group_establishes_beachhead(self):
        s=create_ground_ops(); s.selected_mission_index=1; accept_selected_mission(s)
        ok,_=launch_amphibious_group(s); self.assertTrue(ok)
        g=next(iter(s.amphibious.values())); g.east_nm=s.active_mission.target_east_nm-.05; g.north_nm=s.active_mission.target_north_nm
        advance_ground_ops(s,120)
        self.assertEqual('BEACHHEAD',g.status)

    def test_09_ground_mission_can_complete(self):
        s=create_ground_ops(); s.selected_mission_index=3; accept_selected_mission(s); m=s.active_mission
        u=s.selected_unit; u.east_nm,u.north_nm=m.target_east_nm,m.target_north_nm; u.status='ON STATION'
        advance_ground_ops(s,(m.required_minutes+1)*60)
        self.assertEqual('COMPLETE',m.status); self.assertEqual(1,s.missions_completed)

    def test_10_ground_state_roundtrip(self):
        s=create_ground_ops(); s.operational_score=83; s.drive.distance_m=125; s.units['RIFLE_A'].strength_pct=71
        r=ground_ops_from_dict(ground_ops_to_dict(s))
        self.assertEqual(83,r.operational_score); self.assertEqual(125,r.drive.distance_m); self.assertEqual(71,r.units['RIFLE_A'].strength_pct)

    def test_11_training_vehicle_drive_model(self):
        s=create_ground_ops(); ok,_=enter_training_vehicle(s,28,52); self.assertTrue(ok)
        self.assertIn('RUNNING',toggle_drive_engine(s)); adjust_drive_throttle(s,.8); s.drive.brake=False
        x0,y0=s.drive.x,s.drive.y
        advance_training_vehicle(s,2,steer=.4)
        self.assertGreater(s.drive.distance_m,0); self.assertNotEqual((x0,y0),(s.drive.x,s.drive.y)); self.assertNotEqual(90,s.drive.heading_deg)

    def test_12_vehicle_exit_requires_stop(self):
        s=create_ground_ops(); enter_training_vehicle(s,28,52); toggle_drive_engine(s); adjust_drive_throttle(s,.8); s.drive.brake=False; advance_training_vehicle(s,1)
        ok,msg=exit_training_vehicle(s); self.assertFalse(ok); self.assertIn('Stop',msg)
        s.drive.speed_mps=0; ok,_=exit_training_vehicle(s); self.assertTrue(ok)

    def test_13_ground_physical_interactions_exist(self):
        actions={p.action for p in all_static_interactions()}
        for action in ('ground_console','ground_motor','ground_airfield','ground_amphib','ground_supply','ground_flightline'):
            self.assertIn(action,actions)

    def test_14_base_is_physically_extended_south(self):
        z=LAYERS['BASE'].floor_z+CAMERA_HEIGHT
        self.assertTrue(world_walkable(12,65,z)); self.assertTrue(world_walkable(52,65,z))
        self.assertGreaterEqual(LAYERS['BASE'].height,70)

    def test_15_profile_has_backward_compatible_ground_fields(self):
        p=CareerProfile.from_dict({'name':'Old Save','air_combat_sorties':2})
        self.assertEqual({},p.ground_ops_snapshot); self.assertEqual(0,p.ground_missions_completed)

    def test_16_profile_persists_ground_snapshot_and_stats(self):
        p=CareerProfile(name='Ground Tester',ground_missions_completed=2,ground_amphibious_landings=1,ground_ops_best_score=88)
        p.ground_ops_snapshot=ground_ops_to_dict(create_ground_ops())
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'career.json'; save_profile(p,path); q=load_profile(path)
        self.assertEqual(2,q.ground_missions_completed); self.assertIn('units',q.ground_ops_snapshot)


if __name__=='__main__': unittest.main()
