from __future__ import annotations

"""v2.4 strategic mobility / global logistics network.

All hub names, routes, distances, speeds, cargo quantities, interdiction coefficients and
transport timings in this module are GAME/TRAINING abstractions. Historical scenarios remain
separate in the sourced/locked historical layer.
"""

from dataclasses import dataclass, field, asdict
import math
from typing import Dict, List, Optional, Tuple


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


@dataclass
class LogisticsHub:
    key: str
    name: str
    hub_type: str
    x: float
    y: float
    recipient: str
    capacity: float = 100.0
    damage: float = 0.0
    security: float = 80.0
    congestion: float = 10.0
    inventory: Dict[str, float] = field(default_factory=dict)
    status: str = "OPERATING"
    deliveries: int = 0

    @property
    def effective_capacity(self) -> float:
        return _clamp(self.capacity * (1.0-self.damage/100.0) * (1.0-self.congestion/140.0), 5.0, 100.0)


@dataclass
class LogisticsRoute:
    key: str
    name: str
    mode: str
    origin: str
    destination: str
    distance_km: float
    base_speed_kph: float
    capacity: float = 100.0
    damage: float = 0.0
    interdiction: float = 12.0
    bridge_integrity: float = 100.0
    escort_required: bool = False
    status: str = "OPEN"
    shipments_completed: int = 0
    losses: int = 0

    @property
    def effective_capacity(self) -> float:
        bridge = self.bridge_integrity/100.0 if self.mode in ("ROAD","RAIL") else 1.0
        return _clamp(self.capacity*(1.0-self.damage/100.0)*bridge, 0.0, 100.0)


@dataclass
class CargoPackage:
    key: str
    title: str
    cargo: Dict[str, float]
    priority: int = 2


@dataclass
class StrategicShipment:
    key: str
    route_key: str
    package_key: str
    mode: str
    cargo: Dict[str, float]
    progress_km: float = 0.0
    health: float = 100.0
    escort: bool = False
    priority: int = 2
    status: str = "EN ROUTE"
    delay_min: float = 0.0
    elapsed_min: float = 0.0
    interdiction_exposure: float = 0.0
    last_event: str = "Dispatched."


@dataclass
class LogisticsNetworkState:
    active: bool = False
    elapsed_min: float = 0.0
    hubs: Dict[str, LogisticsHub] = field(default_factory=dict)
    routes: Dict[str, LogisticsRoute] = field(default_factory=dict)
    packages: Dict[str, CargoPackage] = field(default_factory=dict)
    shipments: Dict[str, StrategicShipment] = field(default_factory=dict)
    selected_hub_index: int = 0
    selected_route_index: int = 0
    selected_package_index: int = 0
    selected_shipment_index: int = 0
    priority: int = 2
    shipment_seq: int = 1
    delivered_shipments: int = 0
    lost_shipments: int = 0
    delayed_shipments: int = 0
    escorted_shipments: int = 0
    route_repairs: int = 0
    hub_repairs: int = 0
    hub_issues: int = 0
    cargo_delivered: float = 0.0
    logistics_score: float = 88.0
    last_event: str = "v2.4 strategic mobility network initialized."
    log: List[str] = field(default_factory=list)

    @property
    def selected_hub(self) -> Optional[LogisticsHub]:
        vals=list(self.hubs.values())
        return vals[self.selected_hub_index % len(vals)] if vals else None

    @property
    def selected_route(self) -> Optional[LogisticsRoute]:
        vals=list(self.routes.values())
        return vals[self.selected_route_index % len(vals)] if vals else None

    @property
    def selected_package(self) -> Optional[CargoPackage]:
        vals=list(self.packages.values())
        return vals[self.selected_package_index % len(vals)] if vals else None

    @property
    def selected_shipment(self) -> Optional[StrategicShipment]:
        vals=[x for x in self.shipments.values() if x.status not in ("DELIVERED","LOST")]
        if not vals: vals=list(self.shipments.values())
        return vals[self.selected_shipment_index % len(vals)] if vals else None


