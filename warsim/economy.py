from __future__ import annotations

"""v2.3 national war economy / industrial production simulation.

All facility names, production rates, stock quantities, research timings and training throughput
are GAME/TRAINING abstractions. They are deliberately separated from the locked historical
scenario layer. The purpose is to make long-war logistics, production and replacement capacity
matter to the existing naval, air and land simulation systems.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


@dataclass
class IndustrialFacility:
    key: str
    name: str
    kind: str
    x: float
    y: float
    capacity: float = 100.0
    efficiency: float = 80.0
    damage: float = 0.0
    power: float = 100.0
    workforce: int = 1000
    workforce_required: int = 900
    status: str = "OPERATING"
    queue_key: str = ""
    maintenance: float = 85.0
    output_total: float = 0.0

    @property
    def effective_capacity(self) -> float:
        workforce_factor = min(1.0, self.workforce / max(1, self.workforce_required))
        damage_factor = max(0.05, 1.0 - self.damage / 100.0)
        return self.capacity * (self.efficiency / 100.0) * (self.power / 100.0) * workforce_factor * damage_factor


@dataclass
class ProductionOrder:
    key: str
    title: str
    product: str
    facility_kind: str
    target_quantity: float
    unit_minutes: float
    steel: float = 0.0
    aluminum: float = 0.0
    oil: float = 0.0
    explosives: float = 0.0
    food: float = 0.0
    status: str = "AVAILABLE"
    produced: float = 0.0
    progress_minutes: float = 0.0
    priority: int = 2


@dataclass
class ResearchProject:
    key: str
    title: str
    field: str
    cost: float
    progress: float = 0.0
    status: str = "AVAILABLE"
    level: int = 0
    effect: str = ""


@dataclass
class TrainingPipeline:
    key: str
    title: str
    specialty: str
    cycle_minutes: float
    class_size: int
    progress_minutes: float = 0.0
    graduates: int = 0
    status: str = "ACTIVE"


@dataclass
class TransportNetwork:
    rail_capacity: float = 100.0
    road_capacity: float = 100.0
    port_capacity: float = 100.0
    merchant_shipping: float = 100.0
    rail_damage: float = 0.0
    road_damage: float = 0.0
    port_damage: float = 0.0
    deliveries: int = 0

    @property
    def throughput(self) -> float:
        vals = [
            self.rail_capacity * (1.0-self.rail_damage/100.0),
            self.road_capacity * (1.0-self.road_damage/100.0),
            self.port_capacity * (1.0-self.port_damage/100.0),
            self.merchant_shipping,
        ]
        return _clamp(sum(vals)/len(vals),0,100)


@dataclass
class WarEconomyState:
    active: bool = False
    elapsed_min: float = 0.0
    day: int = 1
    hour: float = 6.0
    reserves: Dict[str, float] = field(default_factory=dict)
    stockpiles: Dict[str, float] = field(default_factory=dict)
    facilities: Dict[str, IndustrialFacility] = field(default_factory=dict)
    orders: Dict[str, ProductionOrder] = field(default_factory=dict)
    research: Dict[str, ResearchProject] = field(default_factory=dict)
    training: Dict[str, TrainingPipeline] = field(default_factory=dict)
    network: TransportNetwork = field(default_factory=TransportNetwork)
    selected_facility_index: int = 0
    selected_order_index: int = 0
    selected_research_index: int = 0
    selected_training_index: int = 0
    selected_allocation: str = "THEATER"
    research_points: float = 120.0
    political_capital: float = 100.0
    industrial_score: float = 82.0
    production_units: float = 0.0
    orders_completed: int = 0
    allocations: int = 0
    facilities_repaired: int = 0
    research_completed: int = 0
    personnel_graduated: int = 0
    infrastructure_repairs: int = 0
    industrial_damage_events: int = 0
    last_event: str = "v2.3 national war economy initialized."
    log: List[str] = field(default_factory=list)

    @property
    def selected_facility(self) -> Optional[IndustrialFacility]:
        vals=list(self.facilities.values())
        return vals[self.selected_facility_index % len(vals)] if vals else None

    @property
    def selected_order(self) -> Optional[ProductionOrder]:
        vals=list(self.orders.values())
        return vals[self.selected_order_index % len(vals)] if vals else None

    @property
    def selected_research(self) -> Optional[ResearchProject]:
        vals=list(self.research.values())
        return vals[self.selected_research_index % len(vals)] if vals else None

    @property
    def selected_training(self) -> Optional[TrainingPipeline]:
        vals=list(self.training.values())
        return vals[self.selected_training_index % len(vals)] if vals else None


def create_war_economy() -> WarEconomyState:
    s=WarEconomyState()
    s.reserves={"STEEL":720.0,"ALUMINUM":460.0,"OIL":820.0,"EXPLOSIVES":390.0,"FOOD":760.0,"POWER":100.0}
    s.stockpiles={
        "FIGHTER_AIRFRAME":4.0,"BOMBER_AIRFRAME":4.0,"TANK":6.0,"TRUCK":10.0,
        "NAVAL_AMMO":120.0,"ARTILLERY_SHELLS":180.0,"SMALL_ARMS_AMMO":220.0,
        "REPAIR_STORES":120.0,"AVIATION_FUEL":180.0,"BUNKER_FUEL":240.0,
        "MEDICAL_STORES":100.0,"TRAINED_PERSONNEL":420.0,
    }
    s.facilities={
        "AIR":IndustrialFacility("AIR","Central Aircraft Works","AIRCRAFT",12,258,capacity=100,efficiency=82,workforce=1800,workforce_required=1600),
        "ARMOR":IndustrialFacility("ARMOR","Armored Vehicle Plant","VEHICLE",31,258,capacity=92,efficiency=80,workforce=1500,workforce_required=1400),
        "MUNITIONS":IndustrialFacility("MUNITIONS","National Munitions Complex","MUNITIONS",50,258,capacity=110,efficiency=86,workforce=2100,workforce_required=1800),
        "SHIPYARD":IndustrialFacility("SHIPYARD","Fleet Shipyard & Repair Basin","SHIPYARD",12,278,capacity=95,efficiency=84,workforce=2400,workforce_required=2200),
        "REFINERY":IndustrialFacility("REFINERY","Strategic Fuel Refinery","REFINERY",31,278,capacity=105,efficiency=85,workforce=1300,workforce_required=1200),
        "TRAINING":IndustrialFacility("TRAINING","National Training Command","TRAINING",50,278,capacity=90,efficiency=88,workforce=900,workforce_required=850),
        "RAIL":IndustrialFacility("RAIL","Rail / Port Logistics Directorate","LOGISTICS",31,298,capacity=100,efficiency=86,workforce=1100,workforce_required=1000),
    }
    s.orders={
        "P-FIGHTER":ProductionOrder("P-FIGHTER","Produce Fighter Airframes","FIGHTER_AIRFRAME","AIRCRAFT",6,180,steel=7,aluminum=12,oil=4),
        "P-BOMBER":ProductionOrder("P-BOMBER","Produce Attack/Scout Airframes","BOMBER_AIRFRAME","AIRCRAFT",6,220,steel=9,aluminum=15,oil=5),
        "P-TANK":ProductionOrder("P-TANK","Produce Armored Vehicles","TANK","VEHICLE",8,240,steel=22,oil=7),
        "P-TRUCK":ProductionOrder("P-TRUCK","Produce Logistics Trucks","TRUCK","VEHICLE",12,120,steel=9,oil=4),
        "P-NAVAMMO":ProductionOrder("P-NAVAMMO","Produce Naval Ammunition","NAVAL_AMMO","MUNITIONS",120,18,steel=.7,explosives=.8),
        "P-ARTY":ProductionOrder("P-ARTY","Produce Artillery Shells","ARTILLERY_SHELLS","MUNITIONS",180,12,steel=.45,explosives=.55),
        "P-SMALL":ProductionOrder("P-SMALL","Produce Small-Arms Ammunition","SMALL_ARMS_AMMO","MUNITIONS",240,7,steel=.18,explosives=.22),
        "P-REPAIR":ProductionOrder("P-REPAIR","Produce Repair Stores","REPAIR_STORES","SHIPYARD",100,15,steel=.7,oil=.25),
        "P-AVFUEL":ProductionOrder("P-AVFUEL","Refine Aviation Fuel","AVIATION_FUEL","REFINERY",160,8,oil=1.2),
        "P-BUNKER":ProductionOrder("P-BUNKER","Refine Bunker Fuel","BUNKER_FUEL","REFINERY",220,6,oil=1.4),
        "P-MED":ProductionOrder("P-MED","Produce Medical Stores","MEDICAL_STORES","MUNITIONS",80,15,food=.35,oil=.15),
    }
    s.research={
        "R-PROD":ResearchProject("R-PROD","Industrial Methods Improvement","PRODUCTION",80,effect="+8% factory efficiency"),
        "R-LOG":ResearchProject("R-LOG","Rail/Port Throughput Program","LOGISTICS",70,effect="+10% transport capacity"),
        "R-REPAIR":ResearchProject("R-REPAIR","Battle-Damage Repair Methods","REPAIR",75,effect="+10% repair output"),
        "R-TRAIN":ResearchProject("R-TRAIN","Accelerated Training Doctrine","TRAINING",65,effect="+15% training throughput"),
    }
    s.training={
        "T-GENERAL":TrainingPipeline("T-GENERAL","General Replacement Training","GENERAL",240,80),
        "T-PILOT":TrainingPipeline("T-PILOT","Pilot Replacement Pipeline","PILOT",360,16),
        "T-TECH":TrainingPipeline("T-TECH","Technical Specialist Pipeline","TECHNICAL",300,32),
    }
    s.log=[s.last_event]
    return s


def begin_war_economy(s: WarEconomyState) -> Tuple[bool,str]:
    if s.active: return False,"National war economy is already active."
    s.active=True
    s.last_event="WAR ECONOMY ACTIVE — production, training, infrastructure and strategic reserves are now advancing continuously."
    s.log.insert(0,s.last_event)
    return True,s.last_event


def cycle_facility(s: WarEconomyState):
    if not s.facilities: return None
    s.selected_facility_index=(s.selected_facility_index+1)%len(s.facilities); return s.selected_facility


def cycle_order(s: WarEconomyState):
    if not s.orders: return None
    s.selected_order_index=(s.selected_order_index+1)%len(s.orders); return s.selected_order


def cycle_research(s: WarEconomyState):
    if not s.research: return None
    s.selected_research_index=(s.selected_research_index+1)%len(s.research); return s.selected_research


def cycle_training(s: WarEconomyState):
    if not s.training: return None
    s.selected_training_index=(s.selected_training_index+1)%len(s.training); return s.selected_training


def cycle_allocation(s: WarEconomyState) -> str:
    vals=("THEATER","NAVY","AIR","LAND","BASES")
    i=vals.index(s.selected_allocation) if s.selected_allocation in vals else 0
    s.selected_allocation=vals[(i+1)%len(vals)]
    return s.selected_allocation


def start_selected_order(s: WarEconomyState) -> Tuple[bool,str]:
    o=s.selected_order
    if not o: return False,"No production order selected."
    if o.status=="ACTIVE": return False,"Selected production order is already active."
    if o.status=="COMPLETE":
        o.status="AVAILABLE"; o.produced=0; o.progress_minutes=0
    facilities=[f for f in s.facilities.values() if f.kind==o.facility_kind and f.damage<90]
    if not facilities: return False,"No usable facility can execute the selected production order."
    # Only one order at a time per facility kind; activating this order pauses a competing one.
    for other in s.orders.values():
        if other.facility_kind==o.facility_kind and other.status=="ACTIVE": other.status="PAUSED"
    o.status="ACTIVE"
    facilities[0].queue_key=o.key
    msg=f"PRODUCTION ORDER ACTIVE — {o.title}."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def toggle_selected_training(s: WarEconomyState) -> Tuple[bool,str]:
    p=s.selected_training
    if not p: return False,"No training pipeline selected."
    p.status="PAUSED" if p.status=="ACTIVE" else "ACTIVE"
    msg=f"TRAINING PIPELINE — {p.title}: {p.status}."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def start_selected_research(s: WarEconomyState) -> Tuple[bool,str]:
    p=s.selected_research
    if not p: return False,"No research project selected."
    if p.status=="COMPLETE": return False,"Selected research project is already complete."
    if p.status=="ACTIVE": return False,"Selected research project is already active."
    if s.research_points < 10: return False,"Insufficient research capacity to start a new project."
    for q in s.research.values():
        if q.status=="ACTIVE": q.status="PAUSED"
    p.status="ACTIVE"
    msg=f"RESEARCH PRIORITY — {p.title}."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def repair_selected_facility(s: WarEconomyState) -> Tuple[bool,str]:
    f=s.selected_facility
    if not f: return False,"No industrial facility selected."
    if f.damage<=0.1: return False,"Selected facility does not require repair."
    if s.stockpiles.get("REPAIR_STORES",0)<12: return False,"National repair-store stockpile is too low."
    s.stockpiles["REPAIR_STORES"]-=12
    f.damage=max(0.0,f.damage-35.0); f.maintenance=_clamp(f.maintenance+15,0,100)
    f.status="OPERATING" if f.damage<75 else "CRIPPLED"
    s.facilities_repaired+=1
    msg=f"INDUSTRIAL REPAIR — {f.name} damage reduced to {f.damage:.0f}%."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def repair_transport_network(s: WarEconomyState) -> Tuple[bool,str]:
    if s.stockpiles.get("REPAIR_STORES",0)<10: return False,"Insufficient repair stores for infrastructure restoration."
    n=s.network
    worst=max(("RAIL",n.rail_damage),("ROAD",n.road_damage),("PORT",n.port_damage),key=lambda x:x[1])
    if worst[1]<=0.1: return False,"Transport network has no significant damage."
    s.stockpiles["REPAIR_STORES"]-=10
    if worst[0]=="RAIL": n.rail_damage=max(0,n.rail_damage-30)
    elif worst[0]=="ROAD": n.road_damage=max(0,n.road_damage-30)
    else: n.port_damage=max(0,n.port_damage-30)
    s.infrastructure_repairs+=1
    msg=f"INFRASTRUCTURE REPAIR — {worst[0]} network restored; national throughput {n.throughput:.0f}%."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def _consume_for_unit(s: WarEconomyState, o: ProductionOrder, units: float) -> bool:
    costs={"STEEL":o.steel,"ALUMINUM":o.aluminum,"OIL":o.oil,"EXPLOSIVES":o.explosives,"FOOD":o.food}
    for key,c in costs.items():
        if c>0 and s.reserves.get(key,0) < c*units: return False
    for key,c in costs.items():
        if c>0: s.reserves[key]=max(0.0,s.reserves.get(key,0)-c*units)
    return True


def _advance_production(s: WarEconomyState, dt_min: float) -> List[str]:
    msgs=[]
    by_kind={}
    for f in s.facilities.values(): by_kind.setdefault(f.kind,[]).append(f)
    for o in s.orders.values():
        if o.status!="ACTIVE": continue
        fs=by_kind.get(o.facility_kind,[])
        if not fs: continue
        f=max(fs,key=lambda q:q.effective_capacity)
        if f.damage>=90 or f.power<20:
            f.status="OFFLINE"; continue
        f.status="OPERATING"
        # 100 effective capacity means baseline order time; transport throughput influences material feed.
        speed=max(.05,f.effective_capacity/100.0) * max(.25,s.network.throughput/100.0)
        o.progress_minutes += dt_min*speed
        while o.progress_minutes >= o.unit_minutes and o.produced < o.target_quantity:
            if not _consume_for_unit(s,o,1.0):
                o.status="MATERIAL HOLD"; msgs.append(f"MATERIAL HOLD — {o.title}; strategic raw reserves insufficient."); break
            o.progress_minutes -= o.unit_minutes; o.produced += 1.0; f.output_total += 1.0; s.production_units += 1.0
            s.stockpiles[o.product]=s.stockpiles.get(o.product,0.0)+1.0
        if o.produced>=o.target_quantity:
            o.status="COMPLETE"; f.queue_key=""; s.orders_completed+=1
            msgs.append(f"PRODUCTION COMPLETE — {o.title}: {o.produced:.0f} units delivered to national stockpile.")
    return msgs


def _advance_research(s: WarEconomyState, dt_min: float) -> List[str]:
    msgs=[]
    for p in s.research.values():
        if p.status!="ACTIVE": continue
        rate=.04*dt_min
        p.progress=_clamp(p.progress+rate,0,100)
        if p.progress>=100:
            p.status="COMPLETE"; p.level+=1; s.research_completed+=1
            if p.field=="PRODUCTION":
                for f in s.facilities.values(): f.efficiency=_clamp(f.efficiency+8,0,100)
            elif p.field=="LOGISTICS":
                s.network.rail_capacity=_clamp(s.network.rail_capacity+10,0,100); s.network.port_capacity=_clamp(s.network.port_capacity+10,0,100)
            elif p.field=="REPAIR":
                ship=s.facilities.get("SHIPYARD")
                if ship: ship.efficiency=_clamp(ship.efficiency+10,0,100)
            elif p.field=="TRAINING":
                train=s.facilities.get("TRAINING")
                if train: train.efficiency=_clamp(train.efficiency+12,0,100)
            msgs.append(f"RESEARCH COMPLETE — {p.title}: {p.effect}.")
    return msgs


def _advance_training(s: WarEconomyState, dt_min: float) -> List[str]:
    msgs=[]; f=s.facilities.get("TRAINING")
    mult=(f.effective_capacity/100.0 if f else 1.0)
    for p in s.training.values():
        if p.status!="ACTIVE": continue
        p.progress_minutes += dt_min*max(.1,mult)
        if p.progress_minutes>=p.cycle_minutes:
            cycles=int(p.progress_minutes//p.cycle_minutes); p.progress_minutes-=cycles*p.cycle_minutes
            grads=cycles*p.class_size; p.graduates+=grads; s.personnel_graduated+=grads
            s.stockpiles["TRAINED_PERSONNEL"]=s.stockpiles.get("TRAINED_PERSONNEL",0)+grads
            msgs.append(f"TRAINING CLASS GRADUATED — {p.title}: {grads} replacement personnel available.")
    return msgs


def _strategic_consumption(s: WarEconomyState, strategic_war, dt_min: float) -> None:
    if strategic_war is None or not getattr(strategic_war,'active',False): return
    formations=[f for f in getattr(strategic_war,'formations',{}).values() if getattr(f,'side','')=='FRIENDLY']
    tempo=sum(1.4 if f.order=='ATTACK' else .7 if f.order in ('DEFEND','RECON') else .35 for f in formations)
    s.stockpiles['BUNKER_FUEL']=max(0,s.stockpiles.get('BUNKER_FUEL',0)-dt_min*.0025*tempo)
    s.stockpiles['SMALL_ARMS_AMMO']=max(0,s.stockpiles.get('SMALL_ARMS_AMMO',0)-dt_min*.0018*tempo)
    # Industrial score drops if war consumption outruns stocks.
    shortages=sum(1 for k in ('BUNKER_FUEL','SMALL_ARMS_AMMO','REPAIR_STORES','TRAINED_PERSONNEL') if s.stockpiles.get(k,0)<15)
    if shortages: s.industrial_score=_clamp(s.industrial_score-dt_min*.003*shortages,0,100)


def _industrial_threat(s: WarEconomyState, strategic_war, dt_min: float=2.0) -> List[str]:
    msgs=[]
    if strategic_war is None or not getattr(strategic_war,'active',False): return msgs
    # Deterministic training interdiction every 12 operational hours if enemy retains high-value sectors.
    hour_index=int(s.elapsed_min//720)
    prev=int(max(0.0,s.elapsed_min-dt_min)//720)
    if hour_index<=0 or hour_index==prev: return msgs
    enemy_hold=sum(sec.value for sec in getattr(strategic_war,'sectors',{}).values() if sec.owner=='ENEMY')
    if enemy_hold>=25:
        fs=list(s.facilities.values()); f=fs[hour_index%len(fs)]
        dmg=6+min(12,enemy_hold*.15); f.damage=_clamp(f.damage+dmg,0,100); s.industrial_damage_events+=1
        s.network.rail_damage=_clamp(s.network.rail_damage+4,0,100)
        msgs.append(f"SIMULATED STRATEGIC INTERDICTION — {f.name} took {dmg:.0f}% industrial damage; rail throughput degraded.")
    return msgs


def allocate_stockpiles(s: WarEconomyState, strategic_war=None, campaign=None, air_wing=None, land_warfare=None, task_force=None, logistics_network=None) -> Tuple[bool,str]:
    if logistics_network is not None and getattr(logistics_network, "active", False):
        return False,"DIRECT ALLOCATION DISABLED — v2.4 strategic logistics is active. Dispatch cargo through the F5 Strategic Mobility network so it must physically reach its recipient."
    dest=s.selected_allocation
    if s.network.throughput<25: return False,"National transport throughput is too degraded for allocation."
    if dest=='THEATER':
        if strategic_war is None: return False,"Theater strategic layer unavailable."
        depots=[d for d in strategic_war.depots.values() if d.side=='FRIENDLY']
        if not depots: return False,"No friendly theater depot available."
        d=min(depots,key=lambda q:(q.fuel+q.ammunition+q.medical+q.repair)/4)
        need={'BUNKER_FUEL':12,'SMALL_ARMS_AMMO':12,'MEDICAL_STORES':8,'REPAIR_STORES':8,'TRAINED_PERSONNEL':60}
        if any(s.stockpiles.get(k,0)<v for k,v in need.items()): return False,"National stockpiles are insufficient for a theater allocation package."
        for k,v in need.items(): s.stockpiles[k]-=v
        d.fuel=_clamp(d.fuel+12,0,100); d.ammunition=_clamp(d.ammunition+12,0,100); d.medical=_clamp(d.medical+8,0,100); d.repair=_clamp(d.repair+8,0,100); d.replacements+=60
        msg=f"WAR ECONOMY ALLOCATION — theater package delivered to {d.name}."
    elif dest=='AIR':
        if air_wing is None: return False,"Air Group unavailable."
        if s.stockpiles.get('AVIATION_FUEL',0)<20 or s.stockpiles.get('FIGHTER_AIRFRAME',0)<1: return False,"Air allocation requires aviation fuel and at least one replacement airframe."
        s.stockpiles['AVIATION_FUEL']-=20; s.stockpiles['FIGHTER_AIRFRAME']-=1
        air_wing.aviation_fuel_units+=800; air_wing.spare_parts+=90
        lost=[a for a in air_wing.aircraft.values() if a.status=='LOST']
        if lost:
            a=lost[0]; a.status='MAINTENANCE'; a.condition=72; a.fuel_pct=100; a.deck='HANGAR'; air_wing.aircraft_lost=max(0,air_wing.aircraft_lost-1)
        msg="WAR ECONOMY ALLOCATION — replacement airframe, aviation fuel and spares delivered to Carrier Air Group."
    elif dest=='LAND':
        if land_warfare is None: return False,"Land warfare layer unavailable."
        if s.stockpiles.get('TANK',0)<1 or s.stockpiles.get('ARTILLERY_SHELLS',0)<30 or s.stockpiles.get('TRAINED_PERSONNEL',0)<60: return False,"Land allocation lacks armor, artillery ammunition or trained replacements."
        s.stockpiles['TANK']-=1; s.stockpiles['ARTILLERY_SHELLS']-=30; s.stockpiles['TRAINED_PERSONNEL']-=60
        damaged=[v for v in land_warfare.vehicles.values() if v.hull_pct<95]
        if damaged: damaged[0].hull_pct=_clamp(damaged[0].hull_pct+35,0,100); damaged[0].mobility_pct=_clamp(damaged[0].mobility_pct+30,0,100)
        else:
            for v in land_warfare.vehicles.values(): v.main_ammo+=6
        for b in land_warfare.artillery.values(): b.shells+=30
        u=min(land_warfare.units.values(),key=lambda q:q.manpower/max(1,q.max_manpower)); u.manpower=min(u.max_manpower,u.manpower+60)
        msg="WAR ECONOMY ALLOCATION — armored replacement, artillery ammunition and trained personnel delivered to land forces."
    elif dest=='NAVY':
        if task_force is None: return False,"Task-force layer unavailable."
        if s.stockpiles.get('NAVAL_AMMO',0)<30 or s.stockpiles.get('BUNKER_FUEL',0)<25 or s.stockpiles.get('REPAIR_STORES',0)<15: return False,"Naval allocation requires ammunition, bunker fuel and repair stores."
        s.stockpiles['NAVAL_AMMO']-=30; s.stockpiles['BUNKER_FUEL']-=25; s.stockpiles['REPAIR_STORES']-=15
        for ship in task_force.friendly.values():
            ship.ammo_pct=_clamp(ship.ammo_pct+8,0,100); ship.fuel_pct=_clamp(ship.fuel_pct+7,0,100); ship.hull_pct=_clamp(ship.hull_pct+2,0,100)
        msg="WAR ECONOMY ALLOCATION — fleet ammunition, fuel and repair stores released to Task Force."
    else: # BASES
        if campaign is None: return False,"Naval campaign base network unavailable."
        if s.stockpiles.get('BUNKER_FUEL',0)<20 or s.stockpiles.get('AVIATION_FUEL',0)<15 or s.stockpiles.get('MEDICAL_STORES',0)<10: return False,"Base allocation stockpile insufficient."
        s.stockpiles['BUNKER_FUEL']-=20; s.stockpiles['AVIATION_FUEL']-=15; s.stockpiles['MEDICAL_STORES']-=10
        b=min(campaign.bases.values(),key=lambda q:q.readiness)
        b.fuel=_clamp(b.fuel+15,0,100); b.aviation_fuel=_clamp(b.aviation_fuel+15,0,100); b.medical=_clamp(b.medical+10,0,100); b.repair_stores=_clamp(b.repair_stores+8,0,100)
        msg=f"WAR ECONOMY ALLOCATION — strategic stocks delivered to {b.name}."
    s.allocations+=1; s.network.deliveries+=1; s.last_event=msg; s.log.insert(0,msg); return True,msg


def advance_war_economy(s: WarEconomyState, dt: float, strategic_war=None, campaign=None, air_wing=None, land_warfare=None, task_force=None) -> List[str]:
    if not s.active: return []
    dt=max(0.0,float(dt)); dt_min=dt*2.0
    s.elapsed_min+=dt_min; s.hour=6+(s.elapsed_min/60); s.day=1+int(s.hour//24); s.hour%=24
    # slow extraction/import stream keeps a long war viable but never infinite.
    s.reserves['STEEL']=min(900,s.reserves.get('STEEL',0)+dt_min*.012)
    s.reserves['ALUMINUM']=min(600,s.reserves.get('ALUMINUM',0)+dt_min*.006)
    s.reserves['OIL']=min(1000,s.reserves.get('OIL',0)+dt_min*.014)
    s.reserves['EXPLOSIVES']=min(500,s.reserves.get('EXPLOSIVES',0)+dt_min*.004)
    s.reserves['FOOD']=min(900,s.reserves.get('FOOD',0)+dt_min*.010)
    s.research_points=min(200,s.research_points+dt_min*.015)
    msgs=[]
    msgs.extend(_advance_production(s,dt_min)); msgs.extend(_advance_research(s,dt_min)); msgs.extend(_advance_training(s,dt_min))
    _strategic_consumption(s,strategic_war,dt_min); msgs.extend(_industrial_threat(s,strategic_war,dt_min))
    # network and facility damage directly influence overall economy health.
    facility_health=sum(100-f.damage for f in s.facilities.values())/max(1,len(s.facilities))
    reserve_health=sum(min(100,s.stockpiles.get(k,0)) for k in ('NAVAL_AMMO','ARTILLERY_SHELLS','REPAIR_STORES','AVIATION_FUEL','BUNKER_FUEL','MEDICAL_STORES'))/6
    s.industrial_score=_clamp(facility_health*.45+s.network.throughput*.30+reserve_health*.25,0,100)
    if msgs:
        s.last_event=msgs[-1]
        for m in reversed(msgs): s.log.insert(0,m)
        s.log=s.log[:120]
    return msgs


def economy_summary(s: WarEconomyState) -> str:
    active=sum(1 for o in s.orders.values() if o.status=='ACTIVE')
    return f"WAR ECONOMY • {'ACTIVE' if s.active else 'STANDBY'} • DAY {s.day} {int(s.hour):02}:00 • SCORE {s.industrial_score:.0f}% • ACTIVE LINES {active} • TRANSPORT {s.network.throughput:.0f}% • ALLOC {s.selected_allocation}"


def facility_lines(s: WarEconomyState) -> List[str]:
    sel=s.selected_facility; out=[]
    for f in s.facilities.values():
        mark='>' if f is sel else ' '
        out.append(f"{mark} {f.key:<10} {f.name:<29} {f.kind:<10} CAP {f.effective_capacity:3.0f}% DMG {f.damage:3.0f}% PWR {f.power:3.0f}% • {f.status}")
    return out


def production_lines(s: WarEconomyState) -> List[str]:
    sel=s.selected_order; out=[]
    for o in s.orders.values():
        mark='>' if o is sel else ' '
        out.append(f"{mark} {o.key:<11} {o.title:<31} {o.status:<13} {o.produced:4.0f}/{o.target_quantity:<4.0f} • {o.progress_minutes:5.0f}/{o.unit_minutes:.0f} min")
    return out


def stockpile_lines(s: WarEconomyState) -> List[str]:
    keys=list(s.stockpiles)
    return ["  "+" • ".join(f"{k.replace('_',' ')} {s.stockpiles[k]:.0f}" for k in keys[i:i+3]) for i in range(0,len(keys),3)]


def research_lines(s: WarEconomyState) -> List[str]:
    sel=s.selected_research; return [f"{'>' if p is sel else ' '} {p.key:<8} {p.title:<34} {p.status:<9} {p.progress:3.0f}% • {p.effect}" for p in s.research.values()]


def training_lines(s: WarEconomyState) -> List[str]:
    sel=s.selected_training; return [f"{'>' if p is sel else ' '} {p.key:<10} {p.title:<31} {p.status:<7} {p.progress_minutes:4.0f}/{p.cycle_minutes:.0f} min • graduates {p.graduates}" for p in s.training.values()]


def war_economy_to_dict(s: WarEconomyState) -> dict:
    return asdict(s)


def war_economy_from_dict(data: dict) -> WarEconomyState:
    if not data: return create_war_economy()
    base=create_war_economy(); complex_keys={'reserves','stockpiles','facilities','orders','research','training','network','log'}
    for k,v in data.items():
        if k in complex_keys: continue
        if hasattr(base,k): setattr(base,k,v)
    base.reserves.update(data.get('reserves',{})); base.stockpiles.update(data.get('stockpiles',{}))
    for k,v in data.get('facilities',{}).items():
        try: base.facilities[k]=IndustrialFacility(**v)
        except TypeError: pass
    for k,v in data.get('orders',{}).items():
        try: base.orders[k]=ProductionOrder(**v)
        except TypeError: pass
    for k,v in data.get('research',{}).items():
        try: base.research[k]=ResearchProject(**v)
        except TypeError: pass
    for k,v in data.get('training',{}).items():
        try: base.training[k]=TrainingPipeline(**v)
        except TypeError: pass
    if isinstance(data.get('network'),dict):
        try: base.network=TransportNetwork(**data['network'])
        except TypeError: pass
    base.log=list(data.get('log',base.log))[:120]
    return base
