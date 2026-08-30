from __future__ import annotations

"""War Simulator v1.3 task-force / open-ocean operations.

Historical ship names used for the friendly Midway task-force roster come from the existing
sourced scenario manifest. Exact formation spacing, captain behavior, fuel/ammunition quantities,
sensor ranges, logistics behavior, enemy surface/submarine training contacts and combat
coefficients are gameplay abstractions unless a scenario explicitly provides sourced values.
"""

from dataclasses import dataclass, field, asdict
import math
from typing import Dict, List, Optional, Tuple


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _wrap(v: float) -> float:
    return v % 360.0


def _signed(v: float) -> float:
    return (v + 180.0) % 360.0 - 180.0


def _nav_vec(direction_deg: float, magnitude: float) -> Tuple[float, float]:
    r = math.radians(direction_deg)
    return math.sin(r) * magnitude, math.cos(r) * magnitude


def _bearing_range(e0: float, n0: float, e1: float, n1: float) -> Tuple[float, float]:
    de, dn = e1-e0, n1-n0
    return _wrap(math.degrees(math.atan2(de, dn))), math.hypot(de, dn)


@dataclass
class FleetVessel:
    key: str
    name: str
    vessel_type: str
    side: str
    east_nm: float
    north_nm: float
    heading_deg: float = 90.0
    speed_knots: float = 15.0
    max_speed_knots: float = 32.0
    desired_bearing_deg: float = 180.0   # relative to flagship bow
    desired_range_nm: float = 1.5
    captain: str = "AI Captain"
    doctrine: str = "FORMATION KEEPING"
    fuel_pct: float = 100.0
    ammo_pct: float = 100.0
    hull_pct: float = 100.0
    propulsion_pct: float = 100.0
    steering_pct: float = 100.0
    sensor_pct: float = 100.0
    radar_range_nm: float = 28.0
    visual_range_nm: float = 12.0
    collision_avoiding: bool = False
    in_station: bool = False
    detached: bool = False
    replenishing: bool = False
    last_order: str = "Maintain assigned station"
    status: str = "FORMATION"
    depth_charges: int = 24
    surface_salvos: int = 80
    repair_destination: str = ""


@dataclass
class FleetContact:
    key: str
    label: str
    contact_type: str
    east_nm: float
    north_nm: float
    heading_deg: float
    speed_knots: float
    side: str = "HOSTILE_TRAINING"
    confidence: float = 0.0
    detected: bool = False
    identified: bool = False
    submerged: bool = False
    health_pct: float = 100.0
    threat: str = "UNKNOWN"
    last_report: str = "No report"
    attacked: bool = False


@dataclass
class FleetLogistics:
    aviation_fuel_pct: float = 84.0
    bunker_fuel_pct: float = 88.0
    food_pct: float = 92.0
    ammunition_pct: float = 86.0
    repair_stores_pct: float = 78.0
    transfer_in_progress: bool = False
    transfer_target: str = ""
    transfer_progress: float = 0.0
    replenishments: int = 0


@dataclass
class TaskForceState:
    friendly: Dict[str, FleetVessel] = field(default_factory=dict)
    contacts: Dict[str, FleetContact] = field(default_factory=dict)
    logistics: FleetLogistics = field(default_factory=FleetLogistics)
    formation: str = "CARRIER SCREEN"
    selected_friendly_index: int = 0
    selected_contact_index: int = 0
    radio_silence: bool = False
    signal_method: str = "TACTICAL RADIO"
    training_problem_active: bool = False
    fleet_alert: str = "ROUTINE"
    closest_approach_nm: float = 99.0
    collision_warnings: int = 0
    formation_orders: int = 0
    signals_sent: int = 0
    surface_contacts_defeated: int = 0
    submarines_defeated: int = 0
    escort_damage_events: int = 0
    miles_steamed: float = 0.0
    log: List[str] = field(default_factory=list)
    _elapsed_s: float = 0.0
    _attack_accum_s: float = 0.0

    @property
    def selected_friendly(self) -> Optional[FleetVessel]:
        vals = list(self.friendly.values())
        return vals[self.selected_friendly_index % len(vals)] if vals else None

    @property
    def selected_contact(self) -> Optional[FleetContact]:
        vals = [c for c in self.contacts.values() if c.health_pct > 0]
        return vals[self.selected_contact_index % len(vals)] if vals else None


