from __future__ import annotations

"""War Simulator v1.0 naval combat and carrier aviation training layer.

The weapon effectiveness, ammunition pools, contact motion and training-raid damage values in
this module are gameplay calibration values. They are NOT represented as exact June 1942 USS
Enterprise ammunition inventories, weapon trials, or a historical claim that Enterprise was
attacked by the simulated raid at Midway. Historical events remain in the sourced historical
layer. This module provides reusable combat mechanics for scenarios that call for them.
"""

from dataclasses import dataclass, field
import math
from typing import Dict, List, Optional, Tuple


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def wrap(v: float) -> float:
    return v % 360.0


def signed_angle(v: float) -> float:
    return (v + 180.0) % 360.0 - 180.0


@dataclass
class CombatTrack:
    key: str
    label: str
    kind: str
    side: str
    bearing_deg: float
    range_nm: float
    altitude_ft: float
    speed_knots: float
    course_deg: float
    confidence: float = 35.0
    identified: bool = False
    threat: str = "UNKNOWN"
    health: float = 100.0
    destroyed: bool = False
    attacked_ship: bool = False
    attack_type: str = ""


@dataclass
class WeaponBattery:
    key: str
    name: str
    ready: bool
    ammo: int
    reserve_ammo: int
    rounds_per_salvo: int
    max_range_nm: float
    effective_range_nm: float
    base_damage: float
    reload_seconds: float
    cooldown: float = 0.0
    director_quality: float = 82.0
    fired_salvos: int = 0


@dataclass
class CarrierAirState:
    aviation_fuel_units: float = 100.0
    fighter_ammo_units: float = 100.0
    bomb_units: int = 28
    torpedo_units: int = 12
    cap_airborne: bool = False
    cap_package_key: Optional[str] = None
    cap_endurance_seconds: float = 0.0
    cap_ammo: float = 0.0
    cap_kills: int = 0
    strike_sorties: int = 0
    recovery_cycles: int = 0
    sorties_launched: int = 0


@dataclass
class NavalCombatState:
    general_quarters: bool = False
    training_mode: bool = False
    raid_active: bool = False
    raid_generation: int = 0
    elapsed_seconds: float = 0.0
    selected_track: Optional[str] = None
    selected_battery: str = "FIVE_INCH"
    solution_quality: float = 0.0
    solution_track: Optional[str] = None
    solution_age: float = 999.0
    radar_readiness: float = 86.0
    lookout_readiness: float = 82.0
    fire_control_readiness: float = 84.0
    magazine_readiness: float = 88.0
    ammo_hoist_ready: bool = True
    air: CarrierAirState = field(default_factory=CarrierAirState)
    tracks: Dict[str, CombatTrack] = field(default_factory=dict)
    batteries: Dict[str, WeaponBattery] = field(default_factory=dict)
    enemy_destroyed: int = 0
    attacks_defeated: int = 0
    hits_taken: int = 0
    damage_taken: float = 0.0
    rounds_fired: int = 0
    training_score: float = 0.0
    log: List[str] = field(default_factory=lambda: [
        "Combat system initialized. Historical lock remains active; training raids are labeled SIMULATED."
    ])


def create_naval_combat() -> NavalCombatState:
    s = NavalCombatState()
    s.batteries = {
        "FIVE_INCH": WeaponBattery("FIVE_INCH", "5-inch dual-purpose battery", True, 120, 360, 4, 12.0, 8.5, 34.0, 2.8, director_quality=88.0),
        "MEDIUM_AA": WeaponBattery("MEDIUM_AA", "Medium AA battery", True, 420, 900, 12, 4.5, 3.0, 22.0, 1.3, director_quality=80.0),
        "LIGHT_AA": WeaponBattery("LIGHT_AA", "Light AA battery", True, 1200, 2400, 36, 1.8, 1.15, 16.0, 0.55, director_quality=70.0),
    }
    return s


def _track_order(state: NavalCombatState) -> List[CombatTrack]:
    return sorted((t for t in state.tracks.values() if not t.destroyed), key=lambda t: (t.range_nm, -t.confidence, t.key))


