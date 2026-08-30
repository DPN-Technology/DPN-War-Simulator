from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
import math


DEPARTMENT_KEYS = (
    "BRIDGE", "CIC", "RADIO", "ENGINEERING", "DAMAGE_CONTROL",
    "FIRE_CONTROL", "AIR_OPS", "MEDICAL", "SUPPLY",
)

DEPARTMENT_NAMES = {
    "BRIDGE": "Navigation / Bridge",
    "CIC": "Combat Information Center",
    "RADIO": "Communications",
    "ENGINEERING": "Engineering",
    "DAMAGE_CONTROL": "Damage Control",
    "FIRE_CONTROL": "Fire Control / Air Defense",
    "AIR_OPS": "Aviation Operations",
    "MEDICAL": "Medical",
    "SUPPLY": "Supply / Logistics",
}

DEPARTMENT_OFFICERS = {
    "BRIDGE": ("LCDR Edward Mercer", "Officer of the Deck"),
    "CIC": ("LT Raymond Walsh", "CIC Watch Officer"),
    "RADIO": ("LTJG Paul Warren", "Communications Officer"),
    "ENGINEERING": ("LCDR Henry Sutton", "Chief Engineer"),
    "DAMAGE_CONTROL": ("LT Charles Mercer", "Damage Control Assistant"),
    "FIRE_CONTROL": ("LT Robert Quinn", "Gunnery Officer"),
    "AIR_OPS": ("LCDR George Halley", "Air Officer"),
    "MEDICAL": ("LCDR James Carter", "Senior Medical Officer"),
    "SUPPLY": ("LT William Brooks", "Supply Officer"),
}

# Authority tiers are gameplay abstractions of progressive responsibility. They are not a claim
# that every historical Navy billet followed these exact thresholds.
AUTHORITY_LABELS = {
    0: "INDIVIDUAL DUTY",
    1: "WORK-CENTER LEAD",
    2: "DIVISION / TEAM LEAD",
    3: "DEPARTMENT WATCH",
    4: "SHIP COMMAND WATCH",
    5: "COMMANDING OFFICER",
}


@dataclass
class DepartmentState:
    key: str
    name: str
    officer: str
    billet: str
    manpower: int
    available: int
    readiness: float = 82.0
    fatigue: float = 14.0
    morale: float = 82.0
    casualties: int = 0
    current_order: str = "ROUTINE WATCH"
    order_progress: float = 0.0
    status: str = "ROUTINE"
    response_count: int = 0


@dataclass
class CommandOrder:
    key: str
    title: str
    department: str
    minimum_authority: int
    priority: str
    issued_minute: int
    deadline_minute: int
    detail: str = ""
    progress: float = 0.0
    completed: bool = False
    failed: bool = False
    auto_generated: bool = False
    source: str = "PLAYER"

    @property
    def status(self) -> str:
        if self.completed:
            return "COMPLETE"
        if self.failed:
            return "FAILED"
        return "ACTIVE"


@dataclass
class SupplyState:
    provisions_units: float = 1000.0
    fresh_water_units: float = 1000.0
    repair_material_units: float = 420.0
    medical_units: float = 260.0
    electrical_spares: float = 120.0
    fire_fighting_agent: float = 300.0
    replacement_personnel: int = 18


@dataclass
class CommandState:
    departments: Dict[str, DepartmentState] = field(default_factory=dict)
    orders: Dict[str, CommandOrder] = field(default_factory=dict)
    supplies: SupplyState = field(default_factory=SupplyState)
    watch_section: str = "PORT"
    watch_number: int = 1
    command_condition: str = "CONDITION III"
    captain_on_bridge: bool = False
    general_quarters: bool = False
    muster_required: bool = False
    last_muster_pct: float = 100.0
    crew_total: int = 2160
    crew_available: int = 2142
    crew_wounded: int = 0
    crew_dead: int = 0
    crew_unaccounted: int = 0
    replacement_assigned: int = 0
    orders_issued: int = 0
    orders_completed: int = 0
    orders_failed: int = 0
    autonomous_actions: int = 0
    watch_reliefs: int = 0
    command_score: float = 100.0
    selected_department_index: int = 0
    log: List[str] = field(default_factory=list)
    _last_minute: int = -1
    _order_serial: int = 0
    _medical_accum: float = 0.0
    _dc_accum: float = 0.0
    _eng_accum: float = 0.0

    @property
    def selected_department(self) -> DepartmentState:
        keys = list(self.departments)
        return self.departments[keys[self.selected_department_index % len(keys)]]


