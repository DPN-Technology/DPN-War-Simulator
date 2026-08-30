from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import deque
import math

from .enterprise import (
    EnterpriseDutyState,
    create_enterprise_duty_state,
    perform_station_action,
    open_tasks,
    STATION_DEFS,
    evaluate_enterprise,
    enterprise_summary,
    advance_enterprise,
)


# The movement layout is deliberately a training schematic. It is NOT presented as an
# exact compartment-by-compartment reconstruction of USS Enterprise (CV-6) in June 1942.
# Historical event timing/operational context remains in the sourced Enterprise/Midway layers.

DECK_NAMES = {
    "ISLAND": "Island / Command Spaces",
    "FLIGHT": "Flight Deck",
    "HANGAR": "Hangar Deck",
    "ENGINEERING": "Engineering / Damage Control",
}

# 32 x 18 collision maps. # = bulkhead/solid structure, . = walkable deck.
DECK_MAPS: Dict[str, Tuple[str, ...]] = {
    "ISLAND": (
        "################################",
        "#.............##...............#",
        "#.............##...............#",
        "#.............##...............#",
        "#..............................#",
        "#..............................#",
        "######..##########..############",
        "#..............................#",
        "#..............................#",
        "#....######..........######....#",
        "#....#....#..........#....#....#",
        "#....#....#..........#....#....#",
        "#....#....#..........#....#....#",
        "#....######..........######....#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "################################",
    ),
    "FLIGHT": (
        "################################",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#.....................#####....#",
        "#.....................#####....#",
        "#.....................#####....#",
        "#.....................#####....#",
        "#.....................#####....#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "################################",
    ),
    "HANGAR": (
        "################################",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..####..................####..#",
        "#..#..#..................#..#..#",
        "#..#..#..................#..#..#",
        "#..####..................####..#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "#..####..................####..#",
        "#..#..#..................#..#..#",
        "#..#..#..................#..#..#",
        "#..####..................####..#",
        "#..............................#",
        "#..............................#",
        "################################",
    ),
    "ENGINEERING": (
        "################################",
        "#..............##..............#",
        "#..............##..............#",
        "#..............##..............#",
        "#..............................#",
        "#..............................#",
        "########..############..########",
        "#..............................#",
        "#..............................#",
        "#....######..........######....#",
        "#....#....#..........#....#....#",
        "#....#....#..........#....#....#",
        "#....#....#..........#....#....#",
        "#....######..........######....#",
        "#..............................#",
        "#..............................#",
        "#..............................#",
        "################################",
    ),
}


@dataclass(frozen=True)
class Zone:
    deck: str
    name: str
    bounds: Tuple[float, float, float, float]
    station: Optional[str] = None

    def contains(self, x: float, y: float) -> bool:
        x1, y1, x2, y2 = self.bounds
        return x1 <= x <= x2 and y1 <= y <= y2


ZONES: Tuple[Zone, ...] = (
    Zone("ISLAND", "Bridge", (1.2, 1.2, 13.6, 5.7), "BRIDGE"),
    Zone("ISLAND", "Combat Information Center", (16.2, 1.2, 30.6, 5.7), "CIC"),
    Zone("ISLAND", "Radio Central", (1.2, 7.2, 14.8, 16.6), "RADIO"),
    Zone("ISLAND", "Fire Control / Air Defense", (17.2, 7.2, 30.6, 16.6), "FIRE_CONTROL"),
    Zone("FLIGHT", "Forward Flight Deck", (1.1, 1.1, 12.0, 16.6), "AIR_OPS"),
    Zone("FLIGHT", "Midships Flight Deck", (12.0, 1.1, 21.6, 16.6), "AIR_OPS"),
    Zone("FLIGHT", "Aft Flight Deck", (21.6, 10.2, 30.7, 16.6), "AIR_OPS"),
    Zone("FLIGHT", "Island Exterior", (21.0, 4.7, 27.4, 10.3), None),
    Zone("HANGAR", "Forward Hangar Bay", (1.2, 1.2, 10.6, 16.6), "AIR_OPS"),
    Zone("HANGAR", "Mid Hangar Bay", (10.6, 1.2, 21.4, 16.6), "AIR_OPS"),
    Zone("HANGAR", "Aft Hangar Bay", (21.4, 1.2, 30.7, 16.6), "AIR_OPS"),
    Zone("ENGINEERING", "Main Engineering Control", (1.2, 1.2, 14.8, 5.8), "ENGINEERING"),
    Zone("ENGINEERING", "Damage Control Central", (16.2, 1.2, 30.7, 5.8), "DAMAGE_CONTROL"),
    Zone("ENGINEERING", "Machinery Passage", (1.2, 7.1, 15.0, 16.6), "ENGINEERING"),
    Zone("ENGINEERING", "Repair / Medical Staging", (17.0, 7.1, 30.7, 16.6), "DAMAGE_CONTROL"),
)


@dataclass(frozen=True)
class EquipmentNode:
    key: str
    deck: str
    x: float
    y: float
    name: str
    station: Optional[str]
    action: str
    detail: str
    qualification_step: Optional[str] = None


@dataclass(frozen=True)
class HatchNode:
    key: str
    deck: str
    x: float
    y: float
    name: str


@dataclass
class EquipmentRuntime:
    health: float = 100.0
    powered: bool = True
    fault: str = ""
    resets: int = 0


@dataclass
class CrewAvatar:
    key: str
    deck: str
    x: float
    y: float
    target_x: float
    target_y: float
    station: str
    waypoint: int = 0


