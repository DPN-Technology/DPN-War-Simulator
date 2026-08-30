from __future__ import annotations

"""v2.2 persistent front-line / strategic war simulation.

This is a GAME/TRAINING abstraction layer. Sector names, force sizes, route capacities,
reinforcement timing, commander identities and combat coefficients are not represented as
historical facts. Historical scenarios remain in the locked historical data layer.
"""

from dataclasses import dataclass, field, asdict
import math
from typing import Dict, List, Optional, Tuple


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


@dataclass
class StrategicSector:
    key: str
    name: str
    x: float
    y: float
    value: int
    coastal: bool = False
    owner: str = "CONTESTED"
    control: float = 50.0  # 0 enemy / 100 friendly
    friendly_power: float = 0.0
    enemy_power: float = 70.0
    fortification: float = 35.0
    infrastructure: float = 80.0
    supply_level: float = 65.0
    intel_confidence: float = 15.0
    recon_age_min: float = 999.0
    road_open: bool = True
    bridge_integrity: float = 100.0
    status: str = "FRONT LINE"
    last_change: str = "Initial training front."


@dataclass
class StrategicFormation:
    key: str
    name: str
    side: str
    role: str
    x: float
    y: float
    strength: float = 100.0
    manpower: int = 900
    max_manpower: int = 900
    readiness: float = 82.0
    morale: float = 78.0
    supply: float = 82.0
    ammo: float = 86.0
    fuel: float = 84.0
    experience: float = 50.0
    commander: str = "Training Commander"
    order: str = "RESERVE"
    target_sector: str = ""
    status: str = "READY"
    casualties: int = 0
    movement_km: float = 0.0
    entrenchment: float = 10.0


@dataclass
class StrategicDepot:
    key: str
    name: str
    side: str
    x: float
    y: float
    fuel: float = 100.0
    ammunition: float = 100.0
    medical: float = 100.0
    replacements: int = 600
    repair: float = 100.0
    throughput: float = 100.0
    damage: float = 0.0
    status: str = "OPERATING"


@dataclass
class StrategicRoute:
    key: str
    name: str
    a: str
    b: str
    capacity: float = 100.0
    bridge_integrity: float = 100.0
    interdiction: float = 0.0
    open: bool = True
    deliveries: int = 0


@dataclass
class StrategicOperation:
    key: str
    title: str
    sector_key: str
    kind: str
    side: str = "FRIENDLY"
    status: str = "AVAILABLE"
    progress: float = 0.0
    priority: int = 2
    deadline_min: float = 720.0
    elapsed_min: float = 0.0
    reward: float = 8.0


@dataclass
class ReinforcementWave:
    key: str
    formation_key: str
    eta_min: float
    manpower: int
    strength: float
    side: str = "FRIENDLY"
    arrived: bool = False


@dataclass
class StrategicWarState:
    active: bool = False
    elapsed_min: float = 0.0
    day: int = 1
    hour: float = 6.0
    sectors: Dict[str, StrategicSector] = field(default_factory=dict)
    formations: Dict[str, StrategicFormation] = field(default_factory=dict)
    depots: Dict[str, StrategicDepot] = field(default_factory=dict)
    routes: Dict[str, StrategicRoute] = field(default_factory=dict)
    operations: Dict[str, StrategicOperation] = field(default_factory=dict)
    reinforcements: Dict[str, ReinforcementWave] = field(default_factory=dict)
    selected_sector_index: int = 0
    selected_formation_index: int = 0
    selected_depot_index: int = 0
    selected_operation_index: int = 0
    command_points: float = 100.0
    strategic_score: float = 75.0
    friendly_vp: int = 0
    enemy_vp: int = 0
    front_shifts: int = 0
    operations_completed: int = 0
    operations_failed: int = 0
    supply_deliveries: int = 0
    recon_reports: int = 0
    bridges_repaired: int = 0
    bridges_lost: int = 0
    reinforcement_waves: int = 0
    enemy_offensives: int = 0
    last_event: str = "v2.2 strategic war layer initialized."
    log: List[str] = field(default_factory=list)

    @property
    def selected_sector(self) -> Optional[StrategicSector]:
        vals=list(self.sectors.values())
        return vals[self.selected_sector_index % len(vals)] if vals else None

    @property
    def selected_formation(self) -> Optional[StrategicFormation]:
        vals=[f for f in self.formations.values() if f.side=="FRIENDLY"]
        return vals[self.selected_formation_index % len(vals)] if vals else None

    @property
    def selected_depot(self) -> Optional[StrategicDepot]:
        vals=[d for d in self.depots.values() if d.side=="FRIENDLY"]
        return vals[self.selected_depot_index % len(vals)] if vals else None

    @property
    def selected_operation(self) -> Optional[StrategicOperation]:
        vals=list(self.operations.values())
        return vals[self.selected_operation_index % len(vals)] if vals else None


