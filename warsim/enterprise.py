from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random

from .historical import (
    HistoricalScenarioState,
    create_midway_state,
    advance_historical,
    hhmm_to_min,
    min_to_hhmm,
    DECISIONS,
)


ENTERPRISE_SOURCES = {
    "enterprise_action_report": {
        "title": "USS Enterprise (CV-6) Action Report — Battle of Midway Island, June 4–6, 1942",
        "organization": "Naval History and Heritage Command",
        "url": "https://www.history.navy.mil/content/history/nhhc/research/archives/digital-exhibits-highlights/action-reports/wwii-battle-of-midway/uss-enterprise-action-report.html",
        "notes": (
            "Used for Enterprise-specific message traffic, ship operating context, attack-group composition, "
            "radar/lookout contact reporting, and the ship's role as TF 16 flagship. Times in the original report "
            "use its stated zone convention; this build does not silently replace the v0.3 canonical Midway clock with them."
        ),
    },
    "nhhc_enterprise": {
        "title": "USS Enterprise (CV-6)",
        "organization": "Naval History and Heritage Command",
        "url": "https://www.history.navy.mil/our-collections/photography/us-navy-ships/aircraft-carriers/uss-enterprise--cv-6-.html",
        "notes": "Used for ship identity, Yorktown-class context, displacement description, and Enterprise's Midway role.",
    },
    "nhhc_midway": {
        "title": "Battle of Midway",
        "organization": "Naval History and Heritage Command",
        "url": "https://www.history.navy.mil/browse-by-topic/wars-conflicts-and-operations/world-war-ii/1942/midway.html",
        "notes": (
            "Used for TF 16 context, the 4 June battle sequence, and Enterprise flight-deck imagery/caption data including "
            "VT-6 preparation and the fourteen TBDs launched from Enterprise."
        ),
    },
    "nhhc_strategic_analysis": {
        "title": "Battle of Midway: Strategic and Tactical Analysis",
        "organization": "Naval History and Heritage Command",
        "url": "https://www.history.navy.mil/content/dam/nhhc/browse-by-topic/War%20and%20Conflict/WWII/midway_strategic_and_tactical_analysis.pdf",
        "notes": (
            "Used for TF 16 operating context, launch-cycle analysis, and the documented change to course 240° true "
            "and 25 knots after launching operations."
        ),
    },
}


STATION_DEFS = {
    "BRIDGE": {
        "name": "Bridge",
        "short": "BRG",
        "mission": "Steer the carrier, maintain formation discipline, and provide safe wind-over-deck conditions for aviation.",
    },
    "CIC": {
        "name": "Combat Information Center",
        "short": "CIC",
        "mission": "Correlate radar, lookout, scouting, and command-net reports without creating false certainty.",
    },
    "RADIO": {
        "name": "Radio Central",
        "short": "RAD",
        "mission": "Receive, classify, route, acknowledge, and preserve critical operational traffic.",
    },
    "ENGINEERING": {
        "name": "Engineering",
        "short": "ENG",
        "mission": "Maintain propulsion, electrical generation, fuel discipline, and readiness for rapid maneuvering.",
    },
    "DAMAGE_CONTROL": {
        "name": "Damage Control Central",
        "short": "DC",
        "mission": "Set material readiness, stage repair parties, preserve watertight integrity, and prepare for casualties.",
    },
    "FIRE_CONTROL": {
        "name": "Fire Control / Air Defense",
        "short": "FC",
        "mission": "Maintain air-defense readiness, classify tracks, coordinate lookouts/radar, and avoid wasteful engagement decisions.",
    },
    "AIR_OPS": {
        "name": "Aviation Operations",
        "short": "AIR",
        "mission": "Coordinate spotting, fueling, arming, launch/recovery cycles, CAP reserve, and flight-deck safety.",
    },
}


@dataclass
class WatchCrew:
    key: str
    name: str
    rating: str
    proficiency: Dict[str, float]
    fatigue: float = 12.0
    stress: float = 8.0
    injured: bool = False


@dataclass
class StationTask:
    key: str
    station: str
    title: str
    detail: str
    opened_minute: int
    deadline_minute: int
    action: str
    points: int
    historical: bool = True
    completed: bool = False
    failed: bool = False
    completed_minute: Optional[int] = None
    result: str = ""

    @property
    def status(self) -> str:
        if self.completed:
            return "COMPLETE"
        if self.failed:
            return "MISSED"
        return "OPEN"