# Training formation slots. Names are sourced from the existing TF16 order-of-battle manifest;
# exact spacing/geometry is deliberately simulation calibration.
_FRIENDLY_ROSTER = [
    ("HORNET", "USS Hornet (CV-8)", "CARRIER", 205, 2.2, 31, 32, 34),
    ("NORTHAMPTON", "USS Northampton", "HEAVY CRUISER", 330, 1.8, 32, 30, 26),
    ("VINCENNES", "USS Vincennes", "HEAVY CRUISER", 30, 1.8, 32, 30, 26),
    ("PENSACOLA", "USS Pensacola", "HEAVY CRUISER", 285, 2.5, 32, 30, 26),
    ("MINNEAPOLIS", "USS Minneapolis", "HEAVY CRUISER", 75, 2.5, 32, 30, 26),
    ("NEW_ORLEANS", "USS New Orleans", "HEAVY CRUISER", 180, 2.8, 32, 30, 26),
    ("ATLANTA", "USS Atlanta", "LIGHT CRUISER (AA)", 0, 1.4, 33, 32, 28),
    ("WORDEN", "USS Worden", "DESTROYER", 315, 1.0, 36, 24, 16),
    ("MONAGHAN", "USS Monaghan", "DESTROYER", 45, 1.0, 36, 24, 16),
    ("PHELPS", "USS Phelps", "DESTROYER", 135, 1.0, 36, 24, 16),
    ("MAURY", "USS Maury", "DESTROYER", 225, 1.0, 36, 24, 16),
]


def create_task_force(flagship_east: float = 0.0, flagship_north: float = 0.0, flagship_heading: float = 90.0) -> TaskForceState:
    s = TaskForceState()
    for key, name, typ, rel_bearing, rng, max_spd, radar, visual in _FRIENDLY_ROSTER:
        abs_bearing = _wrap(flagship_heading + rel_bearing)
        de, dn = _nav_vec(abs_bearing, rng)
        s.friendly[key] = FleetVessel(
            key=key, name=name, vessel_type=typ, side="FRIENDLY",
            east_nm=flagship_east+de, north_nm=flagship_north+dn,
            heading_deg=flagship_heading, speed_knots=0.0,
            max_speed_knots=max_spd, desired_bearing_deg=rel_bearing, desired_range_nm=rng,
            captain=f"{name.split('USS ')[-1].split(' (')[0]} AI Commanding Officer",
            radar_range_nm=radar, visual_range_nm=visual,
            depth_charges=36 if typ == "DESTROYER" else 0,
            surface_salvos=120 if "CRUISER" in typ else 50,
        )
    s.log.append("Task Force 16 training formation initialized around Enterprise. Formation geometry is simulation calibration.")
    return s


def formation_slots(name: str) -> Dict[str, Tuple[float, float]]:
    name = name.upper()
    slots: Dict[str, Tuple[float, float]] = {}
    for i, (key, _, typ, base_brg, base_rng, *_rest) in enumerate(_FRIENDLY_ROSTER):
        if name == "COLUMN":
            slots[key] = (180.0, 1.0 + i * 0.55)
        elif name == "DISPERSED":
            slots[key] = (base_brg, base_rng * 1.65)
        elif name == "ASW SCREEN":
            if typ == "DESTROYER":
                destroyer_idx = [r[0] for r in _FRIENDLY_ROSTER if r[2] == "DESTROYER"].index(key)
                slots[key] = ((315 + destroyer_idx*90) % 360, 2.2)
            else:
                slots[key] = (base_brg, max(base_rng, 2.0))
        else:  # carrier screen
            slots[key] = (base_brg, base_rng)
    return slots


def set_formation(s: TaskForceState, name: str) -> str:
    name = name.upper()
    if name not in ("CARRIER SCREEN", "COLUMN", "DISPERSED", "ASW SCREEN"):
        return f"Unknown formation: {name}."
    s.formation = name
    for key, slot in formation_slots(name).items():
        if key in s.friendly:
            s.friendly[key].desired_bearing_deg, s.friendly[key].desired_range_nm = slot
            s.friendly[key].last_order = f"Take station in {name}"
            s.friendly[key].detached = False
    s.formation_orders += 1
    s.log.insert(0, f"FORMATION ORDER: {name}. Screen ships maneuvering to assigned stations.")
    return f"Task force ordered to {name}."


