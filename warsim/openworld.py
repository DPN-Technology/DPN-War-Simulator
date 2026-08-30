from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple
import math

# v0.9 continues the seamless-world geometry as a training schematic. It is intentionally
# separated from the sourced historical timeline/operations data.

CAMERA_HEIGHT = 1.62
SHIP_ORIGIN_X = 64.0
SHIP_ORIGIN_Y = 8.0
# v2.5 carrier realism rebuild.  World units on Enterprise are now approximately metres.
# The flight-deck footprint is based on Yorktown-class dimensions (~244.6 m x 29.9 m).
SHIP_LENGTH_M = 245
SHIP_WIDTH_M = 30
SHIP_CENTER_X = SHIP_ORIGIN_X + SHIP_LENGTH_M/2
SHIP_CENTER_Y = SHIP_ORIGIN_Y + SHIP_WIDTH_M/2
SHIP_ELEVATORS = ((58.0,15.0),(121.0,15.0),(188.0,15.0))
SHIP_ISLAND_CENTER = (168.0,23.0)


@dataclass(frozen=True)
class WorldLayer:
    key: str
    name: str
    origin_x: float
    origin_y: float
    floor_z: float
    grid: Tuple[str, ...]
    ceiling: bool = True
    wall_color: str = "#3e4652"
    floor_color: str = "#232a32"
    outdoor: bool = False

    @property
    def width(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    @property
    def height(self) -> int:
        return len(self.grid)


@dataclass(frozen=True)
class WorldInteraction:
    key: str
    name: str
    x: float
    y: float
    floor_z: float
    action: str
    kind: str = "console"
    detail: str = ""


@dataclass(frozen=True)
class VerticalConnector:
    key: str
    name: str
    x: float
    y: float
    from_z: float
    to_z: float
    from_layer: str
    to_layer: str
    kind: str = "ladder"


def _blank(w: int, h: int, char: str = " ") -> List[List[str]]:
    return [[char for _ in range(w)] for _ in range(h)]


def _room(g: List[List[str]], x1: int, y1: int, x2: int, y2: int, doors: Iterable[Tuple[int, int]] = ()) -> None:
    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            if y in (y1, y2) or x in (x1, x2):
                g[y][x] = "#"
            else:
                g[y][x] = "."
    for x, y in doors:
        if 0 <= y < len(g) and 0 <= x < len(g[0]):
            g[y][x] = "."


def _corridor(g: List[List[str]], x1: int, y1: int, x2: int, y2: int) -> None:
    for y in range(max(0, y1), min(len(g), y2 + 1)):
        for x in range(max(0, x1), min(len(g[0]), x2 + 1)):
            g[y][x] = "."


def _base_grid() -> Tuple[str, ...]:
    w, h = 64, 382
    g = _blank(w, h, ".")
    # Perimeter/fence with main pier exit.
    for x in range(w):
        g[0][x] = g[h-1][x] = "#"
    for y in range(h):
        g[y][0] = "#"
    # Buildings are walkable interiors with actual walls and doors.
    _room(g, 3, 3, 20, 16, doors=((11,16),(20,10)))      # admin/career
    _room(g, 23, 3, 45, 16, doors=((34,16),(23,10)))     # academy
    _room(g, 3, 20, 27, 39, doors=((15,20),(27,30)))     # simulator center
    _room(g, 31, 20, 55, 39, doors=((43,20),(31,30),(55,30))) # barracks/galley/medical
    # Internal simulator partitions.
    for x in range(5, 26): g[29][x] = "#"
    g[29][9] = g[29][21] = "."
    for y in range(22, 38): g[y][15] = "#"
    g[25][15] = g[34][15] = "."
    # Barracks / galley / sickbay partitions.
    for x in range(33, 54): g[29][x] = "#"
    g[29][38] = g[29][49] = "."
    for y in range(22, 38): g[y][44] = "#"
    g[25][44] = g[34][44] = "."
    # Pier runs east into the ship hangar-deck gangway opening.
    _corridor(g, 55, 27, 63, 32)
    # v1.9 expeditionary operations district: one continuous walkable extension of the shore base.
    _room(g, 3, 47, 20, 59, doors=((11,47),(20,53)))      # ground operations HQ
    _room(g, 23, 47, 40, 59, doors=((31,47),(40,53)))     # motor pool
    _room(g, 43, 47, 60, 59, doors=((51,47),(43,53)))     # expeditionary airfield ops
    # Open training apron/runway/landing staging area south of the buildings.
    _corridor(g, 3, 62, 60, 69)
    _corridor(g, 10, 40, 14, 47)
    _corridor(g, 30, 40, 34, 47)
    _corridor(g, 50, 40, 54, 47)
    # v2.0 combined-arms district: still the same seamless shore coordinate space.
    _corridor(g, 8, 69, 12, 78)
    _corridor(g, 28, 69, 32, 78)
    _corridor(g, 48, 69, 52, 78)
    _room(g, 3, 74, 17, 82, doors=((10,74),(17,78)))       # infantry armory / issue point
    _room(g, 20, 74, 34, 82, doors=((27,74),(34,78)))      # fireteam command / briefing
    _room(g, 43, 74, 58, 82, doors=((50,74),(43,78)))      # field aid / casualty collection
    # Training village / maneuver lanes. Walkable blocks are separated by hard cover/walls.
    _corridor(g, 4, 84, 59, 101)
    for x1,y1,x2,y2,doors in (
        (8,86,18,94,((13,86),(18,90))),
        (24,85,34,92,((29,92),(34,88))),
        (40,86,51,94,((45,86),(40,91))),
        (28,95,42,101,((35,95),)),
    ):
        _room(g,x1,y1,x2,y2,doors=doors)
    # Cover walls / lane dividers with gaps, creating meaningful infantry maneuver choices.
    for x in range(5,59):
        if x not in (12,20,31,37,54): g[84][x] = "#"
    for y in range(86,101):
        if y not in (90,97): g[y][22] = "#"
        if y not in (88,96): g[y][38] = "#"
    # v2.1 battalion maneuver area: continuous road from the v2.0 village into a larger land battlefield.
    _corridor(g, 28, 101, 36, 116)
    _room(g, 4, 108, 18, 116, doors=((11,116),(18,112)))       # battalion / platoon command post
    _room(g, 21, 108, 39, 116, doors=((30,116),(39,112)))      # armored vehicle park
    _room(g, 42, 108, 59, 116, doors=((51,116),(42,112)))      # artillery fire-direction center
    _room(g, 4, 126, 20, 136, doors=((12,126),(20,131)))       # field hospital / CASEVAC
    _room(g, 24, 126, 40, 136, doors=((32,126),(40,131)))      # battalion logistics point
    _room(g, 44, 126, 59, 136, doors=((51,126),(44,131)))      # engineer / maintenance point
    # Main maneuver roads and battlefield floor.
    _corridor(g, 10, 116, 54, 126)
    _corridor(g, 6, 138, 58, 171)
    _corridor(g, 29, 136, 37, 171)
    # Trenches / fighting positions with intentional gaps and multiple approaches.
    for x in range(7,58):
        if x not in (14,23,35,47,54): g[142][x] = "#"
    for x in range(7,58):
        if x not in (11,20,31,42,52): g[153][x] = "#"
    for x in range(7,58):
        if x not in (16,28,39,49): g[164][x] = "#"
    for y in range(140,169):
        if y not in (145,153,160): g[y][25] = "#"
        if y not in (148,157,165): g[y][44] = "#"
    # Hardpoints / small structures at key sectors.
    _room(g, 9, 145, 16, 151, doors=((12,145),))
    _room(g, 31, 146, 39, 152, doors=((35,152),))
    _room(g, 48, 141, 56, 148, doors=((48,145),))
    _room(g, 30, 158, 39, 166, doors=((34,158),))
    # v2.2 strategic war district: command, intelligence/logistics, and persistent front-line map.
    _corridor(g, 29, 171, 37, 180)
    _room(g, 4, 178, 18, 188, doors=((11,178),(18,183)))       # theater / strategic command HQ
    _room(g, 22, 178, 38, 188, doors=((30,178),(38,183)))      # intelligence / reconnaissance center
    _room(g, 42, 178, 59, 188, doors=((50,178),(42,183)))      # theater logistics / reinforcement center
    _corridor(g, 6, 190, 58, 242)
    _corridor(g, 29, 188, 37, 242)
    # strategic front-line terrain and road/bridge chokepoints
    for x in range(7,58):
        if x not in (12,19,27,35,44,53): g[202][x] = "#"
    for x in range(7,58):
        if x not in (10,21,31,40,50): g[218][x] = "#"
    for x in range(7,58):
        if x not in (15,26,34,46,55): g[233][x] = "#"
    for y in range(191,241):
        if y not in (197,205,214,224,235): g[y][21] = "#"
        if y not in (194,207,217,228,238): g[y][45] = "#"
    _room(g, 12, 194, 20, 201, doors=((16,201),))
    _room(g, 29, 191, 38, 199, doors=((33,199),))
    _room(g, 47, 194, 56, 201, doors=((47,198),))
    _room(g, 18, 207, 27, 215, doors=((23,207),))
    _room(g, 39, 207, 48, 215, doors=((43,215),))
    _room(g, 28, 225, 39, 235, doors=((33,225),))
    # v2.3 national industrial / war-economy district. This remains one seamless base world.
    _corridor(g, 29, 242, 37, 252)
    _room(g, 4, 252, 19, 266, doors=((11,252),(19,259)))       # aircraft works
    _room(g, 23, 252, 39, 266, doors=((31,252),(39,259)))      # armored vehicle plant
    _room(g, 43, 252, 59, 266, doors=((51,252),(43,259)))      # munitions complex
    _corridor(g, 8, 267, 56, 272)
    _room(g, 4, 273, 19, 287, doors=((11,273),(19,280)))       # fleet shipyard / repair basin control
    _room(g, 23, 273, 39, 287, doors=((31,273),(39,280)))      # fuel refinery
    _room(g, 43, 273, 59, 287, doors=((51,273),(43,280)))      # training command
    _corridor(g, 28, 288, 38, 294)
    _room(g, 20, 294, 44, 307, doors=((32,294),(20,301),(44,301))) # rail/port logistics + war production command
    # v2.4 strategic mobility / global logistics district. National production now has to physically move.
    _corridor(g, 29, 307, 37, 317)
    _room(g, 4, 317, 19, 329, doors=((11,317),(19,323)))       # national distribution depot
    _room(g, 23, 317, 39, 329, doors=((31,317),(39,323)))      # strategic port control
    _room(g, 43, 317, 59, 329, doors=((51,317),(43,323)))      # railhead control
    _corridor(g, 7, 330, 57, 336)
    _corridor(g, 29, 329, 37, 372)
    _room(g, 4, 343, 23, 357, doors=((16,343),(23,350)))       # forward depot
    _room(g, 25, 343, 43, 357, doors=((34,343),(43,350)))      # air logistics hub
    _room(g, 45, 343, 60, 357, doors=((52,343),(45,350)))      # fleet anchorage control
    _corridor(g, 7, 360, 57, 379)
    # Freight yard / truck marshalling lanes / rail crossings.
    for yy in (363,369,375):
        for x in range(8,57):
            if x not in (18,31,44,54): g[yy][x] = "#"
    for y in range(337,379):
        if y not in (345,351,358,366,374): g[y][15] = "#"
        if y not in (341,349,355,364,376): g[y][48] = "#"
    return tuple("".join(r) for r in g)


def _hull_half_width(x: float, w: int = SHIP_LENGTH_M, max_half: float = 13.4) -> float:
    """Smooth Yorktown-like hull/deck taper for collision maps."""
    t=max(0.0,min(1.0,x/max(1.0,w-1)))
    bow=min(1.0,t/.10)
    stern=min(1.0,(1.0-t)/.075)
    fullness=min(bow,stern)
    # flared ends rather than a rectangular barge
    return 2.0 + (max_half-2.0)*(fullness**.58)


def _ship_hull_grid(w: int = SHIP_LENGTH_M, h: int = SHIP_WIDTH_M, partitions: str = "lower") -> Tuple[str, ...]:
    g=_blank(w,h," ")
    cy=(h-1)/2
    # Tapered hull envelope. The inside stays walkable; the outermost ring becomes shell/bulkhead.
    for x in range(w):
        half=_hull_half_width(x,w,12.7)
        y0=max(0,int(math.floor(cy-half))); y1=min(h-1,int(math.ceil(cy+half)))
        for y in range(y0,y1+1): g[y][x]="."
    # shell ring where a neighbor is outside hull
    snapshot=[row[:] for row in g]
    for y in range(h):
        for x in range(w):
            if snapshot[y][x] != ".": continue
            for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx,ny=x+dx,y+dy
                if nx<0 or nx>=w or ny<0 or ny>=h or snapshot[ny][nx]==" ":
                    g[y][x]="#"; break
    # Legacy gangway passage at the port bow remains for save/gameplay compatibility.
    for x in range(0,9):
        for y in range(19,23):
            if 0<=y<h: g[y][x]="."

    def bulkhead(x:int, gaps=(14,15,16)):
        if not (0<x<w-1): return
        for y in range(2,h-2):
            if g[y][x]=="." and y not in gaps: g[y][x]="#"
    def longitudinal(y:int, gaps=()):
        if not (0<y<h-1): return
        for x in range(5,w-5):
            if g[y][x]=="." and x not in gaps: g[y][x]="#"

    if partitions=="engineering":
        # Major machinery subdivisions and centerline access passage.
        for bx in (45,78,111,145,179,212): bulkhead(bx,(7,14,15,16,22))
        longitudinal(8,(32,58,90,122,156,190,222)); longitudinal(21,(32,58,90,122,156,190,222))
        _corridor(g,6,13,w-7,17)
    elif partitions=="lower":
        # Berthing, medical, stores and magazine zones separated by transverse bulkheads.
        for bx in (31,61,91,121,151,181,211): bulkhead(bx,(6,14,15,16,23))
        longitudinal(9,(18,48,78,108,138,168,198,228)); longitudinal(20,(18,48,78,108,138,168,198,228))
        _corridor(g,5,13,w-6,17)
    return tuple("".join(r) for r in g)


def _hangar_grid(w: int = SHIP_LENGTH_M, h: int = SHIP_WIDTH_M) -> Tuple[str, ...]:
    g=_blank(w,h," ")
    # Historical Yorktown-class hangar was roughly 166 m long and 19 m wide.
    x0,x1=35,202; y0,y1=5,24
    for y in range(y0,y1+1):
        for x in range(x0,x1+1): g[y][x]="."
    for x in range(x0,x1+1): g[y0][x]=g[y1][x]="#"
    for y in range(y0,y1+1): g[y][x0]=g[y][x1]="#"
    # Large open hangar bay with transverse fire-curtain boundaries and side shops.
    for bx in (74,116,158):
        for y in range(y0+1,y1):
            if y not in (9,14,15,20): g[y][bx]="#"
    for y in (9,20):
        for x in range(x0+1,x1):
            if x not in (48,74,95,116,137,158,181): g[y][x]="#"
    # Bow gangway/service passage from the legacy pier into the hangar.
    _corridor(g,0,19,36,22)
    return tuple("".join(r) for r in g)


def _flight_grid() -> Tuple[str, ...]:
    w,h=SHIP_LENGTH_M,SHIP_WIDTH_M
    g=_blank(w,h," "); cy=(h-1)/2
    for x in range(w):
        half=_hull_half_width(x,w,14.4)
        y0=max(0,int(math.floor(cy-half))); y1=min(h-1,int(math.ceil(cy+half)))
        for y in range(y0,y1+1): g[y][x]="."
    # deck edge / safety boundary
    snap=[row[:] for row in g]
    for y in range(h):
        for x in range(w):
            if snap[y][x]!=".": continue
            if any(nx<0 or nx>=w or ny<0 or ny>=h or snap[ny][nx]==" " for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1))):
                g[y][x]="#"
    # starboard island footprint, placed aft of midships
    for y in range(20,29):
        for x in range(154,182):
            if 0<=y<h and 0<=x<w: g[y][x]="#"
    for y in (22,23): g[y][154]="."
    return tuple("".join(r) for r in g)


