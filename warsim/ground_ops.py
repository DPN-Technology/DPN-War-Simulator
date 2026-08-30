from __future__ import annotations

"""v1.9 expeditionary ground/airbase/amphibious operations layer.

All unit names, exact manpower, ranges, vehicle performance, airfield geometry, mission locations,
combat coefficients and logistics quantities here are TRAINING SIMULATION ABSTRACTIONS. This
module does not alter the locked historical Midway scenario.
"""

from dataclasses import dataclass, field, asdict
import math
from typing import Dict, List, Optional, Tuple


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _bearing_range(e0: float, n0: float, e1: float, n1: float) -> Tuple[float,float]:
    de, dn = e1-e0, n1-n0
    return math.degrees(math.atan2(de,dn)) % 360.0, math.hypot(de,dn)


def _nav_vec(direction_deg: float, magnitude: float) -> Tuple[float,float]:
    r=math.radians(direction_deg)
    return math.sin(r)*magnitude, math.cos(r)*magnitude


@dataclass
class GroundUnit:
    key: str
    name: str
    unit_type: str
    east_nm: float
    north_nm: float
    strength_pct: float = 100.0
    morale_pct: float = 82.0
    fatigue_pct: float = 14.0
    supply_pct: float = 92.0
    manpower: int = 42
    speed_knots: float = 3.0
    order: str = "HOLD"
    target_east_nm: float = 0.0
    target_north_nm: float = 0.0
    status: str = "READY"
    casualties: int = 0
    experience: float = 50.0


@dataclass
class GroundVehicle:
    key: str
    name: str
    vehicle_type: str
    east_nm: float
    north_nm: float
    heading_deg: float = 90.0
    speed_knots: float = 0.0
    fuel_pct: float = 100.0
    health_pct: float = 100.0
    cargo_pct: float = 100.0
    crew: int = 2
    status: str = "READY"
    order: str = "HOLD"
    target_east_nm: float = 0.0
    target_north_nm: float = 0.0


@dataclass
class ExpeditionaryAirfield:
    key: str
    name: str
    east_nm: float
    north_nm: float
    runway_condition: float = 100.0
    aviation_fuel: float = 80.0
    ammunition: float = 70.0
    repair_stores: float = 65.0
    medical: float = 60.0
    security_pct: float = 80.0
    status: str = "OPERATIONAL"

    @property
    def readiness(self) -> float:
        return (self.runway_condition+self.aviation_fuel+self.ammunition+self.repair_stores+self.medical+self.security_pct)/6.0


@dataclass
class AmphibiousGroup:
    key: str
    name: str
    east_nm: float
    north_nm: float
    heading_deg: float = 90.0
    speed_knots: float = 8.0
    embarked_strength: int = 72
    craft_health_pct: float = 100.0
    status: str = "STAGED"
    target_east_nm: float = 0.0
    target_north_nm: float = 0.0
    progress_pct: float = 0.0


@dataclass
class GroundMission:
    key: str
    title: str
    mission_type: str
    target_east_nm: float
    target_north_nm: float
    radius_nm: float
    required_minutes: float
    status: str = "AVAILABLE"
    progress_minutes: float = 0.0
    reward_xp: int = 40
    description: str = ""
    air_support_required: bool = False
    amphibious_required: bool = False


@dataclass
class TrainingVehicleDrive:
    active: bool = False
    engine_running: bool = False
    vehicle_key: str = "BASE-JEEP"
    x: float = 17.0
    y: float = 53.0
    heading_deg: float = 90.0
    throttle: float = 0.0
    speed_mps: float = 0.0
    fuel_pct: float = 100.0
    health_pct: float = 100.0
    brake: bool = True
    distance_m: float = 0.0


