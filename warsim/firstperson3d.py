from __future__ import annotations

import math
import random
import time
import tkinter as tk
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .config import APP_NAME, VERSION, COLORS
from .data import ERAS, BRANCHES, WRITTEN_QUESTIONS
from .models import CareerProfile, BridgeState, DamageState
from .persistence import load_profile, save_profile
from .systems import (
    promotion_status, promote, apply_written_exam,
    update_bridge, bridge_next_order, bridge_result,
    damage_tick, damage_action, damage_result,
    generate_crew, apply_shipboard_walk_result, apply_ship_systems_result,
)
from .ship import (
    create_training_ship, ship_tick, evaluate_ship_scenario, ship_summary,
    toggle_breaker, toggle_ventilation, toggle_firemain_valve, route_pump,
    toggle_hatch as ship_toggle_hatch, assign_team,
)
from .walkship import (
    create_shipboard_walk_state, move_player, interact, advance_shipboard,
    current_zone, current_station, nearby_equipment, nearby_hatch,
    qualification_status, shipboard_summary, evaluate_shipboard,
    update_crew_movement, active_objective, objective_navigation, ship_alarm_state,
    tile_walkable, DECK_MAPS, DECK_NAMES, EQUIPMENT, HATCHES, STATION_ANCHORS,
)


@dataclass(frozen=True)
class WorldNode:
    key: str
    x: float
    y: float
    name: str
    action: str
    kind: str = "terminal"


# v0.7's 3D training facility is deliberately a fictional interface/hub, not historical geometry.
HUB_MAP = (
    "##################################",
    "#...............##...............#",
    "#...............##...............#",
    "#...............##...............#",
    "#................................#",
    "#................................#",
    "######..##########..########..####",
    "#................................#",
    "#................................#",
    "#................................#",
    "######..##########..########..####",
    "#................................#",
    "#................................#",
    "#................................#",
    "######..##########..########..####",
    "#................................#",
    "#................................#",
    "#................................#",
    "#................................#",
    "#................................#",
    "##################################",
)

BRIDGE_MAP = (
    "########################",
    "#......................#",
    "#......................#",
    "#....####......####....#",
    "#....#..#......#..#....#",
    "#....####......####....#",
    "#......................#",
    "#......................#",
    "#...####........####...#",
    "#...#..#........#..#...#",
    "#...####........####...#",
    "#......................#",
    "#......................#",
    "#......................#",
    "#......................#",
    "########################",
)

DAMAGE_MAP = BRIDGE_MAP
SYSTEMS_MAP = (
    "################################",
    "#..............................#",
    "#..............................#",
    "#....######........######......#",
    "#....#....#........#....#......#",
    "#....######........######......#",
    "#..............................#",
    "#..............................#",
    "######..##########..############",
    "#..............................#",
    "#..............................#",
    "#....######........######......#",
    "#....#....#........#....#......#",
    "#....######........######......#",
    "#..............................#",
    "#..............................#",
    "#..............................#",
    "################################",
)

HUB_NODES = {
    "CAREER": WorldNode("CAREER", 4.0, 3.0, "Career & Service Record", "career"),
    "ACADEMY": WorldNode("ACADEMY", 11.0, 3.0, "Academy / Written Examination", "academy"),
    "BRIDGE": WorldNode("BRIDGE", 22.0, 3.0, "Bridge Practical Simulator", "bridge", "portal"),
    "DAMAGE": WorldNode("DAMAGE", 29.0, 3.0, "Damage Control Trainer", "damage", "portal"),
    "SYSTEMS": WorldNode("SYSTEMS", 4.0, 8.5, "Full Ship Systems Casualty Trainer", "systems", "portal"),
    "ENTERPRISE": WorldNode("ENTERPRISE", 12.0, 8.5, "USS Enterprise CV-6 — Midway Duty", "enterprise", "portal"),
    "HISTORY": WorldNode("HISTORY", 22.0, 8.5, "Historical Operations / Midway", "historical", "portal"),
    "CREW": WorldNode("CREW", 29.0, 8.5, "Crew & Watch Roster", "crew"),
    "TIMELINE": WorldNode("TIMELINE", 4.0, 13.0, "Historical Timeline Archive", "timeline"),
    "QUALS": WorldNode("QUALS", 12.0, 13.0, "Qualifications Record", "qualifications"),
    "PROMOTION": WorldNode("PROMOTION", 22.0, 13.0, "Promotion Board", "promotion"),
    "HELP": WorldNode("HELP", 29.0, 13.0, "Operations Briefing", "help"),
}

BRIDGE_NODES = {
    "HELM_PORT": WorldNode("HELM_PORT", 6.0, 4.5, "Helm — Left Rudder", "helm_port"),
    "HELM_STBD": WorldNode("HELM_STBD", 17.0, 4.5, "Helm — Right Rudder", "helm_stbd"),
    "THROTTLE_UP": WorldNode("THROTTLE_UP", 6.0, 9.5, "Engine Order — Increase", "throttle_up"),
    "THROTTLE_DOWN": WorldNode("THROTTLE_DOWN", 17.0, 9.5, "Engine Order — Decrease", "throttle_down"),
    "ORDER": WorldNode("ORDER", 11.5, 12.5, "Bridge Evaluator / Next Order", "bridge_order"),
    "EXIT": WorldNode("EXIT", 2.0, 13.5, "Exit to Training Center", "hub", "portal"),
}

DAMAGE_NODES = {
    "FIRE": WorldNode("FIRE", 3.0, 4.5, "Repair Locker — Fire Team", "fire_team"),
    "PUMPS": WorldNode("PUMPS", 11.5, 4.5, "Dewatering Pump Control", "pumps"),
    "ISOLATE": WorldNode("ISOLATE", 20.0, 4.5, "Electrical Isolation", "isolate"),
    "VENT": WorldNode("VENT", 5.0, 9.5, "Ventilation Control", "ventilate"),
    "MED": WorldNode("MED", 11.5, 9.5, "Medical Team", "medical"),
    "POWER": WorldNode("POWER", 18.0, 9.5, "Electrical Repair", "repair_power"),
    "EVAL": WorldNode("EVAL", 11.5, 12.5, "Evaluate Damage Control Drill", "damage_eval"),
    "EXIT": WorldNode("EXIT", 2.0, 13.5, "Exit to Training Center", "hub", "portal"),
}

