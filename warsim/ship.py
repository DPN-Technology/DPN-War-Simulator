from __future__ import annotations
from dataclasses import dataclass, field, asdict
from collections import deque
from typing import Dict, List, Optional, Tuple
import math
import random


@dataclass
class CompartmentState:
    key: str
    name: str
    deck: str
    kind: str
    x: float
    y: float
    w: float
    h: float
    bus: str
    integrity: float = 100.0
    fire: float = 0.0
    flooding: float = 0.0
    smoke: float = 0.0
    oxygen: float = 21.0
    temperature: float = 22.0
    breach: float = 0.0
    casualties: float = 0.0
    ventilation: bool = True
    breaker_closed: bool = True
    firemain_valve: bool = True
    powered: bool = True


@dataclass
class HatchState:
    key: str
    a: str
    b: str
    watertight: bool = True
    open: bool = True
    integrity: float = 100.0


@dataclass
class PumpState:
    name: str
    location: str
    target: Optional[str] = None
    active: bool = False
    portable: bool = False
    rate: float = 3.0


@dataclass
class CrewTeamState:
    name: str
    specialty: str
    location: str
    members: int
    training: float
    fatigue: float = 8.0
    health: float = 100.0
    morale: float = 85.0
    task: str = "STANDBY"
    target: Optional[str] = None
    eta: float = 0.0


@dataclass
class ShipState:
    scenario_name: str = "Machinery Casualty Training"
    elapsed: float = 0.0
    compartments: Dict[str, CompartmentState] = field(default_factory=dict)
    hatches: Dict[str, HatchState] = field(default_factory=dict)
    pumps: Dict[str, PumpState] = field(default_factory=dict)
    teams: Dict[str, CrewTeamState] = field(default_factory=dict)
    bus_health: Dict[str, float] = field(default_factory=lambda: {"A": 100.0, "B": 100.0, "EMERGENCY": 100.0})
    main_generator_output: float = 100.0
    emergency_generator: float = 100.0
    battery: float = 100.0
    firemain_pressure: float = 100.0
    propulsion_port: float = 100.0
    propulsion_starboard: float = 100.0
    steering: float = 100.0
    communications: float = 100.0
    combat_systems: float = 100.0
    medical_capacity: float = 100.0
    magazine_risk: float = 0.0
    total_casualties: float = 0.0
    resolved: bool = False
    failed: bool = False
    score: float = 0.0
    log: List[str] = field(default_factory=list)
    rng_seed: int = 731942

    def compartment(self, key: str) -> CompartmentState:
        return self.compartments[key]


# The layout intentionally mirrors the examples listed in the GDD while remaining
# abstract enough to be usable across multiple historical ship classes later.
COMPARTMENT_BLUEPRINT = [
    ("FLIGHT", "Flight Deck", "01", "aviation", .04, .05, .92, .09, "A"),
    ("BRIDGE", "Bridge", "01", "command", .07, .18, .18, .12, "EMERGENCY"),
    ("FIRE_CONTROL", "Fire Control", "01", "combat", .28, .18, .17, .12, "A"),
    ("RADIO", "Radio Room", "01", "communications", .48, .18, .17, .12, "EMERGENCY"),
    ("CIC", "Combat Information Center", "01", "combat", .68, .18, .25, .12, "A"),
    ("HANGAR", "Hangar", "MAIN", "aviation", .05, .36, .22, .14, "A"),
    ("BERTHING", "Sleeping Quarters", "MAIN", "habitation", .30, .36, .17, .14, "B"),
    ("GALLEY", "Galley", "MAIN", "habitation", .50, .36, .16, .14, "B"),
    ("MEDICAL", "Medical Bay", "MAIN", "medical", .69, .36, .24, .14, "EMERGENCY"),
    ("DC", "Damage Control Central", "MAIN", "damage_control", .05, .56, .20, .14, "EMERGENCY"),
    ("MAG_FWD", "Forward Magazine", "LOWER", "magazine", .28, .56, .17, .14, "A"),
    ("MACHINERY", "Machinery Room", "LOWER", "machinery", .48, .56, .17, .14, "B"),
    ("MAG_AFT", "Ammunition Storage", "LOWER", "magazine", .68, .56, .25, .14, "B"),
    ("BOILER_1", "Boiler Room 1", "LOWER", "engineering", .05, .76, .18, .14, "A"),
    ("ENGINE_1", "Engine Room 1", "LOWER", "engineering", .26, .76, .18, .14, "A"),
    ("PUMP", "Pump Room", "LOWER", "damage_control", .47, .76, .15, .14, "EMERGENCY"),
    ("ENGINE_2", "Engine Room 2", "LOWER", "engineering", .65, .76, .16, .14, "B"),
    ("STEERING", "Steering Gear", "LOWER", "steering", .84, .76, .11, .14, "EMERGENCY"),
]

