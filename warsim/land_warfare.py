from __future__ import annotations

"""v2.1 large-scale land warfare / battlefield command simulation.

All coefficients, force labels, vehicle performance, artillery effects, sector geometry and
training enemy behavior in this module are GAME/TRAINING abstractions. They are deliberately
kept separate from the locked historical scenario layer.
"""

from dataclasses import dataclass, field, asdict
import math
from typing import Dict, List, Optional, Tuple


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _bearing(x0: float, y0: float, x1: float, y1: float) -> float:
    return math.degrees(math.atan2(y1-y0, x1-x0)) % 360.0


@dataclass
class LandUnit:
    key: str
    name: str
    role: str
    x: float
    y: float
    manpower: int
    max_manpower: int
    morale: float = 82.0
    suppression: float = 0.0
    ammo_pct: float = 100.0
    readiness: float = 90.0
    fatigue: float = 12.0
    order: str = "HOLD"
    target_x: float = 0.0
    target_y: float = 0.0
    status: str = "READY"
    casualties: int = 0
    wounded: int = 0
    experience: float = 45.0


@dataclass
class ArmoredVehicle:
    key: str
    name: str
    vehicle_class: str
    x: float
    y: float
    heading_deg: float = 0.0
    speed_mps: float = 0.0
    throttle: float = 0.0
    fuel_pct: float = 100.0
    hull_pct: float = 100.0
    mobility_pct: float = 100.0
    crew: int = 4
    main_ammo: int = 35
    mg_ammo: int = 900
    engine_running: bool = False
    selected: bool = False
    order: str = "PARKED"
    target_x: float = 0.0
    target_y: float = 0.0
    distance_m: float = 0.0
    brake: bool = True


@dataclass
class ArtilleryBattery:
    key: str
    name: str
    x: float
    y: float
    tubes: int = 4
    shells: int = 120
    readiness: float = 92.0
    cooldown: float = 0.0
    missions_fired: int = 0
    status: str = "READY"


@dataclass
class BattlefieldSector:
    key: str
    name: str
    x: float
    y: float
    radius_m: float
    friendly_control: float = 0.0
    enemy_strength: float = 100.0
    fortification: float = 35.0
    status: str = "CONTESTED"
    objective: str = "SECURE"
    progress_seconds: float = 0.0


@dataclass
class BattlefieldContact:
    key: str
    label: str
    x: float
    y: float
    contact_type: str
    strength: float = 100.0
    suppression: float = 0.0
    confidence: float = 0.0
    identified: bool = False
    status: str = "HIDDEN"
    armor: float = 0.0


@dataclass
class CasualtyEvac:
    wounded_waiting: int = 0
    litter_teams_available: int = 2
    ambulances_available: int = 1
    evacuation_progress: float = 0.0
    evacuated_total: int = 0
    medical_stores: float = 100.0
    active: bool = False


@dataclass
class LandLogistics:
    ammunition: float = 100.0
    fuel: float = 100.0
    rations: float = 100.0
    medical: float = 100.0
    repair_parts: float = 100.0
    deliveries: int = 0
    resupply_cooldown: float = 0.0


