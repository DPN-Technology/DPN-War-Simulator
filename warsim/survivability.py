from __future__ import annotations

"""War Simulator v1.1 structural damage and ship-survivability layer.

All penetration, blast, flooding and structural coefficients are gameplay/training calibration.
They are not represented as exact archival USS Enterprise (CV-6) armor tests or a claim that the
simulated casualty occurred during the Battle of Midway. Historical scenarios remain separately
sourced/locked; this module supplies reusable physical consequences for combat and training.
"""

from dataclasses import dataclass, field, asdict
import math
from typing import Dict, List, Optional, Tuple


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


@dataclass
class DamageCompartment:
    key: str
    name: str
    deck: str
    side: str
    longitudinal: float  # -1 bow .. +1 stern
    transverse: float    # -1 port .. +1 starboard
    resistance: float
    structural: float = 100.0
    fire: float = 0.0
    smoke: float = 0.0
    flooding: float = 0.0
    breach_area_m2: float = 0.0
    temperature_c: float = 24.0
    oxygen_pct: float = 21.0
    wounded: int = 0
    dead: int = 0
    isolated: bool = False
    ventilation: bool = True
    dewatering: bool = False
    fire_team: bool = False
    shored: bool = False
    patched: bool = False
    magazine: bool = False
    machinery: bool = False
    medical: bool = False


@dataclass
class DamageBoundary:
    key: str
    a: str
    b: str
    watertight: bool = True
    open: bool = True
    integrity: float = 100.0


@dataclass
class SurvivabilityState:
    compartments: Dict[str, DamageCompartment] = field(default_factory=dict)
    boundaries: Dict[str, DamageBoundary] = field(default_factory=dict)
    selected_compartment: str = "HANGAR_MID"
    elapsed_seconds: float = 0.0
    total_flooding_tons: float = 0.0
    list_deg: float = 0.0
    trim_deg: float = 0.0
    buoyancy_pct: float = 100.0
    stability_pct: float = 100.0
    structural_strength_pct: float = 100.0
    firemain_pct: float = 100.0
    pump_capacity_pct: float = 100.0
    magazine_risk_pct: float = 0.0
    wounded_total: int = 0
    dead_total: int = 0
    medical_load_pct: float = 0.0
    damage_control_readiness: float = 88.0
    abandon_ship_ordered: bool = False
    evacuation_progress_pct: float = 0.0
    sinking: bool = False
    sunk: bool = False
    sink_depth_m: float = 0.0
    catastrophic_failure: bool = False
    casualties_treated: int = 0
    breaches_patched: int = 0
    fires_extinguished: int = 0
    shoring_actions: int = 0
    log: List[str] = field(default_factory=lambda: [
        "Survivability system initialized. Combat damage uses training-calibrated structural physics."
    ])


# Coarse zones map onto the existing seamless carrier spaces. This is intentionally a training
# structural model rather than an exact compartment-by-compartment CV-6 damage-control book.
COMPARTMENTS = [
    ("FLIGHT_FWD", "Forward Flight Deck", "FLIGHT", "CENTER", -0.80, 0.0, 50, False, False, False),
    ("FLIGHT_MID", "Midships Flight Deck", "FLIGHT", "CENTER", -0.10, 0.0, 52, False, False, False),
    ("FLIGHT_AFT", "Aft Flight Deck", "FLIGHT", "CENTER", 0.75, 0.0, 48, False, False, False),
    ("ISLAND", "Island / Command Spaces", "ISLAND", "STARBOARD", -0.05, 0.72, 42, False, False, False),
    ("HANGAR_FWD", "Forward Hangar Bay", "HANGAR", "CENTER", -0.68, 0.0, 38, False, False, False),
    ("HANGAR_MID", "Midships Hangar Bay", "HANGAR", "CENTER", -0.05, 0.0, 38, False, False, False),
    ("HANGAR_AFT", "Aft Hangar Bay", "HANGAR", "CENTER", 0.63, 0.0, 38, False, False, False),
    ("PORT_MACH", "Port Machinery Spaces", "ENGINEERING", "PORT", 0.18, -0.58, 62, False, True, False),
    ("STBD_MACH", "Starboard Machinery Spaces", "ENGINEERING", "STARBOARD", 0.18, 0.58, 62, False, True, False),
    ("FWD_MAG", "Forward Magazine Group", "LOWER", "CENTER", -0.55, 0.0, 72, True, False, False),
    ("AFT_MAG", "Aft Magazine Group", "LOWER", "CENTER", 0.55, 0.0, 72, True, False, False),
    ("SICKBAY", "Sickbay / Medical", "LOWER", "PORT", -0.10, -0.48, 40, False, False, True),
    ("PORT_VOID", "Port Lower Hull", "LOWER", "PORT", 0.0, -0.90, 58, False, False, False),
    ("STBD_VOID", "Starboard Lower Hull", "LOWER", "STARBOARD", 0.0, 0.90, 58, False, False, False),
    ("STEERING", "Steering Gear / Aft Hull", "LOWER", "CENTER", 0.90, 0.0, 60, False, True, False),
]

