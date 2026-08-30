from __future__ import annotations

"""War Simulator v1.6 physical-world presentation and environment layer.

This module intentionally separates visual/interaction simulation from historical claims.
Weather presets, animation speeds, particle counts, ladder geometry, and hull faceting are
training/gameplay approximations unless separately sourced by a historical scenario manifest.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Tuple
import math


WEATHER_MODES = ("CLEAR", "OVERCAST", "RAIN", "STORM")


@dataclass
class PhysicalWorldState:
    weather_mode: str = "CLEAR"
    cloud_cover: float = 0.22
    rain_intensity: float = 0.0
    fog_density: float = 0.04
    daylight: float = 0.45
    sun_azimuth_deg: float = 78.0
    radar_angle_deg: float = 0.0
    propeller_phase_deg: float = 0.0
    ventilation_fan_phase_deg: float = 0.0
    hatch_fraction: Dict[str, float] = field(default_factory=dict)
    elapsed: float = 0.0
    lightning_flash: float = 0.0
    weather_changes: int = 0


def physical_world_from_dict(data: dict | None) -> PhysicalWorldState:
    s = PhysicalWorldState()
    if not data:
        return s
    for key, value in data.items():
        if hasattr(s, key):
            setattr(s, key, value)
    if s.weather_mode not in WEATHER_MODES:
        s.weather_mode = "CLEAR"
    return s


def physical_world_to_dict(state: PhysicalWorldState) -> dict:
    return asdict(state)


def cycle_weather(state: PhysicalWorldState) -> str:
    idx = WEATHER_MODES.index(state.weather_mode) if state.weather_mode in WEATHER_MODES else 0
    state.weather_mode = WEATHER_MODES[(idx + 1) % len(WEATHER_MODES)]
    state.weather_changes += 1
    return f"Training weather set to {state.weather_mode}."


def _weather_targets(mode: str, sea_state: int) -> Tuple[float, float, float]:
    # cloud cover, rain, fog
    table = {
        "CLEAR": (0.16, 0.00, 0.02),
        "OVERCAST": (0.76, 0.00, 0.08),
        "RAIN": (0.88, 0.58, 0.14),
        "STORM": (0.98, 0.95, 0.22),
    }
    c, r, f = table.get(mode, table["CLEAR"])
    sea = max(0, min(9, int(sea_state)))
    if sea >= 6:
        c = max(c, 0.70)
        r = max(r, (sea - 5) * 0.10)
        f = max(f, 0.10)
    return min(1.0, c), min(1.0, r), min(0.60, f)


def advance_physical_world(
    state: PhysicalWorldState,
    dt: float,
    minute_of_day: int,
    sea_state: int,
    ship_speed_knots: float,
    hatch_targets: Dict[str, bool],
    radar_operational: bool = True,
) -> None:
    dt = max(0.0, float(dt))
    state.elapsed += dt

    # Continuous time-of-day lighting. Sunrise/sunset curve is intentionally generic.
    hour = (minute_of_day % 1440) / 60.0
    solar = math.sin((hour - 6.0) / 24.0 * math.tau)
    state.daylight = max(0.04, min(1.0, 0.50 + 0.56 * solar))
    state.sun_azimuth_deg = (hour / 24.0 * 360.0 + 90.0) % 360.0

    tc, tr, tf = _weather_targets(state.weather_mode, sea_state)
    blend = min(1.0, dt * 0.35)
    state.cloud_cover += (tc - state.cloud_cover) * blend
    state.rain_intensity += (tr - state.rain_intensity) * blend
    state.fog_density += (tf - state.fog_density) * blend

    # Animated ship equipment.
    if radar_operational:
        state.radar_angle_deg = (state.radar_angle_deg + dt * 52.0) % 360.0
    state.propeller_phase_deg = (state.propeller_phase_deg + dt * (15.0 + abs(ship_speed_knots) * 28.0)) % 360.0
    state.ventilation_fan_phase_deg = (state.ventilation_fan_phase_deg + dt * 85.0) % 360.0

    # Watertight-door visuals ease to target rather than snapping.
    for key, opened in hatch_targets.items():
        current = float(state.hatch_fraction.get(key, 1.0 if opened else 0.0))
        target = 1.0 if opened else 0.0
        speed = dt * 1.75
        if current < target:
            current = min(target, current + speed)
        else:
            current = max(target, current - speed)
        state.hatch_fraction[key] = current

    # Deterministic lightning pulses in storm mode; no random replay instability.
    if state.weather_mode == "STORM" and state.rain_intensity > 0.75:
        phase = state.elapsed % 13.7
        state.lightning_flash = 1.0 if 0.0 <= phase < 0.12 else (0.45 if 0.22 <= phase < 0.30 else 0.0)
    else:
        state.lightning_flash = 0.0


def sky_colors(state: PhysicalWorldState) -> Tuple[str, str, str]:
    """Return sky-top, sky-horizon, sea colors from daylight/weather state."""
    d = state.daylight
    # Hand-tuned palettes chosen for Tk visibility, not photometric accuracy.
    if d < 0.18:
        top, horizon, sea = "#07111f", "#152334", "#071c2b"
    elif d < 0.42:
        top, horizon, sea = "#1e3651", "#9b6858", "#17354b"
    else:
        top, horizon, sea = "#345d7d", "#7896a8", "#17435c"
    if state.cloud_cover > 0.70:
        top = "#293947" if d > 0.25 else "#0d1721"
        horizon = "#52616b" if d > 0.25 else "#1d2730"
        sea = "#163746"
    if state.lightning_flash > 0:
        top = horizon = "#c7d4df"
    return top, horizon, sea


def damage_world_pose(compartment) -> Tuple[float, float, float]:
    """Coarsely map survivability compartment coordinates into the seamless training carrier."""
    # Import locally to avoid circular module dependency at import time.
    from .openworld import LAYERS, SHIP_ORIGIN_X, SHIP_ORIGIN_Y, SHIP_LENGTH_M, SHIP_WIDTH_M

    # Longitudinal is -1 bow .. +1 stern; v2.5 maps it across the real-scale carrier.
    lx = SHIP_LENGTH_M * .50 + float(compartment.longitudinal) * (SHIP_LENGTH_M * .42)
    ly = SHIP_WIDTH_M * .50 + float(compartment.transverse) * (SHIP_WIDTH_M * .34)
    deck = compartment.deck if compartment.deck in LAYERS else "HANGAR"
    floor = LAYERS[deck].floor_z
    return SHIP_ORIGIN_X + lx, SHIP_ORIGIN_Y + ly, floor


def environment_summary(state: PhysicalWorldState, minute_of_day: int) -> str:
    h = (minute_of_day % 1440) // 60
    m = minute_of_day % 60
    return (
        f"ENV {h:02d}:{m:02d} • {state.weather_mode} • cloud {state.cloud_cover*100:.0f}% • "
        f"rain {state.rain_intensity*100:.0f}% • fog {state.fog_density*100:.0f}% • daylight {state.daylight*100:.0f}%"
    )