# Connections form the internal route / watertight-boundary graph.
HATCH_BLUEPRINT = [
    ("H01", "BRIDGE", "FIRE_CONTROL", False),
    ("H02", "FIRE_CONTROL", "RADIO", False),
    ("H03", "RADIO", "CIC", False),
    ("H04", "BRIDGE", "HANGAR", True),
    ("H05", "FIRE_CONTROL", "BERTHING", True),
    ("H06", "RADIO", "GALLEY", True),
    ("H07", "CIC", "MEDICAL", True),
    ("H08", "HANGAR", "BERTHING", True),
    ("H09", "BERTHING", "GALLEY", True),
    ("H10", "GALLEY", "MEDICAL", True),
    ("H11", "HANGAR", "DC", True),
    ("H12", "BERTHING", "MAG_FWD", True),
    ("H13", "GALLEY", "MACHINERY", True),
    ("H14", "MEDICAL", "MAG_AFT", True),
    ("H15", "DC", "MAG_FWD", True),
    ("H16", "MAG_FWD", "MACHINERY", True),
    ("H17", "MACHINERY", "MAG_AFT", True),
    ("H18", "DC", "BOILER_1", True),
    ("H19", "MAG_FWD", "ENGINE_1", True),
    ("H20", "MACHINERY", "PUMP", True),
    ("H21", "MAG_AFT", "ENGINE_2", True),
    ("H22", "MAG_AFT", "STEERING", True),
    ("H23", "BOILER_1", "ENGINE_1", True),
    ("H24", "ENGINE_1", "PUMP", True),
    ("H25", "PUMP", "ENGINE_2", True),
    ("H26", "ENGINE_2", "STEERING", True),
]


def create_training_ship() -> ShipState:
    s = ShipState()
    s.compartments = {
        key: CompartmentState(key, name, deck, kind, x, y, w, h, bus)
        for key, name, deck, kind, x, y, w, h, bus in COMPARTMENT_BLUEPRINT
    }
    s.hatches = {
        key: HatchState(key, a, b, watertight=watertight, open=True)
        for key, a, b, watertight in HATCH_BLUEPRINT
    }
    s.pumps = {
        "FIXED_1": PumpState("Fixed Dewatering Pump 1", "PUMP", rate=4.2),
        "FIXED_2": PumpState("Fixed Dewatering Pump 2", "PUMP", rate=4.2),
        "PORTABLE_1": PumpState("Portable Pump Alpha", "DC", portable=True, rate=3.0),
        "PORTABLE_2": PumpState("Portable Pump Bravo", "DC", portable=True, rate=3.0),
    }
    s.teams = {
        "REPAIR_1": CrewTeamState("Repair Team 1", "damage control", "DC", 6, 82.0),
        "REPAIR_2": CrewTeamState("Repair Team 2", "damage control", "DC", 6, 78.0),
        "ELECTRICAL": CrewTeamState("Electrical Team", "electrical", "DC", 4, 86.0),
        "ENGINEERING": CrewTeamState("Engineering Team", "engineering", "ENGINE_1", 5, 88.0),
        "MEDICAL": CrewTeamState("Medical Team", "medical", "MEDICAL", 4, 90.0),
    }

    # Starting casualty: fire + hull breach + electrical loss in adjacent machinery spaces.
    e2 = s.compartments["ENGINE_2"]
    e2.fire = 46.0
    e2.smoke = 34.0
    e2.temperature = 88.0
    e2.integrity = 82.0
    e2.breaker_closed = False

    m = s.compartments["MACHINERY"]
    m.flooding = 31.0
    m.breach = 1.25
    m.integrity = 76.0
    m.smoke = 12.0

    s.bus_health["B"] = 72.0
    s.log = [
        "GENERAL QUARTERS: machinery casualty drill initiated.",
        "Engine Room 2 reports major fire and electrical trip.",
        "Machinery Room reports progressive flooding from hull breach.",
        "Command objective: contain casualties, preserve crew, restore critical systems.",
    ]
    recalculate_ship_systems(s)
    return s