@dataclass
class LandWarfareState:
    active: bool = False
    elapsed: float = 0.0
    phase: str = "STANDBY"
    units: Dict[str, LandUnit] = field(default_factory=dict)
    vehicles: Dict[str, ArmoredVehicle] = field(default_factory=dict)
    artillery: Dict[str, ArtilleryBattery] = field(default_factory=dict)
    sectors: Dict[str, BattlefieldSector] = field(default_factory=dict)
    contacts: Dict[str, BattlefieldContact] = field(default_factory=dict)
    casualty_evac: CasualtyEvac = field(default_factory=CasualtyEvac)
    logistics: LandLogistics = field(default_factory=LandLogistics)
    selected_unit_index: int = 0
    selected_vehicle_index: int = 0
    selected_sector_index: int = 0
    selected_contact_index: int = 0
    player_vehicle_key: str = ""
    command_points: float = 100.0
    score: float = 100.0
    sectors_secured: int = 0
    armored_kills: int = 0
    infantry_positions_cleared: int = 0
    artillery_missions: int = 0
    resupply_actions: int = 0
    medevac_actions: int = 0
    operations_completed: int = 0
    operations_failed: int = 0
    last_event: str = "v2.1 battlefield command initialized."
    log: List[str] = field(default_factory=list)

    @property
    def selected_unit(self) -> Optional[LandUnit]:
        vals=list(self.units.values())
        return vals[self.selected_unit_index % len(vals)] if vals else None

    @property
    def selected_vehicle(self) -> Optional[ArmoredVehicle]:
        vals=list(self.vehicles.values())
        return vals[self.selected_vehicle_index % len(vals)] if vals else None

    @property
    def selected_sector(self) -> Optional[BattlefieldSector]:
        vals=list(self.sectors.values())
        return vals[self.selected_sector_index % len(vals)] if vals else None

    @property
    def selected_contact(self) -> Optional[BattlefieldContact]:
        vals=[c for c in self.contacts.values() if c.strength>0]
        return vals[self.selected_contact_index % len(vals)] if vals else None


def create_land_warfare() -> LandWarfareState:
    s=LandWarfareState()
    s.units={
        "1PLT": LandUnit("1PLT","1st Rifle Platoon","INFANTRY",18,118,34,34,experience=52),
        "2PLT": LandUnit("2PLT","2nd Rifle Platoon","INFANTRY",26,120,35,35,experience=48),
        "WPN": LandUnit("WPN","Weapons Platoon","SUPPORT",34,118,28,28,ammo_pct=100,experience=56),
        "ENG": LandUnit("ENG","Combat Engineer Section","ENGINEER",42,120,18,18,readiness=94,experience=63),
        "MED": LandUnit("MED","Battalion Aid Detachment","MEDICAL",14,130,12,12,readiness=96,experience=66),
        "LOG": LandUnit("LOG","Combat Logistics Section","LOGISTICS",30,132,20,20,readiness=91,experience=58),
    }
    s.vehicles={
        "TANK1": ArmoredVehicle("TANK1","Armor One","MEDIUM_TANK",14,112,heading_deg=90,crew=5,main_ammo=42),
        "TANK2": ArmoredVehicle("TANK2","Armor Two","MEDIUM_TANK",20,112,heading_deg=90,crew=5,main_ammo=42),
        "APC1": ArmoredVehicle("APC1","Troop Carrier One","ARMORED_TRANSPORT",28,112,heading_deg=90,crew=2,main_ammo=0,mg_ammo=1200),
        "TRK1": ArmoredVehicle("TRK1","Supply Truck One","LOGISTICS_TRUCK",36,112,heading_deg=90,crew=2,main_ammo=0,mg_ammo=0),
        "AMB1": ArmoredVehicle("AMB1","Field Ambulance One","AMBULANCE",44,112,heading_deg=90,crew=2,main_ammo=0,mg_ammo=0),
    }
    s.artillery={
        "BAT-A": ArtilleryBattery("BAT-A","Field Artillery Battery A",52,118,tubes=4,shells=120),
    }
    s.sectors={
        "ALPHA": BattlefieldSector("ALPHA","Sector Alpha — Hedgerow Line",18,145,11,friendly_control=5,enemy_strength=82,fortification=42),
        "BRAVO": BattlefieldSector("BRAVO","Sector Bravo — Crossroads",36,148,12,friendly_control=0,enemy_strength=95,fortification=55),
        "CHARLIE": BattlefieldSector("CHARLIE","Sector Charlie — Ridge Position",52,144,10,friendly_control=0,enemy_strength=88,fortification=62),
        "DELTA": BattlefieldSector("DELTA","Sector Delta — Rear Supply Route",34,160,12,friendly_control=0,enemy_strength=75,fortification=28),
    }
    s.contacts={
        "E-INF-1": BattlefieldContact("E-INF-1","Opposing Infantry Strongpoint",18,145,"INFANTRY",strength=82,armor=0),
        "E-AT-1": BattlefieldContact("E-AT-1","Opposing Anti-Armor Position",35,148,"ANTI_ARMOR",strength=80,armor=10),
        "E-ARM-1": BattlefieldContact("E-ARM-1","Opposing Armored Section",49,145,"ARMOR",strength=100,armor=55),
        "E-INF-2": BattlefieldContact("E-INF-2","Opposing Reserve Position",34,160,"INFANTRY",strength=76,armor=0),
    }
    s.log.append(s.last_event)
    return s


