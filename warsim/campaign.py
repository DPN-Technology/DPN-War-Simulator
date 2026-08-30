from __future__ import annotations

"""War Simulator v1.4 persistent naval campaign / logistics network.

The base names, positions, stock quantities, convoy schedules, mission geometry and time-compression
rules in this module are TRAINING SIMULATION ABSTRACTIONS. They are deliberately separated from
the locked, sourced Battle of Midway historical scenario data.
"""

from dataclasses import dataclass, field, asdict
import math
from typing import Dict, List, Optional, Tuple


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _bearing_range(e0: float, n0: float, e1: float, n1: float) -> Tuple[float, float]:
    de, dn = e1-e0, n1-n0
    return math.degrees(math.atan2(de, dn)) % 360.0, math.hypot(de, dn)


def _nav_vec(direction_deg: float, magnitude: float) -> Tuple[float, float]:
    r = math.radians(direction_deg)
    return math.sin(r) * magnitude, math.cos(r) * magnitude


@dataclass
class NavalBase:
    key: str
    name: str
    east_nm: float
    north_nm: float
    fuel: float = 100.0
    aviation_fuel: float = 100.0
    ammunition: float = 100.0
    repair_stores: float = 100.0
    provisions: float = 100.0
    medical: float = 100.0
    repair_capacity: float = 1.0
    port_radius_nm: float = 2.0
    status: str = "OPERATIONAL"

    @property
    def readiness(self) -> float:
        return sum((self.fuel,self.aviation_fuel,self.ammunition,self.repair_stores,self.provisions,self.medical))/6.0


@dataclass
class SupplyConvoy:
    key: str
    name: str
    east_nm: float
    north_nm: float
    destination_key: str
    origin_key: str
    speed_knots: float = 10.0
    health_pct: float = 100.0
    fuel_cargo: float = 18.0
    aviation_cargo: float = 12.0
    ammo_cargo: float = 14.0
    repair_cargo: float = 12.0
    provision_cargo: float = 16.0
    medical_cargo: float = 8.0
    status: str = "EN ROUTE"
    escorted: bool = False
    deliveries: int = 0
    threat_exposure_s: float = 0.0


@dataclass
class CampaignMission:
    key: str
    title: str
    mission_type: str
    target_east_nm: float
    target_north_nm: float
    radius_nm: float
    required_minutes: float
    status: str = "AVAILABLE"
    progress_minutes: float = 0.0
    reward_xp: int = 35
    description: str = ""


@dataclass
class CampaignState:
    bases: Dict[str, NavalBase] = field(default_factory=dict)
    convoys: Dict[str, SupplyConvoy] = field(default_factory=dict)
    missions: Dict[str, CampaignMission] = field(default_factory=dict)
    selected_base_index: int = 0
    selected_convoy_index: int = 0
    selected_mission_index: int = 0
    active_mission_key: str = ""
    time_scale: float = 1.0
    campaign_hours: float = 0.0
    missions_completed: int = 0
    missions_failed: int = 0
    convoy_deliveries: int = 0
    convoy_losses: int = 0
    port_services: int = 0
    escort_repairs: int = 0
    supply_points_delivered: float = 0.0
    operational_score: float = 100.0
    log: List[str] = field(default_factory=list)

    @property
    def selected_base(self) -> Optional[NavalBase]:
        vals=list(self.bases.values())
        return vals[self.selected_base_index % len(vals)] if vals else None

    @property
    def selected_convoy(self) -> Optional[SupplyConvoy]:
        vals=list(self.convoys.values())
        return vals[self.selected_convoy_index % len(vals)] if vals else None

    @property
    def selected_mission(self) -> Optional[CampaignMission]:
        vals=list(self.missions.values())
        return vals[self.selected_mission_index % len(vals)] if vals else None

    @property
    def active_mission(self) -> Optional[CampaignMission]:
        return self.missions.get(self.active_mission_key) if self.active_mission_key else None


