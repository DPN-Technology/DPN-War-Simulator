from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List
import random
import time
from .data import NAVAL_RANKS, HELM_TOPICS, CREW_NAMES

@dataclass
class CrewMember:
    name: str
    age: int
    rank: str
    experience: int
    morale: float
    fatigue: float
    stress: float
    injuries: float
    training: float
    relationship: float
    family_history: str
    personality: str
    decision_making: float
    voice: str
    memory: List[str] = field(default_factory=list)
    career_record: List[str] = field(default_factory=list)

    @staticmethod
    def generated(seed: int, idx: int) -> "CrewMember":
        rng = random.Random(seed + idx * 7919)
        name = CREW_NAMES[idx % len(CREW_NAMES)]
        personalities = ["Methodical", "Calm", "Direct", "Cautious", "Analytical", "Steady"]
        histories = [
            "Multigenerational service family", "Civilian maritime family", "First in family to serve",
            "Engineering family background", "Coastal community upbringing",
        ]
        return CrewMember(
            name=name,
            age=rng.randint(19, 38),
            rank=rng.choice(["Seaman Recruit", "Seaman Apprentice", "Seaman", "Petty Officer"]),
            experience=rng.randint(50, 800),
            morale=round(rng.uniform(62, 92), 1),
            fatigue=round(rng.uniform(5, 28), 1),
            stress=round(rng.uniform(4, 25), 1),
            injuries=0.0,
            training=round(rng.uniform(55, 92), 1),
            relationship=round(rng.uniform(35, 75), 1),
            family_history=rng.choice(histories),
            personality=rng.choice(personalities),
            decision_making=round(rng.uniform(52, 90), 1),
            voice=f"Voice Profile {idx + 1}",
        )