@dataclass
class GroundOpsState:
    units: Dict[str,GroundUnit] = field(default_factory=dict)
    vehicles: Dict[str,GroundVehicle] = field(default_factory=dict)
    airfields: Dict[str,ExpeditionaryAirfield] = field(default_factory=dict)
    amphibious: Dict[str,AmphibiousGroup] = field(default_factory=dict)
    missions: Dict[str,GroundMission] = field(default_factory=dict)
    selected_unit_index: int = 0
    selected_vehicle_index: int = 0
    selected_airfield_index: int = 0
    selected_mission_index: int = 0
    active_mission_key: str = ""
    drive: TrainingVehicleDrive = field(default_factory=TrainingVehicleDrive)
    operations_minutes: float = 0.0
    missions_completed: int = 0
    missions_failed: int = 0
    amphibious_landings: int = 0
    airfield_services: int = 0
    ground_units_lost: int = 0
    vehicles_lost: int = 0
    supplies_delivered: float = 0.0
    air_support_points: float = 0.0
    operational_score: float = 100.0
    last_event: str = "v1.9 expeditionary training command initialized."
    log: List[str] = field(default_factory=list)

    @property
    def selected_unit(self) -> Optional[GroundUnit]:
        vals=list(self.units.values()); return vals[self.selected_unit_index%len(vals)] if vals else None
    @property
    def selected_vehicle(self) -> Optional[GroundVehicle]:
        vals=list(self.vehicles.values()); return vals[self.selected_vehicle_index%len(vals)] if vals else None
    @property
    def selected_airfield(self) -> Optional[ExpeditionaryAirfield]:
        vals=list(self.airfields.values()); return vals[self.selected_airfield_index%len(vals)] if vals else None
    @property
    def selected_mission(self) -> Optional[GroundMission]:
        vals=list(self.missions.values()); return vals[self.selected_mission_index%len(vals)] if vals else None
    @property
    def active_mission(self) -> Optional[GroundMission]:
        return self.missions.get(self.active_mission_key) if self.active_mission_key else None


def create_ground_ops() -> GroundOpsState:
    s=GroundOpsState()
    s.airfields={
        "HOME_AIR": ExpeditionaryAirfield("HOME_AIR","Home Expeditionary Airfield",6.0,-7.0,100,95,90,90,90,94),
        "ABLE_AIR": ExpeditionaryAirfield("ABLE_AIR","Forward Airfield Able",148.0,70.0,74,46,52,42,50,63),
    }
    s.units={
        "RIFLE_A": GroundUnit("RIFLE_A","1st Training Rifle Company","INFANTRY",4.0,-5.0,manpower=96,speed_knots=2.6,experience=55),
        "ENGR_A": GroundUnit("ENGR_A","Expeditionary Engineer Platoon","ENGINEER",5.0,-6.0,manpower=34,speed_knots=2.2,experience=62),
        "AA_A": GroundUnit("AA_A","Forward Airfield Defense Detachment","AIR_DEFENSE",148.0,70.0,manpower=46,speed_knots=1.6,experience=58),
        "LOG_A": GroundUnit("LOG_A","Shore Logistics Company","LOGISTICS",1.0,-4.0,manpower=74,speed_knots=2.0,experience=52),
    }
    s.vehicles={
        "TRUCK_A": GroundVehicle("TRUCK_A","Ground Supply Column A","CARGO_TRUCK",2.0,-4.0,cargo_pct=100,crew=12),
        "SCOUT_A": GroundVehicle("SCOUT_A","Reconnaissance Vehicle Section","SCOUT",5.0,-5.0,cargo_pct=35,crew=6),
        "ENG_VEH": GroundVehicle("ENG_VEH","Engineer Support Vehicle","ENGINEER",5.5,-6.0,cargo_pct=75,crew=5),
    }
    s.amphibious={
        "LANDING_A": AmphibiousGroup("LANDING_A","Amphibious Training Group A",32.0,-12.0,target_east_nm=84.0,target_north_nm=-24.0),
    }
    s.missions={
        "AIRFIELD_DEF": GroundMission("AIRFIELD_DEF","Forward Airfield Defense","DEFEND",148,70,4.0,24,reward_xp=45,description="Reinforce Forward Airfield Able and maintain defensive readiness.",air_support_required=True),
        "LANDING": GroundMission("LANDING","Amphibious Landing Exercise Alpha","AMPHIBIOUS",84,-24,3.0,28,reward_xp=60,description="Land and establish a secure beachhead at Training Island Alpha.",amphibious_required=True),
        "GROUND_LOG": GroundMission("GROUND_LOG","Forward Ground Supply Route","LOGISTICS",148,70,4.0,22,reward_xp=45,description="Move a ground supply column to Forward Airfield Able.",air_support_required=False),
        "RECON": GroundMission("RECON","Reconnaissance Patrol Sector Red","RECON",62,18,8.0,18,reward_xp=40,description="Move reconnaissance elements into the assigned patrol sector and report.",air_support_required=False),
    }
    s.log.append(s.last_event)
    return s