def _island_grid() -> Tuple[str, ...]:
    w,h=SHIP_LENGTH_M,SHIP_WIDTH_M
    g=_blank(w,h," ")
    _room(g,150,18,187,29,doors=((150,23),(168,18),(187,23)))
    # CIC/radio/flag spaces arranged as real rooms instead of one solid block.
    for y in range(19,29):
        if y not in (22,26): g[y][166]="#"
    for x in range(151,187):
        if x not in (158,174,182): g[24][x]="#"
    return tuple("".join(r) for r in g)


def _bridge_grid() -> Tuple[str, ...]:
    w,h=SHIP_LENGTH_M,SHIP_WIDTH_M
    g=_blank(w,h," ")
    _room(g,154,19,183,28,doors=((168,28),(154,23)))
    # port/starboard bridge wings
    _corridor(g,150,21,154,26); _corridor(g,183,21,190,26)
    return tuple("".join(r) for r in g)


LAYERS: Dict[str, WorldLayer] = {
    "BASE": WorldLayer("BASE", "Naval Training Base & Pier", 0, 0, 3.2, _base_grid(), ceiling=False, wall_color="#4b5360", floor_color="#34383e", outdoor=True),
    "LOWER": WorldLayer("LOWER", "Enterprise Lower Deck — Berthing / Medical / Supply / Magazines", SHIP_ORIGIN_X, SHIP_ORIGIN_Y, -3.2, _ship_hull_grid(partitions="lower"), True, "#454b56", "#20262d"),
    "ENGINEERING": WorldLayer("ENGINEERING", "Enterprise Machinery / Engineering Deck", SHIP_ORIGIN_X, SHIP_ORIGIN_Y, 0.0, _ship_hull_grid(partitions="engineering"), True, "#49413e", "#242526"),
    "HANGAR": WorldLayer("HANGAR", "Enterprise Hangar Deck", SHIP_ORIGIN_X, SHIP_ORIGIN_Y, 3.2, _hangar_grid(), True, "#444d57", "#242a31"),
    "FLIGHT": WorldLayer("FLIGHT", "Enterprise Flight Deck", SHIP_ORIGIN_X, SHIP_ORIGIN_Y, 6.4, _flight_grid(), False, "#2f3740", "#2a2d31", True),
    "ISLAND": WorldLayer("ISLAND", "Enterprise Island / Command Spaces", SHIP_ORIGIN_X, SHIP_ORIGIN_Y, 9.6, _island_grid(), True, "#3f4b55", "#222a31"),
    "BRIDGE": WorldLayer("BRIDGE", "Enterprise Navigation Bridge", SHIP_ORIGIN_X, SHIP_ORIGIN_Y, 12.8, _bridge_grid(), True, "#40515b", "#232d34"),
}


