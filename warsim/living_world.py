from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import random

from .openworld import LAYERS, CONNECTORS, SHIP_ORIGIN_X, SHIP_ORIGIN_Y


@dataclass
class PlayerNeeds:
    hunger: float = 12.0
    fatigue: float = 10.0
    stress: float = 8.0
    hydration: float = 8.0
    wellness: float = 100.0


@dataclass
class WorkOrder:
    key: str
    title: str
    department: str
    location: str
    due_minute: int
    priority: str = "ROUTINE"
    progress: float = 0.0
    completed: bool = False
    generated_minute: int = 0
    detail: str = ""


@dataclass
class LivingCrew:
    key: str
    name: str
    rating: str
    home_department: str
    x: float
    y: float
    floor_z: float
    target_x: float
    target_y: float
    target_z: float
    duty: str = "WATCH"
    fatigue: float = 10.0
    hunger: float = 10.0
    stress: float = 5.0
    speed: float = 1.15


@dataclass
class LivingWorldState:
    minute_of_day: int = 320  # 05:20
    day: int = 1
    needs: PlayerNeeds = field(default_factory=PlayerNeeds)
    work_orders: Dict[str, WorkOrder] = field(default_factory=dict)
    crew: Dict[str, LivingCrew] = field(default_factory=dict)
    event_log: List[str] = field(default_factory=list)
    maintenance_completed: int = 0
    meals_eaten: int = 0
    sleep_periods: int = 0
    medical_visits: int = 0
    routine_score: float = 100.0
    _last_schedule_hour: int = -1
    _generated_daily: bool = False

    @property
    def clock(self) -> str:
        m = self.minute_of_day % 1440
        return f"{m//60:02d}:{m%60:02d}"


def _pos(lx: float, ly: float, floor: str) -> Tuple[float,float,float]:
    return SHIP_ORIGIN_X+lx, SHIP_ORIGIN_Y+ly, LAYERS[floor].floor_z


def create_living_world(seed: int = 1942) -> LivingWorldState:
    s = LivingWorldState()
    rng = random.Random(seed)
    templates = [
        ("QM", "QM1 Samuel Ortiz", "Quartermaster", "BRIDGE", 56,12,"BRIDGE"),
        ("RAD", "RM1 Charles Avery", "Radioman", "RADIO", 51,9,"ISLAND"),
        ("CIC", "RdM1 Walter Hayes", "Radar Operator", "CIC", 61,9,"ISLAND"),
        ("ENG", "CWT Michael Doyle", "Water Tender", "ENGINEERING", 20,10,"ENGINEERING"),
        ("EM", "EM1 Frank Vance", "Electrician's Mate", "ENGINEERING", 47,18,"ENGINEERING"),
        ("DC", "CMM Robert Hale", "Damage Control", "DAMAGE_CONTROL", 60,18,"ENGINEERING"),
        ("GUN", "GM1 Thomas Reed", "Gunner's Mate", "FIRE_CONTROL", 61,18,"ISLAND"),
        ("AIR", "ACM1 James Cole", "Aviation Machinist", "AIR_OPS", 12,12,"HANGAR"),
        ("DECK", "AB1 William Grant", "Aviation Boatswain", "AIR_OPS", 35,13,"FLIGHT"),
        ("MED", "PhM1 Joseph Flynn", "Pharmacist's Mate", "MEDICAL", 43,8,"LOWER"),
        ("SUP", "SK1 Arthur Bell", "Storekeeper", "SUPPLY", 54,8,"LOWER"),
        ("COOK", "CSp1 Henry Moss", "Cook", "GALLEY", 31,8,"LOWER"),
        ("MACH", "MM1 Frank Kelly", "Machinist's Mate", "ENGINEERING", 22,18,"ENGINEERING"),
        ("ORD", "AOM1 Victor Lane", "Aviation Ordnanceman", "AIR_OPS", 60,12,"HANGAR"),
        ("LOOK", "S1 Robert King", "Lookout", "BRIDGE", 50,12,"BRIDGE"),
        ("MESS", "S2 David Ross", "Messman", "GALLEY", 31,8,"LOWER"),
    ]
    for key,name,rating,dept,lx,ly,floor in templates:
        x,y,z = _pos(lx,ly,floor)
        s.crew[key] = LivingCrew(key,name,rating,dept,x,y,z,x,y,z,
                                 fatigue=rng.uniform(5,18), hunger=rng.uniform(5,20), stress=rng.uniform(3,12), speed=rng.uniform(.8,1.35))
    generate_daily_work(s)
    return s


