import unittest

from warsim.historical import (
    create_midway_state, advance_historical, active_prompt, answer_decision,
    evaluate_historical, historical_summary, EVENTS, DECISIONS, ORDER_OF_BATTLE, hhmm_to_min,
)
from warsim.models import CareerProfile
from warsim.systems import apply_historical_result


class HistoricalScenarioTests(unittest.TestCase):
    def test_no_omniscient_carrier_contact_at_start(self):
        s = create_midway_state()
        self.assertNotIn("JP_CARRIERS", s.contacts)
        self.assertEqual(s.doctrine_groups["US"].known_enemy_confidence, 0.0)

    def test_sighting_and_reporting_delay_are_modeled(self):
        s = create_midway_state()
        advance_historical(s, hhmm_to_min("05:34") - s.current_minute)
        self.assertIn("JP_SURFACE", s.contacts)
        self.assertNotIn("JP_CARRIERS", s.contacts)
        first = next(m for m in s.messages if m["headline"].startswith("PBY reports"))
        self.assertEqual(first["occurrence_time"], "05:30")
        self.assertEqual(first["report_time"], "05:34")
        self.assertEqual(first["lag"], 4)

    def test_carrier_contact_appears_only_when_reported(self):
        s = create_midway_state()
        advance_historical(s, hhmm_to_min("05:51") - s.current_minute)
        self.assertNotIn("JP_CARRIERS", s.contacts)
        advance_historical(s, 1)
        self.assertIn("JP_CARRIERS", s.contacts)
        self.assertGreater(s.contacts["JP_CARRIERS"].uncertainty_nm, 0)
        self.assertLess(s.contacts["JP_CARRIERS"].confidence, 100)

    def test_decision_window_and_best_response(self):
        s = create_midway_state()
        advance_historical(s, hhmm_to_min("05:45") - s.current_minute)
        p = active_prompt(s)
        self.assertIsNotNone(p)
        self.assertEqual(p.key, "air_warning_response")
        before = s.command_readiness
        ok, _ = answer_decision(s, p.key, 0)
        self.assertTrue(ok)
        self.assertGreater(s.command_readiness, before)
        self.assertEqual(s.decisions[p.key]["points"], 20)

    def test_bad_decision_does_not_rewrite_canonical_events(self):
        s = create_midway_state()
        advance_historical(s, hhmm_to_min("05:45") - s.current_minute)
        answer_decision(s, "air_warning_response", 2)
        advance_historical(s, hhmm_to_min("10:31") - s.current_minute)
        delivered = set(s.delivered_events)
        self.assertIn("tf16_launch", delivered)
        self.assertIn("three_carriers_hit", delivered)
        self.assertEqual(next(e for e in EVENTS if e.key == "three_carriers_hit").occurrence_minute, hhmm_to_min("10:22"))

    def test_doctrine_ai_uses_imperfect_information(self):
        s = create_midway_state()
        advance_historical(s, hhmm_to_min("05:40") - s.current_minute)
        self.assertEqual(s.doctrine_groups["US"].known_enemy_confidence, 0.0)
        advance_historical(s, hhmm_to_min("06:06") - s.current_minute)
        self.assertGreater(s.doctrine_groups["US"].known_enemy_confidence, 0.0)
        self.assertLess(s.doctrine_groups["US"].known_enemy_confidence, 100.0)

    def test_optimal_watch_can_pass_strongly(self):
        s = create_midway_state()
        for p in DECISIONS:
            if s.current_minute < p.minute:
                advance_historical(s, p.minute - s.current_minute)
            ok, _ = answer_decision(s, p.key, 0)
            self.assertTrue(ok)
        advance_historical(s, s.end_minute - s.current_minute)
        score = evaluate_historical(s)
        self.assertTrue(s.completed)
        self.assertGreaterEqual(score, 90.0)
        summary = historical_summary(s)
        self.assertEqual(summary["optimal_decisions"], len(DECISIONS))

    def test_historical_result_updates_backward_compatible_career(self):
        p = CareerProfile(name="Historian")
        apply_historical_result(
            p, "midway_1942_ops_watch", "Battle of Midway — Historical Operations Watch", 91.0,
            {"intel_discipline": 94, "command_readiness": 90},
        )
        self.assertEqual(p.historical_runs, 1)
        self.assertEqual(p.historical_best, 91.0)
        self.assertEqual(p.historical_scenarios["midway_1942_ops_watch"], 91.0)
        self.assertTrue(p.qualifications["Historical Operations Watchstanding"])
        self.assertTrue(p.qualifications["Combat Information Plotting"])

    def test_order_of_battle_contains_primary_midway_carrier_forces(self):
        joined = "\n".join(
            [formation] + info["units"]
            for formation, info in []
        ) if False else "\n".join(
            formation + "\n" + "\n".join(info["units"])
            for formation, info in ORDER_OF_BATTLE.items()
        )
        for name in ("USS Enterprise", "USS Hornet", "USS Yorktown", "Akagi", "Kaga", "Soryu", "Hiryu"):
            self.assertIn(name, joined)

    def test_exported_manifest_matches_runtime_scenario_id(self):
        import json
        from pathlib import Path
        path = Path(__file__).resolve().parents[1] / "historical_data" / "midway_1942_manifest.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["scenario_id"], "midway_1942_ops_watch")
        self.assertFalse(payload["rules"]["canonical_events_mutable"])
        self.assertFalse(payload["rules"]["enemy_contacts_visible_before_report"])
        self.assertEqual(len(payload["events"]), len(EVENTS))


if __name__ == "__main__":
    unittest.main()