@dataclass
class CareerProfile:
    name: str = "Cadet"
    branch: str = "Navy"
    era: str = "World War II"
    rank_index: int = 0
    xp: int = 0
    duty_periods: int = 0
    written_exam: float = 0.0
    practical_exam: float = 0.0
    performance_review: float = 50.0
    leadership_eval: float = 40.0
    recommendations: int = 0
    schools_completed: int = 0
    mission_performance: float = 50.0
    discipline: float = 75.0
    professionalism: float = 75.0
    reputation: float = 50.0
    qualifications: Dict[str, bool] = field(default_factory=dict)
    topic_mastery: Dict[str, int] = field(default_factory=lambda: {t: 0 for t in HELM_TOPICS})
    mission_history: List[dict] = field(default_factory=list)
    ship_systems_best: float = 0.0
    ship_systems_runs: int = 0
    historical_runs: int = 0
    historical_best: float = 0.0
    historical_scenarios: Dict[str, float] = field(default_factory=dict)
    enterprise_duty_runs: int = 0
    enterprise_duty_best: float = 0.0
    shipboard_walk_runs: int = 0
    shipboard_walk_best: float = 0.0
    open_world_minutes: int = 0
    maintenance_completed: int = 0
    meals_taken: int = 0
    sleep_periods: int = 0
    life_routine_best: float = 0.0
    seamanship_distance_nm: float = 0.0
    underway_seconds: float = 0.0
    groundings: int = 0
    combat_training_runs: int = 0
    combat_training_best: float = 0.0
    combat_enemy_destroyed: int = 0
    combat_hits_taken: int = 0
    carrier_sorties: int = 0
    combat_snapshot: Dict[str, object] = field(default_factory=dict)
    survivability_snapshot: Dict[str, object] = field(default_factory=dict)
    survivability_drills: int = 0
    survivability_best: float = 0.0
    casualties_treated_total: int = 0
    abandon_ship_drills: int = 0
    command_snapshot: Dict[str, object] = field(default_factory=dict)
    command_orders_issued: int = 0
    command_orders_completed: int = 0
    command_orders_failed: int = 0
    command_watch_reliefs: int = 0
    command_best_score: float = 0.0
    autonomous_crew_actions: int = 0
    task_force_snapshot: Dict[str, object] = field(default_factory=dict)
    fleet_orders_issued: int = 0
    fleet_signals_sent: int = 0
    fleet_replenishments: int = 0
    fleet_surface_contacts_defeated: int = 0
    fleet_submarines_defeated: int = 0
    fleet_collision_warnings: int = 0
    fleet_best_station_pct: float = 0.0
    campaign_snapshot: Dict[str, object] = field(default_factory=dict)
    campaign_missions_completed: int = 0
    campaign_convoy_deliveries: int = 0
    campaign_port_services: int = 0
    campaign_escort_repairs: int = 0
    campaign_best_score: float = 0.0
    air_wing_snapshot: Dict[str, object] = field(default_factory=dict)
    physical_world_snapshot: Dict[str, object] = field(default_factory=dict)
    flight_ops_snapshot: Dict[str, object] = field(default_factory=dict)
    flight_combat_snapshot: Dict[str, object] = field(default_factory=dict)
    ground_ops_snapshot: Dict[str, object] = field(default_factory=dict)
    ground_missions_completed: int = 0
    ground_amphibious_landings: int = 0
    ground_airfield_services: int = 0
    ground_supplies_delivered: float = 0.0
    ground_vehicle_distance_m: float = 0.0
    ground_ops_best_score: float = 0.0
    ground_combat_snapshot: Dict[str, object] = field(default_factory=dict)
    ground_combat_runs: int = 0
    ground_combat_best_score: float = 0.0
    ground_enemies_neutralized: int = 0
    ground_support_calls: int = 0
    ground_casualties_treated: int = 0
    ground_training_losses: int = 0
    land_warfare_snapshot: Dict[str, object] = field(default_factory=dict)
    land_operations_completed: int = 0
    land_operations_failed: int = 0
    land_sectors_secured: int = 0
    land_artillery_missions: int = 0
    land_medevac_actions: int = 0
    land_resupply_actions: int = 0
    land_armored_kills: int = 0
    land_vehicle_distance_m: float = 0.0
    land_warfare_best_score: float = 0.0
    strategic_war_snapshot: Dict[str, object] = field(default_factory=dict)
    strategic_operations_completed: int = 0
    strategic_operations_failed: int = 0
    strategic_front_shifts: int = 0
    strategic_recon_reports: int = 0
    strategic_supply_deliveries: int = 0
    strategic_reinforcement_waves: int = 0
    strategic_bridges_repaired: int = 0
    strategic_best_score: float = 0.0
    war_economy_snapshot: Dict[str, object] = field(default_factory=dict)
    economy_orders_completed: int = 0
    economy_allocations: int = 0
    economy_facilities_repaired: int = 0
    economy_research_completed: int = 0
    economy_personnel_graduated: int = 0
    economy_infrastructure_repairs: int = 0
    economy_best_score: float = 0.0
    logistics_network_snapshot: Dict[str, object] = field(default_factory=dict)
    logistics_shipments_delivered: int = 0
    logistics_shipments_lost: int = 0
    logistics_shipments_delayed: int = 0
    logistics_escorted_shipments: int = 0
    logistics_route_repairs: int = 0
    logistics_hub_repairs: int = 0
    logistics_hub_issues: int = 0
    logistics_cargo_delivered: float = 0.0
    logistics_best_score: float = 0.0
    air_combat_sorties: int = 0
    aerial_victories: int = 0
    air_to_surface_hits: int = 0
    pilot_bailouts: int = 0
    pilot_ditchings: int = 0
    pilot_rescues: int = 0
    cockpit_aircraft_losses: int = 0
    air_combat_best_score: float = 0.0
    cockpit_flights: int = 0
    carrier_takeoffs: int = 0
    carrier_landings: int = 0
    pilot_distance_nm: float = 0.0
    air_wing_missions_completed: int = 0
    air_wing_sorties_launched: int = 0
    air_wing_sorties_recovered: int = 0
    air_wing_aircraft_lost: int = 0
    air_wing_scout_reports: int = 0
    air_wing_best_score: float = 0.0
    ship_nav_east_nm: float = 0.0
    ship_nav_north_nm: float = 0.0
    ship_heading_deg: float = 90.0
    ship_speed_knots: float = 0.0
    ship_engine_order: float = 0.0
    ship_rudder_deg: float = 0.0
    ship_moored: bool = True
    ship_anchor_deployed: bool = False
    ship_hull_integrity: float = 100.0
    ship_sea_state: int = 3
    player_world_x: float = 10.0
    player_world_y: float = 18.0
    player_world_z: float = 4.82
    player_world_yaw: float = 0.0
    player_world_pitch: float = 0.0
    ship_layout_version: int = 1
    station_qualifications: Dict[str, bool] = field(default_factory=dict)
    service_log: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    crew_seed: int = field(default_factory=lambda: random.randint(1000, 9999999))

    @property
    def rank(self) -> str:
        return NAVAL_RANKS[min(self.rank_index, len(NAVAL_RANKS) - 1)]

    @property
    def next_rank(self) -> str:
        if self.rank_index >= len(NAVAL_RANKS) - 1:
            return "Maximum rank achieved"
        return NAVAL_RANKS[self.rank_index + 1]

    def add_log(self, message: str) -> None:
        self.service_log.insert(0, message)
        self.service_log = self.service_log[:100]

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "CareerProfile":
        allowed = {f.name for f in CareerProfile.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in allowed}
        profile = CareerProfile(**filtered)
        for t in HELM_TOPICS:
            profile.topic_mastery.setdefault(t, 0)
        return profile

@dataclass
class BridgeState:
    heading: float = 0.0
    ordered_heading: float = 45.0
    rudder: float = 0.0
    speed: float = 12.0
    throttle: float = 0.5
    wind_heading: float = 315.0
    wind_speed: float = 18.0
    sea_state: int = 4
    visibility_nm: float = 6.0
    score: float = 100.0
    held_seconds: float = 0.0
    completed_orders: int = 0
    elapsed: float = 0.0
    active: bool = True

@dataclass
class DamageState:
    hull: float = 100.0
    power: float = 100.0
    flooding: float = 22.0
    fire: float = 35.0
    smoke: float = 18.0
    crew_health: float = 100.0
    comms: float = 100.0
    steering: float = 100.0
    propulsion: float = 100.0
    fatigue: float = 12.0
    morale: float = 82.0
    elapsed: int = 0
    resolved: bool = False
    failed: bool = False
    log: List[str] = field(default_factory=lambda: ["Damage alarm: fire and flooding reported in machinery spaces."])