BOUNDARIES = [
    ("B01", "FLIGHT_FWD", "FLIGHT_MID", False), ("B02", "FLIGHT_MID", "FLIGHT_AFT", False),
    ("B03", "FLIGHT_MID", "ISLAND", False),
    ("B04", "FLIGHT_FWD", "HANGAR_FWD", True), ("B05", "FLIGHT_MID", "HANGAR_MID", True),
    ("B06", "FLIGHT_AFT", "HANGAR_AFT", True),
    ("B07", "HANGAR_FWD", "HANGAR_MID", False), ("B08", "HANGAR_MID", "HANGAR_AFT", False),
    ("B09", "HANGAR_FWD", "FWD_MAG", True), ("B10", "HANGAR_MID", "PORT_MACH", True),
    ("B11", "HANGAR_MID", "STBD_MACH", True), ("B12", "HANGAR_AFT", "AFT_MAG", True),
    ("B13", "PORT_MACH", "PORT_VOID", True), ("B14", "STBD_MACH", "STBD_VOID", True),
    ("B15", "PORT_MACH", "STBD_MACH", True), ("B16", "PORT_VOID", "SICKBAY", True),
    ("B17", "STBD_VOID", "STEERING", True), ("B18", "AFT_MAG", "STEERING", True),
]


def create_survivability() -> SurvivabilityState:
    s = SurvivabilityState()
    s.compartments = {
        k: DamageCompartment(k,n,d,side,longitudinal,transverse,resistance,
                             magazine=mag,machinery=mach,medical=med)
        for k,n,d,side,longitudinal,transverse,resistance,mag,mach,med in COMPARTMENTS
    }
    s.boundaries = {k: DamageBoundary(k,a,b,wt,True,100.0) for k,a,b,wt in BOUNDARIES}
    recalculate(s)
    return s


def _neighbors(s: SurvivabilityState, key: str):
    for b in s.boundaries.values():
        if b.a == key:
            yield b, b.b
        elif b.b == key:
            yield b, b.a


def cycle_compartment(s: SurvivabilityState) -> DamageCompartment:
    keys = list(s.compartments)
    if s.selected_compartment not in keys:
        s.selected_compartment = keys[0]
    else:
        s.selected_compartment = keys[(keys.index(s.selected_compartment)+1)%len(keys)]
    return s.compartments[s.selected_compartment]


def selected_compartment(s: SurvivabilityState) -> DamageCompartment:
    if s.selected_compartment not in s.compartments:
        s.selected_compartment = next(iter(s.compartments))
    return s.compartments[s.selected_compartment]


def toggle_boundary_for_selected(s: SurvivabilityState) -> Tuple[bool,str]:
    c = selected_compartment(s)
    candidates=[b for b,_ in _neighbors(s,c.key) if b.watertight and b.integrity>10]
    if not candidates:
        return False, f"No operable watertight boundary adjacent to {c.name}."
    b=next((x for x in candidates if x.open), candidates[0])
    b.open=not b.open
    msg=f"{b.key} {'OPEN' if b.open else 'SHUT'} around {c.name}."
    s.log.insert(0,msg)
    return True,msg