def cycle_friendly(s: TaskForceState) -> Optional[FleetVessel]:
    if not s.friendly:
        return None
    s.selected_friendly_index = (s.selected_friendly_index + 1) % len(s.friendly)
    return s.selected_friendly


def cycle_contact(s: TaskForceState) -> Optional[FleetContact]:
    vals = [c for c in s.contacts.values() if c.health_pct > 0]
    if not vals:
        return None
    s.selected_contact_index = (s.selected_contact_index + 1) % len(vals)
    return s.selected_contact


def toggle_radio_silence(s: TaskForceState) -> str:
    s.radio_silence = not s.radio_silence
    s.signal_method = "SIGNAL FLAGS / LAMP" if s.radio_silence else "TACTICAL RADIO"
    s.signals_sent += 1
    msg = f"Fleet communications: {'RADIO SILENCE — visual signaling' if s.radio_silence else 'tactical radio restored'}."
    s.log.insert(0, msg)
    return msg


def order_selected_ship(s: TaskForceState, code: str) -> Tuple[bool, str]:
    v = s.selected_friendly
    if not v:
        return False, "No friendly ship selected."
    code = code.upper()
    if code == "STATION":
        v.detached = False; v.last_order = f"Resume {s.formation} station"; v.status = "FORMATION"
        msg = f"{v.name}: resume assigned formation station."
    elif code == "SCREEN_AHEAD":
        v.detached = False; v.desired_bearing_deg = 0.0; v.desired_range_nm = 2.5; v.last_order = "Screen 2.5 nm ahead"; v.status = "SCREENING"
        msg = f"{v.name}: screen 2.5 nm ahead of Enterprise."
    elif code == "SCREEN_ASTERN":
        v.detached = False; v.desired_bearing_deg = 180.0; v.desired_range_nm = 2.5; v.last_order = "Screen 2.5 nm astern"; v.status = "SCREENING"
        msg = f"{v.name}: screen 2.5 nm astern of Enterprise."
    elif code == "DETACH":
        v.detached = True; v.last_order = "Detached for independent maneuver"; v.status = "DETACHED"
        msg = f"{v.name}: detached from formation for independent maneuver."
    else:
        return False, f"Unknown fleet order: {code}."
    s.formation_orders += 1; s.signals_sent += 1; s.log.insert(0, "SIGNAL: " + msg)
    return True, msg


def start_surface_training_problem(s: TaskForceState, flagship_e: float, flagship_n: float, flagship_heading: float) -> Tuple[bool, str]:
    if s.training_problem_active:
        return False, "A surface/submarine training problem is already active."
    s.contacts.clear()
    spawns = [
        ("RED_CRUISER_1", "SIM hostile cruiser group", "SURFACE", 35.0, 13.0, False, "HIGH"),
        ("RED_DESTROYER_1", "SIM hostile destroyer", "SURFACE", 18.0, 10.5, False, "MEDIUM"),
        ("RED_SUB_1", "SIM submerged submarine", "SUBMARINE", 305.0, 7.8, True, "HIGH"),
    ]
    for key,label,typ,rel_bearing,rng,submerged,threat in spawns:
        de,dn = _nav_vec(_wrap(flagship_heading+rel_bearing),rng)
        s.contacts[key] = FleetContact(
            key=key,label=label,contact_type=typ,east_nm=flagship_e+de,north_nm=flagship_n+dn,
            heading_deg=_wrap(flagship_heading+180),speed_knots=18.0 if typ=="SURFACE" else 7.0,
            submerged=submerged,threat=threat,
        )
    s.training_problem_active = True
    s.fleet_alert = "TACTICAL TRAINING"
    s.log.insert(0, "TRAINING INJECT: simulated hostile surface force and submarine entered the sea room. This is not a Midway historical event.")
    return True, "SIMULATED fleet contact problem started — surface and submarine contacts are now maneuvering."


def _move(v, dt: float) -> None:
    de,dn = _nav_vec(v.heading_deg, v.speed_knots * dt / 3600.0)
    v.east_nm += de; v.north_nm += dn