@dataclass
class StationState:
    key: str
    readiness: float = 82.0
    crew_keys: List[str] = field(default_factory=list)
    alert: str = "NORMAL"
    notes: List[str] = field(default_factory=list)


@dataclass
class EnterpriseDutyState:
    historical: HistoricalScenarioState = field(default_factory=create_midway_state)
    running: bool = False
    speed: int = 1
    completed: bool = False
    evaluated: bool = False
    selected_station: str = "CIC"
    crew: Dict[str, WatchCrew] = field(default_factory=dict)
    stations: Dict[str, StationState] = field(default_factory=dict)
    tasks: Dict[str, StationTask] = field(default_factory=dict)
    task_order: List[str] = field(default_factory=list)
    processed_history_events: List[str] = field(default_factory=list)
    messages_routed: List[str] = field(default_factory=list)
    action_log: List[str] = field(default_factory=list)
    score_points: int = 0
    score_possible: int = 0
    errors: int = 0
    bridge_heading: float = 215.0
    ordered_heading: float = 215.0
    speed_knots: float = 15.0
    ordered_speed: float = 15.0
    engine_order: str = "STANDARD"
    rudder: float = 0.0
    wind_over_deck: float = 12.0
    radar_air_readiness: float = 86.0
    aa_readiness: float = 82.0
    electrical_load: float = 68.0
    plant_readiness: float = 91.0
    fuel_state: float = 96.0
    watertight_integrity: float = 92.0
    repair_party_readiness: float = 78.0
    deck_spot: float = 55.0
    aircraft_fueled: float = 72.0
    aircraft_armed: float = 68.0
    cap_reserve: float = 84.0
    deck_safety: float = 94.0
    strike_launched: bool = False
    recovery_ready: bool = False
    latest_report_key: Optional[str] = None
    rng_seed: int = 6061942

    @property
    def current_minute(self) -> int:
        return self.historical.current_minute

    @property
    def clock(self) -> str:
        return min_to_hhmm(self.current_minute)


CREW_TEMPLATE = (
    ("BOSN", "CPO Harold Mercer", "Chief Boatswain's Mate"),
    ("QM", "QM1 Samuel Ortiz", "Quartermaster First Class"),
    ("RDM", "RM1 Charles Avery", "Radioman First Class"),
    ("RDR", "RdM1 Walter Hayes", "Radar Operator"),
    ("ENG", "CWT Michael Doyle", "Chief Water Tender"),
    ("EM", "EM1 Frank Vance", "Electrician's Mate First Class"),
    ("DC", "CMM Robert Hale", "Chief Machinist's Mate"),
    ("GUN", "GM1 Thomas Reed", "Gunner's Mate First Class"),
    ("AIR", "ACM1 James Cole", "Aviation Chief Machinist's Mate"),
    ("DECK", "AB1 William Grant", "Aviation Boatswain's Mate"),
    ("PLOT", "Y2 Edward Pierce", "Operations Plot Yeoman"),
    ("MED", "PhM1 Joseph Flynn", "Pharmacist's Mate First Class"),
)


def _build_crew(seed: int) -> Dict[str, WatchCrew]:
    rng = random.Random(seed)
    crew: Dict[str, WatchCrew] = {}
    stations = list(STATION_DEFS)
    for key, name, rating in CREW_TEMPLATE:
        proficiency = {s: round(rng.uniform(42.0, 68.0), 1) for s in stations}
        specialty = {
            "BOSN": "BRIDGE", "QM": "BRIDGE", "RDM": "RADIO", "RDR": "CIC",
            "ENG": "ENGINEERING", "EM": "ENGINEERING", "DC": "DAMAGE_CONTROL",
            "GUN": "FIRE_CONTROL", "AIR": "AIR_OPS", "DECK": "AIR_OPS",
            "PLOT": "CIC", "MED": "DAMAGE_CONTROL",
        }[key]
        proficiency[specialty] = round(rng.uniform(78.0, 95.0), 1)
        crew[key] = WatchCrew(key, name, rating, proficiency, fatigue=round(rng.uniform(7, 18), 1), stress=round(rng.uniform(4, 13), 1))
    return crew


def _default_station_assignments() -> Dict[str, List[str]]:
    return {
        "BRIDGE": ["BOSN", "QM"],
        "CIC": ["RDR", "PLOT"],
        "RADIO": ["RDM"],
        "ENGINEERING": ["ENG", "EM"],
        "DAMAGE_CONTROL": ["DC", "MED"],
        "FIRE_CONTROL": ["GUN"],
        "AIR_OPS": ["AIR", "DECK"],
    }


