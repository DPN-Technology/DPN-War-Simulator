from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random


def hhmm_to_min(value: str) -> int:
    h, m = value.split(":")
    return int(h) * 60 + int(m)


def min_to_hhmm(value: int) -> str:
    value %= 24 * 60
    return f"{value // 60:02d}:{value % 60:02d}"


@dataclass(frozen=True)
class HistoricalSource:
    key: str
    title: str
    organization: str
    url: str
    notes: str


@dataclass(frozen=True)
class WeatherZone:
    key: str
    name: str
    ceiling_ft: str
    visibility_nm: str
    wind: str
    conditions: str
    detection_modifier: float
    aviation_modifier: float


@dataclass(frozen=True)
class ContactUpdate:
    key: str
    label: str
    bearing_deg: float
    range_nm: float
    confidence: float
    uncertainty_nm: float
    classification: str
    note: str = ""


@dataclass(frozen=True)
class HistoricalEvent:
    key: str
    occurrence_minute: int
    report_minute: int
    category: str
    headline: str
    detail: str
    source_key: str
    audience: Tuple[str, ...] = ("OPERATIONS",)
    contact: Optional[ContactUpdate] = None
    own_force: bool = False


@dataclass(frozen=True)
class DecisionOption:
    label: str
    points: int
    rationale: str
    readiness_delta: float = 0.0
    intel_delta: float = 0.0


@dataclass(frozen=True)
class DecisionPrompt:
    key: str
    minute: int
    expires_minute: int
    title: str
    briefing: str
    options: Tuple[DecisionOption, ...]


@dataclass
class ContactState:
    key: str
    label: str
    bearing_deg: float
    range_nm: float
    confidence: float
    uncertainty_nm: float
    classification: str
    last_report_minute: int
    note: str = ""


@dataclass
class DoctrineGroup:
    key: str
    name: str
    side: str
    doctrine: str
    known_enemy_confidence: float = 0.0
    last_intel_minute: Optional[int] = None
    current_action: str = "Maintain assigned operating area"
    fuel: float = 100.0
    morale: float = 85.0
    readiness: float = 90.0


@dataclass
class HistoricalScenarioState:
    scenario_id: str = "midway_1942_ops_watch"
    current_minute: int = hhmm_to_min("05:20")
    end_minute: int = hhmm_to_min("18:40")
    running: bool = False
    speed: int = 1
    completed: bool = False
    evaluated: bool = False
    delivered_events: List[str] = field(default_factory=list)
    messages: List[dict] = field(default_factory=list)
    contacts: Dict[str, ContactState] = field(default_factory=dict)
    decisions: Dict[str, dict] = field(default_factory=dict)
    professional_points: int = 0
    max_professional_points: int = 0
    command_readiness: float = 70.0
    intel_discipline: float = 70.0
    aviation_readiness: float = 88.0
    timeline_accuracy: float = 100.0
    doctrine_groups: Dict[str, DoctrineGroup] = field(default_factory=dict)
    log: List[str] = field(default_factory=list)
    rng_seed: int = 4061942

    @property
    def clock(self) -> str:
        return min_to_hhmm(self.current_minute)