def global_xy(layer_key: str, lx: float, ly: float) -> Tuple[float, float]:
    layer = LAYERS[layer_key]
    return layer.origin_x + lx, layer.origin_y + ly


def local_xy(layer_key: str, x: float, y: float) -> Tuple[float, float]:
    layer = LAYERS[layer_key]
    return x - layer.origin_x, y - layer.origin_y


def char_at(layer: WorldLayer, x: float, y: float) -> str:
    lx, ly = local_xy(layer.key, x, y)
    ix, iy = int(lx), int(ly)
    if iy < 0 or iy >= layer.height or ix < 0 or ix >= layer.width:
        return " "
    return layer.grid[iy][ix]


def layer_walkable(layer_key: str, x: float, y: float) -> bool:
    return char_at(LAYERS[layer_key], x, y) == "."


def candidate_layers(camera_z: float, tolerance: float = 1.0) -> List[WorldLayer]:
    feet = camera_z - CAMERA_HEIGHT
    return sorted((l for l in LAYERS.values() if abs(l.floor_z - feet) <= tolerance), key=lambda l: abs(l.floor_z-feet))


def current_layer(x: float, y: float, camera_z: float) -> Optional[WorldLayer]:
    # Exact floor first, then nearby floors so connector travel stays stable.
    for layer in candidate_layers(camera_z, 0.9):
        if layer_walkable(layer.key, x, y):
            return layer
    feet = camera_z - CAMERA_HEIGHT
    walkables = [l for l in LAYERS.values() if layer_walkable(l.key, x, y)]
    return min(walkables, key=lambda l: abs(l.floor_z-feet)) if walkables else None