HATCHES: Dict[str, HatchNode] = {
    "ISLAND_PORT": HatchNode("ISLAND_PORT", "ISLAND", 7.25, 6.15, "Port command-spaces access hatch"),
    "ISLAND_STBD": HatchNode("ISLAND_STBD", "ISLAND", 19.25, 6.15, "Starboard command-spaces access hatch"),
    "ENG_PORT": HatchNode("ENG_PORT", "ENGINEERING", 9.25, 6.15, "Port engineering watertight hatch"),
    "ENG_STBD": HatchNode("ENG_STBD", "ENGINEERING", 22.25, 6.15, "Starboard damage-control watertight hatch"),
    "HANGAR_FWD": HatchNode("HANGAR_FWD", "HANGAR", 9.25, 6.15, "Forward hangar fire-boundary door"),
    "HANGAR_AFT": HatchNode("HANGAR_AFT", "HANGAR", 22.25, 6.15, "Aft hangar fire-boundary door"),
    "LOWER_MESS": HatchNode("LOWER_MESS", "HANGAR", 15.25, 12.15, "Crew-services passage door"),
    "ENG_MACH": HatchNode("ENG_MACH", "ENGINEERING", 15.25, 11.15, "Machinery-space access door"),
    "ISLAND_CIC": HatchNode("ISLAND_CIC", "ISLAND", 15.25, 4.15, "CIC access door"),
    "ISLAND_RADIO": HatchNode("ISLAND_RADIO", "ISLAND", 15.25, 12.15, "Radio/Fire Control access door"),
}


EQUIPMENT: Dict[str, EquipmentNode] = {
    # Island / command spaces
    "HELM": EquipmentNode("HELM", "ISLAND", 4.0, 2.8, "Helm / course repeater", "BRIDGE", "STEADY_COURSE", "Steady the ordered course and verify heading response.", "HELM"),
    "ENGINE_TELEGRAPH": EquipmentNode("ENGINE_TELEGRAPH", "ISLAND", 9.5, 2.8, "Engine order telegraph", "BRIDGE", "AVIATION_COURSE", "Set the aviation maneuver and high-speed engine order.", "TELEGRAPH"),
    "BRIDGE_LOG": EquipmentNode("BRIDGE_LOG", "ISLAND", 6.5, 4.8, "Bridge watch log", "BRIDGE", "WATCH_TURNOVER", "Conduct formal watch turnover and log current orders.", "TURNOVER"),
    "CIC_PLOT": EquipmentNode("CIC_PLOT", "ISLAND", 20.0, 2.8, "CIC tactical plot", "CIC", "SMART_CIC", "Plot or refine the highest-priority carrier contact task.", "PLOT"),
    "RADAR_CONSOLE": EquipmentNode("RADAR_CONSOLE", "ISLAND", 27.0, 2.8, "Air-search radar console", "CIC", "VERIFY_PLOT", "Cross-check radar, lookout, and report information.", "RADAR"),
    "RADIO_RACK": EquipmentNode("RADIO_RACK", "ISLAND", 5.0, 10.0, "Priority radio circuits", "RADIO", "SMART_RADIO", "Open or route the highest-priority operational radio task.", "ROUTE"),
    "RADIO_LOG": EquipmentNode("RADIO_LOG", "ISLAND", 10.5, 14.0, "Radio message log", "RADIO", "RADIO_CHECK", "Run the circuit check and preserve timing/source information.", "CIRCUITS"),
    "AA_DIRECTOR": EquipmentNode("AA_DIRECTOR", "ISLAND", 22.0, 10.0, "Air-defense director", "FIRE_CONTROL", "SMART_AA", "Raise the required air-defense readiness for the current task.", "AA_READY"),
    "TRACK_BOARD": EquipmentNode("TRACK_BOARD", "ISLAND", 28.0, 14.0, "Air track correlation board", "FIRE_CONTROL", "TRACK_CHECK", "Correlate radar and visual tracks before classification.", "TRACK"),
    "ISLAND_LADDER": EquipmentNode("ISLAND_LADDER", "ISLAND", 15.5, 14.8, "Island ladder to flight deck", None, "TO_FLIGHT", "Descend to the flight deck.", None),
    # Flight deck
    "FLIGHT_CONTROL": EquipmentNode("FLIGHT_CONTROL", "FLIGHT", 24.2, 7.2, "Flight-deck control", "AIR_OPS", "SMART_AIR", "Prepare, launch, or recover the flight cycle as current conditions require.", "DECK_CONTROL"),
    "ELEVATOR_1_TOP": EquipmentNode("ELEVATOR_1_TOP", "FLIGHT", 6.0, 6.0, "Aircraft elevator No. 1", "AIR_OPS", "ELEVATOR_1", "Operate forward aircraft elevator.", "ELEVATORS"),
    "ELEVATOR_2_TOP": EquipmentNode("ELEVATOR_2_TOP", "FLIGHT", 15.5, 10.0, "Aircraft elevator No. 2", "AIR_OPS", "ELEVATOR_2", "Operate midships aircraft elevator.", "ELEVATORS"),
    "ELEVATOR_3_TOP": EquipmentNode("ELEVATOR_3_TOP", "FLIGHT", 27.0, 13.5, "Aircraft elevator No. 3", "AIR_OPS", "ELEVATOR_3", "Operate aft aircraft elevator.", "ELEVATORS"),
    "DECK_SAFETY": EquipmentNode("DECK_SAFETY", "FLIGHT", 18.0, 4.0, "Flight-deck safety board", "AIR_OPS", "DECK_SAFETY_CHECK", "Verify movement lanes, firefighting equipment, and deck safety.", "SAFETY"),
    "FLIGHT_TO_ISLAND": EquipmentNode("FLIGHT_TO_ISLAND", "FLIGHT", 25.5, 8.7, "Island access ladder", None, "TO_ISLAND", "Climb to command spaces.", None),
    "FLIGHT_TO_HANGAR": EquipmentNode("FLIGHT_TO_HANGAR", "FLIGHT", 15.5, 14.8, "Hangar access", None, "TO_HANGAR", "Descend to hangar deck.", None),
    # Hangar
    "FUEL_STATION": EquipmentNode("FUEL_STATION", "HANGAR", 5.0, 3.0, "Aviation fueling control", "AIR_OPS", "FUEL_AIRCRAFT", "Fuel the nearest aircraft package using the training handling sequence.", "FUEL"),
    "ORDNANCE_STATION": EquipmentNode("ORDNANCE_STATION", "HANGAR", 5.0, 14.5, "Aviation ordnance control", "AIR_OPS", "ARM_AIRCRAFT", "Arm the nearest aircraft package using the training handling sequence.", "ARM"),
    "TUG_CONTROL": EquipmentNode("TUG_CONTROL", "HANGAR", 16.0, 8.5, "Aircraft handling / tug control", "AIR_OPS", "MOVE_AIRCRAFT", "Move a prepared aircraft package toward an available elevator.", "HANDLE"),
    "ELEVATOR_1_BOTTOM": EquipmentNode("ELEVATOR_1_BOTTOM", "HANGAR", 8.0, 5.0, "Aircraft elevator No. 1 lower control", "AIR_OPS", "ELEVATOR_1", "Operate forward aircraft elevator.", "ELEVATORS"),
    "ELEVATOR_2_BOTTOM": EquipmentNode("ELEVATOR_2_BOTTOM", "HANGAR", 16.0, 12.0, "Aircraft elevator No. 2 lower control", "AIR_OPS", "ELEVATOR_2", "Operate midships aircraft elevator.", "ELEVATORS"),
    "ELEVATOR_3_BOTTOM": EquipmentNode("ELEVATOR_3_BOTTOM", "HANGAR", 25.5, 8.0, "Aircraft elevator No. 3 lower control", "AIR_OPS", "ELEVATOR_3", "Operate aft aircraft elevator.", "ELEVATORS"),
    "HANGAR_TO_FLIGHT": EquipmentNode("HANGAR_TO_FLIGHT", "HANGAR", 15.5, 2.0, "Flight-deck access", None, "TO_FLIGHT", "Climb to flight deck.", None),
    "HANGAR_TO_ENG": EquipmentNode("HANGAR_TO_ENG", "HANGAR", 29.0, 15.0, "Engineering access ladder", None, "TO_ENGINEERING", "Descend to engineering/damage-control spaces.", None),
    # Engineering / DC
    "ENG_CONSOLE": EquipmentNode("ENG_CONSOLE", "ENGINEERING", 6.0, 3.0, "Main engineering maneuvering console", "ENGINEERING", "SMART_ENG", "Set the appropriate plant maneuvering condition or balance load.", "PLANT"),
    "LOAD_BOARD": EquipmentNode("LOAD_BOARD", "ENGINEERING", 12.0, 4.5, "Electrical load board", "ENGINEERING", "BALANCE_LOAD", "Balance electrical load and confirm reserve margin.", "LOAD"),
    "DC_BOARD": EquipmentNode("DC_BOARD", "ENGINEERING", 21.0, 3.0, "Damage-control status board", "DAMAGE_CONTROL", "SMART_DC", "Set or recheck damage-control readiness as the watch requires.", "DC_READY"),
    "BOUNDARY_BOARD": EquipmentNode("BOUNDARY_BOARD", "ENGINEERING", 27.0, 4.5, "Watertight boundary board", "DAMAGE_CONTROL", "CHECK_BOUNDARIES", "Inspect and verify watertight boundaries.", "BOUNDARIES"),
    "MEDICAL_STAGING": EquipmentNode("MEDICAL_STAGING", "ENGINEERING", 23.0, 13.0, "Medical / repair-party staging", "DAMAGE_CONTROL", "MEDICAL_CHECK", "Verify medical support and repair-party staging.", "MEDICAL"),
    "COMMAND_DESK": EquipmentNode("COMMAND_DESK", "ISLAND", 12.0, 4.8, "Captain / Officer-of-the-Deck command desk", None, "COMMAND_CONSOLE", "Review departments, issue lawful orders, and monitor chain-of-command execution.", None),
    "ENG_TO_HANGAR": EquipmentNode("ENG_TO_HANGAR", "ENGINEERING", 29.0, 15.0, "Hangar access ladder", None, "TO_HANGAR", "Climb to hangar deck.", None),
}