def selected_track(state: NavalCombatState) -> Optional[CombatTrack]:
    if state.selected_track:
        t = state.tracks.get(state.selected_track)
        if t and not t.destroyed:
            return t
    tracks = _track_order(state)
    if tracks:
        state.selected_track = tracks[0].key
        return tracks[0]
    state.selected_track = None
    return None


def cycle_track(state: NavalCombatState) -> Optional[CombatTrack]:
    tracks = _track_order(state)
    if not tracks:
        state.selected_track = None
        return None
    keys = [t.key for t in tracks]
    if state.selected_track not in keys:
        state.selected_track = keys[0]
    else:
        state.selected_track = keys[(keys.index(state.selected_track) + 1) % len(keys)]
    state.solution_quality = 0.0
    state.solution_track = None
    return state.tracks[state.selected_track]


def set_general_quarters(state: NavalCombatState, enabled: Optional[bool] = None) -> str:
    state.general_quarters = (not state.general_quarters) if enabled is None else bool(enabled)
    if state.general_quarters:
        state.fire_control_readiness = min(100.0, state.fire_control_readiness + 6.0)
        state.lookout_readiness = min(100.0, state.lookout_readiness + 5.0)
        msg = "GENERAL QUARTERS set. Weapons crews manned; magazines and damage-control parties at battle stations."
    else:
        msg = "General Quarters secured; normal combat watch restored."
    state.log.insert(0, msg)
    return msg


def start_training_raid(state: NavalCombatState) -> Tuple[bool, str]:
    if state.raid_active:
        return False, "A simulated air-defense raid is already active."
    state.training_mode = True
    state.raid_active = True
    state.raid_generation += 1
    state.enemy_destroyed = 0
    state.attacks_defeated = 0
    state.hits_taken = 0
    state.damage_taken = 0.0
    state.rounds_fired = 0
    state.training_score = 0.0
    state.air.cap_kills = 0
    state.air.strike_sorties = 0
    state.air.recovery_cycles = 0
    suffix = str(state.raid_generation)
    state.tracks = {
        f"DB-{suffix}": CombatTrack(f"DB-{suffix}", "Raid leader", "AIR", "HOSTILE", 327.0, 17.5, 9500.0, 205.0, 145.0, 42.0, False, "DIVE BOMBER", 100.0, False, False, "DIVE_BOMB"),
        f"TB-{suffix}": CombatTrack(f"TB-{suffix}", "Low-altitude element", "AIR", "HOSTILE", 035.0, 14.0, 220.0, 155.0, 210.0, 38.0, False, "TORPEDO AIRCRAFT", 112.0, False, False, "TORPEDO"),
        f"ESC-{suffix}": CombatTrack(f"ESC-{suffix}", "Fighter escort", "AIR", "HOSTILE", 350.0, 19.0, 11500.0, 245.0, 165.0, 31.0, False, "FIGHTER", 82.0, False, False, "STRAFE"),
    }
    state.selected_track = f"DB-{suffix}"
    state.solution_quality = 0.0
    state.solution_track = None
    msg = "SIMULATED RAID STARTED — three training air contacts inbound. This is not a historical Midway attack claim."
    state.log.insert(0, msg)
    return True, msg


def acquire_selected_track(state: NavalCombatState) -> Tuple[bool, str]:
    t = selected_track(state)
    if not t:
        return False, "No active contact is available to acquire."
    gain = 18.0 + state.radar_readiness * 0.18 + state.lookout_readiness * 0.07
    range_penalty = max(0.0, t.range_nm - 12.0) * 1.2
    t.confidence = clamp(t.confidence + gain - range_penalty, 0.0, 100.0)
    if t.confidence >= 65.0:
        t.identified = True
    state.solution_quality = 0.0
    state.solution_track = None
    state.log.insert(0, f"Track {t.key} updated: bearing {t.bearing_deg:03.0f}°, range {t.range_nm:.1f} nm, confidence {t.confidence:.0f}%.")
    return True, state.log[0]