def create_logistics_network() -> LogisticsNetworkState:
    s=LogisticsNetworkState()
    s.hubs={
        "NAT-DEPOT": LogisticsHub("NAT-DEPOT","National Distribution Depot","DEPOT",11,322,"NATIONAL",capacity=100,security=90),
        "PORT-DELTA": LogisticsHub("PORT-DELTA","Strategic Port Delta","PORT",31,322,"TRANSIT",capacity=94,security=82),
        "RAIL-ECHO": LogisticsHub("RAIL-ECHO","Railhead Echo","RAILHEAD",51,322,"TRANSIT",capacity=90,security=78),
        "FWD-FOXTROT": LogisticsHub("FWD-FOXTROT","Forward Depot Foxtrot","DEPOT",16,350,"THEATER",capacity=74,security=68),
        "AIR-GOLF": LogisticsHub("AIR-GOLF","Air Logistics Hub Golf","AIRFIELD",34,350,"AIRFIELD",capacity=76,security=72),
        "ANCHOR-HOTEL": LogisticsHub("ANCHOR-HOTEL","Fleet Anchorage Hotel","ANCHORAGE",52,350,"FLEET",capacity=82,security=76),
    }
    s.routes={
        "R-RAIL-1": LogisticsRoute("R-RAIL-1","National Depot → Railhead Echo","RAIL","NAT-DEPOT","RAIL-ECHO",320,42,capacity=92,interdiction=10),
        "R-ROAD-1": LogisticsRoute("R-ROAD-1","Railhead Echo → Forward Depot Foxtrot","ROAD","RAIL-ECHO","FWD-FOXTROT",165,30,capacity=76,interdiction=22,bridge_integrity=88),
        "R-ROAD-2": LogisticsRoute("R-ROAD-2","Forward Depot → Air Logistics Hub","ROAD","FWD-FOXTROT","AIR-GOLF",95,28,capacity=68,interdiction=24,bridge_integrity=92),
        "R-SEA-1": LogisticsRoute("R-SEA-1","Strategic Port Delta → Fleet Anchorage","SEA","PORT-DELTA","ANCHOR-HOTEL",620,24,capacity=88,interdiction=30,escort_required=True),
        "R-SEA-2": LogisticsRoute("R-SEA-2","Strategic Port Delta → Forward Depot Foxtrot","SEA","PORT-DELTA","FWD-FOXTROT",480,21,capacity=74,interdiction=35,escort_required=True),
        "R-PORT": LogisticsRoute("R-PORT","National Depot → Strategic Port Delta","RAIL","NAT-DEPOT","PORT-DELTA",210,38,capacity=90,interdiction=8),
    }
    s.packages={
        "PKG-FUEL": CargoPackage("PKG-FUEL","Fuel Allocation",{"BUNKER_FUEL":30,"AVIATION_FUEL":18},3),
        "PKG-AMMO": CargoPackage("PKG-AMMO","Ammunition Allocation",{"NAVAL_AMMO":20,"ARTILLERY_SHELLS":24,"SMALL_ARMS_AMMO":30},3),
        "PKG-REPAIR": CargoPackage("PKG-REPAIR","Repair / Medical Allocation",{"REPAIR_STORES":20,"MEDICAL_STORES":16},2),
        "PKG-REPL": CargoPackage("PKG-REPL","Replacement Personnel",{"TRAINED_PERSONNEL":120},4),
        "PKG-AIR": CargoPackage("PKG-AIR","Air Group Replacement Package",{"FIGHTER_AIRFRAME":1,"BOMBER_AIRFRAME":1,"AVIATION_FUEL":24,"REPAIR_STORES":10},4),
        "PKG-LAND": CargoPackage("PKG-LAND","Land Force Replacement Package",{"TANK":2,"TRUCK":2,"ARTILLERY_SHELLS":18,"SMALL_ARMS_AMMO":24,"TRAINED_PERSONNEL":80},4),
    }
    s.log=[s.last_event]
    return s