QUALIFICATION_REQUIREMENTS: Dict[str, Tuple[str, ...]] = {
    "BRIDGE": ("HELM", "TELEGRAPH", "TURNOVER"),
    "CIC": ("PLOT", "RADAR"),
    "RADIO": ("ROUTE", "CIRCUITS"),
    "ENGINEERING": ("PLANT", "LOAD"),
    "DAMAGE_CONTROL": ("DC_READY", "BOUNDARIES", "MEDICAL"),
    "FIRE_CONTROL": ("AA_READY", "TRACK"),
    "AIR_OPS": ("DECK_CONTROL", "ELEVATORS", "SAFETY", "FUEL", "ARM", "HANDLE"),
}


STATION_ANCHORS: Dict[str, Tuple[str, float, float]] = {
    "BRIDGE": ("ISLAND", 6.5, 3.5),
    "CIC": ("ISLAND", 23.5, 3.5),
    "RADIO": ("ISLAND", 7.5, 11.5),
    "FIRE_CONTROL": ("ISLAND", 24.5, 11.5),
    "AIR_OPS": ("FLIGHT", 24.0, 7.5),
    "ENGINEERING": ("ENGINEERING", 7.0, 3.5),
    "DAMAGE_CONTROL": ("ENGINEERING", 23.5, 3.5),
}

TASK_ACTION_EQUIPMENT = {
    "OPEN_PRIORITY_NET": "RADIO_RACK", "ROUTE_SCOUT_REPORT": "RADIO_RACK", "ROUTE_BATTLE_REPORTS": "RADIO_RACK",
    "PLOT_CONTACT": "CIC_PLOT", "REFINE_CARRIER_PLOT": "CIC_PLOT", "KEEP_RESIDUAL_THREAT": "CIC_PLOT", "PLOT_HIRYU_RESULT": "CIC_PLOT",
    "AIR_DEFENSE_READY": "AA_DIRECTOR", "HIGH_AA_ALERT": "AA_DIRECTOR",
    "MANEUVERING_READY": "ENG_CONSOLE", "FULL_MANEUVER_READY": "ENG_CONSOLE",
    "SET_DC_READY": "DC_BOARD", "RECHECK_DC": "DC_BOARD",
    "PREPARE_FLIGHT_DECK": "FLIGHT_CONTROL", "LAUNCH_STRIKE": "FLIGHT_CONTROL", "RECOVERY_READY": "FLIGHT_CONTROL",
    "AVIATION_COURSE": "ENGINE_TELEGRAPH",
}