def authority_level(rank_index: int) -> int:
    if rank_index <= 3:       # Recruit through Seaman
        return 0
    if rank_index <= 5:       # Petty Officer / Chief
        return 1
    if rank_index <= 8:       # Senior Chief through Warrant Officer
        return 2
    if rank_index <= 11:      # Ensign through Lieutenant
        return 3
    if rank_index <= 13:      # LCDR / Commander
        return 4
    return 5                  # Captain and above


def authority_label(rank_index: int) -> str:
    return AUTHORITY_LABELS[authority_level(rank_index)]


def create_command_state() -> CommandState:
    manpower = {
        "BRIDGE": 28, "CIC": 46, "RADIO": 34, "ENGINEERING": 486,
        "DAMAGE_CONTROL": 330, "FIRE_CONTROL": 330, "AIR_OPS": 620,
        "MEDICAL": 54, "SUPPLY": 232,
    }
    s = CommandState()
    for key in DEPARTMENT_KEYS:
        officer, billet = DEPARTMENT_OFFICERS[key]
        n = manpower[key]
        s.departments[key] = DepartmentState(
            key=key, name=DEPARTMENT_NAMES[key], officer=officer, billet=billet,
            manpower=n, available=n, readiness=82.0, fatigue=12.0, morale=84.0,
        )
    s.log.append("05:20 — Command organization established; Condition III routine watch set.")
    return s


def cycle_department(s: CommandState) -> DepartmentState:
    s.selected_department_index = (s.selected_department_index + 1) % len(s.departments)
    return s.selected_department


def _new_order(s: CommandState, title: str, department: str, min_auth: int,
               priority: str, minute: int, window: int, detail: str,
               source: str = "PLAYER", auto: bool = False) -> CommandOrder:
    s._order_serial += 1
    key = f"ORD-{s._order_serial:04d}"
    order = CommandOrder(key, title, department, min_auth, priority, minute,
                         minute + window, detail, source=source, auto_generated=auto)
    s.orders[key] = order
    s.orders_issued += 1
    dept = s.departments.get(department)
    if dept:
        dept.current_order = title
        dept.order_progress = 0.0
        dept.status = "RESPONDING"
    s.log.insert(0, f"{minute//60:02d}:{minute%60:02d} — {source} ORDER {key}: {title} → {DEPARTMENT_NAMES.get(department, department)}.")
    s.log = s.log[:160]
    return order


def active_order(s: CommandState, department: str) -> Optional[CommandOrder]:
    candidates = [o for o in s.orders.values() if o.department == department and not o.completed and not o.failed]
    if not candidates:
        return None
    pri = {"EMERGENCY": 4, "URGENT": 3, "HIGH": 2, "ROUTINE": 1}
    return max(candidates, key=lambda o: (pri.get(o.priority, 0), -o.issued_minute))