def calculate_solution(state: NavalCombatState, physics=None) -> Tuple[bool, str]:
    t = selected_track(state)
    if not t:
        return False, "No contact selected for fire-control solution."
    if not state.general_quarters:
        return False, "Fire-control solution held: General Quarters has not been set."
    motion_penalty = 0.0
    if physics is not None:
        motion_penalty = abs(getattr(physics, "roll_deg", 0.0)) * 1.15 + abs(getattr(physics, "pitch_deg", 0.0)) * 0.8
    quality = (
        t.confidence * 0.48
        + state.fire_control_readiness * 0.26
        + state.radar_readiness * 0.18
        + (8.0 if t.identified else 0.0)
        - motion_penalty
        - max(0.0, t.range_nm - 10.0) * 1.4
    )
    state.solution_quality = clamp(quality, 0.0, 100.0)
    state.solution_track = t.key
    state.solution_age = 0.0
    msg = f"Fire-control solution on {t.key}: {state.solution_quality:.0f}% quality at {t.range_nm:.1f} nm."
    state.log.insert(0, msg)
    return state.solution_quality >= 25.0, msg


def select_battery(state: NavalCombatState, key: str) -> str:
    if key not in state.batteries:
        return "Unknown battery."
    state.selected_battery = key
    b = state.batteries[key]
    msg = f"Selected {b.name}: {b.ammo} ready rounds, {b.reserve_ammo} reserve."
    state.log.insert(0, msg)
    return msg


def service_ammunition(state: NavalCombatState) -> Tuple[bool, str]:
    if not state.general_quarters:
        return False, "Ammunition hoist held: set General Quarters before combat servicing."
    if not state.ammo_hoist_ready:
        return False, "Ammunition hoist is not ready."
    transferred = 0
    for b in state.batteries.values():
        desired = max(0, (180 if b.key == "FIVE_INCH" else 600 if b.key == "MEDIUM_AA" else 1600) - b.ammo)
        xfer = min(b.reserve_ammo, desired)
        b.ammo += xfer
        b.reserve_ammo -= xfer
        transferred += xfer
    state.magazine_readiness = max(45.0, state.magazine_readiness - 1.0)
    msg = f"Magazine/hoist cycle completed; {transferred} training rounds transferred to ready-service ammunition."
    state.log.insert(0, msg)
    return True, msg


def fire_selected_battery(state: NavalCombatState, physics=None) -> Tuple[bool, str]:
    t = selected_track(state)
    if not t:
        return False, "No hostile contact selected."
    if not state.general_quarters:
        return False, "Weapons are held until General Quarters is set."
    b = state.batteries[state.selected_battery]
    if not b.ready:
        return False, f"{b.name} is not ready."
    if b.cooldown > 0.01:
        return False, f"{b.name} is reloading ({b.cooldown:.1f}s)."
    if b.ammo < b.rounds_per_salvo:
        return False, f"{b.name} has insufficient ready-service ammunition."
    if t.range_nm > b.max_range_nm:
        return False, f"Target outside {b.name} maximum training range ({b.max_range_nm:.1f} nm)."
    if state.solution_track != t.key or state.solution_quality < 25.0 or state.solution_age > 18.0:
        return False, "Fire held: obtain a current fire-control solution on the selected contact."

    range_factor = clamp(1.18 - t.range_nm / max(0.1, b.max_range_nm) * 0.58, 0.35, 1.15)
    motion_factor = 1.0
    if physics is not None:
        motion_factor = clamp(1.0 - abs(getattr(physics, "roll_deg", 0.0)) / 30.0 - abs(getattr(physics, "pitch_deg", 0.0)) / 36.0, 0.45, 1.0)
    damage = b.base_damage * (state.solution_quality / 100.0) * range_factor * motion_factor
    b.ammo -= b.rounds_per_salvo
    b.cooldown = b.reload_seconds
    b.fired_salvos += 1
    state.rounds_fired += b.rounds_per_salvo
    t.health = max(0.0, t.health - damage)
    state.solution_quality = max(10.0, state.solution_quality - 6.0)
    if t.health <= 0.0:
        t.destroyed = True
        state.enemy_destroyed += 1
        state.training_score += 22.0
        msg = f"{b.name} salvo defeats {t.key}. Contact destroyed in the simulated engagement."
    else:
        msg = f"{b.name} fired on {t.key}; assessed training damage {damage:.0f}, contact integrity {t.health:.0f}%."
    state.log.insert(0, msg)
    return True, msg


