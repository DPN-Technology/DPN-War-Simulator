from __future__ import annotations
from dataclasses import asdict
from math import sin, radians
from .data import PROMOTION_REQUIREMENTS, NAVAL_RANKS
from .models import CareerProfile, BridgeState, DamageState, CrewMember


def promotion_status(profile: CareerProfile) -> dict:
    values = {
        "Testing": profile.written_exam,
        "Practical examinations": profile.practical_exam,
        "Performance reviews": profile.performance_review,
        "Leadership evaluations": profile.leadership_eval,
        "Recommendations": profile.recommendations,
        "Training schools": profile.schools_completed,
        "Time in service": profile.duty_periods,
        "Experience": profile.xp,
        "Mission performance": profile.mission_performance,
    }
    return {
        k: {"value": values[k], "required": req, "met": values[k] >= req}
        for k, req in PROMOTION_REQUIREMENTS.items()
    }


def can_promote(profile: CareerProfile) -> bool:
    return profile.rank_index < len(NAVAL_RANKS) - 1 and all(v["met"] for v in promotion_status(profile).values())


def promote(profile: CareerProfile) -> tuple[bool, str]:
    if profile.rank_index >= len(NAVAL_RANKS) - 1:
        return False, "You already hold the highest rank in the current naval career ladder."
    if not can_promote(profile):
        missing = [k for k, v in promotion_status(profile).items() if not v["met"]]
        return False, "Promotion denied. Outstanding requirements: " + ", ".join(missing)
    old = profile.rank
    profile.rank_index += 1
    profile.recommendations = max(0, profile.recommendations - 1)
    profile.schools_completed = max(0, profile.schools_completed - 1)
    profile.written_exam *= 0.85
    profile.practical_exam *= 0.85
    profile.duty_periods = max(0, profile.duty_periods - 2)
    profile.xp = max(0, profile.xp - 250)
    profile.add_log(f"Promoted from {old} to {profile.rank} after board review.")
    return True, f"Promotion approved: {old} → {profile.rank}"


def apply_written_exam(profile: CareerProfile, score: float, topic_hits: dict[str, int]) -> None:
    profile.written_exam = max(profile.written_exam, score)
    profile.xp += int(score * 1.2)
    profile.schools_completed = max(profile.schools_completed, 1 if score >= 70 else profile.schools_completed)
    for topic, hits in topic_hits.items():
        profile.topic_mastery[topic] = min(100, profile.topic_mastery.get(topic, 0) + hits * 12)
    profile.performance_review = min(100, profile.performance_review + (4 if score >= 70 else 1))
    profile.add_log(f"Helmsman written examination completed: {score:.0f}%.")


def update_bridge(state: BridgeState, dt: float) -> BridgeState:
    state.elapsed += dt
    # Rudder authority falls slightly as sea state grows; wind induces drift.
    turn_rate = state.rudder * (0.16 + state.speed / 100.0) * max(0.55, 1.0 - state.sea_state * 0.035)
    wind_drift = sin(radians(state.wind_heading - state.heading)) * state.wind_speed * 0.008
    state.heading = (state.heading + (turn_rate + wind_drift) * dt) % 360
    state.speed += ((state.throttle * 24.0) - state.speed) * min(1.0, dt * 0.6)
    err = abs(((state.ordered_heading - state.heading + 180) % 360) - 180)
    if err <= 5:
        state.held_seconds += dt
        state.score = min(100.0, state.score + dt * 0.25)
    else:
        state.held_seconds = max(0.0, state.held_seconds - dt * 0.4)
        state.score = max(0.0, state.score - dt * min(1.8, err / 90.0))
    return state


def bridge_next_order(state: BridgeState) -> None:
    sequence = [45.0, 90.0, 135.0, 270.0]
    state.completed_orders += 1
    state.held_seconds = 0.0
    state.ordered_heading = sequence[state.completed_orders % len(sequence)]