def create_enterprise_duty_state() -> EnterpriseDutyState:
    state = EnterpriseDutyState()
    state.crew = _build_crew(state.rng_seed)
    assignments = _default_station_assignments()
    state.stations = {k: StationState(k, crew_keys=list(assignments[k])) for k in STATION_DEFS}
    state.action_log.append("05:20 — Enterprise duty watch assumed. Historical lock active; shipboard performance is evaluated around canonical Midway events.")
    _add_task(state, StationTask(
        "prebattle_dc", "DAMAGE_CONTROL", "Set battle damage-control readiness",
        "Stage repair parties, verify watertight boundaries, and place Damage Control Central at battle readiness before the air action intensifies.",
        hhmm_to_min("05:20"), hhmm_to_min("05:50"), "SET_DC_READY", 12,
    ))
    _add_task(state, StationTask(
        "prebattle_radio", "RADIO", "Open priority command circuits",
        "Establish the priority routing watch so scouting and command-net traffic can be acknowledged and forwarded without unnecessary delay.",
        hhmm_to_min("05:20"), hhmm_to_min("05:40"), "OPEN_PRIORITY_NET", 10,
    ))
    _add_task(state, StationTask(
        "prebattle_air", "AIR_OPS", "Prepare flight deck for combat cycle",
        "Bring spotting, fueling, arming, deck crews, and CAP reserve to launch-ready condition without sacrificing deck safety.",
        hhmm_to_min("05:20"), hhmm_to_min("06:40"), "PREPARE_FLIGHT_DECK", 14,
    ))
    _add_task(state, StationTask(
        "prebattle_eng", "ENGINEERING", "Bring plant to maneuvering readiness",
        "Prepare propulsion and electrical generation for rapid carrier maneuvering and sustained flight operations.",
        hhmm_to_min("05:20"), hhmm_to_min("06:30"), "MANEUVERING_READY", 10,
    ))
    return state


def _add_task(state: EnterpriseDutyState, task: StationTask) -> None:
    if task.key in state.tasks:
        return
    state.tasks[task.key] = task
    state.task_order.append(task.key)
    state.score_possible += task.points
    state.stations[task.station].alert = "ACTION"
    state.action_log.insert(0, f"{state.clock} — NEW TASK [{STATION_DEFS[task.station]['short']}]: {task.title}")


def station_efficiency(state: EnterpriseDutyState, station_key: str) -> float:
    station = state.stations[station_key]
    if not station.crew_keys:
        return 25.0
    vals = []
    for ck in station.crew_keys:
        crew = state.crew[ck]
        prof = crew.proficiency.get(station_key, 45.0)
        penalty = crew.fatigue * 0.22 + crew.stress * 0.16 + (25.0 if crew.injured else 0.0)
        vals.append(max(15.0, prof - penalty))
    return sum(vals) / len(vals)


def assign_crew(state: EnterpriseDutyState, crew_key: str, station_key: str) -> Tuple[bool, str]:
    if crew_key not in state.crew or station_key not in state.stations:
        return False, "Unknown crew member or station."
    for st in state.stations.values():
        if crew_key in st.crew_keys:
            st.crew_keys.remove(crew_key)
    state.stations[station_key].crew_keys.append(crew_key)
    crew = state.crew[crew_key]
    state.action_log.insert(0, f"{state.clock} — {crew.name} reassigned to {STATION_DEFS[station_key]['name']}.")
    return True, f"{crew.name} assigned to {STATION_DEFS[station_key]['name']}."


def _complete_task(state: EnterpriseDutyState, task: StationTask, quality: float, result: str) -> str:
    if task.completed or task.failed:
        return "That task is already closed."
    task.completed = True
    task.completed_minute = state.current_minute
    task.result = result
    earned = int(round(task.points * max(0.25, min(1.0, quality / 100.0))))
    state.score_points += earned
    state.stations[task.station].readiness = min(100.0, state.stations[task.station].readiness + 4.0 + quality * 0.03)
    state.action_log.insert(0, f"{state.clock} — COMPLETE [{STATION_DEFS[task.station]['short']}]: {task.title} (+{earned}/{task.points}). {result}")
    _refresh_station_alerts(state)
    return f"Task complete: {task.title} (+{earned}/{task.points}). {result}"


def _fail_expired_tasks(state: EnterpriseDutyState) -> None:
    for task in state.tasks.values():
        if not task.completed and not task.failed and state.current_minute > task.deadline_minute:
            task.failed = True
            task.result = "Deadline passed without the required station action."
            state.errors += 1
            st = state.stations[task.station]
            st.readiness = max(0.0, st.readiness - 8.0)
            state.action_log.insert(0, f"{min_to_hhmm(task.deadline_minute)} — MISSED [{STATION_DEFS[task.station]['short']}]: {task.title}")
    _refresh_station_alerts(state)


