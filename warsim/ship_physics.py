from __future__ import annotations

"""War Simulator v0.9 ship-motion and seamanship physics.

The coefficients in this module are training-simulation tuning values, not a claim that they
reproduce a specific classified or archival maneuvering trial for USS Enterprise (CV-6).
Historical events remain in the sourced historical layer; this module provides continuous
rigid-vessel response for gameplay: propulsion, rudder response, current, wind, sea motion,
anchor/mooring state, grounding risk and player balance cues.
"""

from dataclasses import dataclass, field
import math
from typing import List, Tuple

KNOT_TO_MPS = 0.514444
G = 9.80665


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _wrap_deg(v: float) -> float:
    return v % 360.0


def _signed_angle(a: float) -> float:
    return (a + 180.0) % 360.0 - 180.0


def _vector_from_nav(direction_deg: float, magnitude: float) -> Tuple[float, float]:
    # 0° = north (+y); 90° = east (+x)
    r = math.radians(direction_deg)
    return math.sin(r) * magnitude, math.cos(r) * magnitude


def _nav_from_vector(x: float, y: float) -> Tuple[float, float]:
    mag = math.hypot(x, y)
    if mag < 1e-9:
        return 0.0, 0.0
    return _wrap_deg(math.degrees(math.atan2(x, y))), mag


@dataclass
class ShipPhysicsState:
    # Global navigation state in a local training sea room. Interior geometry remains vessel-local.
    east_nm: float = 0.0
    north_nm: float = 0.0
    heading_deg: float = 90.0
    course_over_ground_deg: float = 90.0
    speed_knots: float = 0.0
    speed_over_ground_knots: float = 0.0
    engine_order: float = 0.0       # -0.35 backing through +1.0 full ahead
    rudder_deg: float = 0.0         # port negative, starboard positive
    yaw_rate_deg_s: float = 0.0
    turning_radius_nm: float = 999.0

    # Training-calibrated vessel constants.
    max_ahead_knots: float = 32.0
    max_back_knots: float = 8.0
    max_rudder_deg: float = 35.0
    propulsion_integrity: float = 100.0
    steering_integrity: float = 100.0
    hull_integrity: float = 100.0
    draft_m: float = 8.0

    # Environment.
    wind_from_deg: float = 120.0
    wind_speed_knots: float = 14.0
    current_to_deg: float = 65.0
    current_speed_knots: float = 0.8
    wave_from_deg: float = 135.0
    sea_state: int = 3

    # Six-degree-motion cues used by the first-person renderer/player balance model.
    roll_deg: float = 0.0
    pitch_deg: float = 0.0
    heave_m: float = 0.0
    roll_rate_deg_s: float = 0.0
    pitch_rate_deg_s: float = 0.0
    lateral_g: float = 0.0
    longitudinal_g: float = 0.0
    balance_load: float = 0.0
    wave_phase: float = 0.0

    # Seamanship state.
    moored: bool = True
    anchor_deployed: bool = False
    grounded: bool = False
    grounding_load: float = 0.0
    collision_alarm: bool = False
    underway_seconds: float = 0.0
    distance_nm: float = 0.0
    log: List[str] = field(default_factory=lambda: [
        "Ship physics initialized in training sea room. Vessel is moored; gangway available."
    ])

    @property
    def at_home_berth(self) -> bool:
        return math.hypot(self.east_nm, self.north_nm) <= 0.08

    @property
    def underway(self) -> bool:
        return not self.moored and (abs(self.speed_knots) > 0.05 or abs(self.engine_order) > 0.01)


def create_ship_physics() -> ShipPhysicsState:
    return ShipPhysicsState()


def engine_label(order: float) -> str:
    if order <= -0.05:
        return "BACKING"
    if order < 0.08:
        return "STOP"
    if order < 0.24:
        return "DEAD SLOW AHEAD"
    if order < 0.48:
        return "ONE-THIRD AHEAD"
    if order < 0.82:
        return "TWO-THIRDS AHEAD"
    return "FULL AHEAD"