def _desired_position(v: FleetVessel, flagship_e: float, flagship_n: float, flagship_heading: float) -> Tuple[float,float]:
    de,dn = _nav_vec(_wrap(flagship_heading + v.desired_bearing_deg), v.desired_range_nm)
    return flagship_e+de, flagship_n+dn


def _formation_ai(v: FleetVessel, flagship_e: float, flagship_n: float, flagship_heading: float, flagship_speed: float, dt: float) -> None:
    if v.detached or v.hull_pct <= 0:
        _move(v, dt); return
    te,tn = _desired_position(v,flagship_e,flagship_n,flagship_heading)
    brg,rng = _bearing_range(v.east_nm,v.north_nm,te,tn)
    err = _signed(brg-v.heading_deg)
    turn_rate = (4.0 + 7.0*(v.steering_pct/100.0)) * dt
    v.heading_deg = _wrap(v.heading_deg + _clamp(err,-turn_rate,turn_rate))
    desired_speed = _clamp(flagship_speed + (rng-0.08)*7.0, 0.0, v.max_speed_knots*(v.propulsion_pct/100.0))
    accel = 1.6*dt
    if v.speed_knots < desired_speed: v.speed_knots = min(desired_speed,v.speed_knots+accel)
    else: v.speed_knots = max(desired_speed,v.speed_knots-accel)
    v.in_station = rng < 0.18 and abs(_signed(v.heading_deg-flagship_heading)) < 12
    v.status = "IN STATION" if v.in_station else "MANEUVERING"
    _move(v,dt)


def _collision_avoidance(s: TaskForceState, flagship_e: float, flagship_n: float) -> None:
    ships = [("ENTERPRISE",flagship_e,flagship_n,None)] + [(k,v.east_nm,v.north_nm,v) for k,v in s.friendly.items() if v.hull_pct>0]
    s.closest_approach_nm = 99.0
    for i in range(len(ships)):
        for j in range(i+1,len(ships)):
            a,b=ships[i],ships[j]
            d=math.hypot(a[1]-b[1],a[2]-b[2])
            s.closest_approach_nm=min(s.closest_approach_nm,d)
            if d < 0.28:
                target = b[3] or a[3]
                if target:
                    if not target.collision_avoiding:
                        s.collision_warnings += 1
                        s.log.insert(0,f"COLLISION AVOIDANCE: {target.name} maneuvering at {d:.2f} nm separation.")
                    target.collision_avoiding=True
                    target.heading_deg=_wrap(target.heading_deg+35.0)
                    target.speed_knots=max(5.0,target.speed_knots*0.72)
            else:
                if a[3]: a[3].collision_avoiding=False
                if b[3]: b[3].collision_avoiding=False


def _advance_contact(c: FleetContact, flagship_e: float, flagship_n: float, flagship_heading: float, dt: float) -> None:
    if c.health_pct <= 0: return
    # Training threat doctrine: surface units cross the screen; submarine slowly closes to attack position.
    brg_to_flag, rng = _bearing_range(c.east_nm,c.north_nm,flagship_e,flagship_n)
    if c.contact_type == "SUBMARINE":
        if rng > 2.0:
            err=_signed(brg_to_flag-c.heading_deg); c.heading_deg=_wrap(c.heading_deg+_clamp(err,-1.6*dt,1.6*dt))
            c.speed_knots=7.0
        else:
            c.speed_knots=3.0
    else:
        desired=_wrap(flagship_heading+245.0)
        err=_signed(desired-c.heading_deg); c.heading_deg=_wrap(c.heading_deg+_clamp(err,-1.0*dt,1.0*dt))
    de,dn=_nav_vec(c.heading_deg,c.speed_knots*dt/3600.0); c.east_nm+=de; c.north_nm+=dn