SOURCES: Dict[str, HistoricalSource] = {
    "nhhc_midway_overview": HistoricalSource(
        key="nhhc_midway_overview",
        title="Battle of Midway",
        organization="Naval History and Heritage Command",
        url="https://www.history.navy.mil/browse-by-topic/wars-conflicts-and-operations/world-war-ii/1942/midway.html",
        notes=(
            "Used for the U.S. and Japanese carrier forces, COMINT context, task-force organization, "
            "and the broad sequence of the 4 June carrier battle."
        ),
    ),
    "nhhc_isr": HistoricalSource(
        key="nhhc_isr",
        title="H-006-2 ISR at Midway",
        organization="Naval History and Heritage Command",
        url="https://www.history.navy.mil/about-us/leadership/director/directors-corner/h-grams/h-gram-006/h-006-2.html",
        notes=(
            "Used for early 4 June reconnaissance reporting: 0530 sighting/0534 report, 0545 inbound-aircraft report, "
            "0552 carrier sighting, 0553 Midway radar detection, and the fact that carrier-contact information reached senior commanders shortly after 0600."
        ),
    ),
    "nhhc_timeline": HistoricalSource(
        key="nhhc_timeline",
        title="Battle of Midway: Timeline of Significant Events, June 4, 1942",
        organization="Naval History and Heritage Command",
        url="https://www.history.navy.mil/content/dam/nhhc/news-and-events/multimedia%20gallery/LargeFormatBanners/LargeFormatPDF/PopUp_NHHC_BattleOfMidway_Panel2.pdf",
        notes=(
            "Used for the published 0700, 0838, 1020, 1022-1026, 1208, 1441, 1445, 1455, 1500, 1810, and 1830 timeline markers."
        ),
    ),
    "nhhc_aerology": HistoricalSource(
        key="nhhc_aerology",
        title="Battle of Midway: Aerology and Naval Warfare",
        organization="Naval History and Heritage Command",
        url="https://www.history.navy.mil/research/library/online-reading-room/title-list-alphabetically/b/battl-of-midway-aerology-and-naval-warfare.html",
        notes=(
            "Used for 4 June weather: broken/overcast ceilings, showers, visibility variation, Midway's clear conditions, "
            "and the effect of fronts and light southeasterly winds on scouting and carrier aviation."
        ),
    ),
    "nhhc_strategic_analysis": HistoricalSource(
        key="nhhc_strategic_analysis",
        title="Battle of Midway: Strategic and Tactical Analysis",
        organization="Naval History and Heritage Command",
        url="https://www.history.navy.mil/content/dam/nhhc/browse-by-topic/War%20and%20Conflict/WWII/midway_strategic_and_tactical_analysis.pdf",
        notes=(
            "Used for the detailed composition of U.S. Task Forces 16 and 17, including their carrier, cruiser, and destroyer screens."
        ),
    ),
    "nhhc_combat_narrative": HistoricalSource(
        key="nhhc_combat_narrative",
        title="Battle of Midway: 3-6 June 1942 Combat Narrative",
        organization="Naval History and Heritage Command",
        url="https://www.history.navy.mil/research/library/online-reading-room/title-list-alphabetically/b/battle-of-midway-3-6-june-1942-combat-narrative.html",
        notes=(
            "Used for the carrier-centric composition of the Japanese Striking Force and additional task-force operational context."
        ),
    ),
}


ORDER_OF_BATTLE = {
    "U.S. Task Force 16 — Rear Adm. Raymond A. Spruance": {
        "source": "nhhc_strategic_analysis",
        "units": [
            "Aircraft carriers: USS Enterprise (CV-6), USS Hornet (CV-8)",
            "Heavy cruisers: USS Northampton, USS Vincennes, USS Pensacola, USS Minneapolis, USS New Orleans",
            "Light cruiser (AA): USS Atlanta",
            "Destroyers: USS Worden, USS Monaghan, USS Aylwin, USS Phelps, USS Balch, USS Conyngham, USS Benham, USS Ellet, USS Maury",
        ],
    },
    "U.S. Task Force 17 — Rear Adm. Frank Jack Fletcher": {
        "source": "nhhc_strategic_analysis",
        "units": [
            "Aircraft carrier: USS Yorktown (CV-5)",
            "Heavy cruisers: USS Astoria, USS Portland",
            "Destroyers: USS Morris, USS Russell, USS Hammann, USS Anderson, USS Hughes",
        ],
    },
    "Japanese Carrier Strike Force — Vice Adm. Chuichi Nagumo": {
        "source": "nhhc_combat_narrative",
        "units": [
            "Carrier Division 1: Akagi, Kaga",
            "Carrier Division 2: Soryu, Hiryu",
            "Battleships: Haruna, Kirishima",
            "Heavy cruisers: Tone, Chikuma",
            "Light cruiser: Nagara",
            "Destroyer screen: 12 destroyers (carrier striking-force screen in the cited combat narrative)",
        ],
    },
}