def _impact_target(s: SurvivabilityState, zone: Optional[str], attack_type: str, side: str) -> DamageCompartment:
    if zone in s.compartments:
        return s.compartments[zone]
    atk=attack_type.upper()
    if "TORPEDO" in atk:
        key="PORT_VOID" if side.upper()=="PORT" else "STBD_VOID"
    elif "DIVE" in atk or "BOMB" in atk:
        key="FLIGHT_MID" if side.upper()=="CENTER" else ("HANGAR_FWD" if side.upper()=="PORT" else "HANGAR_AFT")
    elif "SHELL" in atk:
        key="PORT_MACH" if side.upper()=="PORT" else "STBD_MACH"
    else:
        key="HANGAR_MID"
    return s.compartments[key]


def apply_impact(s: SurvivabilityState, attack_type: str, severity: float,
                 zone: Optional[str]=None, side: str="STARBOARD") -> str:
    """Apply a localized training impact and return an event description."""
    c=_impact_target(s,zone,attack_type,side)
    sev=clamp(severity,1.0,100.0)
    penetration=max(0.0, sev - c.resistance*0.42)
    blast=sev*(0.50 + penetration/180.0)
    c.structural=max(0.0,c.structural-blast)
    atk=attack_type.upper()
    if "TORPEDO" in atk:
        c.breach_area_m2 += 0.15 + sev*0.012
        c.flooding = clamp(c.flooding + 10 + sev*.38,0,100)
        c.fire = clamp(c.fire + sev*.12,0,100)
    elif "DIVE" in atk or "BOMB" in atk:
        c.fire=clamp(c.fire+18+sev*.45,0,100)
        c.smoke=clamp(c.smoke+14+sev*.32,0,100)
        if c.deck in ("HANGAR","LOWER") or penetration>15:
            c.breach_area_m2 += sev*.0025
    else:
        c.fire=clamp(c.fire+sev*.22,0,100)
        c.smoke=clamp(c.smoke+sev*.18,0,100)
        if penetration>20: c.breach_area_m2 += sev*.003
    c.temperature_c += c.fire*.35
    wounded=max(0,int(sev/18 + (2 if c.fire>45 else 0)))
    dead=max(0,int((sev-62)/22))
    c.wounded += wounded; c.dead += dead
    if c.magazine:
        s.magazine_risk_pct=clamp(s.magazine_risk_pct+sev*.5+c.fire*.3,0,100)
    s.selected_compartment=c.key
    recalculate(s)
    msg=(f"SIMULATED STRUCTURAL HIT — {attack_type.replace('_',' ')} at {c.name}: "
         f"structure {c.structural:.0f}%, fire {c.fire:.0f}%, flooding {c.flooding:.0f}%, "
         f"breach {c.breach_area_m2:.2f} m², casualties {wounded+dead}.")
    s.log.insert(0,msg)
    return msg


def fight_fire(s: SurvivabilityState) -> Tuple[bool,str]:
    c=selected_compartment(s)
    if c.fire<=0.5:
        return False,f"{c.name}: no significant fire to attack."
    c.fire_team=True
    msg=f"Fire party committed to {c.name}. Fire attack and boundary cooling underway."
    s.log.insert(0,msg); return True,msg


def start_dewatering(s: SurvivabilityState) -> Tuple[bool,str]:
    c=selected_compartment(s)
    if c.flooding<=0.5 and c.breach_area_m2<=0.01:
        return False,f"{c.name}: no flooding casualty requiring dewatering."
    if s.pump_capacity_pct<15:
        return False,"Dewatering unavailable: pump capacity critically degraded."
    c.dewatering=True
    msg=f"Dewatering rigged to {c.name}."
    s.log.insert(0,msg); return True,msg


def patch_breach(s: SurvivabilityState) -> Tuple[bool,str]:
    c=selected_compartment(s)
    if c.breach_area_m2<=0.01:
        return False,f"{c.name}: no hull breach requiring patching."
    if c.fire>55:
        return False,f"{c.name}: breach team cannot work through uncontrolled fire."
    c.patched=True
    c.shored=True
    s.breaches_patched += 1
    s.shoring_actions += 1
    msg=f"Collision mat/patch and shoring applied at {c.name}; ingress rate reduced."
    s.log.insert(0,msg); return True,msg


