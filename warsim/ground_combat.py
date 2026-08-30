from __future__ import annotations

"""v2.0 first-person combined-arms ground combat training layer.

This module is deliberately a GAME/TRAINING abstraction. Weapon performance, unit names,
casualty rates, cover values, support effects and training-village geometry are not presented as
historical combat data. The locked historical scenario layer remains separate.
"""

from dataclasses import dataclass, field, asdict
import math
from typing import Dict, List, Optional, Tuple


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _angle_diff(a: float, b: float) -> float:
    return ((a - b + 180.0) % 360.0) - 180.0


def _bearing(x0: float, y0: float, x1: float, y1: float) -> float:
    return math.degrees(math.atan2(y1-y0, x1-x0)) % 360.0


@dataclass
class InfantryWeapon:
    key: str
    name: str
    role: str
    magazine_capacity: int
    magazine_rounds: int
    reserve_rounds: int
    effective_range_m: float
    accuracy: float
    damage: float
    suppression: float
    fire_interval: float
    reload_seconds: float
    automatic: bool = False


@dataclass
class FireteamMember:
    key: str
    name: str
    role: str
    x: float
    y: float
    health: float = 100.0
    suppression: float = 0.0
    morale: float = 82.0
    ammo_pct: float = 100.0
    status: str = "READY"
    order: str = "FOLLOW"
    target_x: float = 0.0
    target_y: float = 0.0
    wounded: bool = False


@dataclass
class GroundContact:
    key: str
    label: str
    x: float
    y: float
    health: float = 100.0
    suppression: float = 0.0
    cover_pct: float = 35.0
    confidence: float = 0.0
    identified: bool = False
    status: str = "HIDDEN"
    role: str = "RIFLE"
    last_seen_seconds: float = 0.0


@dataclass
class GroundObjective:
    key: str
    title: str
    x: float
    y: float
    radius_m: float
    status: str = "PENDING"
    progress_seconds: float = 0.0
    required_seconds: float = 8.0
    description: str = ""


@dataclass
class InfantryPlayer:
    active: bool = False
    health: float = 100.0
    stamina: float = 100.0
    suppression: float = 0.0
    stance: str = "STANDING"
    aiming: bool = False
    selected_weapon: str = "RIFLE"
    reload_remaining: float = 0.0
    fire_cooldown: float = 0.0
    first_aid_kits: int = 2
    wounded: bool = False
    weapon_heat: float = 0.0
    shots_fired: int = 0
    hits: int = 0
    damage_taken: float = 0.0


@dataclass
class GroundCombatState:
    player: InfantryPlayer = field(default_factory=InfantryPlayer)
    weapons: Dict[str, InfantryWeapon] = field(default_factory=dict)
    squad: Dict[str, FireteamMember] = field(default_factory=dict)
    contacts: Dict[str, GroundContact] = field(default_factory=dict)
    objectives: Dict[str, GroundObjective] = field(default_factory=dict)
    selected_contact_index: int = 0
    selected_squad_index: int = 0
    selected_order: str = "FOLLOW"
    elapsed: float = 0.0
    engagement_active: bool = False
    engagement_complete: bool = False
    engagement_failed: bool = False
    score: float = 100.0
    enemies_neutralized: int = 0
    squad_wounded: int = 0
    supports_called: int = 0
    air_support_used: float = 0.0
    naval_support_used: float = 0.0
    casualties_treated: int = 0
    engagements_completed: int = 0
    training_losses: int = 0
    last_event: str = "v2.0 combined-arms ground combat initialized."
    log: List[str] = field(default_factory=list)
    last_tracer_target: str = ""
    muzzle_flash_seconds: float = 0.0
    support_cooldown: float = 0.0

    @property
    def selected_contact(self) -> Optional[GroundContact]:
        vals=[c for c in self.contacts.values() if c.health>0]
        return vals[self.selected_contact_index % len(vals)] if vals else None

    @property
    def selected_squad(self) -> Optional[FireteamMember]:
        vals=list(self.squad.values())
        return vals[self.selected_squad_index % len(vals)] if vals else None

    @property
    def active_objective(self) -> Optional[GroundObjective]:
        for o in self.objectives.values():
            if o.status in ("ACTIVE","PENDING"):
                return o
        return None


