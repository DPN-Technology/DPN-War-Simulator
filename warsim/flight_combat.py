from __future__ import annotations

"""v1.8 first-person air combat / navigation / pilot-survival layer.

All coefficients, target identities, weapon envelopes, damage rates, and rescue timings in this
module are TRAINING SIMULATION CALIBRATION unless separately sourced in HISTORICAL_SOURCES.md.
The module intentionally does not rewrite the locked Midway historical timeline.
"""

from dataclasses import dataclass, field, asdict
import math
from typing import Dict, List, Optional, Tuple


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _angle_delta(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def _bearing_range(e1: float, n1: float, e2: float, n2: float) -> Tuple[float, float]:
    de, dn = e2 - e1, n2 - n1
    return math.degrees(math.atan2(de, dn)) % 360.0, math.hypot(de, dn)


@dataclass
class FlightContact:
    key: str
    kind: str  # AIR / SURFACE
    label: str
    side: str = "HOSTILE_TRAINING"
    east_nm: float = 0.0
    north_nm: float = 0.0
    altitude_ft: float = 0.0
    heading_deg: float = 180.0
    speed_knots: float = 110.0
    health: float = 100.0
    identified: bool = False
    active: bool = True
    threat_level: float = 50.0
    last_range_nm: float = 999.0


@dataclass
class FlightCombatState:
    active_sortie: bool = False
    mission_type: str = "TRAINING"
    selected_contact: str = ""
    contacts: Dict[str, FlightContact] = field(default_factory=dict)
    waypoint_mode: str = "CARRIER"  # CARRIER / MISSION / HOME_BASE
    waypoint_east_nm: float = 0.0
    waypoint_north_nm: float = 0.0
    mission_east_nm: float = 0.0
    mission_north_nm: float = 0.0
    radio_channel: str = "TASK_FORCE"
    radio_messages: List[str] = field(default_factory=list)
    score: float = 100.0
    aerial_victories: int = 0
    surface_hits: int = 0
    shots_fired: int = 0
    ordnance_released: int = 0
    damage_events: int = 0
    bailouts: int = 0
    ditchings: int = 0
    rescues: int = 0
    losses: int = 0
    mission_debriefs: int = 0
    rescue_pending: bool = False
    rescue_seconds: float = 0.0
    pilot_safe: bool = False
    last_event: str = ""


def combat_from_dict(data: dict | None) -> FlightCombatState:
    state = FlightCombatState()
    if not data:
        return state
    contacts_data = data.get("contacts", {}) if isinstance(data, dict) else {}
    for k, v in data.items():
        if k == "contacts" or not hasattr(state, k):
            continue
        setattr(state, k, v)
    state.contacts = {}
    for key, raw in contacts_data.items():
        if isinstance(raw, dict):
            allowed = {f.name for f in FlightContact.__dataclass_fields__.values()}
            state.contacts[key] = FlightContact(**{k: v for k, v in raw.items() if k in allowed})
    return state


def combat_to_dict(state: FlightCombatState) -> dict:
    d = asdict(state)
    return d


def _spawn_air_contacts(state: FlightCombatState, origin_e: float, origin_n: float, heading: float) -> None:
    for i, (bearing_off, rng, alt, speed) in enumerate(((18, 2.7, 3200, 155), (-24, 3.4, 4100, 165), (42, 4.2, 2700, 145)), 1):
        brg = math.radians((heading + bearing_off) % 360)
        key = f"AIR-{i}"
        state.contacts[key] = FlightContact(
            key=key, kind="AIR", label=f"Training Fighter {i}",
            east_nm=origin_e + math.sin(brg) * rng,
            north_nm=origin_n + math.cos(brg) * rng,
            altitude_ft=alt, heading_deg=(heading + 180 - bearing_off * .25) % 360,
            speed_knots=speed, threat_level=72.0,
        )


def _spawn_surface_contact(state: FlightCombatState, origin_e: float, origin_n: float, heading: float) -> None:
    brg = math.radians((heading + 78) % 360)
    state.contacts["SURF-1"] = FlightContact(
        key="SURF-1", kind="SURFACE", label="Training Surface Target",
        east_nm=origin_e + math.sin(brg) * 8.0,
        north_nm=origin_n + math.cos(brg) * 8.0,
        altitude_ft=0.0, heading_deg=(heading + 20) % 360,
        speed_knots=18.0, threat_level=55.0,
    )


def configure_sortie(
    state: FlightCombatState,
    flight,
    mission_type: str,
    carrier_e: float,
    carrier_n: float,
    carrier_heading: float,
    target_e: Optional[float] = None,
    target_n: Optional[float] = None,
) -> str:
    """Start a cockpit sortie in the training combat/navigation layer."""
    state.active_sortie = True
    state.mission_type = (mission_type or "TRAINING").upper()
    state.contacts.clear()
    state.selected_contact = ""
    state.score = 100.0
    state.rescue_pending = False
    state.rescue_seconds = 0.0
    state.pilot_safe = False
    if target_e is None or target_n is None:
        brg = math.radians((carrier_heading + (35 if state.mission_type in ("CAP", "SCOUT") else 70)) % 360)
        radius = 18.0 if state.mission_type == "CAP" else 42.0
        target_e = carrier_e + math.sin(brg) * radius
        target_n = carrier_n + math.cos(brg) * radius
    state.mission_east_nm = float(target_e)
    state.mission_north_nm = float(target_n)
    state.waypoint_east_nm = state.mission_east_nm
    state.waypoint_north_nm = state.mission_north_nm
    state.waypoint_mode = "MISSION"
    if state.mission_type in ("CAP", "TRAINING", "ESCORT"):
        _spawn_air_contacts(state, carrier_e, carrier_n, carrier_heading)
    if state.mission_type in ("STRIKE", "ASW", "TRAINING"):
        _spawn_surface_contact(state, carrier_e, carrier_n, carrier_heading)
    state.selected_contact = next(iter(state.contacts), "")
    # Cockpit stores are training-calibrated and aircraft-type aware.
    ac_type = getattr(flight, "aircraft_type", "")
    flight.gun_ammo = 240 if "F4F" in ac_type else 180
    flight.bombs = 1 if "SBD" in ac_type else 0
    flight.torpedoes = 1 if "TBD" in ac_type else 0
    flight.airframe_health = max(75.0, float(getattr(flight, "airframe_health", 100.0)))
    flight.engine_health = max(75.0, float(getattr(flight, "engine_health", 100.0)))
    flight.control_health = max(75.0, float(getattr(flight, "control_health", 100.0)))
    flight.pilot_health = max(75.0, float(getattr(flight, "pilot_health", 100.0)))
    state.last_event = f"{state.mission_type} cockpit sortie configured. Navigation and training contacts active."
    state.radio_messages.insert(0, state.last_event)
    state.radio_messages = state.radio_messages[:20]
    return state.last_event


def cycle_contact(state: FlightCombatState) -> Optional[FlightContact]:
    keys = [k for k, c in state.contacts.items() if c.active and c.health > 0]
    if not keys:
        state.selected_contact = ""
        return None
    if state.selected_contact not in keys:
        state.selected_contact = keys[0]
    else:
        state.selected_contact = keys[(keys.index(state.selected_contact) + 1) % len(keys)]
    return state.contacts[state.selected_contact]


def selected_contact(state: FlightCombatState) -> Optional[FlightContact]:
    c = state.contacts.get(state.selected_contact)
    return c if c and c.active and c.health > 0 else None


def cycle_waypoint(state: FlightCombatState, carrier_e: float, carrier_n: float, home_e: float = 0.0, home_n: float = 0.0) -> str:
    modes = ["CARRIER", "MISSION", "HOME_BASE"]
    idx = modes.index(state.waypoint_mode) if state.waypoint_mode in modes else 0
    state.waypoint_mode = modes[(idx + 1) % len(modes)]
    if state.waypoint_mode == "CARRIER":
        state.waypoint_east_nm, state.waypoint_north_nm = carrier_e, carrier_n
    elif state.waypoint_mode == "MISSION":
        state.waypoint_east_nm, state.waypoint_north_nm = state.mission_east_nm, state.mission_north_nm
    else:
        state.waypoint_east_nm, state.waypoint_north_nm = home_e, home_n
    return f"Navigation waypoint: {state.waypoint_mode}."


def radio_report(state: FlightCombatState, flight, carrier_e: float, carrier_n: float) -> str:
    brg, rng = _bearing_range(flight.east_nm, flight.north_nm, carrier_e, carrier_n)
    contact = selected_contact(state)
    if contact:
        cbrg, crng = _bearing_range(flight.east_nm, flight.north_nm, contact.east_nm, contact.north_nm)
        if crng < 5.0:
            contact.identified = True
        msg = f"TASK FORCE: carrier bearing {brg:03.0f} range {rng:.1f}nm. Selected contact {contact.key} bearing {cbrg:03.0f} range {crng:.1f}nm {'IDENTIFIED' if contact.identified else 'UNCONFIRMED'}."
    else:
        msg = f"TASK FORCE: carrier bearing {brg:03.0f} range {rng:.1f}nm. No selected contact."
    state.radio_messages.insert(0, msg)
    state.radio_messages = state.radio_messages[:20]
    return msg


def fire_guns(state: FlightCombatState, flight) -> Tuple[bool, str]:
    if not state.active_sortie or not getattr(flight, "active", False) or getattr(flight, "on_deck", True):
        return False, "Guns unavailable until airborne on an active sortie."
    ammo = int(getattr(flight, "gun_ammo", 0))
    if ammo <= 0:
        return False, "Guns dry."
    flight.gun_ammo = max(0, ammo - 12)
    state.shots_fired += 12
    c = selected_contact(state)
    if not c or c.kind != "AIR":
        return False, "Burst fired — no airborne target selected."
    brg, rng = _bearing_range(flight.east_nm, flight.north_nm, c.east_nm, c.north_nm)
    hdg_err = _angle_delta(flight.heading_deg, brg)
    alt_err = abs(float(getattr(flight, "altitude_ft", 0.0)) - c.altitude_ft)
    if rng > 0.72 or hdg_err > 15.0 or alt_err > 750.0:
        state.score = max(0.0, state.score - 0.8)
        return False, f"Burst missed — range {rng:.2f}nm, sight error {hdg_err:.0f}°."
    damage = _clamp(38.0 - rng * 22.0 - hdg_err * .55 - alt_err / 90.0, 8.0, 38.0)
    c.health = max(0.0, c.health - damage)
    if c.health <= 0.0:
        c.active = False
        state.aerial_victories += 1
        state.score = min(100.0, state.score + 4.0)
        msg = f"TRAINING AIR TARGET {c.key} DEFEATED."
        state.last_event = msg
        return True, msg
    return True, f"Hits observed on {c.key} — target condition {c.health:.0f}%."


def release_ordnance(state: FlightCombatState, flight) -> Tuple[bool, str]:
    if not state.active_sortie or getattr(flight, "on_deck", True):
        return False, "Ordnance release unavailable on deck."
    c = selected_contact(state)
    if not c or c.kind != "SURFACE":
        return False, "Select a surface target first."
    brg, rng = _bearing_range(flight.east_nm, flight.north_nm, c.east_nm, c.north_nm)
    hdg_err = _angle_delta(flight.heading_deg, brg)
    alt = float(getattr(flight, "altitude_ft", 0.0))
    if getattr(flight, "bombs", 0) > 0:
        if not 350.0 <= alt <= 5500.0 or rng > 1.15 or hdg_err > 28.0:
            return False, f"Bomb release parameters invalid — alt {alt:.0f}ft, range {rng:.2f}nm, error {hdg_err:.0f}°."
        flight.bombs -= 1
        state.ordnance_released += 1
        damage = _clamp(72.0 - rng * 35.0 - hdg_err * 1.2, 8.0, 72.0)
    elif getattr(flight, "torpedoes", 0) > 0:
        if alt > 260.0 or rng > 1.30 or hdg_err > 18.0 or flight.airspeed_knots > 135.0:
            return False, f"Torpedo release parameters invalid — alt {alt:.0f}ft, IAS {flight.airspeed_knots:.0f}kt, range {rng:.2f}nm."
        flight.torpedoes -= 1
        state.ordnance_released += 1
        damage = _clamp(88.0 - rng * 38.0 - hdg_err * 1.4, 15.0, 88.0)
    else:
        return False, "No releasable bomb or torpedo aboard."
    c.health = max(0.0, c.health - damage)
    state.surface_hits += 1
    if c.health <= 0.0:
        c.active = False
        state.score = min(100.0, state.score + 5.0)
        return True, f"TRAINING SURFACE TARGET {c.key} MISSION-KILLED."
    return True, f"Ordnance hit {c.key} — target condition {c.health:.0f}%."


def apply_aircraft_damage(state: FlightCombatState, flight, severity: float, source: str = "training fire") -> str:
    severity = _clamp(float(severity), 1.0, 35.0)
    flight.airframe_health = max(0.0, float(getattr(flight, "airframe_health", 100.0)) - severity)
    flight.engine_health = max(0.0, float(getattr(flight, "engine_health", 100.0)) - severity * .55)
    flight.control_health = max(0.0, float(getattr(flight, "control_health", 100.0)) - severity * .42)
    flight.pilot_health = max(0.0, float(getattr(flight, "pilot_health", 100.0)) - severity * .18)
    state.damage_events += 1
    state.score = max(0.0, state.score - severity * .22)
    if flight.engine_health < 18.0:
        flight.engine_running = False
        flight.throttle = 0.0
    if flight.airframe_health <= 0.0:
        state.losses += 1
    msg = f"AIRCRAFT HIT ({source}) — AIRFRAME {flight.airframe_health:.0f}% ENGINE {flight.engine_health:.0f}% CONTROLS {flight.control_health:.0f}% PILOT {flight.pilot_health:.0f}%."
    state.last_event = msg
    return msg


def emergency_abandon(state: FlightCombatState, flight) -> Tuple[bool, str]:
    if not getattr(flight, "active", False) or getattr(flight, "on_deck", True):
        return False, "Emergency escape only available airborne."
    alt = float(getattr(flight, "altitude_ft", 0.0))
    if alt >= 700.0:
        state.bailouts += 1
        flight.emergency_state = "BAILED_OUT"
        msg = "BAILOUT COMPLETE — pilot in parachute; rescue beacon active."
    else:
        state.ditchings += 1
        flight.emergency_state = "DITCHED"
        msg = "DITCHING COMPLETE — pilot in survival raft; rescue beacon active."
    flight.airframe_health = 0.0
    flight.engine_running = False
    flight.throttle = 0.0
    flight.active = False
    flight.on_deck = False
    state.rescue_pending = True
    state.rescue_seconds = 0.0
    state.pilot_safe = False
    state.losses += 1
    state.last_event = msg
    state.radio_messages.insert(0, msg)
    return True, msg


def advance_air_combat(state: FlightCombatState, flight, dt: float, carrier_e: float, carrier_n: float) -> Optional[str]:
    dt = max(0.0, min(.25, float(dt)))
    # Rescue clock continues even after cockpit state ends.
    if state.rescue_pending:
        state.rescue_seconds += dt
        if state.rescue_seconds >= 25.0:
            state.rescue_pending = False
            state.pilot_safe = True
            state.rescues += 1
            state.last_event = "SEARCH AND RESCUE COMPLETE — pilot recovered by friendly forces."
            state.radio_messages.insert(0, state.last_event)
            return state.last_event
    if not state.active_sortie or not getattr(flight, "active", False) or getattr(flight, "on_deck", True):
        return None
    # Move contacts in same global sea coordinates.
    for c in state.contacts.values():
        if not c.active:
            continue
        r = math.radians(c.heading_deg)
        step = c.speed_knots * dt / 3600.0
        c.east_nm += math.sin(r) * step
        c.north_nm += math.cos(r) * step
        _, c.last_range_nm = _bearing_range(flight.east_nm, flight.north_nm, c.east_nm, c.north_nm)
        if c.last_range_nm < 4.0:
            c.identified = True
    # Enemy training fighters can score deterministic periodic hits when close/behind.
    closest = min((c for c in state.contacts.values() if c.active and c.kind == "AIR"), key=lambda x: x.last_range_nm, default=None)
    if closest and closest.last_range_nm < .45:
        brg_to_player, _ = _bearing_range(closest.east_nm, closest.north_nm, flight.east_nm, flight.north_nm)
        if _angle_delta(closest.heading_deg, brg_to_player) < 24.0:
            cooldown = float(getattr(flight, "damage_cooldown", 0.0))
            cooldown -= dt
            flight.damage_cooldown = cooldown
            if cooldown <= 0.0:
                flight.damage_cooldown = 5.0
                return apply_aircraft_damage(state, flight, 8.0, "simulated hostile gunfire")
    # Damage degrades handling/airspeed without replacing the main flight model.
    if getattr(flight, "control_health", 100.0) < 45.0:
        flight.bank_deg *= .994
    if getattr(flight, "engine_health", 100.0) < 35.0:
        flight.throttle = min(flight.throttle, .72)
    return None


def navigation_solution(state: FlightCombatState, flight, carrier_e: float, carrier_n: float) -> str:
    if state.waypoint_mode == "CARRIER":
        te, tn = carrier_e, carrier_n
    elif state.waypoint_mode == "MISSION":
        te, tn = state.mission_east_nm, state.mission_north_nm
    else:
        te, tn = state.waypoint_east_nm, state.waypoint_north_nm
    brg, rng = _bearing_range(flight.east_nm, flight.north_nm, te, tn)
    eta_min = rng / max(1.0, float(getattr(flight, "airspeed_knots", 0.0))) * 60.0
    return f"NAV {state.waypoint_mode}: BRG {brg:03.0f}° • RNG {rng:.1f}nm • ETA {eta_min:.1f}min"


def contact_summary(state: FlightCombatState, flight) -> str:
    c = selected_contact(state)
    if not c:
        return "TARGET: NONE"
    brg, rng = _bearing_range(flight.east_nm, flight.north_nm, c.east_nm, c.north_nm)
    aspect = _angle_delta(flight.heading_deg, brg)
    alt = f" • ALT {c.altitude_ft:.0f}ft" if c.kind == "AIR" else ""
    return f"TARGET {c.key} {c.kind} • {'ID' if c.identified else 'UNK'} • BRG {brg:03.0f}° • RNG {rng:.2f}nm{alt} • ASPECT {aspect:.0f}° • COND {c.health:.0f}%"


def combat_summary(state: FlightCombatState, flight) -> str:
    return (
        f"AIR COMBAT {state.mission_type} • SCORE {state.score:.0f}% • A/A {state.aerial_victories} • A/S {state.surface_hits} • "
        f"AIRFRAME {getattr(flight,'airframe_health',100):.0f}% ENG {getattr(flight,'engine_health',100):.0f}% CTRL {getattr(flight,'control_health',100):.0f}% PILOT {getattr(flight,'pilot_health',100):.0f}%"
    )