def world_walkable(x: float, y: float, camera_z: float) -> bool:
    layer = current_layer(x, y, camera_z)
    return bool(layer and layer_walkable(layer.key, x, y))


# Seamless vertical connectors. Activating one moves the player through the same 3D world;
# there is no scene/world replacement or loading transition.
def _conn(key: str, name: str, lx: float, ly: float, a: str, b: str, kind: str = "ladder") -> VerticalConnector:
    x, y = global_xy(a if a != "BASE" else "BASE", lx, ly)
    # For ship connectors lx/ly are ship-local. Base connectors use global-like local coords.
    if a != "BASE":
        x, y = global_xy(a, lx, ly)
    return VerticalConnector(key, name, x, y, LAYERS[a].floor_z, LAYERS[b].floor_z, a, b, kind)


CONNECTORS: Dict[str, VerticalConnector] = {
    "LOWER_ENG_FWD": _conn("LOWER_ENG_FWD", "Forward machinery ladder", 42, 15, "LOWER", "ENGINEERING"),
    "LOWER_ENG_AFT": _conn("LOWER_ENG_AFT", "Aft machinery ladder", 202, 15, "LOWER", "ENGINEERING"),
    "ENG_HANGAR_FWD": _conn("ENG_HANGAR_FWD", "Forward engineering ladder", 55, 15, "ENGINEERING", "HANGAR"),
    "ENG_HANGAR_AFT": _conn("ENG_HANGAR_AFT", "Aft engineering ladder", 188, 15, "ENGINEERING", "HANGAR"),
    "HANGAR_FLIGHT_FWD": _conn("HANGAR_FLIGHT_FWD", "Forward flight-deck ladder", 58, 15, "HANGAR", "FLIGHT"),
    "HANGAR_FLIGHT_MID": _conn("HANGAR_FLIGHT_MID", "Midships flight-deck ladder", 121, 15, "HANGAR", "FLIGHT"),
    "HANGAR_FLIGHT_AFT": _conn("HANGAR_FLIGHT_AFT", "Aft flight-deck ladder", 188, 15, "HANGAR", "FLIGHT"),
    "FLIGHT_ISLAND": _conn("FLIGHT_ISLAND", "Island access ladder", 154, 23, "FLIGHT", "ISLAND"),
    "ISLAND_BRIDGE": _conn("ISLAND_BRIDGE", "Bridge access ladder", 168, 27, "ISLAND", "BRIDGE"),
}