def _refresh_station_alerts(state: EnterpriseDutyState) -> None:
    for key, st in state.stations.items():
        opens = [t for t in state.tasks.values() if t.station == key and not t.completed and not t.failed]
        overdue_soon = any(t.deadline_minute - state.current_minute <= 8 for t in opens)
        if overdue_soon:
            st.alert = "URGENT"
        elif opens:
            st.alert = "ACTION"
        elif st.readiness < 55:
            st.alert = "DEGRADED"
        else:
            st.alert = "READY"


def _sync_historical_events(state: EnterpriseDutyState, before: set[str]) -> None:
    new_events = [e for e in state.historical.delivered_events if e not in before and e not in state.processed_history_events]
    for event_key in new_events:
        state.processed_history_events.append(event_key)
        state.latest_report_key = event_key
        msg = next((m for m in state.historical.messages if m.get("headline") and event_key in state.historical.delivered_events), None)
        # Station task generation keys are explicit so no source-derived event becomes an invented obligation silently.
        if event_key == "pby_ship_sighting":
            _add_task(state, StationTask(
                "route_first_sighting", "RADIO", "Route first Japanese surface sighting",
                "A scouting report has reached the ship. Route it promptly to CIC and command channels while preserving its uncertainty.",
                state.current_minute, state.current_minute + 8, "ROUTE_SCOUT_REPORT", 12,
            ))
            _add_task(state, StationTask(
                "plot_first_sighting", "CIC", "Plot initial surface contact",
                "Enter the reported surface contact on the plot as uncertain rather than treating it as a complete carrier-force solution.",
                state.current_minute, state.current_minute + 12, "PLOT_CONTACT", 12,
            ))
        elif event_key == "incoming_air":
            _add_task(state, StationTask(
                "air_warning_fc", "FIRE_CONTROL", "Raise air-defense readiness",
                "Midway has an inbound-air warning. Bring lookouts, radar correlation, and AA control to high readiness without firing on unidentified tracks.",
                state.current_minute, state.current_minute + 10, "AIR_DEFENSE_READY", 12,
            ))
        elif event_key in ("carrier_sighting", "carrier_report_reaches_command"):
            _add_task(state, StationTask(
                f"cic_{event_key}", "CIC", "Refine carrier contact plot",
                "Update the carrier plot from the newly received report, keep the uncertainty annotation, and push the refined picture to command and aviation operations.",
                state.current_minute, state.current_minute + 12, "REFINE_CARRIER_PLOT", 14,
            ))
        elif event_key == "tf16_launch":
            _add_task(state, StationTask(
                "execute_launch", "AIR_OPS", "Execute historical TF 16 launch cycle",
                "Launch the prepared Enterprise strike cycle while preserving deck safety and a usable CAP/recovery reserve.",
                state.current_minute, state.current_minute + 20, "LAUNCH_STRIKE", 20,
            ))
            _add_task(state, StationTask(
                "bridge_launch_course", "BRIDGE", "Set aviation maneuver",
                "Maneuver the carrier for safe launch/recovery wind conditions while remaining responsive to TF 16 tactical orders.",
                state.current_minute, state.current_minute + 15, "AVIATION_COURSE", 14,
            ))
        elif event_key == "torpedo_attack":
            _add_task(state, StationTask(
                "radio_strike_reports", "RADIO", "Prioritize fragmented strike reports",
                "Combat reports are arriving incomplete. Route priority reports rapidly without merging separate observations into false certainty.",
                state.current_minute, state.current_minute + 12, "ROUTE_BATTLE_REPORTS", 12,
            ))
        elif event_key == "three_carriers_hit":
            _add_task(state, StationTask(
                "cic_residual_threat", "CIC", "Maintain residual-carrier threat",
                "Three Japanese carriers are reported hit. Keep at least one operational carrier threat on the plot until reliable evidence resolves it.",
                state.current_minute, state.current_minute + 15, "KEEP_RESIDUAL_THREAT", 16,
            ))
        elif event_key == "hiryu_launch":
            _add_task(state, StationTask(
                "air_recovery_ready", "AIR_OPS", "Preserve recovery/CAP flexibility",
                "A remaining carrier threat is still possible. Configure the deck to recover returning aircraft while retaining defensive flexibility.",
                state.current_minute, state.current_minute + 18, "RECOVERY_READY", 14,
            ))
        elif event_key == "yorktown_dive_attack":
            _add_task(state, StationTask(
                "dc_general_quarters", "DAMAGE_CONTROL", "Recheck battle damage-control posture",
                "Yorktown is under attack. Re-verify repair-party, firemain, medical, and watertight readiness aboard Enterprise.",
                state.current_minute, state.current_minute + 12, "RECHECK_DC", 14,
            ))
            _add_task(state, StationTask(
                "fc_high_alert", "FIRE_CONTROL", "Maintain high air-defense alert",
                "A carrier in the formation is under attack. Keep Enterprise's defensive control system ready and classify every track before engagement.",
                state.current_minute, state.current_minute + 10, "HIGH_AA_ALERT", 14,
            ))
        elif event_key == "yorktown_torpedo_attack":
            _add_task(state, StationTask(
                "engineering_evasive_ready", "ENGINEERING", "Hold plant for immediate maneuver",
                "Maintain propulsion and generator reserve for immediate high-speed maneuvering while preserving plant reliability.",
                state.current_minute, state.current_minute + 10, "FULL_MANEUVER_READY", 14,
            ))
        elif event_key == "hiryu_strike":
            _add_task(state, StationTask(
                "cic_hiryu_update", "CIC", "Plot late-afternoon Hiryu strike report",
                "Update the tactical plot with the delayed report of the strike on Hiryu, but do not erase uncertainty about other Japanese surface forces.",
                state.current_minute, state.current_minute + 15, "PLOT_HIRYU_RESULT", 14,
            ))