def _scan(s: TaskForceState, flagship_e: float, flagship_n: float, flagship_heading: float) -> None:
    sensors=[("ENTERPRISE",flagship_e,flagship_n,30.0,14.0)]
    sensors += [(v.name,v.east_nm,v.north_nm,v.radar_range_nm*(v.sensor_pct/100),v.visual_range_nm) for v in s.friendly.values() if v.hull_pct>0]
    for c in s.contacts.values():
        if c.health_pct<=0: continue
        best=0.0; reporter=""
        for name,e,n,radar,visual in sensors:
            _,rng=_bearing_range(e,n,c.east_nm,c.north_nm)
            detect_range = min(radar, 9.0 if c.submerged else radar)
            if rng <= detect_range:
                conf=max(18.0,100.0-(rng/detect_range)*70.0)
                if c.submerged: conf*=0.65
                if conf>best: best,reporter=conf,name
            if not c.submerged and rng <= visual:
                conf=max(best,55.0+(1-rng/max(visual,.1))*40.0)
                if conf>best: best,reporter=conf,name
        if best>0:
            first=not c.detected
            c.detected=True; c.confidence=max(c.confidence,best)
            c.identified=c.confidence>=70.0
            c.last_report=f"{reporter}: {'identified' if c.identified else 'contact'} confidence {c.confidence:.0f}%"
            if first: s.log.insert(0,f"CONTACT REPORT: {c.label} detected by {reporter}.")


def engage_selected_contact(s: TaskForceState) -> Tuple[bool,str]:
    c=s.selected_contact
    if not c or not c.detected:
        return False,"No detected fleet contact selected."
    if c.contact_type=="SUBMARINE":
        escorts=[v for v in s.friendly.values() if v.vessel_type=="DESTROYER" and v.depth_charges>0 and v.hull_pct>0]
        if not escorts: return False,"No destroyer with depth charges available."
        escort=min(escorts,key=lambda v: math.hypot(v.east_nm-c.east_nm,v.north_nm-c.north_nm))
        escort.depth_charges=max(0,escort.depth_charges-6); escort.detached=True; escort.status="ASW ATTACK"; escort.last_order=f"Attack {c.key}"
        damage=30.0+0.35*c.confidence; c.health_pct=max(0.0,c.health_pct-damage)
        s.signals_sent+=1
        if c.health_pct<=0: s.submarines_defeated+=1; msg=f"{escort.name} completed simulated ASW attack; {c.label} neutralized."
        else: msg=f"{escort.name} attacking {c.label}; contact health {c.health_pct:.0f}%."
    else:
        shooters=[v for v in s.friendly.values() if ("CRUISER" in v.vessel_type or v.vessel_type=="DESTROYER") and v.surface_salvos>0 and v.hull_pct>0]
        if not shooters:return False,"No escort has surface-fire ammunition available."
        shooter=min(shooters,key=lambda v: math.hypot(v.east_nm-c.east_nm,v.north_nm-c.north_nm))
        shooter.surface_salvos-=1; shooter.detached=True; shooter.status="SURFACE ENGAGEMENT"; shooter.last_order=f"Engage {c.key}"
        damage=18.0+0.25*c.confidence; c.health_pct=max(0.0,c.health_pct-damage)
        s.signals_sent+=1
        if c.health_pct<=0: s.surface_contacts_defeated+=1; msg=f"{shooter.name} reports simulated surface target {c.label} neutralized."
        else: msg=f"{shooter.name} fires on {c.label}; contact health {c.health_pct:.0f}%."
    s.log.insert(0,"FLEET ENGAGEMENT: "+msg)
    return True,msg


def begin_replenishment(s: TaskForceState, selected_key: Optional[str]=None) -> Tuple[bool,str]:
    if s.logistics.transfer_in_progress: return False,"Fleet replenishment transfer already in progress."
    v=s.friendly.get(selected_key) if selected_key else s.selected_friendly
    if not v:return False,"No receiving ship selected."
    if v.hull_pct<=0:return False,"Selected ship cannot receive replenishment."
    s.logistics.transfer_in_progress=True; s.logistics.transfer_target=v.key; s.logistics.transfer_progress=0.0
    v.replenishing=True; v.status="REPLENISHMENT RENDEZVOUS"
    s.log.insert(0,f"LOGISTICS TRAINING: {v.name} ordered to replenishment rendezvous. Transfer quantities are simulation values.")
    return True,f"Replenishment evolution started for {v.name}."