def nearby_connector(x: float, y: float, camera_z: float, radius: float = 1.4) -> Optional[Tuple[VerticalConnector, float]]:
    feet = camera_z - CAMERA_HEIGHT
    best: Optional[Tuple[VerticalConnector, float]] = None
    best_d = radius
    for c in CONNECTORS.values():
        # Can use connector from either end.
        if min(abs(feet-c.from_z), abs(feet-c.to_z)) > 0.85:
            continue
        d = math.hypot(x-c.x, y-c.y)
        if d < best_d:
            best = (c, c.to_z if abs(feet-c.from_z) <= abs(feet-c.to_z) else c.from_z)
            best_d = d
    return best


def _base_interactions() -> List[WorldInteraction]:
    z = LAYERS["BASE"].floor_z
    return [
        WorldInteraction("CAREER", "Personnel Office / Service Record", 8, 8, z, "career", "terminal"),
        WorldInteraction("PROMOTION", "Promotion Board Office", 16, 8, z, "promotion", "terminal"),
        WorldInteraction("ACADEMY", "Academy Written Examination", 28, 8, z, "academy", "terminal"),
        WorldInteraction("TIMELINE", "Historical Reference Library", 40, 8, z, "timeline", "terminal"),
        WorldInteraction("BRIDGE_PORT", "Bridge Simulator — Port Rudder", 7, 24, z, "helm_port"),
        WorldInteraction("BRIDGE_STBD", "Bridge Simulator — Starboard Rudder", 12, 24, z, "helm_stbd"),
        WorldInteraction("BRIDGE_UP", "Bridge Simulator — Increase Engine Order", 7, 27, z, "throttle_up"),
        WorldInteraction("BRIDGE_DOWN", "Bridge Simulator — Decrease Engine Order", 12, 27, z, "throttle_down"),
        WorldInteraction("BRIDGE_EVAL", "Bridge Simulator Evaluator", 9, 33, z, "bridge_order", "terminal"),
        WorldInteraction("DC_FIRE", "Damage Control Trainer — Fire Team", 18, 24, z, "fire_team"),
        WorldInteraction("DC_PUMP", "Damage Control Trainer — Dewatering", 22, 24, z, "pumps"),
        WorldInteraction("DC_ISOLATE", "Damage Control Trainer — Electrical Isolation", 18, 27, z, "isolate"),
        WorldInteraction("DC_VENT", "Damage Control Trainer — Ventilation", 22, 27, z, "ventilate"),
        WorldInteraction("DC_MED", "Damage Control Trainer — Medical", 18, 33, z, "medical"),
        WorldInteraction("DC_POWER", "Damage Control Trainer — Electrical Repair", 22, 33, z, "repair_power"),
        WorldInteraction("DC_EVAL", "Damage Control Trainer Evaluator", 20, 36, z, "damage_eval", "terminal"),
        WorldInteraction("SYS_FIRE", "Full Systems — Engine Room 2 Fire Team", 34, 24, z, "systems_fire"),
        WorldInteraction("SYS_PUMP", "Full Systems — Fixed Dewatering", 38, 24, z, "systems_pump"),
        WorldInteraction("SYS_PORT", "Full Systems — Portable Pump", 42, 24, z, "systems_portable_pump"),
        WorldInteraction("SYS_BREAKER", "Full Systems — Breaker Control", 34, 27, z, "systems_breaker"),
        WorldInteraction("SYS_ELEC", "Full Systems — Electrical Team", 38, 27, z, "systems_electrical"),
        WorldInteraction("SYS_VENT", "Full Systems — Ventilation Isolation", 42, 27, z, "systems_ventilation"),
        WorldInteraction("SYS_REPAIR", "Full Systems — Hull Breach Repair", 34, 33, z, "systems_repair"),
        WorldInteraction("SYS_BOUND", "Full Systems — Watertight Boundary", 38, 33, z, "systems_boundary"),
        WorldInteraction("SYS_EVAL", "Full Systems Evaluator", 42, 33, z, "systems_eval", "terminal"),
        WorldInteraction("WORKBOARD", "Maintenance & Duty Work Board", 49, 24, z, "workboard", "terminal"),
        WorldInteraction("GALLEY", "Galley Serving Line", 48, 33, z, "eat", "life"),
        WorldInteraction("BERTH", "Assigned Berthing", 35, 35, z, "sleep", "life"),
        WorldInteraction("SICKBAY_BASE", "Training Base Sickbay", 51, 35, z, "medical_life", "life"),
        WorldInteraction("CREW", "Watchbill / Crew Roster", 35, 24, z, "crew", "terminal"),
        WorldInteraction("GROUND_OPS", "Expeditionary Ground Operations Center", 8, 52, z, "ground_console", "terminal"),
        WorldInteraction("GROUND_MOTOR", "Motor Pool / Vehicle Dispatch", 28, 52, z, "ground_motor", "life"),
        WorldInteraction("GROUND_AIRFIELD", "Expeditionary Airfield Operations", 48, 52, z, "ground_airfield", "terminal"),
        WorldInteraction("GROUND_AMPHIB", "Amphibious Landing Control", 12, 65, z, "ground_amphib", "terminal"),
        WorldInteraction("GROUND_SUPPLY", "Expeditionary Supply Staging", 36, 65, z, "ground_supply", "life"),
        WorldInteraction("GROUND_RUNWAY", "Training Airfield Flight Line", 52, 65, z, "ground_flightline", "life"),
        WorldInteraction("INF_ARMORY", "Infantry Armory / Equipment Issue", 10, 78, z, "infantry_armory", "life"),
        WorldInteraction("INF_COMMAND", "Fireteam Command & Combined-Arms Briefing", 27, 78, z, "infantry_command", "terminal"),
        WorldInteraction("INF_AID", "Field Aid / Casualty Collection Point", 50, 78, z, "infantry_aid", "life"),
        WorldInteraction("INF_RANGE", "Combined-Arms Training Village Entry", 31, 84, z, "infantry_range", "life"),
        WorldInteraction("LAND_HQ", "Battalion / Platoon Tactical Command Post", 11, 112, z, "land_command", "terminal"),
        WorldInteraction("LAND_ARMOR", "Armored Vehicle Staging / Driver Station", 30, 112, z, "land_armor", "life"),
        WorldInteraction("LAND_ARTY", "Artillery Fire Direction Center", 51, 112, z, "land_artillery", "terminal"),
        WorldInteraction("LAND_AID", "Field Hospital / CASEVAC Control", 12, 131, z, "land_medevac", "life"),
        WorldInteraction("LAND_LOG", "Battalion Logistics & Resupply Point", 32, 131, z, "land_logistics", "life"),
        WorldInteraction("LAND_ENG", "Combat Engineer / Vehicle Maintenance Point", 51, 131, z, "land_engineer", "life"),
        WorldInteraction("LAND_BATTLE", "Battalion Field Maneuver Area Entry", 33, 139, z, "land_battlefield", "life"),
        WorldInteraction("STRAT_HQ", "Theater Strategic Command / Front Line Plot", 11, 183, z, "strategic_command", "terminal"),
        WorldInteraction("STRAT_RECON", "Theater Intelligence & Reconnaissance Center", 30, 183, z, "strategic_recon", "terminal"),
        WorldInteraction("STRAT_LOG", "Theater Logistics / Reinforcement Control", 50, 183, z, "strategic_logistics", "terminal"),
        WorldInteraction("STRAT_FRONT", "Persistent Front Line Maneuver Area", 33, 192, z, "strategic_front", "life"),
        WorldInteraction("ECON_AIR", "Central Aircraft Works Production Office", 11, 259, z, "economy_production", "terminal"),
        WorldInteraction("ECON_ARMOR", "Armored Vehicle Plant Production Office", 31, 259, z, "economy_production", "terminal"),
        WorldInteraction("ECON_MUN", "National Munitions Complex", 51, 259, z, "economy_production", "terminal"),
        WorldInteraction("ECON_SHIP", "Fleet Shipyard / Industrial Repair Control", 11, 280, z, "economy_repair", "terminal"),
        WorldInteraction("ECON_REFINERY", "Strategic Fuel Refinery Control", 31, 280, z, "economy_production", "terminal"),
        WorldInteraction("ECON_TRAIN", "National Training & Research Command", 51, 280, z, "economy_research", "terminal"),
        WorldInteraction("ECON_HQ", "National War Production & Allocation Board", 32, 301, z, "economy_console", "terminal"),
        WorldInteraction("ECON_RAIL", "Rail / Port Strategic Logistics Control", 23, 301, z, "economy_logistics", "terminal"),
        WorldInteraction("LOG_HQ", "Strategic Mobility & Distribution Command", 32, 313, z, "logistics_console", "terminal"),
        WorldInteraction("LOG_NAT", "National Distribution Depot Dispatch", 11, 323, z, "logistics_dispatch", "terminal"),
        WorldInteraction("LOG_PORT", "Strategic Port Delta Convoy Control", 31, 323, z, "logistics_convoy", "terminal"),
        WorldInteraction("LOG_RAIL", "Railhead Echo Movement Control", 51, 323, z, "logistics_route", "terminal"),
        WorldInteraction("LOG_FWD", "Forward Depot Foxtrot Receiving", 16, 350, z, "logistics_receiving", "terminal"),
        WorldInteraction("LOG_AIR", "Air Logistics Hub Golf", 34, 350, z, "logistics_receiving", "terminal"),
        WorldInteraction("LOG_FLEET", "Fleet Anchorage Hotel Logistics", 52, 350, z, "logistics_receiving", "terminal"),
    ]