def create_ground_combat() -> GroundCombatState:
    s=GroundCombatState()
    s.weapons={
        "RIFLE": InfantryWeapon("RIFLE","Service Rifle","RIFLE",20,20,100,220.0,.78,34.0,18.0,.22,2.3,False),
        "AUTO": InfantryWeapon("AUTO","Automatic Rifle","SUPPORT",30,30,120,180.0,.66,24.0,31.0,.11,3.1,True),
        "SIDEARM": InfantryWeapon("SIDEARM","Service Sidearm","SIDEARM",8,8,32,55.0,.62,27.0,9.0,.30,1.7,False),
    }
    s.squad={
        "FTL": FireteamMember("FTL","Cpl. Mercer","Fireteam Leader",12.5,78.0,morale=88),
        "AR": FireteamMember("AR","Pfc. Rivera","Automatic Rifleman",11.7,77.5,morale=84),
        "RIFLE": FireteamMember("RIFLE","Pvt. Hale","Rifleman",11.7,78.5,morale=79),
        "MEDIC": FireteamMember("MEDIC","HM3 Lawson","Corpsman",10.8,78.0,morale=91),
    }
    s.contacts={
        "RED-1": GroundContact("RED-1","Opposing Rifle Team",31.0,86.0,cover_pct=48,role="RIFLE"),
        "RED-2": GroundContact("RED-2","Opposing Support Gun",43.5,89.0,cover_pct=62,role="SUPPORT"),
        "RED-3": GroundContact("RED-3","Opposing Flank Team",51.0,84.0,cover_pct=38,role="RIFLE"),
        "RED-4": GroundContact("RED-4","Opposing Rear Team",39.0,95.0,cover_pct=52,role="RIFLE"),
    }
    s.objectives={
        "CHECKPOINT": GroundObjective("CHECKPOINT","Move to Assault Checkpoint",19.0,82.0,3.0,status="ACTIVE",required_seconds=3,description="Move the fireteam from the assembly area to the marked checkpoint."),
        "VILLAGE": GroundObjective("VILLAGE","Secure Training Village",39.0,90.0,8.0,required_seconds=10,description="Neutralize opposing training contacts and occupy the village center."),
        "AID": GroundObjective("AID","Casualty Collection / Accountability",49.0,78.0,3.0,required_seconds=3,description="Treat any wounded personnel and report accountability at the field-aid point."),
    }
    s.log.append(s.last_event)
    return s


def begin_engagement(s: GroundCombatState) -> Tuple[bool,str]:
    if s.engagement_active and not s.engagement_complete: return False,"Ground combat training is already active."
    # Reset the live exercise while preserving cumulative counters.
    old_completed=s.engagements_completed
    old_losses=s.training_losses
    fresh=create_ground_combat()
    fresh.engagements_completed=old_completed
    fresh.training_losses=old_losses
    s.__dict__.update(fresh.__dict__)
    s.player.active=True; s.engagement_active=True
    msg="COMBINED-ARMS FIELD EXERCISE STARTED — report to the assault checkpoint and lead the fireteam through the training village."
    s.last_event=msg; s.log.insert(0,msg)
    return True,msg


def end_engagement(s: GroundCombatState) -> Tuple[bool,str]:
    if not s.engagement_active: return False,"No ground engagement is active."
    s.player.active=False; s.engagement_active=False
    return True,"Ground combat exercise stood down."


def cycle_weapon(s: GroundCombatState, delta: int=1) -> InfantryWeapon:
    keys=list(s.weapons)
    cur=keys.index(s.player.selected_weapon) if s.player.selected_weapon in keys else 0
    s.player.selected_weapon=keys[(cur+delta)%len(keys)]
    return s.weapons[s.player.selected_weapon]


def cycle_contact(s: GroundCombatState) -> Optional[GroundContact]:
    vals=[c for c in s.contacts.values() if c.health>0]
    if not vals: return None
    s.selected_contact_index=(s.selected_contact_index+1)%len(vals)
    return s.selected_contact