SYSTEMS_NODES = {
    "ENG2_FIRE": WorldNode("ENG2_FIRE", 7.0, 4.5, "Engine Room 2 — Dispatch Fire Team", "systems_fire"),
    "MACH_PUMP": WorldNode("MACH_PUMP", 22.0, 4.5, "Machinery Room — Fixed Dewatering", "systems_pump"),
    "MACH_PORTABLE": WorldNode("MACH_PORTABLE", 27.0, 7.0, "Machinery Room — Portable Pump", "systems_portable_pump"),
    "ENG2_BREAKER": WorldNode("ENG2_BREAKER", 7.0, 12.0, "Engine Room 2 — Breaker", "systems_breaker"),
    "ENG2_ELECTRICAL": WorldNode("ENG2_ELECTRICAL", 12.0, 12.0, "Engine Room 2 — Electrical Team", "systems_electrical"),
    "ENG2_VENT": WorldNode("ENG2_VENT", 12.0, 4.5, "Engine Room 2 — Ventilation Isolation", "systems_ventilation"),
    "MACH_REPAIR": WorldNode("MACH_REPAIR", 22.0, 12.0, "Machinery Room — Seal Hull Breach", "systems_repair"),
    "BOUNDARY": WorldNode("BOUNDARY", 27.0, 12.0, "Watertight Boundary Board", "systems_boundary"),
    "EVAL": WorldNode("EVAL", 15.0, 15.0, "Evaluate Ship Systems Drill", "systems_eval"),
    "EXIT": WorldNode("EXIT", 2.0, 15.0, "Exit to Training Center", "hub", "portal"),
}


def _hex_rgb(value: str) -> Tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))


def shade(value: str, factor: float) -> str:
    r, g, b = _hex_rgb(value)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def project_point(px: float, py: float, pz: float, cx: float, cy: float, cz: float,
                  yaw: float, pitch: float, width: int, height: int, fov_deg: float = 75.0):
    dx, dy, dz = px - cx, py - cy, pz - cz
    sy, cyaw = math.sin(yaw), math.cos(yaw)
    forward = cyaw * dx + sy * dy
    right = -sy * dx + cyaw * dy
    cp, sp = math.cos(pitch), math.sin(pitch)
    f2 = cp * forward + sp * dz
    up = -sp * forward + cp * dz
    if f2 <= 0.08:
        return None
    focal = (width * 0.5) / math.tan(math.radians(fov_deg) * 0.5)
    sx = width * 0.5 + right / f2 * focal
    sy2 = height * 0.5 - up / f2 * focal
    return sx, sy2, f2


def grid_walkable(grid: Tuple[str, ...], x: float, y: float) -> bool:
    ix, iy = int(x), int(y)
    if iy < 0 or iy >= len(grid) or ix < 0 or ix >= len(grid[0]):
        return False
    return grid[iy][ix] != "#"


