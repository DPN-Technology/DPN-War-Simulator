import unittest

from warsim.enterprise import (
    create_enterprise_duty_state,
    advance_enterprise,
    perform_station_action,
    open_tasks,
    station_efficiency,
    assign_crew,
    evaluate_enterprise,
    enterprise_summary,
    STATION_DEFS,
    ENTERPRISE_SOURCES,
)
from warsim.historical import hhmm_to_min
from warsim.models import CareerProfile
from warsim.systems import apply_enterprise_duty_result


class EnterpriseDutyTests(unittest.TestCase):
    def test_all_required_ship_stations_exist(self):
        s = create_enterprise_duty_state()
        self.assertEqual(set(s.stations), {"BRIDGE", "CIC", "RADIO", "ENGINEERING", "DAMAGE_CONTROL", "FIRE_CONTROL", "AIR_OPS"})
        self.assertEqual(set(s.stations), set(STATION_DEFS))

    def test_initial_watch_has_real_station_obligations(self):
        s = create_enterprise_duty_state()
        titles = {t.title for t in open_tasks(s)}
        self.assertIn("Set battle damage-control readiness", titles)
        self.assertIn("Open priority command circuits", titles)
        self.assertIn("Prepare flight deck for combat cycle", titles)
        self.assertIn("Bring plant to maneuvering readiness", titles)

    def test_scouting_report_creates_radio_and_cic_tasks(self):
        s = create_enterprise_duty_state()
        advance_enterprise(s, hhmm_to_min("05:34") - s.current_minute)
        actions = {t.action for t in open_tasks(s)}
        self.assertIn("ROUTE_SCOUT_REPORT", actions)
        self.assertIn("PLOT_CONTACT", actions)
        self.assertIn("pby_ship_sighting", s.historical.delivered_events)

    def test_station_action_completes_matching_task(self):
        s = create_enterprise_duty_state()
        task = next(t for t in open_tasks(s, "RADIO") if t.action == "OPEN_PRIORITY_NET")
        ok, _ = perform_station_action(s, "RADIO", "OPEN_PRIORITY_NET")
        self.assertTrue(ok)
        self.assertTrue(task.completed)
        self.assertGreater(s.score_points, 0)

    def test_flight_deck_must_be_prepared_before_launch(self):
        s = create_enterprise_duty_state()
        advance_enterprise(s, hhmm_to_min("07:00") - s.current_minute)
        ok, msg = perform_station_action(s, "AIR_OPS", "LAUNCH_STRIKE")
        self.assertFalse(ok)
        self.assertIn("Prepare", msg)
        # Reset and follow the preparation requirement.
        s = create_enterprise_duty_state()
        perform_station_action(s, "AIR_OPS", "PREPARE_FLIGHT_DECK")
        advance_enterprise(s, hhmm_to_min("07:00") - s.current_minute)
        ok, _ = perform_station_action(s, "AIR_OPS", "LAUNCH_STRIKE")
        self.assertTrue(ok)
        self.assertTrue(s.strike_launched)

    def test_historical_lock_preserves_canonical_midway_event(self):
        s = create_enterprise_duty_state()
        # Ignore every initial duty task and still advance historical time.
        advance_enterprise(s, hhmm_to_min("10:31") - s.current_minute)
        self.assertIn("three_carriers_hit", s.historical.delivered_events)
        self.assertGreater(len([t for t in s.tasks.values() if t.failed]), 0)

    def test_crew_reassignment_changes_station_efficiency(self):
        s = create_enterprise_duty_state()
        before = station_efficiency(s, "RADIO")
        ok, _ = assign_crew(s, "RDM", "AIR_OPS")
        self.assertTrue(ok)
        after = station_efficiency(s, "RADIO")
        self.assertLess(after, before)
        self.assertEqual(after, 25.0)

    def test_optimal_station_watch_passes(self):
        s = create_enterprise_duty_state()
        # Complete initial tasks immediately.
        for task in list(open_tasks(s)):
            ok, _ = perform_station_action(s, task.station, task.action)
            self.assertTrue(ok)
        # Advance one minute at a time and perform every newly opened duty task.
        while not s.completed:
            advance_enterprise(s, 1)
            for task in list(open_tasks(s)):
                if task.opened_minute <= s.current_minute:
                    ok, msg = perform_station_action(s, task.station, task.action)
                    self.assertTrue(ok, msg)
        score = evaluate_enterprise(s)
        summary = enterprise_summary(s)
        self.assertGreaterEqual(score, 80.0)
        self.assertEqual(summary["tasks_missed"], 0)
        self.assertTrue(summary["strike_launched"])
        self.assertTrue(summary["recovery_ready"])

    def test_enterprise_result_updates_backward_compatible_career(self):
        p = CareerProfile(name="Carrier Sailor")
        apply_enterprise_duty_result(p, 91.0, {"station_readiness": 92, "intel_discipline": 94})
        self.assertEqual(p.enterprise_duty_runs, 1)
        self.assertEqual(p.enterprise_duty_best, 91.0)
        self.assertTrue(p.qualifications["USS Enterprise Midway Duty Watch"])
        self.assertTrue(p.qualifications["Carrier Combat Watch Supervisor"])

    def test_enterprise_source_registry_includes_action_report(self):
        self.assertIn("enterprise_action_report", ENTERPRISE_SOURCES)
        self.assertIn("Naval History and Heritage Command", ENTERPRISE_SOURCES["enterprise_action_report"]["organization"])


if __name__ == "__main__":
    unittest.main()