def begin_logistics_network(s: LogisticsNetworkState) -> Tuple[bool,str]:
    if s.active: return False,"Strategic logistics network is already active."
    s.active=True
    s.last_event="STRATEGIC LOGISTICS ACTIVE — national output must now move through physical transport routes before front-line delivery."
    s.log.insert(0,s.last_event)
    return True,s.last_event


def cycle_hub(s):
    if not s.hubs: return None
    s.selected_hub_index=(s.selected_hub_index+1)%len(s.hubs); return s.selected_hub


def cycle_route(s):
    if not s.routes: return None
    s.selected_route_index=(s.selected_route_index+1)%len(s.routes); return s.selected_route


def cycle_package(s):
    if not s.packages: return None
    s.selected_package_index=(s.selected_package_index+1)%len(s.packages); return s.selected_package


def cycle_shipment(s):
    vals=[x for x in s.shipments.values() if x.status not in ("DELIVERED","LOST")]
    if not vals: vals=list(s.shipments.values())
    if not vals: return None
    s.selected_shipment_index=(s.selected_shipment_index+1)%len(vals); return vals[s.selected_shipment_index]


def cycle_priority(s) -> int:
    s.priority=1 if s.priority>=4 else s.priority+1
    return s.priority


def _can_take(stock: Dict[str,float], cargo: Dict[str,float]) -> bool:
    return all(stock.get(k,0.0)>=v for k,v in cargo.items())