def begin_operation(s: LandWarfareState) -> Tuple[bool,str]:
    if s.active: return False,"Large-scale land operation is already active."
    completed=s.operations_completed; failed=s.operations_failed
    fresh=create_land_warfare(); fresh.operations_completed=completed; fresh.operations_failed=failed
    s.__dict__.update(fresh.__dict__); s.active=True; s.phase="ADVANCE"
    msg="BATTALION FIELD OPERATION STARTED — secure Sectors Alpha through Delta while sustaining the force."
    s.last_event=msg; s.log.insert(0,msg)
    return True,msg


def cycle_unit(s: LandWarfareState) -> Optional[LandUnit]:
    if not s.units: return None
    s.selected_unit_index=(s.selected_unit_index+1)%len(s.units); return s.selected_unit


def cycle_vehicle(s: LandWarfareState) -> Optional[ArmoredVehicle]:
    if not s.vehicles: return None
    s.selected_vehicle_index=(s.selected_vehicle_index+1)%len(s.vehicles); return s.selected_vehicle


def cycle_sector(s: LandWarfareState) -> Optional[BattlefieldSector]:
    if not s.sectors: return None
    s.selected_sector_index=(s.selected_sector_index+1)%len(s.sectors); return s.selected_sector


def cycle_contact(s: LandWarfareState) -> Optional[BattlefieldContact]:
    vals=[c for c in s.contacts.values() if c.strength>0]
    if not vals: return None
    s.selected_contact_index=(s.selected_contact_index+1)%len(vals); return s.selected_contact


def order_selected_unit(s: LandWarfareState, order: str) -> Tuple[bool,str]:
    u=s.selected_unit; sec=s.selected_sector
    if not s.active: return False,"No battalion field operation is active."
    if not u: return False,"No ground unit selected."
    order=order.upper()
    if order not in ("HOLD","ADVANCE","SUPPRESS","ASSAULT","DIG IN","WITHDRAW","RESUPPLY"):
        return False,"Unknown battlefield order."
    u.order=order
    if sec and order in ("ADVANCE","SUPPRESS","ASSAULT","DIG IN"):
        u.target_x,u.target_y=sec.x,sec.y
    elif order=="WITHDRAW": u.target_x,u.target_y=24,120
    elif order=="RESUPPLY": u.target_x,u.target_y=30,132
    msg=f"{u.name} ordered {order}{' toward '+sec.name if sec and order in ('ADVANCE','SUPPRESS','ASSAULT','DIG IN') else ''}."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def enter_selected_vehicle(s: LandWarfareState, player_x: float, player_y: float, radius: float=3.0) -> Tuple[bool,str]:
    if s.player_vehicle_key: return False,"Already operating a battlefield vehicle."
    candidates=[v for v in s.vehicles.values() if v.hull_pct>0]
    if not candidates: return False,"No serviceable battlefield vehicle available."
    v=min(candidates,key=lambda q:math.hypot(q.x-player_x,q.y-player_y))
    if math.hypot(v.x-player_x,v.y-player_y)>radius: return False,"Move closer to a battlefield vehicle."
    s.player_vehicle_key=v.key; v.engine_running=False; v.brake=True; v.throttle=0
    return True,f"Entered {v.name} ({v.vehicle_class}). Start engine with I."


def exit_player_vehicle(s: LandWarfareState) -> Tuple[bool,str]:
    if not s.player_vehicle_key: return False,"Not operating a battlefield vehicle."
    v=s.vehicles[s.player_vehicle_key]
    if abs(v.speed_mps)>.35: return False,"Stop the vehicle before dismounting."
    s.player_vehicle_key=""; v.throttle=0; v.brake=True
    return True,f"Dismounted {v.name}."