def create_strategic_war() -> StrategicWarState:
    s=StrategicWarState()
    s.sectors={
        "NORTH": StrategicSector("NORTH","North Ridge",18,188,8,owner="FRIENDLY",control=72,enemy_power=42,fortification=30),
        "RIVER": StrategicSector("RIVER","River Crossing",34,194,12,owner="CONTESTED",control=48,enemy_power=76,fortification=52,bridge_integrity=74),
        "COAST": StrategicSector("COAST","Coastal Corridor",52,190,10,coastal=True,owner="FRIENDLY",control=66,enemy_power=48,fortification=28),
        "TOWN": StrategicSector("TOWN","Market Town",23,208,15,owner="CONTESTED",control=44,enemy_power=88,fortification=58),
        "HEIGHTS": StrategicSector("HEIGHTS","Hill 214",43,211,18,owner="ENEMY",control=28,enemy_power=96,fortification=70),
        "SOUTH": StrategicSector("SOUTH","Southern Supply Junction",33,227,14,owner="ENEMY",control=22,enemy_power=82,fortification=44),
    }
    s.formations={
        "F-1BDE": StrategicFormation("F-1BDE","1st Training Brigade","FRIENDLY","INFANTRY",16,178,manpower=2200,max_manpower=2200,readiness=88,morale=84,experience=62,commander="Col. Mercer",order="DEFEND",target_sector="NORTH"),
        "F-2BDE": StrategicFormation("F-2BDE","2nd Training Brigade","FRIENDLY","INFANTRY",31,181,manpower=2050,max_manpower=2050,readiness=84,morale=80,experience=57,commander="Col. Hayes",target_sector="RIVER"),
        "F-ARM": StrategicFormation("F-ARM","Armored Combat Group","FRIENDLY","ARMOR",46,179,manpower=780,max_manpower=780,readiness=86,morale=82,experience=65,commander="LtCol. Grant",fuel=76,target_sector="COAST"),
        "F-SUP": StrategicFormation("F-SUP","Operational Support Group","FRIENDLY","SUPPORT",31,173,manpower=620,max_manpower=620,readiness=92,morale=85,experience=60,commander="Maj. Ellis"),
        "E-1BDE": StrategicFormation("E-1BDE","Opposing 1st Brigade","ENEMY","INFANTRY",24,216,manpower=2100,max_manpower=2100,readiness=85,morale=81,experience=59,commander="OPFOR Commander A",order="DEFEND",target_sector="TOWN"),
        "E-ARM": StrategicFormation("E-ARM","Opposing Armored Group","ENEMY","ARMOR",44,219,manpower=720,max_manpower=720,readiness=86,morale=80,experience=63,commander="OPFOR Commander B",order="DEFEND",target_sector="HEIGHTS"),
        "E-2BDE": StrategicFormation("E-2BDE","Opposing 2nd Brigade","ENEMY","INFANTRY",34,235,manpower=1900,max_manpower=1900,readiness=80,morale=78,experience=53,commander="OPFOR Commander C",order="RESERVE",target_sector="SOUTH"),
    }
    s.depots={
        "F-MAIN": StrategicDepot("F-MAIN","Friendly Main Supply Depot","FRIENDLY",12,176,fuel=100,ammunition=100,medical=100,replacements=700,repair=100,throughput=100),
        "F-FWD": StrategicDepot("F-FWD","Forward Logistics Depot","FRIENDLY",50,180,fuel=78,ammunition=82,medical=76,replacements=280,repair=72,throughput=78),
        "E-MAIN": StrategicDepot("E-MAIN","Opposing Rear Depot","ENEMY",34,238,fuel=92,ammunition=94,medical=90,replacements=620,repair=90,throughput=88),
    }
    s.routes={
        "R-NORTH": StrategicRoute("R-NORTH","North Military Road","NORTH","RIVER",capacity=90),
        "R-RIVER": StrategicRoute("R-RIVER","River Bridge Route","RIVER","TOWN",capacity=72,bridge_integrity=74),
        "R-COAST": StrategicRoute("R-COAST","Coastal Road","COAST","HEIGHTS",capacity=88),
        "R-TOWN": StrategicRoute("R-TOWN","Town Supply Road","TOWN","SOUTH",capacity=80),
        "R-HEIGHTS": StrategicRoute("R-HEIGHTS","Heights Track","HEIGHTS","SOUTH",capacity=60),
    }
    s.operations={
        "OP-RIVER": StrategicOperation("OP-RIVER","Secure the River Crossing","RIVER","OFFENSIVE",priority=3,deadline_min=480,reward=10),
        "OP-TOWN": StrategicOperation("OP-TOWN","Seize Market Town","TOWN","OFFENSIVE",priority=4,deadline_min=720,reward=14),
        "OP-COAST": StrategicOperation("OP-COAST","Hold Coastal Corridor","COAST","DEFENSIVE",priority=3,deadline_min=600,reward=9),
        "OP-SUPPLY": StrategicOperation("OP-SUPPLY","Protect Forward Supply Network","NORTH","LOGISTICS",priority=2,deadline_min=900,reward=8),
    }
    s.reinforcements={
        "RW-1": ReinforcementWave("RW-1","F-1BDE",240,260,12),
        "RW-2": ReinforcementWave("RW-2","F-2BDE",480,320,15),
        "RW-E1": ReinforcementWave("RW-E1","E-1BDE",360,280,13,side="ENEMY"),
    }
    s.log=[s.last_event]
    return s