def create_campaign(flagship_e: float=0.0, flagship_n: float=0.0) -> CampaignState:
    s=CampaignState()
    # Training sea-room locations; not historical geography.
    s.bases={
        "HOME": NavalBase("HOME","Naval Training Base — Home Port",0.0,0.0,100,100,100,100,100,100,1.0,2.0),
        "FORWARD": NavalBase("FORWARD","Forward Operating Base Able",145.0,65.0,58,48,52,45,62,55,0.55,2.5),
        "FUEL": NavalBase("FUEL","Fleet Fuel Anchorage Baker",-95.0,120.0,92,72,38,42,55,48,0.35,2.5),
        "REPAIR": NavalBase("REPAIR","Fleet Repair Yard Charlie",-135.0,-80.0,70,48,60,95,68,88,1.35,3.0),
    }
    home=s.bases["HOME"]
    s.convoys={
        "CONVOY_A": SupplyConvoy("CONVOY_A","Supply Convoy A-1",home.east_nm+3,home.north_nm+2,"FORWARD","HOME"),
        "TANKER_B": SupplyConvoy("TANKER_B","Fleet Oiler Group B-1",home.east_nm-4,home.north_nm+1,"FUEL","HOME",speed_knots=12.0,fuel_cargo=24,aviation_cargo=18,ammo_cargo=5,repair_cargo=4,provision_cargo=5,medical_cargo=3),
    }
    s.missions={
        "PATROL": CampaignMission("PATROL","Patrol Sector Able","PATROL",68.0,38.0,12.0,25.0,reward_xp=35,description="Maintain presence inside the assigned patrol sector."),
        "ESCORT": CampaignMission("ESCORT","Escort Supply Convoy A-1","ESCORT",0.0,0.0,10.0,30.0,reward_xp=50,description="Remain within escort distance of Supply Convoy A-1 while it advances."),
        "FORWARD": CampaignMission("FORWARD","Forward Base Logistics Inspection","BASE_VISIT",145.0,65.0,3.0,8.0,reward_xp=45,description="Reach Forward Operating Base Able and remain on station for logistics inspection."),
        "REPAIR": CampaignMission("REPAIR","Fleet Repair Yard Readiness Visit","BASE_VISIT",-135.0,-80.0,3.5,8.0,reward_xp=45,description="Reach Fleet Repair Yard Charlie and inspect repair readiness."),
    }
    s.log.append("v1.4 persistent campaign initialized. Geography, schedules and stock quantities are training abstractions.")
    return s


def cycle_base(s: CampaignState) -> Optional[NavalBase]:
    if not s.bases: return None
    s.selected_base_index=(s.selected_base_index+1)%len(s.bases)
    return s.selected_base


def cycle_convoy(s: CampaignState) -> Optional[SupplyConvoy]:
    if not s.convoys: return None
    s.selected_convoy_index=(s.selected_convoy_index+1)%len(s.convoys)
    return s.selected_convoy


def cycle_mission(s: CampaignState) -> Optional[CampaignMission]:
    if not s.missions: return None
    s.selected_mission_index=(s.selected_mission_index+1)%len(s.missions)
    return s.selected_mission


def accept_selected_mission(s: CampaignState) -> Tuple[bool,str]:
    m=s.selected_mission
    if not m: return False,"No campaign mission selected."
    if s.active_mission and s.active_mission.status=="ACTIVE":
        return False,f"Mission already active: {s.active_mission.title}."
    if m.status=="COMPLETE": return False,"That mission is already complete."
    m.status="ACTIVE"; m.progress_minutes=0.0; s.active_mission_key=m.key
    s.log.insert(0,f"OPERATIONS ORDER: {m.title} accepted.")
    return True,f"Mission accepted: {m.title}."


def set_time_compression(s: CampaignState, scale: float) -> str:
    allowed=(1.0,5.0,15.0,30.0)
    s.time_scale=min(allowed,key=lambda x:abs(x-scale))
    return f"Operational navigation time compression set to {s.time_scale:.0f}×. Emergencies automatically force 1×."


def effective_time_scale(s: CampaignState, *, combat_active: bool=False, casualty_active: bool=False, collision_alarm: bool=False) -> float:
    if combat_active or casualty_active or collision_alarm:
        return 1.0
    return s.time_scale


def _move_toward(e: float,n: float,te: float,tn: float,speed_knots: float,dt: float) -> Tuple[float,float,float]:
    brg,rng=_bearing_range(e,n,te,tn)
    dist=min(rng,max(0.0,speed_knots)*dt/3600.0)
    de,dn=_nav_vec(brg,dist)
    return e+de,n+dn,rng


