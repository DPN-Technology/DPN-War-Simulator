import unittest
from warsim.ship import (
    create_training_ship, ship_tick, toggle_hatch, shortest_path,
    route_pump, assign_team, evaluate_ship_scenario,
)
from warsim.models import CareerProfile
from warsim.systems import apply_ship_systems_result


class ShipSystemsTests(unittest.TestCase):
    def test_training_ship_contains_gdd_compartments(self):
        s = create_training_ship()
        names = {c.name for c in s.compartments.values()}
        required = {
            "Bridge", "Combat Information Center", "Engine Room 1", "Engine Room 2",
            "Boiler Room 1", "Medical Bay", "Galley", "Sleeping Quarters",
            "Machinery Room", "Fire Control", "Steering Gear", "Ammunition Storage",
            "Damage Control Central", "Hangar", "Flight Deck", "Radio Room",
        }
        self.assertTrue(required.issubset(names))

    def test_closing_watertight_hatch_blocks_route(self):
        s = create_training_ship()
        # Repair team begins in DC. Shut both immediate exits from DC.
        for key in ("H11", "H15", "H18"):
            if s.hatches[key].open:
                toggle_hatch(s, key)
        self.assertIsNone(shortest_path(s, "DC", "ENGINE_2"))

    def test_active_pump_reduces_flooding(self):
        s = create_training_ship()
        before = s.compartments["MACHINERY"].flooding
        # Remove ingress so the test isolates pump effect.
        s.compartments["MACHINERY"].breach = 0
        route_pump(s, "PORTABLE_1", "MACHINERY")
        ship_tick(s, 1.0)
        self.assertLess(s.compartments["MACHINERY"].flooding, before)

    def test_fire_team_reduces_fire_after_arrival(self):
        s = create_training_ship()
        # Open route is present by default. Place team locally so no travel ambiguity.
        s.teams["REPAIR_1"].location = "ENGINE_2"
        assign_team(s, "REPAIR_1", "FIREFIGHT", "ENGINE_2")
        before = s.compartments["ENGINE_2"].fire
        ship_tick(s, 2.0)
        self.assertLess(s.compartments["ENGINE_2"].fire, before)

    def test_unsafe_early_end_is_penalized(self):
        s = create_training_ship()
        score = evaluate_ship_scenario(s)
        self.assertLess(score, 70)

    def test_ship_result_updates_backward_compatible_career(self):
        p = CareerProfile(name="Systems Tester")
        apply_ship_systems_result(p, 86.0, {"casualties": 2, "max_fire": 3, "max_flooding": 8})
        self.assertEqual(p.ship_systems_runs, 1)
        self.assertEqual(p.ship_systems_best, 86.0)
        self.assertTrue(p.qualifications["Ship Systems Familiarization"])
        self.assertTrue(p.qualifications["Shipboard Casualty Control"])

    def test_documented_casualty_is_winnable_with_coordinated_response(self):
        s = create_training_ship()
        assign_team(s, "REPAIR_1", "FIREFIGHT", "ENGINE_2")
        assign_team(s, "REPAIR_2", "SEAL", "MACHINERY")
        assign_team(s, "ELECTRICAL", "ELECTRICAL", "ENGINE_2")
        route_pump(s, "FIXED_1", "MACHINERY")
        route_pump(s, "PORTABLE_1", "MACHINERY")
        from warsim.ship import toggle_ventilation
        toggle_ventilation(s, "ENGINE_2")
        for second in range(120):
            ship_tick(s, 1.0)
            if second == 20:
                for hatch_key in ("H17", "H21", "H25", "H26"):
                    if s.hatches[hatch_key].open:
                        toggle_hatch(s, hatch_key)
            if s.resolved or s.failed:
                break
        self.assertTrue(s.resolved)
        self.assertFalse(s.failed)
        self.assertGreaterEqual(evaluate_ship_scenario(s), 70)


if __name__ == "__main__":
    unittest.main()