def begin_strategic_campaign(s: StrategicWarState) -> Tuple[bool,str]:
    if s.active:
        return False,"Strategic campaign is already active."
    s.active=True
    s.last_event="STRATEGIC CAMPAIGN ACTIVE — front line, reinforcements and logistics are now running continuously."
    s.log.insert(0,s.last_event)
    return True,s.last_event


def cycle_sector(s: StrategicWarState):
    if not s.sectors: return None
    s.selected_sector_index=(s.selected_sector_index+1)%len(s.sectors); return s.selected_sector


def cycle_formation(s: StrategicWarState):
    vals=[f for f in s.formations.values() if f.side=="FRIENDLY"]
    if not vals: return None
    s.selected_formation_index=(s.selected_formation_index+1)%len(vals); return s.selected_formation


def cycle_depot(s: StrategicWarState):
    vals=[d for d in s.depots.values() if d.side=="FRIENDLY"]
    if not vals: return None
    s.selected_depot_index=(s.selected_depot_index+1)%len(vals); return s.selected_depot


def cycle_operation(s: StrategicWarState):
    if not s.operations: return None
    s.selected_operation_index=(s.selected_operation_index+1)%len(s.operations); return s.selected_operation


def order_selected_formation(s: StrategicWarState, order: str) -> Tuple[bool,str]:
    f=s.selected_formation; sec=s.selected_sector
    if not f: return False,"No friendly formation selected."
    order=order.upper()
    if order not in ("RESERVE","DEFEND","ATTACK","RECON","WITHDRAW","RESUPPLY"):
        return False,"Unknown strategic formation order."
    if s.command_points < (8 if order=="ATTACK" else 4):
        return False,"Insufficient strategic command points."
    s.command_points-=8 if order=="ATTACK" else 4
    f.order=order
    if order in ("DEFEND","ATTACK","RECON") and sec:
        f.target_sector=sec.key
    elif order=="WITHDRAW":
        f.target_sector="NORTH"
    elif order=="RESUPPLY":
        f.target_sector=""
    msg=f"{f.name} ordered {order}{' — '+sec.name if sec and order in ('DEFEND','ATTACK','RECON') else ''}."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def accept_selected_operation(s: StrategicWarState) -> Tuple[bool,str]:
    op=s.selected_operation
    if not op: return False,"No strategic operation selected."
    if op.status=="ACTIVE": return False,"Operation is already active."
    if op.status=="COMPLETE": return False,"Operation is already complete."
    op.status="ACTIVE"; op.progress=0; op.elapsed_min=0
    msg=f"OPERATION ACCEPTED — {op.title}."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def request_recon(s: StrategicWarState) -> Tuple[bool,str]:
    sec=s.selected_sector
    if not sec: return False,"No sector selected for reconnaissance."
    if s.command_points<6: return False,"Insufficient command points for reconnaissance tasking."
    s.command_points-=6; sec.intel_confidence=_clamp(sec.intel_confidence+42,0,100); sec.recon_age_min=0; s.recon_reports+=1
    msg=f"RECON REPORT — {sec.name}: enemy strength estimate {sec.enemy_power:.0f} / fortification {sec.fortification:.0f}% / supply {sec.supply_level:.0f}%."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def request_strategic_artillery(s: StrategicWarState, land_warfare) -> Tuple[bool,str]:
    sec=s.selected_sector
    batteries=list(getattr(land_warfare,'artillery',{}).values())
    if not sec: return False,"No strategic sector selected."
    if not batteries or batteries[0].shells<12: return False,"Field artillery network lacks ammunition."
    if s.command_points<8: return False,"Insufficient strategic command points."
    b=batteries[0]; b.shells-=12; s.command_points-=8
    sec.enemy_power=_clamp(sec.enemy_power-10,0,150); sec.fortification=_clamp(sec.fortification-6,0,100)
    msg=f"ARTILLERY NETWORK FIRE PLAN — {sec.name}; enemy power {sec.enemy_power:.0f}, fortification {sec.fortification:.0f}%."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def request_air_interdiction(s: StrategicWarState, ground_ops) -> Tuple[bool,str]:
    sec=s.selected_sector
    pts=float(getattr(ground_ops,'air_support_points',0.0))
    if not sec: return False,"No sector selected for air interdiction."
    if pts<20: return False,"Insufficient air-support points."
    if s.command_points<10: return False,"Insufficient strategic command points."
    ground_ops.air_support_points=pts-20; s.command_points-=10
    sec.enemy_power=_clamp(sec.enemy_power-12,0,150); sec.supply_level=_clamp(sec.supply_level-18,0,100)
    for r in s.routes.values():
        if sec.key in (r.a,r.b): r.interdiction=_clamp(r.interdiction+22,0,100)
    msg=f"AIR INTERDICTION — {sec.name}; opposing supply flow disrupted."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def request_coastal_naval_support(s: StrategicWarState, task_force) -> Tuple[bool,str]:
    sec=s.selected_sector
    if not sec or not sec.coastal: return False,"Selected sector is not in naval-fire-support reach."
    ships=[v for v in getattr(task_force,'friendly',{}).values() if getattr(v,'hull_pct',100)>50 and getattr(v,'ammo_pct',100)>15]
    if not ships: return False,"No task-force ship has ammunition/readiness for strategic fire support."
    if s.command_points<10: return False,"Insufficient strategic command points."
    ship=ships[0]; ship.ammo_pct=max(0,ship.ammo_pct-8); s.command_points-=10
    sec.enemy_power=_clamp(sec.enemy_power-14,0,150); sec.fortification=_clamp(sec.fortification-8,0,100)
    msg=f"NAVAL FIRE SUPPORT — {getattr(ship,'name','escort')} engaged targets in {sec.name}."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def reinforce_selected_formation(s: StrategicWarState) -> Tuple[bool,str]:
    f=s.selected_formation; depot=s.selected_depot
    if not f or not depot: return False,"Select a friendly formation and depot."
    if depot.replacements<80 or depot.ammunition<8 or depot.fuel<5: return False,"Depot lacks replacement/supply stocks."
    depot.replacements-=80; depot.ammunition-=8; depot.fuel-=5
    f.manpower=min(f.max_manpower,f.manpower+80); f.strength=_clamp(f.strength+8,0,100); f.supply=_clamp(f.supply+20,0,100); f.ammo=_clamp(f.ammo+25,0,100); f.fuel=_clamp(f.fuel+20,0,100)
    s.reinforcement_waves+=1
    msg=f"REINFORCEMENT / RESUPPLY — {f.name} replenished from {depot.name}."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def repair_selected_bridge(s: StrategicWarState) -> Tuple[bool,str]:
    sec=s.selected_sector; depot=s.selected_depot
    if not sec or not depot: return False,"Select a sector and friendly depot."
    routes=[r for r in s.routes.values() if sec.key in (r.a,r.b) and r.bridge_integrity<99]
    if not routes: return False,"No damaged bridge route is associated with the selected sector."
    if depot.repair<12: return False,"Selected depot lacks engineer repair stores."
    r=min(routes,key=lambda q:q.bridge_integrity); depot.repair-=12; r.bridge_integrity=_clamp(r.bridge_integrity+35,0,100); r.open=r.bridge_integrity>30
    sec.bridge_integrity=max(sec.bridge_integrity,r.bridge_integrity); s.bridges_repaired+=1
    msg=f"ENGINEER BRIDGE REPAIR — {r.name} restored to {r.bridge_integrity:.0f}% integrity."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def _nearest_sector(s: StrategicWarState, f: StrategicFormation) -> Optional[StrategicSector]:
    return min(s.sectors.values(),key=lambda sec:math.hypot(sec.x-f.x,sec.y-f.y)) if s.sectors else None