def bridge_result(profile: CareerProfile, state: BridgeState) -> float:
    completion = min(1.0, state.completed_orders / 3.0)
    score = max(0.0, min(100.0, state.score * 0.65 + completion * 35.0))
    profile.practical_exam = max(profile.practical_exam, score)
    profile.xp += int(80 + score * 1.5)
    profile.duty_periods += 1
    profile.mission_performance = min(100.0, profile.mission_performance * 0.65 + score * 0.35)
    profile.discipline = min(100.0, profile.discipline + (3 if score >= 70 else 0))
    if score >= 70:
        profile.qualifications["Helmsman Practical"] = True
        profile.recommendations = max(profile.recommendations, 1)
    if profile.written_exam >= 70 and score >= 70:
        profile.qualifications["Helmsman"] = True
    profile.add_log(f"Bridge practical completed: {score:.0f}% ({state.completed_orders} orders completed).")
    return score


def damage_tick(state: DamageState) -> None:
    if state.resolved or state.failed:
        return
    state.elapsed += 1
    state.fire = min(100, state.fire + 1.5)
    state.smoke = min(100, state.smoke + state.fire * 0.022)
    state.flooding = min(100, state.flooding + 1.0)
    state.power = max(0, state.power - state.fire * 0.009)
    state.hull = max(0, state.hull - state.flooding * 0.011 - state.fire * 0.006)
    state.crew_health = max(0, state.crew_health - state.smoke * 0.004)
    state.fatigue = min(100, state.fatigue + 0.45)
    state.morale = max(0, state.morale - 0.12)
    if state.hull <= 20 or state.crew_health <= 25 or state.flooding >= 95:
        state.failed = True
        state.log.insert(0, "Ship condition critical. Drill failed.")
    elif state.fire <= 2 and state.flooding <= 4 and state.smoke <= 5:
        state.resolved = True
        state.log.insert(0, "All major casualties controlled. Drill resolved.")


def damage_action(state: DamageState, action: str) -> str:
    if state.resolved or state.failed:
        return "The drill is already complete."
    if action == "fire_team":
        reduction = max(3.0, 13.0 - state.fatigue * 0.06)
        state.fire = max(0, state.fire - reduction)
        state.fatigue = min(100, state.fatigue + 3.0)
        msg = f"Fire team attacked the seat of the fire (-{reduction:.0f} fire)."
    elif action == "pumps":
        reduction = max(2.5, 11.0 - (100 - state.power) * 0.03)
        state.flooding = max(0, state.flooding - reduction)
        state.power = max(0, state.power - 1.0)
        msg = f"Dewatering pumps engaged (-{reduction:.0f} flooding)."
    elif action == "isolate":
        state.power = max(0, state.power - 5)
        state.fire = max(0, state.fire - 5)
        state.smoke = max(0, state.smoke - 2)
        msg = "Damaged electrical zone isolated. Fire spread reduced; local power lost."
    elif action == "ventilate":
        if state.fire > 12:
            state.fire = min(100, state.fire + 3)
            state.smoke = max(0, state.smoke - 5)
            msg = "Ventilation reduced smoke but fed an uncontrolled fire."
        else:
            state.smoke = max(0, state.smoke - 12)
            msg = "Controlled ventilation cleared smoke from the compartment."
    elif action == "medical":
        state.crew_health = min(100, state.crew_health + 4)
        state.morale = min(100, state.morale + 2)
        msg = "Medical team treated casualties and stabilized the crew."
    elif action == "repair_power":
        if state.fire > 20:
            state.fire = min(100, state.fire + 2)
            msg = "Unsafe power repair attempt aggravated the casualty. Control the fire first."
        else:
            state.power = min(100, state.power + 10)
            msg = "Electrical repair restored partial ship service."
    else:
        msg = "Unknown action."
    state.log.insert(0, msg)
    state.log = state.log[:12]
    return msg