def _prepared_package(shipboard, fighter_only: bool = False):
    packages = list(getattr(shipboard, "aircraft", {}).values())
    for a in packages:
        if a.launched or a.deck != "FLIGHT" or not (a.fueled and a.armed and a.spotted):
            continue
        if fighter_only and "F4F" not in a.aircraft_type:
            continue
        return a
    return None


def launch_cap(state: NavalCombatState, shipboard) -> Tuple[bool, str]:
    if state.air.cap_airborne:
        return False, "CAP is already airborne."
    ent = shipboard.enterprise
    if ent.deck_safety < 70.0:
        return False, "CAP launch held: flight-deck safety condition is below launch minimum."
    if ent.wind_over_deck < 8.0:
        return False, "CAP launch held: insufficient wind over deck. Maneuver the carrier for flight operations."
    ac = _prepared_package(shipboard, fighter_only=True)
    if not ac:
        return False, "No fueled, armed, spotted F4F package is ready on the flight deck."
    if state.air.aviation_fuel_units < 8.0 or state.air.fighter_ammo_units < 6.0:
        return False, "Aviation fuel or fighter ammunition reserve is insufficient for CAP launch."
    ac.launched = True
    ac.status = "AIRBORNE CAP"
    state.air.cap_airborne = True
    state.air.cap_package_key = ac.key
    state.air.cap_endurance_seconds = 210.0
    state.air.cap_ammo = 100.0
    state.air.aviation_fuel_units -= 8.0
    state.air.sorties_launched += 1
    state.air.fighter_ammo_units -= 6.0
    state.training_score += 6.0
    msg = f"CAP launched: {ac.label} ({ac.count} × {ac.aircraft_type})."
    state.log.insert(0, msg)
    return True, msg


def recover_cap(state: NavalCombatState, shipboard) -> Tuple[bool, str]:
    if not state.air.cap_airborne or not state.air.cap_package_key:
        return False, "No CAP package is currently airborne."
    ent = shipboard.enterprise
    if ent.deck_safety < 70.0:
        return False, "Recovery held: flight deck is not in a safe recovery condition."
    if ent.wind_over_deck < 8.0:
        return False, "Recovery held: insufficient wind over deck for the training recovery window."
    if state.raid_active and any(not t.destroyed and t.range_nm < 6.0 for t in state.tracks.values()):
        return False, "Recovery held: hostile training contacts are inside the defensive ring."
    ac = shipboard.aircraft.get(state.air.cap_package_key)
    if ac:
        ac.launched = False
        ac.deck = "FLIGHT"
        ac.spotted = True
        ac.fueled = False
        ac.armed = False
        ac.status = "RECOVERED / SERVICE REQUIRED"
    state.air.cap_airborne = False
    state.air.cap_package_key = None
    state.air.cap_endurance_seconds = 0.0
    state.air.cap_ammo = 0.0
    state.air.recovery_cycles += 1
    msg = "CAP recovered aboard; aircraft require refuel/rearm before another sortie."
    state.log.insert(0, msg)
    return True, msg


def launch_training_strike(state: NavalCombatState, shipboard) -> Tuple[bool, str]:
    ent = shipboard.enterprise
    if ent.deck_safety < 70.0:
        return False, "Strike launch held: flight-deck safety condition is below launch minimum."
    if ent.wind_over_deck < 8.0:
        return False, "Strike launch held: insufficient wind over deck."
    ac = _prepared_package(shipboard, fighter_only=False)
    if not ac or "F4F" in ac.aircraft_type:
        ac = next((a for a in shipboard.aircraft.values() if not a.launched and a.deck == "FLIGHT" and a.fueled and a.armed and a.spotted and "F4F" not in a.aircraft_type), None)
    if not ac:
        return False, "No prepared strike aircraft package is spotted on the flight deck."
    if state.air.aviation_fuel_units < 10.0:
        return False, "Insufficient aviation fuel reserve for training strike launch."
    if "TBD" in ac.aircraft_type:
        if state.air.torpedo_units < ac.count:
            return False, "Insufficient torpedo-store units for this package."
        state.air.torpedo_units -= ac.count
    else:
        if state.air.bomb_units < ac.count:
            return False, "Insufficient bomb-store units for this package."
        state.air.bomb_units -= ac.count
    state.air.aviation_fuel_units -= 10.0
    ac.launched = True
    ac.status = "AIRBORNE TRAINING STRIKE"
    state.air.strike_sorties += 1
    state.air.sorties_launched += 1
    state.training_score += 7.0
    msg = f"Training strike launched: {ac.label}. Ordnance/fuel stores decremented."
    state.log.insert(0, msg)
    return True, msg