def set_engine_order(s: ShipPhysicsState, order: float) -> str:
    order = _clamp(order, -0.35, 1.0)
    if s.moored and abs(order) > 0.01:
        return "Engine order rejected while moored. Cast off first."
    if s.anchor_deployed and order > 0.35:
        return "Engine order limited while anchor is deployed. Weigh anchor first."
    s.engine_order = order
    msg = f"Engine telegraph: {engine_label(order)}."
    s.log.insert(0, msg)
    return msg


def set_rudder(s: ShipPhysicsState, rudder_deg: float) -> str:
    s.rudder_deg = _clamp(rudder_deg, -s.max_rudder_deg, s.max_rudder_deg)
    side = "PORT" if s.rudder_deg < -0.1 else "STARBOARD" if s.rudder_deg > 0.1 else "MIDSHIPS"
    msg = f"Helm: {side} {abs(s.rudder_deg):.0f}°." if side != "MIDSHIPS" else "Helm: rudder amidships."
    s.log.insert(0, msg)
    return msg


def cast_off(s: ShipPhysicsState) -> Tuple[bool, str]:
    if not s.moored:
        return False, "Mooring lines are already clear; vessel is not secured to the berth."
    if abs(s.speed_knots) > 0.2:
        return False, "Cannot cast off with residual vessel motion."
    s.moored = False
    s.anchor_deployed = False
    msg = "SEA DETAIL: mooring lines clear. Gangway disconnected; vessel free to maneuver."
    s.log.insert(0, msg)
    return True, msg


def secure_to_berth(s: ShipPhysicsState) -> Tuple[bool, str]:
    if s.moored:
        return True, "Vessel is already secured to the berth."
    if not s.at_home_berth:
        return False, f"Cannot moor: berth is {math.hypot(s.east_nm,s.north_nm):.2f} nm away."
    if abs(s.speed_knots) > 0.5:
        return False, "Cannot moor above 0.5 knots. Stop the ship alongside first."
    s.moored = True
    s.engine_order = 0.0
    s.speed_knots = 0.0
    s.speed_over_ground_knots = 0.0
    s.rudder_deg = 0.0
    msg = "SEA DETAIL: vessel secured to berth. Gangway connected."
    s.log.insert(0, msg)
    return True, msg


def toggle_anchor(s: ShipPhysicsState) -> Tuple[bool, str]:
    if s.moored:
        return False, "Anchor operation unnecessary while secured to the berth."
    if not s.anchor_deployed:
        if abs(s.speed_knots) > 4.0:
            return False, "Anchor deployment rejected above 4 knots. Slow the ship first."
        s.anchor_deployed = True
        msg = "Anchor let go. Vessel will sheer and decelerate as the cable takes strain."
    else:
        s.anchor_deployed = False
        msg = "Anchor weighed and clear. Vessel is free to maneuver."
    s.log.insert(0, msg)
    return True, msg


def training_depth_m(east_nm: float, north_nm: float) -> float:
    """Synthetic training bathymetry. Deep water except for one charted shoal and harbor edge."""
    depth = 85.0
    # Charted shoal east-northeast of the berth, intentionally avoidable.
    d = math.hypot(east_nm - 2.8, north_nm - 1.8)
    if d < 1.25:
        depth = min(depth, 4.0 + 15.0 * d)
    # Harbor shallows away from the marked departure channel.
    if abs(east_nm) < 0.75 and north_nm < -0.45:
        depth = min(depth, 5.5 + max(0.0, (north_nm + 1.0) * 4.0))
    return max(2.0, depth)