def _ship_life_interactions() -> List[WorldInteraction]:
    out: List[WorldInteraction] = []
    lower = LAYERS["LOWER"].floor_z
    hang = LAYERS["HANGAR"].floor_z
    eng = LAYERS["ENGINEERING"].floor_z
    for key, name, lx, ly, z, action in [
        ("SHIP_BERTH_FWD", "Forward Enlisted Berthing", 45, 7, lower, "sleep"),
        ("SHIP_BERTH_AFT", "Aft Enlisted Berthing", 205, 22, lower, "sleep"),
        ("SHIP_GALLEY", "Crew Galley / Mess", 118, 7, lower, "eat"),
        ("SHIP_SICKBAY", "Sickbay", 146, 7, lower, "medical_life"),
        ("SHIP_SUPPLY", "Supply Issue Room", 176, 7, lower, "supply"),
        ("SHIP_MAGAZINE", "Magazine Inspection Station", 208, 7, lower, "maintenance:MAGAZINE"),
        ("SHIP_MACHINE", "Machine Shop Workbench", 86, 22, eng, "maintenance:MACHINE_SHOP"),
        ("SHIP_ELECTRICAL", "Electrical Shop Workbench", 158, 22, eng, "maintenance:ELECTRICAL"),
        ("SHIP_DCB", "Damage Control Work Board", 196, 22, eng, "workboard"),
        ("SHIP_AIRSHOP", "Aviation Maintenance Shop", 52, 7, hang, "maintenance:AVIATION"),
        ("SHIP_ORDSHOP", "Ordnance Maintenance Shop", 188, 7, hang, "maintenance:ORDNANCE"),
        ("SHIP_MOORING", "Mooring & Sea Detail Station", 14, 21, hang, "mooring"),
        ("SHIP_MUSTER", "Abandon Ship Muster / Survival Gear", 104, 6, hang, "survival_muster"),
        ("SHIP_ANCHOR", "Forecastle Anchor Control", 18, 15, LAYERS["FLIGHT"].floor_z, "anchor"),
        ("SHIP_NAV", "Navigation Plot / Ship Motion Board", 166, 22, LAYERS["BRIDGE"].floor_z, "navigation"),
        ("SHIP_FLEET_PLOT", "Task Force Tactical Plot", 160, 22, LAYERS["BRIDGE"].floor_z, "fleet_console"),
        ("SHIP_SIGNAL_BRIDGE", "Signal Bridge / Fleet Communications", 176, 28, LAYERS["ISLAND"].floor_z, "fleet_signal"),
        ("SHIP_FLEET_LOGISTICS", "Fleet Logistics & Replenishment Board", 174, 8, LAYERS["HANGAR"].floor_z, "fleet_logistics"),
        ("SHIP_CAMPAIGN_PLOT", "Operational Campaign Planning Plot", 175, 27, LAYERS["BRIDGE"].floor_z, "campaign_console"),
        ("SHIP_PORT_LOGISTICS", "Base / Convoy Logistics Board", 160, 8, LAYERS["HANGAR"].floor_z, "campaign_logistics"),
        ("SHIP_AIR_WING", "Air Group Operations Planning Room", 160, 27, LAYERS["ISLAND"].floor_z, "air_wing_console"),
        ("SHIP_READY_ROOM", "Squadron Ready Room / Flight Briefing", 92, 8, LAYERS["HANGAR"].floor_z, "air_wing_console"),
    ]:
        x, y = SHIP_ORIGIN_X + lx, SHIP_ORIGIN_Y + ly
        out.append(WorldInteraction(key, name, x, y, z, action, "life"))
    return out


