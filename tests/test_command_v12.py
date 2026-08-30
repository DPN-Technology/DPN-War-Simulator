import tempfile
import unittest
from pathlib import Path

from warsim.command import (
    create_command_state, authority_level, authority_label, issue_order,
    advance_command, route_living_crew, command_to_dict, command_from_dict,
)
from warsim.models import CareerProfile
from warsim.persistence import save_profile, load_profile
from warsim.naval_combat import create_naval_combat, start_training_raid
from warsim.survivability import create_survivability, apply_impact
from warsim.ship_physics import create_ship_physics
from warsim.living_world import create_living_world
from warsim.seamless3d import SHIP_EQUIPMENT_WORLD
from warsim.walkship import EQUIPMENT


class CommandV12Tests(unittest.TestCase):
    def setUp(self):
        self.cmd = create_command_state()
        self.combat = create_naval_combat()
        self.surv = create_survivability()
        self.physics = create_ship_physics()
        self.life = create_living_world(1942)

    def test_authority_grows_with_rank(self):
        self.assertEqual(0, authority_level(0))
        self.assertEqual(1, authority_level(4))
        self.assertEqual(2, authority_level(8))
        self.assertEqual(3, authority_level(9))
        self.assertEqual(4, authority_level(12))
        self.assertEqual(5, authority_level(14))
        self.assertIn("COMMAND", authority_label(14))

    def test_recruit_can_report_but_not_order_general_quarters(self):
        ok, msg = issue_order(self.cmd, 0, "REPORT", 320, "ENGINEERING")
        self.assertTrue(ok)
        ok, msg = issue_order(self.cmd, 0, "GQ", 320)
        self.assertFalse(ok)
        self.assertIn("DENIED", msg)

    def test_petty_officer_can_prioritize_team_repair(self):
        ok, _ = issue_order(self.cmd, 4, "REPAIR", 320, "DAMAGE_CONTROL")
        self.assertTrue(ok)
        self.assertTrue(any(o.department == "DAMAGE_CONTROL" for o in self.cmd.orders.values()))

    def test_junior_officer_can_set_general_quarters(self):
        ok, msg = issue_order(self.cmd, 9, "GQ", 320)
        self.assertTrue(ok)
        self.assertTrue(self.cmd.general_quarters)
        self.assertEqual("GENERAL QUARTERS", self.cmd.command_condition)
        self.assertGreaterEqual(len(self.cmd.orders), 8)
        self.assertIn("GENERAL QUARTERS", msg)

    def test_active_raid_automatically_sounds_general_quarters(self):
        start_training_raid(self.combat)
        msgs = advance_command(self.cmd, 1, self.combat, self.surv, self.physics, self.life)
        self.assertTrue(self.cmd.general_quarters)
        self.assertTrue(any("GENERAL QUARTERS" in m for m in msgs))
        self.assertTrue(any(o.auto_generated for o in self.cmd.orders.values()))

    def test_structural_casualty_dispatches_damage_control_and_medical(self):
        apply_impact(self.surv, "DIVE_BOMB", 92, zone="HANGAR_MID")
        advance_command(self.cmd, 1, self.combat, self.surv, self.physics, self.life)
        depts = {o.department for o in self.cmd.orders.values() if not o.completed}
        self.assertIn("DAMAGE_CONTROL", depts)
        if sum(c.wounded for c in self.surv.compartments.values()) > 0:
            self.assertIn("MEDICAL", depts)

    def test_autonomous_damage_control_reduces_active_fire(self):
        c = self.surv.compartments["HANGAR_MID"]
        c.fire = 75.0
        c.smoke = 55.0
        c.structural = 60.0
        before = c.fire
        for _ in range(12):
            advance_command(self.cmd, 1, self.combat, self.surv, self.physics, self.life)
        self.assertLess(c.fire, before)
        self.assertLess(self.cmd.supplies.fire_fighting_agent, 300.0)

    def test_autonomous_medical_treats_wounded(self):
        c = self.surv.compartments["HANGAR_MID"]
        c.wounded = 8
        before = c.wounded
        for _ in range(24):
            advance_command(self.cmd, 1, self.combat, self.surv, self.physics, self.life)
        self.assertLess(c.wounded, before)
        self.assertLess(self.cmd.supplies.medical_units, 260.0)

    def test_engineering_order_restores_maneuvering_integrity(self):
        self.physics.propulsion_integrity = 55.0
        self.physics.steering_integrity = 60.0
        before = self.physics.propulsion_integrity
        for _ in range(15):
            advance_command(self.cmd, 1, self.combat, self.surv, self.physics, self.life)
        self.assertGreater(self.physics.propulsion_integrity, before)
        self.assertLess(self.cmd.supplies.electrical_spares, 120.0)

    def test_ship_routine_consumes_provisions_and_water(self):
        food = self.cmd.supplies.provisions_units
        water = self.cmd.supplies.fresh_water_units
        advance_command(self.cmd, 30, self.combat, self.surv, self.physics, self.life)
        self.assertLess(self.cmd.supplies.provisions_units, food)
        self.assertLess(self.cmd.supplies.fresh_water_units, water)

    def test_watch_relief_occurs_on_four_hour_boundary(self):
        self.cmd._last_minute = 239
        before = self.cmd.watch_reliefs
        advance_command(self.cmd, 1, self.combat, self.surv, self.physics, self.life)
        self.assertGreater(self.cmd.watch_reliefs, before)

    def test_general_quarters_routes_visible_crew_to_battle_stations(self):
        issue_order(self.cmd, 9, "GQ", 320)
        route_living_crew(self.cmd, self.life)
        radio = self.life.crew["RAD"]
        self.assertEqual("BATTLE STATION", radio.duty)
        self.assertEqual((115.0, 17.0), (radio.target_x, radio.target_y))

    def test_order_can_fail_if_deadline_is_missed(self):
        issue_order(self.cmd, 4, "REPAIR", 100, "DAMAGE_CONTROL")
        self.cmd._last_minute = 200
        advance_command(self.cmd, 1, self.combat, self.surv, self.physics, self.life)
        self.assertTrue(any(o.failed for o in self.cmd.orders.values()))
        self.assertGreater(self.cmd.orders_failed, 0)

    def test_supply_order_replenishes_damage_control_stores(self):
        self.cmd.supplies.repair_material_units = 100
        self.cmd.supplies.medical_units = 100
        ok, _ = issue_order(self.cmd, 8, "SUPPLY", 320)
        self.assertTrue(ok)
        for _ in range(20):
            advance_command(self.cmd, 1, self.combat, self.surv, self.physics, self.life)
        self.assertGreater(self.cmd.supplies.repair_material_units, 100)
        self.assertGreater(self.cmd.supplies.medical_units, 100)

    def test_command_state_round_trip_preserves_orders_and_department_state(self):
        issue_order(self.cmd, 9, "GQ", 320)
        advance_command(self.cmd, 2, self.combat, self.surv, self.physics, self.life)
        restored = command_from_dict(command_to_dict(self.cmd))
        self.assertEqual(self.cmd.general_quarters, restored.general_quarters)
        self.assertEqual(set(self.cmd.orders), set(restored.orders))
        self.assertEqual(self.cmd.departments["CIC"].current_order, restored.departments["CIC"].current_order)

    def test_profile_command_fields_are_backward_compatible(self):
        p = CareerProfile(command_snapshot=command_to_dict(self.cmd), command_orders_issued=3)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "career.json"
            save_profile(p, path)
            loaded = load_profile(path)
        self.assertEqual(3, loaded.command_orders_issued)
        self.assertIn("departments", loaded.command_snapshot)
        old = CareerProfile.from_dict({"name": "Old v1.1 Save", "xp": 22})
        self.assertEqual({}, old.command_snapshot)
        self.assertEqual(0, old.command_orders_completed)

    def test_command_desk_exists_in_seamless_world(self):
        self.assertIn("COMMAND_DESK", SHIP_EQUIPMENT_WORLD)
        self.assertIn("COMMAND_DESK", EQUIPMENT)
        layer, x, y = SHIP_EQUIPMENT_WORLD["COMMAND_DESK"]
        self.assertEqual("BRIDGE", layer)
        self.assertGreater(x, 48)


if __name__ == "__main__":
    unittest.main()