def _update_grounding(s: ShipPhysicsState, dt: float) -> None:
    depth = training_depth_m(s.east_nm, s.north_nm)
    if depth < s.draft_m and abs(s.speed_knots) > 0.25:
        penetration = s.draft_m - depth
        impact = penetration * max(0.2, abs(s.speed_knots)) * 0.025
        s.grounded = True
        s.grounding_load = min(100.0, s.grounding_load + impact * dt * 4.0)
        s.hull_integrity = max(0.0, s.hull_integrity - impact * dt * 0.55)
        s.speed_knots *= max(0.0, 1.0 - min(0.8, penetration * 0.08 * dt))
        if not s.collision_alarm:
            s.collision_alarm = True
            s.log.insert(0, f"GROUNDING ALARM: charted depth {depth:.1f} m below simulated draft {s.draft_m:.1f} m.")
    elif s.grounded:
        # Backing off at low power reduces grounding load; otherwise ship remains pinned.
        if s.engine_order < -0.05:
            s.grounding_load = max(0.0, s.grounding_load - 7.5 * dt)
            if s.grounding_load <= 0.2 and depth >= s.draft_m * 0.9:
                s.grounded = False
                s.collision_alarm = False
                s.log.insert(0, "Grounding load cleared; vessel backed into navigable water.")
        else:
            s.speed_knots *= max(0.0, 1.0 - dt * 0.8)


def sync_operational_damage(s: ShipPhysicsState, shipboard) -> None:
    """Tie existing equipment runtime faults into steering/propulsion capability."""
    def health(key: str) -> float:
        rt = getattr(shipboard, "equipment_runtime", {}).get(key)
        if rt is None:
            return 100.0
        penalty = 35.0 if getattr(rt, "fault", "") else 0.0
        return _clamp(getattr(rt, "health", 100.0) - penalty, 10.0, 100.0)

    s.steering_integrity = min(health("HELM"), health("RADAR_CONSOLE") + 15.0)
    s.propulsion_integrity = min(health("ENG_CONSOLE"), health("LOAD_BOARD"))