def toggle_vehicle_engine(s: LandWarfareState) -> Tuple[bool,str]:
    if not s.player_vehicle_key: return False,"No battlefield vehicle selected for direct control."
    v=s.vehicles[s.player_vehicle_key]
    if v.fuel_pct<=0: return False,"Vehicle fuel exhausted."
    v.engine_running=not v.engine_running
    if not v.engine_running: v.throttle=0
    return True,f"{v.name} engine {'RUNNING' if v.engine_running else 'SECURED'}."


def adjust_vehicle_throttle(s: LandWarfareState, delta: float) -> str:
    if not s.player_vehicle_key: return "No battlefield vehicle under direct control."
    v=s.vehicles[s.player_vehicle_key]
    v.throttle=_clamp(v.throttle+delta,-0.45,1.0)
    if abs(v.throttle)>.02: v.brake=False
    return f"{v.name} throttle {v.throttle*100:+.0f}%."


def player_vehicle(s: LandWarfareState) -> Optional[ArmoredVehicle]:
    return s.vehicles.get(s.player_vehicle_key) if s.player_vehicle_key else None


def fire_vehicle_weapon(s: LandWarfareState) -> Tuple[bool,str]:
    v=player_vehicle(s); c=s.selected_contact
    if not v: return False,"Not operating a battlefield vehicle."
    if not c: return False,"No battlefield contact selected."
    if v.vehicle_class=="MEDIUM_TANK":
        if v.main_ammo<=0: return False,"Main-gun ammunition exhausted."
        v.main_ammo-=1; damage=58.0 if c.contact_type=="ARMOR" else 72.0
    elif v.mg_ammo>0:
        v.mg_ammo=max(0,v.mg_ammo-25); damage=18.0 if c.contact_type!="ARMOR" else 5.0
    else: return False,"This vehicle has no direct-fire weapon."
    rng=math.hypot(c.x-v.x,c.y-v.y)
    if rng>70: damage*=.35
    c.strength=_clamp(c.strength-damage,0,100); c.suppression=100; c.confidence=100; c.identified=True
    if c.strength<=0:
        c.status="NEUTRALIZED"
        if c.contact_type=="ARMOR": s.armored_kills+=1
        else: s.infantry_positions_cleared+=1
    else: c.status="ENGAGED"
    msg=f"{v.name} engaged {c.label} — target strength {c.strength:.0f}%."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def request_artillery(s: LandWarfareState) -> Tuple[bool,str]:
    if not s.active: return False,"No battlefield operation is active."
    c=s.selected_contact; b=next(iter(s.artillery.values()),None)
    if not c: return False,"No contact selected for artillery."
    if not b or b.shells<8: return False,"Artillery battery lacks ammunition."
    if b.cooldown>0: return False,f"Artillery battery is resetting ({b.cooldown:.0f}s)."
    if s.command_points<8: return False,"Insufficient command points."
    b.shells-=8; b.cooldown=18; b.missions_fired+=1; s.artillery_missions+=1; s.command_points-=8
    effect=42*(b.readiness/100.0)*(1-c.armor/140.0)
    c.strength=_clamp(c.strength-effect,0,100); c.suppression=100; c.confidence=100; c.identified=True
    c.status="NEUTRALIZED" if c.strength<=0 else "SUPPRESSED"
    if c.strength<=0:
        if c.contact_type=="ARMOR": s.armored_kills+=1
        else: s.infantry_positions_cleared+=1
    msg=f"SIMULATED ARTILLERY FIRE MISSION — {c.label} strength {c.strength:.0f}%; Battery A shells {b.shells}."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def request_joint_air_support(s: LandWarfareState, ground_ops) -> Tuple[bool,str]:
    c=s.selected_contact
    if not c: return False,"No contact selected for joint air support."
    available=float(getattr(ground_ops,"air_support_points",0.0))
    if available<18: return False,"Insufficient carrier/airfield support points."
    if s.command_points<10: return False,"Insufficient command points."
    ground_ops.air_support_points=available-18; s.command_points-=10
    c.strength=_clamp(c.strength-(52 if c.contact_type=="ARMOR" else 62),0,100); c.suppression=100; c.confidence=100; c.identified=True
    c.status="NEUTRALIZED" if c.strength<=0 else "SUPPRESSED"
    msg=f"SIMULATED JOINT AIR SUPPORT — {c.label} strength {c.strength:.0f}% / air support remaining {ground_ops.air_support_points:.0f}."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def request_naval_gunfire(s: LandWarfareState, task_force) -> Tuple[bool,str]:
    c=s.selected_contact
    if not c: return False,"No contact selected for naval gunfire."
    fleet=getattr(task_force,"friendly",{})
    ships=[v for v in fleet.values() if getattr(v,"hull_pct",100)>50 and getattr(v,"ammo_pct",100)>12]
    if not ships: return False,"No escort has ammunition/readiness for fire support."
    if s.command_points<10: return False,"Insufficient command points."
    ship=ships[0]; ship.ammo_pct=max(0,ship.ammo_pct-6); s.command_points-=10
    c.strength=_clamp(c.strength-(46 if c.contact_type=="ARMOR" else 64),0,100); c.suppression=100; c.confidence=100; c.identified=True
    c.status="NEUTRALIZED" if c.strength<=0 else "SUPPRESSED"
    msg=f"SIMULATED NAVAL GUNFIRE — {getattr(ship,'name','escort')} engaged {c.label}; target strength {c.strength:.0f}%."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def resupply_selected_unit(s: LandWarfareState) -> Tuple[bool,str]:
    u=s.selected_unit
    if not u: return False,"No unit selected."
    if s.logistics.ammunition<8 or s.logistics.rations<4: return False,"Battalion logistics stocks are insufficient."
    s.logistics.ammunition-=8; s.logistics.rations-=4; u.ammo_pct=_clamp(u.ammo_pct+45,0,100); u.readiness=_clamp(u.readiness+12,0,100); u.fatigue=_clamp(u.fatigue-8,0,100)
    s.resupply_actions+=1; s.logistics.deliveries+=1
    return True,f"{u.name} resupplied — ammo {u.ammo_pct:.0f}% / readiness {u.readiness:.0f}%."