def adjacent_hatches(state: ShipState, compartment_key: str) -> List[HatchState]:
    return [h for h in state.hatches.values() if h.a == compartment_key or h.b == compartment_key]


def neighbor_for(hatch: HatchState, key: str) -> str:
    return hatch.b if hatch.a == key else hatch.a


def shortest_path(state: ShipState, start: str, goal: str) -> Optional[List[str]]:
    if start == goal:
        return [start]
    q = deque([(start, [start])])
    visited = {start}
    while q:
        node, path = q.popleft()
        for h in adjacent_hatches(state, node):
            # A shut hatch blocks routine movement. Teams may be reassigned after reopening it.
            if not h.open or h.integrity <= 10:
                continue
            nxt = neighbor_for(h, node)
            if nxt in visited:
                continue
            if nxt == goal:
                return path + [nxt]
            visited.add(nxt)
            q.append((nxt, path + [nxt]))
    return None


def toggle_hatch(state: ShipState, hatch_key: str) -> str:
    h = state.hatches[hatch_key]
    if h.integrity <= 10:
        return f"{h.key} is too damaged to operate."
    h.open = not h.open
    action = "OPEN" if h.open else "SHUT"
    msg = f"{h.key} {action}: {state.compartments[h.a].name} ↔ {state.compartments[h.b].name}."
    state.log.insert(0, msg)
    return msg


def toggle_breaker(state: ShipState, compartment_key: str) -> str:
    c = state.compartments[compartment_key]
    if c.fire > 30 and not c.breaker_closed:
        msg = f"Breaker for {c.name} remains OPEN: unsafe to re-energize with active fire."
    else:
        c.breaker_closed = not c.breaker_closed
        msg = f"{c.name} electrical breaker {'CLOSED' if c.breaker_closed else 'OPENED'}."
    state.log.insert(0, msg)
    recalculate_ship_systems(state)
    return msg


def toggle_ventilation(state: ShipState, compartment_key: str) -> str:
    c = state.compartments[compartment_key]
    c.ventilation = not c.ventilation
    msg = f"{c.name} ventilation {'ENABLED' if c.ventilation else 'SECURED'}."
    state.log.insert(0, msg)
    return msg


def toggle_firemain_valve(state: ShipState, compartment_key: str) -> str:
    c = state.compartments[compartment_key]
    c.firemain_valve = not c.firemain_valve
    msg = f"{c.name} firemain isolation valve {'OPEN' if c.firemain_valve else 'SHUT'}."
    state.log.insert(0, msg)
    return msg


def route_pump(state: ShipState, pump_key: str, target_key: str) -> str:
    p = state.pumps[pump_key]
    target = state.compartments[target_key]
    p.target = target_key
    p.active = True
    if p.portable:
        p.location = target_key
    msg = f"{p.name} routed to {target.name}."
    state.log.insert(0, msg)
    return msg


def stop_pump(state: ShipState, pump_key: str) -> str:
    p = state.pumps[pump_key]
    p.active = False
    msg = f"{p.name} secured."
    state.log.insert(0, msg)
    return msg


def assign_team(state: ShipState, team_key: str, task: str, target_key: str) -> str:
    team = state.teams[team_key]
    target = state.compartments[target_key]
    path = shortest_path(state, team.location, target_key)
    if path is None:
        msg = f"{team.name} cannot reach {target.name}; route blocked by shut/damaged hatches."
        state.log.insert(0, msg)
        return msg
    team.task = task.upper()
    team.target = target_key
    team.eta = max(0.0, (len(path) - 1) * 3.5)
    msg = f"{team.name} assigned {team.task} at {target.name}; ETA {team.eta:.0f}s."
    state.log.insert(0, msg)
    return msg