def _deliver_convoy(s: CampaignState, c: SupplyConvoy, dest: NavalBase) -> str:
    vals=(c.fuel_cargo,c.aviation_cargo,c.ammo_cargo,c.repair_cargo,c.provision_cargo,c.medical_cargo)
    dest.fuel=min(100.0,dest.fuel+c.fuel_cargo)
    dest.aviation_fuel=min(100.0,dest.aviation_fuel+c.aviation_cargo)
    dest.ammunition=min(100.0,dest.ammunition+c.ammo_cargo)
    dest.repair_stores=min(100.0,dest.repair_stores+c.repair_cargo)
    dest.provisions=min(100.0,dest.provisions+c.provision_cargo)
    dest.medical=min(100.0,dest.medical+c.medical_cargo)
    c.deliveries+=1; s.convoy_deliveries+=1; s.supply_points_delivered+=sum(vals)
    c.status="TURNAROUND"
    # Shuttle back to origin; refill cargo when it returns home.
    c.destination_key,c.origin_key=c.origin_key,c.destination_key
    return f"{c.name} delivered supplies to {dest.name}; base readiness now {dest.readiness:.0f}%."


def _advance_convoys(s: CampaignState, flagship_e: float, flagship_n: float, dt: float) -> List[str]:
    msgs=[]
    for c in s.convoys.values():
        if c.health_pct<=0: continue
        dest=s.bases[c.destination_key]
        c.east_nm,c.north_nm,old_rng=_move_toward(c.east_nm,c.north_nm,dest.east_nm,dest.north_nm,c.speed_knots,dt)
        _,new_rng=_bearing_range(c.east_nm,c.north_nm,dest.east_nm,dest.north_nm)
        _,escort_rng=_bearing_range(c.east_nm,c.north_nm,flagship_e,flagship_n)
        c.escorted=escort_rng<=12.0
        c.status="ESCORTED" if c.escorted else "EN ROUTE"
        # Deterministic training interdiction zone to make escort missions matter.
        hazard=math.hypot(c.east_nm-72.0,c.north_nm-34.0)<22.0
        if hazard and not c.escorted:
            c.threat_exposure_s+=dt
            while c.threat_exposure_s>=300.0 and c.health_pct>0:
                c.threat_exposure_s-=300.0; c.health_pct=max(0.0,c.health_pct-8.0)
                s.operational_score=max(0.0,s.operational_score-2.0)
                msgs.append(f"CONVOY WARNING — {c.name} takes simulated interdiction damage while unescorted; health {c.health_pct:.0f}%.")
                if c.health_pct<=0:
                    s.convoy_losses+=1; c.status="LOST"; msgs.append(f"SIMULATED CONVOY LOSS — {c.name} lost in the training sea room.")
        else:
            c.threat_exposure_s=max(0.0,c.threat_exposure_s-dt*.5)
        if new_rng<=1.0 and c.health_pct>0:
            msg=_deliver_convoy(s,c,dest); msgs.append(msg)
            # Home-port turnaround replenishes abstract cargo package and repairs convoy.
            if dest.key=="HOME": c.health_pct=min(100.0,c.health_pct+35.0)
    return msgs


def _advance_active_mission(s: CampaignState, flagship_e: float, flagship_n: float, dt: float) -> Optional[str]:
    m=s.active_mission
    if not m or m.status!="ACTIVE": return None
    if m.mission_type=="ESCORT":
        c=s.convoys.get("CONVOY_A")
        if not c or c.health_pct<=0:
            m.status="FAILED"; s.active_mission_key=""; s.missions_failed+=1; s.operational_score=max(0,s.operational_score-12)
            return f"MISSION FAILED — {m.title}: convoy unavailable."
        _,rng=_bearing_range(flagship_e,flagship_n,c.east_nm,c.north_nm)
        inside=rng<=m.radius_nm
    else:
        _,rng=_bearing_range(flagship_e,flagship_n,m.target_east_nm,m.target_north_nm)
        inside=rng<=m.radius_nm
    if inside:
        m.progress_minutes+=dt/60.0
    else:
        m.progress_minutes=max(0.0,m.progress_minutes-dt/180.0)
    if m.progress_minutes>=m.required_minutes:
        m.status="COMPLETE"; s.active_mission_key=""; s.missions_completed+=1
        s.operational_score=min(100.0,s.operational_score+4.0)
        return f"MISSION COMPLETE — {m.title}."
    return None