class FirstPerson3DApp(tk.Tk):
    """War Simulator v0.7 full-game first-person 3D shell.

    It is a dependency-free software 3D renderer: actual perspective-projected world geometry
    is drawn on a Tk Canvas. Historical Enterprise geometry remains a training schematic.
    """

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{VERSION} — First Person 3D")
        self.geometry("1440x900")
        self.minsize(1024, 640)
        self.configure(bg="#05070b")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.profile = load_profile() or CareerProfile()
        self.shipboard = create_shipboard_walk_state()
        self.bridge = BridgeState()
        self.damage = DamageState()
        self.ship_systems = create_training_ship()

        self.world = "HUB"
        self.x, self.y, self.z = 8.0, 18.0, 1.62
        self.yaw, self.pitch = -math.pi / 2, 0.0
        self.keys = set()
        self.overlay: Optional[str] = "welcome"
        self.message = "Welcome to War Simulator v0.7 — full-game first-person 3D mode."
        self.message_until = time.monotonic() + 7.0
        self.exam_index = 0
        self.exam_correct = 0
        self.exam_topic_hits: Dict[str, int] = {}
        self.new_name = ""
        self.new_branch_index = 0
        self.new_era_index = list(ERAS).index("World War II") if "World War II" in ERAS else 0
        self.fullscreen = False
        self.bridge_accum = 0.0
        self.damage_accum = 0.0
        self.systems_accum = 0.0
        self.running_time = False
        self.last_tick = time.monotonic()
        self.last_mouse: Optional[Tuple[int, int]] = None
        self._frame_counter = 0
        self._fps_time = time.monotonic()
        self.fps = 0
        self._frames = 0
        self.destroyed = False

        self.canvas = tk.Canvas(self, bg="#070b12", highlightthickness=0, cursor="crosshair")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.focus_set()

        self.bind_all("<KeyPress>", self._key_down)
        self.bind_all("<KeyRelease>", self._key_up)
        self.canvas.bind("<ButtonPress-1>", self._mouse_start)
        self.canvas.bind("<B1-Motion>", self._mouse_drag)
        self.canvas.bind("<Configure>", lambda _e: self.canvas.focus_set())

        self.after(20, self._loop)

    # ---------------------------- input / loop ----------------------------
    def _key_down(self, event):
        key = event.keysym.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if self.overlay:
            self._overlay_key(key)
            return
        if key == "e":
            self._interact()
        elif key == "f":
            self._set_message(self._objective_text(), 5)
        elif key == "r":
            self.running_time = not self.running_time
            self.shipboard.running = self.running_time
            self._set_message(f"Historical clock {'RUNNING' if self.running_time else 'PAUSED'}.")
        elif key == "escape":
            self.overlay = "pause"
        elif key == "f1":
            self.overlay = "help"
        elif key == "f10":
            self._open_legacy_ui()
        elif key == "f11":
            self.fullscreen = not self.fullscreen
            self.attributes("-fullscreen", self.fullscreen)
        elif key == "f9":
            self._enter_world("HUB")

    def _key_up(self, event):
        self.keys.discard(event.keysym.lower())

    def _mouse_start(self, event):
        self.last_mouse = (event.x, event.y)
        self.canvas.focus_set()

    def _mouse_drag(self, event):
        if self.overlay or self.last_mouse is None:
            self.last_mouse = (event.x, event.y)
            return
        dx = event.x - self.last_mouse[0]
        dy = event.y - self.last_mouse[1]
        self.last_mouse = (event.x, event.y)
        self.yaw += dx * 0.006
        self.pitch = max(-0.55, min(0.55, self.pitch - dy * 0.004))
        if self.world == "ENTERPRISE":
            self.shipboard.angle = self.yaw

    def _loop(self):
        if self.destroyed:
            return
        now = time.monotonic()
        dt = min(0.08, max(0.001, now - self.last_tick))
        self.last_tick = now
        self._update(dt)
        self._render()
        self._frames += 1
        if now - self._fps_time >= 1.0:
            self.fps = self._frames
            self._frames = 0
            self._fps_time = now
        self.after(20, self._loop)

    def _update(self, dt: float):
        if self.overlay:
            return
        turn = 0.0
        if "left" in self.keys:
            turn -= 1.0
        if "right" in self.keys:
            turn += 1.0
        self.yaw += turn * dt * 2.1
        self.pitch += ((1 if "up" in self.keys else 0) - (1 if "down" in self.keys else 0)) * dt * 1.0
        self.pitch = max(-0.55, min(0.55, self.pitch))

        forward = (1 if "w" in self.keys else 0) - (1 if "s" in self.keys else 0)
        strafe = (1 if "d" in self.keys else 0) - (1 if "a" in self.keys else 0)
        if forward or strafe:
            if self.world == "ENTERPRISE":
                self.shipboard.angle = self.yaw
                move_player(self.shipboard, forward=forward * dt * 7.0, strafe=strafe * dt * 7.0)
                self.x, self.y, self.yaw = self.shipboard.x, self.shipboard.y, self.shipboard.angle
            else:
                self._move_generic(forward, strafe, dt)

        if self.world == "ENTERPRISE":
            update_crew_movement(self.shipboard, dt)
            if self.running_time:
                self.bridge_accum += dt
                # One real second = one historical minute in normal test speed.
                while self.bridge_accum >= 1.0:
                    advance_shipboard(self.shipboard, 1)
                    self.bridge_accum -= 1.0
        elif self.world == "BRIDGE":
            update_bridge(self.bridge, dt)
        elif self.world == "DAMAGE":
            self.damage_accum += dt
            while self.damage_accum >= 1.0 and not (self.damage.resolved or self.damage.failed):
                damage_tick(self.damage)
                self.damage_accum -= 1.0
        elif self.world == "SYSTEMS":
            self.systems_accum += dt
            while self.systems_accum >= 0.25 and not (self.ship_systems.resolved or self.ship_systems.failed):
                ship_tick(self.ship_systems, 0.25)
                self.systems_accum -= 0.25

    def _move_generic(self, forward: float, strafe: float, dt: float):
        speed = (6.6 if "shift_l" in self.keys or "shift_r" in self.keys else 4.2) * dt
        dx = math.cos(self.yaw) * forward + math.cos(self.yaw + math.pi / 2) * strafe
        dy = math.sin(self.yaw) * forward + math.sin(self.yaw + math.pi / 2) * strafe
        grid = self._current_grid()
        nx, ny = self.x + dx * speed, self.y + dy * speed
        radius = 0.23
        if grid_walkable(grid, nx + math.copysign(radius, dx or 1), self.y):
            self.x = nx
        if grid_walkable(grid, self.x, ny + math.copysign(radius, dy or 1)):
            self.y = ny

    # ---------------------------- world / interaction ----------------------------
    def _current_grid(self):
        if self.world == "HUB":
            return HUB_MAP
        if self.world == "BRIDGE":
            return BRIDGE_MAP
        if self.world == "DAMAGE":
            return DAMAGE_MAP
        if self.world == "SYSTEMS":
            return SYSTEMS_MAP
        return DECK_MAPS[self.shipboard.deck]

    def _nodes(self):
        if self.world == "HUB":
            return HUB_NODES
        if self.world == "BRIDGE":
            return BRIDGE_NODES
        if self.world == "DAMAGE":
            return DAMAGE_NODES
        if self.world == "SYSTEMS":
            return SYSTEMS_NODES
        return {}

    def _nearest_node(self, radius: float = 1.7) -> Optional[WorldNode]:
        best = None
        best_d = radius
        for node in self._nodes().values():
            d = math.hypot(node.x - self.x, node.y - self.y)
            if d < best_d:
                best, best_d = node, d
        return best

    def _enterprise_shore_portal_nearby(self) -> bool:
        return self.shipboard.deck == "ISLAND" and math.hypot(self.shipboard.x - 14.7, self.shipboard.y - 16.0) < 1.65

    def _interact(self):
        if self.world == "ENTERPRISE":
            if self._enterprise_shore_portal_nearby():
                self._enter_world("HUB")
                return
            ok, msg = interact(self.shipboard)
            self._set_message(msg, 5)
            if ok:
                self.x, self.y, self.yaw = self.shipboard.x, self.shipboard.y, self.shipboard.angle
            return

        node = self._nearest_node()
        if not node:
            self._set_message("No usable control within reach.", 2)
            return
        action = node.action
        if self.world == "HUB":
            self._hub_action(action)
        elif self.world == "BRIDGE":
            self._bridge_action(action)
        elif self.world == "DAMAGE":
            self._damage_action(action)
        elif self.world == "SYSTEMS":
            self._systems_action(action)

    def _hub_action(self, action: str):
        if action == "bridge":
            self.bridge = BridgeState()
            self._enter_world("BRIDGE")
        elif action == "damage":
            self.damage = DamageState()
            self._enter_world("DAMAGE")
        elif action == "systems":
            self.ship_systems = create_training_ship()
            self._enter_world("SYSTEMS")
        elif action in ("enterprise", "historical"):
            if action == "historical":
                self.shipboard = create_shipboard_walk_state()
                self.running_time = True
                self.shipboard.running = True
            self._enter_world("ENTERPRISE")
        elif action == "academy":
            self.exam_index = 0
            self.exam_correct = 0
            self.exam_topic_hits = {}
            self.overlay = "academy"
        else:
            self.overlay = action

    def _start_new_career(self):
        self.new_name = ""
        self.new_branch_index = 0
        eras = list(ERAS)
        self.new_era_index = eras.index("World War II") if "World War II" in eras else 0
        self.overlay = "new_career"

    def _bridge_action(self, action: str):
        if action == "hub":
            self._enter_world("HUB")
        elif action == "helm_port":
            self.bridge.rudder = max(-35, self.bridge.rudder - 7)
            self._set_message(f"Rudder ordered {self.bridge.rudder:.0f}°.")
        elif action == "helm_stbd":
            self.bridge.rudder = min(35, self.bridge.rudder + 7)
            self._set_message(f"Rudder ordered {self.bridge.rudder:.0f}°.")
        elif action == "throttle_up":
            self.bridge.throttle = min(1.0, self.bridge.throttle + 0.15)
            self._set_message(f"Throttle {self.bridge.throttle*100:.0f}%.")
        elif action == "throttle_down":
            self.bridge.throttle = max(0.0, self.bridge.throttle - 0.15)
            self._set_message(f"Throttle {self.bridge.throttle*100:.0f}%.")
        elif action == "bridge_order":
            err = abs(((self.bridge.ordered_heading - self.bridge.heading + 180) % 360) - 180)
            if err <= 7 and self.bridge.held_seconds >= 2:
                bridge_next_order(self.bridge)
                self._set_message(f"Order satisfied. New heading: {self.bridge.ordered_heading:.0f}°.")
            elif self.bridge.elapsed >= 20 and self.bridge.completed_orders >= 2:
                score = bridge_result(self.profile, self.bridge)
                save_profile(self.profile)
                self._set_message(f"Bridge practical evaluated: {score:.0f}% — saved.", 6)
            else:
                self._set_message(f"Hold ordered heading. Error {err:.1f}°, stable {self.bridge.held_seconds:.1f}s.", 4)

    def _damage_action(self, action: str):
        if action == "hub":
            self._enter_world("HUB")
        elif action == "damage_eval":
            score = damage_result(self.profile, self.damage)
            save_profile(self.profile)
            self._set_message(f"Damage-control drill evaluated: {score:.0f}% — saved.", 6)
        else:
            self._set_message(damage_action(self.damage, action), 4)

    def _systems_action(self, action: str):
        s = self.ship_systems
        if action == "hub":
            self._enter_world("HUB")
        elif action == "systems_fire":
            self._set_message(assign_team(s, "REPAIR_1", "FIREFIGHT", "ENGINE_2"), 5)
        elif action == "systems_pump":
            self._set_message(route_pump(s, "FIXED_1", "MACHINERY"), 5)
        elif action == "systems_portable_pump":
            self._set_message(route_pump(s, "PORTABLE_1", "MACHINERY"), 5)
        elif action == "systems_breaker":
            self._set_message(toggle_breaker(s, "ENGINE_2"), 5)
        elif action == "systems_electrical":
            self._set_message(assign_team(s, "ELECTRICAL", "ELECTRICAL", "ENGINE_2"), 5)
        elif action == "systems_ventilation":
            self._set_message(toggle_ventilation(s, "ENGINE_2"), 5)
        elif action == "systems_repair":
            self._set_message(assign_team(s, "REPAIR_2", "SEAL", "MACHINERY"), 5)
        elif action == "systems_boundary":
            changed = []
            for hk in ("H17", "H21", "H25", "H26"):
                if s.hatches[hk].open:
                    ship_toggle_hatch(s, hk)
                    changed.append(hk)
            self._set_message("Watertight casualty boundary set: " + (", ".join(changed) if changed else "already secured"), 5)
        elif action == "systems_eval":
            score = evaluate_ship_scenario(s)
            apply_ship_systems_result(self.profile, score, ship_summary(s))
            save_profile(self.profile)
            self._set_message(f"Full ship-systems drill evaluated: {score:.0f}% — saved.", 6)

    def _enter_world(self, world: str):
        self.overlay = None
        self.world = world
        if world == "HUB":
            self.x, self.y, self.z = 8.0, 18.0, 1.62
            self.yaw, self.pitch = -math.pi/2, 0.0
            self.running_time = False
            self._set_message("Naval Training & Career Center — all game modes are accessible in-world.", 5)
        elif world == "ENTERPRISE":
            self.x, self.y = self.shipboard.x, self.shipboard.y
            self.z = 1.62
            self.yaw, self.pitch = self.shipboard.angle, 0.0
            self._set_message("USS Enterprise (CV-6) shipboard duty. Training-schematic geometry; historical timeline remains locked.", 6)
        elif world == "BRIDGE":
            self.x, self.y, self.z = 11.5, 13.5, 1.62
            self.yaw, self.pitch = -math.pi/2, 0.0
            self._set_message("3D Bridge Practical. Operate the helm, engine order controls, and evaluator.", 5)
        elif world == "DAMAGE":
            self.x, self.y, self.z = 11.5, 13.5, 1.62
            self.yaw, self.pitch = -math.pi/2, 0.0
            self._set_message("3D Damage Control Trainer. Physically report to each control station.", 5)
        elif world == "SYSTEMS":
            self.x, self.y, self.z = 15.0, 16.0, 1.62
            self.yaw, self.pitch = -math.pi/2, 0.0
            self._set_message("3D Ship Systems casualty trainer — fire, flooding, electrical and repair actions are live.", 5)

    # ---------------------------- overlays ----------------------------
    def _overlay_key(self, key: str):
        if self.overlay == "new_career":
            if key == "escape":
                self.overlay = "career"
                return
            if key == "return":
                name = self.new_name.strip() or "Recruit"
                eras = list(ERAS)
                self.profile = CareerProfile(name=name, branch=BRANCHES[self.new_branch_index], era=eras[self.new_era_index])
                save_profile(self.profile)
                self.overlay = "career"
                self._set_message(f"New career created for {name}.", 5)
                return
            if key == "tab":
                self.new_branch_index = (self.new_branch_index + 1) % len(BRANCHES)
                return
            if key == "f2":
                self.new_era_index = (self.new_era_index + 1) % len(ERAS)
                return
            if key == "backspace":
                self.new_name = self.new_name[:-1]
                return
            if len(key) == 1 and (key.isalnum() or key in " -_.'") and len(self.new_name) < 32:
                self.new_name += key.upper() if not self.new_name else key
                return
            return
        if key in ("escape", "e"):
            if self.overlay == "welcome":
                self.overlay = None
            elif self.overlay == "pause":
                self.overlay = None
            else:
                self.overlay = None
            return
        if self.overlay == "academy" and key in ("1", "2", "3", "4"):
            self._answer_exam(int(key) - 1)
        elif self.overlay == "career" and key == "n":
            self._start_new_career()
        elif self.overlay == "promotion" and key == "p":
            ok, msg = promote(self.profile)
            if ok:
                save_profile(self.profile)
            self._set_message(msg, 7)
            self.overlay = None
        elif self.overlay == "pause":
            if key == "s":
                save_profile(self.profile)
                self._set_message("Career saved.", 4)
                self.overlay = None
            elif key == "h":
                self._enter_world("HUB")
            elif key == "q":
                self.on_close()
        elif self.overlay == "welcome" and key in ("return", "space"):
            self.overlay = None

    def _answer_exam(self, answer: int):
        q = WRITTEN_QUESTIONS[self.exam_index]
        if answer == q["answer"]:
            self.exam_correct += 1
            self.exam_topic_hits[q["topic"]] = self.exam_topic_hits.get(q["topic"], 0) + 1
            self._set_message("Correct.", 1.5)
        else:
            self._set_message(f"Incorrect. Review topic: {q['topic']}.", 2.5)
        self.exam_index += 1
        if self.exam_index >= len(WRITTEN_QUESTIONS):
            score = self.exam_correct / len(WRITTEN_QUESTIONS) * 100.0
            apply_written_exam(self.profile, score, self.exam_topic_hits)
            save_profile(self.profile)
            self.overlay = "exam_result"
            self._set_message(f"Written examination complete: {score:.0f}% — saved.", 6)

    def _open_legacy_ui(self):
        self._set_message("Legacy/admin 2D UI is available only when launching legacy_ui.py directly in v0.7.", 5)

    # ---------------------------- rendering ----------------------------
    def _render(self):
        c = self.canvas
        w, h = max(2, c.winfo_width()), max(2, c.winfo_height())
        c.delete("all")
        horizon = int(h * 0.5 + self.pitch * h * 0.45)
        c.create_rectangle(0, 0, w, horizon, fill="#0a1322", outline="")
        c.create_rectangle(0, horizon, w, h, fill="#161a20", outline="")
        # horizon glow / depth cue
        c.create_rectangle(0, horizon-1, w, horizon+1, fill="#364154", outline="")

        faces = []
        self._collect_world_geometry(faces, w, h)
        faces.sort(key=lambda item: item[0], reverse=True)
        for depth, pts, fill, outline in faces:
            if len(pts) >= 6:
                c.create_polygon(*pts, fill=fill, outline=outline, width=1)

        self._render_entities(w, h)
        self._render_hud(w, h)
        if self.overlay:
            self._render_overlay(w, h)

    def _collect_world_geometry(self, faces: list, w: int, h: int):
        grid = self._current_grid()
        wall_color = "#48515e" if self.world == "HUB" else "#3e4652"
        if self.world == "BRIDGE":
            wall_color = "#40515b"
        if self.world in ("DAMAGE", "SYSTEMS"):
            wall_color = "#4a4240"
        ceiling_z = 2.75
        radius = 14
        minx, maxx = max(0, int(self.x)-radius), min(len(grid[0])-1, int(self.x)+radius)
        miny, maxy = max(0, int(self.y)-radius), min(len(grid)-1, int(self.y)+radius)

        # floor tiles (actual perspective-projected horizontal 3D quads)
        for gy in range(miny, maxy+1):
            for gx in range(minx, maxx+1):
                if grid[gy][gx] == "#":
                    continue
                dist = math.hypot(gx+0.5-self.x, gy+0.5-self.y)
                if dist > radius:
                    continue
                base = "#232a32" if (gx + gy) % 2 == 0 else "#20262d"
                self._add_face(faces, [(gx, gy, 0), (gx+1, gy, 0), (gx+1, gy+1, 0), (gx, gy+1, 0)], base, "", w, h)
                if dist > 1.0:
                    self._add_face(faces, [(gx, gy, ceiling_z), (gx, gy+1, ceiling_z), (gx+1, gy+1, ceiling_z), (gx+1, gy, ceiling_z)], "#171c24", "", w, h)

        # wall faces only where exposed to non-wall cells
        dirs = [(-1, 0, 0.86), (1, 0, 0.68), (0, -1, 0.78), (0, 1, 0.62)]
        for gy in range(miny, maxy+1):
            for gx in range(minx, maxx+1):
                if grid[gy][gx] != "#":
                    continue
                if math.hypot(gx+0.5-self.x, gy+0.5-self.y) > radius:
                    continue
                for dx, dy, sf in dirs:
                    nx, ny = gx+dx, gy+dy
                    exposed = ny < 0 or ny >= len(grid) or nx < 0 or nx >= len(grid[0]) or grid[ny][nx] != "#"
                    if not exposed:
                        continue
                    if dx == -1:
                        quad = [(gx, gy, 0), (gx, gy+1, 0), (gx, gy+1, ceiling_z), (gx, gy, ceiling_z)]
                    elif dx == 1:
                        quad = [(gx+1, gy+1, 0), (gx+1, gy, 0), (gx+1, gy, ceiling_z), (gx+1, gy+1, ceiling_z)]
                    elif dy == -1:
                        quad = [(gx+1, gy, 0), (gx, gy, 0), (gx, gy, ceiling_z), (gx+1, gy, ceiling_z)]
                    else:
                        quad = [(gx, gy+1, 0), (gx+1, gy+1, 0), (gx+1, gy+1, ceiling_z), (gx, gy+1, ceiling_z)]
                    self._add_face(faces, quad, shade(wall_color, sf), "#232b35", w, h)

        # hatches on Enterprise are 3D blockers/doors.
        if self.world == "ENTERPRISE":
            for key, hatch in HATCHES.items():
                if hatch.deck != self.shipboard.deck:
                    continue
                opened = self.shipboard.hatches.get(key, True)
                col = "#2f7f65" if opened else "#9a3d46"
                self._add_box(faces, hatch.x-0.12, hatch.y-0.45, 0.15, 0.24, 0.9, 2.25, col, w, h)

    def _add_face(self, faces, vertices, fill, outline, w, h):
        """Project one polygon with near-plane clipping and coarse screen culling.

        Older builds discarded a complete face as soon as any vertex crossed the camera
        plane.  That was cheap, but it caused the very visible wall/door popping seen
        when walking close to geometry.  v2.5 clips polygons against the near plane
        before projection instead.
        """
        syaw, cyaw = math.sin(self.yaw), math.cos(self.yaw)
        cp, sp = math.cos(self.pitch), math.sin(self.pitch)
        camera = []
        for vx, vy, vz in vertices:
            dx, dy, dz = vx-self.x, vy-self.y, vz-self.z
            forward = cyaw*dx + syaw*dy
            right = -syaw*dx + cyaw*dy
            depth = cp*forward + sp*dz
            up = -sp*forward + cp*dz
            camera.append((right, up, depth))

        near = 0.10
        clipped = []
        if not camera:
            return
        prev = camera[-1]
        prev_in = prev[2] >= near
        for cur in camera:
            cur_in = cur[2] >= near
            if cur_in != prev_in:
                denom = cur[2]-prev[2]
                if abs(denom) > 1e-9:
                    t = (near-prev[2])/denom
                    clipped.append((
                        prev[0]+(cur[0]-prev[0])*t,
                        prev[1]+(cur[1]-prev[1])*t,
                        near,
                    ))
            if cur_in:
                clipped.append(cur)
            prev, prev_in = cur, cur_in
        if len(clipped) < 3:
            return

        # Seamless world uses aggressive distance culling to protect frame time.
        max_distance = getattr(self, "render_distance", 38.0)
        depths = [v[2] for v in clipped]
        if min(depths) > max_distance:
            return
        focal = (w * 0.5) / math.tan(math.radians(75.0) * 0.5)
        projected = []
        xs=[]; ys=[]
        for right, up, depth in clipped:
            sx = w*0.5 + right/depth*focal
            sy2 = h*0.5 - up/depth*focal
            projected.extend((sx,sy2)); xs.append(sx); ys.append(sy2)
        margin = 120
        if max(xs) < -margin or min(xs) > w+margin or max(ys) < -margin or min(ys) > h+margin:
            return
        depth = sum(depths)/len(depths)
        fog = max(0.30, min(1.0, 1.08-depth/max(22.0,max_distance*1.08)))
        # Outlines are useful nearby but expensive/noisy on distant geometry.
        edge = outline if depth < 16.0 else ""
        faces.append((depth, projected, shade(fill, fog) if fill else fill, edge))

    def _add_box(self, faces, x, y, z, sx, sy, sz, color, w, h):
        v = [
            (x, y, z), (x+sx, y, z), (x+sx, y+sy, z), (x, y+sy, z),
            (x, y, z+sz), (x+sx, y, z+sz), (x+sx, y+sy, z+sz), (x, y+sy, z+sz),
        ]
        quads = [
            ([v[0],v[1],v[5],v[4]], .75), ([v[1],v[2],v[6],v[5]], .62),
            ([v[2],v[3],v[7],v[6]], .72), ([v[3],v[0],v[4],v[7]], .86),
            ([v[4],v[5],v[6],v[7]], 1.08),
        ]
        for q, f in quads:
            self._add_face(faces, q, shade(color, f), "#141820", w, h)

    def _render_entities(self, w: int, h: int):
        faces = []
        labels = []
        if self.world == "ENTERPRISE":
            for node in EQUIPMENT.values():
                if node.deck != self.shipboard.deck:
                    continue
                d = math.hypot(node.x-self.x, node.y-self.y)
                if d > 12:
                    continue
                rt = self.shipboard.equipment_runtime.get(node.key)
                color = "#744d97"
                if rt and rt.fault:
                    color = "#a6454e"
                self._add_box(faces, node.x-.28, node.y-.28, .15, .56, .56, 1.1, color, w, h)
                labels.append((node.x, node.y, 1.55, node.name, color))
            for avatar in self.shipboard.crew_avatars.values():
                if avatar.deck != self.shipboard.deck or math.hypot(avatar.x-self.x, avatar.y-self.y) > 10:
                    continue
                self._add_box(faces, avatar.x-.18, avatar.y-.18, 0, .36, .36, 1.72, "#3f708e", w, h)
            # aircraft are low boxes, preserving v0.5/v0.6 package state.
            for ac in self.shipboard.aircraft.values():
                if ac.deck != self.shipboard.deck or math.hypot(ac.x-self.x, ac.y-self.y) > 14:
                    continue
                self._add_box(faces, ac.x-.55, ac.y-.32, .05, 1.1, .64, .35, "#596e62", w, h)
            if self._enterprise_shore_portal_nearby() or self.shipboard.deck == "ISLAND":
                labels.append((14.7, 16.0, 1.35, "SHORE / TRAINING CENTER", "#7acfa4"))
        else:
            for node in self._nodes().values():
                d = math.hypot(node.x-self.x, node.y-self.y)
                if d > 14:
                    continue
                col = "#6a47a8" if node.kind == "terminal" else "#3c7d6c"
                if self.world == "DAMAGE" and node.key != "EXIT":
                    col = "#7e4b45"
                if self.world == "SYSTEMS" and node.key != "EXIT":
                    col = "#735645"
                self._add_box(faces, node.x-.36, node.y-.3, .15, .72, .60, 1.2, col, w, h)
                labels.append((node.x, node.y, 1.62, node.name, col))

        faces.sort(key=lambda item: item[0], reverse=True)
        for _, pts, fill, outline in faces:
            self.canvas.create_polygon(*pts, fill=fill, outline=outline, width=1)
        for lx, ly, lz, text, col in labels:
            p = project_point(lx, ly, lz, self.x, self.y, self.z, self.yaw, self.pitch, w, h)
            if p and 0 < p[2] < 7.5:
                self.canvas.create_text(p[0], p[1]-14, text=text, fill="#edf1f7", font=("Segoe UI", max(8, int(13-p[2]*.6))), anchor="s")

        # Diegetic 3D objective beacon: the marker exists at the physical console's world position.
        if self.world == "ENTERPRISE":
            obj = active_objective(self.shipboard)
            if obj and obj.get("deck") == self.shipboard.deck:
                bob = 1.9 + math.sin(time.monotonic() * 4.0) * 0.12
                p = project_point(float(obj["x"]), float(obj["y"]), bob, self.x, self.y, self.z, self.yaw, self.pitch, w, h)
                if p and 0 < p[2] < 16:
                    size = max(5, min(16, int(70 / p[2])))
                    self.canvas.create_polygon(p[0], p[1]-size, p[0]+size, p[1], p[0], p[1]+size, p[0]-size, p[1], fill="#b68cff", outline="#f0e7ff", width=1)
                    self.canvas.create_text(p[0], p[1]-size-10, text="OBJECTIVE", fill="#d8c5ff", font=("Segoe UI Semibold", 8), anchor="s")

    def _render_hud(self, w: int, h: int):
        c = self.canvas
        # crosshair
        cx, cy = w//2, h//2
        c.create_line(cx-9, cy, cx+9, cy, fill="#e6e9ee", width=1)
        c.create_line(cx, cy-9, cx, cy+9, fill="#e6e9ee", width=1)

        world_name = {
            "HUB": "NAVAL TRAINING & CAREER CENTER",
            "ENTERPRISE": f"USS ENTERPRISE CV-6 • {DECK_NAMES[self.shipboard.deck]}",
            "BRIDGE": "BRIDGE PRACTICAL SIMULATOR",
            "DAMAGE": "DAMAGE CONTROL TRAINER",
            "SYSTEMS": "FULL SHIP SYSTEMS TRAINER",
        }[self.world]
        c.create_rectangle(14, 14, min(w-14, 640), 100, fill="#080c12", outline="#2e3948")
        c.create_text(28, 26, text=world_name, fill="#cdb5ff", font=("Segoe UI Semibold", 14), anchor="nw")
        c.create_text(28, 52, text=f"{self.profile.rank} {self.profile.name} • {self.profile.xp} XP • FPS {self.fps}", fill="#eef1f5", font=("Segoe UI", 10), anchor="nw")
        if self.world == "ENTERPRISE":
            c.create_text(28, 74, text=f"{self.shipboard.clock} • {ship_alarm_state(self.shipboard)} • {current_zone(self.shipboard)} • Clock {'RUN' if self.running_time else 'PAUSED'}", fill="#aab4c2", font=("Segoe UI", 9), anchor="nw")
        elif self.world == "BRIDGE":
            c.create_text(28, 74, text=f"HDG {self.bridge.heading:05.1f}° / ORDER {self.bridge.ordered_heading:03.0f}° • SPD {self.bridge.speed:04.1f} kt • RUD {self.bridge.rudder:+.0f}°", fill="#aab4c2", font=("Segoe UI", 9), anchor="nw")
        elif self.world == "DAMAGE":
            c.create_text(28, 74, text=f"FIRE {self.damage.fire:.0f}% • FLOOD {self.damage.flooding:.0f}% • SMOKE {self.damage.smoke:.0f}% • HULL {self.damage.hull:.0f}%", fill="#ffb0aa", font=("Segoe UI", 9), anchor="nw")
        elif self.world == "SYSTEMS":
            sm = ship_summary(self.ship_systems)
            c.create_text(28, 74, text=f"FIRE {sm.get('max_fire',0):.0f}% • FLOOD {sm.get('max_flooding',0):.0f}% • CASUALTIES {sm.get('casualties',0):.0f}", fill="#ffbf91", font=("Segoe UI", 9), anchor="nw")
        else:
            c.create_text(28, 74, text="Walk to a 3D station and press E. F1 briefing • F objective • Esc pause", fill="#aab4c2", font=("Segoe UI", 9), anchor="nw")

        prompt = self._interaction_prompt()
        if prompt:
            tw = min(740, w-80)
            c.create_rectangle((w-tw)//2, h-110, (w+tw)//2, h-62, fill="#0a1019", outline="#8e6ac8", width=2)
            c.create_text(w//2, h-86, text=prompt, fill="#f1edff", font=("Segoe UI Semibold", 11), anchor="center")

        if time.monotonic() < self.message_until and self.message:
            c.create_rectangle(20, h-54, w-20, h-18, fill="#0a0e14", outline="#26303d")
            c.create_text(30, h-36, text=self.message, fill="#dce2ea", font=("Segoe UI", 10), anchor="w")

        c.create_text(w-20, 20, text=f"WAR SIMULATOR v{VERSION}\nFULL-GAME FIRST PERSON 3D", fill="#8e79b5", font=("Segoe UI Semibold", 9), anchor="ne", justify="right")

    def _interaction_prompt(self) -> str:
        if self.world == "ENTERPRISE":
            if self._enterprise_shore_portal_nearby():
                return "[E] Return to Naval Training & Career Center"
            eq = nearby_equipment(self.shipboard)
            hatch = nearby_hatch(self.shipboard)
            if hatch:
                status = "OPEN" if self.shipboard.hatches.get(hatch.key, True) else "SHUT"
                return f"[E] {hatch.name} • {status}"
            if eq:
                return f"[E] Operate {eq.name}"
            return ""
        node = self._nearest_node()
        return f"[E] {node.name}" if node else ""

    def _objective_text(self) -> str:
        if self.world == "ENTERPRISE":
            return objective_navigation(self.shipboard)
        if self.world == "BRIDGE":
            err = abs(((self.bridge.ordered_heading-self.bridge.heading+180)%360)-180)
            return f"Steady on {self.bridge.ordered_heading:.0f}°. Current course error {err:.1f}°."
        if self.world == "DAMAGE":
            return "Contain fire and flooding, manage smoke/power/crew health, then report to Evaluator."
        if self.world == "SYSTEMS":
            return "Dispatch firefighting to Engine Room 2, dewater Machinery, restore safe electrical service, then evaluate."
        return "Use the Academy, practical trainers, Enterprise duty, historical archive, and promotion board to build your career."

    def _render_overlay(self, w: int, h: int):
        c = self.canvas
        x1, y1, x2, y2 = int(w*.14), int(h*.12), int(w*.86), int(h*.86)
        c.create_rectangle(x1, y1, x2, y2, fill="#090e16", outline="#7d62a8", width=2)
        c.create_rectangle(x1+4, y1+4, x2-4, y1+56, fill="#141a25", outline="")
        title = {
            "welcome":"WAR SIMULATOR — FULL-GAME 3D CONVERSION",
            "career":"CAREER & SERVICE RECORD",
            "new_career":"NEW CAREER ENLISTMENT",
            "academy":"ACADEMY — HELMSMAN WRITTEN EXAMINATION",
            "exam_result":"EXAMINATION RESULT",
            "crew":"CREW & WATCH ROSTER",
            "timeline":"HISTORICAL TIMELINE ARCHIVE",
            "qualifications":"QUALIFICATIONS RECORD",
            "promotion":"PROMOTION BOARD",
            "help":"OPERATIONS BRIEFING",
            "pause":"PAUSED",
        }.get(self.overlay, self.overlay.upper())
        c.create_text(x1+24, y1+30, text=title, fill="#d4c0ff", font=("Segoe UI Semibold", 17), anchor="w")
        c.create_text(x2-20, y1+30, text="E / ESC TO CLOSE", fill="#8f99a7", font=("Segoe UI", 9), anchor="e")
        lines = self._overlay_lines()
        yy = y1+80
        for line, style in lines:
            color = {"head":"#ffffff", "accent":"#c4a2ff", "muted":"#98a3b5", "good":"#75d6a0", "warn":"#efc56b", "danger":"#ff7a87"}.get(style, "#dce2ea")
            font = ("Segoe UI Semibold", 12) if style in ("head","accent") else ("Segoe UI", 10)
            c.create_text(x1+28, yy, text=line, fill=color, font=font, anchor="nw", width=x2-x1-56)
            yy += 30 if style in ("head","accent") else 24
            if yy > y2-30:
                break

    def _overlay_lines(self):
        o = self.overlay
        p = self.profile
        if o == "welcome":
            return [
                ("v0.7 changes the normal game flow to first-person 3D.", "accent"),
                ("You now begin inside the Naval Training & Career Center instead of a 2D menu.", "head"),
                ("W / S — move forward/backward    A / D — strafe", "normal"),
                ("Arrow Left/Right or hold left mouse button and drag — look", "normal"),
                ("E — interact with physical terminals, consoles, hatches and equipment", "normal"),
                ("F — current objective    R — run/pause Midway time aboard Enterprise", "normal"),
                ("F9 — emergency return to Training Center    Esc — pause", "normal"),
                ("Enterprise geometry remains clearly labeled a training schematic; historical events remain sourced/locked.", "warn"),
                ("Press E, Esc, Space, or Enter to begin.", "good"),
            ]
        if o == "career":
            return [
                (f"{p.rank} {p.name} • {p.branch} • {p.era}", "accent"),
                (f"Experience: {p.xp} XP    Duty periods: {p.duty_periods}    Reputation: {p.reputation:.0f}%", "normal"),
                (f"Written: {p.written_exam:.0f}%    Practical: {p.practical_exam:.0f}%    Mission: {p.mission_performance:.0f}%", "normal"),
                (f"Leadership: {p.leadership_eval:.0f}%    Discipline: {p.discipline:.0f}%    Professionalism: {p.professionalism:.0f}%", "normal"),
                (f"Enterprise best: {p.shipboard_walk_best:.0f}%    Historical best: {p.historical_best:.0f}%", "normal"),
                ("N — Create a new career profile", "good"),
                ("Recent service log:", "head"),
            ] + [(f"• {x}", "muted") for x in (p.service_log[:10] or ["No completed duty events yet."])]
        if o == "new_career":
            eras = list(ERAS)
            return [
                ("Type the servicemember name directly on this terminal.", "accent"),
                (f"NAME: {self.new_name or '_'}", "head"),
                (f"BRANCH: {BRANCHES[self.new_branch_index]}    [TAB cycles branch]", "normal"),
                (f"ERA: {eras[self.new_era_index]}    [F2 cycles era]", "normal"),
                ("ENTER — create and save career    ESC — cancel", "good"),
                ("A new career begins at Recruit and must earn advancement through the qualification/progression systems.", "warn"),
            ]
        if o == "academy":
            q = WRITTEN_QUESTIONS[min(self.exam_index, len(WRITTEN_QUESTIONS)-1)]
            return [
                (f"Question {self.exam_index+1} / {len(WRITTEN_QUESTIONS)}", "accent"),
                (q["q"], "head"),
            ] + [(f"{i+1}. {choice}", "normal") for i, choice in enumerate(q["choices"])] + [("Press 1, 2, 3, or 4 to answer.", "good")]
        if o == "exam_result":
            score = self.exam_correct / len(WRITTEN_QUESTIONS) * 100.0
            return [(f"Final score: {score:.0f}%", "good" if score >= 70 else "warn"), ("Career progress was saved. Return to the 3D world and continue practical training.", "normal")]
        if o == "crew":
            crew = generate_crew(p, 10)
            lines = [("Persistent career crew simulation sample", "accent")]
            for m in crew:
                lines.append((f"{m.rank:18} {m.name:18}  Training {m.training:4.0f}%  Morale {m.morale:4.0f}%  Fatigue {m.fatigue:4.0f}%  Stress {m.stress:4.0f}%", "normal"))
            return lines
        if o == "timeline":
            lines = [("Historical eras available in the master design", "accent")]
            for era, items in ERAS.items():
                lines.append((era, "head"))
                lines.append((" • ".join(items[:8]) + (" …" if len(items)>8 else ""), "muted"))
            return lines
        if o == "qualifications":
            lines = [(f"Qualifications earned: {sum(1 for v in p.qualifications.values() if v)}", "accent")]
            for k in sorted(k for k,v in p.qualifications.items() if v):
                lines.append((f"✓ {k}", "good"))
            for station, done in sorted(p.station_qualifications.items()):
                if done:
                    lines.append((f"✓ Enterprise station practical — {station}", "good"))
            if len(lines) == 1:
                lines.append(("No qualifications earned yet. Visit Academy and practical simulators.", "warn"))
            return lines
        if o == "promotion":
            lines = [(f"Current rank: {p.rank}    Next: {p.next_rank}", "accent")]
            for name, d in promotion_status(p).items():
                style = "good" if d["met"] else "warn"
                lines.append((f"{'✓' if d['met'] else '○'} {name}: {d['value']:.0f} / {d['required']}", style))
            lines.append(("Press P to convene the promotion board.", "head"))
            return lines
        if o == "help":
            return [
                ("First-person 3D controls", "accent"),
                ("WASD move • Shift sprint • arrows/mouse-drag look • E interact • F objective • R historical clock", "normal"),
                ("F11 fullscreen • F9 emergency return to hub • Esc pause", "normal"),
                ("Career path", "head"),
                ("Academy → practical training → ship systems → Enterprise watch → historical operations → promotion.", "normal"),
                ("The 3D training facility is fictional interface geometry. Enterprise internal geometry remains a training schematic, not an exact 1942 deck plan.", "warn"),
            ]
        if o == "pause":
            return [
                ("S — Save career", "head"),
                ("H — Return to 3D Training Center", "head"),
                ("Q — Save and quit", "head"),
                ("Esc / E — Resume", "good"),
            ]
        return [("No terminal data.", "muted")]

    def _set_message(self, message: str, seconds: float = 3.0):
        self.message = message
        self.message_until = time.monotonic() + seconds

    def on_close(self):
        if self.destroyed:
            return
        self.destroyed = True
        try:
            # Persist a completed Enterprise walk evaluation if the user has meaningfully interacted.
            if self.shipboard.interactions >= 5 and not self.shipboard.evaluated:
                score = evaluate_shipboard(self.shipboard)
                summary = shipboard_summary(self.shipboard)
                qualified = list(self.shipboard.qualified_this_run)
                apply_shipboard_walk_result(self.profile, score, summary, qualified)
                self.shipboard.evaluated = True
            save_profile(self.profile)
        finally:
            self.destroy()


def run():
    FirstPerson3DApp().mainloop()


if __name__ == "__main__":
    run()