def _move_formations(s: StrategicWarState, dt_min: float) -> None:
    for f in s.formations.values():
        if f.strength<=0: continue
        target=s.sectors.get(f.target_sector)
        if f.order=="RESERVE" or not target: continue
        dist=math.hypot(target.x-f.x,target.y-f.y)
        if dist<1.5: continue
        base=0.018 if f.role=="ARMOR" else 0.012
        speed=base*(f.readiness/100.0)*(f.fuel/100.0 if f.role=="ARMOR" else 1.0)
        step=min(dist,speed*dt_min)
        f.x+=(target.x-f.x)/dist*step; f.y+=(target.y-f.y)/dist*step; f.movement_km+=step
        f.fuel=_clamp(f.fuel-dt_min*(.012 if f.role=="ARMOR" else .002),0,100)
        f.supply=_clamp(f.supply-dt_min*.003,0,100)


def _supply_flow(s: StrategicWarState, dt_min: float) -> None:
    friendly_depots=[d for d in s.depots.values() if d.side=="FRIENDLY" and d.status=="OPERATING"]
    for f in [x for x in s.formations.values() if x.side=="FRIENDLY" and x.strength>0]:
        sec=_nearest_sector(s,f)
        if not sec or not friendly_depots: continue
        dep=min(friendly_depots,key=lambda d:math.hypot(d.x-f.x,d.y-f.y))
        route_factor=.85
        related=[r for r in s.routes.values() if sec.key in (r.a,r.b)]
        if related:
            route_factor=max(.1,max((r.capacity/100.0)*(r.bridge_integrity/100.0)*(1-r.interdiction/120.0) for r in related if r.open) if any(r.open for r in related) else .1)
        throughput=(dep.throughput/100.0)*(1-dep.damage/120.0)*route_factor
        transfer=min(.025*dt_min*throughput, max(0,100-f.supply))
        if transfer>0 and dep.ammunition>0 and dep.fuel>0:
            f.supply=_clamp(f.supply+transfer,0,100); f.ammo=_clamp(f.ammo+transfer*.75,0,100); f.fuel=_clamp(f.fuel+transfer*.45,0,100)
            dep.ammunition=max(0,dep.ammunition-transfer*.03); dep.fuel=max(0,dep.fuel-transfer*.02)
            if int(s.elapsed_min/60)!=int((s.elapsed_min-dt_min)/60): s.supply_deliveries+=1


