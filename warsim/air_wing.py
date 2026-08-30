from __future__ import annotations

"""v1.5 persistent carrier air-wing operations.

This is a gameplay/training layer. Squadron labels reflect the carrier-air-group structure used by
Enterprise-era operations, while exact roster counts, individual aircrew identities, sortie-cycle
rates, fuel/ordnance quantities and performance coefficients are explicitly simulation abstractions
unless separately sourced in HISTORICAL_SOURCES.md.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
import math
import random


MISSION_TYPES = ("CAP", "SCOUT", "STRIKE", "ASW", "FERRY")
STATUS_GROUNDED = "GROUNDED"
STATUS_SPOTTED = "SPOTTED"
STATUS_AIRBORNE = "AIRBORNE"
STATUS_RETURNING = "RETURNING"
STATUS_MAINTENANCE = "MAINTENANCE"
STATUS_LOST = "LOST"


@dataclass
class Aircrew:
    key: str
    name: str
    role: str
    experience: float
    fatigue: float = 12.0
    morale: float = 82.0
    missions: int = 0
    injuries: float = 0.0
    available: bool = True


@dataclass
class Aircraft:
    key: str
    squadron: str
    aircraft_type: str
    bureau_no: str
    condition: float = 100.0
    fuel_pct: float = 100.0
    ammo_pct: float = 100.0
    ordnance: str = "NONE"
    status: str = STATUS_GROUNDED
    deck: str = "HANGAR"
    pilot_key: str = ""
    flight_hours: float = 0.0
    sorties: int = 0


@dataclass
class Squadron:
    key: str
    name: str
    role: str
    aircraft_type: str
    commander: str
    aircraft_keys: List[str] = field(default_factory=list)
    readiness: float = 100.0
    selected: bool = False


@dataclass
class FlightMission:
    key: str
    mission_type: str
    squadron: str
    aircraft_keys: List[str]
    target_east_nm: float
    target_north_nm: float
    planned_minutes: float
    status: str = "PLANNED"
    elapsed_minutes: float = 0.0
    distance_nm: float = 0.0
    fuel_burn_pct: float = 0.0
    reports_generated: int = 0
    aircraft_lost: int = 0
    score: float = 100.0


@dataclass
class AirWingState:
    squadrons: Dict[str, Squadron] = field(default_factory=dict)
    aircraft: Dict[str, Aircraft] = field(default_factory=dict)
    aircrew: Dict[str, Aircrew] = field(default_factory=dict)
    missions: Dict[str, FlightMission] = field(default_factory=dict)
    selected_squadron: str = "VF6"
    selected_mission_type: str = "CAP"
    selected_sortie_size: int = 4
    selected_mission: str = ""
    deck_cycle: str = "RECOVERY_CLEAR"
    launch_queue: List[str] = field(default_factory=list)
    recovery_queue: List[str] = field(default_factory=list)
    aviation_fuel_units: float = 6200.0
    bombs: int = 72
    torpedoes: int = 26
    fighter_ammo_units: float = 3200.0
    spare_parts: float = 900.0
    sorties_launched: int = 0
    sorties_recovered: int = 0
    aircraft_lost: int = 0
    scout_reports: int = 0
    maintenance_actions: int = 0
    operational_score: float = 100.0
    next_mission_id: int = 1
    log: List[str] = field(default_factory=list)


def _crew_names() -> List[str]:
    return [
        "Lt. James Mercer", "Ens. Thomas Hale", "Lt. Robert Quinn", "Ens. William Cross",
        "Lt. Charles Avery", "Ens. Martin Cole", "Lt. George Nolan", "Ens. Peter Shaw",
        "Lt. Daniel Price", "Ens. Samuel Reed", "Lt. Edward Lane", "Ens. Frank Mills",
        "Lt. Henry Doyle", "Ens. Arthur Bennett", "Lt. Joseph Ward", "Ens. Leo Foster",
        "Lt. Raymond Grant", "Ens. Paul Turner", "Lt. Walter Brooks", "Ens. Allen Hayes",
    ]


def create_air_wing(seed: int = 19420604) -> AirWingState:
    rng = random.Random(seed)
    state = AirWingState()
    specs = [
        ("VF6", "Fighting Squadron Six", "FIGHTER", "F4F Wildcat", "Lt. Cdr. VF-6 Training CO", 12),
        ("VB6", "Bombing Squadron Six", "DIVE_BOMBER", "SBD Dauntless", "Lt. Cdr. VB-6 Training CO", 12),
        ("VS6", "Scouting Squadron Six", "SCOUT", "SBD Dauntless", "Lt. Cdr. VS-6 Training CO", 10),
        ("VT6", "Torpedo Squadron Six", "TORPEDO", "TBD Devastator", "Lt. Cdr. VT-6 Training CO", 8),
    ]
    names = _crew_names()
    name_idx = 0
    for skey, name, role, ac_type, commander, count in specs:
        sq = Squadron(skey, name, role, ac_type, commander, selected=(skey == "VF6"))
        state.squadrons[skey] = sq
        for i in range(1, count + 1):
            akey = f"{skey}-{i:02d}"
            ckey = f"P-{skey}-{i:02d}"
            crew_name = names[name_idx % len(names)] + f" {skey}-{i:02d}"
            name_idx += 1
            state.aircrew[ckey] = Aircrew(
                ckey, crew_name, "PILOT", experience=round(rng.uniform(54.0, 91.0), 1),
                fatigue=round(rng.uniform(5.0, 22.0), 1), morale=round(rng.uniform(72.0, 94.0), 1),
            )
            state.aircraft[akey] = Aircraft(
                key=akey, squadron=skey, aircraft_type=ac_type,
                bureau_no=f"TRN-{skey}-{100+i}", condition=round(rng.uniform(86.0, 100.0), 1),
                fuel_pct=100.0, ammo_pct=100.0, ordnance="NONE", status=STATUS_GROUNDED,
                deck="HANGAR", pilot_key=ckey,
            )
            sq.aircraft_keys.append(akey)
    state.log.append("Air Group training roster initialized. Individual names/counts are simulation abstractions.")
    refresh_readiness(state)
    return state


def refresh_readiness(state: AirWingState) -> None:
    for sq in state.squadrons.values():
        aircraft = [state.aircraft[k] for k in sq.aircraft_keys if k in state.aircraft]
        if not aircraft:
            sq.readiness = 0.0
            continue
        usable = [a for a in aircraft if a.status != STATUS_LOST and a.condition >= 45]
        avg_cond = sum(a.condition for a in usable) / max(1, len(usable))
        availability = len(usable) / len(aircraft) * 100.0
        sq.readiness = max(0.0, min(100.0, availability * .55 + avg_cond * .45))


def selected_squadron(state: AirWingState) -> Squadron:
    if state.selected_squadron not in state.squadrons:
        state.selected_squadron = next(iter(state.squadrons))
    return state.squadrons[state.selected_squadron]


def cycle_squadron(state: AirWingState) -> Squadron:
    keys = list(state.squadrons)
    idx = keys.index(state.selected_squadron) if state.selected_squadron in keys else 0
    state.selected_squadron = keys[(idx + 1) % len(keys)]
    for k, sq in state.squadrons.items():
        sq.selected = k == state.selected_squadron
    return state.squadrons[state.selected_squadron]


def cycle_mission_type(state: AirWingState) -> str:
    idx = MISSION_TYPES.index(state.selected_mission_type) if state.selected_mission_type in MISSION_TYPES else 0
    state.selected_mission_type = MISSION_TYPES[(idx + 1) % len(MISSION_TYPES)]
    return state.selected_mission_type


def adjust_sortie_size(state: AirWingState, delta: int) -> int:
    state.selected_sortie_size = max(2, min(12, state.selected_sortie_size + delta))
    return state.selected_sortie_size


def _eligible_aircraft(state: AirWingState, squadron: Squadron) -> List[Aircraft]:
    out = []
    for key in squadron.aircraft_keys:
        ac = state.aircraft[key]
        crew = state.aircrew.get(ac.pilot_key)
        if ac.status in (STATUS_GROUNDED, STATUS_SPOTTED) and ac.condition >= 60 and ac.fuel_pct >= 65 and crew and crew.available and crew.injuries < 35:
            out.append(ac)
    return sorted(out, key=lambda a: (-a.condition, -state.aircrew[a.pilot_key].experience))


def plan_selected_mission(state: AirWingState, carrier_east_nm: float, carrier_north_nm: float, heading_deg: float) -> Tuple[bool, str]:
    sq = selected_squadron(state)
    mission_type = state.selected_mission_type
    # Role guards make the squadron choice matter without requiring exact archival doctrine.
    if mission_type == "CAP" and sq.role != "FIGHTER":
        return False, "CAP planning requires the fighter squadron."
    if mission_type == "SCOUT" and sq.role not in ("SCOUT", "DIVE_BOMBER"):
        return False, "Scouting requires a scouting/dive-bomber squadron."
    if mission_type == "STRIKE" and sq.role not in ("DIVE_BOMBER", "TORPEDO"):
        return False, "Strike planning requires bombing or torpedo aircraft."
    eligible = _eligible_aircraft(state, sq)
    count = min(state.selected_sortie_size, len(eligible))
    if count < 2:
        return False, "Insufficient serviceable aircraft/aircrew for the selected mission."
    bearing = heading_deg if mission_type == "CAP" else (heading_deg + (45 if mission_type == "SCOUT" else 90)) % 360
    range_nm = {"CAP": 18.0, "SCOUT": 55.0, "STRIKE": 70.0, "ASW": 30.0, "FERRY": 45.0}[mission_type]
    r = math.radians(bearing)
    target_e = carrier_east_nm + math.sin(r) * range_nm
    target_n = carrier_north_nm + math.cos(r) * range_nm
    key = f"AW-{state.next_mission_id:03d}"
    state.next_mission_id += 1
    mission = FlightMission(
        key=key, mission_type=mission_type, squadron=sq.key,
        aircraft_keys=[a.key for a in eligible[:count]], target_east_nm=target_e,
        target_north_nm=target_n, planned_minutes={"CAP":75,"SCOUT":110,"STRIKE":135,"ASW":95,"FERRY":80}[mission_type],
    )
    state.missions[key] = mission
    state.selected_mission = key
    for a in eligible[:count]:
        a.status = STATUS_SPOTTED
        a.deck = "FLIGHT"
        if mission_type == "STRIKE":
            a.ordnance = "TORPEDO" if sq.role == "TORPEDO" else "BOMB"
    state.deck_cycle = "LAUNCH_PREP"
    state.log.insert(0, f"Planned {mission_type} {key}: {count} {sq.aircraft_type} aircraft spotted for launch.")
    return True, f"Mission {key} planned: {count} aircraft. Flight deck spotted for {mission_type}."


def launch_selected_mission(state: AirWingState, wind_over_deck: float, speed_knots: float, deck_safe: bool = True) -> Tuple[bool, str]:
    if not state.selected_mission or state.selected_mission not in state.missions:
        return False, "No selected planned air-wing mission."
    m = state.missions[state.selected_mission]
    if m.status != "PLANNED":
        return False, f"Mission {m.key} is {m.status}, not ready to launch."
    if wind_over_deck < 8.0:
        return False, "Launch held: insufficient wind over deck. Maneuver the carrier for flight operations."
    if not deck_safe:
        return False, "Launch held: flight deck not safe for launch."
    needed_fuel = len(m.aircraft_keys) * 28.0
    if state.aviation_fuel_units < needed_fuel:
        return False, "Launch held: insufficient aviation fuel inventory."
    if m.mission_type == "STRIKE":
        sq = state.squadrons[m.squadron]
        if sq.role == "TORPEDO" and state.torpedoes < len(m.aircraft_keys):
            return False, "Launch held: insufficient torpedoes."
        if sq.role != "TORPEDO" and state.bombs < len(m.aircraft_keys):
            return False, "Launch held: insufficient bombs."
    state.aviation_fuel_units -= needed_fuel
    if m.mission_type == "STRIKE":
        sq = state.squadrons[m.squadron]
        if sq.role == "TORPEDO": state.torpedoes -= len(m.aircraft_keys)
        else: state.bombs -= len(m.aircraft_keys)
    for key in m.aircraft_keys:
        ac = state.aircraft[key]
        ac.status = STATUS_AIRBORNE
        ac.fuel_pct = 100.0
        ac.sorties += 1
        ac.deck = "AIR"
        crew = state.aircrew[ac.pilot_key]
        crew.missions += 1
        crew.fatigue = min(100.0, crew.fatigue + 4.0)
    m.status = "AIRBORNE"
    state.deck_cycle = "RECOVERY_CLEAR"
    state.sorties_launched += len(m.aircraft_keys)
    state.log.insert(0, f"Launched {m.key} ({m.mission_type}) with {len(m.aircraft_keys)} aircraft at {speed_knots:.1f} kt ship speed / {wind_over_deck:.1f} kt WOD.")
    return True, f"{m.key} launched: {len(m.aircraft_keys)} aircraft airborne."


def advance_air_wing(state: AirWingState, dt_seconds: float, carrier_east_nm: float, carrier_north_nm: float, sea_state: int = 3) -> List[str]:
    messages: List[str] = []
    minutes = dt_seconds / 60.0
    if minutes <= 0:
        return messages
    for mission in state.missions.values():
        if mission.status not in ("AIRBORNE", "RETURNING"):
            continue
        mission.elapsed_minutes += minutes
        burn = minutes * (0.75 if mission.mission_type == "CAP" else 0.92)
        mission.fuel_burn_pct += burn
        mission.distance_nm += minutes * (2.2 if mission.mission_type == "SCOUT" else 1.8)
        for key in list(mission.aircraft_keys):
            ac = state.aircraft.get(key)
            if not ac or ac.status == STATUS_LOST:
                continue
            ac.flight_hours += minutes / 60.0
            ac.fuel_pct = max(0.0, 100.0 - mission.fuel_burn_pct)
            crew = state.aircrew.get(ac.pilot_key)
            if crew:
                crew.fatigue = min(100.0, crew.fatigue + minutes * .08)
        if mission.mission_type == "SCOUT" and mission.reports_generated == 0 and mission.elapsed_minutes >= mission.planned_minutes * .38:
            mission.reports_generated += 1
            state.scout_reports += 1
            state.log.insert(0, f"{mission.key}: scouting report transmitted from search sector. Role-limited training report only.")
            messages.append(f"AIR WING — {mission.key} transmitted a scouting report from its assigned search sector.")
        # Automatically turn home late in the sortie or on low fuel.
        if mission.status == "AIRBORNE" and (mission.elapsed_minutes >= mission.planned_minutes * .70 or mission.fuel_burn_pct >= 70):
            mission.status = "RETURNING"
            for key in mission.aircraft_keys:
                if key in state.aircraft and state.aircraft[key].status == STATUS_AIRBORNE:
                    state.aircraft[key].status = STATUS_RETURNING
            messages.append(f"AIR WING — {mission.key} is returning to Enterprise.")
        # Sea state adds a small operational cost rather than random catastrophic loss.
        if sea_state >= 7:
            mission.score = max(0.0, mission.score - minutes * .08)
    refresh_readiness(state)
    return messages


def recover_selected_mission(state: AirWingState, wind_over_deck: float, deck_safe: bool = True) -> Tuple[bool, str]:
    if not state.selected_mission or state.selected_mission not in state.missions:
        returning = [m for m in state.missions.values() if m.status == "RETURNING"]
        if returning:
            state.selected_mission = returning[0].key
        else:
            return False, "No returning air-wing mission selected."
    m = state.missions[state.selected_mission]
    if m.status not in ("RETURNING", "AIRBORNE"):
        return False, f"Mission {m.key} is not in a recoverable state."
    if wind_over_deck < 8.0:
        return False, "Recovery held: insufficient wind over deck."
    if not deck_safe:
        return False, "Recovery held: flight deck is fouled/unsafe."
    recovered = 0
    for key in m.aircraft_keys:
        ac = state.aircraft.get(key)
        if not ac or ac.status == STATUS_LOST:
            continue
        ac.status = STATUS_GROUNDED
        ac.deck = "HANGAR"
        ac.ordnance = "NONE"
        ac.condition = max(35.0, ac.condition - max(0.2, ac.flight_hours * .05))
        recovered += 1
    m.status = "COMPLETE"
    state.sorties_recovered += recovered
    state.deck_cycle = "RECOVERY_CLEAR"
    state.operational_score = max(0.0, min(100.0, state.operational_score + 0.4 - m.aircraft_lost * 3.0))
    state.log.insert(0, f"Recovered {m.key}: {recovered} aircraft. Mission complete.")
    refresh_readiness(state)
    return True, f"{m.key} recovered: {recovered} aircraft back aboard."


def service_selected_squadron(state: AirWingState) -> Tuple[bool, str]:
    sq = selected_squadron(state)
    candidates = [state.aircraft[k] for k in sq.aircraft_keys if state.aircraft[k].status == STATUS_GROUNDED and state.aircraft[k].condition < 99.5]
    if not candidates:
        # Still refuel/rearm grounded aircraft.
        candidates = [state.aircraft[k] for k in sq.aircraft_keys if state.aircraft[k].status == STATUS_GROUNDED and (state.aircraft[k].fuel_pct < 99 or state.aircraft[k].ammo_pct < 99)]
    if not candidates:
        return False, f"{sq.key} has no aircraft requiring immediate servicing."
    ac = min(candidates, key=lambda x: x.condition)
    parts = min(18.0, state.spare_parts)
    fuel = min(18.0, state.aviation_fuel_units)
    if parts <= 0 and fuel <= 0:
        return False, "Air wing servicing blocked: no spare parts or aviation fuel."
    ac.condition = min(100.0, ac.condition + parts * .55)
    ac.fuel_pct = min(100.0, ac.fuel_pct + fuel * 2.0)
    ac.ammo_pct = 100.0
    state.spare_parts -= parts
    state.aviation_fuel_units -= fuel
    state.maintenance_actions += 1
    refresh_readiness(state)
    state.log.insert(0, f"Serviced {ac.key}: condition {ac.condition:.0f}%, fuel {ac.fuel_pct:.0f}%.")
    return True, f"Serviced {ac.key} — condition {ac.condition:.0f}% / fuel {ac.fuel_pct:.0f}%."


def air_wing_summary(state: AirWingState) -> str:
    refresh_readiness(state)
    ready = sum(1 for a in state.aircraft.values() if a.status != STATUS_LOST and a.condition >= 60)
    airborne = sum(1 for a in state.aircraft.values() if a.status in (STATUS_AIRBORNE, STATUS_RETURNING))
    return (
        f"Air Wing {ready}/{len(state.aircraft)} serviceable • {airborne} airborne • "
        f"fuel {state.aviation_fuel_units:.0f} • bombs {state.bombs} • torps {state.torpedoes} • "
        f"score {state.operational_score:.0f}%"
    )


def squadron_lines(state: AirWingState) -> List[str]:
    refresh_readiness(state)
    lines = []
    for sq in state.squadrons.values():
        aircraft = [state.aircraft[k] for k in sq.aircraft_keys]
        airborne = sum(1 for a in aircraft if a.status in (STATUS_AIRBORNE, STATUS_RETURNING))
        serviceable = sum(1 for a in aircraft if a.status != STATUS_LOST and a.condition >= 60)
        mark = ">" if sq.key == state.selected_squadron else " "
        lines.append(f"{mark} {sq.key:<3} {sq.aircraft_type:<14} ready {sq.readiness:5.1f}% • {serviceable:2}/{len(aircraft):2} svc • {airborne:2} airborne")
    return lines


def aircraft_lines(state: AirWingState, max_lines: int = 18) -> List[str]:
    sq = selected_squadron(state)
    lines = []
    for key in sq.aircraft_keys[:max_lines]:
        a = state.aircraft[key]
        crew = state.aircrew.get(a.pilot_key)
        lines.append(
            f"{a.key:<7} {a.status:<11} cond {a.condition:5.1f}% fuel {a.fuel_pct:5.1f}% "
            f"{a.ordnance:<7} • {crew.name if crew else 'UNASSIGNED'}"
        )
    return lines


def mission_lines(state: AirWingState, max_lines: int = 12) -> List[str]:
    missions = list(state.missions.values())[-max_lines:]
    if not missions:
        return ["No planned/active air-wing missions."]
    lines = []
    for m in missions:
        mark = ">" if m.key == state.selected_mission else " "
        lines.append(f"{mark} {m.key} {m.mission_type:<6} {m.squadron} • {len(m.aircraft_keys)} ac • {m.status:<9} • {m.elapsed_minutes:5.1f} min")
    return lines


def air_wing_to_dict(state: AirWingState) -> dict:
    return asdict(state)


def air_wing_from_dict(data: dict, seed: int = 19420604) -> AirWingState:
    if not data:
        return create_air_wing(seed)
    try:
        s = AirWingState(
            selected_squadron=str(data.get("selected_squadron", "VF6")),
            selected_mission_type=str(data.get("selected_mission_type", "CAP")),
            selected_sortie_size=int(data.get("selected_sortie_size", 4)),
            selected_mission=str(data.get("selected_mission", "")),
            deck_cycle=str(data.get("deck_cycle", "RECOVERY_CLEAR")),
            launch_queue=list(data.get("launch_queue", [])),
            recovery_queue=list(data.get("recovery_queue", [])),
            aviation_fuel_units=float(data.get("aviation_fuel_units", 6200.0)),
            bombs=int(data.get("bombs", 72)), torpedoes=int(data.get("torpedoes", 26)),
            fighter_ammo_units=float(data.get("fighter_ammo_units", 3200.0)),
            spare_parts=float(data.get("spare_parts", 900.0)),
            sorties_launched=int(data.get("sorties_launched", 0)),
            sorties_recovered=int(data.get("sorties_recovered", 0)),
            aircraft_lost=int(data.get("aircraft_lost", 0)), scout_reports=int(data.get("scout_reports", 0)),
            maintenance_actions=int(data.get("maintenance_actions", 0)),
            operational_score=float(data.get("operational_score", 100.0)),
            next_mission_id=int(data.get("next_mission_id", 1)), log=list(data.get("log", [])),
        )
        for k, v in data.get("squadrons", {}).items():
            s.squadrons[k] = Squadron(**v)
        for k, v in data.get("aircraft", {}).items():
            s.aircraft[k] = Aircraft(**v)
        for k, v in data.get("aircrew", {}).items():
            s.aircrew[k] = Aircrew(**v)
        for k, v in data.get("missions", {}).items():
            s.missions[k] = FlightMission(**v)
        if not s.squadrons or not s.aircraft:
            return create_air_wing(seed)
        refresh_readiness(s)
        return s
    except Exception:
        return create_air_wing(seed)