def issue_order(s: CommandState, rank_index: int, order_code: str, minute: int,
                department: Optional[str] = None) -> Tuple[bool, str]:
    code = order_code.upper()
    dept = department or s.selected_department.key
    catalog = {
        "REPORT": ("Submit condition report through chain of command", dept, 0, "ROUTINE", 12,
                   "Report observed condition to the department watch supervisor for action or escalation."),
        "MUSTER": ("Conduct accountability muster", "SUPPLY", 1, "HIGH", 20,
                   "Account for assigned personnel and report missing, wounded, or unavailable crew."),
        "REPAIR": ("Prioritize casualty restoration", dept, 1, "URGENT", 30,
                   "Assign qualified personnel to the highest-priority active casualty in the department."),
        "WATERTIGHT": ("Set enhanced watertight integrity", "DAMAGE_CONTROL", 2, "URGENT", 15,
                   "Secure designated watertight boundaries and verify closure reports."),
        "MEDICAL": ("Establish casualty receiving posture", "MEDICAL", 1, "URGENT", 15,
                   "Prepare triage, treatment, and casualty evacuation teams."),
        "ENGINEERING": ("Restore propulsion and electrical readiness", "ENGINEERING", 2, "URGENT", 25,
                   "Prioritize machinery, electrical distribution, and steering support casualties."),
        "AIRDEF": ("Set air-defense readiness", "FIRE_CONTROL", 2, "URGENT", 10,
                   "Man air-defense stations and maintain weapon/radar readiness."),
        "AIR": ("Set aviation operations readiness", "AIR_OPS", 2, "HIGH", 20,
                   "Prepare flight deck, aircraft handling, fueling, arming, launch and recovery teams."),
        "GQ": ("Set General Quarters", "BRIDGE", 3, "EMERGENCY", 10,
                   "Man battle stations ship-wide and secure the ship for combat."),
        "STANDDOWN": ("Stand down from General Quarters", "BRIDGE", 3, "HIGH", 15,
                   "Return to directed readiness after the tactical/casualty situation permits."),
        "SUPPLY": ("Replenish repair and medical stores", "SUPPLY", 2, "HIGH", 45,
                   "Issue repair material, electrical spares, firefighting agent, and medical consumables."),
    }
    if code not in catalog:
        return False, f"Unknown command order: {order_code}."
    title, target, min_auth, pri, window, detail = catalog[code]
    if authority_level(rank_index) < min_auth:
        return False, f"ORDER DENIED — {title} requires {AUTHORITY_LABELS[min_auth]} authority."
    if code == "GQ":
        s.general_quarters = True
        s.command_condition = "GENERAL QUARTERS"
        s.captain_on_bridge = True
        # Shipwide order plus department child orders.
        _new_order(s, title, target, min_auth, pri, minute, window, detail)
        for d in ("CIC", "RADIO", "ENGINEERING", "DAMAGE_CONTROL", "FIRE_CONTROL", "AIR_OPS", "MEDICAL"):
            _new_order(s, "Man battle stations", d, 0, "EMERGENCY", minute, 12,
                       "Report battle-station manning and readiness.", source="CHAIN OF COMMAND", auto=True)
        return True, "GENERAL QUARTERS ordered. Department heads are manning battle stations."
    if code == "STANDDOWN":
        if any(not o.completed and not o.failed and o.priority == "EMERGENCY" for o in s.orders.values() if o.department != "BRIDGE"):
            return False, "Stand-down denied: emergency department orders remain unresolved."
        s.general_quarters = False
        s.command_condition = "CONDITION III"
        s.captain_on_bridge = False
    if code == "MUSTER":
        s.muster_required = True
    _new_order(s, title, target, min_auth, pri, minute, window, detail)
    return True, f"Order issued: {title} → {DEPARTMENT_NAMES[target]}."


def auto_generate_orders(s: CommandState, minute: int, combat, survivability, physics) -> List[str]:
    msgs: List[str] = []
    active_titles = {o.title for o in s.orders.values() if not o.completed and not o.failed}
    if getattr(combat, "raid_active", False) and not s.general_quarters:
        s.general_quarters = True
        s.command_condition = "GENERAL QUARTERS"
        s.captain_on_bridge = True
        _new_order(s, "Set General Quarters", "BRIDGE", 0, "EMERGENCY", minute, 8,
                   "Automatic combat alarm: man battle stations.", source="ALARM SYSTEM", auto=True)
        for d in ("CIC", "RADIO", "ENGINEERING", "DAMAGE_CONTROL", "FIRE_CONTROL", "AIR_OPS", "MEDICAL"):
            if not active_order(s, d):
                _new_order(s, "Man battle stations", d, 0, "EMERGENCY", minute, 10,
                           "Automatic combat alarm response.", source="ALARM SYSTEM", auto=True)
        msgs.append("GENERAL QUARTERS alarm sounded automatically for active air attack.")
    fires = sum(c.fire for c in survivability.compartments.values())
    flooding = sum(c.flooding for c in survivability.compartments.values())
    wounded = sum(c.wounded for c in survivability.compartments.values())
    severe_struct = min(c.structural for c in survivability.compartments.values())
    if (fires > 30 or flooding > 35 or severe_struct < 65) and not active_order(s, "DAMAGE_CONTROL"):
        _new_order(s, "Respond to structural casualty", "DAMAGE_CONTROL", 0, "EMERGENCY", minute, 20,
                   "Fight fire, control flooding, isolate boundaries, patch breaches, and shore weakened structure.", source="CASUALTY ALARM", auto=True)
        msgs.append("Damage Control Central dispatched repair parties to the active casualty.")
    if wounded > 0 and not active_order(s, "MEDICAL"):
        _new_order(s, "Receive and treat casualties", "MEDICAL", 0, "URGENT", minute, 25,
                   "Triage wounded, treat casualties, and maintain evacuation readiness.", source="CASUALTY ALARM", auto=True)
        msgs.append("Medical department activated casualty receiving teams.")
    if (getattr(physics, "propulsion_integrity", 100) < 85 or getattr(physics, "steering_integrity", 100) < 85) and not active_order(s, "ENGINEERING"):
        _new_order(s, "Restore maneuvering capability", "ENGINEERING", 0, "URGENT", minute, 30,
                   "Restore propulsion, steering support, and electrical distribution.", source="ENGINEERING ALARM", auto=True)
        msgs.append("Engineering watch organized restoration teams.")
    return msgs