def shore_structure(s: SurvivabilityState) -> Tuple[bool,str]:
    c=selected_compartment(s)
    if c.structural>92:
        return False,f"{c.name}: structural condition does not require shoring."
    c.shored=True; s.shoring_actions += 1
    msg=f"Emergency shoring installed at {c.name}. Progressive structural failure slowed."
    s.log.insert(0,msg); return True,msg


def secure_ventilation(s: SurvivabilityState) -> Tuple[bool,str]:
    c=selected_compartment(s); c.ventilation=not c.ventilation
    msg=f"{c.name} ventilation {'RESTORED' if c.ventilation else 'SECURED'}."
    s.log.insert(0,msg); return True,msg


def treat_casualties(s: SurvivabilityState) -> Tuple[bool,str]:
    wounded=sum(c.wounded for c in s.compartments.values())
    if wounded<=0:
        return False,"Medical reports no untreated wounded."
    treated=min(wounded, max(1,int(6*(100-s.medical_load_pct)/100)+1))
    left=treated
    for c in sorted(s.compartments.values(),key=lambda x:x.wounded, reverse=True):
        take=min(c.wounded,left); c.wounded-=take; left-=take
        if left<=0: break
    s.casualties_treated += treated
    recalculate(s)
    msg=f"Medical teams treated {treated} wounded; remaining untreated wounded {sum(c.wounded for c in s.compartments.values())}."
    s.log.insert(0,msg); return True,msg


def order_abandon_ship(s: SurvivabilityState) -> Tuple[bool,str]:
    if s.abandon_ship_ordered:
        return False,"Abandon-ship order is already in effect."
    s.abandon_ship_ordered=True
    msg="ABANDON SHIP ORDERED — muster, casualty evacuation, flotation gear and survival stations activated."
    s.log.insert(0,msg); return True,msg



def muster_abandon_ship(s: SurvivabilityState) -> Tuple[bool,str]:
    if not s.abandon_ship_ordered:
        return False,"Abandon-ship muster is not active. The order has not been given."
    if s.evacuation_progress_pct >= 100:
        return True,"Abandon-ship muster complete; all simulated survivors accounted for."
    gain=max(4.0,10.0-s.medical_load_pct*.03)
    s.evacuation_progress_pct=clamp(s.evacuation_progress_pct+gain,0,100)
    msg=f"Muster station processed survival gear and personnel; evacuation {s.evacuation_progress_pct:.0f}% complete."
    s.log.insert(0,msg); return True,msg

def recalculate(s: SurvivabilityState) -> None:
    comps=list(s.compartments.values())
    s.total_flooding_tons=sum(c.flooding*(1.4 if c.deck=="LOWER" else .5) for c in comps)
    side_moment=sum(c.flooding*c.transverse for c in comps)
    long_moment=sum(c.flooding*c.longitudinal for c in comps)
    s.list_deg=clamp(side_moment/38.0,-28,28)
    s.trim_deg=clamp(long_moment/55.0,-16,16)
    lower_flood=sum(c.flooding for c in comps if c.deck in ("LOWER","ENGINEERING"))
    s.buoyancy_pct=clamp(100.0-lower_flood*.16-s.total_flooding_tons*.035,0,100)
    weak=sum(max(0,55-c.structural) for c in comps)
    s.structural_strength_pct=clamp(sum(c.structural for c in comps)/len(comps)-weak*.018,0,100)
    s.stability_pct=clamp(100-abs(s.list_deg)*2.7-abs(s.trim_deg)*1.5-lower_flood*.055,0,100)
    s.wounded_total=sum(c.wounded for c in comps)
    s.dead_total=sum(c.dead for c in comps)
    s.medical_load_pct=clamp(s.wounded_total*5+s.dead_total*2,0,100)
    mag=max((c.fire+c.temperature_c/4+c.structural*-0.05 for c in comps if c.magazine),default=0)
    s.magazine_risk_pct=clamp(max(s.magazine_risk_pct*.992,mag),0,100)
    machinery=[c for c in comps if c.machinery]
    s.pump_capacity_pct=clamp(100-sum(c.flooding*.22+max(0,45-c.structural)*.7 for c in machinery),5,100)
    s.firemain_pct=clamp(100-sum(c.fire*.08+max(0,35-c.structural)*.5 for c in machinery),10,100)
    if s.buoyancy_pct<22 or s.stability_pct<18 or s.structural_strength_pct<20:
        s.sinking=True
    if s.magazine_risk_pct>=96:
        s.catastrophic_failure=True; s.sinking=True
    if s.sunk:
        s.sinking=True