def service_selected_vehicle(s: LandWarfareState) -> Tuple[bool,str]:
    v=s.selected_vehicle
    if not v: return False,"No battlefield vehicle selected."
    if s.logistics.repair_parts<8 or s.logistics.fuel<6: return False,"Insufficient repair/fuel stocks."
    s.logistics.repair_parts-=8; s.logistics.fuel-=6
    v.hull_pct=_clamp(v.hull_pct+35,0,100); v.mobility_pct=_clamp(v.mobility_pct+45,0,100); v.fuel_pct=_clamp(v.fuel_pct+40,0,100)
    return True,f"{v.name} serviced — hull {v.hull_pct:.0f}% / mobility {v.mobility_pct:.0f}% / fuel {v.fuel_pct:.0f}%."


def begin_medevac(s: LandWarfareState) -> Tuple[bool,str]:
    wounded=sum(u.wounded for u in s.units.values())
    if wounded<=0: return False,"No battalion casualties await evacuation."
    if s.casualty_evac.active: return False,"CASEVAC is already in progress."
    if s.logistics.medical<5: return False,"Insufficient medical stocks."
    s.casualty_evac.wounded_waiting=wounded; s.casualty_evac.active=True; s.casualty_evac.evacuation_progress=0
    s.logistics.medical-=5; s.medevac_actions+=1
    return True,f"CASEVAC dispatched for {wounded} wounded personnel."