WEATHER_ZONES: Dict[str, WeatherZone] = {
    "MIDWAY": WeatherZone(
        key="MIDWAY",
        name="Midway Atoll",
        ceiling_ft="Unlimited",
        visibility_nm=">12",
        wind="Light easterly",
        conditions="Clear early; good local visual conditions",
        detection_modifier=1.08,
        aviation_modifier=1.04,
    ),
    "JAPANESE_FORCE": WeatherZone(
        key="JAPANESE_FORCE",
        name="Northwest carrier-force area",
        ceiling_ft="1,000-2,300 broken",
        visibility_nm="Good except showers",
        wind="Variable / post-frontal",
        conditions="Broken cloud, scattered showers; concealment available",
        detection_modifier=0.72,
        aviation_modifier=0.86,
    ),
    "US_FORCE": WeatherZone(
        key="US_FORCE",
        name="U.S. carrier task-force area",
        ceiling_ft="Unlimited locally, lowering westward; later 1,000-2,300",
        visibility_nm="Generally good",
        wind="Light southeasterly by late morning",
        conditions="Cloudy/broken with scattered showers after frontal passage",
        detection_modifier=0.90,
        aviation_modifier=0.90,
    ),
}


# Coordinates are deliberately schematic and normalized for the tactical plotting UI.
# They communicate relative direction and uncertainty, not a claim of exact geodetic position.
FORCE_PLOT = {
    "MIDWAY": (0.50, 0.62),
    "TF16": (0.68, 0.35),
    "TF17": (0.63, 0.38),
    "JAPANESE_SEARCH_AREA": (0.29, 0.27),
}


def _event(key: str, occurrence: str, report: str, category: str, headline: str, detail: str,
           source: str, *, contact: Optional[ContactUpdate] = None, own_force: bool = False) -> HistoricalEvent:
    return HistoricalEvent(
        key=key,
        occurrence_minute=hhmm_to_min(occurrence),
        report_minute=hhmm_to_min(report),
        category=category,
        headline=headline,
        detail=detail,
        source_key=source,
        contact=contact,
        own_force=own_force,
    )