def survivability_tick(s: SurvivabilityState, dt: float) -> List[str]:
    dt=clamp(dt,.01,.5); s.elapsed_seconds+=dt; messages=[]
    # Primary compartment evolution.
    for c in s.compartments.values():
        # Progressive ingress. A patch reduces but does not instantly erase flooding.
        if c.breach_area_m2>0.001:
            ingress=(c.breach_area_m2*3.3)*(0.18 if c.patched else 1.0)
            c.flooding=clamp(c.flooding+ingress*dt,0,100)
        if c.dewatering and c.flooding>0:
            pump=(2.8*(s.pump_capacity_pct/100.0))*dt
            c.flooding=max(0,c.flooding-pump)
            if c.flooding<=.2 and c.breach_area_m2<=.02: c.dewatering=False
        if c.fire>0:
            suppression=(4.4 if c.fire_team else .25)*(s.firemain_pct/100.0)*dt
            oxygen_factor=clamp(c.oxygen_pct/21,0.25,1.0)
            growth=(.30 if c.ventilation else .08)*oxygen_factor*dt
            old=c.fire; c.fire=clamp(c.fire+growth-suppression,0,100)
            c.smoke=clamp(c.smoke+c.fire*.014*dt-(.55 if c.ventilation else .12)*dt,0,100)
            c.temperature_c=max(22,c.temperature_c+c.fire*.025*dt-(1.5 if c.fire_team else .15)*dt)
            if old>2 and c.fire<=1:
                c.fire_team=False; s.fires_extinguished+=1
                messages.append(f"Fire extinguished in {c.name}.")
        c.oxygen_pct=clamp(21-c.smoke*.07-c.fire*.025,8,21)
        if c.fire>65 and c.structural<55 and not c.shored:
            c.structural=max(0,c.structural-.12*dt)
        elif c.shored and c.structural<95:
            c.structural=min(95,c.structural+.03*dt)

    # Smoke/fire/flood propagation across boundaries.
    deltas={k:[0.0,0.0,0.0] for k in s.compartments}
    for b in s.boundaries.values():
        a,bcomp=s.compartments[b.a],s.compartments[b.b]
        open_factor=1.0 if b.open else (0.04 if b.watertight else .18)
        if b.integrity<35: open_factor=max(open_factor,.55)
        fire_source,fire_dest=(a,bcomp) if a.fire>bcomp.fire else (bcomp,a)
        if fire_source.fire>35:
            deltas[fire_dest.key][0]+=fire_source.fire*.004*open_factor*dt
        smoke_source,smoke_dest=(a,bcomp) if a.smoke>bcomp.smoke else (bcomp,a)
        deltas[smoke_dest.key][1]+=max(0,smoke_source.smoke-smoke_dest.smoke)*.018*open_factor*dt
        flood_source,flood_dest=(a,bcomp) if a.flooding>bcomp.flooding else (bcomp,a)
        if flood_source.flooding>18:
            flood_factor=open_factor if b.watertight else max(open_factor,.35)
            deltas[flood_dest.key][2]+=max(0,flood_source.flooding-flood_dest.flooding)*.008*flood_factor*dt
    for k,(df,ds,dw) in deltas.items():
        c=s.compartments[k]; c.fire=clamp(c.fire+df,0,100); c.smoke=clamp(c.smoke+ds,0,100); c.flooding=clamp(c.flooding+dw,0,100)

    recalculate(s)
    if s.sinking:
        rate=clamp((30-s.buoyancy_pct)*.012+(22-s.stability_pct)*.008+(25-s.structural_strength_pct)*.006,.02,1.6)
        s.sink_depth_m += rate*dt
        if not s.abandon_ship_ordered and (s.buoyancy_pct<15 or s.stability_pct<12):
            messages.append("CAPTAIN'S WARNING: survivability margin critical; consider abandon ship.")
        if s.sink_depth_m>=12:
            s.sunk=True; messages.append("SIMULATED LOSS OF SHIP — vessel no longer has recoverable buoyancy/stability.")
    if s.abandon_ship_ordered:
        progress=(1.1 + s.damage_control_readiness*.012)*dt
        if s.sinking: progress*=1.15
        s.evacuation_progress_pct=clamp(s.evacuation_progress_pct+progress,0,100)
    for m in messages: s.log.insert(0,m)
    return messages