def damage_result(profile: CareerProfile, state: DamageState) -> float:
    survival = state.crew_health
    containment = 100 - (state.fire + state.flooding + state.smoke) / 3
    ship = (state.hull + state.power + state.steering + state.propulsion + state.comms) / 5
    time_bonus = max(0, 100 - state.elapsed * 1.5)
    score = max(0, min(100, 0.30 * containment + 0.25 * survival + 0.25 * ship + 0.20 * time_bonus))
    if state.failed:
        score *= 0.55
    profile.xp += int(60 + score)
    profile.duty_periods += 1
    profile.leadership_eval = min(100.0, profile.leadership_eval * 0.75 + score * 0.25)
    profile.performance_review = min(100.0, profile.performance_review * 0.8 + score * 0.2)
    profile.mission_performance = min(100.0, profile.mission_performance * 0.75 + score * 0.25)
    if score >= 70:
        profile.qualifications["Damage Control Familiarization"] = True
    profile.mission_history.insert(0, {
        "mission": "Damage Control Qualification Drill",
        "score": round(score, 1),
        "crew_survival": round(survival, 1),
        "discipline": round(profile.discipline, 1),
        "efficiency": round(containment, 1),
        "professionalism": round(profile.professionalism, 1),
    })
    profile.add_log(f"Damage-control drill completed: {score:.0f}%.")
    return score


def generate_crew(profile: CareerProfile, count: int = 10) -> list[CrewMember]:
    crew = [CrewMember.generated(profile.crew_seed, i) for i in range(count)]
    leadership = profile.leadership_eval
    for member in crew:
        member.morale = min(100, member.morale + (leadership - 50) * 0.08)
        member.relationship = min(100, member.relationship + (profile.reputation - 50) * 0.06)
    return crew


def apply_ship_systems_result(profile: CareerProfile, score: float, summary: dict) -> None:
    """Apply the full ship-systems casualty evaluation to career progression."""
    profile.ship_systems_runs += 1
    profile.ship_systems_best = max(profile.ship_systems_best, score)
    profile.xp += int(90 + score * 1.8)
    profile.duty_periods += 1
    profile.performance_review = min(100.0, profile.performance_review * 0.78 + score * 0.22)
    profile.leadership_eval = min(100.0, profile.leadership_eval * 0.72 + score * 0.28)
    profile.mission_performance = min(100.0, profile.mission_performance * 0.72 + score * 0.28)
    if score >= 70:
        profile.qualifications["Ship Systems Familiarization"] = True
        profile.qualifications["Damage Control Familiarization"] = True
        profile.recommendations = max(profile.recommendations, 1)
    if score >= 85:
        profile.qualifications["Shipboard Casualty Control"] = True
    profile.mission_history.insert(0, {
        "mission": "Full Ship Systems Casualty Simulation",
        "score": round(score, 1),
        "crew_survival": round(100.0 - float(summary.get("casualties", 0.0)), 1),
        "discipline": round(profile.discipline, 1),
        "efficiency": round(max(0.0, 100.0 - float(summary.get("max_fire", 0.0)) * 0.5 - float(summary.get("max_flooding", 0.0)) * 0.4), 1),
        "professionalism": round(profile.professionalism, 1),
    })
    profile.mission_history = profile.mission_history[:50]
    profile.add_log(f"Full ship-systems casualty simulation completed: {score:.0f}%.")


def apply_historical_result(profile: CareerProfile, scenario_id: str, scenario_name: str, score: float, summary: dict) -> None:
    """Apply a historical operations-watch evaluation to the persistent career.

    Historical mode rewards disciplined information handling and professional watchstanding.
    It does not rewrite the fixed historical outcome.
    """
    profile.historical_runs += 1
    profile.historical_best = max(profile.historical_best, score)
    profile.historical_scenarios[scenario_id] = max(profile.historical_scenarios.get(scenario_id, 0.0), score)
    profile.xp += int(110 + score * 2.0)
    profile.duty_periods += 1
    profile.performance_review = min(100.0, profile.performance_review * 0.78 + score * 0.22)
    profile.leadership_eval = min(100.0, profile.leadership_eval * 0.80 + score * 0.20)
    profile.mission_performance = min(100.0, profile.mission_performance * 0.74 + score * 0.26)
    profile.professionalism = min(100.0, profile.professionalism * 0.80 + score * 0.20)
    if score >= 70:
        profile.qualifications["Historical Operations Watchstanding"] = True
        profile.recommendations = max(profile.recommendations, 1)
    if score >= 88:
        profile.qualifications["Combat Information Plotting"] = True
    profile.mission_history.insert(0, {
        "mission": scenario_name,
        "score": round(score, 1),
        "crew_survival": 100.0,
        "discipline": round(float(summary.get("intel_discipline", profile.discipline)), 1),
        "efficiency": round(float(summary.get("command_readiness", score)), 1),
        "professionalism": round(profile.professionalism, 1),
    })
    profile.mission_history = profile.mission_history[:50]
    profile.add_log(f"Historical operations watch completed — {scenario_name}: {score:.0f}%.")