def _complete(s: CommandState, order: CommandOrder, minute: int) -> None:
    if order.completed or order.failed:
        return
    order.completed = True
    order.progress = 100.0
    s.orders_completed += 1
    d = s.departments.get(order.department)
    if d:
        d.response_count += 1
        d.current_order = "ROUTINE WATCH"
        d.order_progress = 0.0
        d.status = "BATTLE READY" if s.general_quarters else "ROUTINE"
        d.readiness = min(100.0, d.readiness + 2.5)
    s.log.insert(0, f"{minute//60:02d}:{minute%60:02d} — ORDER COMPLETE {order.key}: {order.title}.")


def _worst_compartment(survivability):
    return max(survivability.compartments.values(), key=lambda c: c.fire + c.flooding + (100-c.structural)*0.65 + c.wounded*4)


def advance_command(s: CommandState, minutes: int, combat, survivability, physics, living_world=None) -> List[str]:
    """Advance autonomous department response in simulated minutes.

    Departments reduce casualties gradually; they do not instantly solve emergencies and are limited by
    readiness, fatigue, manpower and consumable stores.
    """
    msgs: List[str] = []
    for _ in range(max(1, int(minutes))):
        minute = (s._last_minute + 1) if s._last_minute >= 0 else getattr(living_world, "minute_of_day", 320)
        s._last_minute = minute % 1440
        msgs.extend(auto_generate_orders(s, s._last_minute, combat, survivability, physics))

        # Casualty accounting from the structural model.
        wounded = sum(c.wounded for c in survivability.compartments.values())
        dead = sum(c.dead for c in survivability.compartments.values())
        s.crew_wounded = wounded
        s.crew_dead = dead
        casualty_vacancies = max(0, dead - s.replacement_assigned)
        s.crew_available = max(0, s.crew_total - wounded - casualty_vacancies - s.crew_unaccounted)
        availability_ratio = s.crew_available / max(1, s.crew_total)

        for d in s.departments.values():
            d.available = max(0, min(d.manpower, round(d.manpower * availability_ratio)))
            d.fatigue = min(100.0, d.fatigue + (0.08 if s.general_quarters else -0.035))
            d.morale = max(20.0, min(100.0, d.morale - (0.015 if wounded + dead else -0.01)))
            d.readiness = max(5.0, min(100.0, d.readiness - max(0.0, d.fatigue - 70) * 0.003))

        # Slow ship-wide logistics consumption.
        s.supplies.provisions_units = max(0.0, s.supplies.provisions_units - s.crew_total * 0.00018)
        s.supplies.fresh_water_units = max(0.0, s.supplies.fresh_water_units - s.crew_total * 0.00024)

        for order in list(s.orders.values()):
            if order.completed or order.failed:
                continue
            d = s.departments[order.department]
            if s._last_minute > order.deadline_minute and order.deadline_minute < 1440:
                order.failed = True
                s.orders_failed += 1
                s.command_score = max(0.0, s.command_score - (8 if order.priority == "EMERGENCY" else 4))
                d.status = "ORDER MISSED"
                s.log.insert(0, f"{s._last_minute//60:02d}:{s._last_minute%60:02d} — ORDER MISSED {order.key}: {order.title}.")
                continue
            efficiency = (d.readiness * 0.45 + d.morale * 0.25 + (100-d.fatigue) * 0.20 + availability_ratio*100*0.10) / 100
            rate = {"EMERGENCY": 11.0, "URGENT": 8.0, "HIGH": 6.0, "ROUTINE": 4.0}.get(order.priority, 5.0)
            order.progress = min(100.0, order.progress + rate * max(0.20, efficiency))
            d.order_progress = order.progress

            # Department-specific real consequences.
            if order.department == "DAMAGE_CONTROL":
                c = _worst_compartment(survivability)
                if s.supplies.fire_fighting_agent > 0 and c.fire > 0:
                    reduction = min(c.fire, 2.0 * efficiency)
                    c.fire -= reduction
                    c.smoke = max(0.0, c.smoke - 0.8 * efficiency)
                    s.supplies.fire_fighting_agent = max(0.0, s.supplies.fire_fighting_agent - 0.35)
                if s.supplies.repair_material_units > 0 and c.flooding > 0:
                    c.flooding = max(0.0, c.flooding - 0.9 * efficiency)
                    if c.breach_area_m2 > 0:
                        c.breach_area_m2 = max(0.0, c.breach_area_m2 - 0.015 * efficiency)
                    s.supplies.repair_material_units = max(0.0, s.supplies.repair_material_units - 0.25)
                if s.supplies.repair_material_units > 0 and c.structural < 100:
                    c.structural = min(100.0, c.structural + 0.25 * efficiency)
            elif order.department == "MEDICAL" and wounded > 0 and s.supplies.medical_units > 0:
                cands = [c for c in survivability.compartments.values() if c.wounded > 0]
                if cands:
                    c = max(cands, key=lambda q: q.wounded)
                    if order.progress >= 35 and (int(order.progress) % 12) < 7:
                        c.wounded -= 1
                        survivability.casualties_treated += 1
                        s.supplies.medical_units = max(0.0, s.supplies.medical_units - 1.0)
            elif order.department == "ENGINEERING":
                if s.supplies.electrical_spares > 0:
                    physics.propulsion_integrity = min(100.0, physics.propulsion_integrity + 0.32 * efficiency)
                    physics.steering_integrity = min(100.0, physics.steering_integrity + 0.20 * efficiency)
                    s.supplies.electrical_spares = max(0.0, s.supplies.electrical_spares - 0.08)
            elif order.department == "SUPPLY" and order.title.startswith("Replenish"):
                # Pull limited material from deep reserve / storerooms.
                if order.progress >= 90:
                    s.supplies.repair_material_units = min(500.0, s.supplies.repair_material_units + 50)
                    s.supplies.medical_units = min(300.0, s.supplies.medical_units + 25)
                    s.supplies.electrical_spares = min(150.0, s.supplies.electrical_spares + 15)
                    s.supplies.fire_fighting_agent = min(350.0, s.supplies.fire_fighting_agent + 30)
                    if getattr(physics, "moored", False) and s.supplies.replacement_personnel > 0:
                        vacancies = max(0, s.crew_dead - s.replacement_assigned)
                        moved = min(vacancies, s.supplies.replacement_personnel)
                        s.replacement_assigned += moved
                        s.supplies.replacement_personnel -= moved

            if order.progress >= 100.0:
                _complete(s, order, s._last_minute)
                s.autonomous_actions += 1

        if s.muster_required:
            accounted = max(0, s.crew_total - s.crew_unaccounted)
            s.last_muster_pct = accounted / max(1, s.crew_total) * 100
            if any(o.title == "Conduct accountability muster" and o.completed for o in s.orders.values()):
                s.muster_required = False

        # Watch relief every four hours. GQ delays nonessential relief but fatigue still grows.
        if s._last_minute % 240 == 0 and not s.general_quarters:
            sections = ["PORT", "STARBOARD", "DOG WATCH"]
            s.watch_section = sections[(sections.index(s.watch_section) + 1) % len(sections)] if s.watch_section in sections else "PORT"
            s.watch_number += 1
            s.watch_reliefs += 1
            for d in s.departments.values():
                d.fatigue = max(5.0, d.fatigue - 18.0)
                d.status = "WATCH RELIEVED"
            s.log.insert(0, f"{s._last_minute//60:02d}:{s._last_minute%60:02d} — {s.watch_section} section assumed the watch.")

    s.log = s.log[:160]
    return msgs