def _apply_training_hit(state: NavalCombatState, track: CombatTrack, physics, shipboard, survivability=None) -> str:
    # Reusable physical-damage hook. Values are training calibration, not a historical Enterprise hit claim.
    severity = 18.0 if track.attack_type == "DIVE_BOMB" else 14.0 if track.attack_type == "TORPEDO" else 8.0
    if track.health < 55.0:
        severity *= 0.68
    if getattr(physics, "speed_knots", 0.0) > 18.0 and abs(getattr(physics, "rudder_deg", 0.0)) > 15.0:
        severity *= 0.78
    physics.hull_integrity = max(0.0, physics.hull_integrity - severity)
    state.hits_taken += 1
    state.damage_taken += severity
    targets = ["LOAD_BOARD", "ENG_CONSOLE", "RADIO_RACK", "DC_BOARD", "AA_DIRECTOR", "FLIGHT_CONTROL"]
    key = targets[(state.hits_taken - 1) % len(targets)]
    rt = shipboard.equipment_runtime.get(key)
    if rt is not None:
        rt.health = max(20.0, rt.health - severity * 1.5)
        if not rt.fault:
            rt.fault = "SIMULATED COMBAT DAMAGE"
    structural_note = ""
    if survivability is not None:
        try:
            from .survivability import apply_impact
            side = "PORT" if track.bearing_deg > 180 else "STARBOARD"
            structural_note = apply_impact(survivability, track.attack_type, severity * 2.8, side=side)
            physics.hull_integrity = min(physics.hull_integrity, survivability.structural_strength_pct)
        except Exception:
            structural_note = ""
    msg = f"SIMULATED HIT: {track.attack_type.replace('_',' ')} training impact. Hull {physics.hull_integrity:.0f}%; {key} casualty injected."
    if structural_note:
        msg += " " + structural_note
    state.log.insert(0, msg)
    return msg


def _advance_tracks(state: NavalCombatState, physics, shipboard, dt: float, survivability=None) -> List[str]:
    messages: List[str] = []
    if not state.raid_active:
        return messages
    for t in state.tracks.values():
        if t.destroyed or t.attacked_ship:
            continue
        closing = max(0.02, t.speed_knots * dt / 3600.0)
        # Carrier speed changes relative closure slightly; training approximation.
        closing += max(0.0, getattr(physics, "speed_knots", 0.0)) * dt / 3600.0 * 0.18
        t.range_nm = max(0.0, t.range_nm - closing)
        t.bearing_deg = wrap(t.bearing_deg + math.sin(state.elapsed_seconds * 0.035 + len(t.key)) * 0.018 * dt)
        if t.range_nm < 12.0:
            t.confidence = clamp(t.confidence + dt * 0.8, 0.0, 100.0)
        attack_range = 1.2 if t.attack_type == "TORPEDO" else 0.65 if t.attack_type == "DIVE_BOMB" else 0.35
        if t.range_nm <= attack_range:
            t.attacked_ship = True
            if t.health <= 32.0:
                state.attacks_defeated += 1
                messages.append(f"{t.key} attack breaks off after defensive damage; no ship hit.")
                state.training_score += 8.0
            else:
                messages.append(_apply_training_hit(state, t, physics, shipboard, survivability))
    alive = [t for t in state.tracks.values() if not t.destroyed and not t.attacked_ship]
    if not alive:
        state.raid_active = False
        state.training_score += max(0.0, 25.0 - state.damage_taken * 0.5)
        messages.append("SIMULATED RAID COMPLETE — combat system returned to post-engagement assessment.")
        state.log.insert(0, messages[-1])
    return messages