def advance_ship_physics(s: ShipPhysicsState, dt: float) -> None:
    dt = _clamp(dt, 0.001, 0.15)
    old_speed = s.speed_knots
    old_roll = s.roll_deg
    old_pitch = s.pitch_deg

    if s.moored:
        s.engine_order = 0.0
        s.speed_knots += (0.0 - s.speed_knots) * min(1.0, dt * 3.0)
        s.yaw_rate_deg_s = 0.0
    else:
        integrity = _clamp(s.propulsion_integrity / 100.0, 0.05, 1.0)
        if s.engine_order >= 0:
            target = s.max_ahead_knots * (s.engine_order ** 0.72) * integrity
            tau = 70.0 + 55.0 * max(0.0, s.speed_knots / max(1.0, s.max_ahead_knots))
        else:
            target = -s.max_back_knots * ((-s.engine_order / 0.35) ** 0.8) * integrity
            tau = 48.0
        accel_knots_s = _clamp((target - s.speed_knots) / tau, -0.075, 0.055)
        s.speed_knots += accel_knots_s * dt

        # Anchor drag becomes dominant once the ship is nearly stopped.
        if s.anchor_deployed:
            drag = min(abs(s.speed_knots), (0.08 + abs(s.speed_knots) * 0.09) * dt)
            s.speed_knots -= math.copysign(drag, s.speed_knots) if abs(s.speed_knots) > 1e-6 else 0.0
            if abs(s.speed_knots) < 0.06:
                s.speed_knots = 0.0

        speed_frac = _clamp(abs(s.speed_knots) / max(1.0, s.max_ahead_knots), 0.0, 1.2)
        steer = (s.rudder_deg / s.max_rudder_deg) * (s.steering_integrity / 100.0)
        # Training-calibrated carrier yaw response: very little authority at low speed.
        s.yaw_rate_deg_s = steer * 0.52 * (speed_frac ** 1.25)
        if s.speed_knots < -0.1:
            s.yaw_rate_deg_s *= -0.65
        # Small wind-induced weather helm at low speed.
        rel_wind = math.radians(_signed_angle(s.wind_from_deg - s.heading_deg))
        s.yaw_rate_deg_s += math.sin(rel_wind) * s.wind_speed_knots * 0.0008 * (1.0 - min(1.0, speed_frac))
        s.heading_deg = _wrap_deg(s.heading_deg + s.yaw_rate_deg_s * dt)

        # Through-water velocity + current gives COG/SOG.
        vx, vy = _vector_from_nav(s.heading_deg, s.speed_knots)
        cx, cy = _vector_from_nav(s.current_to_deg, s.current_speed_knots)
        gvx, gvy = vx + cx, vy + cy
        s.course_over_ground_deg, s.speed_over_ground_knots = _nav_from_vector(gvx, gvy)
        de = gvx * dt / 3600.0
        dn = gvy * dt / 3600.0
        s.east_nm += de
        s.north_nm += dn
        s.distance_nm += math.hypot(de, dn)
        s.underway_seconds += dt

        omega = math.radians(s.yaw_rate_deg_s)
        v_mps = abs(s.speed_knots) * KNOT_TO_MPS
        s.turning_radius_nm = 999.0 if abs(omega) < 1e-5 else abs(v_mps / omega) / 1852.0
        s.lateral_g = _clamp((v_mps * omega) / G, -0.25, 0.25)
        dv_mps = (s.speed_knots - old_speed) * KNOT_TO_MPS
        s.longitudinal_g = _clamp((dv_mps / dt) / G, -0.18, 0.18)

    # Sea motion is active even when moored, but much smaller alongside.
    s.wave_phase += dt * (0.52 + s.sea_state * 0.035)
    rel_wave = math.radians(_signed_angle(s.wave_from_deg - s.heading_deg))
    sea = _clamp(float(s.sea_state), 0.0, 9.0)
    moor_factor = 0.28 if s.moored else 1.0
    beam = abs(math.sin(rel_wave))
    head = abs(math.cos(rel_wave))
    roll_amp = moor_factor * (0.22 + sea * 0.68) * (0.35 + 0.95 * beam)
    pitch_amp = moor_factor * (0.15 + sea * 0.34) * (0.35 + 0.9 * head)
    target_roll = roll_amp * math.sin(s.wave_phase * 1.18) + math.degrees(math.atan2(s.lateral_g * G, G)) * 0.35
    target_pitch = pitch_amp * math.sin(s.wave_phase * 0.82 + 0.8) - s.longitudinal_g * 28.0
    smooth = min(1.0, dt * 2.8)
    s.roll_deg += (target_roll - s.roll_deg) * smooth
    s.pitch_deg += (target_pitch - s.pitch_deg) * smooth
    s.heave_m = moor_factor * sea * 0.055 * math.sin(s.wave_phase * 0.72)
    s.roll_rate_deg_s = (s.roll_deg - old_roll) / dt
    s.pitch_rate_deg_s = (s.pitch_deg - old_pitch) / dt
    s.balance_load = _clamp(abs(s.roll_deg) / 12.0 + abs(s.pitch_deg) / 8.0 + abs(s.lateral_g) * 12.0 + abs(s.longitudinal_g) * 9.0, 0.0, 3.0)

    _update_grounding(s, dt)


def player_motion_modifiers(s: ShipPhysicsState) -> Tuple[float, float]:
    """Return movement speed multiplier and local athwartship drift m/s-like world units/s."""
    speed_mul = _clamp(1.0 - max(0.0, s.balance_load - 0.35) * 0.18, 0.48, 1.0)
    drift = _clamp((s.roll_deg / 18.0 + s.lateral_g * 7.0) * 0.22, -0.42, 0.42)
    return speed_mul, drift


def physics_summary(s: ShipPhysicsState) -> str:
    status = "MOORED" if s.moored else "ANCHORED" if s.anchor_deployed else "UNDERWAY"
    if s.grounded:
        status = "GROUNDED"
    return (
        f"{status} | HDG {s.heading_deg:03.0f}° | {s.speed_knots:4.1f} kt STW | "
        f"COG {s.course_over_ground_deg:03.0f}° / {s.speed_over_ground_knots:4.1f} kt | "
        f"Rudder {s.rudder_deg:+.0f}° | {engine_label(s.engine_order)}"
    )