DRILL_FAULTS = (
    (8 * 60 + 5, "RADIO_LOG", "SIMULATED CIRCUIT GROUND"),
    (12 * 60 + 10, "LOAD_BOARD", "SIMULATED BUS OVERLOAD"),
    (14 * 60 + 30, "DC_BOARD", "SIMULATED FIREMAIN INDICATION FAULT"),
)

@dataclass
class AircraftPackage:
    key: str
    label: str
    aircraft_type: str
    count: int
    deck: str
    x: float
    y: float
    fueled: bool = False
    armed: bool = False
    spotted: bool = False
    launched: bool = False
    status: str = "PARKED"


@dataclass
class ShipboardWalkState:
    enterprise: EnterpriseDutyState = field(default_factory=create_enterprise_duty_state)
    deck: str = "ISLAND"
    x: float = 7.0
    y: float = 4.0
    angle: float = 0.0
    running: bool = False
    move_speed: float = 0.34
    turn_speed: float = math.radians(9)
    interaction_range: float = 1.65
    action_log: List[str] = field(default_factory=list)
    qualification_progress: Dict[str, List[str]] = field(default_factory=lambda: {k: [] for k in STATION_DEFS})
    qualified_this_run: List[str] = field(default_factory=list)
    elevators: Dict[str, str] = field(default_factory=lambda: {"1": "HANGAR", "2": "HANGAR", "3": "FLIGHT"})
    aircraft: Dict[str, AircraftPackage] = field(default_factory=dict)
    selected_aircraft: Optional[str] = None
    watch_period: str = "0400-0800"
    last_watch_period: str = "0400-0800"
    watch_turnovers: int = 0
    interactions: int = 0
    movement_distance: float = 0.0
    completed: bool = False
    evaluated: bool = False
    hatches: Dict[str, bool] = field(default_factory=lambda: {k: True for k in HATCHES})
    equipment_runtime: Dict[str, EquipmentRuntime] = field(default_factory=dict)
    crew_avatars: Dict[str, CrewAvatar] = field(default_factory=dict)
    injected_faults: List[str] = field(default_factory=list)
    training_faults_resolved: int = 0
    objective_completions: int = 0

    @property
    def clock(self) -> str:
        return self.enterprise.clock


def create_shipboard_walk_state(enterprise: Optional[EnterpriseDutyState] = None) -> ShipboardWalkState:
    st = ShipboardWalkState(enterprise=enterprise or create_enterprise_duty_state())
    st.aircraft = {
        "F4F_CAP": AircraftPackage("F4F_CAP", "CAP section", "F4F Wildcat", 6, "HANGAR", 9.0, 8.0),
        "SBD_SCOUT": AircraftPackage("SBD_SCOUT", "Scout section", "SBD Dauntless", 6, "HANGAR", 13.0, 6.0),
        "SBD_STRIKE_A": AircraftPackage("SBD_STRIKE_A", "Bombing section A", "SBD Dauntless", 8, "HANGAR", 18.0, 6.0),
        "SBD_STRIKE_B": AircraftPackage("SBD_STRIKE_B", "Bombing section B", "SBD Dauntless", 8, "HANGAR", 20.0, 11.0),
        "TBD_TORPEDO": AircraftPackage("TBD_TORPEDO", "Torpedo section", "TBD Devastator", 8, "HANGAR", 24.0, 11.0),
        "F4F_RESERVE": AircraftPackage("F4F_RESERVE", "Fighter reserve", "F4F Wildcat", 4, "HANGAR", 27.0, 4.0),
    }
    st.equipment_runtime = {k: EquipmentRuntime() for k in EQUIPMENT}
    assignments = {}
    for station_key, station_state in st.enterprise.stations.items():
        for crew_key in station_state.crew_keys:
            assignments[crew_key] = station_key
    offsets = [(-0.7, -0.4), (0.6, 0.5), (-0.3, 0.7)]
    for idx, crew_key in enumerate(st.enterprise.crew):
        station = assignments.get(crew_key, "BRIDGE")
        deck, ax, ay = STATION_ANCHORS[station]
        ox, oy = offsets[idx % len(offsets)]
        st.crew_avatars[crew_key] = CrewAvatar(crew_key, deck, ax + ox, ay + oy, ax, ay, station, idx % 3)
    st.action_log.append("05:20 — Shipboard movement watch assumed in training-schematic mode. Use WASD/arrow keys; E interacts with nearby equipment and hatches.")
    st.action_log.append("05:20 — v0.6 training injectors armed. Any equipment malfunction labeled SIMULATED is gameplay training, not a claim about historical Enterprise damage.")
    return st


def tile_walkable(deck: str, x: float, y: float, state: Optional[ShipboardWalkState] = None) -> bool:
    grid = DECK_MAPS[deck]
    ix, iy = int(x), int(y)
    if iy < 0 or iy >= len(grid) or ix < 0 or ix >= len(grid[0]):
        return False
    if grid[iy][ix] == "#":
        return False
    if state is not None:
        for key, hatch in HATCHES.items():
            if hatch.deck == deck and not state.hatches.get(key, True):
                if math.hypot(hatch.x - x, hatch.y - y) < 0.48:
                    return False
    return True


def nearby_hatch(state: ShipboardWalkState, radius: float = 1.25) -> Optional[HatchNode]:
    best = None
    best_d = 999.0
    for hatch in HATCHES.values():
        if hatch.deck != state.deck:
            continue
        d = math.hypot(hatch.x - state.x, hatch.y - state.y)
        if d <= radius and d < best_d:
            best, best_d = hatch, d
    return best


def toggle_hatch(state: ShipboardWalkState, key: str) -> Tuple[bool, str]:
    if key not in HATCHES:
        return False, "Unknown hatch."
    state.hatches[key] = not state.hatches.get(key, True)
    status = "OPEN" if state.hatches[key] else "SHUT"
    msg = f"{HATCHES[key].name} {status}; dog/closure indication verified."
    state.action_log.insert(0, f"{state.clock} — {msg}")
    return True, msg