def generate_daily_work(s: LivingWorldState) -> None:
    if s._generated_daily:
        return
    s._generated_daily = True
    items = [
        ("MAGAZINE", "Inspect magazine temperature and security", "ORDNANCE", "Magazine Inspection Station", 540, "HIGH", "Verify temperature, sprinkling readiness, access control, and log conditions."),
        ("ELECTRICAL", "Inspect distribution panel and standby circuit", "ENGINEERING", "Electrical Shop Workbench", 600, "ROUTINE", "Check load balance, insulation indications, breaker condition, and standby supply."),
        ("AVIATION", "Complete aircraft servicing inspection", "AIR", "Aviation Maintenance Shop", 660, "HIGH", "Inspect servicing tools, leaks, chocks/tiedowns, and maintenance discrepancies."),
        ("MACHINE_SHOP", "Machinery preventive-maintenance round", "ENGINEERING", "Machine Shop Workbench", 720, "ROUTINE", "Lubrication, fastener, leakage, vibration, and tool-control checks."),
        ("ORDNANCE", "Inspect aviation ordnance handling area", "ORDNANCE", "Ordnance Maintenance Shop", 780, "HIGH", "Verify handling safety, segregation, equipment condition, and accountability."),
    ]
    for key,title,dept,loc,due,pri,detail in items:
        s.work_orders[key] = WorkOrder(key,title,dept,loc,due,pri,0.0,False,s.minute_of_day,detail)
    s.event_log.insert(0, f"{s.clock} — Daily work package issued: {len(items)} maintenance requirements.")


def _destination(dept: str, duty: str, minute: int) -> Tuple[float,float,float,str]:
    # Daily-life routing targets. These are simulation behavior, not a historical watchbill.
    if duty == "MESS":
        x,y,z = _pos(31,8,"LOWER"); return x,y,z,"MESS"
    if duty == "BERTHING":
        x,y,z = _pos(7 if dept not in ("AIR_OPS","ORDNANCE") else 64, 8 if dept not in ("AIR_OPS","ORDNANCE") else 18, "LOWER"); return x,y,z,"BERTHING"
    anchors = {
        "BRIDGE": (56,12,"BRIDGE"), "RADIO": (51,9,"ISLAND"), "CIC": (61,9,"ISLAND"),
        "ENGINEERING": (24,10,"ENGINEERING"), "DAMAGE_CONTROL": (60,18,"ENGINEERING"),
        "FIRE_CONTROL": (61,18,"ISLAND"), "AIR_OPS": (35,13,"FLIGHT"), "MEDICAL": (43,8,"LOWER"),
        "SUPPLY": (54,8,"LOWER"), "GALLEY": (31,8,"LOWER"), "ORDNANCE": (60,12,"HANGAR"),
    }
    lx,ly,floor = anchors.get(dept,(36,13,"HANGAR"))
    x,y,z = _pos(lx,ly,floor)
    return x,y,z,"WATCH"


