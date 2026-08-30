import tempfile
import unittest
from pathlib import Path

from warsim.task_force import (
    create_task_force, advance_task_force, set_formation, cycle_friendly, cycle_contact,
    start_surface_training_problem, engage_selected_contact, begin_replenishment,
    task_force_to_dict, task_force_from_dict, toggle_radio_silence,
)
from warsim.ship_physics import create_ship_physics
from warsim.models import CareerProfile
from warsim.persistence import save_profile, load_profile
from warsim.openworld import all_static_interactions


class TaskForceV13Tests(unittest.TestCase):
    def setUp(self):
        self.physics = create_ship_physics()
        self.physics.moored = False
        self.physics.speed_knots = 18.0
        self.physics.heading_deg = 90.0
        self.tf = create_task_force(self.physics.east_nm, self.physics.north_nm, self.physics.heading_deg)

    def test_tf16_training_roster_contains_enterprise_escorts(self):
        self.assertIn("HORNET", self.tf.friendly)
        self.assertIn("ATLANTA", self.tf.friendly)
        self.assertIn("WORDEN", self.tf.friendly)
        self.assertGreaterEqual(len(self.tf.friendly), 10)

    def test_formation_order_changes_slots(self):
        before = self.tf.friendly["WORDEN"].desired_range_nm
        msg = set_formation(self.tf, "ASW SCREEN")
        self.assertIn("ASW SCREEN", msg)
        self.assertNotEqual(before, self.tf.friendly["WORDEN"].desired_range_nm)
        self.assertEqual("ASW SCREEN", self.tf.formation)

    def test_formation_ai_moves_ship_toward_station(self):
        v = self.tf.friendly["HORNET"]
        v.east_nm += 3.0
        before = ((v.east_nm-self.physics.east_nm)**2 + (v.north_nm-self.physics.north_nm)**2) ** 0.5
        for _ in range(120):
            advance_task_force(self.tf, self.physics, 1.0)
        after = ((v.east_nm-self.physics.east_nm)**2 + (v.north_nm-self.physics.north_nm)**2) ** 0.5
        self.assertLess(after, before)
        self.assertGreater(v.speed_knots, 0.0)

    def test_collision_avoidance_triggers_for_close_escort(self):
        v = self.tf.friendly["WORDEN"]
        v.east_nm = self.physics.east_nm + 0.05
        v.north_nm = self.physics.north_nm
        advance_task_force(self.tf, self.physics, 1.0)
        self.assertGreater(self.tf.collision_warnings, 0)

    def test_training_problem_has_surface_and_submarine_contacts(self):
        ok, msg = start_surface_training_problem(self.tf, 0, 0, 90)
        self.assertTrue(ok)
        self.assertTrue(self.tf.training_problem_active)
        self.assertTrue(any(c.contact_type == "SURFACE" for c in self.tf.contacts.values()))
        self.assertTrue(any(c.contact_type == "SUBMARINE" for c in self.tf.contacts.values()))
        self.assertIn("SIMULATED", msg)

    def test_fleet_sensors_can_detect_contacts(self):
        start_surface_training_problem(self.tf, 0, 0, 90)
        for _ in range(5):
            advance_task_force(self.tf, self.physics, 1.0)
        self.assertTrue(any(c.detected for c in self.tf.contacts.values()))

    def test_surface_escort_can_engage_detected_contact(self):
        start_surface_training_problem(self.tf, 0, 0, 90)
        for c in self.tf.contacts.values():
            c.detected = True; c.confidence = 90; c.identified = True
        # cycle until a surface contact is selected
        for _ in range(4):
            c = self.tf.selected_contact
            if c and c.contact_type == "SURFACE": break
            cycle_contact(self.tf)
        before = self.tf.selected_contact.health_pct
        ok, _ = engage_selected_contact(self.tf)
        self.assertTrue(ok)
        self.assertLess(self.tf.selected_contact.health_pct, before)

    def test_destroyer_can_attack_submarine(self):
        start_surface_training_problem(self.tf, 0, 0, 90)
        sub = next(c for c in self.tf.contacts.values() if c.contact_type == "SUBMARINE")
        sub.detected = True; sub.confidence = 95; sub.identified = True
        vals = [c for c in self.tf.contacts.values() if c.health_pct > 0]
        self.tf.selected_contact_index = vals.index(sub)
        before = sum(v.depth_charges for v in self.tf.friendly.values())
        ok, _ = engage_selected_contact(self.tf)
        self.assertTrue(ok)
        after = sum(v.depth_charges for v in self.tf.friendly.values())
        self.assertLess(after, before)
        self.assertLess(sub.health_pct, 100)

    def test_radio_silence_changes_signal_method(self):
        msg = toggle_radio_silence(self.tf)
        self.assertTrue(self.tf.radio_silence)
        self.assertIn("SIGNAL", self.tf.signal_method)
        self.assertIn("RADIO SILENCE", msg)

    def test_replenishment_completes_at_low_speed(self):
        v = self.tf.selected_friendly
        v.fuel_pct = 40
        ok, _ = begin_replenishment(self.tf)
        self.assertTrue(ok)
        self.physics.speed_knots = 10
        # Put receiver alongside so transfer can begin immediately.
        v.east_nm = self.physics.east_nm + 0.1
        v.north_nm = self.physics.north_nm
        for _ in range(30):
            advance_task_force(self.tf, self.physics, 1.0)
        self.assertFalse(self.tf.logistics.transfer_in_progress)
        self.assertGreater(v.fuel_pct, 40)
        self.assertGreaterEqual(self.tf.logistics.replenishments, 1)

    def test_replenishment_pauses_above_safe_training_speed(self):
        v = self.tf.selected_friendly
        begin_replenishment(self.tf)
        v.east_nm = self.physics.east_nm + 0.1
        v.north_nm = self.physics.north_nm
        self.physics.speed_knots = 20
        before = self.tf.logistics.transfer_progress
        advance_task_force(self.tf, self.physics, 2.0)
        self.assertEqual(before, self.tf.logistics.transfer_progress)

    def test_task_force_round_trip(self):
        set_formation(self.tf, "COLUMN")
        start_surface_training_problem(self.tf, 0, 0, 90)
        restored = task_force_from_dict(task_force_to_dict(self.tf), 0, 0, 90)
        self.assertEqual("COLUMN", restored.formation)
        self.assertEqual(set(self.tf.friendly), set(restored.friendly))
        self.assertEqual(set(self.tf.contacts), set(restored.contacts))

    def test_profile_task_force_fields_are_backward_compatible(self):
        p = CareerProfile(task_force_snapshot=task_force_to_dict(self.tf), fleet_orders_issued=2)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "career.json"
            save_profile(p, path)
            loaded = load_profile(path)
        self.assertEqual(2, loaded.fleet_orders_issued)
        self.assertIn("friendly", loaded.task_force_snapshot)
        old = CareerProfile.from_dict({"name":"Old v1.2 Save","xp":44})
        self.assertEqual({}, old.task_force_snapshot)
        self.assertEqual(0, old.fleet_signals_sent)

    def test_physical_task_force_stations_exist(self):
        actions = {p.action for p in all_static_interactions()}
        self.assertIn("fleet_console", actions)
        self.assertIn("fleet_signal", actions)
        self.assertIn("fleet_logistics", actions)

    def test_selected_ship_cycles(self):
        first = self.tf.selected_friendly.key
        second = cycle_friendly(self.tf).key
        self.assertNotEqual(first, second)

    def test_training_contact_penetration_can_damage_escort(self):
        start_surface_training_problem(self.tf, 0, 0, 90)
        c = next(c for c in self.tf.contacts.values() if c.contact_type == "SUBMARINE")
        c.east_nm = 0.1; c.north_nm = 0.0; c.detected = True
        before = sum(v.hull_pct for v in self.tf.friendly.values())
        for _ in range(9):
            advance_task_force(self.tf, self.physics, 1.0)
        after = sum(v.hull_pct for v in self.tf.friendly.values())
        self.assertLess(after, before)
        self.assertGreater(self.tf.escort_damage_events, 0)


if __name__ == "__main__":
    unittest.main()