def cycle_unit(s: GroundOpsState) -> Optional[GroundUnit]:
    if not s.units: return None
    s.selected_unit_index=(s.selected_unit_index+1)%len(s.units); return s.selected_unit

def cycle_vehicle(s: GroundOpsState) -> Optional[GroundVehicle]:
    if not s.vehicles: return None
    s.selected_vehicle_index=(s.selected_vehicle_index+1)%len(s.vehicles); return s.selected_vehicle

def cycle_airfield(s: GroundOpsState) -> Optional[ExpeditionaryAirfield]:
    if not s.airfields: return None
    s.selected_airfield_index=(s.selected_airfield_index+1)%len(s.airfields); return s.selected_airfield

def cycle_mission(s: GroundOpsState) -> Optional[GroundMission]:
    if not s.missions: return None
    s.selected_mission_index=(s.selected_mission_index+1)%len(s.missions); return s.selected_mission


def accept_selected_mission(s: GroundOpsState) -> Tuple[bool,str]:
    m=s.selected_mission
    if not m: return False,"No ground mission selected."
    if s.active_mission and s.active_mission.status=="ACTIVE": return False,f"Ground mission already active: {s.active_mission.title}."
    if m.status=="COMPLETE": return False,"That ground mission is already complete."
    m.status="ACTIVE"; m.progress_minutes=0.0; s.active_mission_key=m.key
    msg=f"GROUND OPERATIONS ORDER ACCEPTED — {m.title}."
    s.last_event=msg; s.log.insert(0,msg); s.log=s.log[:50]
    return True,msg


def order_selected_unit_to_mission(s: GroundOpsState) -> Tuple[bool,str]:
    m=s.active_mission; u=s.selected_unit
    if not m: return False,"Accept a ground mission first."
    if not u: return False,"No ground unit selected."
    if u.strength_pct<=15: return False,f"{u.name} is combat ineffective."
    u.order=m.mission_type; u.target_east_nm=m.target_east_nm; u.target_north_nm=m.target_north_nm; u.status="MOVING"
    msg=f"{u.name} ordered toward {m.title}."
    s.last_event=msg; s.log.insert(0,msg)
    return True,msg


def order_selected_vehicle_to_mission(s: GroundOpsState) -> Tuple[bool,str]:
    m=s.active_mission; v=s.selected_vehicle
    if not m: return False,"Accept a ground mission first."
    if not v: return False,"No ground vehicle selected."
    if v.health_pct<=20 or v.fuel_pct<=3: return False,f"{v.name} is unavailable."
    v.order=m.mission_type; v.target_east_nm=m.target_east_nm; v.target_north_nm=m.target_north_nm; v.status="MOVING"
    msg=f"{v.name} dispatched toward {m.title}."
    s.last_event=msg; s.log.insert(0,msg)
    return True,msg


def launch_amphibious_group(s: GroundOpsState) -> Tuple[bool,str]:
    m=s.active_mission
    if not m or not m.amphibious_required: return False,"No active amphibious mission."
    group=next(iter(s.amphibious.values()),None)
    if not group: return False,"No amphibious group available."
    if group.craft_health_pct<=25 or group.embarked_strength<=10: return False,"Amphibious group is not fit to launch."
    group.target_east_nm=m.target_east_nm; group.target_north_nm=m.target_north_nm; group.status="APPROACHING"
    msg=f"{group.name} launched toward the training beachhead."
    s.last_event=msg; s.log.insert(0,msg)
    return True,msg


def service_selected_airfield(s: GroundOpsState, campaign=None) -> Tuple[bool,str]:
    a=s.selected_airfield
    if not a: return False,"No airfield selected."
    if campaign is not None:
        base = campaign.bases.get("HOME" if a.key=="HOME_AIR" else "FORWARD")
        if base:
            fuel=min(18.0,max(0.0,base.aviation_fuel)); ammo=min(15.0,max(0.0,base.ammunition)); repair=min(15.0,max(0.0,base.repair_stores)); med=min(8.0,max(0.0,base.medical))
            if fuel+ammo+repair+med<=0: return False,"Supporting naval base has no transferable airfield stores."
            base.aviation_fuel-=fuel; base.ammunition-=ammo; base.repair_stores-=repair; base.medical-=med
            a.aviation_fuel=min(100,a.aviation_fuel+fuel); a.ammunition=min(100,a.ammunition+ammo); a.repair_stores=min(100,a.repair_stores+repair); a.medical=min(100,a.medical+med)
    else:
        a.aviation_fuel=min(100,a.aviation_fuel+10); a.ammunition=min(100,a.ammunition+10); a.repair_stores=min(100,a.repair_stores+10)
    if a.repair_stores>10 and a.runway_condition<100:
        use=min(8.0,a.repair_stores,100-a.runway_condition); a.repair_stores-=use; a.runway_condition+=use
    s.airfield_services+=1
    msg=f"{a.name} serviced — readiness {a.readiness:.0f}%."
    s.last_event=msg; s.log.insert(0,msg)
    return True,msg