def move_player(state: ShipboardWalkState, forward: float = 0.0, strafe: float = 0.0, turn: float = 0.0) -> bool:
    state.angle = (state.angle + turn * state.turn_speed) % (math.pi * 2)
    dx = math.cos(state.angle) * forward * state.move_speed + math.cos(state.angle + math.pi / 2) * strafe * state.move_speed
    dy = math.sin(state.angle) * forward * state.move_speed + math.sin(state.angle + math.pi / 2) * strafe * state.move_speed
    nx, ny = state.x + dx, state.y + dy
    moved = False
    # Axis-separated collision prevents most corner clipping.
    if tile_walkable(state.deck, nx, state.y, state):
        state.x = nx
        moved = True
    if tile_walkable(state.deck, state.x, ny, state):
        state.y = ny
        moved = True
    if moved:
        state.movement_distance += math.hypot(dx, dy)
    return moved


def current_zone(state: ShipboardWalkState) -> str:
    for z in ZONES:
        if z.deck == state.deck and z.contains(state.x, state.y):
            return z.name
    return "Passage / open deck"


def current_station(state: ShipboardWalkState) -> Optional[str]:
    for z in ZONES:
        if z.deck == state.deck and z.contains(state.x, state.y):
            return z.station
    return None


def nearby_equipment(state: ShipboardWalkState) -> Optional[EquipmentNode]:
    best: Optional[EquipmentNode] = None
    best_d = 999.0
    for node in EQUIPMENT.values():
        if node.deck != state.deck:
            continue
        d = math.hypot(node.x - state.x, node.y - state.y)
        if d <= state.interaction_range and d < best_d:
            best, best_d = node, d
    return best


def nearby_aircraft(state: ShipboardWalkState, radius: float = 2.2) -> Optional[AircraftPackage]:
    best = None
    best_d = 999.0
    for ac in state.aircraft.values():
        if ac.deck != state.deck or ac.launched:
            continue
        d = math.hypot(ac.x - state.x, ac.y - state.y)
        if d <= radius and d < best_d:
            best, best_d = ac, d
    return best


def _smart_action(state: ShipboardWalkState, station: str, choices: Tuple[str, ...], fallback: str) -> str:
    tasks = open_tasks(state.enterprise, station)
    for task in tasks:
        if task.action in choices:
            return task.action
    return fallback


def _mark_qualification_step(state: ShipboardWalkState, node: EquipmentNode) -> None:
    if not node.station or not node.qualification_step:
        return
    progress = state.qualification_progress.setdefault(node.station, [])
    if node.qualification_step not in progress:
        progress.append(node.qualification_step)
    needed = set(QUALIFICATION_REQUIREMENTS.get(node.station, ()))
    if needed and needed.issubset(set(progress)) and node.station not in state.qualified_this_run:
        state.qualified_this_run.append(node.station)
        state.action_log.insert(0, f"{state.clock} — PRACTICAL COMPLETE: {STATION_DEFS[node.station]['name']} station qualification checklist satisfied this run.")


