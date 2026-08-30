import math
import unittest
import json
from pathlib import Path

from warsim.walkship import (
    create_shipboard_walk_state,
    move_player,
    nearby_equipment,
    interact,
    qualification_status,
    advance_shipboard,
    evaluate_shipboard,
    shipboard_summary,
    raycast,
    DECK_MAPS,
    QUALIFICATION_REQUIREMENTS,
)
from warsim.enterprise import open_tasks, perform_station_action
from warsim.models import CareerProfile
from warsim.systems import apply_shipboard_walk_result


class ShipboardWalkTests(unittest.TestCase):
    def test_all_deck_maps_have_consistent_dimensions(self):
        for deck, grid in DECK_MAPS.items():
            self.assertGreaterEqual(len(grid), 10, deck)
            width = len(grid[0])
            self.assertTrue(all(len(row) == width for row in grid), deck)

    def test_collision_blocks_bulkhead(self):
        s = create_shipboard_walk_state()
        s.deck = "ISLAND"
        s.x, s.y, s.angle = 1.15, 2.0, math.pi
        before = s.x
        move_player(s, forward=1)
        self.assertGreaterEqual(s.x, 1.0)
        self.assertAlmostEqual(s.x, before, places=2)

    def test_bridge_equipment_interaction_records_practical_step(self):
        s = create_shipboard_walk_state()
        s.deck = "ISLAND"
        s.x, s.y = 4.0, 2.8
        self.assertEqual(nearby_equipment(s).key, "HELM")
        ok, _ = interact(s)
        self.assertTrue(ok)
        done, total, complete = qualification_status(s, "BRIDGE")
        self.assertEqual(done, 1)
        self.assertEqual(total, len(QUALIFICATION_REQUIREMENTS["BRIDGE"]))
        self.assertFalse(complete)

    def test_bridge_practical_can_be_completed_by_moving_to_equipment(self):
        s = create_shipboard_walk_state()
        for x, y in [(4.0, 2.8), (9.5, 2.8), (6.5, 4.8)]:
            s.deck, s.x, s.y = "ISLAND", x, y
            ok, msg = interact(s)
            self.assertTrue(ok, msg)
        done, total, complete = qualification_status(s, "BRIDGE")
        self.assertEqual(done, total)
        self.assertTrue(complete)
        self.assertIn("BRIDGE", s.qualified_this_run)

    def test_island_ladder_changes_deck(self):
        s = create_shipboard_walk_state()
        s.deck, s.x, s.y = "ISLAND", 15.5, 14.8
        ok, _ = interact(s)
        self.assertTrue(ok)
        self.assertEqual(s.deck, "FLIGHT")

    def test_radio_console_completes_initial_priority_net_task(self):
        s = create_shipboard_walk_state()
        task = next(t for t in open_tasks(s.enterprise, "RADIO") if t.action == "OPEN_PRIORITY_NET")
        s.deck, s.x, s.y = "ISLAND", 5.0, 10.0
        ok, msg = interact(s)
        self.assertTrue(ok, msg)
        self.assertTrue(task.completed)

    def test_aircraft_can_be_fueled_armed_and_spotted(self):
        s = create_shipboard_walk_state()
        # Fuel the first available package.
        s.deck, s.x, s.y = "HANGAR", 5.0, 3.0
        ok, msg = interact(s)
        self.assertTrue(ok, msg)
        # Arm it.
        s.x, s.y = 5.0, 14.5
        ok, msg = interact(s)
        self.assertTrue(ok, msg)
        # Move it via an available elevator.
        s.x, s.y = 16.0, 8.5
        ok, msg = interact(s)
        self.assertTrue(ok, msg)
        prepared = [a for a in s.aircraft.values() if a.fueled and a.armed and a.spotted and a.deck == "FLIGHT"]
        self.assertGreaterEqual(len(prepared), 1)

    def test_watch_rotation_changes_at_0800(self):
        s = create_shipboard_walk_state()
        self.assertEqual(s.watch_period, "0400-0800")
        advance_shipboard(s, 160)  # 05:20 -> 08:00
        self.assertEqual(s.watch_period, "0800-1200")
        self.assertGreaterEqual(s.watch_turnovers, 1)

    def test_raycast_returns_positive_depths(self):
        s = create_shipboard_walk_state()
        rays = raycast(s, rays=64)
        self.assertEqual(len(rays), 64)
        self.assertTrue(all(d > 0 for d, _ in rays))

    def test_old_career_dict_loads_without_v05_fields(self):
        old = {"name": "Legacy", "branch": "Navy", "era": "World War II", "enterprise_duty_runs": 2}
        p = CareerProfile.from_dict(old)
        self.assertEqual(p.shipboard_walk_runs, 0)
        self.assertEqual(p.station_qualifications, {})

    def test_shipboard_result_persists_station_qualifications(self):
        p = CareerProfile(name="Walkthrough Sailor")
        apply_shipboard_walk_result(p, 91.0, {"station_readiness": 90, "intel_discipline": 94}, ["BRIDGE", "CIC", "RADIO", "AIR_OPS", "ENGINEERING"])
        self.assertEqual(p.shipboard_walk_runs, 1)
        self.assertEqual(p.shipboard_walk_best, 91.0)
        self.assertTrue(p.station_qualifications["BRIDGE"])
        self.assertTrue(p.qualifications["USS Enterprise Shipboard Duty"])
        self.assertTrue(p.qualifications["Carrier Multi-Station Watchstander"])



    def test_strong_full_walkthrough_can_pass(self):
        s = create_shipboard_walk_state()
        # Complete every station practical through physical interaction nodes.
        positions = [
            ("ISLAND",4.0,2.8),("ISLAND",9.5,2.8),("ISLAND",6.5,4.8),
            ("ISLAND",20.0,2.8),("ISLAND",27.0,2.8),
            ("ISLAND",5.0,10.0),("ISLAND",10.5,14.0),
            ("ISLAND",22.0,10.0),("ISLAND",28.0,14.0),
            ("ENGINEERING",6.0,3.0),("ENGINEERING",12.0,4.5),
            ("ENGINEERING",21.0,3.0),("ENGINEERING",27.0,4.5),("ENGINEERING",23.0,13.0),
            ("FLIGHT",24.2,7.2),("FLIGHT",6.0,6.0),("FLIGHT",18.0,4.0),
            ("HANGAR",5.0,3.0),("HANGAR",5.0,14.5),("HANGAR",16.0,8.5),
        ]
        for deck, x, y in positions:
            s.deck, s.x, s.y = deck, x, y
            ok, msg = interact(s)
            self.assertTrue(ok, msg)
        self.assertEqual(len(s.qualified_this_run), len(QUALIFICATION_REQUIREMENTS))
        # Run the full historical duty clock and immediately perform newly opened obligations.
        for task in list(open_tasks(s.enterprise)):
            ok, msg = perform_station_action(s.enterprise, task.station, task.action)
            self.assertTrue(ok, msg)
        while not s.enterprise.completed:
            advance_shipboard(s, 1)
            for task in list(open_tasks(s.enterprise)):
                if task.opened_minute <= s.enterprise.current_minute:
                    ok, msg = perform_station_action(s.enterprise, task.station, task.action)
                    self.assertTrue(ok, msg)
        score = evaluate_shipboard(s)
        self.assertGreaterEqual(score, 80.0)
        self.assertGreaterEqual(s.watch_turnovers, 3)

    def test_walkthrough_manifest_labels_geometry_as_training_schematic(self):
        path = Path(__file__).resolve().parents[1] / "historical_data" / "enterprise_cv6_walkthrough_v05.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["build"], "0.5.0")
        self.assertEqual(data["geometry_policy"], "TRAINING_SCHEMATIC_NOT_EXACT_DECK_PLAN")
        self.assertIn("historical_lock", data)