def _minute_systems(state: EnterpriseDutyState) -> None:
    # Shipboard readiness evolves slowly and is influenced by crew fatigue and station efficiency.
    elapsed = max(0, state.current_minute - hhmm_to_min("05:20"))
    for crew in state.crew.values():
        crew.fatigue = min(100.0, crew.fatigue + 0.012)
        crew.stress = min(100.0, max(0.0, crew.stress + (0.012 if state.current_minute >= hhmm_to_min("07:00") else -0.004)))
    eng_eff = station_efficiency(state, "ENGINEERING")
    state.plant_readiness = max(35.0, min(100.0, state.plant_readiness + (eng_eff - 70.0) * 0.002 - max(0, state.speed_knots - 20) * 0.004))
    state.fuel_state = max(25.0, state.fuel_state - 0.006 * (0.7 + state.speed_knots / 20.0))
    air_eff = station_efficiency(state, "AIR_OPS")
    state.deck_safety = max(30.0, min(100.0, state.deck_safety + (air_eff - 68.0) * 0.002))
    state.aircraft_fueled = min(100.0, state.aircraft_fueled + 0.02 * (air_eff / 70.0))
    state.aircraft_armed = min(100.0, state.aircraft_armed + 0.018 * (air_eff / 70.0))
    state.bridge_heading += (state.ordered_heading - state.bridge_heading) * 0.06
    state.speed_knots += (state.ordered_speed - state.speed_knots) * 0.08
    # Wind-over-deck is a gameplay approximation, not a reconstructed meteorological vector.
    state.wind_over_deck = max(0.0, min(40.0, state.speed_knots * 0.72 + 6.0))
    state.electrical_load = max(45.0, min(96.0, 62.0 + (state.radar_air_readiness + state.aa_readiness) * 0.08 + (5.0 if state.strike_launched else 0.0)))
    if elapsed % 90 == 0 and elapsed > 0:
        state.action_log.insert(0, f"{state.clock} — Watch rotation check: crew fatigue and station readiness reviewed.")


def advance_enterprise(state: EnterpriseDutyState, minutes: int = 1) -> EnterpriseDutyState:
    if state.completed:
        return state
    target = min(state.historical.end_minute, state.current_minute + max(1, int(minutes)))
    while state.current_minute < target:
        before = set(state.historical.delivered_events)
        advance_historical(state.historical, 1)
        # Task-force decision prompts belong to the separate Historical Operations mode.
        # In named-ship station duty they are treated as handled by the command team so
        # the player is not penalized for a second UI they cannot answer here.
        for prompt in DECISIONS:
            if prompt.minute <= state.current_minute and prompt.key not in state.historical.decisions:
                state.historical.decisions[prompt.key] = {
                    "option": "HANDLED BY COMMAND TEAM",
                    "points": 0,
                    "rationale": "Task-force command decision is outside this station-duty player's scope.",
                    "minute": state.current_minute,
                }
        _sync_historical_events(state, before)
        _minute_systems(state)
        _fail_expired_tasks(state)
        if state.historical.completed:
            state.completed = True
            state.running = False
            state.action_log.insert(0, f"{state.clock} — Enterprise Midway duty watch complete. Evaluate the station record.")
            break
    return state