def _advance_cap(state: NavalCombatState, dt: float) -> None:
    if not state.air.cap_airborne:
        return
    state.air.cap_endurance_seconds = max(0.0, state.air.cap_endurance_seconds - dt)
    if state.air.cap_endurance_seconds <= 0.0:
        state.air.cap_ammo = 0.0
        state.log.insert(0, "CAP endurance exhausted; immediate recovery required.")
        return
    targets = [t for t in _track_order(state) if t.kind == "AIR" and t.range_nm <= 10.0]
    if not targets or state.air.cap_ammo <= 0:
        return
    t = targets[0]
    damage = dt * (2.0 if t.threat == "FIGHTER" else 1.45)
    t.health = max(0.0, t.health - damage)
    state.air.cap_ammo = max(0.0, state.air.cap_ammo - dt * 0.9)
    if t.health <= 0.0 and not t.destroyed:
        t.destroyed = True
        state.enemy_destroyed += 1
        state.air.cap_kills += 1
        state.training_score += 24.0
        state.log.insert(0, f"CAP defeats {t.key} before it reaches the carrier defensive ring.")


def advance_naval_combat(state: NavalCombatState, physics, shipboard, dt: float, survivability=None) -> List[str]:
    dt = clamp(dt, 0.001, 0.25)
    state.elapsed_seconds += dt
    state.solution_age += dt
    if state.solution_age > 18.0:
        state.solution_quality = max(0.0, state.solution_quality - dt * 1.5)
    for b in state.batteries.values():
        b.cooldown = max(0.0, b.cooldown - dt)
        if b.ammo <= 0:
            b.ready = False
    _advance_cap(state, dt)
    messages = _advance_tracks(state, physics, shipboard, dt, survivability)
    # Keep readiness connected to the existing shipboard runtime.
    aa_rt = shipboard.equipment_runtime.get("AA_DIRECTOR")
    radar_rt = shipboard.equipment_runtime.get("RADAR_CONSOLE")
    ord_rt = shipboard.equipment_runtime.get("ORDNANCE_STATION")
    if ord_rt is not None:
        state.ammo_hoist_ready = not bool(ord_rt.fault) and ord_rt.health >= 40.0
        state.magazine_readiness = clamp(0.9 * state.magazine_readiness + 0.1 * ord_rt.health - (15.0 if ord_rt.fault else 0.0), 10.0, 100.0)
    if aa_rt is not None:
        state.fire_control_readiness = clamp(0.8 * state.fire_control_readiness + 0.2 * aa_rt.health - (22.0 if aa_rt.fault else 0.0), 10.0, 100.0)
    if radar_rt is not None:
        state.radar_readiness = clamp(0.82 * state.radar_readiness + 0.18 * radar_rt.health - (20.0 if radar_rt.fault else 0.0), 10.0, 100.0)
    return messages


def combat_summary(state: NavalCombatState) -> str:
    t = selected_track(state)
    contact = "NO ACTIVE TRACK" if not t else f"{t.key} {t.range_nm:.1f}nm {t.bearing_deg:03.0f}° {t.confidence:.0f}%"
    b = state.batteries[state.selected_battery]
    gq = "GQ" if state.general_quarters else "WATCH"
    raid = "SIM RAID" if state.raid_active else "NO RAID"
    cap = "CAP AIRBORNE" if state.air.cap_airborne else "CAP DOWN"
    return f"{gq} | {raid} | {contact} | {b.name}: {b.ammo} rds | SOL {state.solution_quality:.0f}% | {cap}"


def combat_score(state: NavalCombatState) -> float:
    base = 45.0 + state.enemy_destroyed * 13.0 + state.attacks_defeated * 8.0 + state.air.cap_kills * 4.0
    penalty = state.hits_taken * 14.0 + state.damage_taken * 0.4
    ammo_discipline = max(0.0, 12.0 - state.rounds_fired / 180.0)
    return round(clamp(base + ammo_discipline + state.training_score * 0.22 - penalty, 0.0, 100.0), 1)


