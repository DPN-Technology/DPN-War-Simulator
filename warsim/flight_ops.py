from __future__ import annotations

"""v1.7 first-person carrier flight runtime.

The flight coefficients are intentionally training/gameplay calibration rather than archival
F4F/SBD/TBD performance data. Historical air-group identities remain sourced separately.
"""

from dataclasses import dataclass, asdict
import math
from typing import Optional, Tuple


@dataclass
class FlightState:
    active: bool = False
    aircraft_key: str = ""
    aircraft_type: str = ""
    on_deck: bool = False
    engine_running: bool = False
    throttle: float = 0.0
    brakes: bool = True
    gear_down: bool = True
    flaps_down: bool = False
    east_nm: float = 0.0
    north_nm: float = 0.0
    altitude_ft: float = 0.0
    heading_deg: float = 90.0
    airspeed_knots: float = 0.0
    pitch_deg: float = 0.0
    bank_deg: float = 0.0
    vertical_speed_fpm: float = 0.0
    fuel_pct: float = 100.0
    distance_nm: float = 0.0
    airborne_seconds: float = 0.0
    landings: int = 0
    takeoffs: int = 0
    last_event: str = ""
    # v1.8 cockpit combat/survival state (training calibration).
    gun_ammo: int = 0
    bombs: int = 0
    torpedoes: int = 0
    airframe_health: float = 100.0
    engine_health: float = 100.0
    control_health: float = 100.0
    pilot_health: float = 100.0
    damage_cooldown: float = 0.0
    emergency_state: str = ""


def flight_from_dict(data: dict | None) -> FlightState:
    s = FlightState()
    if not data:
        return s
    for k, v in data.items():
        if hasattr(s, k):
            setattr(s, k, v)
    return s


def flight_to_dict(state: FlightState) -> dict:
    return asdict(state)


def enter_cockpit(state: FlightState, aircraft, carrier_e: float, carrier_n: float, carrier_heading: float) -> Tuple[bool, str]:
    if state.active:
        return False, "Already in a cockpit."
    if getattr(aircraft, "status", "") not in ("SPOTTED", "GROUNDED") or getattr(aircraft, "deck", "") != "FLIGHT":
        return False, "Aircraft must be physically spotted on the Flight Deck before cockpit entry."
    if getattr(aircraft, "condition", 0.0) < 55.0:
        return False, "Aircraft is not serviceable enough for flight."
    state.active = True
    state.aircraft_key = aircraft.key
    state.aircraft_type = aircraft.aircraft_type
    state.on_deck = True
    state.engine_running = False
    state.throttle = 0.0
    state.brakes = True
    state.gear_down = True
    state.flaps_down = False
    state.east_nm = carrier_e
    state.north_nm = carrier_n
    state.altitude_ft = 0.0
    state.heading_deg = carrier_heading % 360.0
    state.airspeed_knots = 0.0
    state.pitch_deg = 0.0
    state.bank_deg = 0.0
    state.vertical_speed_fpm = 0.0
    state.fuel_pct = float(getattr(aircraft, "fuel_pct", 100.0))
    state.gun_ammo = 240 if "F4F" in state.aircraft_type else 180
    state.bombs = 1 if "SBD" in state.aircraft_type else 0
    state.torpedoes = 1 if "TBD" in state.aircraft_type else 0
    state.airframe_health = max(75.0, state.airframe_health)
    state.engine_health = max(75.0, state.engine_health)
    state.control_health = max(75.0, state.control_health)
    state.pilot_health = max(75.0, state.pilot_health)
    state.damage_cooldown = 0.0
    state.emergency_state = ""
    state.last_event = f"Entered {aircraft.key} cockpit on Flight Deck."
    return True, state.last_event


def exit_cockpit(state: FlightState) -> Tuple[bool, str]:
    if not state.active:
        return False, "Not in an aircraft."
    if not state.on_deck or state.airspeed_knots > 4.0:
        return False, "Cannot leave cockpit until aircraft is stopped on deck."
    state.active = False
    state.last_event = "Exited cockpit on Flight Deck."
    return True, state.last_event


def toggle_engine(state: FlightState) -> str:
    if not state.active or not state.on_deck:
        return "Engine control unavailable."
    state.engine_running = not state.engine_running
    if not state.engine_running:
        state.throttle = 0.0
    state.last_event = f"Engine {'STARTED' if state.engine_running else 'SECURED'}."
    return state.last_event


def adjust_throttle(state: FlightState, delta: float) -> str:
    if not state.active:
        return "No cockpit controls active."
    if not state.engine_running and delta > 0:
        return "Start the engine first (I)."
    state.throttle = max(0.0, min(1.0, state.throttle + delta))
    return f"Throttle {state.throttle*100:.0f}%"


def toggle_gear(state: FlightState) -> str:
    if not state.active:
        return "No cockpit controls active."
    if state.on_deck:
        state.gear_down = True
        return "Landing gear locked DOWN while on deck."
    state.gear_down = not state.gear_down
    return f"Landing gear {'DOWN' if state.gear_down else 'UP'}."


def toggle_flaps(state: FlightState) -> str:
    if not state.active:
        return "No cockpit controls active."
    state.flaps_down = not state.flaps_down
    return f"Flaps {'DOWN' if state.flaps_down else 'UP'}."


def set_brakes(state: FlightState, enabled: bool) -> None:
    state.brakes = bool(enabled)


def flight_range_to_carrier(state: FlightState, carrier_e: float, carrier_n: float) -> float:
    return math.hypot(state.east_nm - carrier_e, state.north_nm - carrier_n)