def apply_enterprise_duty_result(profile: CareerProfile, score: float, summary: dict) -> None:
    """Apply the Enterprise station-duty evaluation to persistent career progression."""
    profile.enterprise_duty_runs += 1
    profile.enterprise_duty_best = max(profile.enterprise_duty_best, score)
    profile.xp += int(130 + score * 2.2)
    profile.duty_periods += 1
    profile.performance_review = min(100.0, profile.performance_review * 0.76 + score * 0.24)
    profile.leadership_eval = min(100.0, profile.leadership_eval * 0.77 + score * 0.23)
    profile.mission_performance = min(100.0, profile.mission_performance * 0.72 + score * 0.28)
    profile.professionalism = min(100.0, profile.professionalism * 0.76 + score * 0.24)
    if score >= 70:
        profile.qualifications["USS Enterprise Midway Duty Watch"] = True
        profile.qualifications["Carrier Station Coordination"] = True
        profile.recommendations = max(profile.recommendations, 1)
    if score >= 88:
        profile.qualifications["Carrier Combat Watch Supervisor"] = True
    profile.mission_history.insert(0, {
        "mission": "USS Enterprise (CV-6) — Midway Station Duty",
        "score": round(score, 1),
        "crew_survival": 100.0,
        "discipline": round(float(summary.get("intel_discipline", profile.discipline)), 1),
        "efficiency": round(float(summary.get("station_readiness", score)), 1),
        "professionalism": round(profile.professionalism, 1),
    })
    profile.mission_history = profile.mission_history[:50]
    profile.add_log(f"USS Enterprise Midway station-duty watch completed: {score:.0f}%.")


def apply_shipboard_walk_result(profile: CareerProfile, score: float, summary: dict, qualified_stations=None) -> None:
    """Apply first-person/schematic shipboard duty results while preserving older career saves."""
    qualified_stations = qualified_stations or []
    profile.shipboard_walk_runs += 1
    profile.shipboard_walk_best = max(profile.shipboard_walk_best, score)
    profile.xp += int(160 + score * 2.5)
    profile.duty_periods += 1
    profile.performance_review = min(100.0, profile.performance_review * 0.75 + score * 0.25)
    profile.leadership_eval = min(100.0, profile.leadership_eval * 0.76 + score * 0.24)
    profile.mission_performance = min(100.0, profile.mission_performance * 0.70 + score * 0.30)
    profile.professionalism = min(100.0, profile.professionalism * 0.74 + score * 0.26)
    for station in qualified_stations:
        profile.station_qualifications[station] = True
        profile.qualifications[f"Enterprise {station.replace('_', ' ').title()} Station Practical"] = True
    if score >= 72:
        profile.qualifications["USS Enterprise Shipboard Duty"] = True
        profile.recommendations = max(profile.recommendations, 1)
    if score >= 90 and len(qualified_stations) >= 5:
        profile.qualifications["Carrier Multi-Station Watchstander"] = True
    profile.mission_history.insert(0, {
        "mission": "USS Enterprise (CV-6) — Shipboard Movement Duty",
        "score": round(score, 1),
        "crew_survival": 100.0,
        "discipline": round(float(summary.get("intel_discipline", profile.discipline)), 1),
        "efficiency": round(float(summary.get("station_readiness", score)), 1),
        "professionalism": round(profile.professionalism, 1),
    })
    profile.mission_history = profile.mission_history[:50]
    profile.add_log(
        f"USS Enterprise shipboard duty completed: {score:.0f}% • "
        f"{len(qualified_stations)} station practical(s) completed."
    )