def track_table_lines(state: NavalCombatState) -> List[str]:
    lines = []
    for t in sorted(state.tracks.values(), key=lambda x: x.range_nm):
        status = "DESTROYED" if t.destroyed else "ATTACK COMPLETE" if t.attacked_ship else "TRACKING"
        ident = t.threat if t.identified else "UNIDENTIFIED AIR"
        lines.append(f"{t.key:<7} BRG {t.bearing_deg:03.0f}° RNG {t.range_nm:5.1f}nm ALT {t.altitude_ft:5.0f}ft CONF {t.confidence:3.0f}% {ident:<18} {status}")
    return lines or ["No active contacts. Start an explicitly simulated raid from Fire Control to exercise the combat engine."]


def ammunition_lines(state: NavalCombatState) -> List[str]:
    lines = [f"MAGAZINE READINESS {state.magazine_readiness:.0f}% • HOIST {'READY' if state.ammo_hoist_ready else 'OUT OF SERVICE'}"]
    for b in state.batteries.values():
        lines.append(f"{b.name:<28} ready {b.ammo:4d} • reserve {b.reserve_ammo:4d} • {'READY' if b.ready else 'NOT READY'}")
    lines.append(f"Aviation fuel {state.air.aviation_fuel_units:.0f} • fighter ammo {state.air.fighter_ammo_units:.0f} • bombs {state.air.bomb_units} • torpedoes {state.air.torpedo_units}")
    return lines


def combat_to_dict(state: NavalCombatState) -> dict:
    return {
        "general_quarters": state.general_quarters,
        "training_mode": state.training_mode,
        "raid_active": state.raid_active,
        "raid_generation": state.raid_generation,
        "elapsed_seconds": state.elapsed_seconds,
        "selected_track": state.selected_track,
        "selected_battery": state.selected_battery,
        "solution_quality": state.solution_quality,
        "solution_track": state.solution_track,
        "solution_age": state.solution_age,
        "radar_readiness": state.radar_readiness,
        "lookout_readiness": state.lookout_readiness,
        "fire_control_readiness": state.fire_control_readiness,
        "magazine_readiness": state.magazine_readiness,
        "ammo_hoist_ready": state.ammo_hoist_ready,
        "air": state.air.__dict__.copy(),
        "tracks": {k: v.__dict__.copy() for k,v in state.tracks.items()},
        "batteries": {k: v.__dict__.copy() for k,v in state.batteries.items()},
        "enemy_destroyed": state.enemy_destroyed,
        "attacks_defeated": state.attacks_defeated,
        "hits_taken": state.hits_taken,
        "damage_taken": state.damage_taken,
        "rounds_fired": state.rounds_fired,
        "training_score": state.training_score,
        "log": state.log[:80],
    }


def combat_from_dict(data: Optional[dict]) -> NavalCombatState:
    state = create_naval_combat()
    if not isinstance(data, dict) or not data:
        return state
    scalar = (
        "general_quarters","training_mode","raid_active","raid_generation","elapsed_seconds",
        "selected_track","selected_battery","solution_quality","solution_track","solution_age",
        "radar_readiness","lookout_readiness","fire_control_readiness","magazine_readiness",
        "ammo_hoist_ready","enemy_destroyed","attacks_defeated","hits_taken","damage_taken",
        "rounds_fired","training_score",
    )
    for key in scalar:
        if key in data:
            setattr(state,key,data[key])
    air = data.get("air", {})
    for key in CarrierAirState.__dataclass_fields__:
        if key in air:
            setattr(state.air,key,air[key])
    tracks = {}
    for key, raw in data.get("tracks", {}).items():
        try:
            allowed={f for f in CombatTrack.__dataclass_fields__}
            tracks[key]=CombatTrack(**{k:v for k,v in raw.items() if k in allowed})
        except Exception:
            continue
    state.tracks = tracks
    for key, raw in data.get("batteries", {}).items():
        if key not in state.batteries:
            continue
        for field_name in WeaponBattery.__dataclass_fields__:
            if field_name in raw:
                setattr(state.batteries[key], field_name, raw[field_name])
    if state.selected_battery not in state.batteries:
        state.selected_battery="FIVE_INCH"
    state.log = list(data.get("log", state.log))[:80]
    return state