BASE_INTERACTIONS = tuple(_base_interactions())
SHIP_LIFE_INTERACTIONS = tuple(_ship_life_interactions())


def all_static_interactions() -> Tuple[WorldInteraction, ...]:
    return BASE_INTERACTIONS + SHIP_LIFE_INTERACTIONS


def nearest_static_interaction(x: float, y: float, camera_z: float, radius: float = 1.6) -> Optional[WorldInteraction]:
    feet = camera_z - CAMERA_HEIGHT
    best = None
    best_d = radius
    for i in all_static_interactions():
        if abs(i.floor_z-feet) > 0.9:
            continue
        d = math.hypot(i.x-x, i.y-y)
        if d < best_d:
            best, best_d = i, d
    return best


def layer_label(x: float, y: float, camera_z: float) -> str:
    layer = current_layer(x,y,camera_z)
    return layer.name if layer else "Open World / Exterior"


def ship_deck_for_floor(floor_z: float) -> Optional[str]:
    if abs(floor_z-LAYERS["BRIDGE"].floor_z) < .6 or abs(floor_z-LAYERS["ISLAND"].floor_z) < .6:
        return "ISLAND"
    if abs(floor_z-LAYERS["FLIGHT"].floor_z) < .6:
        return "FLIGHT"
    if abs(floor_z-LAYERS["HANGAR"].floor_z) < .6:
        return "HANGAR"
    if abs(floor_z-LAYERS["ENGINEERING"].floor_z) < .6:
        return "ENGINEERING"
    return None