def command_summary(s: CommandState, rank_index: int) -> str:
    active = sum(1 for o in s.orders.values() if not o.completed and not o.failed)
    return (f"{s.command_condition} • {s.watch_section} watch • Authority {authority_label(rank_index)} • "
            f"Orders {active} active / {s.orders_completed} complete / {s.orders_failed} failed • "
            f"Crew {s.crew_available}/{s.crew_total} available • Command score {s.command_score:.0f}%")


def department_lines(s: CommandState) -> List[str]:
    out = []
    for d in s.departments.values():
        out.append(f"{d.key:14} {d.status:14} ready {d.readiness:3.0f}% fatigue {d.fatigue:3.0f}% "
                   f"man {d.available:3d}/{d.manpower:3d} • {d.current_order} {d.order_progress:3.0f}%")
    return out


def order_lines(s: CommandState, limit: int = 12) -> List[str]:
    pri = {"EMERGENCY": 4, "URGENT": 3, "HIGH": 2, "ROUTINE": 1}
    orders = sorted(s.orders.values(), key=lambda o: (o.completed or o.failed, -pri.get(o.priority,0), -o.issued_minute))
    return [f"{o.status:8} {o.priority:9} {o.key} {o.department:14} {o.progress:3.0f}% • {o.title}" for o in orders[:limit]]