def cycle_squad(s: GroundCombatState) -> Optional[FireteamMember]:
    if not s.squad: return None
    s.selected_squad_index=(s.selected_squad_index+1)%len(s.squad)
    return s.selected_squad


def cycle_stance(s: GroundCombatState) -> str:
    order=("STANDING","CROUCHED","PRONE")
    s.player.stance=order[(order.index(s.player.stance)+1)%len(order)]
    return f"Stance: {s.player.stance}."


def toggle_aim(s: GroundCombatState) -> str:
    s.player.aiming=not s.player.aiming
    return f"Aim {'ON' if s.player.aiming else 'OFF'}."


def reload_weapon(s: GroundCombatState) -> Tuple[bool,str]:
    p=s.player; w=s.weapons[p.selected_weapon]
    if p.reload_remaining>0: return False,"Reload already in progress."
    need=w.magazine_capacity-w.magazine_rounds
    if need<=0: return False,f"{w.name} magazine is already full."
    if w.reserve_rounds<=0: return False,f"No reserve ammunition for {w.name}."
    p.reload_remaining=w.reload_seconds
    return True,f"Reloading {w.name}..."


def _finish_reload(s: GroundCombatState) -> None:
    p=s.player; w=s.weapons[p.selected_weapon]
    need=max(0,w.magazine_capacity-w.magazine_rounds); take=min(need,w.reserve_rounds)
    w.magazine_rounds+=take; w.reserve_rounds-=take
    s.last_event=f"{w.name} reloaded — {w.magazine_rounds}/{w.reserve_rounds}."
    s.log.insert(0,s.last_event)


def fire_weapon(s: GroundCombatState, player_x: float, player_y: float, heading_deg: float) -> Tuple[bool,str]:
    p=s.player
    if not s.engagement_active or not p.active: return False,"No live ground-combat exercise is active."
    if p.health<=0: return False,"Player is incapacitated."
    if p.reload_remaining>0: return False,"Cannot fire while reloading."
    if p.fire_cooldown>0: return False,"Weapon not ready."
    w=s.weapons[p.selected_weapon]
    if w.magazine_rounds<=0: return False,"Magazine empty — reload."
    w.magazine_rounds-=1; p.shots_fired+=1; p.fire_cooldown=w.fire_interval; p.weapon_heat=_clamp(p.weapon_heat+4.0,0,100)
    p.stamina=_clamp(p.stamina-0.4,0,100); s.muzzle_flash_seconds=.08
    target=s.selected_contact
    if not target:
        return True,f"{w.name} fired — no active target."
    rng=math.hypot(target.x-player_x,target.y-player_y); bearing=_bearing(player_x,player_y,target.x,target.y); error=abs(_angle_diff(bearing,heading_deg))
    target.confidence=_clamp(target.confidence+22,0,100); target.identified=target.confidence>=45; target.status="CONTACT"
    aim_bonus=.16 if p.aiming else 0.0
    stance_bonus={"STANDING":0.0,"CROUCHED":.08,"PRONE":.14}[p.stance]
    suppression_penalty=p.suppression/170.0
    range_factor=_clamp(1.0-rng/max(1.0,w.effective_range_m),.08,1.0)
    angle_factor=_clamp(1.0-error/18.0,0.0,1.0)
    cover_factor=1.0-target.cover_pct/150.0
    chance=_clamp((w.accuracy+aim_bonus+stance_bonus-suppression_penalty)*range_factor*angle_factor*cover_factor,.03,.96)
    # Deterministic hit roll derived from shot/contact state; repeatable for regression testing.
    seed=(p.shots_fired*37 + sum(ord(ch) for ch in target.key)*11 + int(rng*10))%100
    hit=seed < chance*100
    target.suppression=_clamp(target.suppression+w.suppression,0,100)
    s.last_tracer_target=target.key
    if hit:
        damage=w.damage*(.72+.28*angle_factor)
        target.health=_clamp(target.health-damage,0,100); p.hits+=1
        if target.health<=0:
            target.status="NEUTRALIZED"; s.enemies_neutralized+=1; s.score=_clamp(s.score+2,0,100)
            msg=f"{target.label} neutralized."
        else:
            target.status="SUPPRESSED" if target.suppression>=55 else "ENGAGED"
            msg=f"Hit {target.label} — condition {target.health:.0f}% / suppression {target.suppression:.0f}%."
    else:
        target.status="SUPPRESSED" if target.suppression>=55 else "ENGAGED"
        msg=f"Rounds near {target.label} — suppression {target.suppression:.0f}%."
    s.last_event=msg; s.log.insert(0,msg); s.log=s.log[:60]
    return True,msg