def add_air_support(s: GroundOpsState, points: float, source: str="carrier air wing") -> str:
    points=max(0.0,float(points)); s.air_support_points=min(100.0,s.air_support_points+points)
    msg=f"Ground operations received {points:.0f} air-support points from {source}."
    s.last_event=msg; s.log.insert(0,msg)
    return msg


def _move(e: float,n: float,te: float,tn: float,speed_knots: float,dt: float) -> Tuple[float,float,float]:
    brg,rng=_bearing_range(e,n,te,tn); dist=min(rng,max(0.0,speed_knots)*dt/3600.0); de,dn=_nav_vec(brg,dist); return e+de,n+dn,rng


def _mission_progress(s: GroundOpsState, dt: float) -> Optional[str]:
    m=s.active_mission
    if not m or m.status!="ACTIVE": return None
    nearby_units=[u for u in s.units.values() if u.strength_pct>20 and _bearing_range(u.east_nm,u.north_nm,m.target_east_nm,m.target_north_nm)[1]<=m.radius_nm]
    nearby_vehicles=[v for v in s.vehicles.values() if v.health_pct>20 and _bearing_range(v.east_nm,v.north_nm,m.target_east_nm,m.target_north_nm)[1]<=m.radius_nm]
    amphibious_ok=True
    if m.amphibious_required:
        amphibious_ok=any(g.status in ("BEACHHEAD","SECURED") and _bearing_range(g.east_nm,g.north_nm,m.target_east_nm,m.target_north_nm)[1]<=m.radius_nm for g in s.amphibious.values())
    air_ok=(not m.air_support_required) or s.air_support_points>=12.0
    presence=bool(nearby_units or nearby_vehicles)
    if presence and amphibious_ok and air_ok:
        m.progress_minutes += dt/60.0
        for u in nearby_units:
            u.fatigue_pct=_clamp(u.fatigue_pct+dt/240.0,0,100); u.supply_pct=_clamp(u.supply_pct-dt/1200.0,0,100); u.experience=_clamp(u.experience+dt/600.0,0,100)
        if m.progress_minutes>=m.required_minutes:
            m.status="COMPLETE"; s.missions_completed+=1; s.operational_score=min(100,s.operational_score+3); s.active_mission_key=""
            if m.amphibious_required: s.amphibious_landings+=1
            msg=f"GROUND MISSION COMPLETE — {m.title}."
            s.last_event=msg; s.log.insert(0,msg); return msg
    return None


