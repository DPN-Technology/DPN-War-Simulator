import tempfile
import unittest
from pathlib import Path

from warsim.land_warfare import (
    create_land_warfare, begin_operation, cycle_unit, cycle_vehicle, cycle_sector, cycle_contact,
    order_selected_unit, enter_selected_vehicle, exit_player_vehicle, toggle_vehicle_engine,
    adjust_vehicle_throttle, steer_player_vehicle, fire_vehicle_weapon, request_artillery,
    request_joint_air_support, request_naval_gunfire, resupply_selected_unit, begin_medevac,
    advance_land_warfare, land_warfare_to_dict, land_warfare_from_dict,
)
from warsim.ground_ops import create_ground_ops
from warsim.task_force import create_task_force
from warsim.openworld import all_static_interactions, LAYERS, world_walkable, CAMERA_HEIGHT
from warsim.models import CareerProfile
from warsim.persistence import save_profile, load_profile


class LandWarfareV21Tests(unittest.TestCase):
    def test_01_state_has_platoons_vehicles_artillery_and_sectors(self):
        s=create_land_warfare()
        self.assertGreaterEqual(len(s.units),6); self.assertGreaterEqual(len(s.vehicles),5)
        self.assertGreaterEqual(len(s.artillery),1); self.assertEqual(4,len(s.sectors))

    def test_02_begin_operation_activates_battalion_exercise(self):
        s=create_land_warfare(); ok,msg=begin_operation(s)
        self.assertTrue(ok); self.assertTrue(s.active); self.assertEqual('ADVANCE',s.phase); self.assertIn('BATTALION',msg)

    def test_03_selectors_cycle(self):
        s=create_land_warfare(); u0=s.selected_unit.key; v0=s.selected_vehicle.key; b0=s.selected_sector.key; c0=s.selected_contact.key
        self.assertNotEqual(u0,cycle_unit(s).key); self.assertNotEqual(v0,cycle_vehicle(s).key)
        self.assertNotEqual(b0,cycle_sector(s).key); self.assertNotEqual(c0,cycle_contact(s).key)

    def test_04_platoon_order_targets_selected_sector(self):
        s=create_land_warfare(); begin_operation(s); u=s.selected_unit; sec=s.selected_sector
        ok,msg=order_selected_unit(s,'ADVANCE')
        self.assertTrue(ok); self.assertEqual('ADVANCE',u.order); self.assertAlmostEqual(sec.x,u.target_x); self.assertIn('ordered ADVANCE',msg)

    def test_05_enter_and_exit_battlefield_vehicle(self):
        s=create_land_warfare(); v=s.vehicles['TANK1']
        ok,msg=enter_selected_vehicle(s,v.x,v.y); self.assertTrue(ok); self.assertEqual('TANK1',s.player_vehicle_key)
        ok,msg=exit_player_vehicle(s); self.assertTrue(ok); self.assertEqual('',s.player_vehicle_key)

    def test_06_vehicle_engine_throttle_and_steering_moves(self):
        s=create_land_warfare(); v=s.vehicles['TANK1']; enter_selected_vehicle(s,v.x,v.y)
        toggle_vehicle_engine(s); adjust_vehicle_throttle(s,1.0); v.brake=False; x0,y0,h0=v.x,v.y,v.heading_deg
        for _ in range(20): steer_player_vehicle(s,1.0,.1)
        self.assertGreater(v.distance_m,0); self.assertNotEqual(h0,v.heading_deg); self.assertNotEqual((x0,y0),(v.x,v.y))

    def test_07_tank_fire_consumes_round_and_damages_contact(self):
        s=create_land_warfare(); v=s.vehicles['TANK1']; enter_selected_vehicle(s,v.x,v.y); c=s.selected_contact
        c.contact_type='ARMOR'; before=c.strength; ammo=v.main_ammo
        ok,msg=fire_vehicle_weapon(s)
        self.assertTrue(ok); self.assertEqual(ammo-1,v.main_ammo); self.assertLess(c.strength,before); self.assertIn('engaged',msg)

    def test_08_artillery_is_finite_and_damages_target(self):
        s=create_land_warfare(); begin_operation(s); c=s.selected_contact; b=next(iter(s.artillery.values())); shells=b.shells; before=c.strength
        ok,msg=request_artillery(s)
        self.assertTrue(ok); self.assertLess(b.shells,shells); self.assertLess(c.strength,before); self.assertGreater(s.artillery_missions,0)

    def test_09_joint_air_support_consumes_ground_support_pool(self):
        s=create_land_warfare(); begin_operation(s); go=create_ground_ops(); go.air_support_points=40; before=s.selected_contact.strength
        ok,msg=request_joint_air_support(s,go)
        self.assertTrue(ok); self.assertLess(go.air_support_points,40); self.assertLess(s.selected_contact.strength,before); self.assertIn('AIR SUPPORT',msg)

    def test_10_naval_support_consumes_escort_ammunition(self):
        s=create_land_warfare(); begin_operation(s); tf=create_task_force(); ship=next(iter(tf.friendly.values())); before=ship.ammo_pct
        ok,msg=request_naval_gunfire(s,tf)
        self.assertTrue(ok); self.assertLess(ship.ammo_pct,before); self.assertIn('NAVAL GUNFIRE',msg)

    def test_11_field_resupply_consumes_logistics(self):
        s=create_land_warfare(); u=s.selected_unit; u.ammo_pct=20; before=s.logistics.ammunition
        ok,msg=resupply_selected_unit(s)
        self.assertTrue(ok); self.assertGreater(u.ammo_pct,20); self.assertLess(s.logistics.ammunition,before); self.assertIn('resupplied',msg)

    def test_12_casevac_moves_wounded_to_field_hospital(self):
        s=create_land_warfare(); begin_operation(s); u=s.units['1PLT']; u.wounded=3; u.manpower=31
        ok,msg=begin_medevac(s); self.assertTrue(ok); self.assertTrue(s.casualty_evac.active)
        advance_land_warfare(s,13.0)
        self.assertFalse(s.casualty_evac.active); self.assertGreaterEqual(s.casualty_evac.evacuated_total,3); self.assertEqual(0,u.wounded)

    def test_13_sector_control_can_be_secured_by_assaulting_units(self):
        s=create_land_warfare(); begin_operation(s); sec=s.sectors['ALPHA']; u=s.units['1PLT']
        u.x,u.y=sec.x,sec.y; u.order='ASSAULT'; u.target_x,u.target_y=sec.x,sec.y
        sec.friendly_control=89; sec.enemy_strength=5
        for c in s.contacts.values():
            if abs(c.x-sec.x)<8 and abs(c.y-sec.y)<8: c.strength=0
        advance_land_warfare(s,1.0)
        self.assertEqual('SECURED',sec.status); self.assertGreaterEqual(s.sectors_secured,1)

    def test_14_full_operation_can_complete(self):
        s=create_land_warfare(); begin_operation(s)
        for c in s.contacts.values(): c.strength=0; c.status='NEUTRALIZED'
        for sec,u in zip(s.sectors.values(),list(s.units.values())[:4]):
            sec.friendly_control=90; sec.enemy_strength=5; u.x,u.y=sec.x,sec.y; u.order='ASSAULT'; u.target_x,u.target_y=sec.x,sec.y
        advance_land_warfare(s,1.0)
        self.assertFalse(s.active); self.assertEqual('COMPLETE',s.phase); self.assertEqual(1,s.operations_completed)

    def test_15_roundtrip_preserves_battlefield_state(self):
        s=create_land_warfare(); begin_operation(s); s.sectors['BRAVO'].friendly_control=47; s.vehicles['TANK1'].fuel_pct=66; s.score=84
        r=land_warfare_from_dict(land_warfare_to_dict(s))
        self.assertEqual(47,r.sectors['BRAVO'].friendly_control); self.assertEqual(66,r.vehicles['TANK1'].fuel_pct); self.assertEqual(84,r.score)

    def test_16_physical_battalion_sites_are_in_same_walkable_world(self):
        wanted=('land_command','land_armor','land_artillery','land_medevac','land_logistics','land_engineer','land_battlefield')
        interactions=all_static_interactions(); z=LAYERS['BASE'].floor_z+CAMERA_HEIGHT
        self.assertGreaterEqual(LAYERS['BASE'].height,170)
        for action in wanted:
            p=next(x for x in interactions if x.action==action)
            self.assertTrue(world_walkable(p.x,p.y,z),action)
        self.assertTrue(world_walkable(34,160,z))

    def test_17_old_profiles_get_new_land_warfare_fields(self):
        p=CareerProfile.from_dict({'name':'v2.0 Save','ground_combat_runs':3})
        self.assertEqual({},p.land_warfare_snapshot); self.assertEqual(0,p.land_operations_completed); self.assertEqual(3,p.ground_combat_runs)

    def test_18_profile_persists_land_warfare_snapshot_and_stats(self):
        p=CareerProfile(name='Land Tester',land_operations_completed=2,land_sectors_secured=7,land_warfare_best_score=93)
        p.land_warfare_snapshot=land_warfare_to_dict(create_land_warfare())
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'career.json'; save_profile(p,path); q=load_profile(path)
        self.assertEqual(2,q.land_operations_completed); self.assertEqual(7,q.land_sectors_secured); self.assertEqual(93,q.land_warfare_best_score); self.assertIn('sectors',q.land_warfare_snapshot)

if __name__=='__main__': unittest.main()