def advance_flight(
    state: FlightState,
    dt: float,
    carrier_e: float,
    carrier_n: float,
    carrier_heading: float,
    carrier_speed: float,
    wind_over_deck: float,
    sea_state: int,
    roll_input: float = 0.0,
    pitch_input: float = 0.0,
    yaw_input: float = 0.0,
) -> Optional[str]:
    if not state.active:
        return None
    dt = max(0.0, min(0.08, float(dt)))
    # Smooth pilot controls.
    state.bank_deg += (max(-1.0, min(1.0, roll_input))*42.0 - state.bank_deg) * min(1.0, dt*2.8)
    state.pitch_deg += (max(-1.0, min(1.0, pitch_input))*18.0 - state.pitch_deg) * min(1.0, dt*2.6)
    if state.on_deck:
        state.heading_deg = carrier_heading % 360.0
        state.east_nm = carrier_e
        state.north_nm = carrier_n
        state.altitude_ft = 0.0
        target = (72.0 * state.throttle if state.engine_running else 0.0)
        if state.brakes:
            target = min(target, 2.0)
        state.airspeed_knots += (target - state.airspeed_knots) * min(1.0, dt*1.7)
        state.vertical_speed_fpm = 0.0
        launch_speed = max(48.0, 62.0 - wind_over_deck*0.35)
        if state.engine_running and not state.brakes and state.throttle >= .82 and state.airspeed_knots >= launch_speed:
            state.on_deck = False
            state.takeoffs += 1
            state.altitude_ft = 18.0
            state.pitch_deg = max(state.pitch_deg, 5.0)
            state.airspeed_knots = max(72.0, state.airspeed_knots + wind_over_deck*.25)
            state.last_event = "AIRBORNE — carrier takeoff complete."
            return state.last_event
        return None

    # Airborne simplified fixed-wing model.
    max_speed = 185.0
    min_power_speed = 58.0
    engine_factor = max(0.18, min(1.0, state.engine_health / 100.0))
    target_speed = min_power_speed + state.throttle * (max_speed-min_power_speed) * engine_factor
    drag = 7.0 if state.gear_down else 0.0
    if state.flaps_down:
        drag += 5.0
    target_speed = max(45.0, target_speed-drag)
    state.airspeed_knots += (target_speed-state.airspeed_knots)*min(1.0,dt*.55)
    control_factor = max(0.25, min(1.0, state.control_health / 100.0))
    state.heading_deg = (state.heading_deg + (state.bank_deg/42.0)*25.0*dt*control_factor + yaw_input*7.0*dt*control_factor) % 360.0
    # Pitch and power drive climb; aggressive bank reduces lift.
    bank_loss = abs(state.bank_deg)/42.0*350.0
    state.vertical_speed_fpm = state.pitch_deg*105.0 + (state.throttle-.52)*420.0 - bank_loss
    state.altitude_ft = max(0.0, state.altitude_ft + state.vertical_speed_fpm/60.0*dt)
    distance = state.airspeed_knots * dt / 3600.0
    r = math.radians(state.heading_deg)
    state.east_nm += math.sin(r)*distance
    state.north_nm += math.cos(r)*distance
    state.distance_nm += distance
    state.airborne_seconds += dt
    burn = dt * (.025 + state.throttle*.055)
    state.fuel_pct = max(0.0, state.fuel_pct-burn)
    if state.fuel_pct <= 0.0:
        state.engine_running = False
        state.throttle = 0.0
        state.last_event = "ENGINE STOPPED — fuel exhausted."
        return state.last_event
    return None


def attempt_recovery(state: FlightState, carrier_e: float, carrier_n: float, carrier_heading: float, wind_over_deck: float, deck_safe: bool = True) -> Tuple[bool, str]:
    if not state.active or state.on_deck:
        return False, "Aircraft is not airborne."
    rng = flight_range_to_carrier(state, carrier_e, carrier_n)
    if not deck_safe:
        return False, "Recovery denied: flight deck unsafe."
    if wind_over_deck < 7.0:
        return False, "Recovery denied: insufficient wind over deck."
    if rng > 0.55:
        return False, f"Too far from carrier for recovery ({rng:.2f} nm)."
    if state.altitude_ft > 140.0:
        return False, f"Too high for recovery ({state.altitude_ft:.0f} ft)."
    if not state.gear_down or not state.flaps_down:
        return False, "Recovery configuration incomplete: gear and flaps must be DOWN."
    if not 48.0 <= state.airspeed_knots <= 98.0:
        return False, f"Airspeed outside recovery envelope ({state.airspeed_knots:.0f} kt)."
    # Require broadly aligned heading, but keep training tolerances generous.
    delta = abs((state.heading_deg-carrier_heading+180)%360-180)
    if delta > 55.0:
        return False, f"Approach not aligned with carrier ({delta:.0f}° heading error)."
    state.on_deck = True
    state.east_nm = carrier_e
    state.north_nm = carrier_n
    state.heading_deg = carrier_heading
    state.altitude_ft = 0.0
    state.airspeed_knots = min(16.0, state.airspeed_knots*.18)
    state.throttle = 0.15
    state.brakes = True
    state.landings += 1
    state.last_event = "RECOVERED ABOARD — arrested landing complete."
    return True, state.last_event


def cockpit_summary(state: FlightState, carrier_e: float, carrier_n: float) -> str:
    rng = flight_range_to_carrier(state, carrier_e, carrier_n)
    return (
        f"{state.aircraft_key or 'NO AIRCRAFT'} • {'DECK' if state.on_deck else 'AIRBORNE'} • "
        f"HDG {state.heading_deg:03.0f}° • IAS {state.airspeed_knots:.0f}kt • ALT {state.altitude_ft:.0f}ft • "
        f"THR {state.throttle*100:.0f}% • FUEL {state.fuel_pct:.0f}% • ENTERPRISE {rng:.2f}nm"
    )