EVENTS: Tuple[HistoricalEvent, ...] = (
    _event(
        "pby_ship_sighting", "05:30", "05:34", "INTEL",
        "PBY reports Japanese ships northwest of Midway",
        "A patrol aircraft sighted Japanese ships northwest of Midway at 0530 and issued its sighting report at 0534. The report is useful, but it is not perfect knowledge of the entire enemy force.",
        "nhhc_isr",
        contact=ContactUpdate("JP_SURFACE", "Japanese surface contact", 315, 180, 42, 45, "SURFACE FORCE", "Initial patrol-aircraft report"),
    ),
    _event(
        "incoming_air", "05:45", "05:45", "AIR WARNING",
        "Many aircraft reported heading toward Midway",
        "A second PBY reported many aircraft heading toward Midway. This is an air-warning report, not a precise carrier-position solution.",
        "nhhc_isr",
    ),
    _event(
        "carrier_sighting", "05:52", "05:52", "INTEL",
        "Two Japanese carriers sighted",
        "The same patrol aircraft sighted two Japanese carriers. The report improves the plot but still leaves uncertainty about the full Japanese carrier force.",
        "nhhc_isr",
        contact=ContactUpdate("JP_CARRIERS", "Japanese carrier contact", 315, 155, 62, 28, "CARRIERS", "Two carriers visually reported"),
    ),
    _event(
        "midway_radar", "05:53", "05:53", "RADAR",
        "Midway radar detects inbound strike",
        "Midway radar detected the incoming Japanese strike. The defensive warning is now corroborated by a different sensor source.",
        "nhhc_isr",
    ),
    _event(
        "carrier_report_reaches_command", "05:52", "06:05", "COMMAND NET",
        "Carrier-contact information reaches carrier commanders",
        "Carrier-contact information reached senior U.S. commanders shortly after 0600. The simulation deliberately models the gap between observation and command-level receipt.",
        "nhhc_isr",
        contact=ContactUpdate("JP_CARRIERS", "Japanese carrier contact", 315, 155, 72, 22, "CARRIERS", "Command-level receipt; position remains approximate"),
    ),
    _event(
        "tf16_launch", "07:00", "07:00", "OWN FORCE",
        "Enterprise and Hornet begin launching",
        "Enterprise and Hornet begin launching their attack groups.",
        "nhhc_timeline", own_force=True,
    ),
    _event(
        "yorktown_launch", "08:38", "08:38", "OWN FORCE",
        "Yorktown launches",
        "Yorktown begins launching its strike according to the NHHC significant-events timeline.",
        "nhhc_timeline", own_force=True,
    ),
    _event(
        "torpedo_attack", "10:20", "10:25", "BATTLE REPORT",
        "U.S. carrier torpedo squadrons attack",
        "Enterprise and Yorktown torpedo squadrons attack. Reports arriving at the operations plot remain fragmented and should not be treated as a complete picture of the battle.",
        "nhhc_timeline",
        contact=ContactUpdate("JP_CARRIERS", "Japanese carrier contact", 300, 135, 76, 18, "CARRIERS", "Attack reports refine the tactical picture"),
    ),
    _event(
        "three_carriers_hit", "10:22", "10:30", "BATTLE REPORT",
        "Akagi, Kaga, and Soryu hit by dive bombers",
        "Between 1022 and 1026, Enterprise and Yorktown dive bombers attacked and hit Akagi, Kaga, and Soryu. The operations watch receives confirmation after the attack window rather than at the instant bombs strike.",
        "nhhc_timeline",
        contact=ContactUpdate("JP_CARRIERS", "Japanese carrier contact", 300, 135, 88, 12, "DAMAGED CARRIERS", "Three carriers reported hit; one carrier remains a threat"),
    ),
    _event(
        "hiryu_launch", "11:00", "11:15", "INTEL INFERENCE",
        "Enemy carrier threat remains",
        "Historical sources record that Hiryu, which escaped the morning destruction, launched a counterstrike around 1100. The player is not given omniscient launch knowledge at 1100; the scenario instead raises the unresolved-carrier threat as information develops.",
        "nhhc_midway_overview",
        contact=ContactUpdate("JP_CARRIERS", "Japanese carrier contact", 295, 130, 74, 24, "AT LEAST ONE OPERATIONAL CARRIER", "Residual carrier threat inferred from continuing enemy air activity"),
    ),
    _event(
        "yorktown_dive_attack", "12:08", "12:08", "OWN FORCE DAMAGE",
        "Japanese dive bombers attack Yorktown",
        "Japanese dive bombers attack Yorktown. Carrier-defense, damage-control, and reporting discipline become immediate priorities.",
        "nhhc_timeline", own_force=True,
    ),
    _event(
        "yorktown_torpedo_attack", "14:41", "14:41", "OWN FORCE DAMAGE",
        "Japanese torpedo planes attack Yorktown",
        "A second Japanese strike attacks Yorktown with torpedoes.",
        "nhhc_timeline", own_force=True,
    ),
    _event(
        "yorktown_hit", "14:45", "14:45", "OWN FORCE DAMAGE",
        "Yorktown hit",
        "Yorktown is hit during the torpedo attack.",
        "nhhc_timeline", own_force=True,
    ),
    _event(
        "yorktown_abandon", "14:55", "14:55", "OWN FORCE DAMAGE",
        "Yorktown abandonment ordered",
        "The NHHC significant-events timeline marks Yorktown's abandonment at 1455.",
        "nhhc_timeline", own_force=True,
    ),
    _event(
        "b17_launch", "15:00", "15:00", "OWN FORCE",
        "B-17s take off from Midway",
        "The NHHC significant-events timeline marks a B-17 launch from Midway at 1500.",
        "nhhc_timeline", own_force=True,
    ),
    _event(
        "hiryu_strike", "17:00", "17:12", "BATTLE REPORT",
        "U.S. dive bombers attack Hiryu",
        "Historical summaries place the strike that mortally damaged Hiryu around 1700. The report reaches the simulated watch after a communications delay.",
        "nhhc_midway_overview",
        contact=ContactUpdate("JP_CARRIERS", "Japanese carrier contact", 286, 120, 92, 9, "HIRYU HEAVILY DAMAGED", "Late-afternoon strike report"),
    ),
    _event(
        "b17_1810", "18:10", "18:10", "BATTLE REPORT",
        "Two B-17s attack battleship and damaged carrier",
        "The NHHC significant-events timeline records a two-aircraft B-17 attack at 1810.",
        "nhhc_timeline",
    ),
    _event(
        "b17_1830", "18:30", "18:30", "BATTLE REPORT",
        "Six B-17s attack damaged carrier and destroyer",
        "The NHHC significant-events timeline records a six-aircraft B-17 attack at 1830.",
        "nhhc_timeline",
    ),
)