def jump_to_next_enterprise_task(state: EnterpriseDutyState) -> EnterpriseDutyState:
    candidates: List[int] = []
    candidates.extend(t.opened_minute for t in state.tasks.values() if not t.completed and not t.failed and t.opened_minute > state.current_minute)
    # Historical event report times are the main future task triggers.
    from .historical import EVENTS
    candidates.extend(e.report_minute for e in EVENTS if e.key not in state.historical.delivered_events and e.report_minute > state.current_minute)
    open_deadlines = [t.deadline_minute for t in state.tasks.values() if not t.completed and not t.failed and t.deadline_minute > state.current_minute]
    candidates.extend(open_deadlines)
    if not candidates:
        return advance_enterprise(state, state.historical.end_minute - state.current_minute)
    return advance_enterprise(state, max(1, min(candidates) - state.current_minute))


def open_tasks(state: EnterpriseDutyState, station: Optional[str] = None) -> List[StationTask]:
    tasks = [state.tasks[k] for k in state.task_order if not state.tasks[k].completed and not state.tasks[k].failed]
    if station:
        tasks = [t for t in tasks if t.station == station]
    return tasks


def closed_tasks(state: EnterpriseDutyState, station: Optional[str] = None) -> List[StationTask]:
    tasks = [state.tasks[k] for k in state.task_order if state.tasks[k].completed or state.tasks[k].failed]
    if station:
        tasks = [t for t in tasks if t.station == station]
    return tasks


