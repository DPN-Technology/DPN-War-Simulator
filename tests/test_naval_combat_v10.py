import tempfile
import unittest
from pathlib import Path

from warsim.naval_combat import (
    create_naval_combat, start_training_raid, set_general_quarters,
    acquire_selected_track, calculate_solution, fire_selected_battery,
    select_battery, service_ammunition, advance_naval_combat, launch_cap,
    recover_cap, launch_training_strike, combat_score, combat_to_dict,
    combat_from_dict,
)
from warsim.ship_physics import create_ship_physics, cast_off
from warsim.walkship import create_shipboard_walk_state
from warsim.models import CareerProfile
from warsim.persistence import save_profile, load_profile


class NavalCombatV10Tests(unittest.TestCase):
    def setUp(self):
        self.combat = create_naval_combat()
        self.physics = create_ship_physics()
        self.shipboard = create_shipboard_walk_state()

    def test_training_raid_is_explicit_and_spawns_contacts(self):
        ok, msg = start_training_raid(self.combat)
        self.assertTrue(ok)
        self.assertIn("SIMULATED", msg)
        self.assertEqual(3, len(self.combat.tracks))
        self.assertTrue(self.combat.training_mode)

    def test_weapons_require_general_quarters_and_solution(self):
        start_training_raid(self.combat)
        t = next(iter(self.combat.tracks.values()))
        t.range_nm = 7.0
        ok, msg = fire_selected_battery(self.combat, self.physics)
        self.assertFalse(ok)
        self.assertIn("General Quarters", msg)
        set_general_quarters(self.combat, True)
        ok, msg = fire_selected_battery(self.combat, self.physics)
        self.assertFalse(ok)
        self.assertIn("solution", msg.lower())

    def test_track_acquisition_and_solution_improve_fire_control(self):
        start_training_raid(self.combat)
        t = next(iter(self.combat.tracks.values()))
        t.range_nm = 8.0
        before = t.confidence
        acquire_selected_track(self.combat)
        self.assertGreater(t.confidence, before)
        set_general_quarters(self.combat, True)
        ok, _ = calculate_solution(self.combat, self.physics)
        self.assertTrue(ok)
        self.assertGreater(self.combat.solution_quality, 25)

    def test_firing_consumes_ammo_and_damages_target(self):
        start_training_raid(self.combat)
        set_general_quarters(self.combat, True)
        t = next(iter(self.combat.tracks.values()))
        t.range_nm = 6.0
        acquire_selected_track(self.combat)
        calculate_solution(self.combat, self.physics)
        b = self.combat.batteries["FIVE_INCH"]
        ammo, health = b.ammo, t.health
        ok, _ = fire_selected_battery(self.combat, self.physics)
        self.assertTrue(ok)
        self.assertLess(b.ammo, ammo)
        self.assertLess(t.health, health)

    def test_weapon_batteries_have_different_engagement_ranges(self):
        start_training_raid(self.combat)
        set_general_quarters(self.combat, True)
        t = next(iter(self.combat.tracks.values()))
        t.range_nm = 3.5
        acquire_selected_track(self.combat); calculate_solution(self.combat, self.physics)
        select_battery(self.combat, "LIGHT_AA")
        ok, msg = fire_selected_battery(self.combat, self.physics)
        self.assertFalse(ok)
        self.assertIn("range", msg.lower())
        select_battery(self.combat, "MEDIUM_AA")
        calculate_solution(self.combat, self.physics)
        ok, _ = fire_selected_battery(self.combat, self.physics)
        self.assertTrue(ok)

    def test_ammunition_hoist_replenishes_ready_service(self):
        set_general_quarters(self.combat, True)
        b = self.combat.batteries["FIVE_INCH"]
        b.ammo = 20
        reserve = b.reserve_ammo
        ok, _ = service_ammunition(self.combat)
        self.assertTrue(ok)
        self.assertGreater(b.ammo, 20)
        self.assertLess(b.reserve_ammo, reserve)

    def test_cap_requires_prepared_fighter_and_consumes_stores(self):
        ac = self.shipboard.aircraft["F4F_CAP"]
        ac.deck = "FLIGHT"; ac.fueled = True; ac.armed = True; ac.spotted = True
        fuel = self.combat.air.aviation_fuel_units
        ok, _ = launch_cap(self.combat, self.shipboard)
        self.assertTrue(ok)
        self.assertTrue(self.combat.air.cap_airborne)
        self.assertTrue(ac.launched)
        self.assertLess(self.combat.air.aviation_fuel_units, fuel)
        self.combat.raid_active = False
        ok, _ = recover_cap(self.combat, self.shipboard)
        self.assertTrue(ok)
        self.assertFalse(ac.launched)
        self.assertFalse(ac.fueled)

    def test_cap_intercepts_simulated_air_track(self):
        ac = self.shipboard.aircraft["F4F_CAP"]
        ac.deck = "FLIGHT"; ac.fueled = True; ac.armed = True; ac.spotted = True
        launch_cap(self.combat, self.shipboard)
        start_training_raid(self.combat)
        target = next(iter(self.combat.tracks.values()))
        target.range_nm = 5.0
        hp = target.health
        for _ in range(40):
            advance_naval_combat(self.combat, self.physics, self.shipboard, .25)
        self.assertLess(target.health, hp)

    def test_training_strike_consumes_physical_aircraft_and_ordnance(self):
        ac = self.shipboard.aircraft["SBD_STRIKE_A"]
        ac.deck = "FLIGHT"; ac.fueled = True; ac.armed = True; ac.spotted = True
        bombs = self.combat.air.bomb_units
        ok, _ = launch_training_strike(self.combat, self.shipboard)
        self.assertTrue(ok)
        self.assertTrue(ac.launched)
        self.assertLess(self.combat.air.bomb_units, bombs)

    def test_incoming_training_attack_causes_physical_damage(self):
        start_training_raid(self.combat)
        t = next(iter(self.combat.tracks.values()))
        t.range_nm = 0.05
        hull = self.physics.hull_integrity
        messages = advance_naval_combat(self.combat, self.physics, self.shipboard, .25)
        self.assertLess(self.physics.hull_integrity, hull)
        self.assertGreater(self.combat.hits_taken, 0)
        self.assertTrue(any("SIMULATED HIT" in m for m in messages))
        self.assertTrue(any(rt.fault == "SIMULATED COMBAT DAMAGE" for rt in self.shipboard.equipment_runtime.values()))

    def test_combat_state_round_trips_active_raid(self):
        start_training_raid(self.combat)
        set_general_quarters(self.combat, True)
        self.combat.batteries["FIVE_INCH"].ammo = 77
        data = combat_to_dict(self.combat)
        restored = combat_from_dict(data)
        self.assertTrue(restored.raid_active)
        self.assertTrue(restored.general_quarters)
        self.assertEqual(77, restored.batteries["FIVE_INCH"].ammo)
        self.assertEqual(len(self.combat.tracks), len(restored.tracks))

    def test_new_combat_profile_fields_are_backward_compatible(self):
        p = CareerProfile(combat_training_runs=3, combat_training_best=88.0,
                          combat_enemy_destroyed=7, carrier_sorties=4,
                          combat_snapshot={"raid_active": False})
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "career.json"
            save_profile(p, path)
            loaded = load_profile(path)
        self.assertEqual(3, loaded.combat_training_runs)
        self.assertEqual(7, loaded.combat_enemy_destroyed)
        self.assertEqual(4, loaded.carrier_sorties)
        # Old dictionaries still work because from_dict filters/defaults missing v1.0 fields.
        old = CareerProfile.from_dict({"name": "Old Save", "xp": 10})
        self.assertEqual(0, old.combat_training_runs)
        self.assertEqual({}, old.combat_snapshot)

    def test_full_defensive_problem_can_be_won_without_ship_hit(self):
        start_training_raid(self.combat)
        set_general_quarters(self.combat, True)
        # Put the raid in the engagement envelope and prosecute each track professionally.
        for t in self.combat.tracks.values():
            t.range_nm = 5.5
            t.confidence = 80
            t.identified = True
        for key in list(self.combat.tracks):
            self.combat.selected_track = key
            while not self.combat.tracks[key].destroyed:
                acquire_selected_track(self.combat)
                calculate_solution(self.combat, self.physics)
                select_battery(self.combat, "FIVE_INCH")
                ok, _ = fire_selected_battery(self.combat, self.physics)
                self.assertTrue(ok)
                for _ in range(12):
                    advance_naval_combat(self.combat, self.physics, self.shipboard, .25)
        # One update closes the raid after all contacts are defeated.
        advance_naval_combat(self.combat, self.physics, self.shipboard, .25)
        self.assertFalse(self.combat.raid_active)
        self.assertEqual(0, self.combat.hits_taken)
        self.assertGreaterEqual(self.combat.enemy_destroyed, 3)
        self.assertGreater(combat_score(self.combat), 70)

    def test_new_raid_resets_per_raid_combat_statistics(self):
        start_training_raid(self.combat)
        self.combat.enemy_destroyed = 3
        self.combat.hits_taken = 2
        self.combat.rounds_fired = 88
        self.combat.raid_active = False
        ok, _ = start_training_raid(self.combat)
        self.assertTrue(ok)
        self.assertEqual(0, self.combat.enemy_destroyed)
        self.assertEqual(0, self.combat.hits_taken)
        self.assertEqual(0, self.combat.rounds_fired)

    def test_carrier_air_launch_requires_wind_over_deck(self):
        ac = self.shipboard.aircraft["F4F_CAP"]
        ac.deck = "FLIGHT"; ac.fueled = True; ac.armed = True; ac.spotted = True
        self.shipboard.enterprise.wind_over_deck = 3.0
        ok, msg = launch_cap(self.combat, self.shipboard)
        self.assertFalse(ok)
        self.assertIn("wind over deck", msg.lower())
        self.shipboard.enterprise.wind_over_deck = 15.0
        ok, _ = launch_cap(self.combat, self.shipboard)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()