def advance_task_force(s: TaskForceState, physics, dt: float) -> List[str]:
    msgs: List[str]=[]
    s._elapsed_s += dt
    flagship_e,flagship_n,flagship_h,flagship_speed=physics.east_nm,physics.north_nm,physics.heading_deg,max(0.0,physics.speed_knots)
    for v in s.friendly.values():
        _formation_ai(v,flagship_e,flagship_n,flagship_h,flagship_speed,dt)
        # Fuel burn is intentionally calibrated for gameplay, not an archival endurance curve.
        v.fuel_pct=max(0.0,v.fuel_pct-(v.speed_knots/max(v.max_speed_knots,1))**2*0.0018*dt)
        if v.fuel_pct<10: v.status="LOW FUEL"
    _collision_avoidance(s,flagship_e,flagship_n)
    if s.training_problem_active:
        for c in s.contacts.values(): _advance_contact(c,flagship_e,flagship_n,flagship_h,dt)
        _scan(s,flagship_e,flagship_n,flagship_h)
        # Threats may make simulated attacks if allowed to penetrate the screen.
        s._attack_accum_s += dt
        if s._attack_accum_s>=8.0:
            s._attack_accum_s=0.0
            for c in s.contacts.values():
                if c.health_pct<=0: continue
                _,rng=_bearing_range(c.east_nm,c.north_nm,flagship_e,flagship_n)
                if c.contact_type=="SUBMARINE" and rng<1.4 and not c.attacked:
                    c.attacked=True
                    escorts=[v for v in s.friendly.values() if v.hull_pct>0]
                    if escorts:
                        target=min(escorts,key=lambda v: math.hypot(v.east_nm-c.east_nm,v.north_nm-c.north_nm))
                        target.hull_pct=max(0.0,target.hull_pct-18.0); target.propulsion_pct=max(25.0,target.propulsion_pct-12.0); target.status="SIM TORPEDO DAMAGE"
                        s.escort_damage_events+=1
                        msgs.append(f"SIM SUBMARINE ATTACK — {target.name} reports training torpedo damage after the submarine penetrated the screen.")
                    else:
                        msgs.append("SIM SUBMARINE ATTACK WARNING — hostile training submarine reached firing position inside the screen.")
                    s.log.insert(0,msgs[-1]); s.fleet_alert="URGENT"
                elif c.contact_type=="SURFACE" and rng<5.0 and not c.attacked:
                    c.attacked=True
                    escorts=[v for v in s.friendly.values() if v.hull_pct>0]
                    if escorts:
                        target=min(escorts,key=lambda v: math.hypot(v.east_nm-c.east_nm,v.north_nm-c.north_nm))
                        target.hull_pct=max(0.0,target.hull_pct-10.0); target.sensor_pct=max(30.0,target.sensor_pct-8.0); target.status="SIM SURFACE-FIRE DAMAGE"
                        s.escort_damage_events+=1
                        msgs.append(f"SIM SURFACE FIRE — {c.label} damages {target.name} after penetrating to {rng:.1f} nm.")
                    else:
                        msgs.append(f"SIM SURFACE FIRE WARNING — {c.label} has penetrated to {rng:.1f} nm.")
                    s.log.insert(0,msgs[-1]); s.fleet_alert="URGENT"
        if all(c.health_pct<=0 for c in s.contacts.values()):
            s.training_problem_active=False; s.fleet_alert="ROUTINE"
            msgs.append("FLEET TRAINING PROBLEM COMPLETE — all simulated hostile contacts neutralized.")
            s.log.insert(0,msgs[-1])
    if s.logistics.transfer_in_progress:
        key=s.logistics.transfer_target; v=s.friendly.get(key)
        if not v:
            s.logistics.transfer_in_progress=False
        else:
            _,rng=_bearing_range(v.east_nm,v.north_nm,flagship_e,flagship_n)
            if rng>0.45:
                v.desired_bearing_deg=270.0; v.desired_range_nm=0.22; v.detached=False
            elif flagship_speed>12.0:
                msgs.append("Replenishment transfer paused — flagship speed must be 12 knots or less.")
            else:
                s.logistics.transfer_progress=min(100.0,s.logistics.transfer_progress+dt*4.0)
                if s.logistics.transfer_progress>=100.0:
                    v.fuel_pct=min(100.0,v.fuel_pct+30.0); v.ammo_pct=min(100.0,v.ammo_pct+25.0)
                    v.replenishing=False; v.detached=False; v.status="FORMATION"; v.last_order=f"Resume {s.formation} station"
                    s.logistics.transfer_in_progress=False; s.logistics.replenishments+=1
                    msgs.append(f"Replenishment complete for {v.name}; fuel and ammunition stores increased.")
                    s.log.insert(0,msgs[-1])
    s.miles_steamed += flagship_speed*dt/3600.0
    s.log=s.log[:180]
    return msgs