DECISIONS: Tuple[DecisionPrompt, ...] = (
    DecisionPrompt(
        key="air_warning_response",
        minute=hhmm_to_min("05:45"), expires_minute=hhmm_to_min("06:00"),
        title="Incoming air strike report",
        briefing="A patrol aircraft reports many aircraft heading toward Midway. What should an operations watchstander recommend with the information actually available?",
        options=(
            DecisionOption("Raise air-defense readiness; log the report as unconfirmed track data", 20, "Acts promptly without pretending the report is more precise than it is.", readiness_delta=8, intel_delta=4),
            DecisionOption("Wait for visual confirmation before warning anyone", 5, "Avoids a false alarm but wastes critical warning time.", readiness_delta=-7, intel_delta=-2),
            DecisionOption("Declare the enemy carrier force's exact position and strength", 0, "This invents information the report does not provide.", intel_delta=-14),
        ),
    ),
    DecisionPrompt(
        key="carrier_contact_handling",
        minute=hhmm_to_min("06:05"), expires_minute=hhmm_to_min("06:25"),
        title="Carrier contact reaches command",
        briefing="A visual report of two Japanese carriers has reached carrier commanders. The full force and exact position remain uncertain.",
        options=(
            DecisionOption("Update the plot, preserve uncertainty, and route the contact immediately", 20, "Correctly distinguishes a useful contact from perfect intelligence.", readiness_delta=4, intel_delta=10),
            DecisionOption("Treat the two reported carriers as the entire Japanese force", 4, "Overconfidence can make later reports harder to interpret.", intel_delta=-8),
            DecisionOption("Hold the contact until the entire force is identified", 2, "Withholds actionable information while waiting for certainty that may never arrive.", readiness_delta=-5, intel_delta=-5),
        ),
    ),
    DecisionPrompt(
        key="launch_recommendation",
        minute=hhmm_to_min("06:50"), expires_minute=hhmm_to_min("07:10"),
        title="Strike launch planning",
        briefing="Carrier-contact information is available, but weather, range, recovery, CAP, and incomplete enemy information still matter.",
        options=(
            DecisionOption("Support an organized strike while preserving CAP and recovery margins", 20, "Balances offensive action with the continuing need to defend and recover aircraft.", readiness_delta=7, intel_delta=3),
            DecisionOption("Commit every available aircraft and ignore defensive coverage", 4, "Maximizes immediate weight but creates avoidable operational risk.", readiness_delta=-10),
            DecisionOption("Recommend no strike until the enemy force is fully mapped", 1, "Demands a level of certainty the battle did not provide.", readiness_delta=-8, intel_delta=-3),
        ),
    ),
    DecisionPrompt(
        key="fragmented_reports",
        minute=hhmm_to_min("10:25"), expires_minute=hhmm_to_min("10:45"),
        title="Fragmented attack reports",
        briefing="Torpedo attacks are underway and early strike reports are arriving. The plot is changing faster than reports can be correlated.",
        options=(
            DecisionOption("Time-stamp each report, correlate sources, and keep uncertain contacts marked uncertain", 20, "Maintains a usable common operating picture under communications delay.", intel_delta=10),
            DecisionOption("Declare the entire enemy carrier force destroyed immediately", 0, "Premature certainty is exactly what the historical-intelligence model is designed to prevent.", intel_delta=-15),
            DecisionOption("Discard conflicting reports until they agree", 5, "Reduces clutter but can erase important evidence during a fast battle.", intel_delta=-6),
        ),
    ),
    DecisionPrompt(
        key="residual_carrier_threat",
        minute=hhmm_to_min("11:15"), expires_minute=hhmm_to_min("11:40"),
        title="Residual enemy carrier threat",
        briefing="Three Japanese carriers have been reported hit, yet enemy air activity continues. What should the watch assume?",
        options=(
            DecisionOption("Keep at least one operational enemy carrier on the threat plot until disproved", 20, "Matches disciplined reasoning from incomplete battle reports.", readiness_delta=7, intel_delta=8),
            DecisionOption("Remove all Japanese carrier threats because three were hit", 0, "Confuses damage reports with proof that no other carrier can strike.", readiness_delta=-12, intel_delta=-12),
            DecisionOption("Ignore all carrier reports and focus only on Midway", 3, "Abandons the wider tactical picture.", readiness_delta=-8, intel_delta=-5),
        ),
    ),
    DecisionPrompt(
        key="yorktown_defense",
        minute=hhmm_to_min("12:08"), expires_minute=hhmm_to_min("12:28"),
        title="Yorktown under air attack",
        briefing="Yorktown is under attack. The watch must support defense and damage response while keeping the wider tactical picture alive.",
        options=(
            DecisionOption("Prioritize CAP/damage reporting while maintaining the enemy-carrier plot", 20, "Handles the immediate casualty without losing operational awareness.", readiness_delta=8, intel_delta=5),
            DecisionOption("Stop all plotting until Yorktown's damage is fully known", 5, "Focuses on the casualty but sacrifices tactical awareness.", intel_delta=-6),
            DecisionOption("Ignore Yorktown's attack because the offensive strike is more important", 0, "Fails the own-force reporting and survival responsibilities of the watch.", readiness_delta=-14),
        ),
    ),
)