def _resolve_front(s: StrategicWarState, dt_min: float) -> List[str]:
    msgs=[]
    tick=int(s.elapsed_min/10); prev=int((s.elapsed_min-dt_min)/10)
    if tick==prev: return msgs
    for sec in s.sectors.values():
        friendly=[f for f in s.formations.values() if f.side=="FRIENDLY" and f.strength>0 and math.hypot(f.x-sec.x,f.y-sec.y)<7.0]
        enemy=[f for f in s.formations.values() if f.side=="ENEMY" and f.strength>0 and math.hypot(f.x-sec.x,f.y-sec.y)<7.0]
        fp=sum(f.strength*(f.readiness/100)*(f.morale/100)*(f.supply/100)*(1.20 if f.order=="ATTACK" else 1.0) for f in friendly)
        ep=sec.enemy_power+sum(f.strength*(f.readiness/100)*(f.morale/100)*(f.supply/100)*(1.18 if f.order=="ATTACK" else 1.0) for f in enemy)
        sec.friendly_power=fp
        if fp+ep>0:
            delta=(fp-ep)/(fp+ep+50)*6.5
            if sec.fortification>40 and delta>0: delta*=max(.35,1-sec.fortification/140)
            sec.control=_clamp(sec.control+delta,0,100)
        # attrition is deterministic and intentionally modest.
        if friendly and enemy and abs(fp-ep)<140:
            loss_scale=min(1.5,(fp+ep)/250)
            for f in friendly:
                loss=max(0,int(loss_scale*(1.2-f.entrenchment/140)))
                if loss:
                    f.manpower=max(0,f.manpower-loss); f.casualties+=loss; f.strength=_clamp(f.strength-loss*.025,0,100); f.morale=_clamp(f.morale-.08*loss,0,100)
            for f in enemy:
                loss=max(0,int(loss_scale*(1.15-f.entrenchment/150)))
                if loss:
                    f.manpower=max(0,f.manpower-loss); f.casualties+=loss; f.strength=_clamp(f.strength-loss*.025,0,100)
        old=sec.owner
        if sec.control>=68: sec.owner="FRIENDLY"; sec.status="FRIENDLY HELD"
        elif sec.control<=32: sec.owner="ENEMY"; sec.status="ENEMY HELD"
        else: sec.owner="CONTESTED"; sec.status="FRONT LINE"
        if old!=sec.owner:
            sec.last_change=f"Day {s.day} {int(s.hour):02}:00 — {old} → {sec.owner}"
            s.front_shifts+=1; msgs.append(f"FRONT LINE SHIFT — {sec.name} is now {sec.owner}.")
            if sec.owner=="FRIENDLY": s.friendly_vp+=sec.value
            elif sec.owner=="ENEMY": s.enemy_vp+=sec.value
        sec.recon_age_min+=10
        sec.intel_confidence=_clamp(sec.intel_confidence-1.2,0,100)
    return msgs