def task_force_summary(s: TaskForceState, physics=None) -> str:
    in_station=sum(1 for v in s.friendly.values() if v.in_station)
    damaged=sum(1 for v in s.friendly.values() if v.hull_pct<99.9)
    detected=sum(1 for c in s.contacts.values() if c.detected and c.health_pct>0)
    active=sum(1 for c in s.contacts.values() if c.health_pct>0)
    return (f"TF16 {s.formation} • {in_station}/{len(s.friendly)} escorts in station • closest {s.closest_approach_nm:.2f}nm • "
            f"contacts {detected}/{active} • escorts damaged {damaged} • fleet alert {s.fleet_alert}")


def friendly_lines(s: TaskForceState, flagship_e: float, flagship_n: float) -> List[str]:
    out=[]
    for v in s.friendly.values():
        brg,rng=_bearing_range(flagship_e,flagship_n,v.east_nm,v.north_nm)
        out.append(f"{v.name:<22} {v.vessel_type:<18} BRG {brg:03.0f}° {rng:4.1f}nm  {v.speed_knots:4.1f}kt  fuel {v.fuel_pct:3.0f}%  hull {v.hull_pct:3.0f}%  {v.status}")
    return out


def contact_lines(s: TaskForceState, flagship_e: float, flagship_n: float) -> List[str]:
    out=[]
    for c in s.contacts.values():
        brg,rng=_bearing_range(flagship_e,flagship_n,c.east_nm,c.north_nm)
        status="DESTROYED" if c.health_pct<=0 else ("ID" if c.identified else "TRACK" if c.detected else "UNDETECTED")
        out.append(f"{c.key:<16} {c.contact_type:<10} BRG {brg:03.0f}° {rng:4.1f}nm  {status:<10} conf {c.confidence:3.0f}%  health {c.health_pct:3.0f}%")
    return out or ["No fleet contacts in the training sea room."]


def logistics_lines(s: TaskForceState) -> List[str]:
    l=s.logistics
    line=f"Fleet logistics: bunker {l.bunker_fuel_pct:.0f}% • aviation {l.aviation_fuel_pct:.0f}% • ammo {l.ammunition_pct:.0f}% • food {l.food_pct:.0f}% • repair stores {l.repair_stores_pct:.0f}%"
    if l.transfer_in_progress: line += f" • transfer {l.transfer_target} {l.transfer_progress:.0f}%"
    return [line, f"Replenishments completed {l.replenishments} • signal method {s.signal_method} • signals sent {s.signals_sent}"]


def task_force_to_dict(s: TaskForceState) -> dict:
    return asdict(s)


def task_force_from_dict(data: dict, flagship_e: float=0.0, flagship_n: float=0.0, flagship_heading: float=90.0) -> TaskForceState:
    if not isinstance(data,dict) or not data:
        return create_task_force(flagship_e,flagship_n,flagship_heading)
    base=create_task_force(flagship_e,flagship_n,flagship_heading)
    for k,v in data.items():
        if k in ("friendly","contacts","logistics"): continue
        if hasattr(base,k): setattr(base,k,v)
    fr=data.get("friendly",{})
    if isinstance(fr,dict):
        for k,raw in fr.items():
            if isinstance(raw,dict):
                allowed=FleetVessel.__dataclass_fields__.keys(); vals={a:b for a,b in raw.items() if a in allowed}
                try: base.friendly[k]=FleetVessel(**vals)
                except TypeError: pass
    base.contacts={}
    co=data.get("contacts",{})
    if isinstance(co,dict):
        for k,raw in co.items():
            if isinstance(raw,dict):
                allowed=FleetContact.__dataclass_fields__.keys(); vals={a:b for a,b in raw.items() if a in allowed}
                try: base.contacts[k]=FleetContact(**vals)
                except TypeError: pass
    lo=data.get("logistics",{})
    if isinstance(lo,dict):
        allowed=FleetLogistics.__dataclass_fields__.keys(); vals={a:b for a,b in lo.items() if a in allowed}
        try: base.logistics=FleetLogistics(**vals)
        except TypeError: pass
    return base