def _advance_player_vehicle(s: LandWarfareState, dt: float, steer: float=0.0) -> None:
    v=player_vehicle(s)
    if not v: return
    target=0.0 if not v.engine_running or v.brake else v.throttle*(10.5 if v.vehicle_class=="MEDIUM_TANK" else 13.0)
    accel=2.0*(v.mobility_pct/100.0)
    if v.speed_mps<target: v.speed_mps=min(target,v.speed_mps+accel*dt)
    else: v.speed_mps=max(target,v.speed_mps-accel*1.5*dt)
    if abs(v.speed_mps)>.15:
        v.heading_deg=(v.heading_deg+steer*38.0*dt*min(1.0,abs(v.speed_mps)/5.0))%360
        dx=math.cos(math.radians(v.heading_deg))*v.speed_mps*dt; dy=math.sin(math.radians(v.heading_deg))*v.speed_mps*dt
        v.x+=dx; v.y+=dy; v.distance_m+=math.hypot(dx,dy); v.fuel_pct=_clamp(v.fuel_pct-abs(v.speed_mps)*dt*.006,0,100)
    if v.fuel_pct<=0: v.engine_running=False; v.throttle=0


def steer_player_vehicle(s: LandWarfareState, steer: float, dt: float) -> None:
    _advance_player_vehicle(s,dt,_clamp(steer,-1,1))


def _advance_ai_units(s: LandWarfareState, dt: float) -> List[str]:
    msgs=[]
    for u in s.units.values():
        if u.manpower<=0: continue
        dist=math.hypot(u.target_x-u.x,u.target_y-u.y)
        if u.order in ("ADVANCE","ASSAULT","SUPPRESS","DIG IN","WITHDRAW","RESUPPLY") and dist>.6:
            speed={"INFANTRY":1.2,"SUPPORT":.9,"ENGINEER":1.0,"MEDICAL":1.0,"LOGISTICS":1.0}.get(u.role,1.0)
            speed*=max(.35,1-u.fatigue/140.0); step=min(dist,speed*dt)
            u.x+=(u.target_x-u.x)/dist*step; u.y+=(u.target_y-u.y)/dist*step; u.fatigue=_clamp(u.fatigue+dt*.15,0,100)
        u.suppression=_clamp(u.suppression-dt*2.2,0,100)
        if u.order=="RESUPPLY" and math.hypot(u.x-30,u.y-132)<2.5:
            if u.ammo_pct<85 and s.logistics.ammunition>=4:
                s.logistics.ammunition-=4; u.ammo_pct=_clamp(u.ammo_pct+25,0,100); s.logistics.deliveries+=1; u.order="HOLD"; msgs.append(f"{u.name} completed field resupply.")
    return msgs


def _advance_sector_combat(s: LandWarfareState, dt: float) -> List[str]:
    msgs=[]
    for sec in s.sectors.values():
        friendly=[u for u in s.units.values() if u.manpower>0 and math.hypot(u.x-sec.x,u.y-sec.y)<=sec.radius_m+3]
        hostile=[c for c in s.contacts.values() if c.strength>0 and math.hypot(c.x-sec.x,c.y-sec.y)<=sec.radius_m+5]
        friendly_power=sum((u.manpower/max(1,u.max_manpower))*u.readiness*(u.ammo_pct/100.0)*(1-u.suppression/140.0) for u in friendly)
        hostile_power=sum(c.strength*(1-c.suppression/140.0)*(1+c.armor/160.0) for c in hostile)
        if friendly_power>0:
            sec.friendly_control=_clamp(sec.friendly_control+dt*(friendly_power/(hostile_power+80))*1.8,0,100)
            sec.enemy_strength=_clamp(sec.enemy_strength-dt*(friendly_power/(sec.fortification+80))*1.25,0,100)
            for c in hostile:
                pressure=dt*sum(1 for u in friendly if u.order in ("ASSAULT","SUPPRESS"))*1.3
                c.suppression=_clamp(c.suppression+pressure,0,100)
                if any(u.order=="ASSAULT" for u in friendly): c.strength=_clamp(c.strength-dt*friendly_power/220.0,0,100)
            # Deterministic casualty pulse under heavy opposition.
            pulse=int(s.elapsed/12.0); prev=int((s.elapsed-dt)/12.0)
            if hostile_power>20 and pulse!=prev and friendly:
                u=friendly[pulse%len(friendly)]; risk=min(35,int(hostile_power/8))
                if ((pulse*29+len(sec.key)*7)%100)<risk:
                    loss=1 if u.manpower>4 else 0
                    if loss:
                        u.manpower-=loss; u.casualties+=loss; u.wounded+=1; u.morale=_clamp(u.morale-3,0,100); s.casualty_evac.wounded_waiting+=1
                        msgs.append(f"{u.name} reports a training casualty in {sec.name}.")
        if sec.friendly_control>=85 and sec.enemy_strength<=12 and sec.status!="SECURED":
            sec.status="SECURED"; s.sectors_secured+=1; s.score=_clamp(s.score+4,0,100); msgs.append(f"BATTLEFIELD SECTOR SECURED — {sec.name}.")
        elif friendly_power>0: sec.status="CONTESTED"
        else: sec.status="ENEMY HELD" if sec.enemy_strength>20 else sec.status
    return msgs