def _team_effectiveness(team: CrewTeamState) -> float:
    return max(0.20, (team.training / 100.0) * (1.0 - team.fatigue / 135.0) * (team.health / 100.0))


def _apply_team_task(state: ShipState, team: CrewTeamState, dt: float) -> None:
    if not team.target or team.task == "STANDBY":
        team.fatigue = max(0.0, team.fatigue - 0.15 * dt)
        return
    if team.eta > 0:
        team.eta = max(0.0, team.eta - dt)
        if team.eta == 0:
            team.location = team.target
            state.log.insert(0, f"{team.name} arrived at {state.compartments[team.target].name}.")
        return

    c = state.compartments[team.target]
    eff = _team_effectiveness(team)
    hazard = c.fire * 0.005 + c.smoke * 0.003 + c.flooding * 0.0015
    team.fatigue = min(100.0, team.fatigue + (0.20 + hazard) * dt)
    if c.fire > 55 or c.smoke > 70:
        team.health = max(0.0, team.health - hazard * 0.12 * dt)

    task = team.task
    if task == "FIREFIGHT":
        pressure_factor = state.firemain_pressure / 100.0 if c.firemain_valve else 0.15
        c.fire = max(0.0, c.fire - (2.4 * eff * pressure_factor) * dt)
        c.temperature = max(22.0, c.temperature - (1.2 * eff) * dt)
    elif task == "DEWATER":
        c.flooding = max(0.0, c.flooding - (1.1 * eff) * dt)
    elif task == "REPAIR":
        if c.fire < 15 and c.flooding < 55:
            c.integrity = min(100.0, c.integrity + (0.65 * eff) * dt)
            c.breach = max(0.0, c.breach - (0.030 * eff) * dt)
    elif task == "ELECTRICAL":
        if c.fire < 12:
            state.bus_health[c.bus] = min(100.0, state.bus_health[c.bus] + (0.75 * eff) * dt)
            if state.bus_health[c.bus] > 45:
                c.breaker_closed = True
    elif task == "MEDICAL":
        if c.casualties > 0:
            treated = min(c.casualties, (0.9 * eff) * dt)
            c.casualties -= treated
            state.total_casualties = max(0.0, state.total_casualties - treated * 0.15)
    elif task == "SEAL":
        c.breach = max(0.0, c.breach - (0.050 * eff) * dt)


def _spread_between(state: ShipState, hatch: HatchState, dt: float) -> None:
    if not hatch.open or hatch.integrity <= 10:
        return
    a = state.compartments[hatch.a]
    b = state.compartments[hatch.b]

    # Smoke equalizes through open boundaries.
    smoke_delta = (a.smoke - b.smoke) * 0.020 * dt
    a.smoke = max(0.0, a.smoke - smoke_delta)
    b.smoke = max(0.0, b.smoke + smoke_delta)

    # Water can spread through open watertight boundaries; closing hatches is meaningful.
    if hatch.watertight:
        flood_delta = (a.flooding - b.flooding) * 0.010 * dt
        a.flooding = max(0.0, a.flooding - flood_delta)
        b.flooding = max(0.0, b.flooding + flood_delta)

    # Severe fire can ignite an adjacent compartment when an open route exists.
    if a.fire > 48 and b.fire < a.fire * 0.35:
        b.fire = min(100.0, b.fire + (a.fire - 45) * 0.0025 * dt)
    if b.fire > 48 and a.fire < b.fire * 0.35:
        a.fire = min(100.0, a.fire + (b.fire - 45) * 0.0025 * dt)