def advance_ground_ops(s: GroundOpsState, dt: float, campaign=None) -> List[str]:
    msgs=[]; dt=max(0.0,float(dt)); s.operations_minutes+=dt/60.0
    for u in s.units.values():
        if u.status=="MOVING":
            u.east_nm,u.north_nm,rng=_move(u.east_nm,u.north_nm,u.target_east_nm,u.target_north_nm,u.speed_knots,dt)
            u.fatigue_pct=_clamp(u.fatigue_pct+dt/360.0,0,100); u.supply_pct=_clamp(u.supply_pct-dt/1800.0,0,100)
            if rng<=0.3: u.status="ON STATION"
        else:
            u.fatigue_pct=_clamp(u.fatigue_pct-dt/2400.0,0,100)
        if u.supply_pct<12: u.morale_pct=_clamp(u.morale_pct-dt/900.0,0,100)
    for v in s.vehicles.values():
        if v.status=="MOVING":
            v.east_nm,v.north_nm,rng=_move(v.east_nm,v.north_nm,v.target_east_nm,v.target_north_nm,14.0,dt)
            v.fuel_pct=_clamp(v.fuel_pct-dt/900.0,0,100)
            if v.fuel_pct<=0: v.status="OUT OF FUEL"
            elif rng<=0.4:
                v.status="ON STATION"
                if v.vehicle_type=="CARGO_TRUCK" and v.cargo_pct>0:
                    delivered=min(v.cargo_pct,30.0); v.cargo_pct-=delivered; s.supplies_delivered+=delivered
                    for u in s.units.values():
                        if _bearing_range(u.east_nm,u.north_nm,v.east_nm,v.north_nm)[1]<=3:
                            u.supply_pct=min(100,u.supply_pct+delivered*.5)
                    msgs.append(f"{v.name} delivered {delivered:.0f} ground supply points.")
    for g in s.amphibious.values():
        if g.status=="APPROACHING":
            g.east_nm,g.north_nm,rng=_move(g.east_nm,g.north_nm,g.target_east_nm,g.target_north_nm,g.speed_knots,dt)
            g.progress_pct=_clamp(100.0-rng*3.0,0,95)
            if rng<=0.45:
                g.status="BEACHHEAD"; g.progress_pct=100.0
                # Embarked training force appears on the beachhead.
                u=s.units.get("RIFLE_A")
                if u:
                    u.east_nm,u.north_nm=g.target_east_nm,g.target_north_nm; u.status="ON STATION"; u.order="SECURE BEACHHEAD"
                msgs.append(f"{g.name} established a training beachhead.")
    evt=_mission_progress(s,dt)
    if evt: msgs.append(evt)
    if s.air_support_points>0: s.air_support_points=max(0.0,s.air_support_points-dt/3600.0)
    if msgs:
        s.last_event=msgs[-1]
        for m in msgs: s.log.insert(0,m)
        s.log=s.log[:50]
    return msgs


def enter_training_vehicle(s: GroundOpsState, x: float, y: float) -> Tuple[bool,str]:
    d=s.drive
    if d.active: return False,"Already operating a ground vehicle."
    d.active=True; d.x=x; d.y=y; d.heading_deg=90.0; d.speed_mps=0; d.throttle=0; d.brake=True
    return True,"Entered base utility vehicle. I engine • W/S throttle • A/D steer • B brake • E exit."


def exit_training_vehicle(s: GroundOpsState) -> Tuple[bool,str]:
    d=s.drive
    if not d.active: return False,"Not in a ground vehicle."
    if abs(d.speed_mps)>0.5: return False,"Stop the vehicle before exiting."
    d.active=False; d.throttle=0; d.brake=True
    return True,"Exited base utility vehicle."


def toggle_drive_engine(s: GroundOpsState) -> str:
    d=s.drive
    if d.fuel_pct<=0 or d.health_pct<=10: return "Vehicle engine unavailable."
    d.engine_running=not d.engine_running
    if not d.engine_running: d.throttle=0
    return f"Ground vehicle engine {'RUNNING' if d.engine_running else 'SECURED'}."


def adjust_drive_throttle(s: GroundOpsState, delta: float) -> str:
    d=s.drive
    if not d.engine_running and delta>0: return "Start the vehicle engine first."
    d.throttle=_clamp(d.throttle+delta,-0.35,1.0); d.brake=False
    return f"Ground vehicle throttle {d.throttle*100:+.0f}%."


def advance_training_vehicle(s: GroundOpsState, dt: float, steer: float=0.0, brake: bool=False) -> Tuple[float,float,float]:
    d=s.drive
    if not d.active: return d.x,d.y,d.heading_deg
    target=(8.5*d.throttle if d.engine_running else 0.0)
    if brake or d.brake: target=0.0
    accel=3.4 if abs(target)>abs(d.speed_mps) else 5.5
    if d.speed_mps<target: d.speed_mps=min(target,d.speed_mps+accel*dt)
    elif d.speed_mps>target: d.speed_mps=max(target,d.speed_mps-accel*dt)
    if abs(d.speed_mps)>.15:
        d.heading_deg=(d.heading_deg+steer*72.0*dt*min(1.0,abs(d.speed_mps)/3.0)*(1 if d.speed_mps>=0 else -1))%360
    r=math.radians(d.heading_deg); nx=d.x+math.cos(r)*d.speed_mps*dt; ny=d.y+math.sin(r)*d.speed_mps*dt
    d.distance_m+=math.hypot(nx-d.x,ny-d.y); d.x,d.y=nx,ny
    if d.engine_running and abs(d.throttle)>.05: d.fuel_pct=_clamp(d.fuel_pct-dt*(.004+.006*abs(d.throttle)),0,100)
    if d.fuel_pct<=0: d.engine_running=False; d.throttle=0
    return d.x,d.y,d.heading_deg