MAX_DECISION_POINTS = sum(max(option.points for option in prompt.options) for prompt in DECISIONS)


def create_midway_state() -> HistoricalScenarioState:
    state = HistoricalScenarioState()
    state.max_professional_points = MAX_DECISION_POINTS
    state.doctrine_groups = {
        "US": DoctrineGroup(
            key="US", name="U.S. Carrier Task Forces", side="U.S.",
            doctrine="Use intelligence advantage to locate and strike the enemy carrier force while retaining enough combat air patrol and recovery capacity to protect the carriers.",
            current_action="Hold northeast of Midway and maintain search/strike readiness",
            fuel=96.0, morale=86.0, readiness=91.0,
        ),
        "JP": DoctrineGroup(
            key="JP", name="Japanese Carrier Strike Force", side="Japan",
            doctrine="Execute the Midway air attack, protect the carrier striking force, and counterattack U.S. carriers when located. Decisions depend on reconnaissance and communications rather than perfect knowledge.",
            current_action="Operate northwest of Midway under broken cloud and prepare/execute air operations",
            fuel=94.0, morale=90.0, readiness=94.0,
        ),
    }
    state.log.append("05:20 — Historical lock active. Canonical battle events are fixed; your performance is judged on information handling and watchstanding decisions.")
    return state


def current_weather(state: HistoricalScenarioState) -> WeatherZone:
    # The U.S. carrier-area description changes after the force crosses the frontal zone.
    if state.current_minute >= hhmm_to_min("10:00"):
        return WeatherZone(
            key="US_FORCE_LATE",
            name="U.S. carrier task-force area",
            ceiling_ft="1,000-2,300 broken/overcast",
            visibility_nm="Good except showers",
            wind="Light southeasterly",
            conditions="Post-frontal broken/overcast with scattered showers; launch/recovery requires maneuvering into wind",
            detection_modifier=0.88,
            aviation_modifier=0.86,
        )
    return WEATHER_ZONES["US_FORCE"]


def active_prompt(state: HistoricalScenarioState) -> Optional[DecisionPrompt]:
    for prompt in DECISIONS:
        if prompt.key in state.decisions:
            continue
        if prompt.minute <= state.current_minute <= prompt.expires_minute:
            return prompt
    return None


def upcoming_prompt(state: HistoricalScenarioState) -> Optional[DecisionPrompt]:
    for prompt in DECISIONS:
        if prompt.key not in state.decisions and state.current_minute < prompt.minute:
            return prompt
    return None


def answer_decision(state: HistoricalScenarioState, prompt_key: str, option_index: int) -> Tuple[bool, str]:
    prompt = next((p for p in DECISIONS if p.key == prompt_key), None)
    if prompt is None:
        return False, "Unknown decision prompt."
    if prompt.key in state.decisions:
        return False, "That decision has already been logged."
    if not (prompt.minute <= state.current_minute <= prompt.expires_minute):
        return False, "That decision window is not active."
    if option_index < 0 or option_index >= len(prompt.options):
        return False, "Unknown option."
    option = prompt.options[option_index]
    state.decisions[prompt.key] = {
        "option": option.label,
        "points": option.points,
        "rationale": option.rationale,
        "minute": state.current_minute,
    }
    state.professional_points += option.points
    state.command_readiness = max(0.0, min(100.0, state.command_readiness + option.readiness_delta))
    state.intel_discipline = max(0.0, min(100.0, state.intel_discipline + option.intel_delta))
    state.log.insert(0, f"{state.clock} — DECISION: {option.label} ({option.points} pts). {option.rationale}")
    return True, option.rationale


