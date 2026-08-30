import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from warsim.flight_ops import (
    FlightState, enter_cockpit, exit_cockpit, toggle_engine, adjust_throttle,
    toggle_gear, toggle_flaps, advance_flight, attempt_recovery,
    flight_to_dict, flight_from_dict, cockpit_summary,
)
from warsim.models import CareerProfile
from warsim.persistence import save_profile, load_profile
from warsim.openworld import LAYERS, SHIP_ORIGIN_X, SHIP_ORIGIN_Y, layer_walkable
from warsim.seamless3d import SHIP_HATCH_WORLD, SeamlessOpenWorld3DApp


class FlightOpsV17Tests(unittest.TestCase):
    def aircraft(self,status="SPOTTED",deck="FLIGHT",condition=95):
        return SimpleNamespace(key="VF6-01",aircraft_type="F4F Wildcat",status=status,deck=deck,condition=condition,fuel_pct=100.0)

    def test_01_entry_requires_flight_deck_spotted_aircraft(self):
        s=FlightState(); ok,_=enter_cockpit(s,self.aircraft(status="AIRBORNE"),0,0,90)
        self.assertFalse(ok); self.assertFalse(s.active)
        ok,_=enter_cockpit(s,self.aircraft(),0,0,90)
        self.assertTrue(ok); self.assertTrue(s.active); self.assertTrue(s.on_deck)

    def test_02_engine_required_before_throttle(self):
        s=FlightState(); enter_cockpit(s,self.aircraft(),0,0,90)
        msg=adjust_throttle(s,.5); self.assertIn("Start",msg); self.assertEqual(0,s.throttle)
        toggle_engine(s); adjust_throttle(s,.5); self.assertAlmostEqual(.5,s.throttle)

    def test_03_brakes_prevent_takeoff(self):
        s=FlightState(); enter_cockpit(s,self.aircraft(),0,0,90); toggle_engine(s); s.throttle=1; s.brakes=True
        for _ in range(100): advance_flight(s,.05,0,0,90,15,18,3)
        self.assertTrue(s.on_deck); self.assertLessEqual(s.airspeed_knots,3)

    def test_04_carrier_takeoff_occurs_with_power_and_released_brakes(self):
        s=FlightState(); enter_cockpit(s,self.aircraft(),0,0,90); toggle_engine(s); s.throttle=1; s.brakes=False
        event=None
        for _ in range(120):
            event=advance_flight(s,.05,0,0,90,15,18,3) or event
            if not s.on_deck: break
        self.assertFalse(s.on_deck); self.assertEqual(1,s.takeoffs); self.assertIn("AIRBORNE",event)

    def test_05_airborne_aircraft_moves_in_global_sea_coordinates(self):
        s=FlightState(active=True,aircraft_key="VF6-01",aircraft_type="F4F",on_deck=False,engine_running=True,throttle=.8,heading_deg=90,airspeed_knots=100,altitude_ft=500)
        e0=s.east_nm
        for _ in range(50): advance_flight(s,.05,0,0,90,15,18,3)
        self.assertGreater(s.east_nm,e0); self.assertGreater(s.distance_nm,0)

    def test_06_fuel_burns_while_airborne(self):
        s=FlightState(active=True,on_deck=False,engine_running=True,throttle=1,airspeed_knots=120,altitude_ft=1000,fuel_pct=50)
        for _ in range(100): advance_flight(s,.05,0,0,90,15,18,3)
        self.assertLess(s.fuel_pct,50)

    def test_07_gear_and_flaps_toggle(self):
        s=FlightState(active=True,on_deck=False)
        self.assertIn("UP",toggle_gear(s)); self.assertFalse(s.gear_down)
        self.assertIn("DOWN",toggle_flaps(s)); self.assertTrue(s.flaps_down)

    def test_08_recovery_rejects_bad_configuration(self):
        s=FlightState(active=True,on_deck=False,east_nm=0,north_nm=0,altitude_ft=80,airspeed_knots=70,heading_deg=90,gear_down=False,flaps_down=False)
        ok,msg=attempt_recovery(s,0,0,90,18,True)
        self.assertFalse(ok); self.assertIn("gear",msg.lower())

    def test_09_successful_carrier_recovery(self):
        s=FlightState(active=True,on_deck=False,east_nm=.05,north_nm=0,altitude_ft=80,airspeed_knots=72,heading_deg=90,gear_down=True,flaps_down=True)
        ok,msg=attempt_recovery(s,0,0,90,18,True)
        self.assertTrue(ok); self.assertTrue(s.on_deck); self.assertEqual(1,s.landings); self.assertIn("RECOVERED",msg)

    def test_10_exit_requires_stopped_on_deck(self):
        s=FlightState(active=True,on_deck=False,airspeed_knots=70)
        self.assertFalse(exit_cockpit(s)[0])
        s.on_deck=True; s.airspeed_knots=0
        self.assertTrue(exit_cockpit(s)[0]); self.assertFalse(s.active)

    def test_11_flight_state_round_trip(self):
        s=FlightState(active=True,aircraft_key="VS6-02",altitude_ft=1200,bank_deg=12,fuel_pct=76,landings=2)
        r=flight_from_dict(flight_to_dict(s))
        self.assertEqual("VS6-02",r.aircraft_key); self.assertEqual(2,r.landings); self.assertAlmostEqual(76,r.fuel_pct)

    def test_12_profile_save_preserves_flight_snapshot_and_stats(self):
        p=CareerProfile(name="V17 Pilot",cockpit_flights=2,carrier_takeoffs=3,carrier_landings=2,pilot_distance_nm=14.5)
        p.flight_ops_snapshot=flight_to_dict(FlightState(aircraft_key="VF6-03",fuel_pct=61))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"career.json"; save_profile(p,path); q=load_profile(path)
        self.assertEqual(3,q.carrier_takeoffs); self.assertEqual("VF6-03",q.flight_ops_snapshot["aircraft_key"])

    def test_13_all_v17_dynamic_doors_are_on_walkable_cells(self):
        self.assertGreaterEqual(len(SHIP_HATCH_WORLD),10)
        for key,(layer,lx,ly) in SHIP_HATCH_WORLD.items():
            self.assertTrue(layer_walkable(layer,SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly),key)

    def test_14_d_key_legacy_harness_without_flight_state_still_strafes(self):
        fake=SimpleNamespace(keys=set(),overlay=None)
        fake._interact=lambda:None; fake._set_message=lambda *a,**k:None
        SeamlessOpenWorld3DApp._key_down(fake,SimpleNamespace(keysym="d"))
        self.assertIn("d",fake.keys); self.assertIsNone(fake.overlay)

    def test_15_cockpit_summary_reports_core_instruments(self):
        s=FlightState(active=True,aircraft_key="VF6-01",airspeed_knots=88,altitude_ft=600,heading_deg=122,throttle=.7,fuel_pct=84)
        text=cockpit_summary(s,0,0)
        self.assertIn("IAS 88",text); self.assertIn("ALT 600",text); self.assertIn("FUEL 84%",text)


if __name__ == '__main__': unittest.main()