def update_schedule(s: LivingWorldState) -> None:
    hour = (s.minute_of_day // 60) % 24
    if hour == s._last_schedule_hour:
        return
    s._last_schedule_hour = hour
    for idx, c in enumerate(s.crew.values()):
        # Stagger crew: approximately 1/3 watch, 1/3 maintenance/support, 1/3 off watch.
        phase = (hour + idx) % 8
        if phase in (0,1):
            duty = "MESS"
        elif phase in (6,7):
            duty = "BERTHING"
        else:
            duty = "WATCH"
        tx,ty,tz,label = _destination(c.home_department,duty,s.minute_of_day)
        c.target_x,c.target_y,c.target_z,c.duty = tx,ty,tz,label
    s.event_log.insert(0, f"{s.clock} — Ship routine updated: watch, mess, maintenance and off-watch movements in progress.")


def advance_life(s: LivingWorldState, minutes: int = 1) -> None:
    for _ in range(max(1,int(minutes))):
        s.minute_of_day += 1
        if s.minute_of_day >= 1440:
            s.minute_of_day = 0
            s.day += 1
            s._generated_daily = False
            generate_daily_work(s)
        n = s.needs
        n.hunger = min(100.0, n.hunger + .055)
        n.hydration = min(100.0, n.hydration + .07)
        n.fatigue = min(100.0, n.fatigue + .038)
        if n.hunger > 70 or n.hydration > 70 or n.fatigue > 80:
            n.stress = min(100.0, n.stress + .05)
            n.wellness = max(0.0, n.wellness - .015)
            s.routine_score = max(0.0, s.routine_score - .01)
        else:
            n.stress = max(0.0, n.stress - .012)
        for c in s.crew.values():
            c.hunger = min(100.0, c.hunger + .04)
            c.fatigue = min(100.0, c.fatigue + (.025 if c.duty == "WATCH" else -.02))
            c.stress = min(100.0, max(0.0, c.stress + (.015 if c.duty == "WATCH" else -.02)))
        for wo in s.work_orders.values():
            if not wo.completed and s.minute_of_day > wo.due_minute:
                s.routine_score = max(0.0, s.routine_score - .015)
        update_schedule(s)


def _nearest_floor(z: float) -> float:
    floors=sorted({l.floor_z for k,l in LAYERS.items() if k != "BASE"})
    return min(floors,key=lambda f:abs(f-z))


def _next_connector(c: LivingCrew):
    current=_nearest_floor(c.floor_z); target=_nearest_floor(c.target_z)
    if abs(current-target)<.1:
        return None,target
    floors=sorted({l.floor_z for k,l in LAYERS.items() if k != "BASE"})
    ci=floors.index(current); ti=floors.index(target); next_floor=floors[ci+(1 if ti>ci else -1)]
    candidates=[]
    for conn in CONNECTORS.values():
        ends={round(conn.from_z,2),round(conn.to_z,2)}
        if {round(current,2),round(next_floor,2)}==ends:
            candidates.append(conn)
    if not candidates:
        return None,next_floor
    return min(candidates,key=lambda q:math.hypot(c.x-q.x,c.y-q.y)),next_floor


def update_crew_positions(s: LivingWorldState, dt: float) -> None:
    for c in s.crew.values():
        current=_nearest_floor(c.floor_z); target=_nearest_floor(c.target_z)
        if abs(current-target)>.1 or abs(c.floor_z-current)>.08:
            conn,next_floor=_next_connector(c)
            if conn is not None and abs(c.floor_z-current)<=.1:
                dx,dy=conn.x-c.x,conn.y-c.y; d=math.hypot(dx,dy)
                if d>.18:
                    step=min(d,c.speed*dt); c.x+=dx/d*step; c.y+=dy/d*step
                    continue
                c.floor_z += max(-1,min(1,next_floor-c.floor_z))*dt*2.0
                if abs(c.floor_z-next_floor)<.08: c.floor_z=next_floor
                continue
            dz=next_floor-c.floor_z
            c.floor_z += max(-1,min(1,dz))*dt*2.0
            if abs(c.floor_z-next_floor)<.08: c.floor_z=next_floor
            continue
        dx,dy=c.target_x-c.x,c.target_y-c.y; d=math.hypot(dx,dy)
        if d>.08:
            step=min(d,c.speed*dt); c.x+=dx/d*step; c.y+=dy/d*step


def eat_meal(s: LivingWorldState) -> str:
    n=s.needs
    n.hunger=max(0,n.hunger-58); n.hydration=max(0,n.hydration-35); n.stress=max(0,n.stress-5)
    s.meals_eaten += 1
    s.event_log.insert(0,f"{s.clock} — Meal completed; hydration and nutrition restored.")
    return "Meal completed. Hunger, hydration and stress improved."


def sleep_period(s: LivingWorldState) -> str:
    n=s.needs
    n.fatigue=max(0,n.fatigue-62); n.stress=max(0,n.stress-18); n.hunger=min(100,n.hunger+10); n.hydration=min(100,n.hydration+8)
    s.sleep_periods += 1
    s.event_log.insert(0,f"{s.clock} — Off-watch sleep period completed.")
    return "Off-watch sleep completed. Fatigue and stress reduced."


def medical_check(s: LivingWorldState) -> str:
    n=s.needs
    n.wellness=min(100,n.wellness+22); n.stress=max(0,n.stress-8)
    s.medical_visits += 1
    s.event_log.insert(0,f"{s.clock} — Medical evaluation completed.")
    return "Medical evaluation completed; wellness improved."


def complete_maintenance(s: LivingWorldState, key: str) -> Tuple[bool,str]:
    wo=s.work_orders.get(key)
    if not wo:
        return False,"No matching maintenance requirement is on the work package."
    if wo.completed:
        return True,f"{wo.title} is already complete."
    wo.progress=100.0; wo.completed=True; s.maintenance_completed += 1
    s.routine_score=min(100.0,s.routine_score+2.5)
    s.event_log.insert(0,f"{s.clock} — WORK COMPLETE [{wo.department}]: {wo.title}.")
    return True,f"Maintenance complete: {wo.title}."


def workboard_lines(s: LivingWorldState) -> List[str]:
    lines=[]
    for wo in s.work_orders.values():
        status="COMPLETE" if wo.completed else ("OVERDUE" if s.minute_of_day>wo.due_minute else "OPEN")
        due=f"{wo.due_minute//60:02d}:{wo.due_minute%60:02d}"
        lines.append(f"{status:8} {wo.priority:7} {wo.department:12} due {due} — {wo.title}")
    return lines


def needs_summary(s: LivingWorldState) -> str:
    n=s.needs
    return f"Hunger {n.hunger:.0f}%  Hydration {n.hydration:.0f}%  Fatigue {n.fatigue:.0f}%  Stress {n.stress:.0f}%  Wellness {n.wellness:.0f}%"