def _update_compartment(state: ShipState, c: CompartmentState, dt: float) -> None:
    if c.breach > 0:
        c.flooding = min(100.0, c.flooding + c.breach * 0.72 * dt)
    if c.fire > 0:
        oxygen_factor = max(0.0, c.oxygen / 21.0)
        vent_factor = 1.10 if c.ventilation else 0.48
        growth = max(-0.12, (0.18 * oxygen_factor * vent_factor) - 0.09)
        c.fire = max(0.0, min(100.0, c.fire + growth * dt))
        c.smoke = min(100.0, c.smoke + c.fire * 0.020 * dt)
        c.temperature = min(240.0, c.temperature + c.fire * 0.010 * dt)
        c.oxygen = max(7.0, c.oxygen - c.fire * 0.0012 * dt)
        c.integrity = max(0.0, c.integrity - c.fire * 0.0016 * dt)
    else:
        c.temperature = max(22.0, c.temperature - 0.35 * dt)
        c.oxygen = min(21.0, c.oxygen + (0.18 if c.ventilation else 0.04) * dt)

    if c.ventilation:
        c.smoke = max(0.0, c.smoke - 0.28 * dt)
    if c.flooding > 40:
        c.fire = max(0.0, c.fire - 0.10 * dt)
    if c.flooding > 75:
        c.integrity = max(0.0, c.integrity - (c.flooding - 75) * 0.0012 * dt)

    # Exposed personnel become casualties if a compartment is allowed to remain lethal.
    lethal = max(0.0, c.fire - 55) + max(0.0, c.smoke - 70) * 0.6
    if lethal > 0:
        c.casualties = min(100.0, c.casualties + lethal * 0.0020 * dt)
        state.total_casualties = min(100.0, state.total_casualties + lethal * 0.0005 * dt)


def _update_pumps(state: ShipState, dt: float) -> None:
    for p in state.pumps.values():
        if not p.active or not p.target:
            continue
        target = state.compartments[p.target]
        if target.flooding <= 0:
            continue
        power_factor = 1.0
        if not p.portable:
            pump_room = state.compartments["PUMP"]
            power_factor = 1.0 if pump_room.powered and pump_room.integrity > 25 else 0.15
        else:
            power_factor = max(0.35, state.emergency_generator / 100.0)
        target.flooding = max(0.0, target.flooding - p.rate * power_factor * dt)


def recalculate_ship_systems(state: ShipState) -> None:
    # Bus damage is influenced by compartments actively burning/flooding on that bus.
    for bus in ("A", "B"):
        threats = [c for c in state.compartments.values() if c.bus == bus]
        penalty = sum(max(0.0, c.fire - 25) * 0.020 + max(0.0, c.flooding - 45) * 0.012 for c in threats)
        state.bus_health[bus] = max(0.0, min(100.0, state.bus_health[bus] - penalty * 0.02))

    eng1 = state.compartments["ENGINE_1"]
    eng2 = state.compartments["ENGINE_2"]
    boiler = state.compartments["BOILER_1"]
    pump = state.compartments["PUMP"]
    steer = state.compartments["STEERING"]
    radio = state.compartments["RADIO"]
    cic = state.compartments["CIC"]
    fire_control = state.compartments["FIRE_CONTROL"]
    medical = state.compartments["MEDICAL"]

    def health(c: CompartmentState) -> float:
        hazard = c.fire * 0.55 + c.flooding * 0.45
        return max(0.0, min(100.0, c.integrity - hazard * 0.50))

    state.main_generator_output = max(0.0, min(100.0, (health(eng1) + health(eng2) + health(boiler)) / 3.0))
    state.emergency_generator = max(0.0, min(100.0, state.compartments["DC"].integrity - state.compartments["DC"].fire * 0.4))
    if state.main_generator_output < 45:
        state.battery = max(0.0, state.battery - 0.05)
    elif state.battery < 100:
        state.battery = min(100.0, state.battery + 0.03)

    for c in state.compartments.values():
        bus_power = state.bus_health.get(c.bus, 0.0)
        source = state.emergency_generator if c.bus == "EMERGENCY" else state.main_generator_output
        c.powered = bool(c.breaker_closed and bus_power > 20 and source > 20 and c.flooding < 70 and c.fire < 70)

    state.propulsion_port = health(eng1) * (1.0 if eng1.powered else 0.35)
    state.propulsion_starboard = health(eng2) * (1.0 if eng2.powered else 0.35)
    state.steering = health(steer) * (1.0 if steer.powered else 0.45)
    state.communications = health(radio) * (1.0 if radio.powered else 0.40)
    state.combat_systems = ((health(cic) + health(fire_control)) / 2.0) * (1.0 if cic.powered else 0.45)
    state.medical_capacity = health(medical) * (1.0 if medical.powered else 0.65)
    state.firemain_pressure = max(0.0, min(100.0, health(pump) * (1.0 if pump.powered else 0.35)))

    mags = [state.compartments["MAG_FWD"], state.compartments["MAG_AFT"]]
    state.magazine_risk = max(
        min(100.0, m.fire * 0.70 + max(0.0, m.temperature - 55) * 0.75)
        for m in mags
    )


