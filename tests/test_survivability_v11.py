import tempfile
import unittest
from pathlib import Path

from warsim.survivability import (
    create_survivability, apply_impact, survivability_tick, cycle_compartment,
    fight_fire, start_dewatering, patch_breach, shore_structure,
    toggle_boundary_for_selected, treat_casualties, order_abandon_ship,
    muster_abandon_ship, operational_factors, survivability_to_dict,
    survivability_from_dict,
)
from warsim.naval_combat import create_naval_combat, start_training_raid, advance_naval_combat
from warsim.ship_physics import create_ship_physics
from warsim.walkship import create_shipboard_walk_state
from warsim.models import CareerProfile
from warsim.persistence import save_profile, load_profile


class SurvivabilityV11Tests(unittest.TestCase):
    def setUp(self):
        self.s = create_survivability()

    def test_bomb_hit_is_localized_and_creates_fire(self):
        msg = apply_impact(self.s, "DIVE_BOMB", 70, zone="HANGAR_MID")
        c = self.s.compartments["HANGAR_MID"]
        self.assertIn("HANGAR", msg.upper())
        self.assertLess(c.structural, 100)
        self.assertGreater(c.fire, 20)
        self.assertEqual(self.s.selected_compartment, "HANGAR_MID")

    def test_torpedo_hit_opens_breach_and_progressively_floods(self):
        apply_impact(self.s, "TORPEDO", 78, zone="STBD_VOID")
        c = self.s.compartments["STBD_VOID"]
        self.assertGreater(c.breach_area_m2, .5)
        before = c.flooding
        for _ in range(20): survivability_tick(self.s, .25)
        self.assertGreater(c.flooding, before)

    def test_watertight_boundary_reduces_flood_spread(self):
        c = self.s.compartments["STBD_MACH"]
        c.flooding = 80
        target = self.s.compartments["PORT_MACH"]
        # B15 connects the machinery spaces and starts open.
        for _ in range(30): survivability_tick(self.s, .25)
        open_spread = target.flooding
        self.s = create_survivability()
        self.s.compartments["STBD_MACH"].flooding = 80
        self.s.boundaries["B15"].open = False
        for _ in range(30): survivability_tick(self.s, .25)
        self.assertLess(self.s.compartments["PORT_MACH"].flooding, open_spread)

    def test_asymmetric_flooding_creates_list(self):
        self.s.compartments["STBD_VOID"].flooding = 95
        survivability_tick(self.s, .1)
        self.assertGreater(self.s.list_deg, 1.0)
        self.s = create_survivability()
        self.s.compartments["PORT_VOID"].flooding = 95
        survivability_tick(self.s, .1)
        self.assertLess(self.s.list_deg, -1.0)

    def test_fore_aft_flooding_creates_trim(self):
        self.s.compartments["FWD_MAG"].flooding = 85
        survivability_tick(self.s, .1)
        self.assertLess(self.s.trim_deg, -0.5)
        self.s.compartments["AFT_MAG"].flooding = 100
        survivability_tick(self.s, .1)
        self.assertGreater(self.s.trim_deg, -1.0)

    def test_fire_attack_extinguishes_over_time(self):
        c = self.s.compartments["HANGAR_MID"]
        c.fire = 65; c.smoke = 45
        self.s.selected_compartment = c.key
        ok, _ = fight_fire(self.s)
        self.assertTrue(ok)
        for _ in range(100): survivability_tick(self.s, .25)
        self.assertLess(c.fire, 10)

    def test_patch_and_dewater_can_control_flooding(self):
        apply_impact(self.s, "TORPEDO", 65, zone="PORT_VOID")
        self.s.selected_compartment = "PORT_VOID"
        # Ensure fire does not block patching.
        self.s.compartments["PORT_VOID"].fire = 0
        ok, _ = patch_breach(self.s); self.assertTrue(ok)
        ok, _ = start_dewatering(self.s); self.assertTrue(ok)
        before = self.s.compartments["PORT_VOID"].flooding
        for _ in range(100): survivability_tick(self.s, .25)
        self.assertLess(self.s.compartments["PORT_VOID"].flooding, before)

    def test_machinery_damage_degrades_propulsion(self):
        apply_impact(self.s, "SHELL", 92, zone="PORT_MACH")
        c=self.s.compartments["PORT_MACH"]; c.flooding=55; c.fire=45
        factors=operational_factors(self.s)
        self.assertLess(factors["propulsion"], 70)

    def test_steering_damage_degrades_steering(self):
        apply_impact(self.s, "SHELL", 90, zone="STEERING")
        self.s.compartments["STEERING"].flooding=50
        self.assertLess(operational_factors(self.s)["steering"], 70)

    def test_magazine_fire_drives_magazine_risk(self):
        apply_impact(self.s, "DIVE_BOMB", 95, zone="AFT_MAG")
        c=self.s.compartments["AFT_MAG"]; c.fire=95; c.temperature_c=220
        for _ in range(30): survivability_tick(self.s, .25)
        self.assertGreater(self.s.magazine_risk_pct, 50)

    def test_medical_treatment_reduces_wounded(self):
        apply_impact(self.s, "DIVE_BOMB", 90, zone="HANGAR_MID")
        before=self.s.wounded_total
        ok,_=treat_casualties(self.s)
        self.assertTrue(ok)
        self.assertLess(sum(c.wounded for c in self.s.compartments.values()), before)

    def test_critical_flooding_can_enter_sinking_state(self):
        for key in ("PORT_VOID","STBD_VOID","PORT_MACH","STBD_MACH","FWD_MAG","AFT_MAG"):
            self.s.compartments[key].flooding=100
            self.s.compartments[key].structural=25
        for _ in range(10): survivability_tick(self.s, .25)
        self.assertTrue(self.s.sinking)
        self.assertLess(self.s.buoyancy_pct, 40)

    def test_abandon_ship_and_muster_progress(self):
        ok,msg=order_abandon_ship(self.s)
        self.assertTrue(ok); self.assertIn("ABANDON",msg)
        before=self.s.evacuation_progress_pct
        ok,_=muster_abandon_ship(self.s)
        self.assertTrue(ok); self.assertGreater(self.s.evacuation_progress_pct,before)

    def test_state_round_trip_preserves_active_casualty(self):
        apply_impact(self.s,"TORPEDO",80,zone="STBD_VOID")
        self.s.boundaries["B14"].open=False
        restored=survivability_from_dict(survivability_to_dict(self.s))
        self.assertGreater(restored.compartments["STBD_VOID"].breach_area_m2,0)
        self.assertFalse(restored.boundaries["B14"].open)

    def test_naval_combat_hit_feeds_structural_model(self):
        combat=create_naval_combat(); physics=create_ship_physics(); shipboard=create_shipboard_walk_state()
        start_training_raid(combat)
        t=next(iter(combat.tracks.values())); t.range_nm=.01; t.health=100
        before=sum(c.fire+c.flooding for c in self.s.compartments.values())
        msgs=advance_naval_combat(combat,physics,shipboard,.25,self.s)
        after=sum(c.fire+c.flooding for c in self.s.compartments.values())
        self.assertGreater(after,before)
        self.assertTrue(any("STRUCTURAL HIT" in m for m in msgs))

    def test_profile_survivability_fields_are_backward_compatible(self):
        p=CareerProfile(survivability_drills=2,survivability_best=84.0,
                        survivability_snapshot=survivability_to_dict(self.s))
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"career.json"; save_profile(p,path); loaded=load_profile(path)
        self.assertEqual(2,loaded.survivability_drills)
        self.assertIn("compartments",loaded.survivability_snapshot)
        old=CareerProfile.from_dict({"name":"Old v1.0 Save","xp":12})
        self.assertEqual({},old.survivability_snapshot)


if __name__ == "__main__":
    unittest.main()