def request_port_service(s: CampaignState, task_force, physics, survivability=None) -> Tuple[bool,str]:
    b=s.selected_base
    if not b: return False,"No base selected."
    _,rng=_bearing_range(physics.east_nm,physics.north_nm,b.east_nm,b.north_nm)
    if rng>b.port_radius_nm: return False,f"Enterprise is {rng:.1f} nm from {b.name}; enter the port service radius first."
    if abs(physics.speed_knots)>1.0: return False,"Port service denied — reduce ship speed to 1 knot or less."
    # Draw finite base stocks into task-force/ship stores.
    fuel=min(22.0,b.fuel); av=min(18.0,b.aviation_fuel); ammo=min(18.0,b.ammunition); repair=min(15.0,b.repair_stores)
    b.fuel-=fuel; b.aviation_fuel-=av; b.ammunition-=ammo; b.repair_stores-=repair
    task_force.logistics.bunker_fuel_pct=min(100.0,task_force.logistics.bunker_fuel_pct+fuel)
    task_force.logistics.aviation_fuel_pct=min(100.0,task_force.logistics.aviation_fuel_pct+av)
    task_force.logistics.ammunition_pct=min(100.0,task_force.logistics.ammunition_pct+ammo)
    task_force.logistics.repair_stores_pct=min(100.0,task_force.logistics.repair_stores_pct+repair)
    physics.hull_integrity=min(100.0,physics.hull_integrity+repair*.35*b.repair_capacity)
    if survivability is not None:
        survivability.structural_strength_pct=min(100.0,survivability.structural_strength_pct+repair*.22*b.repair_capacity)
    s.port_services+=1
    msg=f"Port service complete at {b.name}: fuel/ammunition/repair stocks transferred from finite base inventory."
    s.log.insert(0,msg); return True,msg


def dispatch_selected_for_repair(s: CampaignState, task_force) -> Tuple[bool,str]:
    v=task_force.selected_friendly
    b=s.selected_base
    if not v or not b: return False,"Select a friendly ship and repair base first."
    if b.repair_capacity<0.8: return False,f"{b.name} lacks heavy repair capacity. Select Fleet Repair Yard Charlie."
    if v.hull_pct>=99 and v.propulsion_pct>=99 and v.steering_pct>=99: return False,f"{v.name} does not require repair."
    brg,_=_bearing_range(v.east_nm,v.north_nm,b.east_nm,b.north_nm)
    v.detached=True; v.heading_deg=brg; v.speed_knots=min(18.0,v.max_speed_knots*.6); v.status=f"ROUTING TO {b.key} REPAIR"; v.last_order=f"Proceed {b.name} for repair"
    # Store lightweight repair destination dynamically; dataclass serialization keeps it only if field exists,
    # so use campaign log/ship key map encoded in mission-like dictionary on CampaignState via attribute below.
    v.repair_destination=b.key
    s.log.insert(0,f"REPAIR ORDER: {v.name} detached to {b.name}.")
    return True,f"{v.name} ordered to {b.name} for repairs."


def _advance_repairs(s: CampaignState, task_force, dt: float) -> List[str]:
    msgs=[]
    for v in task_force.friendly.values():
        # Persisted v1.3 vessels won't have this dynamic attribute after reload; last_order is the stable fallback.
        dest_key=v.repair_destination
        if not dest_key and "Proceed " in v.last_order and "repair" in v.last_order.lower():
            for key,b in s.bases.items():
                if b.name in v.last_order: dest_key=key; break
        if not dest_key or dest_key not in s.bases: continue
        b=s.bases[dest_key]
        brg,rng=_bearing_range(v.east_nm,v.north_nm,b.east_nm,b.north_nm)
        if rng>1.5:
            v.heading_deg=brg; v.speed_knots=min(18.0,v.max_speed_knots*.6); v.detached=True
            continue
        v.speed_knots=max(0.0,v.speed_knots-dt*0.8); v.status="IN REPAIR"
        if b.repair_stores<=0.1: continue
        rate=.025*b.repair_capacity*dt
        before=v.hull_pct
        v.hull_pct=min(100.0,v.hull_pct+rate); v.propulsion_pct=min(100.0,v.propulsion_pct+rate*.85); v.steering_pct=min(100.0,v.steering_pct+rate*.9); v.sensor_pct=min(100.0,v.sensor_pct+rate*.7)
        used=max(0.0,v.hull_pct-before)*.12; b.repair_stores=max(0.0,b.repair_stores-used)
        if min(v.hull_pct,v.propulsion_pct,v.steering_pct)>=99.0:
            v.detached=False; v.status="RETURNING TO FORMATION"; v.last_order=f"Resume {task_force.formation} station"
            v.repair_destination=""
            s.escort_repairs+=1; msgs.append(f"REPAIR COMPLETE — {v.name} released from {b.name} and returning to formation.")
    return msgs