def ground_summary(s: GroundOpsState) -> str:
    m=s.active_mission
    return (f"GROUND OPS • score {s.operational_score:.0f}% • missions {s.missions_completed}/{s.missions_failed} • "
            f"amphibious landings {s.amphibious_landings} • supplies {s.supplies_delivered:.0f} • air support {s.air_support_points:.0f}% • "
            f"active {m.title if m else 'NONE'}")


def unit_lines(s: GroundOpsState) -> List[str]:
    out=[]
    for u in s.units.values():
        brg,rng=_bearing_range(0,0,u.east_nm,u.north_nm)
        mark=">" if u is s.selected_unit else " "
        out.append(f"{mark} {u.name:<38} {u.unit_type:<11} STR {u.strength_pct:3.0f}% SUP {u.supply_pct:3.0f}% MOR {u.morale_pct:3.0f}% FAT {u.fatigue_pct:3.0f}% • E{u.east_nm:+.0f} N{u.north_nm:+.0f} • {u.status}")
    return out


def vehicle_lines(s: GroundOpsState) -> List[str]:
    out=[]
    for v in s.vehicles.values():
        mark=">" if v is s.selected_vehicle else " "
        out.append(f"{mark} {v.name:<32} {v.vehicle_type:<11} HLTH {v.health_pct:3.0f}% FUEL {v.fuel_pct:3.0f}% CARGO {v.cargo_pct:3.0f}% • E{v.east_nm:+.0f} N{v.north_nm:+.0f} • {v.status}")
    return out


def airfield_lines(s: GroundOpsState) -> List[str]:
    out=[]
    for a in s.airfields.values():
        mark=">" if a is s.selected_airfield else " "
        out.append(f"{mark} {a.name:<34} RDY {a.readiness:3.0f}% RUNWAY {a.runway_condition:3.0f}% AVFUEL {a.aviation_fuel:3.0f}% AMMO {a.ammunition:3.0f}% REPAIR {a.repair_stores:3.0f}% SEC {a.security_pct:3.0f}%")
    return out


def mission_lines(s: GroundOpsState) -> List[str]:
    out=[]
    for m in s.missions.values():
        mark=">" if m is s.selected_mission else " "
        out.append(f"{mark} {m.title:<38} {m.status:<9} {m.progress_minutes:5.1f}/{m.required_minutes:.0f} min • E{m.target_east_nm:+.0f} N{m.target_north_nm:+.0f} • {m.mission_type}")
    return out


def ground_ops_to_dict(s: GroundOpsState) -> dict:
    return asdict(s)


def ground_ops_from_dict(data: dict) -> GroundOpsState:
    if not data: return create_ground_ops()
    base=create_ground_ops()
    for k,v in data.items():
        if k in ("units","vehicles","airfields","amphibious","missions","drive","log"): continue
        if hasattr(base,k): setattr(base,k,v)
    for k,v in data.get("units",{}).items():
        if k in base.units:
            for fld,val in v.items():
                if hasattr(base.units[k],fld): setattr(base.units[k],fld,val)
        else: base.units[k]=GroundUnit(**v)
    for k,v in data.get("vehicles",{}).items():
        if k in base.vehicles:
            for fld,val in v.items():
                if hasattr(base.vehicles[k],fld): setattr(base.vehicles[k],fld,val)
        else: base.vehicles[k]=GroundVehicle(**v)
    for k,v in data.get("airfields",{}).items():
        if k in base.airfields:
            for fld,val in v.items():
                if hasattr(base.airfields[k],fld): setattr(base.airfields[k],fld,val)
        else: base.airfields[k]=ExpeditionaryAirfield(**v)
    for k,v in data.get("amphibious",{}).items():
        if k in base.amphibious:
            for fld,val in v.items():
                if hasattr(base.amphibious[k],fld): setattr(base.amphibious[k],fld,val)
        else: base.amphibious[k]=AmphibiousGroup(**v)
    for k,v in data.get("missions",{}).items():
        if k in base.missions:
            for fld,val in v.items():
                if hasattr(base.missions[k],fld): setattr(base.missions[k],fld,val)
        else: base.missions[k]=GroundMission(**v)
    if data.get("drive"):
        d=data["drive"]
        for fld,val in d.items():
            if hasattr(base.drive,fld): setattr(base.drive,fld,val)
    base.log=list(data.get("log",base.log))[:50]
    return base