def dispatch_selected_shipment(s: LogisticsNetworkState, war_economy) -> Tuple[bool,str]:
    if not s.active: return False,"Strategic logistics network is not active."
    r=s.selected_route; p=s.selected_package
    if not r or not p: return False,"Select a route and cargo package first."
    if r.status!="OPEN" or r.effective_capacity<15: return False,"Selected transport route is not capable of accepting a shipment."
    if war_economy is None: return False,"National war economy is unavailable."
    origin=s.hubs.get(r.origin)
    if origin is None: return False,"Selected route origin hub is unavailable."
    stock=getattr(war_economy,'stockpiles',{}) if origin.key=="NAT-DEPOT" else origin.inventory
    if not _can_take(stock,p.cargo):
        source_name="national stockpile" if origin.key=="NAT-DEPOT" else f"{origin.name} staged inventory"
        return False,f"SOURCE SHORTAGE — {source_name} does not contain the selected cargo package. Move/stage the cargo through preceding route legs first."
    # Route congestion limits simultaneous active lifts.
    active=sum(1 for sh in s.shipments.values() if sh.route_key==r.key and sh.status in ("EN ROUTE","DELAYED"))
    slots=max(1,int(r.effective_capacity//25))
    if active>=slots: return False,f"ROUTE CONGESTION — {r.name} has no free transport slot."
    for k,v in p.cargo.items(): stock[k]=max(0.0,stock.get(k,0.0)-v)
    key=f"LOG-{s.shipment_seq:03d}"; s.shipment_seq+=1
    sh=StrategicShipment(key,r.key,p.key,r.mode,dict(p.cargo),escort=False,priority=s.priority)
    s.shipments[key]=sh
    msg=f"SHIPMENT DISPATCHED — {key}: {p.title} via {r.name}. Cargo reserved from its route-origin inventory and is now in transit."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def assign_escort(s: LogisticsNetworkState, task_force=None) -> Tuple[bool,str]:
    sh=s.selected_shipment
    if not sh or sh.status not in ("EN ROUTE","DELAYED"): return False,"No active shipment selected."
    r=s.routes.get(sh.route_key)
    if not r: return False,"Shipment route unavailable."
    if sh.escort:
        sh.escort=False; return True,f"ESCORT RELEASED — {sh.key}."
    if r.mode=="SEA":
        if task_force is None: return False,"Task-force escort assets unavailable."
        escorts=[v for v in getattr(task_force,'friendly',{}).values() if getattr(v,'hull_pct',100)>45 and getattr(v,'fuel_pct',100)>20]
        if not escorts: return False,"No serviceable fleet escort is available."
    sh.escort=True; s.escorted_shipments+=1
    msg=f"ESCORT ASSIGNED — {sh.key} protected along {r.name}."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def repair_selected_route(s: LogisticsNetworkState, war_economy) -> Tuple[bool,str]:
    r=s.selected_route
    if not r: return False,"No route selected."
    if r.damage<=.1 and r.bridge_integrity>=99: return False,"Selected route does not require significant repair."
    stock=getattr(war_economy,'stockpiles',{}) if war_economy else {}
    if stock.get('REPAIR_STORES',0)<12: return False,"National repair stores are insufficient for route restoration."
    stock['REPAIR_STORES']-=12
    r.damage=max(0.0,r.damage-28.0); r.bridge_integrity=min(100.0,r.bridge_integrity+35.0)
    if r.effective_capacity>=15: r.status="OPEN"
    s.route_repairs+=1
    msg=f"ROUTE REPAIR — {r.name}: damage {r.damage:.0f}%, bridge {r.bridge_integrity:.0f}%, effective capacity {r.effective_capacity:.0f}%."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def repair_selected_hub(s: LogisticsNetworkState, war_economy) -> Tuple[bool,str]:
    h=s.selected_hub
    if not h: return False,"No logistics hub selected."
    if h.damage<=.1: return False,"Selected hub does not require repair."
    stock=getattr(war_economy,'stockpiles',{}) if war_economy else {}
    if stock.get('REPAIR_STORES',0)<10: return False,"National repair stores are insufficient for hub restoration."
    stock['REPAIR_STORES']-=10; h.damage=max(0,h.damage-32); h.status="OPERATING" if h.damage<80 else "CRIPPLED"; s.hub_repairs+=1
    msg=f"HUB REPAIR — {h.name}: damage reduced to {h.damage:.0f}%."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def _apply_to_recipient(h: LogisticsHub, cargo: Dict[str,float], strategic_war=None, campaign=None, air_wing=None, ground_ops=None, land_warfare=None, task_force=None) -> str:
    rec=h.recipient
    if rec=="THEATER" and strategic_war is not None:
        depots=[d for d in strategic_war.depots.values() if d.side=="FRIENDLY"]
        if depots:
            d=min(depots,key=lambda q:(q.fuel+q.ammunition+q.medical+q.repair)/4)
            d.fuel=_clamp(d.fuel+cargo.get('BUNKER_FUEL',0)*.7,0,100)
            d.ammunition=_clamp(d.ammunition+(cargo.get('SMALL_ARMS_AMMO',0)+cargo.get('ARTILLERY_SHELLS',0))*.35,0,100)
            d.medical=_clamp(d.medical+cargo.get('MEDICAL_STORES',0)*.7,0,100)
            d.repair=_clamp(d.repair+cargo.get('REPAIR_STORES',0)*.7,0,100)
            d.replacements += int(cargo.get('TRAINED_PERSONNEL',0))
            if land_warfare is not None:
                bats=list(getattr(land_warfare,'artillery',{}).values())
                for bat in bats:
                    bat.shells += int(cargo.get('ARTILLERY_SHELLS',0)/max(1,len(bats)))
                lg=getattr(land_warfare,'logistics',None)
                if lg is not None:
                    lg.ammunition=_clamp(lg.ammunition+cargo.get('SMALL_ARMS_AMMO',0)*.25,0,100)
                    lg.fuel=_clamp(lg.fuel+cargo.get('BUNKER_FUEL',0)*.35,0,100)
                    lg.medical=_clamp(lg.medical+cargo.get('MEDICAL_STORES',0)*.45,0,100)
                    lg.repair_parts=_clamp(lg.repair_parts+cargo.get('REPAIR_STORES',0)*.45,0,100)
            return f"issued into {d.name}"
    if rec=="FLEET" and task_force is not None:
        lg=getattr(task_force,'logistics',None)
        if lg is not None:
            lg.bunker_fuel_pct=_clamp(lg.bunker_fuel_pct+cargo.get('BUNKER_FUEL',0)*.35,0,100)
            lg.aviation_fuel_pct=_clamp(lg.aviation_fuel_pct+cargo.get('AVIATION_FUEL',0)*.35,0,100)
            lg.ammunition_pct=_clamp(lg.ammunition_pct+cargo.get('NAVAL_AMMO',0)*.45,0,100)
            lg.repair_stores_pct=_clamp(lg.repair_stores_pct+cargo.get('REPAIR_STORES',0)*.45,0,100)
        return "issued to Task Force logistics"
    if rec=="AIRFIELD" and ground_ops is not None:
        af=ground_ops.selected_airfield or (list(ground_ops.airfields.values())[0] if ground_ops.airfields else None)
        if af:
            af.aviation_fuel=_clamp(af.aviation_fuel+cargo.get('AVIATION_FUEL',0)*.8,0,100)
            af.ammunition=_clamp(af.ammunition+(cargo.get('SMALL_ARMS_AMMO',0)+cargo.get('ARTILLERY_SHELLS',0))*.25,0,100)
            af.repair_stores=_clamp(af.repair_stores+cargo.get('REPAIR_STORES',0)*.7,0,100)
            af.medical=_clamp(af.medical+cargo.get('MEDICAL_STORES',0)*.7,0,100)
            if air_wing is not None:
                air_wing.aviation_fuel_units += cargo.get('AVIATION_FUEL',0)*35
                air_wing.spare_parts += cargo.get('REPAIR_STORES',0)*4
            return f"issued to {af.name}"
    if rec=="BASE" and campaign is not None:
        b=campaign.selected_base or (list(campaign.bases.values())[0] if campaign.bases else None)
        if b:
            for attr,key,mult in (("fuel","BUNKER_FUEL",.8),("aviation_fuel","AVIATION_FUEL",.8),("ammunition","NAVAL_AMMO",.8),("repair_stores","REPAIR_STORES",.8),("medical","MEDICAL_STORES",.8)):
                if hasattr(b,attr): setattr(b,attr,_clamp(getattr(b,attr)+cargo.get(key,0)*mult,0,100))
            return f"issued to {b.name}"
    return "recipient unavailable"


def issue_selected_hub(s: LogisticsNetworkState, strategic_war=None, campaign=None, air_wing=None, ground_ops=None, land_warfare=None, task_force=None) -> Tuple[bool,str]:
    h=s.selected_hub
    if not h: return False,"No logistics hub selected."
    if h.recipient in ("NATIONAL","TRANSIT"):
        return False,f"{h.name} is a staging/transit hub; its inventory must move on another route rather than being issued operationally."
    cargo={k:v for k,v in h.inventory.items() if v>1e-6}
    if not cargo: return False,f"{h.name} has no staged cargo to issue."
    where=_apply_to_recipient(h,cargo,strategic_war,campaign,air_wing,ground_ops,land_warfare,task_force)
    if where=="recipient unavailable": return False,"Selected hub's operational recipient is unavailable."
    for k in list(cargo): h.inventory[k]=0.0
    s.hub_issues+=1; s.cargo_delivered+=sum(cargo.values())
    msg=f"HUB ISSUE COMPLETE — {h.name}: {where}; {sum(cargo.values()):.0f} cargo units transferred from staged inventory."
    s.last_event=msg; s.log.insert(0,msg); return True,msg


def _interdiction_pressure(strategic_war) -> float:
    if strategic_war is None or not getattr(strategic_war,'active',False): return 0.0
    sectors=getattr(strategic_war,'sectors',{}).values()
    enemy=sum(getattr(x,'value',0) for x in sectors if getattr(x,'owner','')=='ENEMY')
    return min(25.0,enemy*.45)


def advance_logistics_network(s: LogisticsNetworkState, dt_sec: float, war_economy=None, strategic_war=None, campaign=None, air_wing=None, ground_ops=None, land_warfare=None, task_force=None) -> List[str]:
    if not s.active: return []
    dt_min=max(0.0,float(dt_sec))*2.0; s.elapsed_min+=dt_min; msgs=[]
    enemy_pressure=_interdiction_pressure(strategic_war)
    # Economy transport damage propagates into route/hub performance rather than being duplicated as a separate universe.
    if war_economy is not None:
        net=getattr(war_economy,'network',None)
        if net:
            for r in s.routes.values():
                base=getattr(net,'port_damage',0) if r.mode=='SEA' else getattr(net,'rail_damage',0) if r.mode=='RAIL' else getattr(net,'road_damage',0)
                r.damage=max(r.damage,base*.45)
                if r.effective_capacity<15: r.status="CLOSED"
    for sh in list(s.shipments.values()):
        if sh.status not in ("EN ROUTE","DELAYED"): continue
        r=s.routes.get(sh.route_key)
        if not r: sh.status="LOST"; s.lost_shipments+=1; continue
        origin=s.hubs.get(r.origin); dest=s.hubs.get(r.destination)
        if not origin or not dest: continue
        sh.elapsed_min += dt_min
        if r.status!="OPEN" or r.effective_capacity<15 or dest.effective_capacity<15:
            if sh.status!="DELAYED": s.delayed_shipments+=1
            sh.status="DELAYED"; sh.delay_min+=dt_min; sh.last_event="Transport route/hub capacity insufficient."
            continue
        sh.status="EN ROUTE"
        speed=r.base_speed_kph * max(.22,r.effective_capacity/100.0) * max(.25,dest.effective_capacity/100.0)
        speed*=1.0 + .08*(sh.priority-2)
        remaining=max(0.0,r.distance_km-sh.progress_km)
        # A large simulation tick must not expose a shipment to interdiction after it has already arrived.
        travel_min=min(dt_min, (remaining/max(.001,speed))*60.0)
        sh.progress_km += speed*(travel_min/60.0)
        # Deterministic exposure accumulation. Escort cuts sea interdiction substantially and helps land movements too.
        risk=max(0.0,r.interdiction+enemy_pressure-dest.security*.10)
        if sh.escort: risk*=.30 if r.mode=='SEA' else .55
        sh.interdiction_exposure += travel_min*risk/100.0
        # Every 25 exposure points causes a deterministic hit and resets the accumulator.
        while sh.interdiction_exposure>=25 and sh.status=="EN ROUTE":
            sh.interdiction_exposure-=25
            dmg=7.0 + r.interdiction*.18
            sh.health=max(0.0,sh.health-dmg)
            sh.last_event=f"SIMULATED INTERDICTION — shipment took {dmg:.0f}% damage."
            if sh.health<=0:
                sh.status="LOST"; r.losses+=1; s.lost_shipments+=1
                msg=f"SHIPMENT LOST — {sh.key} destroyed/interdicted on {r.name}; cargo did not reach destination."
                s.last_event=msg; s.log.insert(0,msg); msgs.append(msg)
        if sh.status!="EN ROUTE": continue
        if sh.progress_km>=r.distance_km-1e-6:
            sh.progress_km=r.distance_km; sh.status="DELIVERED"; r.shipments_completed+=1; s.delivered_shipments+=1; dest.deliveries+=1
            delivered={k:v*(sh.health/100.0) for k,v in sh.cargo.items()}
            for k,v in delivered.items(): dest.inventory[k]=dest.inventory.get(k,0.0)+v
            msg=f"SHIPMENT ARRIVED — {sh.key} received at {dest.name}; cargo condition {sh.health:.0f}%. Staged inventory must be issued or moved onward."
            sh.last_event=msg; s.last_event=msg; s.log.insert(0,msg); msgs.append(msg)
    active=sum(1 for x in s.shipments.values() if x.status in ("EN ROUTE","DELAYED"))
    open_routes=sum(1 for r in s.routes.values() if r.status=="OPEN")
    total_routes=max(1,len(s.routes)); loss_penalty=s.lost_shipments*4.5
    delay_penalty=sum(min(10,sh.delay_min/60.0) for sh in s.shipments.values() if sh.status=="DELAYED")
    s.logistics_score=_clamp(70 + open_routes/total_routes*20 + min(10,s.delivered_shipments*.8) - loss_penalty - delay_penalty,0,100)
    return msgs


def logistics_summary(s: LogisticsNetworkState) -> str:
    active=sum(1 for x in s.shipments.values() if x.status in ("EN ROUTE","DELAYED"))
    return f"LOGISTICS {'ACTIVE' if s.active else 'STANDBY'} • active {active} • arrived {s.delivered_shipments} • issued {s.hub_issues} • lost {s.lost_shipments} • delayed {s.delayed_shipments} • score {s.logistics_score:.0f}%"


def hub_lines(s) -> List[str]:
    sel=s.selected_hub
    return [f"{'>' if h is sel else ' '} {h.key:<12} {h.name:<30} {h.hub_type:<9} cap {h.effective_capacity:3.0f}% dmg {h.damage:3.0f}% sec {h.security:3.0f}% arrivals {h.deliveries} stock {sum(h.inventory.values()):.0f}" for h in s.hubs.values()]


def route_lines(s) -> List[str]:
    sel=s.selected_route
    return [f"{'>' if r is sel else ' '} {r.key:<10} {r.mode:<4} {r.name:<43} cap {r.effective_capacity:3.0f}% risk {r.interdiction:2.0f}% {r.status}" for r in s.routes.values()]


def package_lines(s) -> List[str]:
    sel=s.selected_package
    out=[]
    for p in s.packages.values():
        cargo=', '.join(f"{k.replace('_',' ')} {v:.0f}" for k,v in p.cargo.items())
        out.append(f"{'>' if p is sel else ' '} {p.key:<10} {p.title:<31} • {cargo}")
    return out


def shipment_lines(s) -> List[str]:
    sel=s.selected_shipment
    vals=list(s.shipments.values())[-8:]
    return [f"{'>' if sh is sel else ' '} {sh.key:<8} {sh.mode:<4} {sh.status:<9} {sh.progress_km:5.0f}/{s.routes.get(sh.route_key).distance_km if s.routes.get(sh.route_key) else 0:.0f} km • health {sh.health:3.0f}% • escort {'YES' if sh.escort else 'NO'}" for sh in vals]


def logistics_network_to_dict(s: LogisticsNetworkState) -> dict:
    return asdict(s)


def logistics_network_from_dict(data: dict) -> LogisticsNetworkState:
    if not data: return create_logistics_network()
    base=create_logistics_network(); complex_keys={'hubs','routes','packages','shipments','log'}
    for k,v in data.items():
        if k in complex_keys: continue
        if hasattr(base,k): setattr(base,k,v)
    for k,v in data.get('hubs',{}).items():
        try: base.hubs[k]=LogisticsHub(**v)
        except TypeError: pass
    for k,v in data.get('routes',{}).items():
        try: base.routes[k]=LogisticsRoute(**v)
        except TypeError: pass
    for k,v in data.get('packages',{}).items():
        try: base.packages[k]=CargoPackage(**v)
        except TypeError: pass
    for k,v in data.get('shipments',{}).items():
        try: base.shipments[k]=StrategicShipment(**v)
        except TypeError: pass
    base.log=list(data.get('log',base.log))[:160]
    return base