def ship_tick(state: ShipState, dt: float = 1.0) -> None:
    if state.resolved or state.failed:
        return
    state.elapsed += dt
    for c in state.compartments.values():
        _update_compartment(state, c, dt)
    for h in state.hatches.values():
        _spread_between(state, h, dt)
    for team in state.teams.values():
        _apply_team_task(state, team, dt)
    _update_pumps(state, dt)
    recalculate_ship_systems(state)

    # Catastrophic conditions.
    if state.magazine_risk >= 98:
        state.failed = True
        state.log.insert(0, "CATASTROPHIC: magazine thermal risk exceeded survivable limits.")
    elif state.total_casualties >= 70:
        state.failed = True
        state.log.insert(0, "CATASTROPHIC: crew casualties exceeded survivable limits.")
    elif sum(c.flooding for c in state.compartments.values()) / len(state.compartments) >= 62:
        state.failed = True
        state.log.insert(0, "CATASTROPHIC: uncontrolled progressive flooding threatens loss of ship.")

    max_fire = max(c.fire for c in state.compartments.values())
    max_flood = max(c.flooding for c in state.compartments.values())
    max_breach = max(c.breach for c in state.compartments.values())
    if state.elapsed >= 20 and max_fire <= 4 and max_flood <= 12 and max_breach <= 0.10 and state.steering >= 45 and max(state.propulsion_port, state.propulsion_starboard) >= 35:
        state.resolved = True
        state.log.insert(0, "CASUALTY CONTROLLED: fire, flooding, and critical mobility restored to safe limits.")

    state.log = state.log[:80]


def evaluate_ship_scenario(state: ShipState) -> float:
    fires = sum(c.fire for c in state.compartments.values()) / len(state.compartments)
    floods = sum(c.flooding for c in state.compartments.values()) / len(state.compartments)
    integrity = sum(c.integrity for c in state.compartments.values()) / len(state.compartments)
    mobility = (state.propulsion_port + state.propulsion_starboard + state.steering) / 3.0
    command = (state.communications + state.combat_systems) / 2.0
    casualty_score = 100.0 - state.total_casualties
    containment = max(0.0, 100.0 - fires * 1.4 - floods * 1.1)
    time_score = max(0.0, 100.0 - max(0.0, state.elapsed - 90.0) * 0.22)
    score = (
        0.23 * containment +
        0.19 * integrity +
        0.18 * mobility +
        0.12 * command +
        0.18 * casualty_score +
        0.10 * time_score
    )
    if state.resolved:
        score += 6.0
    elif not state.failed:
        # Ending a still-active casualty is a command failure even if the ship remains afloat.
        score *= 0.72
    if state.failed:
        score *= 0.48
    state.score = max(0.0, min(100.0, score))
    return state.score


def ship_summary(state: ShipState) -> dict:
    max_fire_comp = max(state.compartments.values(), key=lambda c: c.fire)
    max_flood_comp = max(state.compartments.values(), key=lambda c: c.flooding)
    return {
        "elapsed": round(state.elapsed, 1),
        "max_fire": round(max_fire_comp.fire, 1),
        "max_fire_location": max_fire_comp.name,
        "max_flooding": round(max_flood_comp.flooding, 1),
        "max_flood_location": max_flood_comp.name,
        "casualties": round(state.total_casualties, 1),
        "propulsion": round((state.propulsion_port + state.propulsion_starboard) / 2.0, 1),
        "steering": round(state.steering, 1),
        "communications": round(state.communications, 1),
        "firemain": round(state.firemain_pressure, 1),
        "magazine_risk": round(state.magazine_risk, 1),
        "resolved": state.resolved,
        "failed": state.failed,
    }