def operational_factors(s: SurvivabilityState) -> Dict[str,float]:
    mach=[c for c in s.compartments.values() if c.machinery]
    machinery=min((c.structural-c.flooding*.35-c.fire*.25 for c in mach),default=100)
    steering=s.compartments["STEERING"]
    island=s.compartments["ISLAND"]
    return {
        "propulsion": clamp(machinery,5,100),
        "steering": clamp(steering.structural-steering.flooding*.3-steering.fire*.2,5,100),
        "combat": clamp(island.structural-island.fire*.25-island.smoke*.12,5,100),
        "aviation": clamp(min(s.compartments["FLIGHT_MID"].structural,s.compartments["HANGAR_MID"].structural)-s.compartments["FLIGHT_MID"].fire*.2,5,100),
    }


def casualty_summary(s: SurvivabilityState) -> str:
    active_fire=sum(1 for c in s.compartments.values() if c.fire>5)
    flooded=sum(1 for c in s.compartments.values() if c.flooding>5)
    breached=sum(1 for c in s.compartments.values() if c.breach_area_m2>.01)
    status="SUNK" if s.sunk else "SINKING" if s.sinking else "CRITICAL" if min(s.buoyancy_pct,s.stability_pct,s.structural_strength_pct)<40 else "DAMAGED" if active_fire or flooded else "STABLE"
    return (f"{status} • buoyancy {s.buoyancy_pct:.0f}% • stability {s.stability_pct:.0f}% • structure {s.structural_strength_pct:.0f}% • "
            f"list {s.list_deg:+.1f}° • trim {s.trim_deg:+.1f}° • fires {active_fire} • flooded {flooded} • breaches {breached} • "
            f"wounded {s.wounded_total} / dead {s.dead_total} • magazine risk {s.magazine_risk_pct:.0f}%")


def compartment_lines(s: SurvivabilityState) -> List[str]:
    out=[]
    for c in s.compartments.values():
        flags=[]
        if c.fire>5: flags.append(f"FIRE {c.fire:.0f}")
        if c.flooding>5: flags.append(f"FLOOD {c.flooding:.0f}")
        if c.breach_area_m2>.01: flags.append(f"BREACH {c.breach_area_m2:.2f}m²")
        if c.wounded or c.dead: flags.append(f"CAS {c.wounded}W/{c.dead}K")
        if c.patched: flags.append("PATCHED")
        if c.shored: flags.append("SHORED")
        out.append(f"{'> ' if c.key==s.selected_compartment else '  '}{c.name}: STR {c.structural:.0f}%" + (" • "+" • ".join(flags) if flags else " • clear"))
    return out


def survivability_to_dict(s: SurvivabilityState) -> dict:
    return asdict(s)


def survivability_from_dict(data: Optional[dict]) -> SurvivabilityState:
    s=create_survivability()
    if not isinstance(data,dict) or not data: return s
    scalar_fields=[k for k in SurvivabilityState.__dataclass_fields__ if k not in ("compartments","boundaries","log")]
    for k in scalar_fields:
        if k in data: setattr(s,k,data[k])
    for key,raw in data.get("compartments",{}).items():
        if key not in s.compartments or not isinstance(raw,dict): continue
        for f in DamageCompartment.__dataclass_fields__:
            if f in raw: setattr(s.compartments[key],f,raw[f])
    for key,raw in data.get("boundaries",{}).items():
        if key not in s.boundaries or not isinstance(raw,dict): continue
        for f in DamageBoundary.__dataclass_fields__:
            if f in raw: setattr(s.boundaries[key],f,raw[f])
    s.log=list(data.get("log",s.log))[:120]
    recalculate(s)
    return s
