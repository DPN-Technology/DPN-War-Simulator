import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from warsim.flight_ops import FlightState, flight_from_dict, flight_to_dict
from warsim.flight_combat import (
    FlightCombatState, configure_sortie, cycle_contact, cycle_waypoint, radio_report,
    fire_guns, release_ordnance, apply_aircraft_damage, emergency_abandon,
    advance_air_combat, navigation_solution, combat_to_dict, combat_from_dict,
)
from warsim.models import CareerProfile
from warsim.persistence import save_profile, load_profile


class FlightCombatV18Tests(unittest.TestCase):
    def flight(self, ac_type='F4F Wildcat'):
        return FlightState(active=True,aircraft_key='VF6-01',aircraft_type=ac_type,on_deck=False,
                           engine_running=True,throttle=.85,east_nm=0,north_nm=0,altitude_ft=3000,
                           heading_deg=90,airspeed_knots=130,fuel_pct=80)

    def test_01_configure_cap_spawns_air_targets_and_stores(self):
        f=self.flight(); c=FlightCombatState(); msg=configure_sortie(c,f,'CAP',0,0,90)
        self.assertIn('CAP',msg); self.assertTrue(c.active_sortie)
        self.assertGreaterEqual(sum(x.kind=='AIR' for x in c.contacts.values()),3)
        self.assertEqual(240,f.gun_ammo)

    def test_02_configure_strike_gives_sbd_bomb(self):
        f=self.flight('SBD Dauntless'); c=FlightCombatState(); configure_sortie(c,f,'STRIKE',0,0,90)
        self.assertEqual(1,f.bombs); self.assertTrue(any(x.kind=='SURFACE' for x in c.contacts.values()))

    def test_03_cycle_contact_changes_selection(self):
        f=self.flight(); c=FlightCombatState(); configure_sortie(c,f,'CAP',0,0,90)
        first=c.selected_contact; cycle_contact(c); self.assertNotEqual(first,c.selected_contact)

    def test_04_gun_hit_and_kill_uses_geometry(self):
        f=self.flight(); c=FlightCombatState(); configure_sortie(c,f,'CAP',0,0,90)
        target=next(x for x in c.contacts.values() if x.kind=='AIR'); c.selected_contact=target.key
        # Place target directly ahead in training firing envelope.
        target.east_nm=.20; target.north_nm=0; target.altitude_ft=f.altitude_ft; target.health=12
        f.heading_deg=90
        ok,msg=fire_guns(c,f)
        self.assertTrue(ok); self.assertFalse(target.active); self.assertEqual(1,c.aerial_victories); self.assertLess(f.gun_ammo,240)

    def test_05_gun_miss_still_consumes_ammo(self):
        f=self.flight(); c=FlightCombatState(); configure_sortie(c,f,'CAP',0,0,90)
        target=next(x for x in c.contacts.values() if x.kind=='AIR'); c.selected_contact=target.key
        target.east_nm=3; target.north_nm=0
        before=f.gun_ammo; ok,msg=fire_guns(c,f)
        self.assertFalse(ok); self.assertLess(f.gun_ammo,before); self.assertIn('miss',msg.lower())

    def test_06_bomb_release_hits_surface_target(self):
        f=self.flight('SBD Dauntless'); f.altitude_ft=1400; c=FlightCombatState(); configure_sortie(c,f,'STRIKE',0,0,90)
        target=next(x for x in c.contacts.values() if x.kind=='SURFACE'); c.selected_contact=target.key
        target.east_nm=.35; target.north_nm=0; f.heading_deg=90
        ok,msg=release_ordnance(c,f)
        self.assertTrue(ok); self.assertEqual(0,f.bombs); self.assertEqual(1,c.surface_hits)

    def test_07_torpedo_requires_low_slow_attack(self):
        f=self.flight('TBD Devastator'); f.altitude_ft=120; f.airspeed_knots=110; c=FlightCombatState(); configure_sortie(c,f,'STRIKE',0,0,90)
        target=next(x for x in c.contacts.values() if x.kind=='SURFACE'); c.selected_contact=target.key
        target.east_nm=.45; target.north_nm=0; f.heading_deg=90
        ok,_=release_ordnance(c,f); self.assertTrue(ok); self.assertEqual(0,f.torpedoes)

    def test_08_damage_degrades_engine_controls_and_pilot(self):
        f=self.flight(); c=FlightCombatState(); msg=apply_aircraft_damage(c,f,20,'test')
        self.assertLess(f.airframe_health,100); self.assertLess(f.engine_health,100); self.assertLess(f.control_health,100); self.assertIn('AIRCRAFT HIT',msg)

    def test_09_severe_engine_damage_can_stop_engine(self):
        f=self.flight(); f.engine_health=20; c=FlightCombatState(); apply_aircraft_damage(c,f,10,'test')
        self.assertFalse(f.engine_running); self.assertEqual(0,f.throttle)

    def test_10_navigation_cycles_and_solution(self):
        f=self.flight(); c=FlightCombatState(); configure_sortie(c,f,'SCOUT',0,0,90)
        txt=navigation_solution(c,f,0,0); self.assertIn('NAV MISSION',txt)
        self.assertIn('HOME_BASE',cycle_waypoint(c,0,0)); self.assertIn('CARRIER',cycle_waypoint(c,0,0))

    def test_11_radio_report_identifies_close_contact(self):
        f=self.flight(); c=FlightCombatState(); configure_sortie(c,f,'CAP',0,0,90)
        target=next(x for x in c.contacts.values() if x.kind=='AIR'); c.selected_contact=target.key
        target.east_nm=.5; target.north_nm=0
        txt=radio_report(c,f,0,0); self.assertIn('carrier bearing',txt); self.assertTrue(target.identified)

    def test_12_bailout_high_altitude_starts_rescue(self):
        f=self.flight(); f.altitude_ft=1800; c=FlightCombatState(); configure_sortie(c,f,'CAP',0,0,90)
        ok,msg=emergency_abandon(c,f); self.assertTrue(ok); self.assertIn('BAILOUT',msg); self.assertFalse(f.active); self.assertTrue(c.rescue_pending)

    def test_13_ditch_low_altitude(self):
        f=self.flight(); f.altitude_ft=150; c=FlightCombatState(); configure_sortie(c,f,'CAP',0,0,90)
        ok,msg=emergency_abandon(c,f); self.assertTrue(ok); self.assertIn('DITCHING',msg); self.assertEqual(1,c.ditchings)

    def test_14_rescue_completes_after_beacon_time(self):
        f=self.flight(); c=FlightCombatState(rescue_pending=True)
        evt=None
        for _ in range(120): evt=advance_air_combat(c,f,.25,0,0) or evt
        self.assertTrue(c.pilot_safe); self.assertEqual(1,c.rescues); self.assertIn('RESCUE',evt)

    def test_15_combat_state_round_trip(self):
        f=self.flight(); c=FlightCombatState(); configure_sortie(c,f,'CAP',0,0,90); c.aerial_victories=2
        r=combat_from_dict(combat_to_dict(c)); self.assertEqual(2,r.aerial_victories); self.assertEqual(len(c.contacts),len(r.contacts))

    def test_16_flight_state_round_trip_preserves_damage_and_weapons(self):
        f=self.flight(); f.gun_ammo=111; f.airframe_health=63; f.emergency_state='TEST'
        r=flight_from_dict(flight_to_dict(f)); self.assertEqual(111,r.gun_ammo); self.assertEqual(63,r.airframe_health); self.assertEqual('TEST',r.emergency_state)

    def test_17_profile_persists_v18_stats_and_snapshot(self):
        p=CareerProfile(name='V18 Pilot',air_combat_sorties=3,aerial_victories=2,pilot_rescues=1,air_combat_best_score=91)
        p.flight_combat_snapshot=combat_to_dict(FlightCombatState(aerial_victories=2))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'career.json'; save_profile(p,path); q=load_profile(path)
        self.assertEqual(3,q.air_combat_sorties); self.assertEqual(2,q.flight_combat_snapshot['aerial_victories'])

if __name__=='__main__': unittest.main()