if __name__ == "__main__":
    unittest.main()


class ShipboardV06IntegrationTests(unittest.TestCase):
    def test_closed_hatch_blocks_dynamic_collision(self):
        from warsim.walkship import HATCHES, tile_walkable
        s = create_shipboard_walk_state()
        h = HATCHES["ISLAND_PORT"]
        self.assertTrue(tile_walkable(h.deck, h.x, h.y, s))
        s.hatches[h.key] = False
        self.assertFalse(tile_walkable(h.deck, h.x, h.y, s))

    def test_hatch_can_be_operated_locally(self):
        from warsim.walkship import HATCHES
        s = create_shipboard_walk_state()
        h = HATCHES["ISLAND_PORT"]
        s.deck, s.x, s.y = h.deck, h.x, h.y - 0.3
        ok, msg = interact(s)
        self.assertTrue(ok, msg)
        self.assertFalse(s.hatches[h.key])

    def test_initial_objective_routes_player_to_priority_radio(self):
        from warsim.walkship import active_objective, objective_navigation
        s = create_shipboard_walk_state()
        obj = active_objective(s)
        self.assertIsNotNone(obj)
        self.assertEqual(obj["node"], "RADIO_RACK")
        self.assertIn("OBJECTIVE", objective_navigation(s))

    def test_alarm_reports_action_stations_with_open_tasks(self):
        from warsim.walkship import ship_alarm_state
        s = create_shipboard_walk_state()
        self.assertEqual(ship_alarm_state(s), "ACTION STATIONS")

    def test_training_fault_injects_without_claiming_historical_damage(self):
        s = create_shipboard_walk_state()
        advance_shipboard(s, 165)  # 05:20 -> 08:05
        rt = s.equipment_runtime["RADIO_LOG"]
        self.assertTrue(rt.fault.startswith("SIMULATED"))
        self.assertTrue(any("TRAINING INJECT" in line for line in s.action_log))

    def test_training_fault_can_be_restored_by_physical_interaction(self):
        s = create_shipboard_walk_state()
        advance_shipboard(s, 165)
        s.deck, s.x, s.y = "ISLAND", 10.5, 14.0
        ok, msg = interact(s)
        self.assertTrue(ok, msg)
        self.assertEqual(s.equipment_runtime["RADIO_LOG"].fault, "")
        self.assertEqual(s.training_faults_resolved, 1)

    def test_watchstanders_have_live_avatars_and_move(self):
        from warsim.walkship import update_crew_movement
        s = create_shipboard_walk_state()
        self.assertEqual(len(s.crew_avatars), len(s.enterprise.crew))
        before = {k: (v.x, v.y) for k, v in s.crew_avatars.items()}
        update_crew_movement(s, 0.8)
        self.assertTrue(any((v.x, v.y) != before[k] for k, v in s.crew_avatars.items()))

    def test_summary_exposes_v06_operational_metrics(self):
        s = create_shipboard_walk_state()
        summary = shipboard_summary(s)
        for key in ("training_faults_resolved", "training_faults_open", "hatches_shut", "objective_completions", "alarm_state"):
            self.assertIn(key, summary)

    def test_v06_manifest_separates_training_injects_from_history(self):
        path = Path(__file__).resolve().parents[1] / "historical_data" / "enterprise_cv6_walkthrough_v06.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["build"], "0.6.0")
        self.assertEqual(data["geometry_policy"], "TRAINING_SCHEMATIC_NOT_EXACT_DECK_PLAN")
        self.assertEqual(data["training_fault_policy"], "SIMULATED_INJECTS_NOT_HISTORICAL_CASUALTIES")