def _miss_expired_decisions(state: HistoricalScenarioState) -> None:
    for prompt in DECISIONS:
        if prompt.key in state.decisions:
            continue
        if state.current_minute > prompt.expires_minute:
            state.decisions[prompt.key] = {
                "option": "NO RESPONSE LOGGED",
                "points": 0,
                "rationale": "The decision window expired without a watch recommendation.",
                "minute": prompt.expires_minute,
            }
            state.command_readiness = max(0.0, state.command_readiness - 4.0)
            state.log.insert(0, f"{min_to_hhmm(prompt.expires_minute)} — MISSED DECISION: {prompt.title}.")


def _deliver_event(state: HistoricalScenarioState, event: HistoricalEvent) -> None:
    if event.key in state.delivered_events:
        return
    state.delivered_events.append(event.key)
    lag = max(0, event.report_minute - event.occurrence_minute)
    state.messages.insert(0, {
        "report_time": min_to_hhmm(event.report_minute),
        "occurrence_time": min_to_hhmm(event.occurrence_minute),
        "category": event.category,
        "headline": event.headline,
        "detail": event.detail,
        "source_key": event.source_key,
        "lag": lag,
    })
    state.messages = state.messages[:100]
    if event.contact:
        c = event.contact
        # Weather broadens uncertainty. The random jitter is deterministic and affects only the schematic plot.
        weather = WEATHER_ZONES["JAPANESE_FORCE"]
        rng = random.Random(state.rng_seed + event.report_minute + len(state.delivered_events) * 37)
        jitter = (1.0 - weather.detection_modifier) * rng.uniform(-7.0, 7.0)
        state.contacts[c.key] = ContactState(
            key=c.key,
            label=c.label,
            bearing_deg=(c.bearing_deg + jitter) % 360,
            range_nm=max(1.0, c.range_nm + jitter * 0.8),
            confidence=max(0.0, min(100.0, c.confidence * weather.detection_modifier + 15.0)),
            uncertainty_nm=c.uncertainty_nm / weather.detection_modifier,
            classification=c.classification,
            last_report_minute=event.report_minute,
            note=c.note,
        )
    if event.category == "OWN FORCE DAMAGE":
        state.command_readiness = max(0.0, state.command_readiness - 5.0)
        state.aviation_readiness = max(0.0, state.aviation_readiness - 6.0)
    elif event.category == "OWN FORCE":
        state.aviation_readiness = max(0.0, state.aviation_readiness - 1.0)
    state.log.insert(0, f"{min_to_hhmm(event.report_minute)} — {event.category}: {event.headline}")