def advance_campaign(s: CampaignState, physics, task_force, dt: float) -> List[str]:
    msgs=[]
    s.campaign_hours+=dt/3600.0
    msgs.extend(_advance_convoys(s,physics.east_nm,physics.north_nm,dt))
    msgs.extend(_advance_repairs(s,task_force,dt))
    m=_advance_active_mission(s,physics.east_nm,physics.north_nm,dt)
    if m: msgs.append(m)
    # Operational attrition: task-force stores decline slowly with steaming and aircraft/crew operations.
    burn=max(0.0,physics.speed_knots)/30.0*0.0009*dt
    task_force.logistics.bunker_fuel_pct=max(0.0,task_force.logistics.bunker_fuel_pct-burn)
    task_force.logistics.food_pct=max(0.0,task_force.logistics.food_pct-0.00018*dt)
    if task_force.logistics.bunker_fuel_pct<8.0:
        s.operational_score=max(0.0,s.operational_score-0.002*dt)
    s.log=[*msgs[::-1],*s.log][:220]
    return msgs


def campaign_summary(s: CampaignState, physics=None) -> str:
    active=s.active_mission.title if s.active_mission else "No active mission"
    nearest=""
    if physics and s.bases:
        b=min(s.bases.values(),key=lambda x:math.hypot(x.east_nm-physics.east_nm,x.north_nm-physics.north_nm))
        _,rng=_bearing_range(physics.east_nm,physics.north_nm,b.east_nm,b.north_nm); nearest=f" • nearest base {b.key} {rng:.0f}nm"
    return f"CAMPAIGN D+{s.campaign_hours/24.0:.1f} • {active} • score {s.operational_score:.0f}% • deliveries {s.convoy_deliveries}{nearest} • nav {s.time_scale:.0f}×"


def base_lines(s: CampaignState, e: float, n: float) -> List[str]:
    out=[]
    for b in s.bases.values():
        brg,rng=_bearing_range(e,n,b.east_nm,b.north_nm)
        out.append(f"{b.key:<8} {b.name:<34} BRG {brg:03.0f}° {rng:6.1f}nm  readiness {b.readiness:3.0f}%  fuel {b.fuel:3.0f}% ammo {b.ammunition:3.0f}% repair {b.repair_stores:3.0f}%")
    return out


def convoy_lines(s: CampaignState, e: float, n: float) -> List[str]:
    out=[]
    for c in s.convoys.values():
        brg,rng=_bearing_range(e,n,c.east_nm,c.north_nm)
        out.append(f"{c.name:<24} BRG {brg:03.0f}° {rng:6.1f}nm  {c.status:<10} health {c.health_pct:3.0f}% → {c.destination_key}")
    return out


def mission_lines(s: CampaignState) -> List[str]:
    return [f"{m.key:<8} {m.title:<36} {m.status:<9} {m.progress_minutes:5.1f}/{m.required_minutes:.0f} min • {m.description}" for m in s.missions.values()]


def campaign_to_dict(s: CampaignState) -> dict:
    return asdict(s)


def campaign_from_dict(data: dict, flagship_e: float=0.0, flagship_n: float=0.0) -> CampaignState:
    base=create_campaign(flagship_e,flagship_n)
    if not isinstance(data,dict) or not data: return base
    for k,v in data.items():
        if k in ("bases","convoys","missions"): continue
        if hasattr(base,k): setattr(base,k,v)
    raw_b=data.get("bases",{})
    if isinstance(raw_b,dict):
        for k,raw in raw_b.items():
            if isinstance(raw,dict):
                vals={a:b for a,b in raw.items() if a in NavalBase.__dataclass_fields__}
                try: base.bases[k]=NavalBase(**vals)
                except TypeError: pass
    raw_c=data.get("convoys",{})
    if isinstance(raw_c,dict):
        base.convoys={}
        for k,raw in raw_c.items():
            if isinstance(raw,dict):
                vals={a:b for a,b in raw.items() if a in SupplyConvoy.__dataclass_fields__}
                try: base.convoys[k]=SupplyConvoy(**vals)
                except TypeError: pass
    raw_m=data.get("missions",{})
    if isinstance(raw_m,dict):
        for k,raw in raw_m.items():
            if isinstance(raw,dict):
                vals={a:b for a,b in raw.items() if a in CampaignMission.__dataclass_fields__}
                try: base.missions[k]=CampaignMission(**vals)
                except TypeError: pass
    return base