def supply_lines(s: CommandState) -> List[str]:
    q = s.supplies
    return [
        f"Provisions {q.provisions_units:.0f} • Fresh water {q.fresh_water_units:.0f}",
        f"Repair material {q.repair_material_units:.0f} • Electrical spares {q.electrical_spares:.0f}",
        f"Medical stores {q.medical_units:.0f} • Firefighting agent {q.fire_fighting_agent:.0f}",
        f"Replacement personnel reserve {q.replacement_personnel}",
    ]


def command_to_dict(s: CommandState) -> dict:
    d = asdict(s)
    # Internal tick accumulators are stateful but safe to preserve; dataclass conversion handles them.
    return d


def command_from_dict(data: Optional[dict]) -> CommandState:
    if not data:
        return create_command_state()
    s = create_command_state()
    scalar_fields = [
        "watch_section","watch_number","command_condition","captain_on_bridge","general_quarters",
        "muster_required","last_muster_pct","crew_total","crew_available","crew_wounded","crew_dead",
        "crew_unaccounted","replacement_assigned","orders_issued","orders_completed","orders_failed","autonomous_actions",
        "watch_reliefs","command_score","selected_department_index","log","_last_minute","_order_serial",
        "_medical_accum","_dc_accum","_eng_accum",
    ]
    for k in scalar_fields:
        if k in data:
            setattr(s, k, data[k])
    sup = data.get("supplies", {})
    for k in SupplyState.__dataclass_fields__:
        if k in sup:
            setattr(s.supplies, k, sup[k])
    for key, raw in data.get("departments", {}).items():
        if key in s.departments:
            for k in DepartmentState.__dataclass_fields__:
                if k in raw:
                    setattr(s.departments[key], k, raw[k])
    s.orders = {}
    for key, raw in data.get("orders", {}).items():
        try:
            s.orders[key] = CommandOrder(**{k: raw[k] for k in CommandOrder.__dataclass_fields__ if k in raw})
        except TypeError:
            continue
    return s


def route_living_crew(s: CommandState, living_world) -> None:
    """Route visible living-world crew to battle/department stations when command orders change."""
    # Ship-global positions match the training-schematic open-world layer.
    from .openworld import SHIP_ORIGIN_X, SHIP_ORIGIN_Y, LAYERS
    anchors = {
        "BRIDGE": (56, 12, "BRIDGE"), "CIC": (61, 9, "ISLAND"), "RADIO": (51, 9, "ISLAND"),
        "ENGINEERING": (24, 10, "ENGINEERING"), "DAMAGE_CONTROL": (60, 18, "ENGINEERING"),
        "FIRE_CONTROL": (61, 18, "ISLAND"), "AIR_OPS": (35, 13, "FLIGHT"),
        "MEDICAL": (43, 8, "LOWER"), "SUPPLY": (54, 8, "LOWER"),
        "ORDNANCE": (60, 12, "HANGAR"), "GALLEY": (31, 8, "LOWER"),
    }
    for c in living_world.crew.values():
        dept = c.home_department
        mapped = "SUPPLY" if dept == "GALLEY" else ("AIR_OPS" if dept == "ORDNANCE" else dept)
        order = active_order(s, mapped) if mapped in s.departments else None
        if s.general_quarters or order:
            lx, ly, floor = anchors.get(dept, anchors.get(mapped, (36,13,"HANGAR")))
            c.target_x = SHIP_ORIGIN_X + lx
            c.target_y = SHIP_ORIGIN_Y + ly
            c.target_z = LAYERS[floor].floor_z
            c.duty = "BATTLE STATION" if s.general_quarters else "ORDERED DUTY"