def _update_doctrine_ai(state: HistoricalScenarioState) -> None:
    us = state.doctrine_groups["US"]
    jp = state.doctrine_groups["JP"]
    contact = state.contacts.get("JP_CARRIERS")
    if contact:
        us.known_enemy_confidence = contact.confidence
        us.last_intel_minute = contact.last_report_minute
        age = max(0, state.current_minute - contact.last_report_minute)
        if state.current_minute < hhmm_to_min("07:00"):
            us.current_action = "Build strike plot from carrier contact; maintain defensive air readiness"
        elif state.current_minute < hhmm_to_min("10:20"):
            us.current_action = "Strikes airborne; correlate search/contact reports and preserve recovery/CAP capacity"
        elif state.current_minute < hhmm_to_min("11:15"):
            us.current_action = "Assess fragmented strike reports; do not assume all enemy carriers neutralized"
        elif state.current_minute < hhmm_to_min("17:12"):
            us.current_action = "Track residual carrier threat while protecting damaged own forces"
        else:
            us.current_action = "Exploit confirmed damage while retaining uncertainty about surviving enemy surface forces"
        # Stale reports degrade belief quality.
        us.known_enemy_confidence = max(20.0, contact.confidence - age * 0.45)
    else:
        us.current_action = "Continue reconnaissance; no verified enemy-carrier plot available"
        us.known_enemy_confidence = 0.0

    # Japanese AI deliberately does not gain omniscient U.S. positions from the player's plot.
    if state.current_minute < hhmm_to_min("12:08"):
        jp.known_enemy_confidence = min(58.0, max(0.0, (state.current_minute - hhmm_to_min("07:00")) * 0.13))
        jp.current_action = "Execute assigned strike/recovery cycle while searching for U.S. carriers"
    elif state.current_minute < hhmm_to_min("14:41"):
        jp.known_enemy_confidence = 72.0
        jp.current_action = "Exploit contact on Yorktown with follow-up carrier air attack"
    elif state.current_minute < hhmm_to_min("17:12"):
        jp.known_enemy_confidence = 64.0
        jp.current_action = "Continue counterstrike operations while carrier force is under severe damage pressure"
    else:
        jp.known_enemy_confidence = 38.0
        jp.current_action = "Damaged carrier force attempts survival/withdrawal; tactical picture deteriorating"

    elapsed_hours = max(0.0, (state.current_minute - hhmm_to_min("05:20")) / 60.0)
    us.fuel = max(35.0, 96.0 - elapsed_hours * 2.2)
    jp.fuel = max(30.0, 94.0 - elapsed_hours * 2.4)
    us.readiness = max(35.0, state.aviation_readiness - elapsed_hours * 0.7)
    jp.readiness = max(20.0, 94.0 - elapsed_hours * 3.5 - (18.0 if state.current_minute >= hhmm_to_min("10:30") else 0.0))


def advance_historical(state: HistoricalScenarioState, minutes: int = 1) -> HistoricalScenarioState:
    if state.completed:
        return state
    target = min(state.end_minute, state.current_minute + max(1, int(minutes)))
    # Process each simulated minute so event delivery and prompt expiry remain deterministic at high speed.
    while state.current_minute < target:
        state.current_minute += 1
        for event in EVENTS:
            if event.report_minute <= state.current_minute and event.key not in state.delivered_events:
                _deliver_event(state, event)
        _miss_expired_decisions(state)
        _update_doctrine_ai(state)
        if state.current_minute >= state.end_minute:
            state.completed = True
            state.running = False
            state.log.insert(0, f"{state.clock} — Scenario watch complete. Evaluate the record.")
            break
    return state


def jump_to_next_event(state: HistoricalScenarioState) -> HistoricalScenarioState:
    future_times = [e.report_minute for e in EVENTS if e.key not in state.delivered_events and e.report_minute > state.current_minute]
    future_prompts = [p.minute for p in DECISIONS if p.key not in state.decisions and p.minute > state.current_minute]
    candidates = future_times + future_prompts
    if not candidates:
        return advance_historical(state, state.end_minute - state.current_minute)
    nxt = min(candidates)
    return advance_historical(state, max(1, nxt - state.current_minute))


def historical_summary(state: HistoricalScenarioState) -> dict:
    answered = [v for v in state.decisions.values() if v.get("option") != "NO RESPONSE LOGGED"]
    optimal = [v for v in state.decisions.values() if v.get("points") == 20]
    contact = state.contacts.get("JP_CARRIERS")
    return {
        "clock": state.clock,
        "events_received": len(state.delivered_events),
        "decisions_answered": len(answered),
        "optimal_decisions": len(optimal),
        "command_readiness": state.command_readiness,
        "intel_discipline": state.intel_discipline,
        "aviation_readiness": state.aviation_readiness,
        "carrier_contact_confidence": contact.confidence if contact else 0.0,
    }


def evaluate_historical(state: HistoricalScenarioState) -> float:
    # Ensure unanswered prompts are counted as missed if the player evaluates early.
    if not state.completed:
        state.current_minute = max(state.current_minute, max(p.expires_minute for p in DECISIONS) + 1)
        _miss_expired_decisions(state)
    decision_component = 70.0 * (state.professional_points / max(1, state.max_professional_points))
    discipline_component = 0.15 * state.intel_discipline
    readiness_component = 0.10 * state.command_readiness
    timeline_component = 0.05 * state.timeline_accuracy
    score = max(0.0, min(100.0, decision_component + discipline_component + readiness_component + timeline_component))
    state.evaluated = True
    return round(score, 1)


def source_for(key: str) -> HistoricalSource:
    return SOURCES[key]