def _advance_contacts(s: LandWarfareState, dt: float) -> None:
    for c in s.contacts.values():
        if c.strength<=0: c.status="NEUTRALIZED"; continue
        nearest=min((math.hypot(u.x-c.x,u.y-c.y) for u in s.units.values() if u.manpower>0),default=999)
        if nearest<55:
            c.confidence=_clamp(c.confidence+dt*(5 if nearest<30 else 2.5),0,100)
            if c.confidence>=20: c.status="CONTACT"
            if c.confidence>=50: c.identified=True
        c.suppression=_clamp(c.suppression-dt*2.0,0,100)


def advance_land_warfare(s: LandWarfareState, dt: float) -> List[str]:
    dt=max(0.0,float(dt)); s.elapsed+=dt; msgs=[]
    for b in s.artillery.values(): b.cooldown=max(0.0,b.cooldown-dt)
    s.logistics.resupply_cooldown=max(0.0,s.logistics.resupply_cooldown-dt)
    s.command_points=_clamp(s.command_points+dt*.35,0,100)
    if not s.active:
        return msgs
    msgs.extend(_advance_ai_units(s,dt)); _advance_contacts(s,dt); msgs.extend(_advance_sector_combat(s,dt))
    if s.casualty_evac.active:
        s.casualty_evac.evacuation_progress+=dt*8
        if s.casualty_evac.evacuation_progress>=100:
            moved=s.casualty_evac.wounded_waiting; s.casualty_evac.evacuated_total+=moved; s.casualty_evac.wounded_waiting=0; s.casualty_evac.active=False
            for u in s.units.values(): u.wounded=0
            msgs.append(f"CASEVAC COMPLETE — {moved} wounded moved to field hospital.")
    # Ongoing logistics consumption while battalion is committed.
    engaged=sum(1 for u in s.units.values() if u.order in ("ADVANCE","SUPPRESS","ASSAULT"))
    s.logistics.ammunition=_clamp(s.logistics.ammunition-dt*.015*engaged,0,100)
    s.logistics.rations=_clamp(s.logistics.rations-dt*.003*sum(1 for u in s.units.values() if u.manpower>0),0,100)
    if s.sectors_secured==len(s.sectors) and not any(c.strength>0 for c in s.contacts.values()):
        s.active=False; s.phase="COMPLETE"; s.operations_completed+=1; s.score=_clamp(s.score + max(0,10-s.casualty_evac.wounded_waiting),0,100)
        msgs.append(f"BATTALION FIELD OPERATION COMPLETE — score {s.score:.0f}%.")
    combat_manpower=sum(u.manpower for u in s.units.values() if u.role in ("INFANTRY","SUPPORT","ENGINEER"))
    if combat_manpower<=20 and s.active:
        s.active=False; s.phase="FAILED"; s.operations_failed+=1; s.score=max(0,s.score-30); msgs.append("BATTALION FIELD OPERATION FAILED — combat-effective manpower exhausted.")
    if msgs:
        s.last_event=msgs[-1]
        for m in reversed(msgs): s.log.insert(0,m)
        s.log=s.log[:80]
    return msgs