def _enemy_ai(s: StrategicWarState, dt_min: float) -> List[str]:
    msgs=[]
    tick=int(s.elapsed_min/60); prev=int((s.elapsed_min-dt_min)/60)
    if tick==prev: return msgs
    enemy=[f for f in s.formations.values() if f.side=="ENEMY" and f.strength>25]
    if not enemy: return msgs
    candidates=[sec for sec in s.sectors.values() if sec.owner!="ENEMY"]
    if candidates:
        sec=sorted(candidates,key=lambda x:(x.control,-x.value))[0]
        f=enemy[tick%len(enemy)]; f.order="ATTACK"; f.target_sector=sec.key; s.enemy_offensives+=1
        msgs.append(f"OPFOR ACTIVITY — enemy formation pressure increasing toward {sec.name}.")
    # occasional route interdiction / bridge damage is deterministic.
    if tick>0 and tick%3==0:
        routes=list(s.routes.values()); r=routes[tick%len(routes)]; r.interdiction=_clamp(r.interdiction+12,0,100)
        if tick%6==0 and r.bridge_integrity>35:
            r.bridge_integrity=_clamp(r.bridge_integrity-18,0,100); r.open=r.bridge_integrity>30; s.bridges_lost+=1
            msgs.append(f"ROUTE DAMAGE — {r.name} bridge integrity reduced to {r.bridge_integrity:.0f}%.")
    return msgs


def _reinforcements(s: StrategicWarState, dt_min: float, economy=None) -> List[str]:
    msgs=[]
    for rw in s.reinforcements.values():
        if rw.arrived or s.elapsed_min<rw.eta_min: continue
        f=s.formations.get(rw.formation_key)
        if f:
            # v2.3: friendly reinforcement waves require national replacement and logistics stocks when the war-economy layer is active.
            if rw.side=="FRIENDLY" and economy is not None and getattr(economy,"active",False):
                stocks=getattr(economy,"stockpiles",{})
                need_people=float(rw.manpower); need_ammo=max(4.0,rw.strength*.35); need_fuel=max(2.0,rw.strength*.18)
                if stocks.get("TRAINED_PERSONNEL",0)<need_people or stocks.get("SMALL_ARMS_AMMO",0)<need_ammo or stocks.get("BUNKER_FUEL",0)<need_fuel:
                    rw.eta_min += 60
                    msgs.append(f"REINFORCEMENT DELAY — {f.name} replacement wave held for national manpower/ammunition/fuel shortage.")
                    continue
                stocks["TRAINED_PERSONNEL"]-=need_people; stocks["SMALL_ARMS_AMMO"]-=need_ammo; stocks["BUNKER_FUEL"]-=need_fuel
            f.manpower=min(f.max_manpower,f.manpower+rw.manpower); f.strength=_clamp(f.strength+rw.strength,0,100); f.readiness=_clamp(f.readiness+6,0,100); f.morale=_clamp(f.morale+5,0,100)
            rw.arrived=True; s.reinforcement_waves+=1; msgs.append(f"REINFORCEMENTS ARRIVED — {f.name} received {rw.manpower} personnel/equivalent combat replacements.")
    return msgs