def use_first_aid(s: GroundCombatState) -> Tuple[bool,str]:
    p=s.player
    if p.first_aid_kits<=0: return False,"No individual first-aid kit remaining."
    if p.health>=98 and not p.wounded: return False,"No immediate self-aid required."
    p.first_aid_kits-=1; p.health=_clamp(p.health+24,0,100); p.suppression=_clamp(p.suppression-25,0,100); p.wounded=p.health<70
    s.casualties_treated+=1
    return True,f"Self-aid complete — health {p.health:.0f}% / kits {p.first_aid_kits}."


def order_squad(s: GroundCombatState, order: str, player_x: float, player_y: float) -> Tuple[bool,str]:
    order=order.upper()
    if order not in ("FOLLOW","HOLD","SUPPRESS","ASSAULT","FALL BACK"): return False,"Unknown fireteam order."
    target=s.selected_contact
    objective=s.active_objective
    for i,m in enumerate(s.squad.values()):
        if m.health<=0: continue
        m.order=order
        if order=="FOLLOW": m.target_x=player_x-1.0-(i%2)*.7; m.target_y=player_y+(i//2)*.7
        elif order=="HOLD": m.target_x,m.target_y=m.x,m.y
        elif order in ("SUPPRESS","ASSAULT") and target: m.target_x,m.target_y=target.x,target.y
        elif order=="ASSAULT" and objective: m.target_x,m.target_y=objective.x,objective.y
        elif order=="FALL BACK": m.target_x,m.target_y=12.0,78.0
    s.selected_order=order
    msg=f"FIRETEAM ORDER — {order}."
    s.last_event=msg; s.log.insert(0,msg)
    return True,msg


def request_air_support(s: GroundCombatState, ground_ops, player_x: float, player_y: float) -> Tuple[bool,str]:
    if s.support_cooldown>0: return False,f"Support net busy for {s.support_cooldown:.0f}s."
    target=s.selected_contact
    if not target: return False,"No target designated for air support."
    available=float(getattr(ground_ops,"air_support_points",0.0))
    if available<12: return False,"Insufficient carrier-air support points."
    ground_ops.air_support_points=max(0.0,available-12.0); s.air_support_used+=12; s.supports_called+=1; s.support_cooldown=18.0
    target.health=_clamp(target.health-46,0,100); target.suppression=100; target.status="NEUTRALIZED" if target.health<=0 else "SUPPRESSED"
    if target.health<=0: s.enemies_neutralized+=1
    msg=f"SIMULATED CLOSE AIR SUPPORT executed on {target.label} — target condition {target.health:.0f}%."
    s.last_event=msg; s.log.insert(0,msg)
    return True,msg


def request_naval_support(s: GroundCombatState, task_force, player_x: float, player_y: float) -> Tuple[bool,str]:
    if s.support_cooldown>0: return False,f"Support net busy for {s.support_cooldown:.0f}s."
    target=s.selected_contact
    if not target: return False,"No target designated for naval support."
    # Keep this deliberately abstract: require a healthy friendly screen ship rather than modeling real gunnery tables.
    fleet=getattr(task_force,"friendly",getattr(task_force,"friendlies",{}))
    candidates=[v for v in fleet.values() if getattr(v,"hull_pct",100)>40 and getattr(v,"ammo_pct",getattr(v,"ammunition_pct",100))>10]
    if not candidates: return False,"No task-force ship is available for simulated naval fire support."
    ship=candidates[0]
    if hasattr(ship,"ammo_pct"): ship.ammo_pct=max(0.0,ship.ammo_pct-4.0)
    elif hasattr(ship,"ammunition_pct"): ship.ammunition_pct=max(0.0,ship.ammunition_pct-4.0)
    s.naval_support_used+=1; s.supports_called+=1; s.support_cooldown=24.0
    target.health=_clamp(target.health-55,0,100); target.suppression=100; target.status="NEUTRALIZED" if target.health<=0 else "SUPPRESSED"
    if target.health<=0: s.enemies_neutralized+=1
    msg=f"SIMULATED NAVAL FIRE SUPPORT from {getattr(ship,'name','task force escort')} impacted {target.label}."
    s.last_event=msg; s.log.insert(0,msg)
    return True,msg


def treat_selected_squad_casualty(s: GroundCombatState) -> Tuple[bool,str]:
    wounded=[m for m in s.squad.values() if m.wounded and m.health>0]
    if not wounded: return False,"No fireteam casualty requires treatment."
    m=wounded[0]; m.health=_clamp(m.health+28,0,100); m.suppression=_clamp(m.suppression-35,0,100); m.wounded=m.health<70
    if not m.wounded: m.status="READY"
    s.casualties_treated+=1
    return True,f"Corpsman treated {m.name} — health {m.health:.0f}%."


def _advance_contacts(s: GroundCombatState, dt: float, player_x: float, player_y: float, player_heading_deg: float) -> List[str]:
    msgs=[]; p=s.player
    if not s.engagement_active or p.health<=0: return msgs
    for idx,c in enumerate(s.contacts.values()):
        if c.health<=0: continue
        rng=math.hypot(c.x-player_x,c.y-player_y)
        # Contacts become detected by proximity/line of attention, not globally visible on exercise start.
        view_error=abs(_angle_diff(_bearing(player_x,player_y,c.x,c.y),player_heading_deg))
        if rng<45 and view_error<65:
            c.confidence=_clamp(c.confidence+dt*(8 if rng<28 else 4),0,100)
            if c.confidence>=20: c.status="CONTACT"
            if c.confidence>=45: c.identified=True
            c.last_seen_seconds=s.elapsed
        else:
            c.confidence=_clamp(c.confidence-dt*.8,0,100)
        c.suppression=_clamp(c.suppression-dt*3.5,0,100)
        # Simple return-fire model. Cover, range, player stance and suppression matter.
        if rng<70 and c.confidence>=20 and c.suppression<82:
            cadence=3.4 if c.role=="SUPPORT" else 5.0
            pulse=int((s.elapsed+idx*1.37)/cadence)
            prev=int((s.elapsed-dt+idx*1.37)/cadence)
            if pulse!=prev:
                stance_factor={"STANDING":1.0,"CROUCHED":.72,"PRONE":.48}[p.stance]
                hit_chance=_clamp((.42*(1-rng/120.0))*stance_factor*(1-c.suppression/130.0),.02,.33)
                seed=(pulse*29+idx*17+int(rng*3))%100
                p.suppression=_clamp(p.suppression+(17 if c.role=="SUPPORT" else 10),0,100)
                if seed<hit_chance*100:
                    dmg=10.0 if c.role=="SUPPORT" else 7.0
                    p.health=_clamp(p.health-dmg,0,100); p.damage_taken+=dmg; p.wounded=p.health<70
                    s.score=_clamp(s.score-2.5,0,100); msgs.append(f"TRAINING HIT — player health {p.health:.0f}%.")
    return msgs


def _advance_squad(s: GroundCombatState, dt: float, player_x: float, player_y: float) -> List[str]:
    msgs=[]; targets=[c for c in s.contacts.values() if c.health>0 and c.confidence>=15]
    for idx,m in enumerate(s.squad.values()):
        if m.health<=0: continue
        # Movement based on current order.
        if m.order=="FOLLOW":
            m.target_x=player_x-1.2-(idx%2)*.8; m.target_y=player_y+(idx//2)*.8
        tx,ty=m.target_x,m.target_y; dist=math.hypot(tx-m.x,ty-m.y)
        if dist>.25 and m.order!="HOLD":
            speed=(1.3 if m.order=="SUPPRESS" else 2.2)*(1-m.suppression/160.0)
            step=min(dist,speed*dt); m.x+=(tx-m.x)/dist*step; m.y+=(ty-m.y)/dist*step
        m.suppression=_clamp(m.suppression-dt*4.0,0,100)
        m.ammo_pct=_clamp(m.ammo_pct-dt*(.02 if m.order in ("SUPPRESS","ASSAULT") and targets else .002),0,100)
        if targets and m.order in ("SUPPRESS","ASSAULT") and m.ammo_pct>0:
            c=min(targets,key=lambda t:math.hypot(t.x-m.x,t.y-m.y))
            rng=math.hypot(c.x-m.x,c.y-m.y)
            if rng<70:
                c.suppression=_clamp(c.suppression+dt*(10 if m.role=="Automatic Rifleman" else 5),0,100)
                if m.order=="ASSAULT" and rng<35:
                    c.health=_clamp(c.health-dt*2.0,0,100)
                    if c.health<=0 and c.status!="NEUTRALIZED": c.status="NEUTRALIZED"; s.enemies_neutralized+=1; msgs.append(f"Fireteam neutralized {c.label}.")
        # Opposing support fire can wound exposed squad members.
        threat=sum(1 for c in targets if math.hypot(c.x-m.x,c.y-m.y)<55 and c.suppression<55)
        if threat and int((s.elapsed+idx*2.1)/9.0)!=int((s.elapsed-dt+idx*2.1)/9.0):
            seed=(int(s.elapsed)*13+idx*31)%100
            if seed < 7*threat:
                m.health=_clamp(m.health-18,0,100); m.wounded=m.health<70; m.status="WOUNDED" if m.health>0 else "INCAPACITATED"
                if m.wounded: s.squad_wounded+=1; msgs.append(f"{m.name} is wounded.")
    return msgs


def _advance_objectives(s: GroundCombatState, dt: float, player_x: float, player_y: float) -> Optional[str]:
    # Objectives activate sequentially.
    order=list(s.objectives.values())
    for i,o in enumerate(order):
        if o.status=="COMPLETE": continue
        if o.status=="PENDING":
            if all(prev.status=="COMPLETE" for prev in order[:i]): o.status="ACTIVE"
            else: return None
        if o.key=="VILLAGE":
            alive=sum(1 for c in s.contacts.values() if c.health>0)
            in_zone=math.hypot(player_x-o.x,player_y-o.y)<=o.radius_m
            if alive==0 and in_zone: o.progress_seconds+=dt
        elif o.key=="AID":
            in_zone=math.hypot(player_x-o.x,player_y-o.y)<=o.radius_m
            untreated=any(m.wounded for m in s.squad.values()) or s.player.wounded
            if in_zone and not untreated: o.progress_seconds+=dt
        else:
            if math.hypot(player_x-o.x,player_y-o.y)<=o.radius_m: o.progress_seconds+=dt
        if o.progress_seconds>=o.required_seconds:
            o.status="COMPLETE"
            msg=f"GROUND OBJECTIVE COMPLETE — {o.title}."
            s.last_event=msg; s.log.insert(0,msg)
            if all(x.status=="COMPLETE" for x in order):
                s.engagement_complete=True; s.engagement_active=False; s.player.active=False; s.engagements_completed+=1
                s.score=_clamp(s.score + max(0,15-s.squad_wounded*2),0,100)
                msg=f"COMBINED-ARMS FIELD EXERCISE COMPLETE — score {s.score:.0f}%."
                s.last_event=msg; s.log.insert(0,msg)
            return msg
        return None
    return None


def advance_ground_combat(s: GroundCombatState, dt: float, player_x: float, player_y: float, player_heading_deg: float) -> List[str]:
    dt=max(0.0,float(dt)); msgs=[]; s.elapsed+=dt
    p=s.player
    if p.fire_cooldown>0: p.fire_cooldown=max(0.0,p.fire_cooldown-dt)
    if p.reload_remaining>0:
        before=p.reload_remaining; p.reload_remaining=max(0.0,p.reload_remaining-dt)
        if before>0 and p.reload_remaining<=0: _finish_reload(s); msgs.append(s.last_event)
    p.weapon_heat=_clamp(p.weapon_heat-dt*5.5,0,100); p.suppression=_clamp(p.suppression-dt*5.0,0,100)
    if s.support_cooldown>0: s.support_cooldown=max(0.0,s.support_cooldown-dt)
    s.muzzle_flash_seconds=max(0.0,s.muzzle_flash_seconds-dt)
    if not s.engagement_active: return msgs
    msgs.extend(_advance_contacts(s,dt,player_x,player_y,player_heading_deg))
    msgs.extend(_advance_squad(s,dt,player_x,player_y))
    evt=_advance_objectives(s,dt,player_x,player_y)
    if evt: msgs.append(evt)
    if p.health<=0 and not s.engagement_failed:
        s.engagement_failed=True; s.engagement_active=False; p.active=False; s.training_losses+=1; s.score=max(0,s.score-25)
        msgs.append("PLAYER INCAPACITATED — exercise terminated and medical evacuation initiated.")
    if msgs:
        s.last_event=msgs[-1]
        for m in reversed(msgs): s.log.insert(0,m)
        s.log=s.log[:60]
    return msgs


def ground_combat_summary(s: GroundCombatState) -> str:
    p=s.player; w=s.weapons[p.selected_weapon]; obj=s.active_objective
    return (f"GROUND COMBAT • {'ACTIVE' if s.engagement_active else 'COMPLETE' if s.engagement_complete else 'STANDBY'} • "
            f"score {s.score:.0f}% • health {p.health:.0f}% • suppression {p.suppression:.0f}% • "
            f"{w.name} {w.magazine_rounds}/{w.reserve_rounds} • objective {obj.title if obj else 'NONE'}")


def contact_lines(s: GroundCombatState) -> List[str]:
    out=[]
    active=[c for c in s.contacts.values() if c.health>0]
    selected=s.selected_contact
    for c in s.contacts.values():
        mark=">" if c is selected else " "
        ident=c.label if c.identified else "Unidentified training contact"
        out.append(f"{mark} {c.key:<7} {ident:<30} HLTH {c.health:3.0f}% SUP {c.suppression:3.0f}% CONF {c.confidence:3.0f}% • {c.status}")
    return out


def squad_lines(s: GroundCombatState) -> List[str]:
    out=[]
    for m in s.squad.values():
        mark=">" if m is s.selected_squad else " "
        out.append(f"{mark} {m.name:<18} {m.role:<20} HLTH {m.health:3.0f}% SUP {m.suppression:3.0f}% AMMO {m.ammo_pct:3.0f}% • {m.order}/{m.status}")
    return out


def objective_lines(s: GroundCombatState) -> List[str]:
    return [f"{o.title:<38} {o.status:<9} {o.progress_seconds:4.1f}/{o.required_seconds:.0f}s • {o.description}" for o in s.objectives.values()]


def ground_combat_to_dict(s: GroundCombatState) -> dict:
    return asdict(s)


def ground_combat_from_dict(data: dict) -> GroundCombatState:
    if not data: return create_ground_combat()
    base=create_ground_combat()
    for k,v in data.items():
        if k in ("player","weapons","squad","contacts","objectives","log"): continue
        if hasattr(base,k): setattr(base,k,v)
    if data.get("player"):
        for k,v in data["player"].items():
            if hasattr(base.player,k): setattr(base.player,k,v)
    for key,val in data.get("weapons",{}).items():
        if key in base.weapons:
            for k,v in val.items():
                if hasattr(base.weapons[key],k): setattr(base.weapons[key],k,v)
        else: base.weapons[key]=InfantryWeapon(**val)
    for key,val in data.get("squad",{}).items():
        if key in base.squad:
            for k,v in val.items():
                if hasattr(base.squad[key],k): setattr(base.squad[key],k,v)
        else: base.squad[key]=FireteamMember(**val)
    for key,val in data.get("contacts",{}).items():
        if key in base.contacts:
            for k,v in val.items():
                if hasattr(base.contacts[key],k): setattr(base.contacts[key],k,v)
        else: base.contacts[key]=GroundContact(**val)
    for key,val in data.get("objectives",{}).items():
        if key in base.objectives:
            for k,v in val.items():
                if hasattr(base.objectives[key],k): setattr(base.objectives[key],k,v)
        else: base.objectives[key]=GroundObjective(**val)
    base.log=list(data.get("log",base.log))[:60]
    return base