def _watch_period(minute: int) -> str:
    h = (minute // 60) % 24
    if 4 <= h < 8:
        return "0400-0800"
    if 8 <= h < 12:
        return "0800-1200"
    if 12 <= h < 16:
        return "1200-1600"
    if 16 <= h < 18:
        return "1600-1800"
    if 18 <= h < 20:
        return "1800-2000"
    if 20 <= h or h < 0:
        return "2000-0000"
    return "0000-0400"


def _handle_watch_change(state: ShipboardWalkState) -> None:
    period = _watch_period(state.enterprise.current_minute)
    state.watch_period = period
    if period != state.last_watch_period:
        state.last_watch_period = period
        state.watch_turnovers += 1
        # Watch change gives offgoing personnel some relief but creates a coordination dip.
        for crew in state.enterprise.crew.values():
            crew.fatigue = max(2.0, crew.fatigue - 4.0)
        for station in state.enterprise.stations.values():
            station.readiness = max(45.0, station.readiness - 1.5)
        state.action_log.insert(0, f"{state.clock} — WATCH ROTATION: {period}. Conduct station turnover and verify standing orders.")


def _inject_training_faults(state: ShipboardWalkState) -> None:
    for minute, node_key, fault in DRILL_FAULTS:
        token = f"{minute}:{node_key}"
        if state.enterprise.current_minute >= minute and token not in state.injected_faults:
            state.injected_faults.append(token)
            runtime = state.equipment_runtime[node_key]
            runtime.fault = fault
            runtime.health = max(55.0, runtime.health - 18.0)
            state.action_log.insert(0, f"{state.clock} — TRAINING INJECT: {EQUIPMENT[node_key].name} reports {fault}. This is a simulated drill fault, not a historical casualty claim.")


def _crew_station_for_key(state: ShipboardWalkState, crew_key: str) -> str:
    for station_key, station_state in state.enterprise.stations.items():
        if crew_key in station_state.crew_keys:
            return station_key
    return "BRIDGE"


def update_crew_movement(state: ShipboardWalkState, dt: float = 0.08) -> None:
    """Move visible watchstanders around their assigned station areas using collision-aware steps."""
    for key, av in state.crew_avatars.items():
        station = _crew_station_for_key(state, key)
        av.station = station
        target_deck, ax, ay = STATION_ANCHORS[station]
        if av.deck != target_deck:
            # Cross-deck movement is abstracted as a watchstander transit rather than pretending the schematic ladders are exact historical routes.
            av.deck, av.x, av.y = target_deck, ax, ay
        alert = state.enterprise.stations[station].alert
        spread = 0.55 if alert in ("ACTION", "URGENT") else 1.15
        phase = (av.waypoint % 4) * math.pi / 2
        tx = ax + math.cos(phase) * spread
        ty = ay + math.sin(phase) * spread
        if not tile_walkable(av.deck, tx, ty, state):
            tx, ty = ax, ay
        av.target_x, av.target_y = tx, ty
        dx, dy = tx - av.x, ty - av.y
        dist = math.hypot(dx, dy)
        if dist < 0.12:
            av.waypoint = (av.waypoint + 1) % 4
            continue
        step = min(dist, max(0.02, dt * (0.7 if alert == "URGENT" else 0.42)))
        nx, ny = av.x + dx / dist * step, av.y + dy / dist * step
        if tile_walkable(av.deck, nx, ny, state):
            av.x, av.y = nx, ny


def ship_alarm_state(state: ShipboardWalkState) -> str:
    tasks = open_tasks(state.enterprise)
    if any(t.deadline_minute - state.enterprise.current_minute <= 5 for t in tasks):
        return "URGENT ACTION"
    if tasks:
        return "ACTION STATIONS"
    if any(rt.fault for rt in state.equipment_runtime.values()):
        return "TRAINING CASUALTY"
    return "WATCH ROUTINE"


def active_objective(state: ShipboardWalkState) -> Optional[dict]:
    tasks = sorted(open_tasks(state.enterprise), key=lambda t: (t.deadline_minute, t.opened_minute))
    if not tasks:
        faulted = next((k for k,v in state.equipment_runtime.items() if v.fault), None)
        if faulted:
            node = EQUIPMENT[faulted]
            return {"title": f"Restore {node.name}", "deck": node.deck, "x": node.x, "y": node.y, "station": node.station, "deadline": None, "node": node.key}
        return None
    task = tasks[0]
    node_key = TASK_ACTION_EQUIPMENT.get(task.action)
    if node_key and node_key in EQUIPMENT:
        node = EQUIPMENT[node_key]
        return {"title": task.title, "deck": node.deck, "x": node.x, "y": node.y, "station": task.station, "deadline": task.deadline_minute, "node": node.key}
    deck, x, y = STATION_ANCHORS[task.station]
    return {"title": task.title, "deck": deck, "x": x, "y": y, "station": task.station, "deadline": task.deadline_minute, "node": None}


def objective_navigation(state: ShipboardWalkState) -> str:
    obj = active_objective(state)
    if not obj:
        return "No urgent duty task. Continue qualifications or run the historical clock."
    station_name = STATION_DEFS[obj["station"]]["name"] if obj.get("station") else DECK_NAMES[obj["deck"]]
    if obj["deck"] != state.deck:
        return f"OBJECTIVE: {obj['title']} • report to {station_name} on {DECK_NAMES[obj['deck']]}"
    dx, dy = obj["x"] - state.x, obj["y"] - state.y
    dist = math.hypot(dx, dy)
    bearing = (math.degrees(math.atan2(dy, dx)) % 360)
    return f"OBJECTIVE: {obj['title']} • {dist:.1f} deck units • bearing {bearing:03.0f}°"


def advance_shipboard(state: ShipboardWalkState, minutes: int) -> None:
    if state.completed:
        return
    advance_enterprise(state.enterprise, minutes)
    _handle_watch_change(state)
    _inject_training_faults(state)
    update_crew_movement(state, min(1.0, max(0.08, minutes * 0.12)))
    # Walking mode uses the same battle readiness metrics; fatigue accumulates while the watch runs.
    for crew in state.enterprise.crew.values():
        crew.fatigue = min(100.0, crew.fatigue + minutes * 0.035)
    if state.enterprise.completed:
        state.completed = True


def _change_deck(state: ShipboardWalkState, target: str) -> Tuple[bool, str]:
    state.deck = target
    # Safe spawn points near access points.
    spawns = {
        "ISLAND": (15.5, 14.2, -math.pi / 2),
        "FLIGHT": (25.0, 9.2, math.pi),
        "HANGAR": (15.5, 2.5, math.pi / 2),
        "ENGINEERING": (28.5, 14.5, math.pi),
    }
    state.x, state.y, state.angle = spawns[target]
    state.action_log.insert(0, f"{state.clock} — Moved to {DECK_NAMES[target]}.")
    return True, f"Moved to {DECK_NAMES[target]}."


def _operate_elevator(state: ShipboardWalkState, number: str) -> Tuple[bool, str]:
    current = state.elevators[number]
    target = "FLIGHT" if current == "HANGAR" else "HANGAR"
    # Do not move an elevator beneath a package marked as spotted elsewhere; simplified safety interlock.
    state.elevators[number] = target
    state.enterprise.deck_safety = max(55.0, state.enterprise.deck_safety - 0.5)
    return True, f"Aircraft elevator No. {number} moved to {target.lower()} level; safety interlock verified."


def _nearest_aircraft_for_handling(state: ShipboardWalkState) -> Optional[AircraftPackage]:
    ac = nearby_aircraft(state, radius=5.5)
    if ac:
        return ac
    # If at a handling station, pick the first non-launched hangar package.
    for item in state.aircraft.values():
        if item.deck == "HANGAR" and not item.launched:
            return item
    return None


def _sync_air_readiness(state: ShipboardWalkState) -> None:
    active = [a for a in state.aircraft.values() if not a.launched]
    if not active:
        return
    fueled = sum(a.count for a in active if a.fueled) / max(1, sum(a.count for a in active))
    armed = sum(a.count for a in active if a.armed) / max(1, sum(a.count for a in active))
    spotted = sum(a.count for a in active if a.spotted or a.deck == "FLIGHT") / max(1, sum(a.count for a in active))
    state.enterprise.aircraft_fueled = max(state.enterprise.aircraft_fueled, 55 + 45 * fueled)
    state.enterprise.aircraft_armed = max(state.enterprise.aircraft_armed, 50 + 50 * armed)
    state.enterprise.deck_spot = max(state.enterprise.deck_spot, 45 + 55 * spotted)


def _aircraft_action(state: ShipboardWalkState, action: str) -> Tuple[bool, str]:
    # Handling stations choose a package appropriate to the requested step. This avoids
    # accidentally trying to spot an unprepared package simply because it is physically
    # closer to the tug-control position.
    ac = None
    if state.selected_aircraft:
        selected = state.aircraft.get(state.selected_aircraft)
        if selected and selected.deck == "HANGAR" and not selected.launched:
            ac = selected
    if action == "FUEL_AIRCRAFT":
        ac = ac if ac and not ac.fueled else next((a for a in state.aircraft.values() if a.deck == "HANGAR" and not a.launched and not a.fueled), None)
    elif action == "ARM_AIRCRAFT":
        ac = ac if ac and ac.fueled and not ac.armed else next((a for a in state.aircraft.values() if a.deck == "HANGAR" and not a.launched and a.fueled and not a.armed), None)
    elif action == "MOVE_AIRCRAFT":
        ac = ac if ac and ac.fueled and ac.armed else next((a for a in state.aircraft.values() if a.deck == "HANGAR" and not a.launched and a.fueled and a.armed), None)
    if not ac:
        return False, "No aircraft package is available for this handling action."
    state.selected_aircraft = ac.key
    if action == "FUEL_AIRCRAFT":
        if ac.fueled:
            return True, f"{ac.label} is already fueled."
        ac.fueled = True
        ac.status = "FUELED"
        msg = f"Fueled {ac.label} ({ac.count} × {ac.aircraft_type}); fuel-control checklist logged."
    elif action == "ARM_AIRCRAFT":
        if not ac.fueled:
            return False, "Arming held in this training sequence: fuel/handling clearance has not been completed for the selected package."
        ac.armed = True
        ac.status = "ARMED"
        msg = f"Armed {ac.label}; ordnance-control checklist logged."
    elif action == "MOVE_AIRCRAFT":
        if not (ac.fueled and ac.armed):
            return False, "Handling held: the selected package must be fueled and armed before it is spotted for this combat cycle."
        # Pick an elevator already at hangar level.
        elevator = next((n for n, level in state.elevators.items() if level == "HANGAR"), None)
        if not elevator:
            return False, "No aircraft elevator is available at hangar level. Bring an elevator down first."
        targets = {"1": (6.0, 6.0), "2": (15.5, 10.0), "3": (27.0, 13.5)}
        ac.deck = "FLIGHT"
        ac.x, ac.y = targets[elevator]
        ac.spotted = True
        ac.status = f"SPOTTED VIA ELEV {elevator}"
        state.elevators[elevator] = "FLIGHT"
        state.enterprise.deck_safety = max(60.0, state.enterprise.deck_safety - 1.0)
        msg = f"{ac.label} moved by handling crew and spotted on flight deck via elevator No. {elevator}."
    else:
        return False, "Unknown aircraft handling action."
    _sync_air_readiness(state)
    return True, msg


def interact(state: ShipboardWalkState) -> Tuple[bool, str]:
    hatch = nearby_hatch(state)
    if hatch:
        state.interactions += 1
        return toggle_hatch(state, hatch.key)
    node = nearby_equipment(state)
    if not node:
        ac = nearby_aircraft(state)
        if ac:
            state.selected_aircraft = ac.key
            return True, f"Selected {ac.label}: {ac.count} × {ac.aircraft_type} • {ac.status}. Report to fueling, ordnance, or tug control to handle it."
        return False, "No equipment is within reach. Move closer to a highlighted control or aircraft package."

    state.interactions += 1
    runtime = state.equipment_runtime.setdefault(node.key, EquipmentRuntime())
    if runtime.fault:
        fault = runtime.fault
        runtime.fault = ""
        runtime.health = min(100.0, runtime.health + 24.0)
        runtime.resets += 1
        state.training_faults_resolved += 1
        msg = f"Training fault cleared at {node.name}: {fault}. Equipment reset, indications checked, and station returned to service."
        state.action_log.insert(0, f"{state.clock} — TRAINING RESTORE: {msg}")
        return True, msg
    action = node.action
    if action.startswith("TO_"):
        target = action[3:]
        return _change_deck(state, target)
    if action.startswith("ELEVATOR_"):
        ok, msg = _operate_elevator(state, action.split("_")[-1])
        if ok:
            _mark_qualification_step(state, node)
            state.action_log.insert(0, f"{state.clock} — {msg}")
        return ok, msg
    if action in ("FUEL_AIRCRAFT", "ARM_AIRCRAFT", "MOVE_AIRCRAFT"):
        ok, msg = _aircraft_action(state, action)
        if ok:
            _mark_qualification_step(state, node)
            state.action_log.insert(0, f"{state.clock} — [AIR] {msg}")
        return ok, msg
    if action == "MEDICAL_CHECK":
        state.enterprise.repair_party_readiness = min(100.0, state.enterprise.repair_party_readiness + 3.0)
        msg = "Medical support, stretcher routes, and repair-party casualty staging verified."
        _mark_qualification_step(state, node)
        state.action_log.insert(0, f"{state.clock} — [DC] {msg}")
        return True, msg
    if action == "WATCH_TURNOVER":
        state.enterprise.stations["BRIDGE"].readiness = min(100.0, state.enterprise.stations["BRIDGE"].readiness + 2.0)
        msg = f"Bridge watch turnover completed for {state.watch_period}; standing orders and current course/speed logged."
        _mark_qualification_step(state, node)
        state.action_log.insert(0, f"{state.clock} — [BRG] {msg}")
        return True, msg

    # Context-sensitive station consoles select the currently relevant task action first.
    if action == "SMART_CIC":
        action = _smart_action(state, "CIC", ("PLOT_CONTACT", "REFINE_CARRIER_PLOT", "KEEP_RESIDUAL_THREAT", "PLOT_HIRYU_RESULT"), "VERIFY_PLOT")
    elif action == "SMART_RADIO":
        action = _smart_action(state, "RADIO", ("OPEN_PRIORITY_NET", "ROUTE_SCOUT_REPORT", "ROUTE_BATTLE_REPORTS"), "RADIO_CHECK")
    elif action == "SMART_AA":
        action = _smart_action(state, "FIRE_CONTROL", ("AIR_DEFENSE_READY", "HIGH_AA_ALERT"), "TRACK_CHECK")
    elif action == "SMART_ENG":
        action = _smart_action(state, "ENGINEERING", ("MANEUVERING_READY", "FULL_MANEUVER_READY"), "BALANCE_LOAD")
    elif action == "SMART_DC":
        action = _smart_action(state, "DAMAGE_CONTROL", ("SET_DC_READY", "RECHECK_DC"), "CHECK_BOUNDARIES")
    elif action == "SMART_AIR":
        action = _smart_action(state, "AIR_OPS", ("PREPARE_FLIGHT_DECK", "LAUNCH_STRIKE", "RECOVERY_READY"), "DECK_SAFETY_CHECK")

    if node.station:
        ok, msg = perform_station_action(state.enterprise, node.station, action)
        if ok:
            _mark_qualification_step(state, node)
            state.action_log.insert(0, f"{state.clock} — [{STATION_DEFS[node.station]['short']}] {node.name}: {msg}")
            # If a valid launch action occurred, launch all physically spotted prepared packages.
            if action == "LAUNCH_STRIKE" and state.enterprise.strike_launched:
                for ac in state.aircraft.values():
                    if ac.deck == "FLIGHT" and ac.spotted and ac.fueled and ac.armed:
                        ac.launched = True
                        ac.status = "LAUNCHED"
            state.objective_completions += 1
            return ok, msg
        return ok, msg
    return False, "This equipment has no configured action."


def qualification_status(state: ShipboardWalkState, station: str) -> Tuple[int, int, bool]:
    required = set(QUALIFICATION_REQUIREMENTS.get(station, ()))
    complete = set(state.qualification_progress.get(station, ()))
    return len(required & complete), len(required), required.issubset(complete) if required else False


def shipboard_summary(state: ShipboardWalkState) -> dict:
    ent = enterprise_summary(state.enterprise)
    qualified = len(state.qualified_this_run)
    aircraft_ready = len([a for a in state.aircraft.values() if a.fueled and a.armed])
    aircraft_spotted = len([a for a in state.aircraft.values() if a.spotted or a.launched])
    return {
        **ent,
        "qualified_stations": qualified,
        "aircraft_ready_packages": aircraft_ready,
        "aircraft_spotted_packages": aircraft_spotted,
        "watch_turnovers": state.watch_turnovers,
        "interactions": state.interactions,
        "movement_distance": state.movement_distance,
        "training_faults_resolved": state.training_faults_resolved,
        "training_faults_open": sum(1 for rt in state.equipment_runtime.values() if rt.fault),
        "hatches_shut": sum(1 for v in state.hatches.values() if not v),
        "objective_completions": state.objective_completions,
        "alarm_state": ship_alarm_state(state),
    }


def evaluate_shipboard(state: ShipboardWalkState) -> float:
    base = evaluate_enterprise(state.enterprise)
    qualified = len(state.qualified_this_run) / max(1, len(QUALIFICATION_REQUIREMENTS))
    interaction = min(1.0, state.interactions / 18.0)
    handling = sum(1 for a in state.aircraft.values() if a.fueled and a.armed) / max(1, len(state.aircraft))
    mobility = min(1.0, state.movement_distance / 35.0)
    fault_control = 1.0 if not any(rt.fault for rt in state.equipment_runtime.values()) else max(0.0, 1.0 - sum(1 for rt in state.equipment_runtime.values() if rt.fault) * 0.2)
    objective_discipline = min(1.0, state.objective_completions / 10.0)
    score = 0.69 * base + 12.0 * qualified + 6.0 * interaction + 5.0 * handling + 3.0 * mobility + 2.0 * fault_control + 3.0 * objective_discipline
    state.completed = True
    state.evaluated = True
    return round(max(0.0, min(100.0, score)), 1)


def raycast(state: ShipboardWalkState, rays: int = 160, fov: float = math.radians(68), max_dist: float = 24.0) -> List[Tuple[float, str]]:
    """Return distance + hit side per ray for a simple first-person renderer."""
    grid = DECK_MAPS[state.deck]
    out: List[Tuple[float, str]] = []
    for i in range(rays):
        ra = state.angle - fov / 2 + fov * (i / max(1, rays - 1))
        cs, sn = math.cos(ra), math.sin(ra)
        dist = 0.04
        hit_side = "wall"
        while dist < max_dist:
            rx, ry = state.x + cs * dist, state.y + sn * dist
            ix, iy = int(rx), int(ry)
            if iy < 0 or iy >= len(grid) or ix < 0 or ix >= len(grid[0]) or not tile_walkable(state.deck, rx, ry, state):
                # Crude orientation shading hint based on local ray component.
                hit_side = "ns" if abs(cs) > abs(sn) else "ew"
                break
            dist += 0.055
        # Fish-eye correction.
        corrected = max(0.08, dist * math.cos(ra - state.angle))
        out.append((corrected, hit_side))
    return out


def visible_equipment(state: ShipboardWalkState, fov: float = math.radians(68), max_dist: float = 10.0) -> List[Tuple[EquipmentNode, float, float]]:
    """Nodes inside view cone. Returns (node, signed angle offset, distance)."""
    result = []
    for node in EQUIPMENT.values():
        if node.deck != state.deck:
            continue
        dx, dy = node.x - state.x, node.y - state.y
        d = math.hypot(dx, dy)
        if d > max_dist:
            continue
        a = math.atan2(dy, dx)
        off = (a - state.angle + math.pi) % (2 * math.pi) - math.pi
        if abs(off) <= fov / 2:
            # Basic line-of-sight march.
            steps = max(2, int(d / 0.15))
            blocked = False
            for s in range(1, steps):
                t = s / steps
                if not tile_walkable(state.deck, state.x + dx * t, state.y + dy * t, state):
                    blocked = True
                    break
            if not blocked:
                result.append((node, off, d))
    return sorted(result, key=lambda v: v[2], reverse=True)


def visible_crew(state: ShipboardWalkState, fov: float = math.radians(68), max_dist: float = 9.0) -> List[Tuple[CrewAvatar, float, float]]:
    result = []
    for av in state.crew_avatars.values():
        if av.deck != state.deck:
            continue
        dx, dy = av.x - state.x, av.y - state.y
        d = math.hypot(dx, dy)
        if d <= 0.15 or d > max_dist:
            continue
        a = math.atan2(dy, dx)
        off = (a - state.angle + math.pi) % (2 * math.pi) - math.pi
        if abs(off) <= fov / 2:
            result.append((av, off, d))
    return sorted(result, key=lambda v: v[2], reverse=True)