def _operations(s: StrategicWarState, dt_min: float) -> List[str]:
    msgs=[]
    for op in s.operations.values():
        if op.status!="ACTIVE": continue
        op.elapsed_min+=dt_min; sec=s.sectors.get(op.sector_key)
        if not sec: continue
        if op.kind=="OFFENSIVE":
            if sec.owner=="FRIENDLY": op.progress=_clamp(op.progress+dt_min*.45,0,100)
            elif sec.control>50: op.progress=_clamp(op.progress+dt_min*.10,0,100)
        elif op.kind=="DEFENSIVE":
            if sec.owner=="FRIENDLY": op.progress=_clamp(op.progress+dt_min*.35,0,100)
            else: op.progress=_clamp(op.progress-dt_min*.18,0,100)
        elif op.kind=="LOGISTICS":
            good=sec.supply_level>55 and any(r.open and r.bridge_integrity>40 for r in s.routes.values() if sec.key in (r.a,r.b))
            if good: op.progress=_clamp(op.progress+dt_min*.28,0,100)
        if op.progress>=100:
            op.status="COMPLETE"; s.operations_completed+=1; s.strategic_score=_clamp(s.strategic_score+op.reward,0,100); msgs.append(f"STRATEGIC OPERATION COMPLETE — {op.title}.")
        elif op.elapsed_min>op.deadline_min:
            op.status="FAILED"; s.operations_failed+=1; s.strategic_score=_clamp(s.strategic_score-10,0,100); msgs.append(f"STRATEGIC OPERATION FAILED — {op.title} exceeded its operational window.")
    return msgs


def _sync_tactical_results(s: StrategicWarState, land_warfare, last_land_ops_completed: int) -> int:
    completed=int(getattr(land_warfare,'operations_completed',0))
    if completed>last_land_ops_completed:
        sec=s.selected_sector
        if sec:
            sec.control=_clamp(sec.control+24,0,100); sec.enemy_power=_clamp(sec.enemy_power-20,0,150); sec.fortification=_clamp(sec.fortification-10,0,100)
            sec.last_change=f"Tactical battalion victory applied at strategic level (operation {completed})."
            s.log.insert(0,f"TACTICAL RESULT LINK — battalion victory improved the situation in {sec.name}.")
    return completed