def perform_station_action(state: EnterpriseDutyState, station: str, action: str) -> Tuple[bool, str]:
    if state.completed:
        return False, "The duty watch is complete."
    if station not in state.stations:
        return False, "Unknown station."
    eff = station_efficiency(state, station)
    candidates = [t for t in open_tasks(state, station) if t.action == action and t.opened_minute <= state.current_minute]
    task = candidates[0] if candidates else None

    # Station controls can be used even if no scored task is active; they still affect readiness.
    if station == "BRIDGE":
        if action == "AVIATION_COURSE":
            state.ordered_heading = (state.bridge_heading + 20.0) % 360.0
            state.ordered_speed = 25.0
            state.engine_order = "AVIATION MANEUVER"
            state.stations[station].readiness = min(100, state.stations[station].readiness + 5)
            result = "Maneuvered for improved wind-over-deck at 25 knots. The heading is a gameplay abstraction; the historical source note is kept separately rather than forcing differing clock conventions into one timeline."
        elif action == "STEADY_COURSE":
            state.ordered_heading = round(state.bridge_heading / 5.0) * 5.0
            state.rudder = 0.0
            result = f"Steady on {state.ordered_heading:.0f}°T; rudder amidships."
        elif action == "SLOW_TO_15":
            state.ordered_speed = 15.0
            state.engine_order = "STANDARD"
            result = "Engine order reduced to standard 15 knots."
        else:
            return False, "That bridge action is unavailable."
    elif station == "CIC":
        if action in ("PLOT_CONTACT", "REFINE_CARRIER_PLOT", "KEEP_RESIDUAL_THREAT", "PLOT_HIRYU_RESULT"):
            state.radar_air_readiness = min(100, state.radar_air_readiness + 2)
            result = "Plot updated with uncertainty preserved and the contact routed to affected stations."
        elif action == "VERIFY_PLOT":
            state.stations[station].readiness = min(100, state.stations[station].readiness + 2)
            result = "Plot cross-check complete; stale and source-separated tracks remain marked."
        else:
            return False, "That CIC action is unavailable."
    elif station == "RADIO":
        if action in ("OPEN_PRIORITY_NET", "ROUTE_SCOUT_REPORT", "ROUTE_BATTLE_REPORTS"):
            state.messages_routed.append(action)
            result = "Priority traffic routed and acknowledged; report source and delay retained in the log."
        elif action == "RADIO_CHECK":
            state.stations[station].readiness = min(100, state.stations[station].readiness + 2)
            result = "Radio circuit check complete."
        else:
            return False, "That radio action is unavailable."
    elif station == "ENGINEERING":
        if action == "MANEUVERING_READY":
            state.plant_readiness = min(100, state.plant_readiness + 6)
            state.electrical_load = max(55, state.electrical_load - 2)
            result = "Engineering plant set for rapid maneuvering with electrical reserve available."
        elif action == "FULL_MANEUVER_READY":
            state.plant_readiness = min(100, state.plant_readiness + 5)
            state.ordered_speed = max(state.ordered_speed, 25.0)
            result = "Plant held ready for immediate high-speed maneuver; generator reserve confirmed."
        elif action == "BALANCE_LOAD":
            state.electrical_load = max(52.0, state.electrical_load - 8.0)
            state.plant_readiness = min(100, state.plant_readiness + 2)
            result = "Electrical loads balanced; reserve margin improved."
        else:
            return False, "That engineering action is unavailable."
    elif station == "DAMAGE_CONTROL":
        if action == "SET_DC_READY":
            state.repair_party_readiness = min(100, state.repair_party_readiness + 12)
            state.watertight_integrity = min(100, state.watertight_integrity + 5)
            result = "Repair parties staged and watertight/battle readiness verified."
        elif action == "RECHECK_DC":
            state.repair_party_readiness = min(100, state.repair_party_readiness + 8)
            state.watertight_integrity = min(100, state.watertight_integrity + 3)
            result = "Firemain, repair parties, medical readiness, and watertight status rechecked."
        elif action == "CHECK_BOUNDARIES":
            state.watertight_integrity = min(100, state.watertight_integrity + 3)
            result = "Watertight boundary inspection complete."
        else:
            return False, "That damage-control action is unavailable."
    elif station == "FIRE_CONTROL":
        if action in ("AIR_DEFENSE_READY", "HIGH_AA_ALERT"):
            state.aa_readiness = min(100, state.aa_readiness + 10)
            state.radar_air_readiness = min(100, state.radar_air_readiness + 5)
            result = "Air-defense stations raised; tracks must still be positively classified before engagement."
        elif action == "TRACK_CHECK":
            state.radar_air_readiness = min(100, state.radar_air_readiness + 3)
            result = "Radar/lookout track correlation check complete."
        else:
            return False, "That fire-control action is unavailable."
    elif station == "AIR_OPS":
        if action == "PREPARE_FLIGHT_DECK":
            state.deck_spot = min(100, state.deck_spot + 24)
            state.aircraft_fueled = min(100, state.aircraft_fueled + 18)
            state.aircraft_armed = min(100, state.aircraft_armed + 20)
            state.deck_safety = max(70, state.deck_safety - 2)
            result = "Flight deck spotted; fueling/arming advanced while safety lanes remain controlled."
        elif action == "LAUNCH_STRIKE":
            if state.aircraft_fueled < 80 or state.aircraft_armed < 80 or state.deck_spot < 75:
                state.errors += 1
                state.deck_safety = max(25, state.deck_safety - 8)
                return False, "Launch held: spotting/fueling/arming readiness is insufficient. Prepare the flight deck first."
            state.strike_launched = True
            state.deck_spot = max(15, state.deck_spot - 48)
            state.aircraft_fueled = max(25, state.aircraft_fueled - 35)
            state.aircraft_armed = max(20, state.aircraft_armed - 38)
            state.cap_reserve = max(45, state.cap_reserve - 7)
            result = "Enterprise strike cycle launched; deck transitions toward recovery/CAP support."
        elif action == "RECOVERY_READY":
            state.recovery_ready = True
            state.deck_spot = min(100, state.deck_spot + 18)
            state.cap_reserve = min(100, state.cap_reserve + 4)
            result = "Deck configured for recovery with defensive flexibility retained."
        elif action == "DECK_SAFETY_CHECK":
            state.deck_safety = min(100, state.deck_safety + 4)
            result = "Flight-deck safety check complete; movement lanes and firefighting readiness verified."
        else:
            return False, "That aviation action is unavailable."
    else:
        return False, "Unknown station."

    # Task quality combines crew capability with timing. Early completion is rewarded but not required.
    if task:
        remaining = max(0, task.deadline_minute - state.current_minute)
        span = max(1, task.deadline_minute - task.opened_minute)
        timing = 70.0 + 30.0 * remaining / span
        quality = max(30.0, min(100.0, 0.65 * eff + 0.35 * timing))
        return True, _complete_task(state, task, quality, result)

    state.stations[station].readiness = min(100.0, state.stations[station].readiness + max(0.5, (eff - 55.0) * 0.02))
    state.action_log.insert(0, f"{state.clock} — [{STATION_DEFS[station]['short']}] {result}")
    return True, result