def warfare_summary(s: LandWarfareState) -> str:
    sec=s.selected_sector; u=s.selected_unit; v=s.selected_vehicle
    return (f"LAND WARFARE • {'ACTIVE' if s.active else s.phase} • SCORE {s.score:.0f}% • SECTORS {s.sectors_secured}/{len(s.sectors)} • "
            f"CP {s.command_points:.0f} • UNIT {u.key if u else '-'} • VEH {v.key if v else '-'} • SECTOR {sec.key if sec else '-'}")


def unit_lines(s: LandWarfareState) -> List[str]:
    out=[]
    for u in s.units.values():
        mark='>' if u is s.selected_unit else ' '
        out.append(f"{mark} {u.key:<5} {u.name:<27} {u.manpower:2}/{u.max_manpower:<2} AMMO {u.ammo_pct:3.0f}% RDY {u.readiness:3.0f}% MOR {u.morale:3.0f}% • {u.order}/{u.status}")
    return out


def vehicle_lines(s: LandWarfareState) -> List[str]:
    out=[]
    for v in s.vehicles.values():
        mark='>' if v is s.selected_vehicle else ' '
        out.append(f"{mark} {v.key:<6} {v.name:<20} {v.vehicle_class:<18} HULL {v.hull_pct:3.0f}% MOB {v.mobility_pct:3.0f}% FUEL {v.fuel_pct:3.0f}% AMMO {v.main_ammo:3} • {v.order}")
    return out


def sector_lines(s: LandWarfareState) -> List[str]:
    out=[]
    for sec in s.sectors.values():
        mark='>' if sec is s.selected_sector else ' '
        out.append(f"{mark} {sec.key:<7} {sec.name:<36} CTRL {sec.friendly_control:3.0f}% ENEMY {sec.enemy_strength:3.0f}% FORT {sec.fortification:3.0f}% • {sec.status}")
    return out


def contact_lines(s: LandWarfareState) -> List[str]:
    out=[]; selected=s.selected_contact
    for c in s.contacts.values():
        mark='>' if c is selected else ' '
        label=c.label if c.identified else 'Unidentified battlefield contact'
        out.append(f"{mark} {c.key:<8} {label:<32} STR {c.strength:3.0f}% SUP {c.suppression:3.0f}% CONF {c.confidence:3.0f}% • {c.status}")
    return out


def logistics_lines(s: LandWarfareState) -> List[str]:
    l=s.logistics; ce=s.casualty_evac
    return [
        f"Ammo {l.ammunition:.0f}% • Fuel {l.fuel:.0f}% • Rations {l.rations:.0f}% • Medical {l.medical:.0f}% • Repair {l.repair_parts:.0f}%",
        f"CASEVAC waiting {ce.wounded_waiting} • {'ACTIVE '+str(int(ce.evacuation_progress))+'%' if ce.active else 'standby'} • Evacuated {ce.evacuated_total}",
        f"Artillery shells {next(iter(s.artillery.values())).shells if s.artillery else 0} • Missions {s.artillery_missions} • Resupplies {s.resupply_actions}",
    ]


def land_warfare_to_dict(s: LandWarfareState) -> dict:
    return asdict(s)


def land_warfare_from_dict(data: dict) -> LandWarfareState:
    if not data: return create_land_warfare()
    base=create_land_warfare()
    for k,v in data.items():
        if k in ('units','vehicles','artillery','sectors','contacts','casualty_evac','logistics','log'): continue
        if hasattr(base,k): setattr(base,k,v)
    for key,val in data.get('units',{}).items():
        base.units[key]=LandUnit(**val)
    for key,val in data.get('vehicles',{}).items():
        base.vehicles[key]=ArmoredVehicle(**val)
    for key,val in data.get('artillery',{}).items():
        base.artillery[key]=ArtilleryBattery(**val)
    for key,val in data.get('sectors',{}).items():
        base.sectors[key]=BattlefieldSector(**val)
    for key,val in data.get('contacts',{}).items():
        base.contacts[key]=BattlefieldContact(**val)
    if data.get('casualty_evac'): base.casualty_evac=CasualtyEvac(**data['casualty_evac'])
    if data.get('logistics'): base.logistics=LandLogistics(**data['logistics'])
    base.log=list(data.get('log',base.log))[:80]
    return base