def advance_strategic_war(s: StrategicWarState, dt: float, land_warfare=None, ground_ops=None, task_force=None, campaign=None, last_land_ops_completed: int=0, economy=None) -> Tuple[List[str],int]:
    dt=max(0.0,float(dt)); dt_min=dt*2.0
    if not s.active:
        return [],last_land_ops_completed
    s.elapsed_min+=dt_min; s.hour=6.0+(s.elapsed_min/60.0); s.day=1+int(s.hour//24); s.hour%=24
    s.command_points=_clamp(s.command_points+dt_min*.035,0,100)
    _move_formations(s,dt_min); _supply_flow(s,dt_min)
    msgs=[]
    msgs.extend(_resolve_front(s,dt_min)); msgs.extend(_enemy_ai(s,dt_min)); msgs.extend(_reinforcements(s,dt_min,economy)); msgs.extend(_operations(s,dt_min))
    last_land_ops_completed=_sync_tactical_results(s,land_warfare,last_land_ops_completed) if land_warfare is not None else last_land_ops_completed
    # strategic score also reflects territory balance.
    held_f=sum(sec.value for sec in s.sectors.values() if sec.owner=="FRIENDLY")
    held_e=sum(sec.value for sec in s.sectors.values() if sec.owner=="ENEMY")
    s.strategic_score=_clamp(72+(held_f-held_e)*.35-s.operations_failed*5,0,100)
    if msgs:
        s.last_event=msgs[-1]
        for m in reversed(msgs): s.log.insert(0,m)
        s.log=s.log[:100]
    return msgs,last_land_ops_completed


def strategic_summary(s: StrategicWarState) -> str:
    f=sum(1 for sec in s.sectors.values() if sec.owner=="FRIENDLY"); e=sum(1 for sec in s.sectors.values() if sec.owner=="ENEMY")
    return f"STRATEGIC WAR • {'ACTIVE' if s.active else 'STANDBY'} • DAY {s.day} {int(s.hour):02}:00 • SCORE {s.strategic_score:.0f}% • SECTORS F {f} / E {e} / C {len(s.sectors)-f-e} • CP {s.command_points:.0f}"


def sector_lines(s: StrategicWarState) -> List[str]:
    out=[]
    for sec in s.sectors.values():
        mark='>' if sec is s.selected_sector else ' '
        intel=f"INTEL {sec.intel_confidence:3.0f}%" if sec.intel_confidence>=25 else "INTEL LOW"
        out.append(f"{mark} {sec.key:<8} {sec.name:<25} CTRL {sec.control:3.0f}% {sec.owner:<9} ENY {sec.enemy_power:3.0f} FORT {sec.fortification:3.0f}% SUP {sec.supply_level:3.0f}% {intel}")
    return out


def formation_lines(s: StrategicWarState) -> List[str]:
    out=[]
    selected=s.selected_formation
    for f in s.formations.values():
        if f.side!="FRIENDLY": continue
        mark='>' if f is selected else ' '
        out.append(f"{mark} {f.key:<7} {f.name:<25} STR {f.strength:3.0f}% MP {f.manpower:4}/{f.max_manpower:<4} RDY {f.readiness:3.0f}% SUP {f.supply:3.0f}% • {f.order} {f.target_sector}")
    return out


def depot_lines(s: StrategicWarState) -> List[str]:
    out=[]; selected=s.selected_depot
    for d in s.depots.values():
        if d.side!="FRIENDLY": continue
        mark='>' if d is selected else ' '
        out.append(f"{mark} {d.key:<7} {d.name:<27} FUEL {d.fuel:3.0f}% AMMO {d.ammunition:3.0f}% MED {d.medical:3.0f}% REPL {d.replacements:3} REPAIR {d.repair:3.0f}%")
    return out


def route_lines(s: StrategicWarState) -> List[str]:
    return [f"  {r.key:<9} {r.name:<24} {r.a}->{r.b} CAP {r.capacity:3.0f}% BRIDGE {r.bridge_integrity:3.0f}% INTERDICT {r.interdiction:3.0f}% • {'OPEN' if r.open else 'CLOSED'}" for r in s.routes.values()]


def operation_lines(s: StrategicWarState) -> List[str]:
    out=[]; selected=s.selected_operation
    for op in s.operations.values():
        mark='>' if op is selected else ' '
        out.append(f"{mark} {op.key:<10} {op.title:<34} {op.kind:<10} {op.status:<9} {op.progress:3.0f}% • sector {op.sector_key}")
    return out


def strategic_war_to_dict(s: StrategicWarState) -> dict:
    return asdict(s)


def strategic_war_from_dict(data: dict) -> StrategicWarState:
    if not data: return create_strategic_war()
    base=create_strategic_war()
    complex_keys={'sectors','formations','depots','routes','operations','reinforcements','log'}
    for k,v in data.items():
        if k in complex_keys: continue
        if hasattr(base,k): setattr(base,k,v)
    for k,v in data.get('sectors',{}).items(): base.sectors[k]=StrategicSector(**v)
    for k,v in data.get('formations',{}).items(): base.formations[k]=StrategicFormation(**v)
    for k,v in data.get('depots',{}).items(): base.depots[k]=StrategicDepot(**v)
    for k,v in data.get('routes',{}).items(): base.routes[k]=StrategicRoute(**v)
    for k,v in data.get('operations',{}).items(): base.operations[k]=StrategicOperation(**v)
    for k,v in data.get('reinforcements',{}).items(): base.reinforcements[k]=ReinforcementWave(**v)
    base.log=list(data.get('log',base.log))[:100]
    return base