def station_snapshot(state: EnterpriseDutyState, station: str) -> dict:
    st = state.stations[station]
    return {
        "station": STATION_DEFS[station]["name"],
        "readiness": st.readiness,
        "efficiency": station_efficiency(state, station),
        "alert": st.alert,
        "crew": [state.crew[k].name for k in st.crew_keys],
        "open_tasks": len(open_tasks(state, station)),
    }


def enterprise_summary(state: EnterpriseDutyState) -> dict:
    open_count = len(open_tasks(state))
    complete = len([t for t in state.tasks.values() if t.completed])
    missed = len([t for t in state.tasks.values() if t.failed])
    avg_station = sum(s.readiness for s in state.stations.values()) / max(1, len(state.stations))
    avg_eff = sum(station_efficiency(state, k) for k in state.stations) / max(1, len(state.stations))
    return {
        "clock": state.clock,
        "tasks_complete": complete,
        "tasks_missed": missed,
        "tasks_open": open_count,
        "score_points": state.score_points,
        "score_possible": state.score_possible,
        "station_readiness": avg_station,
        "crew_efficiency": avg_eff,
        "plant_readiness": state.plant_readiness,
        "deck_safety": state.deck_safety,
        "intel_discipline": state.historical.intel_discipline,
        "errors": state.errors,
        "strike_launched": state.strike_launched,
        "recovery_ready": state.recovery_ready,
    }


def evaluate_enterprise(state: EnterpriseDutyState) -> float:
    _fail_expired_tasks(state)
    if not state.completed:
        # Evaluation may be requested early; close current open tasks as missed without advancing canonical history.
        newly_failed = 0
        for t in state.tasks.values():
            if not t.completed and not t.failed:
                t.failed = True
                t.result = "Watch ended before task completion."
                newly_failed += 1
        state.errors += newly_failed
    summary = enterprise_summary(state)
    task_component = 58.0 * state.score_points / max(1, state.score_possible)
    station_component = 0.16 * summary["station_readiness"]
    crew_component = 0.08 * summary["crew_efficiency"]
    plant_component = 0.06 * state.plant_readiness
    safety_component = 0.08 * state.deck_safety
    professionalism = 4.0 if state.strike_launched else 0.0
    penalty = min(18.0, summary["tasks_missed"] * 2.5 + state.errors * 1.5)
    score = max(0.0, min(100.0, task_component + station_component + crew_component + plant_component + safety_component + professionalism - penalty))
    state.evaluated = True
    return round(score, 1)


def action_catalog(station: str) -> List[Tuple[str, str]]:
    return {
        "BRIDGE": [
            ("AVIATION_COURSE", "Set aviation maneuver / 25 kt"),
            ("STEADY_COURSE", "Steady current course"),
            ("SLOW_TO_15", "Standard 15 knots"),
        ],
        "CIC": [
            ("PLOT_CONTACT", "Plot initial contact"),
            ("REFINE_CARRIER_PLOT", "Refine carrier contact"),
            ("KEEP_RESIDUAL_THREAT", "Keep residual carrier threat"),
            ("PLOT_HIRYU_RESULT", "Plot Hiryu strike report"),
            ("VERIFY_PLOT", "Cross-check tactical plot"),
        ],
        "RADIO": [
            ("OPEN_PRIORITY_NET", "Open priority command circuits"),
            ("ROUTE_SCOUT_REPORT", "Route scouting report"),
            ("ROUTE_BATTLE_REPORTS", "Route battle reports"),
            ("RADIO_CHECK", "Run radio circuit check"),
        ],
        "ENGINEERING": [
            ("MANEUVERING_READY", "Set maneuvering readiness"),
            ("FULL_MANEUVER_READY", "Hold full maneuver readiness"),
            ("BALANCE_LOAD", "Balance electrical load"),
        ],
        "DAMAGE_CONTROL": [
            ("SET_DC_READY", "Set battle DC readiness"),
            ("RECHECK_DC", "Recheck repair parties / firemain"),
            ("CHECK_BOUNDARIES", "Inspect watertight boundaries"),
        ],
        "FIRE_CONTROL": [
            ("AIR_DEFENSE_READY", "Raise air-defense readiness"),
            ("HIGH_AA_ALERT", "Set high AA alert"),
            ("TRACK_CHECK", "Radar/lookout track check"),
        ],
        "AIR_OPS": [
            ("PREPARE_FLIGHT_DECK", "Prepare flight deck"),
            ("LAUNCH_STRIKE", "Execute strike launch"),
            ("RECOVERY_READY", "Configure recovery deck"),
            ("DECK_SAFETY_CHECK", "Flight-deck safety check"),
        ],
    }[station]
