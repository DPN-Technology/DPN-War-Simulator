from __future__ import annotations

import math
import time
import tkinter as tk
from typing import Dict, List, Optional, Tuple

from .config import APP_NAME, VERSION
from .firstperson3d import FirstPerson3DApp, project_point, shade
from .openworld import (
    CAMERA_HEIGHT, LAYERS, CONNECTORS, SHIP_ORIGIN_X, SHIP_ORIGIN_Y,
    SHIP_LENGTH_M, SHIP_WIDTH_M, SHIP_CENTER_X, SHIP_CENTER_Y, SHIP_ELEVATORS, SHIP_ISLAND_CENTER,
    current_layer, world_walkable, nearby_connector, nearest_static_interaction,
    layer_label, WorldInteraction, all_static_interactions,
)
from .living_world import (
    create_living_world, advance_life, update_crew_positions, eat_meal,
    sleep_period, medical_check, complete_maintenance, workboard_lines, needs_summary,
)
from .walkship import EQUIPMENT, HATCHES, interact as ship_interact, active_objective, STATION_ANCHORS
from .persistence import save_profile
from .ship_physics import (
    create_ship_physics, advance_ship_physics, sync_operational_damage, player_motion_modifiers,
    set_engine_order, set_rudder, cast_off, secure_to_berth, toggle_anchor, physics_summary,
    engine_label, training_depth_m,
)
from .naval_combat import (
    combat_from_dict, combat_to_dict, advance_naval_combat, combat_summary, combat_score,
    start_training_raid, set_general_quarters, cycle_track, acquire_selected_track,
    calculate_solution, select_battery, fire_selected_battery, service_ammunition,
    launch_cap, recover_cap, launch_training_strike, track_table_lines, ammunition_lines,
)
from .command import (
    command_from_dict, command_to_dict, advance_command, route_living_crew,
    command_summary, department_lines, order_lines, supply_lines, cycle_department,
    issue_order, authority_label, authority_level,
)
from .task_force import (
    task_force_from_dict, task_force_to_dict, advance_task_force, task_force_summary,
    friendly_lines, contact_lines, logistics_lines, set_formation, cycle_friendly, cycle_contact,
    toggle_radio_silence, order_selected_ship, start_surface_training_problem,
    engage_selected_contact, begin_replenishment,
)
from .campaign import (
    campaign_from_dict, campaign_to_dict, advance_campaign, campaign_summary,
    base_lines, convoy_lines, mission_lines, cycle_base, cycle_convoy, cycle_mission,
    accept_selected_mission, set_time_compression, effective_time_scale,
    request_port_service, dispatch_selected_for_repair,
)
from .physical_world import (
    physical_world_from_dict, physical_world_to_dict, advance_physical_world, cycle_weather,
    sky_colors, damage_world_pose, environment_summary,
)
from .flight_ops import (
    flight_from_dict, flight_to_dict, enter_cockpit, exit_cockpit, toggle_engine, adjust_throttle,
    toggle_gear, toggle_flaps, set_brakes, advance_flight, attempt_recovery, cockpit_summary,
)
from .flight_combat import (
    combat_from_dict as flight_combat_from_dict, combat_to_dict as flight_combat_to_dict,
    configure_sortie as configure_flight_combat, advance_air_combat, cycle_contact as cycle_flight_contact,
    cycle_waypoint as cycle_flight_waypoint, radio_report as flight_radio_report, fire_guns as flight_fire_guns,
    release_ordnance as flight_release_ordnance, emergency_abandon as flight_emergency_abandon,
    navigation_solution as flight_navigation_solution, contact_summary as flight_contact_summary,
    combat_summary as flight_combat_summary, selected_contact as selected_flight_contact,
)
from .air_wing import (
    air_wing_from_dict, air_wing_to_dict, advance_air_wing, air_wing_summary,
    squadron_lines, aircraft_lines, mission_lines as air_mission_lines,
    cycle_squadron, cycle_mission_type, adjust_sortie_size, plan_selected_mission,
    launch_selected_mission, recover_selected_mission, service_selected_squadron,
)
from .ground_ops import (
    ground_ops_from_dict, ground_ops_to_dict, advance_ground_ops, ground_summary,
    unit_lines as ground_unit_lines, vehicle_lines as ground_vehicle_lines, airfield_lines as ground_airfield_lines,
    mission_lines as ground_mission_lines, cycle_unit as cycle_ground_unit, cycle_vehicle as cycle_ground_vehicle,
    cycle_airfield as cycle_ground_airfield, cycle_mission as cycle_ground_mission, accept_selected_mission as accept_ground_mission,
    order_selected_unit_to_mission, order_selected_vehicle_to_mission, launch_amphibious_group, service_selected_airfield,
    add_air_support, enter_training_vehicle, exit_training_vehicle, toggle_drive_engine, adjust_drive_throttle, advance_training_vehicle,
)
from .ground_combat import (
    ground_combat_from_dict, ground_combat_to_dict, advance_ground_combat, ground_combat_summary,
    contact_lines as infantry_contact_lines, squad_lines as infantry_squad_lines, objective_lines as infantry_objective_lines,
    begin_engagement as begin_ground_engagement, end_engagement as end_ground_engagement, cycle_weapon as cycle_ground_weapon,
    cycle_contact as cycle_ground_contact, cycle_stance as cycle_ground_stance, toggle_aim as toggle_ground_aim,
    reload_weapon as reload_ground_weapon, fire_weapon as fire_ground_weapon, use_first_aid as ground_first_aid,
    order_squad as order_ground_squad, request_air_support as ground_air_support, request_naval_support as ground_naval_support,
    treat_selected_squad_casualty as treat_ground_casualty,
)
from .land_warfare import (
    land_warfare_from_dict, land_warfare_to_dict, advance_land_warfare, warfare_summary,
    unit_lines as land_unit_lines, vehicle_lines as land_vehicle_lines, sector_lines as land_sector_lines,
    contact_lines as land_contact_lines, logistics_lines as land_logistics_lines,
    begin_operation as begin_land_operation, cycle_unit as cycle_land_unit, cycle_vehicle as cycle_land_vehicle,
    cycle_sector as cycle_land_sector, cycle_contact as cycle_land_contact, order_selected_unit as order_land_unit,
    enter_selected_vehicle as enter_land_vehicle, exit_player_vehicle as exit_land_vehicle,
    toggle_vehicle_engine as toggle_land_vehicle_engine, adjust_vehicle_throttle as adjust_land_vehicle_throttle,
    steer_player_vehicle as steer_land_vehicle, player_vehicle as current_land_vehicle, fire_vehicle_weapon as fire_land_vehicle,
    request_artillery as land_artillery_support, request_joint_air_support as land_air_support,
    request_naval_gunfire as land_naval_support, resupply_selected_unit as land_resupply,
    begin_medevac as land_medevac, service_selected_vehicle as service_land_vehicle,
)
from .strategic_war import (
    strategic_war_from_dict, strategic_war_to_dict, advance_strategic_war, strategic_summary,
    sector_lines as strategic_sector_lines, formation_lines as strategic_formation_lines,
    depot_lines as strategic_depot_lines, route_lines as strategic_route_lines,
    operation_lines as strategic_operation_lines, begin_strategic_campaign,
    cycle_sector as cycle_strategic_sector, cycle_formation as cycle_strategic_formation,
    cycle_depot as cycle_strategic_depot, cycle_operation as cycle_strategic_operation,
    order_selected_formation as order_strategic_formation, accept_selected_operation as accept_strategic_operation,
    request_recon as strategic_recon, request_strategic_artillery, request_air_interdiction,
    request_coastal_naval_support, reinforce_selected_formation, repair_selected_bridge,
)
from .economy import (
    war_economy_from_dict, war_economy_to_dict, advance_war_economy, economy_summary,
    facility_lines as economy_facility_lines, production_lines as economy_production_lines,
    stockpile_lines as economy_stockpile_lines, research_lines as economy_research_lines,
    training_lines as economy_training_lines, begin_war_economy, cycle_facility as cycle_economy_facility,
    cycle_order as cycle_economy_order, cycle_research as cycle_economy_research,
    cycle_training as cycle_economy_training, cycle_allocation as cycle_economy_allocation,
    start_selected_order as start_economy_order, start_selected_research as start_economy_research,
    toggle_selected_training as toggle_economy_training, repair_selected_facility as repair_economy_facility,
    repair_transport_network as repair_economy_transport, allocate_stockpiles as allocate_economy_stockpiles,
)
from .logistics_network import (
    logistics_network_from_dict, logistics_network_to_dict, advance_logistics_network, logistics_summary,
    hub_lines as logistics_hub_lines, route_lines as logistics_route_lines, package_lines as logistics_package_lines,
    shipment_lines as logistics_shipment_lines, begin_logistics_network, cycle_hub as cycle_logistics_hub,
    cycle_route as cycle_logistics_route, cycle_package as cycle_logistics_package, cycle_shipment as cycle_logistics_shipment,
    cycle_priority as cycle_logistics_priority, dispatch_selected_shipment as dispatch_logistics_shipment,
    assign_escort as assign_logistics_escort, repair_selected_route as repair_logistics_route,
    repair_selected_hub as repair_logistics_hub, issue_selected_hub as issue_logistics_hub,
)
from .survivability import (
    create_survivability, survivability_from_dict, survivability_to_dict, survivability_tick,
    casualty_summary, compartment_lines, cycle_compartment, selected_compartment, apply_impact,
    fight_fire as survivability_fight_fire, start_dewatering, patch_breach, shore_structure,
    secure_ventilation as survivability_ventilation, toggle_boundary_for_selected,
    treat_casualties, order_abandon_ship, muster_abandon_ship, operational_factors,
)


# Physical world poses for the existing Enterprise station controls. The historical/operational
# behavior remains in walkship/enterprise; only the geometry/placement is new.
SHIP_EQUIPMENT_WORLD: Dict[str, Tuple[str,float,float]] = {
    "HELM": ("BRIDGE", 166, 22),
    "ENGINE_TELEGRAPH": ("BRIDGE", 174, 22),
    "BRIDGE_LOG": ("BRIDGE", 169, 26),
    "CIC_PLOT": ("ISLAND", 158, 21),
    "RADAR_CONSOLE": ("ISLAND", 174, 21),
    "RADIO_RACK": ("ISLAND", 158, 27),
    "RADIO_LOG": ("ISLAND", 162, 27),
    "AA_DIRECTOR": ("ISLAND", 178, 27),
    "TRACK_BOARD": ("ISLAND", 182, 27),
    "FLIGHT_CONTROL": ("FLIGHT", 178, 19),
    "ELEVATOR_1_TOP": ("FLIGHT", 58, 15),
    "ELEVATOR_2_TOP": ("FLIGHT", 121, 15),
    "ELEVATOR_3_TOP": ("FLIGHT", 188, 15),
    "DECK_SAFETY": ("FLIGHT", 166, 11),
    "FUEL_STATION": ("HANGAR", 52, 7),
    "ORDNANCE_STATION": ("HANGAR", 188, 7),
    "TUG_CONTROL": ("HANGAR", 121, 15),
    "ELEVATOR_1_BOTTOM": ("HANGAR", 58, 15),
    "ELEVATOR_2_BOTTOM": ("HANGAR", 121, 15),
    "ELEVATOR_3_BOTTOM": ("HANGAR", 188, 15),
    "ENG_CONSOLE": ("ENGINEERING", 92, 13),
    "LOAD_BOARD": ("ENGINEERING", 128, 13),
    "DC_BOARD": ("ENGINEERING", 172, 22),
    "BOUNDARY_BOARD": ("ENGINEERING", 202, 22),
    "MEDICAL_STAGING": ("LOWER", 146, 7),
    "COMMAND_DESK": ("BRIDGE", 178, 26),
}


# World-space dynamic hatches tied to the existing shipboard hatch state.
SHIP_HATCH_WORLD: Dict[str, Tuple[str,float,float]] = {
    "ISLAND_PORT": ("ISLAND", 166, 22),
    "ISLAND_STBD": ("ISLAND", 166, 26),
    "ENG_PORT": ("ENGINEERING", 111, 14),
    "ENG_STBD": ("ENGINEERING", 145, 16),
    "HANGAR_FWD": ("HANGAR", 74, 15),
    "HANGAR_AFT": ("HANGAR", 158, 15),
    "LOWER_MESS": ("LOWER", 121, 15),
    "ENG_MACH": ("ENGINEERING", 145, 22),
    "ISLAND_CIC": ("ISLAND", 165, 23),
    "ISLAND_RADIO": ("ISLAND", 174, 26),
}



class SeamlessOpenWorld3DApp(FirstPerson3DApp):
    """v2.7 CV-6 Midway-1942 reconstruction + streamable Unreal ship modules with all prior systems retained.

    All normal gameplay spaces exist in one coordinate system. Rooms/decks are not loaded as
    separate scenes; vertical travel changes only the player's z coordinate in the same renderer.
    """

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{VERSION} — Enterprise 1942 Visual Rebuild")
        self.world = "OPEN_WORLD"
        self.x = getattr(self.profile, "player_world_x", 10.0)
        self.y = getattr(self.profile, "player_world_y", 18.0)
        self.z = getattr(self.profile, "player_world_z", LAYERS["BASE"].floor_z + CAMERA_HEIGHT)
        self.yaw = getattr(self.profile, "player_world_yaw", 0.0)
        self.pitch = getattr(self.profile, "player_world_pitch", 0.0)
        # v2.5 expands the old 72 x 28 prototype carrier to a ~245 x 30 m ship.
        # Migrate old on-ship player coordinates once; shore saves are unchanged.
        if getattr(self.profile, "ship_layout_version", 1) < 2:
            feet=self.z-CAMERA_HEIGHT
            ship_floors=tuple(LAYERS[k].floor_z for k in ("LOWER","ENGINEERING","HANGAR","FLIGHT","ISLAND","BRIDGE"))
            if (SHIP_ORIGIN_X-.25 <= self.x <= SHIP_ORIGIN_X+72.5 and
                SHIP_ORIGIN_Y-.25 <= self.y <= SHIP_ORIGIN_Y+28.5 and
                any(abs(feet-fz)<.9 for fz in ship_floors)):
                old_lx=max(0.0,min(72.0,self.x-SHIP_ORIGIN_X))
                old_ly=max(0.0,min(28.0,self.y-SHIP_ORIGIN_Y))
                self.x=SHIP_ORIGIN_X+(old_lx/72.0)*SHIP_LENGTH_M
                self.y=SHIP_ORIGIN_Y+(old_ly/28.0)*SHIP_WIDTH_M
            self.profile.ship_layout_version=2
        if current_layer(self.x,self.y,self.z) is None:
            self.x, self.y, self.z = 10.0, 18.0, LAYERS["BASE"].floor_z + CAMERA_HEIGHT
            self.yaw, self.pitch = 0.0, 0.0
        self.life = create_living_world(self.profile.crew_seed)
        self.vertical_travel: Optional[dict] = None
        self.overlay = "welcome_open"
        self.message = "War Simulator v2.7 — CV-6 1942 reconstruction: denser period exterior, streamable UE ship/interior modules, and physical compartment framework are active."
        self.message_until = time.monotonic() + 8
        self.open_world_minutes = 0
        self._life_accum = 0.0
        self._last_layer = "BASE"
        self._last_autosave_minute = -1
        self.physics = create_ship_physics()
        self.physics.east_nm = getattr(self.profile, "ship_nav_east_nm", 0.0)
        self.physics.north_nm = getattr(self.profile, "ship_nav_north_nm", 0.0)
        self.physics.heading_deg = getattr(self.profile, "ship_heading_deg", 90.0)
        self.physics.speed_knots = getattr(self.profile, "ship_speed_knots", 0.0)
        self.physics.engine_order = getattr(self.profile, "ship_engine_order", 0.0)
        self.physics.rudder_deg = getattr(self.profile, "ship_rudder_deg", 0.0)
        self.physics.moored = getattr(self.profile, "ship_moored", True)
        self.physics.anchor_deployed = getattr(self.profile, "ship_anchor_deployed", False)
        self.physics.hull_integrity = getattr(self.profile, "ship_hull_integrity", 100.0)
        self.physics.sea_state = getattr(self.profile, "ship_sea_state", 3)
        self.ship_motion_seconds = 0.0
        self._last_physics_alarm = ""
        self.combat = combat_from_dict(getattr(self.profile, "combat_snapshot", {}))
        self.survivability = survivability_from_dict(getattr(self.profile, "survivability_snapshot", {}))
        self._last_sunk_state = self.survivability.sunk
        self._last_abandon_state = self.survivability.abandon_ship_ordered
        self._last_combat_kills = self.combat.enemy_destroyed
        self._last_combat_hits = self.combat.hits_taken
        self._last_combat_sorties = self.combat.air.sorties_launched
        self.command = command_from_dict(getattr(self.profile, "command_snapshot", {}))
        self._last_command_complete = self.command.orders_completed
        self._last_command_failed = self.command.orders_failed
        self.task_force = task_force_from_dict(
            getattr(self.profile, "task_force_snapshot", {}),
            self.physics.east_nm, self.physics.north_nm, self.physics.heading_deg,
        )
        self._last_fleet_surface = self.task_force.surface_contacts_defeated
        self._last_fleet_subs = self.task_force.submarines_defeated
        self._last_fleet_replenishments = self.task_force.logistics.replenishments
        self.campaign = campaign_from_dict(
            getattr(self.profile, "campaign_snapshot", {}), self.physics.east_nm, self.physics.north_nm
        )
        self._last_campaign_missions = self.campaign.missions_completed
        self._last_campaign_deliveries = self.campaign.convoy_deliveries
        self._last_campaign_port_services = self.campaign.port_services
        self._last_campaign_repairs = self.campaign.escort_repairs
        self.air_wing = air_wing_from_dict(getattr(self.profile, "air_wing_snapshot", {}), self.profile.crew_seed + 1500)
        self.physical_world = physical_world_from_dict(getattr(self.profile, "physical_world_snapshot", {}))
        self.flight = flight_from_dict(getattr(self.profile, "flight_ops_snapshot", {}))
        self.flight_combat = flight_combat_from_dict(getattr(self.profile, "flight_combat_snapshot", {}))
        self.ground_ops = ground_ops_from_dict(getattr(self.profile, "ground_ops_snapshot", {}))
        self.ground_combat = ground_combat_from_dict(getattr(self.profile, "ground_combat_snapshot", {}))
        self.land_warfare = land_warfare_from_dict(getattr(self.profile, "land_warfare_snapshot", {}))
        self.strategic_war = strategic_war_from_dict(getattr(self.profile, "strategic_war_snapshot", {}))
        self._strategic_last_land_ops = self.land_warfare.operations_completed
        self._last_strategic_operations = self.strategic_war.operations_completed
        self._last_strategic_failed = self.strategic_war.operations_failed
        self._last_strategic_front_shifts = self.strategic_war.front_shifts
        self._last_strategic_recon = self.strategic_war.recon_reports
        self._last_strategic_supply = self.strategic_war.supply_deliveries
        self._last_strategic_reinforcements = self.strategic_war.reinforcement_waves
        self._last_strategic_bridges = self.strategic_war.bridges_repaired
        self.war_economy = war_economy_from_dict(getattr(self.profile, "war_economy_snapshot", {}))
        self._last_economy_orders = self.war_economy.orders_completed
        self._last_economy_allocations = self.war_economy.allocations
        self._last_economy_repairs = self.war_economy.facilities_repaired
        self._last_economy_research = self.war_economy.research_completed
        self._last_economy_graduates = self.war_economy.personnel_graduated
        self._last_economy_infra = self.war_economy.infrastructure_repairs
        self.logistics_network = logistics_network_from_dict(getattr(self.profile, "logistics_network_snapshot", {}))
        self._last_logistics_delivered = self.logistics_network.delivered_shipments
        self._last_logistics_lost = self.logistics_network.lost_shipments
        self._last_logistics_delayed = self.logistics_network.delayed_shipments
        self._last_logistics_escorted = self.logistics_network.escorted_shipments
        self._last_logistics_route_repairs = self.logistics_network.route_repairs
        self._last_logistics_hub_repairs = self.logistics_network.hub_repairs
        self._last_logistics_hub_issues = self.logistics_network.hub_issues
        self._last_land_ops_complete = self.land_warfare.operations_completed
        self._last_land_ops_failed = self.land_warfare.operations_failed
        self._last_land_sectors = self.land_warfare.sectors_secured
        self._last_land_artillery = self.land_warfare.artillery_missions
        self._last_land_medevac = self.land_warfare.medevac_actions
        self._last_land_resupply = self.land_warfare.resupply_actions
        self._last_ground_combat_runs = self.ground_combat.engagements_completed
        self._last_ground_combat_losses = self.ground_combat.training_losses
        self._last_ground_missions = self.ground_ops.missions_completed
        self._last_ground_landings = self.ground_ops.amphibious_landings
        self._last_ground_services = self.ground_ops.airfield_services
        self._last_ground_supplies = self.ground_ops.supplies_delivered
        # Active cockpit, pilot-survival and ground-operations states are persisted explicitly from v1.7-v1.9 onward.
        self._flight_message_latch = ""
        self._last_air_missions = sum(1 for m in self.air_wing.missions.values() if m.status == "COMPLETE")
        self._last_air_sorties_launched = self.air_wing.sorties_launched
        self._last_air_sorties_recovered = self.air_wing.sorties_recovered
        self._last_air_scout_reports = self.air_wing.scout_reports
        self._walk_phase = 0.0
        # v2.5 renderer budget. BALANCED is the default because the old 50-FPS
        # Tk Canvas loop generated thousands of objects and could stutter badly.
        self.visual_quality = "BALANCED"
        self.render_distance = 22.0
        self.detail_radius = 7.5
        self.entity_radius = 8.5
        self.target_frame_ms = 33.3
        self._render_ms = 0.0
        self._adaptive_slow_frames = 0
        self.hud_expanded = False
        self.canvas.bind("<ButtonPress-3>", self._ground_right_click)

    # -------------------- input / movement --------------------
    def _mouse_start(self, event):
        # In infantry mode, left click fires while drag still supplies mouse-look.
        if getattr(getattr(self, "ground_combat", None), "player", None) and self.ground_combat.player.active and not self.overlay:
            ok,msg=fire_ground_weapon(self.ground_combat,self.x,self.y,math.degrees(self.yaw)%360.0)
            if ok or "empty" in msg.lower() or "reload" in msg.lower(): self._set_message(msg,2)
        super()._mouse_start(event)

    def _ground_right_click(self, event):
        if getattr(getattr(self, "ground_combat", None), "player", None) and self.ground_combat.player.active and not self.overlay:
            self._set_message(toggle_ground_aim(self.ground_combat),2)
            self.canvas.focus_set()

    def _key_down(self, event):
        key = event.keysym.lower()
        if key in self.keys:
            return
        self.keys.add(key)
        if getattr(getattr(self,"land_warfare",None),"player_vehicle_key",""):
            if self.overlay == "land_vehicle_help":
                if key in ("escape","e","h","return","space"): self.overlay=None
                return
            if key == "w": self._set_message(adjust_land_vehicle_throttle(self.land_warfare,+0.15),2)
            elif key == "s": self._set_message(adjust_land_vehicle_throttle(self.land_warfare,-0.15),2)
            elif key == "i":
                _,msg=toggle_land_vehicle_engine(self.land_warfare); self._set_message(msg,3)
            elif key == "b":
                v=current_land_vehicle(self.land_warfare); v.brake=not v.brake; self._set_message(f"{v.name} brake {'SET' if v.brake else 'RELEASED'}.",2)
            elif key == "space":
                _,msg=fire_land_vehicle(self.land_warfare); self._set_message(msg,4)
            elif key == "t":
                c=cycle_land_contact(self.land_warfare); self._set_message(f"Battlefield contact: {c.label if c else 'NONE'}.",3)
            elif key == "e":
                v=current_land_vehicle(self.land_warfare); ok,msg=exit_land_vehicle(self.land_warfare)
                if ok and v:
                    self.x,self.y,self.z=v.x,v.y,LAYERS["BASE"].floor_z+CAMERA_HEIGHT
                self._set_message(msg,4)
            elif key == "escape": self.overlay="land_vehicle_help"
            return
        if getattr(getattr(self,"ground_ops",None),"drive",None) and self.ground_ops.drive.active:
            if self.overlay == "ground_vehicle_help":
                if key in ("escape","e","h","return","space"): self.overlay=None
                return
            if key == "w": self._set_message(adjust_drive_throttle(self.ground_ops,+0.15),2)
            elif key == "s": self._set_message(adjust_drive_throttle(self.ground_ops,-0.15),2)
            elif key == "i": self._set_message(toggle_drive_engine(self.ground_ops),3)
            elif key == "b": self.ground_ops.drive.brake=not self.ground_ops.drive.brake; self._set_message(f"Vehicle brake {'SET' if self.ground_ops.drive.brake else 'RELEASED'}.",2)
            elif key == "e":
                ok,msg=exit_training_vehicle(self.ground_ops)
                if ok:
                    self.x,self.y=self.ground_ops.drive.x,self.ground_ops.drive.y
                    self.z=LAYERS["BASE"].floor_z+CAMERA_HEIGHT
                self._set_message(msg,4)
            elif key == "escape": self.overlay="ground_vehicle_help"
            return
        if getattr(getattr(self,"flight",None),"active",False):
            if self.overlay == "flight_help":
                if key in ("escape","e","h","return","space"): self.overlay=None
                return
            if key == "w": self._set_message(adjust_throttle(self.flight, +0.10), 2)
            elif key == "s": self._set_message(adjust_throttle(self.flight, -0.10), 2)
            elif key == "i": self._set_message(toggle_engine(self.flight), 3)
            elif key == "g": self._set_message(toggle_gear(self.flight), 3)
            elif key == "f": self._set_message(toggle_flaps(self.flight), 3)
            elif key == "b": self.flight.brakes = not self.flight.brakes; self._set_message(f"Wheel brakes {'SET' if self.flight.brakes else 'RELEASED'}.", 2)
            elif key == "space":
                ok,msg=flight_fire_guns(self.flight_combat,self.flight); self._set_message(msg,4)
            elif key == "t":
                ok,msg=flight_release_ordnance(self.flight_combat,self.flight); self._set_message(msg,5)
            elif key == "j":
                c=cycle_flight_contact(self.flight_combat); self._set_message(f"Selected target: {c.key} {c.label}." if c else "No active training contacts.",3)
            elif key == "m":
                self._set_message(cycle_flight_waypoint(self.flight_combat,self.physics.east_nm,self.physics.north_nm),3)
            elif key == "q":
                self._set_message(flight_radio_report(self.flight_combat,self.flight,self.physics.east_nm,self.physics.north_nm),5)
            elif key == "x":
                ac_key=self.flight.aircraft_key
                ok,msg=flight_emergency_abandon(self.flight_combat,self.flight)
                if ok:
                    ac=self.air_wing.aircraft.get(ac_key)
                    if ac:
                        if ac.status != "LOST": self.air_wing.aircraft_lost += 1
                        ac.status="LOST"; ac.deck="AIR"; ac.condition=0.0
                        for mission in self.air_wing.missions.values():
                            if ac.key in mission.aircraft_keys and mission.status not in ("COMPLETE","LOST"):
                                mission.aircraft_lost += 1
                        crew=self.air_wing.aircrew.get(ac.pilot_key)
                        if crew:
                            crew.available=False; crew.injuries=max(crew.injuries,18.0)
                    self.overlay="pilot_survival"
                self._set_message(msg,6)
            elif key == "l":
                safe=not self.survivability.sunk and operational_factors(self.survivability)["aviation"]>35
                ok,msg=attempt_recovery(self.flight,self.physics.east_nm,self.physics.north_nm,self.physics.heading_deg,self.shipboard.enterprise.wind_over_deck,safe)
                if ok:
                    ac=self.air_wing.aircraft.get(self.flight.aircraft_key)
                    if ac:
                        ac.status="GROUNDED"; ac.deck="FLIGHT"; ac.fuel_pct=self.flight.fuel_pct; ac.condition=min(ac.condition,self.flight.airframe_health)
                        crew=self.air_wing.aircrew.get(ac.pilot_key)
                        if crew:
                            crew.injuries=max(crew.injuries,100.0-self.flight.pilot_health)
                    self.profile.carrier_landings += 1
                    if self.flight_combat.active_sortie:
                        self.flight_combat.active_sortie=False; self.flight_combat.mission_debriefs += 1
                        self.flight_combat.last_event=f"MISSION DEBRIEF — score {self.flight_combat.score:.0f}% • A/A {self.flight_combat.aerial_victories} • A/S {self.flight_combat.surface_hits}."
                self._set_message(msg,5)
            elif key == "e":
                ok,msg=exit_cockpit(self.flight)
                if ok:
                    self.x,self.y,self.z=SHIP_ORIGIN_X+121.0,SHIP_ORIGIN_Y+15.0,LAYERS["FLIGHT"].floor_z+CAMERA_HEIGHT
                    self.profile.cockpit_flights += 1
                self._set_message(msg,4)
            elif key == "escape": self.overlay="flight_help"
            return
        if getattr(getattr(self,"ground_combat",None),"player",None) and self.ground_combat.player.active:
            if self.overlay == "ground_combat_help":
                if key in ("escape","e","h","return"): self.overlay=None
                return
            if key in ("1","2","3"):
                self.ground_combat.player.selected_weapon={"1":"RIFLE","2":"AUTO","3":"SIDEARM"}[key]
                w=self.ground_combat.weapons[self.ground_combat.player.selected_weapon]
                self._set_message(f"Selected {w.name} — {w.magazine_rounds}/{w.reserve_rounds}.",2)
            elif key == "space":
                _,msg=fire_ground_weapon(self.ground_combat,self.x,self.y,math.degrees(self.yaw)%360.0); self._set_message(msg,2)
            elif key == "r":
                _,msg=reload_ground_weapon(self.ground_combat); self._set_message(msg,3)
            elif key == "c": self._set_message(cycle_ground_stance(self.ground_combat),2)
            elif key == "t":
                c=cycle_ground_contact(self.ground_combat); self._set_message(f"Ground target: {c.label if c else 'NONE'}.",2)
            elif key == "j":
                orders=("FOLLOW","HOLD","SUPPRESS","ASSAULT","FALL BACK")
                cur=self.ground_combat.selected_order if self.ground_combat.selected_order in orders else "FOLLOW"
                order=orders[(orders.index(cur)+1)%len(orders)]
                _,msg=order_ground_squad(self.ground_combat,order,self.x,self.y); self._set_message(msg,3)
            elif key == "h":
                _,msg=ground_first_aid(self.ground_combat); self._set_message(msg,3)
            elif key == "m":
                _,msg=treat_ground_casualty(self.ground_combat); self._set_message(msg,3)
            elif key == "5":
                _,msg=ground_air_support(self.ground_combat,self.ground_ops,self.x,self.y); self._set_message(msg,5)
            elif key == "6":
                _,msg=ground_naval_support(self.ground_combat,self.task_force,self.x,self.y); self._set_message(msg,5)
            elif key == "g": self.overlay="ground_combat_console"
            elif key == "f": self._set_message(self._objective_text(),5)
            elif key == "e": self._interact()
            elif key == "x":
                _,msg=end_ground_engagement(self.ground_combat); self._set_message(msg,4)
            elif key == "escape": self.overlay="ground_combat_help"
            return
        if self.overlay:
            self._overlay_key(key)
            return
        if key == "e":
            self._interact()
        elif key == "f":
            self._set_message(self._objective_text(), 6)
        elif key == "r":
            self.running_time = not self.running_time
            self.shipboard.running = self.running_time
            self._set_message(f"Ship clock {'RUNNING' if self.running_time else 'PAUSED'} — historical duties and daily routine advance together.", 4)
        elif key == "escape":
            self.overlay = "pause_open"
        elif key == "f1":
            self.overlay = "help_open"
        elif key == "f11":
            self.fullscreen = not self.fullscreen
            self.attributes("-fullscreen", self.fullscreen)
        elif key == "n":
            self.overlay = "navigation"
        elif key == "b":
            self.overlay = "combat_plot"
        elif key == "f6":
            self.overlay = "survivability_dc"
        elif key == "k":
            self.overlay = "air_wing_console"
        elif key == "g":
            self.overlay = "ground_console"
        elif key == "c":
            self.overlay = "command_console"
        elif key == "v":
            self.overlay = "fleet_console"
        elif key == "o":
            self.overlay = "campaign_console"
        elif key == "f7":
            self._set_message(cycle_weather(self.physical_world), 4)
        elif key == "f8":
            self.overlay = "land_command"
        elif key == "f10":
            self.overlay = "strategic_command"
        elif key == "f12":
            self.overlay = "economy_console"
        elif key == "tab":
            self.hud_expanded = not self.hud_expanded
            self._set_message(f"Systems HUD {'expanded' if self.hud_expanded else 'compact'}.",2)
        elif key == "f4":
            modes=("PERFORMANCE","BALANCED","HIGH")
            self.visual_quality=modes[(modes.index(self.visual_quality)+1)%len(modes)]
            if self.visual_quality=="PERFORMANCE":
                self.render_distance,self.detail_radius,self.entity_radius=20.0,6.0,7.0
            elif self.visual_quality=="HIGH":
                self.render_distance,self.detail_radius,self.entity_radius=34.0,13.0,14.0
            else:
                self.render_distance,self.detail_radius,self.entity_radius=22.0,7.5,8.5
            self._set_message(f"Visual quality: {self.visual_quality}. F4 cycles quality modes.",4)
        elif key == "f5":
            self.overlay = "logistics_console"
        elif key == "f9":
            # Emergency relocation only; not part of normal traversal. Disabled while vessel is away from berth.
            if self.physics.moored:
                self.x, self.y, self.z = 10.0, 18.0, LAYERS["BASE"].floor_z + CAMERA_HEIGHT
                self.vertical_travel = None
                self._set_message("Emergency relocation to Naval Training Base.", 4)
            else:
                self._set_message("Emergency shore relocation blocked while Enterprise is underway.", 4)

    def _loop(self):
        """Frame-budgeted loop for the software renderer.

        The inherited v0.7 loop always slept another 20 ms after rendering, which
        amplified stutter once frame rendering itself became expensive.  v2.5 aims
        for a stable ~30 FPS and schedules only the remaining frame budget.
        """
        if self.destroyed:
            return
        frame_start=time.perf_counter()
        now=time.monotonic()
        dt=min(0.08,max(0.001,now-self.last_tick)); self.last_tick=now
        self._update(dt); self._render()
        self._render_ms=(time.perf_counter()-frame_start)*1000.0
        self._frames+=1
        if now-self._fps_time>=1.0:
            self.fps=self._frames; self._frames=0; self._fps_time=now
            # Automatic emergency LOD only lowers visual density after sustained
            # slow frames; it never changes simulation fidelity.
            if self.visual_quality=="BALANCED":
                if self._render_ms>45: self._adaptive_slow_frames+=1
                else: self._adaptive_slow_frames=max(0,self._adaptive_slow_frames-1)
                if self._adaptive_slow_frames>=4:
                    self.detail_radius=max(6.2,self.detail_radius-.5)
                    self.entity_radius=max(7.2,self.entity_radius-.4)
                    self.entity_radius=max(8.5,self.entity_radius-.8)
                    self._adaptive_slow_frames=0
        delay=max(1,int(self.target_frame_ms-self._render_ms))
        self.after(delay,self._loop)

    def _update(self, dt: float):
        # Menus/records are in-world interfaces, not scene loads. Only the explicit pause overlay
        # freezes simulation; other terminals can stay open while a running world clock continues.
        hard_paused = self.overlay == "pause_open"
        controls_blocked = self.overlay is not None
        if hard_paused:
            return
        # Seamless ladder/elevator travel animation; no scene replacement.
        if self.vertical_travel:
            t = min(1.0, (time.monotonic()-self.vertical_travel["start"]) / self.vertical_travel["duration"])
            eased = t*t*(3-2*t)
            self.z = self.vertical_travel["from_camera"] + (self.vertical_travel["to_camera"]-self.vertical_travel["from_camera"]) * eased
            # Climb motion stays in the same coordinate space and adds a small hand-over-hand body sway.
            sway = math.sin(math.pi*t) * 0.16
            self.x = self.vertical_travel["from_x"] + math.cos(self.vertical_travel["yaw"])*sway
            self.y = self.vertical_travel["from_y"] + math.sin(self.vertical_travel["yaw"])*sway
            if t >= 1.0:
                name = self.vertical_travel["name"]
                self.x,self.y = self.vertical_travel["from_x"],self.vertical_travel["from_y"]
                self.vertical_travel = None
                self._set_message(f"Arrived via {name}: {layer_label(self.x,self.y,self.z)}.", 3)
        elif self.land_warfare.player_vehicle_key and not controls_blocked and not self.flight.active:
            v=current_land_vehicle(self.land_warfare)
            ox,oy,oh=v.x,v.y,v.heading_deg
            steer=(1 if "d" in self.keys else 0)-(1 if "a" in self.keys else 0)
            steer_land_vehicle(self.land_warfare,steer,dt)
            camz=LAYERS["BASE"].floor_z+CAMERA_HEIGHT
            if world_walkable(v.x,v.y,camz):
                self.x,self.y,self.z=v.x,v.y,camz; self.yaw=math.radians(v.heading_deg)
            else:
                v.x,v.y,v.heading_deg=ox,oy,oh; v.speed_mps=0.0; self.x,self.y,self.z=ox,oy,camz
        elif self.ground_ops.drive.active and not controls_blocked and not self.flight.active:
            d=self.ground_ops.drive
            ox,oy,oh=d.x,d.y,d.heading_deg
            steer=(1 if "d" in self.keys else 0)-(1 if "a" in self.keys else 0)
            nx,ny,nh=advance_training_vehicle(self.ground_ops,dt,steer,brake=d.brake)
            camz=LAYERS["BASE"].floor_z+CAMERA_HEIGHT
            if world_walkable(nx,ny,camz):
                self.x,self.y,self.z=nx,ny,camz
                self.yaw=math.radians(nh)
            else:
                d.x,d.y,d.heading_deg=ox,oy,oh; d.speed_mps=0.0
                self.x,self.y,self.z=ox,oy,camz
        elif not controls_blocked and not self.flight.active and not self.ground_ops.drive.active and not self.land_warfare.player_vehicle_key:
            turn = ((1 if "right" in self.keys else 0) - (1 if "left" in self.keys else 0))
            self.yaw += turn * dt * 2.1
            self.pitch += ((1 if "up" in self.keys else 0) - (1 if "down" in self.keys else 0)) * dt
            self.pitch = max(-0.62, min(0.62, self.pitch))
            forward = (1 if "w" in self.keys else 0) - (1 if "s" in self.keys else 0)
            strafe = (1 if "d" in self.keys else 0) - (1 if "a" in self.keys else 0)
            if forward or strafe:
                self._move_open_world(forward, strafe, dt)
                self._walk_phase = (self._walk_phase + dt * (11.0 if "shift_l" in self.keys or "shift_r" in self.keys else 7.0)) % (math.pi * 2)

        update_crew_positions(self.life, dt)
        radar_rt = self.shipboard.equipment_runtime.get("RADAR_CONSOLE")
        advance_physical_world(
            self.physical_world, dt, self.life.minute_of_day, self.physics.sea_state,
            self.physics.speed_knots, self.shipboard.hatches,
            radar_operational=not bool(radar_rt and radar_rt.fault),
        )

        if self.flight.active:
            roll_input=(1 if "d" in self.keys else 0)-(1 if "a" in self.keys else 0)
            pitch_input=(1 if "up" in self.keys else 0)-(1 if "down" in self.keys else 0)
            yaw_input=(1 if "right" in self.keys else 0)-(1 if "left" in self.keys else 0)
            before_airborne=not self.flight.on_deck
            evt=advance_flight(self.flight,dt,self.physics.east_nm,self.physics.north_nm,self.physics.heading_deg,
                               self.physics.speed_knots,self.shipboard.enterprise.wind_over_deck,self.physics.sea_state,
                               roll_input,pitch_input,yaw_input)
            if evt: self._set_message(evt,5)
            if not self.flight.on_deck and not before_airborne:
                ac=self.air_wing.aircraft.get(self.flight.aircraft_key)
                if ac: ac.status="AIRBORNE"; ac.deck="AIR"
                self.profile.carrier_takeoffs += 1
                mission_type="CAP" if self.flight.aircraft_key.startswith("VF6") else ("SCOUT" if self.flight.aircraft_key.startswith("VS6") else "STRIKE")
                target_e=target_n=None
                for mission in self.air_wing.missions.values():
                    if self.flight.aircraft_key in mission.aircraft_keys and mission.status not in ("COMPLETE","LOST"):
                        mission_type=mission.mission_type; target_e=mission.target_east_nm; target_n=mission.target_north_nm; break
                self._set_message(configure_flight_combat(self.flight_combat,self.flight,mission_type,self.physics.east_nm,self.physics.north_nm,self.physics.heading_deg,target_e,target_n),5)
            if self.flight.active:
                ac=self.air_wing.aircraft.get(self.flight.aircraft_key)
                if ac: ac.fuel_pct=self.flight.fuel_pct
                self.profile.pilot_distance_nm=max(self.profile.pilot_distance_nm,self.flight.distance_nm)

        air_evt=advance_air_combat(self.flight_combat,self.flight,dt,self.physics.east_nm,self.physics.north_nm)
        if air_evt:
            self._set_message(air_evt,6)
            if self.flight_combat.pilot_safe and self.overlay=="pilot_survival":
                ac=self.air_wing.aircraft.get(self.flight.aircraft_key)
                if ac:
                    crew=self.air_wing.aircrew.get(ac.pilot_key)
                    if crew: crew.available=True
                self.x,self.y,self.z=SHIP_ORIGIN_X+146.0,SHIP_ORIGIN_Y+7.0,LAYERS["LOWER"].floor_z+CAMERA_HEIGHT
                self.overlay=None

        # v0.9 vessel physics run continuously in real time. Interior coordinates remain ship-local
        # while navigation position, heading, speed, sea motion and inertial forces evolve outside.
        sync_operational_damage(self.physics, self.shipboard)
        casualty_active = bool(self.survivability.sunk or self.survivability.abandon_ship_ordered or self.survivability.structural_strength_pct < 88.0)
        nav_scale = effective_time_scale(self.campaign, combat_active=self.combat.raid_active, casualty_active=casualty_active, collision_alarm=self.physics.collision_alarm)
        nav_dt = dt * nav_scale
        advance_ship_physics(self.physics, nav_dt)
        self.ship_motion_seconds += nav_dt if not self.physics.moored else 0.0
        ent = self.shipboard.enterprise
        ent.bridge_heading = self.physics.heading_deg
        ent.speed_knots = max(0.0, self.physics.speed_knots)
        ent.rudder = self.physics.rudder_deg
        ent.wind_over_deck = max(0.0, self.physics.speed_knots + self.physics.wind_speed_knots * 0.45)
        if self.physics.collision_alarm and self._last_physics_alarm != "GROUNDING":
            self._last_physics_alarm = "GROUNDING"
            self._set_message("GROUNDING / COLLISION ALARM — reduce power, assess depth and back clear if possible.", 6)
        elif not self.physics.collision_alarm:
            self._last_physics_alarm = ""

        fleet_messages = advance_task_force(self.task_force, self.physics, nav_dt)
        if self.task_force.surface_contacts_defeated > self._last_fleet_surface:
            delta = self.task_force.surface_contacts_defeated - self._last_fleet_surface
            self.profile.fleet_surface_contacts_defeated += delta
            self._last_fleet_surface = self.task_force.surface_contacts_defeated
        if self.task_force.submarines_defeated > self._last_fleet_subs:
            delta = self.task_force.submarines_defeated - self._last_fleet_subs
            self.profile.fleet_submarines_defeated += delta
            self._last_fleet_subs = self.task_force.submarines_defeated
        if self.task_force.logistics.replenishments > self._last_fleet_replenishments:
            delta = self.task_force.logistics.replenishments - self._last_fleet_replenishments
            self.profile.fleet_replenishments += delta
            self._last_fleet_replenishments = self.task_force.logistics.replenishments
        if fleet_messages:
            self._set_message(fleet_messages[-1], 5)

        campaign_messages = advance_campaign(self.campaign, self.physics, self.task_force, nav_dt)
        if self.campaign.missions_completed > self._last_campaign_missions:
            delta = self.campaign.missions_completed - self._last_campaign_missions
            self.profile.campaign_missions_completed += delta
            self.profile.xp += 35 * delta
            self.profile.add_log(f"Completed {delta} naval campaign operation(s).")
            self._last_campaign_missions = self.campaign.missions_completed
        if self.campaign.convoy_deliveries > self._last_campaign_deliveries:
            self.profile.campaign_convoy_deliveries += self.campaign.convoy_deliveries - self._last_campaign_deliveries
            self._last_campaign_deliveries = self.campaign.convoy_deliveries
        if self.campaign.port_services > self._last_campaign_port_services:
            self.profile.campaign_port_services += self.campaign.port_services - self._last_campaign_port_services
            self._last_campaign_port_services = self.campaign.port_services
        if self.campaign.escort_repairs > self._last_campaign_repairs:
            self.profile.campaign_escort_repairs += self.campaign.escort_repairs - self._last_campaign_repairs
            self._last_campaign_repairs = self.campaign.escort_repairs
        self.profile.campaign_best_score = max(self.profile.campaign_best_score, self.campaign.operational_score)
        if campaign_messages:
            self._set_message(campaign_messages[-1], 5)

        air_messages = advance_air_wing(self.air_wing, nav_dt, self.physics.east_nm, self.physics.north_nm, self.physics.sea_state)
        complete_now = sum(1 for m in self.air_wing.missions.values() if m.status == "COMPLETE")
        if complete_now > self._last_air_missions:
            delta = complete_now - self._last_air_missions
            self.profile.air_wing_missions_completed += delta
            self.profile.xp += 20 * delta
            self.profile.add_log(f"Completed {delta} carrier air-wing mission(s).")
            add_air_support(self.ground_ops, 12.0 * delta, "completed carrier-air missions")
            self._last_air_missions = complete_now
        if self.air_wing.sorties_launched > self._last_air_sorties_launched:
            self.profile.air_wing_sorties_launched += self.air_wing.sorties_launched - self._last_air_sorties_launched
            self._last_air_sorties_launched = self.air_wing.sorties_launched
        if self.air_wing.sorties_recovered > self._last_air_sorties_recovered:
            self.profile.air_wing_sorties_recovered += self.air_wing.sorties_recovered - self._last_air_sorties_recovered
            self._last_air_sorties_recovered = self.air_wing.sorties_recovered
        if self.air_wing.scout_reports > self._last_air_scout_reports:
            self.profile.air_wing_scout_reports += self.air_wing.scout_reports - self._last_air_scout_reports
            self._last_air_scout_reports = self.air_wing.scout_reports
        self.profile.air_wing_best_score = max(self.profile.air_wing_best_score, self.air_wing.operational_score)
        if air_messages:
            self._set_message(air_messages[-1], 5)

        # v1.9 expeditionary ground/airbase/amphibious operations share the same operational clock.
        # Completed carrier-air missions contribute limited abstract air-support value without revealing hidden history.
        ground_messages = advance_ground_ops(self.ground_ops, nav_dt, self.campaign)
        if self.ground_ops.missions_completed > self._last_ground_missions:
            delta=self.ground_ops.missions_completed-self._last_ground_missions
            self.profile.ground_missions_completed += delta
            self.profile.xp += 40*delta
            self.profile.add_log(f"Completed {delta} expeditionary ground operation(s).")
            self._last_ground_missions=self.ground_ops.missions_completed
        if self.ground_ops.amphibious_landings > self._last_ground_landings:
            self.profile.ground_amphibious_landings += self.ground_ops.amphibious_landings-self._last_ground_landings
            self._last_ground_landings=self.ground_ops.amphibious_landings
        if self.ground_ops.airfield_services > self._last_ground_services:
            self.profile.ground_airfield_services += self.ground_ops.airfield_services-self._last_ground_services
            self._last_ground_services=self.ground_ops.airfield_services
        if self.ground_ops.supplies_delivered > self._last_ground_supplies:
            self.profile.ground_supplies_delivered += self.ground_ops.supplies_delivered-self._last_ground_supplies
            self._last_ground_supplies=self.ground_ops.supplies_delivered
        self.profile.ground_vehicle_distance_m=max(self.profile.ground_vehicle_distance_m,self.ground_ops.drive.distance_m)
        self.profile.ground_ops_best_score=max(self.profile.ground_ops_best_score,self.ground_ops.operational_score)
        if ground_messages:
            self._set_message(ground_messages[-1],5)

        # v2.1 battalion-scale land warfare runs in the same continuous shore/battlefield coordinate space.
        land_messages = advance_land_warfare(self.land_warfare, dt)
        if self.land_warfare.operations_completed > self._last_land_ops_complete:
            delta=self.land_warfare.operations_completed-self._last_land_ops_complete
            self.profile.land_operations_completed += delta; self.profile.xp += 70*delta
            self.profile.add_log(f"Completed {delta} battalion-scale field operation(s).")
            if self.land_warfare.score>=75: self.profile.qualifications["Battalion Field Operations Practical"] = True
            self._last_land_ops_complete=self.land_warfare.operations_completed
        if self.land_warfare.operations_failed > self._last_land_ops_failed:
            self.profile.land_operations_failed += self.land_warfare.operations_failed-self._last_land_ops_failed
            self._last_land_ops_failed=self.land_warfare.operations_failed
        if self.land_warfare.sectors_secured > self._last_land_sectors:
            self.profile.land_sectors_secured += self.land_warfare.sectors_secured-self._last_land_sectors
            self._last_land_sectors=self.land_warfare.sectors_secured
        if self.land_warfare.artillery_missions > self._last_land_artillery:
            self.profile.land_artillery_missions += self.land_warfare.artillery_missions-self._last_land_artillery
            self._last_land_artillery=self.land_warfare.artillery_missions
        if self.land_warfare.medevac_actions > self._last_land_medevac:
            self.profile.land_medevac_actions += self.land_warfare.medevac_actions-self._last_land_medevac
            self._last_land_medevac=self.land_warfare.medevac_actions
        if self.land_warfare.resupply_actions > self._last_land_resupply:
            self.profile.land_resupply_actions += self.land_warfare.resupply_actions-self._last_land_resupply
            self._last_land_resupply=self.land_warfare.resupply_actions
        self.profile.land_armored_kills=max(self.profile.land_armored_kills,self.land_warfare.armored_kills)
        self.profile.land_warfare_best_score=max(self.profile.land_warfare_best_score,self.land_warfare.score if self.land_warfare.phase=="COMPLETE" else 0.0)
        self.profile.land_vehicle_distance_m=max(self.profile.land_vehicle_distance_m,sum(v.distance_m for v in self.land_warfare.vehicles.values()))
        if land_messages: self._set_message(land_messages[-1],5)

        # v2.2 strategic war layer persists above tactical battalion combat and can absorb tactical victories.
        strategic_messages, self._strategic_last_land_ops = advance_strategic_war(
            self.strategic_war, dt, self.land_warfare, self.ground_ops, self.task_force, self.campaign, self._strategic_last_land_ops, self.war_economy
        )
        if self.strategic_war.operations_completed > self._last_strategic_operations:
            delta=self.strategic_war.operations_completed-self._last_strategic_operations
            self.profile.strategic_operations_completed += delta; self.profile.xp += 110*delta
            self.profile.add_log(f"Completed {delta} theater-level strategic operation(s).")
            self._last_strategic_operations=self.strategic_war.operations_completed
        if self.strategic_war.operations_failed > self._last_strategic_failed:
            self.profile.strategic_operations_failed += self.strategic_war.operations_failed-self._last_strategic_failed
            self._last_strategic_failed=self.strategic_war.operations_failed
        if self.strategic_war.front_shifts > self._last_strategic_front_shifts:
            self.profile.strategic_front_shifts += self.strategic_war.front_shifts-self._last_strategic_front_shifts
            self._last_strategic_front_shifts=self.strategic_war.front_shifts
        if self.strategic_war.recon_reports > self._last_strategic_recon:
            self.profile.strategic_recon_reports += self.strategic_war.recon_reports-self._last_strategic_recon
            self._last_strategic_recon=self.strategic_war.recon_reports
        if self.strategic_war.supply_deliveries > self._last_strategic_supply:
            self.profile.strategic_supply_deliveries += self.strategic_war.supply_deliveries-self._last_strategic_supply
            self._last_strategic_supply=self.strategic_war.supply_deliveries
        if self.strategic_war.reinforcement_waves > self._last_strategic_reinforcements:
            self.profile.strategic_reinforcement_waves += self.strategic_war.reinforcement_waves-self._last_strategic_reinforcements
            self._last_strategic_reinforcements=self.strategic_war.reinforcement_waves
        if self.strategic_war.bridges_repaired > self._last_strategic_bridges:
            self.profile.strategic_bridges_repaired += self.strategic_war.bridges_repaired-self._last_strategic_bridges
            self._last_strategic_bridges=self.strategic_war.bridges_repaired
        self.profile.strategic_best_score=max(self.profile.strategic_best_score,self.strategic_war.strategic_score)
        if strategic_messages: self._set_message(strategic_messages[-1],5)

        # v2.3 national war economy: production/training/transport now feeds the strategic, naval, air and land layers.
        economy_messages = advance_war_economy(
            self.war_economy, dt, self.strategic_war, self.campaign, self.air_wing, self.land_warfare, self.task_force
        )
        if self.war_economy.orders_completed > self._last_economy_orders:
            delta=self.war_economy.orders_completed-self._last_economy_orders
            self.profile.economy_orders_completed += delta; self.profile.xp += 40*delta
            self.profile.add_log(f"National industry completed {delta} production order(s).")
            self._last_economy_orders=self.war_economy.orders_completed
        if self.war_economy.allocations > self._last_economy_allocations:
            self.profile.economy_allocations += self.war_economy.allocations-self._last_economy_allocations
            self._last_economy_allocations=self.war_economy.allocations
        if self.war_economy.facilities_repaired > self._last_economy_repairs:
            self.profile.economy_facilities_repaired += self.war_economy.facilities_repaired-self._last_economy_repairs
            self._last_economy_repairs=self.war_economy.facilities_repaired
        if self.war_economy.research_completed > self._last_economy_research:
            delta=self.war_economy.research_completed-self._last_economy_research
            self.profile.economy_research_completed += delta; self.profile.xp += 60*delta
            self._last_economy_research=self.war_economy.research_completed
        if self.war_economy.personnel_graduated > self._last_economy_graduates:
            self.profile.economy_personnel_graduated += self.war_economy.personnel_graduated-self._last_economy_graduates
            self._last_economy_graduates=self.war_economy.personnel_graduated
        if self.war_economy.infrastructure_repairs > self._last_economy_infra:
            self.profile.economy_infrastructure_repairs += self.war_economy.infrastructure_repairs-self._last_economy_infra
            self._last_economy_infra=self.war_economy.infrastructure_repairs
        self.profile.economy_best_score=max(self.profile.economy_best_score,self.war_economy.industrial_score)
        if economy_messages: self._set_message(economy_messages[-1],5)

        # v2.4 strategic mobility: production is only useful after cargo physically traverses the logistics network.
        logistics_messages = advance_logistics_network(
            self.logistics_network, dt, self.war_economy, self.strategic_war, self.campaign, self.air_wing,
            self.ground_ops, self.land_warfare, self.task_force
        )
        if self.logistics_network.delivered_shipments > self._last_logistics_delivered:
            delta=self.logistics_network.delivered_shipments-self._last_logistics_delivered
            self.profile.logistics_shipments_delivered += delta; self.profile.xp += 35*delta
            self.profile.add_log(f"Strategic logistics staged {delta} shipment arrival(s) at destination hubs.")
            self._last_logistics_delivered=self.logistics_network.delivered_shipments
        if self.logistics_network.lost_shipments > self._last_logistics_lost:
            self.profile.logistics_shipments_lost += self.logistics_network.lost_shipments-self._last_logistics_lost
            self._last_logistics_lost=self.logistics_network.lost_shipments
        if self.logistics_network.delayed_shipments > self._last_logistics_delayed:
            self.profile.logistics_shipments_delayed += self.logistics_network.delayed_shipments-self._last_logistics_delayed
            self._last_logistics_delayed=self.logistics_network.delayed_shipments
        if self.logistics_network.escorted_shipments > self._last_logistics_escorted:
            self.profile.logistics_escorted_shipments += self.logistics_network.escorted_shipments-self._last_logistics_escorted
            self._last_logistics_escorted=self.logistics_network.escorted_shipments
        if self.logistics_network.route_repairs > self._last_logistics_route_repairs:
            self.profile.logistics_route_repairs += self.logistics_network.route_repairs-self._last_logistics_route_repairs
            self._last_logistics_route_repairs=self.logistics_network.route_repairs
        if self.logistics_network.hub_repairs > self._last_logistics_hub_repairs:
            self.profile.logistics_hub_repairs += self.logistics_network.hub_repairs-self._last_logistics_hub_repairs
            self._last_logistics_hub_repairs=self.logistics_network.hub_repairs
        if self.logistics_network.hub_issues > self._last_logistics_hub_issues:
            delta=self.logistics_network.hub_issues-self._last_logistics_hub_issues
            self.profile.logistics_hub_issues += delta; self.profile.xp += 45*delta
            self.profile.add_log(f"Strategic logistics issued staged cargo from {delta} operational hub(s).")
            self._last_logistics_hub_issues=self.logistics_network.hub_issues
        self.profile.logistics_cargo_delivered=max(self.profile.logistics_cargo_delivered,self.logistics_network.cargo_delivered)
        self.profile.logistics_best_score=max(self.profile.logistics_best_score,self.logistics_network.logistics_score)
        if logistics_messages: self._set_message(logistics_messages[-1],5)

        # v2.0 first-person infantry/combat exercise shares this exact shore world and campaign support pool.
        ground_combat_messages = advance_ground_combat(
            self.ground_combat, dt, self.x, self.y, math.degrees(self.yaw)%360.0
        )
        if self.ground_combat.engagements_completed > self._last_ground_combat_runs:
            delta=self.ground_combat.engagements_completed-self._last_ground_combat_runs
            self.profile.ground_combat_runs += delta
            self.profile.ground_enemies_neutralized += self.ground_combat.enemies_neutralized
            self.profile.ground_support_calls += self.ground_combat.supports_called
            self.profile.ground_casualties_treated += self.ground_combat.casualties_treated
            self.profile.ground_combat_best_score=max(self.profile.ground_combat_best_score,self.ground_combat.score)
            self.profile.xp += int(45*delta + max(0,self.ground_combat.score-60)*.5)
            if self.ground_combat.score>=75:
                self.profile.qualifications["Combined-Arms Fireteam Practical"] = True
            self.profile.add_log(f"Completed combined-arms field exercise: {self.ground_combat.score:.1f}%.")
            self._last_ground_combat_runs=self.ground_combat.engagements_completed
            self.overlay="ground_combat_debrief"
            self._sync_physics_profile(); save_profile(self.profile)
        if self.ground_combat.training_losses > self._last_ground_combat_losses:
            self.profile.ground_training_losses += self.ground_combat.training_losses-self._last_ground_combat_losses
            self.profile.ground_enemies_neutralized += self.ground_combat.enemies_neutralized
            self.profile.ground_support_calls += self.ground_combat.supports_called
            self.profile.ground_casualties_treated += self.ground_combat.casualties_treated
            self._last_ground_combat_losses=self.ground_combat.training_losses
            self.x,self.y,self.z=50.0,78.0,LAYERS["BASE"].floor_z+CAMERA_HEIGHT
            self.ground_combat.player.health=max(35.0,self.ground_combat.player.health)
            self.ground_combat.player.wounded=True
            self.overlay="ground_combat_debrief"
            self.profile.add_log("Combined-arms exercise terminated after simulated incapacitation; medically evacuated to field aid.")
            self._sync_physics_profile(); save_profile(self.profile)
        elif ground_combat_messages:
            self._set_message(ground_combat_messages[-1],5)

        combat_was_active = self.combat.raid_active
        combat_messages = advance_naval_combat(self.combat, self.physics, self.shipboard, dt, self.survivability)
        if self.combat.enemy_destroyed > self._last_combat_kills:
            self.profile.combat_enemy_destroyed += self.combat.enemy_destroyed - self._last_combat_kills
            self._last_combat_kills = self.combat.enemy_destroyed
        if self.combat.hits_taken > self._last_combat_hits:
            self.profile.combat_hits_taken += self.combat.hits_taken - self._last_combat_hits
            self._last_combat_hits = self.combat.hits_taken
        if self.combat.air.sorties_launched > self._last_combat_sorties:
            self.profile.carrier_sorties += self.combat.air.sorties_launched - self._last_combat_sorties
            self._last_combat_sorties = self.combat.air.sorties_launched
        if combat_was_active and not self.combat.raid_active:
            score = combat_score(self.combat)
            self.profile.combat_training_runs += 1
            self.profile.combat_training_best = max(self.profile.combat_training_best, score)
            self.profile.add_log(f"Completed simulated carrier combat-defense problem: {score:.1f}%.")
            if score >= 75.0:
                self.profile.qualifications["Carrier Air Defense Watch"] = True
            self._sync_physics_profile()
            save_profile(self.profile)
            self._set_message(f"SIMULATED RAID COMPLETE — combat evaluation {score:.1f}%.", 6)
        elif combat_messages:
            self._set_message(combat_messages[-1], 5)
        combat_alert = "URGENT" if self.combat.raid_active else "ACTION" if self.combat.general_quarters else "NORMAL"
        for station_key in ("CIC","FIRE_CONTROL","DAMAGE_CONTROL","ENGINEERING","AIR_OPS","BRIDGE","RADIO"):
            if station_key in self.shipboard.enterprise.stations:
                self.shipboard.enterprise.stations[station_key].alert = combat_alert

        # v1.1 structural casualties remain active after impact and feed back into ship handling.
        survival_messages = survivability_tick(self.survivability, dt)
        factors = operational_factors(self.survivability)
        self.physics.propulsion_integrity = min(self.physics.propulsion_integrity, factors["propulsion"])
        self.physics.steering_integrity = min(self.physics.steering_integrity, factors["steering"])
        self.physics.hull_integrity = min(self.physics.hull_integrity, self.survivability.structural_strength_pct)
        if self.survivability.sunk and not self._last_sunk_state:
            self._last_sunk_state = True
            self.profile.add_log("Simulated ship-loss event completed in structural survivability training.")
            self._set_message("SIMULATED LOSS OF SHIP — abandon-ship/evacuation state remains active.", 8)
        elif survival_messages:
            self._set_message(survival_messages[-1], 5)

        # The bridge/damage/full-systems trainers are physically present on the base and keep running.
        from .systems import update_bridge, damage_tick
        from .ship import ship_tick
        update_bridge(self.bridge, dt)
        self.damage_accum += dt
        while self.damage_accum >= 1.0 and not (self.damage.resolved or self.damage.failed):
            damage_tick(self.damage); self.damage_accum -= 1.0
        self.systems_accum += dt
        while self.systems_accum >= .25 and not (self.ship_systems.resolved or self.ship_systems.failed):
            ship_tick(self.ship_systems, .25); self.systems_accum -= .25

        if self.running_time:
            self._life_accum += dt
            while self._life_accum >= 1.0:
                # one real second = one simulation minute, matching earlier builds
                from .walkship import advance_shipboard
                advance_shipboard(self.shipboard, 1)
                advance_life(self.life, 1)
                command_messages = advance_command(self.command, 1, self.combat, self.survivability, self.physics, self.life)
                route_living_crew(self.command, self.life)
                if self.command.orders_completed > self._last_command_complete:
                    delta = self.command.orders_completed - self._last_command_complete
                    self.profile.command_orders_completed += delta
                    self._last_command_complete = self.command.orders_completed
                if self.command.orders_failed > self._last_command_failed:
                    delta = self.command.orders_failed - self._last_command_failed
                    self.profile.command_orders_failed += delta
                    self._last_command_failed = self.command.orders_failed
                if command_messages:
                    self._set_message(command_messages[-1], 5)
                self.open_world_minutes += 1
                if self.open_world_minutes % 30 == 0 and self.open_world_minutes != self._last_autosave_minute:
                    self._last_autosave_minute = self.open_world_minutes
                    self._sync_physics_profile()
                    save_profile(self.profile)
                    self._set_message("AUTOSAVE — career, open-world duty and ship navigation checkpoint saved.", 2)
                self._life_accum -= 1.0

        layer = current_layer(self.x,self.y,self.z)
        if layer and layer.key != self._last_layer:
            self._last_layer = layer.key
            self._set_message(f"Entered {layer.name} — seamless world, no loading transition.", 3)

    def _hatch_blocked(self, x: float, y: float) -> bool:
        feet = self.z - CAMERA_HEIGHT
        for key,(layer_key,lx,ly) in SHIP_HATCH_WORLD.items():
            layer=LAYERS[layer_key]
            if abs(feet-layer.floor_z) > .7:
                continue
            gx,gy=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly
            if not self.shipboard.hatches.get(key, True) and math.hypot(x-gx,y-gy) < .65:
                return True
        return False

    def _player_on_ship(self) -> bool:
        layer = current_layer(self.x, self.y, self.z)
        return bool(layer and layer.key != "BASE")

    def _gangway_transition_blocked(self, x0: float, x1: float, y: float) -> bool:
        if self.physics.moored:
            return False
        if not (26.5 <= y <= 32.5):
            return False
        boundary = SHIP_ORIGIN_X
        return (x0 < boundary <= x1) or (x1 < boundary <= x0)

    def _move_open_world(self, forward: float, strafe: float, dt: float):
        on_ship = self._player_on_ship()
        motion_mul, ship_drift = player_motion_modifiers(self.physics) if on_ship else (1.0, 0.0)
        sprint=("shift_l" in self.keys or "shift_r" in self.keys)
        # Full-scale Enterprise uses human-scale movement; the old prototype used arcade-fast traversal.
        if on_ship:
            base_speed=4.2 if sprint else 1.75
        else:
            base_speed=7.0 if sprint else 4.4
        if getattr(self.ground_combat.player,"active",False):
            p=self.ground_combat.player
            stance_mul={"STANDING":1.0,"CROUCHED":.66,"PRONE":.34}.get(p.stance,1.0)
            if sprint and p.stance=="STANDING" and p.stamina>4:
                p.stamina=max(0.0,p.stamina-dt*12.0)
            else:
                sprint=False; base_speed=4.4; p.stamina=min(100.0,p.stamina+dt*5.0)
            base_speed*=stance_mul*max(.48,1.0-p.suppression/170.0)
        speed = base_speed * dt * motion_mul
        dx = math.cos(self.yaw)*forward + math.cos(self.yaw+math.pi/2)*strafe
        dy = math.sin(self.yaw)*forward + math.sin(self.yaw+math.pi/2)*strafe
        mag=max(1.0,math.hypot(dx,dy)); dx/=mag; dy/=mag
        radius=.22
        nx=self.x+dx*speed; ny=self.y+dy*speed + (ship_drift * dt if on_ship else 0.0)
        testx=nx + math.copysign(radius,dx or 1)
        if (not self._gangway_transition_blocked(self.x,nx,self.y)) and world_walkable(testx,self.y,self.z) and not self._hatch_blocked(testx,self.y): self.x=nx
        testy=ny + math.copysign(radius,(dy or ship_drift or 1))
        if world_walkable(self.x,testy,self.z) and not self._hatch_blocked(self.x,testy): self.y=ny

    def _aircraft_world_pose(self, aircraft):
        if getattr(aircraft,"deck","") not in ("HANGAR","FLIGHT"):
            return None
        deck=aircraft.deck
        pool=[a for a in self.air_wing.aircraft.values() if a.deck==deck and a.status not in ("LOST","AIRBORNE","RETURNING")]
        try: idx=pool.index(aircraft)
        except ValueError: return None
        row=idx//8; col=idx%8
        # Individual aircraft are now distributed over the real-scale hangar/flight-deck footprint.
        return SHIP_ORIGIN_X+45.0+col*21.5, SHIP_ORIGIN_Y+6.5+row*3.2, LAYERS[deck].floor_z

    def _nearest_enterable_aircraft(self, radius: float=2.35):
        feet=self.z-CAMERA_HEIGHT
        if abs(feet-LAYERS["FLIGHT"].floor_z)>.85:
            return None
        best=None; bestd=radius
        for ac in self.air_wing.aircraft.values():
            if ac.deck!="FLIGHT" or ac.status not in ("SPOTTED","GROUNDED"): continue
            pose=self._aircraft_world_pose(ac)
            if not pose: continue
            gx,gy,gz=pose; d=math.hypot(self.x-gx,self.y-gy)
            if d<bestd: best=(ac,gx,gy,gz); bestd=d
        return best

    def _deck_power_factor(self, layer_key: str) -> float:
        factor=1.0
        keys_by_layer={
            "ENGINEERING":("ENG_CONSOLE","LOAD_BOARD","DC_BOARD","BOUNDARY_BOARD"),
            "ISLAND":("RADAR_CONSOLE","RADIO_RACK","AA_DIRECTOR","TRACK_BOARD"),
            "BRIDGE":("HELM","ENGINE_TELEGRAPH","BRIDGE_LOG"),
            "HANGAR":("FUEL_STATION","ORDNANCE_STATION","TUG_CONTROL"),
            "FLIGHT":("FLIGHT_CONTROL","DECK_SAFETY"),
        }
        for key in keys_by_layer.get(layer_key,()):
            rt=self.shipboard.equipment_runtime.get(key)
            if rt and (rt.fault or not rt.powered): factor=min(factor,.62)
        load=self.shipboard.equipment_runtime.get("LOAD_BOARD")
        if load and (load.fault or not load.powered) and layer_key in ("ENGINEERING","ISLAND","BRIDGE"):
            factor=min(factor,.38)
        return factor

    def _render_power_failure_overlay(self,w:int,h:int,layer):
        if not layer or layer.outdoor: return
        factor=self._deck_power_factor(layer.key)
        if factor>=.95: return
        darkness=int((1-factor)*5)
        for i in range(max(1,darkness)):
            self.canvas.create_rectangle(0,0,w,h,fill="#020305",outline="",stipple="gray50")
        # Emergency battle lantern glow.
        pulse=.70+.30*math.sin(self.physical_world.elapsed*3.0)
        self.canvas.create_rectangle(0,0,w,9,fill=shade("#8a2525",pulse),outline="")
        self.canvas.create_text(w-22,112,text="EMERGENCY LIGHTING • ELECTRICAL CASUALTY",fill="#ff8f8f",font=("Segoe UI Semibold",9),anchor="ne")

    def _add_fault_effects(self,faces,w:int,h:int):
        feet=self.z-CAMERA_HEIGHT; phase=self.physical_world.elapsed
        for key,(layer_key,lx,ly) in SHIP_EQUIPMENT_WORLD.items():
            rt=self.shipboard.equipment_runtime.get(key)
            if not rt or not rt.fault: continue
            layer=LAYERS[layer_key]
            if abs(feet-layer.floor_z)>.9: continue
            gx,gy=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly
            if math.hypot(gx-self.x,gy-self.y)>15: continue
            # White steam plume for engineering-type casualties; blue-white arcs elsewhere.
            if key in ("ENG_CONSOLE","LOAD_BOARD","FUEL_STATION"):
                for i in range(5):
                    ox=math.sin(phase*2.0+i)*(.20+i*.06); oy=math.cos(phase*1.7+i)*(.16+i*.05)
                    self._add_box(faces,gx+ox-.10,gy+oy-.10,layer.floor_z+.75+i*.24,.20,.20,.18,shade("#cbd4d8",.78+i*.04),w,h)
            else:
                for i in range(3):
                    zz=layer.floor_z+.7+i*.17; flick=.75+.25*math.sin(phase*18+i*2)
                    self._add_box(faces,gx-.12+i*.10,gy-.34,zz,.05,.08,.05,shade("#8ed8ff",flick),w,h)

    # -------------------- interactions --------------------
    def _world_ship_equipment(self, radius: float=1.6):
        feet=self.z-CAMERA_HEIGHT
        best=None; bestd=radius
        for key,(layer_key,lx,ly) in SHIP_EQUIPMENT_WORLD.items():
            if key not in EQUIPMENT: continue
            layer=LAYERS[layer_key]
            if abs(feet-layer.floor_z)>.85: continue
            gx,gy=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly
            d=math.hypot(self.x-gx,self.y-gy)
            if d<bestd: best=(key,gx,gy,layer_key); bestd=d
        return best

    def _world_hatch(self, radius: float=1.3):
        feet=self.z-CAMERA_HEIGHT
        best=None; bestd=radius
        for key,(layer_key,lx,ly) in SHIP_HATCH_WORLD.items():
            layer=LAYERS[layer_key]
            if abs(feet-layer.floor_z)>.85: continue
            gx,gy=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly
            d=math.hypot(self.x-gx,self.y-gy)
            if d<bestd: best=(key,gx,gy); bestd=d
        return best

    def _start_vertical_travel(self, connector, target_floor: float):
        delta=abs((target_floor+CAMERA_HEIGHT)-self.z)
        self.vertical_travel={
            "start":time.monotonic(),"duration":max(1.25,delta/1.9),"from_camera":self.z,
            "to_camera":target_floor+CAMERA_HEIGHT,"name":connector.name,
            "from_x":self.x,"from_y":self.y,"yaw":self.yaw,
        }
        self._set_message(f"Using {connector.name} — remaining in the same continuous world.", 2)

    def _interact(self):
        aircraft=self._nearest_enterable_aircraft()
        if aircraft:
            ac,_,_,_=aircraft
            ok,msg=enter_cockpit(self.flight,ac,self.physics.east_nm,self.physics.north_nm,self.physics.heading_deg)
            if ok:
                self._set_message(msg+" • I start engine • W/S throttle • B brakes • arrows/A/D fly • L recover.",7)
            else: self._set_message(msg,4)
            return
        conn=nearby_connector(self.x,self.y,self.z)
        if conn:
            c,target=conn
            self._start_vertical_travel(c,target)
            return
        hatch=self._world_hatch()
        if hatch:
            key,_,_=hatch
            self.shipboard.hatches[key]=not self.shipboard.hatches.get(key,True)
            status="OPEN" if self.shipboard.hatches[key] else "SHUT"
            self._set_message(f"{HATCHES[key].name}: {status}. Physical passage {'clear' if status=='OPEN' else 'blocked'}.",4)
            return
        eq=self._world_ship_equipment()
        if eq:
            key,_,_,layer_key=eq
            node=EQUIPMENT[key]
            if key == "COMMAND_DESK":
                self.overlay = "command_console"
                self._set_message("Command desk opened — authority is limited by your earned rank.", 4)
                return
            # Preserve the mature qualification/task logic, then expose real v0.9 vessel controls.
            self.shipboard.deck=node.deck; self.shipboard.x=node.x; self.shipboard.y=node.y; self.shipboard.angle=self.yaw
            ok,msg=ship_interact(self.shipboard)
            if key == "HELM":
                self.overlay = "helm_physics"
                self._set_message(msg + "  Helm control opened.", 4)
            elif key == "ENGINE_TELEGRAPH":
                self.overlay = "engine_physics"
                self._set_message(msg + "  Engine telegraph opened.", 4)
            elif key in ("CIC_PLOT", "RADAR_CONSOLE"):
                self.overlay = "combat_plot"
                self._set_message(msg + "  Tactical combat plot opened.", 4)
            elif key in ("AA_DIRECTOR", "TRACK_BOARD"):
                self.overlay = "weapons_control"
                self._set_message(msg + "  Weapons/fire-control panel opened.", 4)
            elif key == "FLIGHT_CONTROL":
                self.overlay = "air_combat"
                self._set_message(msg + "  Carrier air-operations combat panel opened.", 4)
            elif key == "ORDNANCE_STATION":
                self.overlay = "magazine_combat"
                self._set_message(msg + "  Magazine/ordnance panel opened.", 4)
            elif key == "DC_BOARD":
                self.overlay = "survivability_dc"
                self._set_message(msg + "  Structural damage-control board opened.", 4)
            elif key == "BOUNDARY_BOARD":
                self.overlay = "survivability_boundaries"
                self._set_message(msg + "  Watertight boundary control opened.", 4)
            elif key == "MEDICAL_STAGING":
                self.overlay = "survivability_medical"
                self._set_message(msg + "  Casualty receiving station opened.", 4)
            else:
                self._set_message(msg,6)
            return
        point=nearest_static_interaction(self.x,self.y,self.z)
        if not point:
            self._set_message("Nothing usable within reach. Walk closer to a console, hatch, ladder, work station, bunk or mess area.",2)
            return
        a=point.action
        if a in ("career","academy","timeline","crew","promotion"):
            if a=="academy": self.exam_index=0; self.exam_correct=0; self.exam_topic_hits={}
            self.overlay=a
        elif a in ("helm_port","helm_stbd","throttle_up","throttle_down","bridge_order"):
            self._bridge_action(a)
        elif a in ("fire_team","pumps","isolate","ventilate","medical","repair_power","damage_eval"):
            self._damage_action(a)
        elif a.startswith("systems_"):
            self._systems_action(a)
        elif a=="workboard": self.overlay="workboard"
        elif a=="eat": self._set_message(eat_meal(self.life),5)
        elif a=="sleep": self._set_message(sleep_period(self.life),5)
        elif a=="medical_life": self._set_message(medical_check(self.life),5)
        elif a=="supply": self._set_message("Supply issue logged: replacement consumables, PPE and routine stores checked out.",5)
        elif a=="navigation": self.overlay="navigation"
        elif a in ("fleet_console","fleet_signal","fleet_logistics"):
            self.overlay=a
            self._set_message("Task-force operations board opened. Fleet-changing orders require SHIP COMMAND WATCH authority.",4)
        elif a in ("campaign_console","campaign_logistics"):
            self.overlay=a
            self._set_message("Persistent campaign operations board opened. Mission/port/repair orders require SHIP COMMAND WATCH authority.",4)
        elif a == "air_wing_console":
            self.overlay="air_wing_console"
            self._set_message("Air Group operations room opened — plan, spot, launch, recover and service individual aircraft.",4)
        elif a in ("ground_console","ground_airfield","ground_amphib","ground_supply"):
            self.overlay="ground_console"
            self._set_message("Expeditionary operations board opened — ground units, airfields, vehicles and amphibious forces share the persistent campaign world.",4)
        elif a=="ground_motor":
            ok,msg=enter_training_vehicle(self.ground_ops,self.x,self.y)
            if ok:
                self.ground_ops.drive.x,self.ground_ops.drive.y=self.x,self.y
            self._set_message(msg,6)
        elif a=="ground_flightline":
            self._set_message("Training flight line: expeditionary aircraft servicing and airfield operations are controlled from the nearby Airfield Operations building.",5)
        elif a=="infantry_armory":
            defaults={"RIFLE":100,"AUTO":120,"SIDEARM":32}
            for wk,w in self.ground_combat.weapons.items():
                w.magazine_rounds=w.magazine_capacity; w.reserve_rounds=defaults.get(wk,w.reserve_rounds)
            self.ground_combat.player.first_aid_kits=2
            self._set_message("Infantry issue complete — weapons, training ammunition, protective equipment and two first-aid kits checked out.",5)
        elif a=="infantry_command":
            self.overlay="ground_combat_console"
            self._set_message("Fireteam command board opened — live exercise orders, contacts, casualties and support requests are shown here.",4)
        elif a=="infantry_aid":
            ok,msg=ground_first_aid(self.ground_combat)
            if not ok:
                ok,msg=treat_ground_casualty(self.ground_combat)
            self._set_message(msg,5)
        elif a=="infantry_range":
            ok,msg=begin_ground_engagement(self.ground_combat)
            if ok:
                self._last_ground_combat_runs=self.ground_combat.engagements_completed
                self._last_ground_combat_losses=self.ground_combat.training_losses
            self._set_message(msg,6)
        elif a in ("land_command","land_artillery"):
            self.overlay="land_command"
            self._set_message("Battalion tactical command board opened — units, armor, artillery, sectors, CASEVAC and logistics share one live battlefield.",5)
        elif a=="land_armor":
            ok,msg=enter_land_vehicle(self.land_warfare,self.x,self.y)
            self._set_message(msg,6)
        elif a=="land_medevac":
            ok,msg=land_medevac(self.land_warfare); self._set_message(msg,6)
        elif a=="land_logistics":
            ok,msg=land_resupply(self.land_warfare); self._set_message(msg,5)
        elif a=="land_engineer":
            ok,msg=service_land_vehicle(self.land_warfare); self._set_message(msg,5)
        elif a=="land_battlefield":
            ok,msg=begin_land_operation(self.land_warfare)
            if ok:
                self._last_land_ops_complete=self.land_warfare.operations_completed; self._last_land_ops_failed=self.land_warfare.operations_failed
            self._set_message(msg,7)
        elif a in ("strategic_command","strategic_recon","strategic_logistics"):
            self.overlay="strategic_command"
            self._set_message("Theater strategic command opened — persistent front line, formations, routes, depots, recon and multiple operations are live above the tactical battle.",6)
        elif a=="strategic_front":
            ok,msg=begin_strategic_campaign(self.strategic_war); self._set_message(msg,7)
        elif a in ("economy_console","economy_production","economy_repair","economy_research","economy_logistics"):
            self.overlay="economy_console"
            self._set_message("National War Production Board opened — industry, raw reserves, transport, research, training and strategic allocations are live.",6)
        elif a in ("logistics_console","logistics_dispatch","logistics_convoy","logistics_route","logistics_receiving"):
            self.overlay="logistics_console"
            self._set_message("Strategic Mobility Command opened — cargo must be dispatched, transported, protected and physically delivered before operational recipients receive it.",6)
        elif a=="mooring":
            ok,msg = secure_to_berth(self.physics) if not self.physics.moored else cast_off(self.physics)
            self._set_message(msg,6)
        elif a=="anchor":
            ok,msg=toggle_anchor(self.physics); self._set_message(msg,6)
        elif a=="survival_muster":
            ok,msg=muster_abandon_ship(self.survivability); self._set_message(msg,6)
        elif a.startswith("maintenance:"):
            _,key=a.split(":",1); ok,msg=complete_maintenance(self.life,key)
            if ok and "already complete" not in msg:
                self.profile.xp += 10
                self.profile.add_log(f"Completed shipboard maintenance: {msg.replace('Maintenance complete: ','')}")
                if all(w.completed for w in self.life.work_orders.values()):
                    self.profile.qualifications["Shipboard Routine & Maintenance"] = True
                    self.profile.xp += 25
                    self.profile.add_log("Completed the full daily shipboard maintenance work package.")
                save_profile(self.profile)
            self._set_message(msg,6)
        else:
            self._set_message(f"{point.name}: no active action.",3)

    # -------------------- objective --------------------
    def _objective_world_pose(self):
        if getattr(self.ground_combat,"engagement_active",False):
            obj=self.ground_combat.active_objective
            if obj:
                return obj.x,obj.y,LAYERS["BASE"].floor_z,obj.title
        if getattr(self.land_warfare,"active",False) and self.land_warfare.selected_sector:
            sec=self.land_warfare.selected_sector
            return sec.x,sec.y,LAYERS["BASE"].floor_z,f"Battalion objective: {sec.name}"
        # Critical personal needs take precedence only when severe.
        n=self.life.needs
        if n.wellness<45:
            for p in all_static_interactions():
                if p.action=="medical_life": return p.x,p.y,p.floor_z,"Report to Sickbay"
        if n.fatigue>88:
            p=next(p for p in all_static_interactions() if p.key=="SHIP_BERTH_FWD"); return p.x,p.y,p.floor_z,"Take required off-watch rest"
        if n.hunger>88 or n.hydration>90:
            p=next(p for p in all_static_interactions() if p.key=="SHIP_GALLEY"); return p.x,p.y,p.floor_z,"Report to crew mess"
        emergency_orders=[o for o in self.command.orders.values() if not o.completed and not o.failed and o.priority in ("EMERGENCY","URGENT")]
        if emergency_orders:
            order=min(emergency_orders,key=lambda o:o.deadline_minute)
            station_to_eq={"BRIDGE":"COMMAND_DESK","CIC":"CIC_PLOT","RADIO":"RADIO_RACK","ENGINEERING":"ENG_CONSOLE","DAMAGE_CONTROL":"DC_BOARD","FIRE_CONTROL":"AA_DIRECTOR","AIR_OPS":"FLIGHT_CONTROL","MEDICAL":"MEDICAL_STAGING","SUPPLY":"COMMAND_DESK"}
            key=station_to_eq.get(order.department,"COMMAND_DESK")
            if key in SHIP_EQUIPMENT_WORLD:
                layer,lx,ly=SHIP_EQUIPMENT_WORLD[key]
                return SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly,LAYERS[layer].floor_z,f"{order.priority}: {order.title}"
        obj=active_objective(self.shipboard)
        if obj and obj.get("station"):
            station=obj["station"]
            candidates=[k for k,n in EQUIPMENT.items() if n.station==station and k in SHIP_EQUIPMENT_WORLD]
            if candidates:
                key=candidates[0]
                layer,lx,ly=SHIP_EQUIPMENT_WORLD[key]
                return SHIP_ORIGIN_X+lx, SHIP_ORIGIN_Y+ly, LAYERS[layer].floor_z, obj["title"]
        opens=[w for w in self.life.work_orders.values() if not w.completed]
        if opens:
            w=min(opens,key=lambda x:x.due_minute)
            keymap={"MAGAZINE":"SHIP_MAGAZINE","ELECTRICAL":"SHIP_ELECTRICAL","AVIATION":"SHIP_AIRSHOP","MACHINE_SHOP":"SHIP_MACHINE","ORDNANCE":"SHIP_ORDSHOP"}
            target=keymap.get(w.key)
            if target:
                p=next(p for p in all_static_interactions() if p.key==target)
                return p.x,p.y,p.floor_z,w.title
        return None

    def _objective_text(self) -> str:
        obj=self._objective_world_pose()
        if not obj:
            m=self.campaign.active_mission
            if m:
                if m.mission_type=="ESCORT" and "CONVOY_A" in self.campaign.convoys:
                    target=self.campaign.convoys["CONVOY_A"]; te,tn=target.east_nm,target.north_nm
                else:
                    te,tn=m.target_east_nm,m.target_north_nm
                de,dn=te-self.physics.east_nm,tn-self.physics.north_nm
                rng=math.hypot(de,dn); brg=math.degrees(math.atan2(de,dn))%360.0
                return f"OPERATIONAL OBJECTIVE: {m.title} • BRG {brg:03.0f}° • {rng:.1f} nm • progress {m.progress_minutes:.1f}/{m.required_minutes:.0f} min"
            return "No urgent assignment. Continue qualifications, maintenance, ship routine, campaign operations or historical duties."
        x,y,z,title=obj
        dz=z-(self.z-CAMERA_HEIGHT); d=math.hypot(x-self.x,y-self.y)
        bearing=math.degrees(math.atan2(y-self.y,x-self.x))%360
        vertical="same deck" if abs(dz)<.7 else (f"{abs(dz):.1f}m above" if dz>0 else f"{abs(dz):.1f}m below")
        return f"OBJECTIVE: {title} • {d:.1f}m • bearing {bearing:03.0f}° • {vertical}"

    # -------------------- rendering --------------------
    def _render(self):
        c=self.canvas; w,h=max(2,c.winfo_width()),max(2,c.winfo_height()); c.delete("all")
        if self.flight.active:
            self._render_flight_cockpit(w,h)
            if self.overlay: self._render_overlay(w,h)
            return
        layer=current_layer(self.x,self.y,self.z)
        outdoors=bool(layer and layer.outdoor)
        on_ship=bool(layer and layer.key != "BASE")
        vessel_roll = (self.physics.roll_deg + self.survivability.list_deg) if (on_ship and outdoors) else 0.0
        vessel_pitch = (self.physics.pitch_deg + self.survivability.trim_deg) if (on_ship and outdoors) else 0.0
        horizon_mid=h*.5+self.pitch*h*.42 + vessel_pitch*h/75.0
        slope=math.tan(math.radians(vessel_roll))*w*.48
        left_y=int(horizon_mid-slope); right_y=int(horizon_mid+slope)
        sky_top,sky_horizon,sea_color=sky_colors(self.physical_world)
        sky=sky_top if outdoors else ("#070b10" if self.physical_world.daylight<.18 else "#091321")
        ground=sea_color if (outdoors and on_ship and not self.physics.moored) else ("#132737" if outdoors else "#151a20")
        c.create_polygon(0,0,w,0,w,right_y,0,left_y,fill=sky,outline="")
        c.create_polygon(0,left_y,w,right_y,w,h,0,h,fill=ground,outline="")
        if outdoors:
            # Day/night atmosphere, cloud cover and moving sea bands.
            bands=(sky_top, shade(sky_top,.92), sky_horizon, shade(sky_horizon,.88))
            for i,col in enumerate(bands):
                y0=int(i*h*.085); y1=int((i+1)*h*.085)
                c.create_rectangle(0,y0,w,y1,fill=col,outline="")
            sea_y=max(0,min(h,int((left_y+right_y)/2)))
            wave_phase=(time.monotonic()*26.0 + self.physics.distance_nm*90.0) % 48
            wave_gap=max(18,30-int(self.physics.sea_state*1.6))
            for yy in range(sea_y+16,h,wave_gap):
                offset=((yy+wave_phase)%48)-24
                c.create_line(0+offset,yy,w,yy+int(slope*.18),fill=shade(sea_color,1.35),width=1)
                c.create_line(70+offset,yy+5,w,yy+5+int(slope*.18),fill=shade(sea_color,.78),width=1)
            c.create_text(w-22,22,text=f"OPEN WORLD • {self.physical_world.weather_mode} • SEA STATE {self.physics.sea_state}",fill="#d3e9ff",font=("Segoe UI Semibold",9),anchor="ne")
        faces=[]; self._collect_open_geometry(faces,w,h); self._collect_detail_geometry(faces,w,h); faces.sort(key=lambda x:x[0],reverse=True)
        for depth,pts,fill,outline in faces:
            if len(pts)>=6: c.create_polygon(*pts,fill=fill,outline=outline,width=1)
        self._render_open_entities(w,h)
        self._render_weather_overlay(w,h,outdoors)
        self._render_power_failure_overlay(w,h,layer)
        self._render_open_hud(w,h)
        if self.overlay: self._render_overlay(w,h)

    def _collect_open_geometry(self, faces, w:int, h:int):
        """Collect nearby static world surfaces using merged floor/ceiling spans.

        v2.4 emitted one polygon for every walkable floor tile and another for every
        ceiling tile.  Large ship compartments therefore generated hundreds of tiny
        Canvas objects every frame.  v2.5 merges contiguous visible cells into long
        quads while preserving wall collision/layout geometry.
        """
        radius = 8 if getattr(self, "visual_quality", "BALANCED") == "PERFORMANCE" else (14 if getattr(self, "visual_quality", "BALANCED") == "HIGH" else 9)
        feet=self.z-CAMERA_HEIGHT
        for layer in LAYERS.values():
            if not self.physics.moored and self._player_on_ship() and layer.key == "BASE":
                continue
            if abs(layer.floor_z-feet)>3.35:
                continue
            lx0=int(self.x-layer.origin_x); ly0=int(self.y-layer.origin_y)
            minx,maxx=max(0,lx0-radius),min(layer.width-1,lx0+radius)
            miny,maxy=max(0,ly0-radius),min(layer.height-1,ly0+radius)
            ceil=layer.floor_z+2.75

            # Floor and ceiling surfaces: one quad per contiguous row span instead of
            # one quad per cell.  This is the main rendering-performance fix.
            for gy in range(miny,maxy+1):
                row_y=layer.origin_y+gy+.5
                dy=row_y-self.y
                if abs(dy)>radius:
                    continue
                reach=math.sqrt(max(0.0,radius*radius-dy*dy))
                rs=max(minx,int(self.x-layer.origin_x-reach)-1)
                re=min(maxx,int(self.x-layer.origin_x+reach)+1)
                gx=rs
                while gx<=re:
                    if layer.grid[gy][gx] != ".":
                        gx+=1; continue
                    a=gx
                    while gx+1<=re and layer.grid[gy][gx+1]==".":
                        gx+=1
                    b=gx
                    wx0=layer.origin_x+a; wx1=layer.origin_x+b+1
                    wy0=layer.origin_y+gy; wy1=wy0+1
                    base=layer.floor_color if gy%2==0 else shade(layer.floor_color,.965)
                    self._add_face(faces,[(wx0,wy0,layer.floor_z),(wx1,wy0,layer.floor_z),(wx1,wy1,layer.floor_z),(wx0,wy1,layer.floor_z)],base,"",w,h)
                    base_indoor = layer.key == "BASE" and (
                        (3 <= a <= 20 and 3 <= gy <= 16) or
                        (23 <= a <= 45 and 3 <= gy <= 16) or
                        (3 <= a <= 27 and 20 <= gy <= 39) or
                        (31 <= a <= 55 and 20 <= gy <= 39)
                    )
                    if (layer.ceiling or base_indoor) and abs(ceil-self.z)>.25:
                        self._add_face(faces,[(wx0,wy0,ceil),(wx0,wy1,ceil),(wx1,wy1,ceil),(wx1,wy0,ceil)],"#171c24","",w,h)
                    gx+=1

            # Exposed bulkheads are merged into continuous runs.  The old renderer
            # emitted one face per one-meter wall cell; long carrier corridors therefore
            # became a picket fence of Canvas polygons and visible seams.
            def cell(ix,iy):
                if iy<0 or iy>=layer.height or ix<0 or ix>=layer.width: return " "
                return layer.grid[iy][ix]

            # North/south-facing walls: merge along X.
            for gy in range(miny,maxy+1):
                for dy,sf,yoff,reverse in ((-1,.78,0.0,False),(1,.62,1.0,True)):
                    gx=minx
                    while gx<=maxx:
                        exposed=(cell(gx,gy)=="#" and cell(gx,gy+dy)==".")
                        if not exposed:
                            gx+=1; continue
                        a=gx
                        while gx+1<=maxx and cell(gx+1,gy)=="#" and cell(gx+1,gy+dy)==".": gx+=1
                        b=gx
                        wx0,wx1=layer.origin_x+a,layer.origin_x+b+1
                        wy=layer.origin_y+gy+yoff
                        if math.hypot((wx0+wx1)*.5-self.x,wy-self.y)<=radius+3:
                            if not reverse:
                                q=[(wx1,wy,layer.floor_z),(wx0,wy,layer.floor_z),(wx0,wy,ceil),(wx1,wy,ceil)]
                            else:
                                q=[(wx0,wy,layer.floor_z),(wx1,wy,layer.floor_z),(wx1,wy,ceil),(wx0,wy,ceil)]
                            self._add_face(faces,q,shade(layer.wall_color,sf),"#202832",w,h)
                        gx+=1

            # West/east-facing walls: merge along Y.
            for gx in range(minx,maxx+1):
                for dx,sf,xoff,reverse in ((-1,.86,0.0,True),(1,.68,1.0,False)):
                    gy=miny
                    while gy<=maxy:
                        exposed=(cell(gx,gy)=="#" and cell(gx+dx,gy)==".")
                        if not exposed:
                            gy+=1; continue
                        a=gy
                        while gy+1<=maxy and cell(gx,gy+1)=="#" and cell(gx+dx,gy+1)==".": gy+=1
                        b=gy
                        wy0,wy1=layer.origin_y+a,layer.origin_y+b+1
                        wx=layer.origin_x+gx+xoff
                        if math.hypot(wx-self.x,(wy0+wy1)*.5-self.y)<=radius+3:
                            if reverse:
                                q=[(wx,wy0,layer.floor_z),(wx,wy1,layer.floor_z),(wx,wy1,ceil),(wx,wy0,ceil)]
                            else:
                                q=[(wx,wy1,layer.floor_z),(wx,wy0,layer.floor_z),(wx,wy0,ceil),(wx,wy1,ceil)]
                            self._add_face(faces,q,shade(layer.wall_color,sf),"#202832",w,h)
                        gy+=1

        # Dockside water around the carrier is rendered as a few large surfaces.
        water_z=2.35
        for x0,y0,x1,y1 in [(58,0,316,7),(58,38,316,52),(309,7,322,38)]:
            self._add_face(faces,[(x0,y0,water_z),(x1,y0,water_z),(x1,y1,water_z),(x0,y1,water_z)],"#12354c","",w,h)

    def _add_cylinder(self, faces, cx: float, cy: float, z: float, radius: float, height: float, color: str, w: int, h: int, sides: int = 8):
        """Small software-rendered vertical prism used for heads, masts, pipes and stanchions."""
        pts0=[]; pts1=[]
        count=max(6,sides)
        if getattr(self,"visual_quality","BALANCED")!="HIGH":
            count=min(count,6)
        for i in range(count):
            a=math.tau*i/count
            pts0.append((cx+math.cos(a)*radius,cy+math.sin(a)*radius,z))
            pts1.append((cx+math.cos(a)*radius,cy+math.sin(a)*radius,z+height))
        for i in range(len(pts0)):
            j=(i+1)%len(pts0)
            self._add_face(faces,[pts0[i],pts0[j],pts1[j],pts1[i]],shade(color,.76+.18*(i%3)),"#141820",w,h)
        self._add_face(faces,list(reversed(pts1)),shade(color,1.08),"#141820",w,h)

    def _add_oriented_box(self, faces, cx: float, cy: float, z: float, length: float, width: float, height: float, angle_deg: float, color: str, w: int, h: int):
        a=math.radians(angle_deg); ux,uy=math.cos(a),math.sin(a); vx,vy=-uy,ux
        hl,hw=length/2,width/2
        base=[(cx+ux*hl+vx*hw,cy+uy*hl+vy*hw,z),(cx-ux*hl+vx*hw,cy-uy*hl+vy*hw,z),(cx-ux*hl-vx*hw,cy-uy*hl-vy*hw,z),(cx+ux*hl-vx*hw,cy+uy*hl-vy*hw,z)]
        top=[(x,y,z+height) for x,y,_ in base]
        self._add_face(faces,base,color,"#141820",w,h); self._add_face(faces,list(reversed(top)),shade(color,1.08),"#141820",w,h)
        for i in range(4):
            j=(i+1)%4; self._add_face(faces,[base[i],base[j],top[j],top[i]],shade(color,.82+.08*(i%2)),"#141820",w,h)

    def _add_extruded_polygon(self, faces, points, z: float, height: float, color: str, w: int, h: int):
        """Extrude a 2D footprint with chamfered/angled sides; used for ship structure."""
        if len(points)<3: return
        bottom=[(x,y,z) for x,y in points]
        top=[(x,y,z+height) for x,y in points]
        self._add_face(faces,bottom,shade(color,.72),"#1b2227",w,h)
        self._add_face(faces,list(reversed(top)),shade(color,1.04),"#1b2227",w,h)
        for i in range(len(points)):
            j=(i+1)%len(points)
            self._add_face(faces,[bottom[i],bottom[j],top[j],top[i]],shade(color,.76+.05*(i%4)),"#202930",w,h)

    def _add_rotating_propeller(self, faces, x: float, y: float, z: float, phase_deg: float, w: int, h: int):
        # Stylized stern screw in the vertical Y/Z plane.
        a=math.radians(phase_deg)
        for k in range(4):
            q=a+k*math.pi/2
            dy,dz=math.cos(q)*.72,math.sin(q)*.72
            py,pz=math.cos(q+math.pi/2)*.11,math.sin(q+math.pi/2)*.11
            self._add_face(faces,[(x-.035,y-py,z-pz),(x-.035,y+py,z+pz),(x-.035,y+dy+py,z+dz+pz),(x-.035,y+dy-py,z+dz-pz)],"#81744f","#31343a",w,h)
        self._add_cylinder(faces,x,y,z-.10,.13,.20,"#585b5d",w,h,8)

    def _add_damage_effects(self, faces, w: int, h: int):
        feet=self.z-CAMERA_HEIGHT
        phase=self.physical_world.elapsed
        for comp in self.survivability.compartments.values():
            if max(comp.fire,comp.smoke,comp.flooding,comp.breach_area_m2*30)<1.0:
                continue
            gx,gy,gz=damage_world_pose(comp)
            if abs(gz-feet)>3.5 or math.hypot(gx-self.x,gy-self.y)>16:
                continue
            if comp.flooding>2:
                water_h=min(1.25,.04+comp.flooding/100*1.18)
                self._add_box(faces,gx-1.35,gy-1.05,gz+.02,2.7,2.1,water_h,shade("#236a85",.80),w,h)
                if comp.breach_area_m2>.02:
                    self._add_box(faces,gx-1.48,gy-.12,gz+.18,.22,.24,min(1.0,.22+comp.breach_area_m2*.4),"#4f9fba",w,h)
            if comp.fire>2:
                flames=max(1,min(7,int(comp.fire/14)+1))
                for i in range(flames):
                    ox=math.sin(phase*3.1+i*2.2)*.42; oy=math.cos(phase*2.7+i*1.7)*.38
                    fh=.22+.55*(comp.fire/100)*(1+.25*math.sin(phase*5+i))
                    col="#f0a33c" if i%2==0 else "#c94f2e"
                    self._add_box(faces,gx+ox-.07,gy+oy-.07,gz+.08,.14,.14,fh,col,w,h)
            if comp.smoke>3 or comp.fire>20:
                amount=max(comp.smoke,comp.fire*.55)
                puffs=max(1,min(6,int(amount/18)+1))
                for i in range(puffs):
                    ox=math.sin(phase*.8+i*2.0)*.55; oy=math.cos(phase*.65+i*1.5)*.48
                    zz=gz+.65+i*.31+(phase*.14)% .25
                    self._add_box(faces,gx+ox-.18,gy+oy-.18,zz,.36,.36,.28,shade("#41464a",.72+i*.03),w,h)

    def _add_5in38_mount(self, faces, x: float, y: float, z: float, outward: float, w: int, h: int):
        """Low-draw-call silhouette for the period single 5in/38 deck-edge mounts."""
        self._add_cylinder(faces,x,y,z,.42,.34,"#6d777d",w,h,8)
        self._add_cylinder(faces,x,y,z+.31,.30,.36,"#59656c",w,h,8)
        self._add_oriented_box(faces,x+outward*.70,y,z+.58,1.55,.07,.07,0,"#30383d",w,h)

    def _add_11quad_mount(self, faces, x: float, y: float, z: float, heading: float, w: int, h: int):
        self._add_cylinder(faces,x,y,z,.36,.22,"#68747a",w,h,8)
        self._add_oriented_box(faces,x,y,z+.26,.95,.66,.34,heading,"#556168",w,h)
        a=math.radians(heading); dx,dy=math.cos(a),math.sin(a)
        for off in (-.18,-.06,.06,.18):
            bx=x+dx*.65-dy*off; by=y+dy*.65+dx*off
            self._add_oriented_box(faces,bx,by,z+.52,1.15,.035,.035,heading,"#242b30",w,h)

    def _add_20mm_mount(self, faces, x: float, y: float, z: float, heading: float, w: int, h: int):
        self._add_cylinder(faces,x,y,z,.11,.24,"#69737a",w,h,7)
        a=math.radians(heading); dx,dy=math.cos(a),math.sin(a)
        self._add_oriented_box(faces,x+dx*.34,y+dy*.34,z+.38,.72,.025,.025,heading,"#22292d",w,h)

    def _add_faceted_hull(self, faces, w: int, h: int):
        """Real-scale Yorktown-class carrier silhouette with tapered multi-strake hull.

        This is still procedural geometry, but unlike the pre-v2.5 72 m box it uses the
        245 m flight-deck footprint, a fine bow, cruiser stern, sheer-like deck edge,
        hangar openings, gallery deck, elevator plates and a concentrated starboard island.
        """
        feet=self.z-CAMERA_HEIGHT
        layer=current_layer(self.x,self.y,self.z)
        if not layer:
            return
        # Render the actual carrier from the pier/shore as well as from aboard.
        if not self._player_on_ship():
            nearest_x=max(SHIP_ORIGIN_X,min(SHIP_ORIGIN_X+SHIP_LENGTH_M,self.x))
            nearest_y=max(SHIP_ORIGIN_Y,min(SHIP_ORIGIN_Y+SHIP_WIDTH_M,self.y))
            if math.hypot(nearest_x-self.x,nearest_y-self.y)>170.0:
                return
        # Enough stations to read as a ship without flooding Tk Canvas with polygons.
        stations=(0.0,5.0,13.0,28.0,52.0,82.0,118.0,154.0,190.0,218.0,236.0,245.0)
        def half(lx, scale=1.0):
            t=max(0.0,min(1.0,lx/SHIP_LENGTH_M))
            # very fine stem, full parallel mid-body, quicker stern taper
            bow=min(1.0,max(.05,t/.15))
            stern=min(1.0,max(.08,(1.0-t)/.12))
            fullness=min(bow,stern)
            return (2.0 + 10.7*(math.sin(fullness*math.pi/2)**.55))*scale
        z_keel=-5.2; z_lower=-2.7; z_hangar=3.05; z_gallery=5.15; z_flight=6.38
        cy=SHIP_CENTER_Y
        for a,b in zip(stations[:-1],stations[1:]):
            xa,xb=SHIP_ORIGIN_X+a,SHIP_ORIGIN_X+b
            ha,hb=half(a),half(b)
            # skip stations nowhere near the camera before constructing faces
            if min(abs(xa-self.x),abs(xb-self.x))>self.render_distance+16:
                continue
            for side in (-1.0,1.0):
                ya,yb=cy+side*ha,cy+side*hb
                # lower strake rolls inward toward the keel
                yka,ykb=cy+side*ha*.52,cy+side*hb*.52
                col1="#263039" if side<0 else "#222b33"
                col2="#35414a" if side<0 else "#303b43"
                self._add_face(faces,[(xa,yka,z_keel),(xb,ykb,z_keel),(xb,yb,z_lower),(xa,ya,z_lower)],col1,"#182027",w,h)
                self._add_face(faces,[(xa,ya,z_lower),(xb,yb,z_lower),(xb,yb,z_hangar),(xa,ya,z_hangar)],col2,"#1b242b",w,h)
                # upper hangar/gallery side is slightly tucked in, giving visible flare/overhang
                uga,ugb=cy+side*ha*.92,cy+side*hb*.92
                self._add_face(faces,[(xa,ya,z_hangar),(xb,yb,z_hangar),(xb,ugb,z_gallery),(xa,uga,z_gallery)],"#3e4a53","#232d34",w,h)
        # Flight deck: a single thin, broad slab with a believable rectangular carrier overhang.
        deck_x0=SHIP_ORIGIN_X+3.0; deck_x1=SHIP_ORIGIN_X+242.0
        deck_y0=SHIP_ORIGIN_Y+.35; deck_y1=SHIP_ORIGIN_Y+29.65
        if math.hypot(SHIP_CENTER_X-self.x,SHIP_CENTER_Y-self.y)<self.render_distance+135:
            # Large silhouette surfaces are deliberately allowed beyond the normal detail
            # distance; they cost only three polygons and prevent the carrier from ending
            # at the player's local render bubble.
            _rd=self.render_distance; self.render_distance=max(_rd,180.0)
            self._add_face(faces,[(deck_x0,deck_y0,z_flight),(deck_x1,deck_y0,z_flight),(deck_x1,deck_y1,z_flight),(deck_x0,deck_y1,z_flight)],"#3d423d","#252b29",w,h)
            self._add_face(faces,[(deck_x0,deck_y0,z_gallery),(deck_x1,deck_y0,z_gallery),(deck_x1,deck_y0,z_flight),(deck_x0,deck_y0,z_flight)],"#343f46","#1f282e",w,h)
            self._add_face(faces,[(deck_x0,deck_y1,z_gallery),(deck_x1,deck_y1,z_gallery),(deck_x1,deck_y1,z_flight),(deck_x0,deck_y1,z_flight)],"#303a41","#1d252b",w,h)
            self.render_distance=_rd
        # Hangar side openings/readable structural bays along port/starboard sides.
        if layer.key in ("HANGAR","FLIGHT","ISLAND","BRIDGE"):
            for lx in range(46,199,18):
                gx=SHIP_ORIGIN_X+lx
                if abs(gx-self.x)>self.detail_radius+10: continue
                for side in (-1,1):
                    gy=cy+side*11.85
                    self._add_oriented_box(faces,gx,gy,3.45,10.5,.12,1.35,0,"#11181d",w,h)
                    # vertical frame columns break up the black opening and read as real structure
                    for off in (-5.0,0,5.0):
                        self._add_box(faces,gx+off-.06,gy-.08,3.35,.12,.16,1.60,"#59636a",w,h)
        # Three elevator plates and deck markings at sourced Yorktown-class locations normalized for gameplay.
        if layer.key=="FLIGHT":
            for ex,ey in SHIP_ELEVATORS:
                gx,gy=SHIP_ORIGIN_X+ex,SHIP_ORIGIN_Y+ey
                if math.hypot(gx-self.x,gy-self.y)<self.detail_radius+14:
                    self._add_oriented_box(faces,gx,gy,z_flight+.015,11.0,8.8,.035,0,"#3b454a",w,h)
                    # thin perimeter bars instead of a filled cube lip
                    self._add_oriented_box(faces,gx,gy-4.35,z_flight+.04,11.0,.08,.035,0,"#a8a090",w,h)
                    self._add_oriented_box(faces,gx,gy+4.35,z_flight+.04,11.0,.08,.035,0,"#a8a090",w,h)
        # Starboard island: chamfered Yorktown-style superstructure rather than stacked cubes.
        ix=SHIP_ORIGIN_X+SHIP_ISLAND_CENTER[0]; iy=SHIP_ORIGIN_Y+SHIP_ISLAND_CENTER[1]
        if math.hypot(ix-self.x,iy-self.y)<150.0:
            _rd=self.render_distance; self.render_distance=max(_rd,160.0)
            base=[(ix-13,iy-3.4),(ix+8.5,iy-3.4),(ix+12,iy-1.6),(ix+12,iy+2.7),(ix+8,iy+3.5),(ix-10.5,iy+3.5),(ix-13,iy+1.4)]
            mid=[(ix-9.5,iy-3.0),(ix+7,iy-3.0),(ix+9.5,iy-1.2),(ix+9,iy+2.4),(ix+5.5,iy+3.0),(ix-8,iy+3.0)]
            bridge=[(ix-5.5,iy-3.25),(ix+7.2,iy-3.25),(ix+8.5,iy-1.7),(ix+7.3,iy+2.1),(ix-5.0,iy+2.35),(ix-7.2,iy+.7)]
            self._add_extruded_polygon(faces,base,6.46,2.85,"#48545b",w,h)
            self._add_extruded_polygon(faces,mid,9.25,2.55,"#526068",w,h)
            self._add_extruded_polygon(faces,bridge,11.75,2.15,"#5b686f",w,h)
            # Broad bridge glazing facing port/forward gives the island a recognizable command level.
            self._add_face(faces,[(ix-5.0,iy-3.29,12.45),(ix+6.7,iy-3.29,12.45),(ix+6.7,iy-3.29,13.20),(ix-5.0,iy-3.29,13.20)],"#203742","#10181d",w,h)
            for wx in (-3.4,-.9,1.6,4.1):
                self._add_box(faces,ix+wx,iy-3.34,12.42,.06,.05,.82,"#77858b",w,h)
            # Large integrated funnel; faceted cylinder avoids another rectangular tower.
            self._add_cylinder(faces,ix-3.2,iy+1.0,13.75,1.45,3.9,"#4d595f",w,h,12)
            self._add_cylinder(faces,ix-3.2,iy+1.0,17.58,1.48,.24,"#232a2e",w,h,12)
            # Tripod mast and yards.
            for ox,oy in ((2.9,0),(2.2,.62),(2.2,-.62)):
                self._add_cylinder(faces,ix+ox,iy+oy,13.7,.085,6.9,"#5e6a70",w,h,7)
            self._add_oriented_box(faces,ix+2.8,iy,18.15,8.4,.10,.10,0,"#707a80",w,h)
            self._add_oriented_box(faces,ix+2.8,iy,16.45,5.8,.10,.10,90,"#707a80",w,h)
            # Small radar/director discs and gallery rails.
            self._add_cylinder(faces,ix+5.8,iy-1.5,14.0,.50,.18,"#69767c",w,h,10)
            for off in (-8,-4,0,4,8):
                self._add_cylinder(faces,ix+off,iy-3.55,9.4,.025,.65,"#a6afb4",w,h,6)
            self._add_oriented_box(faces,ix,iy-3.55,10.02,18.0,.035,.035,0,"#a6afb4",w,h)
            self.render_distance=_rd
        # Starboard gallery/sponson blocks for AA/director positions. Kept sparse for performance.
        if layer.key=="FLIGHT":
            for lx in (42,82,132,198,224):
                gx=SHIP_ORIGIN_X+lx; gy=SHIP_ORIGIN_Y+29.5
                if math.hypot(gx-self.x,gy-self.y)<self.detail_radius+12:
                    self._add_oriented_box(faces,gx,gy,5.65,6.0,2.2,.55,0,"#3d474e",w,h)
                    self._add_cylinder(faces,gx,gy,6.18,.42,.18,"#59636a",w,h,9)
        # v2.6 Midway-1942 period silhouette: 5in/38 galleries, 1.1in quads, 20mm Oerlikons,
        # aircraft crane/searchlights and stronger wood/tie-down deck read. Exact coordinates are art reconstruction.
        if layer.key in ("FLIGHT","ISLAND","BRIDGE"):
            zgun=z_flight+.04
            five=[(31,-.45,-1),(64,-.45,-1),(181,-.45,-1),(214,-.45,-1),(31,30.45,1),(64,30.45,1),(181,30.45,1),(214,30.45,1)]
            for lx,ly,out in five:
                gx=SHIP_ORIGIN_X+lx; gy=SHIP_ORIGIN_Y+ly
                if math.hypot(gx-self.x,gy-self.y)<self.detail_radius+10:
                    self._add_5in38_mount(faces,gx,gy,zgun,out,w,h)
            quads=[(157,19.2,180),(170,19.2,180),(72,29.8,90),(202,29.8,90)]
            for lx,ly,hdg in quads:
                gx=SHIP_ORIGIN_X+lx; gy=SHIP_ORIGIN_Y+ly
                if math.hypot(gx-self.x,gy-self.y)<self.detail_radius+9:
                    self._add_11quad_mount(faces,gx,gy,zgun,hdg,w,h)
            # Thirty close-range 20mm positions are distributed as period-detail cues; only nearby mounts render.
            oer=[]
            for lx in (18,35,52,69,86,103,120,137,154,188,207,226): oer.append((lx,.55,-90))
            for lx in (18,35,52,69,86,103,120,137,188,207,226,235): oer.append((lx,29.45,90))
            oer += [(155,18.9,180),(161,18.9,180),(167,18.9,180),(173,18.9,180),(160,29.1,90),(177,29.1,90)]
            for lx,ly,hdg in oer[:30]:
                gx=SHIP_ORIGIN_X+lx; gy=SHIP_ORIGIN_Y+ly
                if math.hypot(gx-self.x,gy-self.y)<self.detail_radius+5:
                    self._add_20mm_mount(faces,gx,gy,zgun,hdg,w,h)
            # Period aircraft crane and large searchlights visible in March/April 1942 island photos.
            crane_x,crane_y=SHIP_ORIGIN_X+154,SHIP_ORIGIN_Y+27.2
            if math.hypot(crane_x-self.x,crane_y-self.y)<self.detail_radius+14:
                self._add_cylinder(faces,crane_x,crane_y,z_flight+.25,.08,3.0,"#657077",w,h,8)
                self._add_oriented_box(faces,crane_x+2.0,crane_y,z_flight+3.1,4.4,.12,.12,-12,"#657077",w,h)
                for sx,sy in ((163,19.8),(175,19.8)):
                    self._add_cylinder(faces,SHIP_ORIGIN_X+sx,SHIP_ORIGIN_Y+sy,z_flight+.42,.32,.30,"#7c8589",w,h,10)

    def _render_weather_overlay(self, w: int, h: int, outdoors: bool):
        if not outdoors:
            return
        c=self.canvas; rain=self.physical_world.rain_intensity; fog=self.physical_world.fog_density
        if rain>.05:
            count=int(18+rain*85)
            phase=int(self.physical_world.elapsed*210)
            for i in range(count):
                x=(i*73+phase*3)%max(1,w); y=(i*131+phase*7)%max(1,h)
                ln=8+int(16*rain); c.create_line(x,y,x-3-rain*5,y+ln,fill="#98b7c7",width=1)
        if fog>.04:
            layers=max(1,min(5,int(fog*10)))
            for i in range(layers):
                yy=int(h*(.30+i*.12)); c.create_rectangle(0,yy,w,min(h,yy+int(h*.12)),fill=shade("#91a0a8",.55+i*.05),outline="",stipple="gray50")
        if self.physical_world.lightning_flash>0:
            c.create_rectangle(0,0,w,h,fill="#dce8ef",outline="",stipple="gray75")

    def _add_console_model(self, faces, x: float, y: float, z: float, color: str, w: int, h: int, screen: str = "#2a8ca0"):
        self._add_box(faces,x-.36,y-.28,z+.05,.72,.56,.72,shade(color,.72),w,h)
        self._add_box(faces,x-.31,y-.24,z+.76,.62,.48,.18,color,w,h)
        self._add_box(faces,x-.24,y-.285,z+.84,.48,.035,.28,screen,w,h)
        for bx in (-.18,-.06,.06,.18):
            self._add_box(faces,x+bx-.025,y-.305,z+.72,.05,.025,.04,"#d0b35d",w,h)

    def _add_humanoid(self, faces, x: float, y: float, z: float, body: str, w: int, h: int, heading: float = 0.0, walk_phase: float = 0.0):
        """Articulated procedural sailor with simple gait and arm swing."""
        moving=abs(walk_phase)>.001
        swing=math.sin(walk_phase)*.16 if moving else 0.0
        arm_swing=-math.sin(walk_phase)*.18 if moving else 0.0
        # legs use oriented narrow boxes offset fore/aft to imply a real stride
        a=heading
        rad=math.radians(a); fx,fy=math.cos(rad),math.sin(rad); sx,sy=-fy,fx
        hipx,hipy=x,y
        for side,phase in ((-1,swing),(1,-swing)):
            lx=hipx+sx*side*.085+fx*phase*.38; ly=hipy+sy*side*.085+fy*phase*.38
            self._add_oriented_box(faces,lx,ly,z+.34,.16,.12,.70,a,"#27313d",w,h)
        self._add_oriented_box(faces,x,y,z+.99,.46,.29,.64,a,body,w,h)
        for side,phase in ((-1,arm_swing),(1,-arm_swing)):
            ax=x+sx*side*.29+fx*phase*.28; ay=y+sy*side*.29+fy*phase*.28
            self._add_oriented_box(faces,ax,ay,z+1.01,.12,.12,.54,a,shade(body,.82),w,h)
        self._add_cylinder(faces,x,y,z+1.34,.15,.26,"#c8a889",w,h,8)
        self._add_cylinder(faces,x,y,z+1.59,.17,.05,"#d8dde1",w,h,8)

    def _add_aircraft_model(self, faces, x: float, y: float, z: float, color: str, w: int, h: int, scale: float = 1.0):
        # Stylized but recognizably aircraft-shaped: fuselage, wings, tailplane, vertical tail and canopy.
        self._add_box(faces,x-1.15*scale,y-.15*scale,z+.20*scale,2.30*scale,.30*scale,.30*scale,color,w,h)
        self._add_box(faces,x-.28*scale,y-1.15*scale,z+.25*scale,.65*scale,2.30*scale,.12*scale,shade(color,.92),w,h)
        self._add_box(faces,x-.92*scale,y-.58*scale,z+.32*scale,.42*scale,1.16*scale,.08*scale,shade(color,.8),w,h)
        self._add_box(faces,x-.98*scale,y-.07*scale,z+.35*scale,.18*scale,.14*scale,.46*scale,shade(color,.75),w,h)
        self._add_box(faces,x+.16*scale,y-.12*scale,z+.48*scale,.42*scale,.24*scale,.18*scale,"#416273",w,h)
        self._add_cylinder(faces,x+1.14*scale,y,z+.29*scale,.18*scale,.10*scale,"#25292f",w,h,8)

    def _add_ship_model(self, faces, x: float, y: float, z: float, length: float, color: str, w: int, h: int, carrier: bool = False):
        width=max(.42,length*.23)
        self._add_box(faces,x-length/2,y-width/2,z,length,width,.22,shade(color,.70),w,h)
        self._add_box(faces,x-length*.34,y-width*.42,z+.20,length*.68,width*.84,.16,color,w,h)
        if carrier:
            self._add_box(faces,x-length*.46,y-width*.65,z+.39,length*.92,width*1.30,.08,shade(color,.93),w,h)
            self._add_box(faces,x+length*.08,y-width*.10,z+.46,length*.16,width*.48,.42,shade(color,.78),w,h)
        else:
            self._add_box(faces,x-length*.12,y-width*.18,z+.36,length*.26,width*.36,.34,shade(color,.82),w,h)
            self._add_cylinder(faces,x+length*.03,y,z+.68,width*.10,.32,"#3e444c",w,h,7)

    def _add_ground_vehicle_model(self, faces, x: float, y: float, z: float, heading_deg: float, color: str, w: int, h: int, scale: float = 1.0):
        # Procedural utility/truck silhouette for v1.9 motor-pool and ground-logistics presentation.
        self._add_oriented_box(faces,x,y,z+.18,1.75*scale,.82*scale,.42*scale,heading_deg,color,w,h)
        rad=math.radians(heading_deg); fx,fy=math.cos(rad),math.sin(rad); sx,sy=-fy,fx
        cabx=x+fx*.48*scale; caby=y+fy*.48*scale
        self._add_oriented_box(faces,cabx,caby,z+.58,.66*scale,.76*scale,.48*scale,heading_deg,shade(color,.88),w,h)
        for fore in (-.52,.52):
            for side in (-.37,.37):
                wx=x+fx*fore*scale+sx*side*scale; wy=y+fy*fore*scale+sy*side*scale
                self._add_cylinder(faces,wx,wy,z+.08,.16*scale,.18*scale,"#20242a",w,h,8)

    def _add_armored_vehicle_model(self, faces, x: float, y: float, z: float, heading_deg: float, vehicle_class: str, color: str, w: int, h: int):
        scale=1.0
        if vehicle_class=="MEDIUM_TANK":
            self._add_oriented_box(faces,x,y,z+.22,2.4,1.25,.55,heading_deg,color,w,h)
            self._add_cylinder(faces,x,y,z+.72,.46,.25,shade(color,.9),w,h,10)
            rad=math.radians(heading_deg); fx,fy=math.cos(rad),math.sin(rad)
            self._add_oriented_box(faces,x+fx*.95,y+fy*.95,z+.82,1.75,.14,.12,heading_deg,"#40474a",w,h)
            for fore in (-.78,0,.78):
                for side in (-.58,.58):
                    sx,sy=-fy,fx; wx=x+fx*fore+sx*side; wy=y+fy*fore+sy*side
                    self._add_cylinder(faces,wx,wy,z+.08,.18,.20,"#1e2325",w,h,8)
        elif vehicle_class=="ARMORED_TRANSPORT":
            self._add_oriented_box(faces,x,y,z+.20,2.25,1.05,.72,heading_deg,color,w,h)
            self._add_oriented_box(faces,x,y,z+.89,1.25,.72,.30,heading_deg,shade(color,.9),w,h)
            self._add_ground_vehicle_model(faces,x,y,z,heading_deg,color,w,h,.95)
        else:
            self._add_ground_vehicle_model(faces,x,y,z,heading_deg,color,w,h,.95)

    def _collect_detail_geometry(self, faces, w: int, h: int):
        """v1.5 visual-density pass: ribs, lights, pipes, railings, deck markings and machinery."""
        layer=current_layer(self.x,self.y,self.z)
        if not layer:
            return
        feet=self.z-CAMERA_HEIGHT
        self._add_faceted_hull(faces,w,h)
        self._add_damage_effects(faces,w,h)
        self._add_fault_effects(faces,w,h)
        # Interior overhead structure and utilities.
        if not layer.outdoor:
            ceil=layer.floor_z+2.75
            lx0=int(self.x-layer.origin_x); ly0=int(self.y-layer.origin_y)
            for gx in range(max(1,lx0-10),min(layer.width-1,lx0+11)):
                for gy in range(max(1,ly0-10),min(layer.height-1,ly0+11)):
                    if layer.grid[gy][gx] != ".":
                        continue
                    wx,wy=layer.origin_x+gx+.5,layer.origin_y+gy+.5
                    dist=math.hypot(wx-self.x,wy-self.y)
                    if dist>10.5:
                        continue
                    # fluorescent/battle lights and overhead longitudinal piping at intervals
                    if (gx+gy)%7==0:
                        light="#a9c7c8" if not self.command.general_quarters else "#a83f46"
                        self._add_box(faces,wx-.28,wy-.08,ceil-.09,.56,.16,.05,light,w,h)
                    if gy%9==3 and gx%4==0:
                        pipe="#7e8d78" if layer.key in ("ENGINEERING","HANGAR") else "#667483"
                        self._add_box(faces,wx-.52,wy-.035,ceil-.24,1.04,.07,.07,pipe,w,h)
            # heavy transverse frames every few meters
            for gx in range(max(1,lx0-9),min(layer.width-1,lx0+10)):
                if gx%6: continue
                for gy in range(max(1,ly0-9),min(layer.height-1,ly0+10)):
                    if layer.grid[gy][gx] != ".": continue
                    wx,wy=layer.origin_x+gx+.08,layer.origin_y+gy+.5
                    if math.hypot(wx-self.x,wy-self.y)>9: continue
                    self._add_box(faces,wx-.035,wy-.45,layer.floor_z+.05,.07,.9,2.55,"#59626b",w,h)
        # v1.9 expeditionary district: runway/apron, motor pool, field barriers and airfield cues.
        if layer.key=="BASE" and self.y>40:
            z=layer.floor_z+.025
            # training runway/apron stripe and threshold bars
            self._add_box(faces,3.0,64.9,z,57.0,.18,.025,"#d9d2b5",w,h)
            for xx in range(7,59,6):
                if math.hypot(xx-self.x,65-self.y)<22:
                    self._add_box(faces,xx,64.35,z,.8,.10,.025,"#e7e3cf",w,h)
                    self._add_box(faces,xx,65.45,z,.8,.10,.025,"#e7e3cf",w,h)
            # motor-pool sheds / field stores / sandbag lines
            for gx,gy in ((25,56),(30,56),(35,56)):
                if math.hypot(gx-self.x,gy-self.y)<18:
                    self._add_ground_vehicle_model(faces,gx,gy,layer.floor_z,90,"#64745f",w,h,.9)
            for gx in range(8,20,2):
                if math.hypot(gx-self.x,61-self.y)<16:
                    self._add_box(faces,gx,60.9,layer.floor_z+.05,1.3,.34,.32,"#8a7d5d",w,h)
            # windsock mast and simple airfield light standards
            if math.hypot(55-self.x,61-self.y)<24:
                self._add_cylinder(faces,55,61,layer.floor_z+.05,.06,3.1,"#707981",w,h,7)
                self._add_oriented_box(faces,55.55,61,layer.floor_z+2.70,1.15,.18,.18,0,"#d56f45",w,h)
            for gx in range(6,60,7):
                if math.hypot(gx-self.x,68-self.y)<22:
                    self._add_cylinder(faces,gx,68,layer.floor_z+.03,.04,.30,"#8f9699",w,h,6)
        # v2.0 combined-arms training village: cover, fighting positions, aid point and range detail.
        if layer.key=="BASE" and self.y>72:
            z=layer.floor_z+.04
            # Sandbag / concrete cover lines aligned with the collision geometry.
            for gx,gy,ang,length in (
                (16,84,0,5.5),(29,84,0,5.0),(47,84,0,6.0),
                (22,89,90,6.0),(38,91,90,5.5),(17,97,0,4.5),(46,97,0,5.0),
                (31,93,0,3.2),(52,91,90,3.2),
            ):
                if math.hypot(gx-self.x,gy-self.y)<22:
                    # layered low cover instead of one plain cube
                    for i in range(3):
                        offset=(i-1)*.22
                        if ang==0:
                            self._add_oriented_box(faces,gx,gy+offset,z+i*.16,length,.34,.18,ang,"#8a7a58",w,h)
                        else:
                            self._add_oriented_box(faces,gx+offset,gy,z+i*.16,length,.34,.18,ang,"#8a7a58",w,h)
            # Observation tower / range markers / casualty collection tent.
            if math.hypot(58-self.x,87-self.y)<25:
                for dx,dy in ((-.7,-.7),(.7,-.7),(-.7,.7),(.7,.7)):
                    self._add_cylinder(faces,58+dx,87+dy,layer.floor_z+.05,.06,3.0,"#6f756d",w,h,7)
                self._add_box(faces,57.0,86.0,layer.floor_z+2.7,2.0,2.0,.16,"#696f67",w,h)
            # Field aid tent visual shell.
            if math.hypot(50-self.x,78-self.y)<20:
                self._add_oriented_box(faces,50,78,layer.floor_z+.05,4.0,2.8,.08,0,"#66725f",w,h)
                self._add_oriented_box(faces,50,78,layer.floor_z+1.45,4.2,.08,1.5,0,"#78826c",w,h)
                self._add_cylinder(faces,50,78,layer.floor_z+.3,.18,.18,"#c8d1ca",w,h,8)

        # v2.1 battalion maneuver area: roads, trenches, artillery pits and logistics/medical field sites.
        if layer.key=="BASE" and self.y>103:
            z=layer.floor_z+.035
            # Main dirt/vehicle route through the expanded battlefield.
            self._add_box(faces,29.2,101.0,z,7.6,70.0,.02,"#6d654f",w,h)
            for yy in range(108,171,8):
                if math.hypot(33-self.x,yy-self.y)<28:
                    self._add_box(faces,32.8,yy,z,.35,3.0,.025,"#b8a776",w,h)
            # Sandbag/trench systems around sector lines.
            for gy,gaps in ((142,(14,23,35,47,54)),(153,(11,20,31,42,52)),(164,(16,28,39,49))):
                for gx in range(7,58,3):
                    if any(abs(gx-gap)<2 for gap in gaps): continue
                    if math.hypot(gx-self.x,gy-self.y)<28:
                        self._add_oriented_box(faces,gx,gy,z+.08,2.4,.46,.34,0,"#796e50",w,h)
            # Artillery battery positions and command/medical identifiers.
            for gx in (49,52,55):
                if math.hypot(gx-self.x,118-self.y)<24:
                    self._add_oriented_box(faces,gx,118,z+.22,1.7,.55,.28,0,"#59624f",w,h)
                    self._add_oriented_box(faces,gx+.9,118,z+.48,1.8,.10,.10,0,"#404944",w,h)
            if math.hypot(12-self.x,131-self.y)<22:
                self._add_oriented_box(faces,12,131,z+.05,5.0,3.4,.08,0,"#68715f",w,h)
                self._add_oriented_box(faces,12,131,z+1.55,5.1,.10,1.55,0,"#7d866f",w,h)
                self._add_box(faces,11.75,129.25,z+1.0,.5,.08,.5,"#d5d9d2",w,h)
                self._add_box(faces,11.93,129.07,z+1.0,.14,.44,.5,"#a84f4f",w,h)
            # Anti-vehicle obstacles at the contested line.
            for gx in (8,19,29,41,55):
                if math.hypot(gx-self.x,138-self.y)<24:
                    self._add_oriented_box(faces,gx,138,z+.25,1.2,.14,.14,45,"#565b59",w,h)
                    self._add_oriented_box(faces,gx,138,z+.25,1.2,.14,.14,-45,"#565b59",w,h)

        # v2.2 theater/strategic-war district and persistent front line.
        if layer.key=="BASE" and self.y>171:
            z=layer.floor_z+.035
            # Theater HQ map tables / antenna mast / logistics stacks.
            if math.hypot(11-self.x,183-self.y)<24:
                self._add_oriented_box(faces,11,183,z+.58,4.8,2.8,.95,0,"#4c5962",w,h)
                self._add_oriented_box(faces,11,183,z+1.57,4.4,2.4,.08,0,"#9a8b63",w,h)
            if math.hypot(30-self.x,183-self.y)<24:
                self._add_cylinder(faces,30,183,z+.05,.08,3.5,"#6f777d",w,h,8)
                self._add_oriented_box(faces,30.55,183,z+3.0,1.1,.10,.10,0,"#8e989e",w,h)
            if math.hypot(50-self.x,183-self.y)<24:
                for ix in range(3):
                    for iy in range(2):
                        self._add_box(faces,48.5+ix*1.35,181.8+iy*1.45,z+.08,1.05,1.0,.72,"#6d715b",w,h)
            # Strategic road network and bridge crossing.
            for yline in (194,208,227):
                if abs(yline-self.y)<28:
                    self._add_box(faces,6,yline,z,52,.42,.025,"#706950",w,h)
            if math.hypot(34-self.x,199-self.y)<26:
                # river and bridge at the strategic crossing
                self._add_box(faces,5,198.8,z-.03,54,1.55,.02,"#314f68",w,h)
                bridge=max(0.15,getattr(self.strategic_war.sectors.get("RIVER"),"bridge_integrity",74)/100.0)
                self._add_box(faces,31.5,198.5,z+.06,5.0,2.0,.15,shade("#77705e",bridge),w,h)
            # Sector flags / depots / formations are dynamic and persistent.
            for sec in getattr(self.strategic_war,"sectors",{}).values():
                if math.hypot(sec.x-self.x,sec.y-self.y)>30: continue
                col="#6e9f78" if sec.owner=="FRIENDLY" else ("#a45656" if sec.owner=="ENEMY" else "#b79a55")
                self._add_cylinder(faces,sec.x,sec.y,z+.04,.045,2.0,"#7b8185",w,h,7)
                self._add_oriented_box(faces,sec.x+.45,sec.y,z+1.65,.9,.06,.55,0,col,w,h)
                if sec.fortification>45:
                    self._add_oriented_box(faces,sec.x,sec.y+.9,z+.12,2.2,.42,.36,0,"#766d52",w,h)
            for dep in getattr(self.strategic_war,"depots",{}).values():
                if dep.side!="FRIENDLY" or math.hypot(dep.x-self.x,dep.y-self.y)>28: continue
                self._add_oriented_box(faces,dep.x,dep.y,z+.08,3.0,2.2,.65,0,"#5d6657",w,h)
                self._add_oriented_box(faces,dep.x,dep.y,z+.78,2.4,1.6,.35,0,"#707a67",w,h)
            for form in getattr(self.strategic_war,"formations",{}).values():
                if math.hypot(form.x-self.x,form.y-self.y)>30: continue
                col="#596e87" if form.side=="FRIENDLY" else "#7d5353"
                if form.role=="ARMOR":
                    self._add_armored_vehicle_model(faces,form.x,form.y,z,0,"MEDIUM_TANK",col,w,h)
                else:
                    # one rendered figure represents a strategic formation marker, not one soldier.
                    self._add_humanoid(faces,form.x,form.y,z,col,w,h,0,self._walk_phase if form.order in ("ATTACK","DEFEND","RECON") else 0)
                    self._add_cylinder(faces,form.x+.55,form.y,z+.05,.04,1.35,"#737b80",w,h,6)
                    self._add_oriented_box(faces,form.x+.83,form.y,z+1.08,.55,.05,.34,0,col,w,h)

        # v2.3 national industrial district: factories, shipyard, refinery, training command and rail/port control.
        if layer.key=="BASE" and self.y>242:
            z=layer.floor_z+.035
            # Main industrial service road and rail spine.
            self._add_box(faces,28.5,245,z,8.5,62,.02,"#625d52",w,h)
            self._add_box(faces,31.2,245,z+.025,.13,62,.05,"#555b60",w,h)
            self._add_box(faces,34.6,245,z+.025,.13,62,.05,"#555b60",w,h)
            for yy in range(250,307,3):
                if abs(yy-self.y)<30:
                    self._add_box(faces,31.2,yy,z+.02,3.55,.12,.04,"#68635b",w,h)
            # Facility stacks / tanks / production sheds reflect live damage/readiness.
            for f in self.war_economy.facilities.values():
                if math.hypot(f.x-self.x,f.y-self.y)>32: continue
                health=max(.18,1.0-f.damage/100.0)
                col=shade("#66717a",health)
                if f.kind in ("AIRCRAFT","VEHICLE","MUNITIONS","TRAINING","LOGISTICS"):
                    self._add_oriented_box(faces,f.x,f.y,z+.05,6.0,4.2,1.8,0,col,w,h)
                    self._add_oriented_box(faces,f.x,f.y,z+1.9,5.3,3.5,.15,0,"#818991",w,h)
                    for dx in (-2.0,0,2.0): self._add_cylinder(faces,f.x+dx,f.y-1.45,z+1.85,.08,1.2,"#858b8d",w,h,7)
                elif f.kind=="REFINERY":
                    for dx in (-1.7,0,1.7): self._add_cylinder(faces,f.x+dx,f.y,z+.05,.72,2.3,shade("#777e78",health),w,h,10)
                    self._add_cylinder(faces,f.x+2.7,f.y+.8,z+.05,.14,4.0,"#656b6d",w,h,8)
                elif f.kind=="SHIPYARD":
                    self._add_oriented_box(faces,f.x,f.y,z+.05,7.0,4.5,.55,0,shade("#56636b",health),w,h)
                    self._add_cylinder(faces,f.x-2.5,f.y,z+.55,.09,3.5,"#7b8285",w,h,7)
                    self._add_oriented_box(faces,f.x-1.2,f.y,z+3.6,3.0,.12,.12,0,"#7b8285",w,h)
                if f.damage>20:
                    # Industrial damage/smoke is a visual training effect tied to the economy state.
                    self._add_cylinder(faces,f.x+.6,f.y+.5,z+2.1,.15,1.2,"#4b4f52",w,h,7)
            # Stockpile crates around national allocation board.
            if math.hypot(32-self.x,301-self.y)<26:
                for ix in range(4):
                    for iy in range(2):
                        self._add_box(faces,28.8+ix*1.55,298.6+iy*1.4,z+.06,1.15,1.0,.72,"#74694f",w,h)

        # v2.4 strategic mobility district: freight yards, rail/road spines, port cranes and moving shipment markers.
        if layer.key=="BASE" and self.y>307:
            z=layer.floor_z+.035
            # Central heavy road and twin rail lines connect the industrial district to dispatch/receiving hubs.
            self._add_box(faces,28.5,309,z,8.5,70,.025,"#5d5b54",w,h)
            self._add_box(faces,30.7,309,z+.03,.12,70,.05,"#4f565b",w,h)
            self._add_box(faces,34.5,309,z+.03,.12,70,.05,"#4f565b",w,h)
            for yy in range(312,379,3):
                if abs(yy-self.y)<31: self._add_box(faces,30.7,yy,z+.02,3.92,.10,.035,"#6b665d",w,h)
            # Hub geometry reflects damage/capacity.
            for hub in self.logistics_network.hubs.values():
                if math.hypot(hub.x-self.x,hub.y-self.y)>34: continue
                health=max(.18,1.0-hub.damage/100.0); col=shade("#65717a",health)
                if hub.hub_type in ("DEPOT","RAILHEAD"):
                    self._add_oriented_box(faces,hub.x,hub.y,z+.05,5.2,3.5,1.25,0,col,w,h)
                    for dx in (-1.6,0,1.6): self._add_box(faces,hub.x+dx-.45,hub.y+1.9,z+.06,.9,.8,.65,"#756b52",w,h)
                elif hub.hub_type=="PORT":
                    self._add_oriented_box(faces,hub.x,hub.y,z+.05,5.5,3.6,.65,0,col,w,h)
                    self._add_cylinder(faces,hub.x-2.0,hub.y,z+.7,.08,3.4,"#7b8589",w,h,7)
                    self._add_oriented_box(faces,hub.x-.7,hub.y,z+3.6,2.8,.10,.10,0,"#7b8589",w,h)
                elif hub.hub_type=="AIRFIELD":
                    self._add_oriented_box(faces,hub.x,hub.y,z+.05,5.0,2.8,1.0,0,col,w,h)
                    self._add_box(faces,hub.x-4.5,hub.y+2.5,z,.0+9.0,.35,.025,"#74716a",w,h)
                elif hub.hub_type=="ANCHORAGE":
                    self._add_oriented_box(faces,hub.x,hub.y,z+.05,5.2,3.0,.8,0,col,w,h)
                    for dx in (-1.7,1.7): self._add_cylinder(faces,hub.x+dx,hub.y+.9,z+.05,.42,1.2,"#737a75",w,h,9)
                if hub.damage>25:
                    self._add_cylinder(faces,hub.x+.6,hub.y+.4,z+1.2,.14,.9,"#474c50",w,h,7)
            # Active shipments are visible as railcars/truck/convoy markers interpolated between their physical dispatch hubs.
            for sh in self.logistics_network.shipments.values():
                if sh.status not in ("EN ROUTE","DELAYED"): continue
                route=self.logistics_network.routes.get(sh.route_key)
                if not route: continue
                a=self.logistics_network.hubs.get(route.origin); b=self.logistics_network.hubs.get(route.destination)
                if not a or not b: continue
                t=max(0.0,min(1.0,sh.progress_km/max(.001,route.distance_km)))
                sx=a.x+(b.x-a.x)*t; sy=a.y+(b.y-a.y)*t
                if math.hypot(sx-self.x,sy-self.y)>34: continue
                col="#7a8f78" if sh.status=="EN ROUTE" else "#a78d5d"
                if route.mode=="RAIL":
                    for k in range(3): self._add_oriented_box(faces,sx,sy-k*.95,z+.16,1.6,.72,.62,0,col,w,h)
                elif route.mode=="ROAD":
                    self._add_oriented_box(faces,sx,sy,z+.15,1.7,.85,.72,0,col,w,h)
                    self._add_box(faces,sx-.65,sy-.48,z+.04,.28,.16,.18,"#22282c",w,h); self._add_box(faces,sx+.38,sy-.48,z+.04,.28,.16,.18,"#22282c",w,h)
                else:
                    self._add_oriented_box(faces,sx,sy,z+.05,2.5,.72,.45,0,"#5f7078",w,h)
                    self._add_oriented_box(faces,sx+.2,sy,z+.52,.8,.52,.4,0,"#74828a",w,h)
                if sh.escort:
                    self._add_oriented_box(faces,sx+1.4,sy+.8,z+.10,1.15,.55,.48,0,"#526b7e",w,h)

        # Engineering gets large machinery and colored pipe runs.
        if layer.key=="ENGINEERING":
            for lx,ly in ((58,9),(86,20),(118,9),(151,20),(184,9),(210,20)):
                gx,gy=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly
                if math.hypot(gx-self.x,gy-self.y)<16:
                    self._add_box(faces,gx-1.15,gy-.65,layer.floor_z+.05,2.3,1.3,1.55,"#4a5558",w,h)
                    self._add_cylinder(faces,gx-.45,gy,layer.floor_z+1.58,.18,.62,"#6b6657",w,h,8)
                    self._add_cylinder(faces,gx+.45,gy,layer.floor_z+1.58,.18,.62,"#6b6657",w,h,8)
            for yy,col in ((5,"#8d5a52"),(12,"#607b86"),(20,"#84764e")):
                gy=SHIP_ORIGIN_Y+yy
                if abs(gy-self.y)<12:
                    self._add_box(faces,SHIP_ORIGIN_X+42,gy,layer.floor_z+2.32,169,.10,.10,col,w,h)
        # Hangar structural trusses, catwalks and safety lanes.
        if layer.key=="HANGAR":
            for lx in range(42,201,12):
                gx=SHIP_ORIGIN_X+lx
                if abs(gx-self.x)<16:
                    self._add_box(faces,gx-.05,SHIP_ORIGIN_Y+5.0,layer.floor_z+2.38,.10,19.0,.12,"#6c747b",w,h)
            for ly in (5.2,23.8):
                gy=SHIP_ORIGIN_Y+ly
                if abs(gy-self.y)<14:
                    self._add_box(faces,SHIP_ORIGIN_X+36,gy,layer.floor_z+.03,168,.07,.025,"#d5b85a",w,h)
        # Flight deck markings, catwalk railings and island mast detail.
        if layer.key=="FLIGHT":
            z=layer.floor_z+.025
            # Straight-deck carrier landing cues: longitudinal centerline and aft arresting wires.
            if abs(self.y-SHIP_CENTER_Y)<18:
                self._add_box(faces,SHIP_ORIGIN_X+10,SHIP_CENTER_Y-.045,z,225,.09,.022,"#c6b98d",w,h)
            for lx in (194,198,202,206,210,214,218,222,226):
                gx=SHIP_ORIGIN_X+lx
                if abs(gx-self.x)<28:
                    self._add_box(faces,gx-.035,SHIP_ORIGIN_Y+3.0,z+.018,.07,24.0,.026,"#2a2c2d",w,h)
            for lx in range(18,233,12):
                gx=SHIP_ORIGIN_X+lx
                if abs(gx-self.x)<20:
                    self._add_box(faces,gx,SHIP_CENTER_Y,z,1.6,.08,.025,"#d2c497",w,h)
            for ly in (.8,29.2):
                gy=SHIP_ORIGIN_Y+ly
                for lx in range(8,239,5):
                    gx=SHIP_ORIGIN_X+lx
                    if math.hypot(gx-self.x,gy-self.y)<18:
                        self._add_cylinder(faces,gx,gy,layer.floor_z+.05,.035,.78,"#b3bac1",w,h,6)
                        self._add_box(faces,gx-2.0,gy-.025,layer.floor_z+.72,4.0,.05,.05,"#aab2b8",w,h)
            mastx,masty=SHIP_ORIGIN_X+172,SHIP_ORIGIN_Y+23
            if math.hypot(mastx-self.x,masty-self.y)<24:
                self._add_cylinder(faces,mastx,masty,layer.floor_z+.5,.18,4.3,"#59636c",w,h,8)
                self._add_box(faces,mastx-1.35,masty-.06,layer.floor_z+3.7,2.7,.12,.10,"#737d84",w,h)
        # Lower deck reads as inhabited ship rather than empty corridors: bunks, lockers and mess tables.
        if layer.key=="LOWER":
            for lx,ly in ((42,7),(45,7),(198,21),(201,21),(208,7),(211,7)):
                gx,gy=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly
                if math.hypot(gx-self.x,gy-self.y)<12:
                    for zz in (.18,.86,1.54):
                        self._add_box(faces,gx-.65,gy-.34,layer.floor_z+zz,1.30,.68,.12,"#53616c",w,h)
            for lx in (112,116,120,124):
                gx,gy=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+8
                if math.hypot(gx-self.x,gy-self.y)<12:
                    self._add_box(faces,gx-.55,gy-.40,layer.floor_z+.58,1.1,.8,.08,"#675d4d",w,h)
                    self._add_box(faces,gx-.48,gy-.32,layer.floor_z+.08,.08,.08,.50,"#4d5359",w,h)
                    self._add_box(faces,gx+.40,gy-.32,layer.floor_z+.08,.08,.08,.50,"#4d5359",w,h)
        # Animated rotating machinery/fans and radar antenna.
        if layer.key=="ENGINEERING":
            for lx,ly in ((62,7),(118,22),(176,7),(207,22)):
                gx,gy=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly
                if math.hypot(gx-self.x,gy-self.y)<14:
                    ang=self.physical_world.ventilation_fan_phase_deg
                    for k in range(4):
                        a=ang+k*90
                        self._add_oriented_box(faces,gx,gy,layer.floor_z+1.45,.9,.10,.08,a,"#78848a",w,h)
                    self._add_cylinder(faces,gx,gy,layer.floor_z+1.40,.12,.14,"#4b5258",w,h,8)
        if layer.key in ("ISLAND","BRIDGE","FLIGHT"):
            rx,ry=SHIP_ORIGIN_X+174,SHIP_ORIGIN_Y+23
            rz=LAYERS["ISLAND"].floor_z+2.55
            if math.hypot(rx-self.x,ry-self.y)<25:
                self._add_cylinder(faces,rx,ry,rz-.35,.07,.55,"#626c74",w,h,8)
                self._add_oriented_box(faces,rx,ry,rz,3.1,.10,.10,self.physical_world.radar_angle_deg,"#8a949a",w,h)
        if layer.key=="FLIGHT":
            px=SHIP_ORIGIN_X+242.0
            for py in (SHIP_ORIGIN_Y+9.8,SHIP_ORIGIN_Y+13.3,SHIP_ORIGIN_Y+16.7,SHIP_ORIGIN_Y+20.2):
                if math.hypot(px-self.x,py-self.y)<28:
                    self._add_rotating_propeller(faces,px,py,2.25,self.physical_world.propeller_phase_deg,w,h)

        # Bridge/island windows and instrument rails.
        if layer.key in ("BRIDGE","ISLAND"):
            for lx in range(157,183,3):
                gx=SHIP_ORIGIN_X+lx; gy=SHIP_ORIGIN_Y+20.1 if layer.key=="BRIDGE" else SHIP_ORIGIN_Y+20.0
                if math.hypot(gx-self.x,gy-self.y)<16:
                    self._add_box(faces,gx-.55,gy-.035,layer.floor_z+1.15,1.1,.07,.62,"#29495a",w,h)

    def _render_open_entities(self,w:int,h:int):
        faces=[]; labels=[]; feet=self.z-CAMERA_HEIGHT
        for p in all_static_interactions():
            if abs(p.floor_z-feet)>4 or math.hypot(p.x-self.x,p.y-self.y)>self.entity_radius: continue
            color="#6e55a0" if p.kind=="terminal" else "#526776"
            self._add_console_model(faces,p.x,p.y,p.floor_z,color,w,h,"#2e8ba2" if p.kind=="terminal" else "#6e8c7b")
            labels.append((p.x,p.y,p.floor_z+1.45,p.name,color))
        for key,(layer_key,lx,ly) in SHIP_EQUIPMENT_WORLD.items():
            layer=LAYERS[layer_key]; gx,gy=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly
            if abs(layer.floor_z-feet)>4 or math.hypot(gx-self.x,gy-self.y)>self.entity_radius: continue
            rt=self.shipboard.equipment_runtime.get(key); color="#76529b" if not(rt and rt.fault) else "#ad4653"
            screen="#2b99a6" if not(rt and rt.fault) else "#b84b55"
            self._add_console_model(faces,gx,gy,layer.floor_z,color,w,h,screen)
            labels.append((gx,gy,layer.floor_z+1.5,EQUIPMENT[key].name,color))
        # Hatches animate around a hinge instead of snapping between two block states.
        for key,(layer_key,lx,ly) in SHIP_HATCH_WORLD.items():
            layer=LAYERS[layer_key]; gx,gy=SHIP_ORIGIN_X+lx,SHIP_ORIGIN_Y+ly
            if abs(layer.floor_z-feet)>4 or math.hypot(gx-self.x,gy-self.y)>self.entity_radius: continue
            opened=self.shipboard.hatches.get(key,True); frac=self.physical_world.hatch_fraction.get(key,1.0 if opened else 0.0)
            color="#4f7667" if frac>.5 else "#8c454d"
            angle=90.0-88.0*frac; a=math.radians(angle)
            hx,hy=gx,gy-.45; cx=hx+math.cos(a)*.45; cy=hy+math.sin(a)*.45
            self._add_oriented_box(faces,cx,cy,layer.floor_z+.08,.90,.10,2.2,angle,color,w,h)
            self._add_cylinder(faces,hx,hy,layer.floor_z+.15,.055,2.0,"#8e969b",w,h,7)
        # Vertical connectors / ladder rails and visible rungs.
        for c in CONNECTORS.values():
            if math.hypot(c.x-self.x,c.y-self.y)>self.entity_radius+1.5: continue
            low=min(c.from_z,c.to_z); high=max(c.from_z,c.to_z)
            self._add_box(faces,c.x-.35,c.y-.08,low,.08,.08,high-low+2.1,"#b5a15f",w,h)
            self._add_box(faces,c.x+.27,c.y-.08,low,.08,.08,high-low+2.1,"#b5a15f",w,h)
            rung=low+.35
            while rung<high+1.7:
                self._add_box(faces,c.x-.31,c.y-.095,rung,.58,.07,.045,"#a9965c",w,h); rung+=.34
        # Living crew move through the persistent world.
        for crew in self.life.crew.values():
            if abs(crew.floor_z-feet)>4 or math.hypot(crew.x-self.x,crew.y-self.y)>self.entity_radius: continue
            body="#596a80" if "BATTLE" not in crew.duty.upper() else "#6d574e"
            dx,dy=crew.target_x-crew.x,crew.target_y-crew.y
            heading=math.degrees(math.atan2(dy,dx)) if abs(dx)+abs(dy)>.02 else 0.0
            moving=math.hypot(dx,dy)>.12
            phase=(self.physical_world.elapsed*7.0 + (sum(ord(ch) for ch in crew.key)%17)) if moving else 0.0
            self._add_humanoid(faces,crew.x,crew.y,crew.floor_z,body,w,h,heading,phase)
            labels.append((crew.x,crew.y,crew.floor_z+1.95,f"{crew.name} • {crew.duty}","#aac4df"))
        # v1.9 shore expeditionary district: ground unit representatives, motor-pool vehicle and landing staging.
        layer_now=current_layer(self.x,self.y,self.z)
        if layer_now and layer_now.key=="BASE" and self.y>40:
            z=LAYERS["BASE"].floor_z
            unit_pose={"RIFLE_A":(10.0,62.0),"ENGR_A":(16.0,62.0),"AA_A":(47.0,62.0),"LOG_A":(34.0,62.0)}
            for key,u in self.ground_ops.units.items():
                gx,gy=unit_pose.get(key,(12.0,63.0))
                if math.hypot(gx-self.x,gy-self.y)>18: continue
                col="#6e7863" if u.strength_pct>45 else "#8f5d55"
                count=max(1,min(4,int(u.manpower/24)))
                for i in range(count):
                    self._add_humanoid(faces,gx+(i%2)*.55,gy+(i//2)*.62,z,col,w,h,0.0,self.physical_world.elapsed*5+i)
                labels.append((gx,gy,z+2.0,f"{u.name} • {u.status}","#d6dfb7"))
            d=self.ground_ops.drive
            vx,vy=(d.x,d.y) if d.active else (28.0,55.0)
            if math.hypot(vx-self.x,vy-self.y)<20:
                self._add_ground_vehicle_model(faces,vx,vy,z,d.heading_deg,"#66745f",w,h,1.0)
                if not d.active: labels.append((vx,vy,z+1.5,"BASE UTILITY VEHICLE • PRESS E AT MOTOR POOL","#ead8a0"))
            # Amphibious staging craft is represented on the training apron as a recognizable landing craft mock-up.
            if math.hypot(13-self.x,67-self.y)<20:
                self._add_oriented_box(faces,13,67,z+.10,3.4,1.35,.48,90,"#596b70",w,h)
                self._add_box(faces,14.45,66.45,z+.55,.30,1.1,.38,"#68787c",w,h)
                labels.append((13,67,z+1.35,"AMPHIBIOUS TRAINING CRAFT / BEACHHEAD CONTROL","#b9d4d8"))
            # v2.0 live fireteam and opposing-force entities occupy the same training village.
            if self.ground_combat.engagement_active or self.ground_combat.engagement_complete or self.y>73:
                for m in self.ground_combat.squad.values():
                    if math.hypot(m.x-self.x,m.y-self.y)>24: continue
                    col="#59765d" if m.health>=45 else "#8a5a56"
                    heading=_bearing = math.degrees(math.atan2(m.target_y-m.y,m.target_x-m.x)) if abs(m.target_x-m.x)+abs(m.target_y-m.y)>.05 else 0.0
                    phase=self.physical_world.elapsed*6.5 + sum(ord(ch) for ch in m.key)
                    self._add_humanoid(faces,m.x,m.y,z,col,w,h,heading,phase)
                    labels.append((m.x,m.y,z+2.0,f"{m.name} • {m.order} • {m.health:.0f}%","#bde2bf"))
                for contact in self.ground_combat.contacts.values():
                    d=math.hypot(contact.x-self.x,contact.y-self.y)
                    if d>35: continue
                    visible=contact.confidence>=20 or d<9
                    if not visible: continue
                    col="#8e4f4f" if contact.health>0 else "#4e4444"
                    if contact.health>0:
                        self._add_humanoid(faces,contact.x,contact.y,z,col,w,h,180.0,self.physical_world.elapsed*4.3)
                    else:
                        self._add_oriented_box(faces,contact.x,contact.y,z+.08,1.45,.38,.22,25,"#55494a",w,h)
                    ident=contact.label if contact.identified else "TRAINING CONTACT"
                    labels.append((contact.x,contact.y,z+1.9, f"{ident} • {contact.health:.0f}% • SUP {contact.suppression:.0f}%", "#ffc0b7" if contact.health>0 else "#9d8e8b"))

        # v2.1 battalion-scale battlefield entities use the same seamless shore renderer.
        if layer_now and layer_now.key=="BASE" and self.y>102:
            z=LAYERS["BASE"].floor_z
            for u in self.land_warfare.units.values():
                if math.hypot(u.x-self.x,u.y-self.y)>34 or u.manpower<=0: continue
                col="#607452" if u.role!="MEDICAL" else "#728276"
                count=max(1,min(5,int(u.manpower/8)))
                for i in range(count):
                    ox=(i%3)*.58; oy=(i//3)*.60
                    heading=math.degrees(math.atan2(u.target_y-u.y,u.target_x-u.x)) if abs(u.target_x-u.x)+abs(u.target_y-u.y)>.1 else 0.0
                    phase=self.physical_world.elapsed*5.7+i+sum(ord(ch) for ch in u.key)%7
                    self._add_humanoid(faces,u.x+ox,u.y+oy,z,col,w,h,heading,phase)
                labels.append((u.x,u.y,z+2.0,f"{u.key} {u.name} • {u.manpower}/{u.max_manpower} • {u.order}","#c6e0b1"))
            for v in self.land_warfare.vehicles.values():
                if math.hypot(v.x-self.x,v.y-self.y)>38 or v.hull_pct<=0: continue
                col="#687255" if v.hull_pct>45 else "#875a50"
                self._add_armored_vehicle_model(faces,v.x,v.y,z,v.heading_deg,v.vehicle_class,col,w,h)
                labels.append((v.x,v.y,z+1.65,f"{v.key} {v.name} • {v.hull_pct:.0f}% • {v.fuel_pct:.0f}% fuel","#e4d8a3"))
            for b in self.land_warfare.artillery.values():
                if math.hypot(b.x-self.x,b.y-self.y)>30: continue
                self._add_oriented_box(faces,b.x,b.y,z+.25,2.1,.65,.35,0,"#5f6753",w,h)
                self._add_oriented_box(faces,b.x+1.05,b.y,z+.56,2.3,.10,.11,0,"#444b42",w,h)
                labels.append((b.x,b.y,z+1.4,f"{b.name} • shells {b.shells} • {b.status}","#d5d1a8"))
            for sec in self.land_warfare.sectors.values():
                if math.hypot(sec.x-self.x,sec.y-self.y)>42: continue
                col="#6d975c" if sec.status=="SECURED" else "#b88b4b" if sec.friendly_control>35 else "#9b5550"
                self._add_cylinder(faces,sec.x,sec.y,z+.05,.07,2.8,col,w,h,7)
                self._add_oriented_box(faces,sec.x+.42,sec.y,z+2.25,.85,.06,.52,0,col,w,h)
                labels.append((sec.x,sec.y,z+3.0,f"{sec.key} • CTRL {sec.friendly_control:.0f}% • ENEMY {sec.enemy_strength:.0f}% • {sec.status}","#eee0b8"))
            for contact in self.land_warfare.contacts.values():
                d=math.hypot(contact.x-self.x,contact.y-self.y)
                if d>42 or contact.strength<=0: continue
                visible=contact.confidence>=20 or d<12
                if not visible: continue
                if contact.contact_type=="ARMOR":
                    self._add_armored_vehicle_model(faces,contact.x,contact.y,z,180,"MEDIUM_TANK","#7f4f4d",w,h)
                else:
                    n=3 if contact.contact_type=="INFANTRY" else 2
                    for i in range(n): self._add_humanoid(faces,contact.x+(i-.5)*.45,contact.y+(i%2)*.5,z,"#82504d",w,h,180,self.physical_world.elapsed*4+i)
                ident=contact.label if contact.identified else "BATTLEFIELD CONTACT"
                labels.append((contact.x,contact.y,z+2.1,f"{ident} • STR {contact.strength:.0f}% • SUP {contact.suppression:.0f}%","#ffb0a8"))

        # Aircraft packages remain physical entities.
        for ac in self.shipboard.aircraft.values():
            layer_key="FLIGHT" if ac.deck=="FLIGHT" else "HANGAR"
            floor=LAYERS[layer_key].floor_z
            # spread existing local aircraft positions into the larger physical bay/deck
            gx=SHIP_ORIGIN_X+38+ac.x*5.2; gy=SHIP_ORIGIN_Y+5.5+ac.y*2.25
            if abs(floor-feet)>4 or math.hypot(gx-self.x,gy-self.y)>self.entity_radius+2.0: continue
            self._add_aircraft_model(faces,gx,gy,floor,"#6e7680",w,h,.55)
            labels.append((gx,gy,floor+1.12,f"{ac.aircraft_type} ×{ac.count} • {ac.status}","#d6dde5"))
        # v1.0 simulated combat contacts exist outside the carrier in the same renderer.
        layer_now=current_layer(self.x,self.y,self.z)
        if layer_now and layer_now.outdoor and self.combat.tracks:
            center_x,center_y=SHIP_CENTER_X,SHIP_CENTER_Y
            for track in self.combat.tracks.values():
                if track.destroyed or track.attacked_ship:
                    continue
                rel=math.radians((track.bearing_deg-self.physics.heading_deg)%360.0)
                visual_range=3.5+min(22.0,track.range_nm*1.05)
                gx=center_x+math.cos(rel)*visual_range
                gy=center_y+math.sin(rel)*visual_range
                gz=LAYERS["FLIGHT"].floor_z+2.0+min(7.0,track.altitude_ft/2200.0)
                if math.hypot(gx-self.x,gy-self.y)>32:
                    continue
                color="#b84b55" if track.identified else "#a66b4f"
                self._add_aircraft_model(faces,gx,gy,gz-.25,color,w,h,.34)
                labels.append((gx,gy,gz+.65,f"SIM CONTACT {track.key} • {track.range_nm:.1f}nm • {track.health:.0f}%",color))
            if self.combat.air.cap_airborne:
                rel=math.radians(325.0)
                gx=center_x+math.cos(rel)*8.0; gy=center_y+math.sin(rel)*8.0; gz=LAYERS["FLIGHT"].floor_z+5.2
                self._add_aircraft_model(faces,gx,gy,gz-.22,"#4d789e",w,h,.32)
                labels.append((gx,gy,gz+.6,"FRIENDLY CAP","#9fd0ff"))
        # v1.3 task-force ships and detected open-ocean contacts are rendered in the same exterior world.
        layer_now=current_layer(self.x,self.y,self.z)
        if layer_now and layer_now.outdoor and self._player_on_ship():
            center_x,center_y=SHIP_CENTER_X,SHIP_CENTER_Y
            for v in self.task_force.friendly.values():
                de=v.east_nm-self.physics.east_nm; dn=v.north_nm-self.physics.north_nm
                rng=math.hypot(de,dn)
                brg=(math.degrees(math.atan2(de,dn))%360.0) if rng>1e-6 else self.physics.heading_deg
                rel=math.radians((brg-self.physics.heading_deg)%360.0)
                visual_range=3.0+min(30.0,rng*5.0)
                gx=center_x+math.cos(rel)*visual_range; gy=center_y+math.sin(rel)*visual_range; gz=LAYERS["FLIGHT"].floor_z+0.35
                if math.hypot(gx-self.x,gy-self.y)>36: continue
                color="#527fa4" if v.hull_pct>55 else "#9b6060"
                length=1.8 if v.vessel_type=="CARRIER" else 1.25 if "CRUISER" in v.vessel_type else .88
                self._add_ship_model(faces,gx,gy,gz,length,color,w,h,v.vessel_type=="CARRIER")
                labels.append((gx,gy,gz+.9,f"{v.name} • {rng:.1f}nm • {v.status}","#acd7ff" if v.hull_pct>55 else "#ffb2b2"))
            for fc in self.task_force.contacts.values():
                if not fc.detected or fc.health_pct<=0: continue
                de=fc.east_nm-self.physics.east_nm; dn=fc.north_nm-self.physics.north_nm
                rng=math.hypot(de,dn); brg=(math.degrees(math.atan2(de,dn))%360.0) if rng>1e-6 else self.physics.heading_deg
                rel=math.radians((brg-self.physics.heading_deg)%360.0)
                visual_range=4.0+min(30.0,rng*2.2)
                gx=center_x+math.cos(rel)*visual_range; gy=center_y+math.sin(rel)*visual_range
                gz=LAYERS["FLIGHT"].floor_z+(0.05 if fc.submerged else .3)
                if math.hypot(gx-self.x,gy-self.y)>36: continue
                color="#a45555" if not fc.submerged else "#7b556f"
                self._add_ship_model(faces,gx,gy,gz,.95,color,w,h,False)
                labels.append((gx,gy,gz+.7,f"FLEET CONTACT {fc.key} • {rng:.1f}nm • {fc.confidence:.0f}%", "#ffb3b3"))
            # v1.4 persistent campaign entities: nearby logistics convoys and operational bases.
            for cv in self.campaign.convoys.values():
                de=cv.east_nm-self.physics.east_nm; dn=cv.north_nm-self.physics.north_nm
                rng=math.hypot(de,dn)
                if rng>35.0 or cv.health_pct<=0: continue
                brg=(math.degrees(math.atan2(de,dn))%360.0) if rng>1e-6 else self.physics.heading_deg
                rel=math.radians((brg-self.physics.heading_deg)%360.0)
                visual_range=4.0+min(30.0,rng*2.4)
                gx=center_x+math.cos(rel)*visual_range; gy=center_y+math.sin(rel)*visual_range; gz=LAYERS["FLIGHT"].floor_z+.30
                if math.hypot(gx-self.x,gy-self.y)>38: continue
                color="#6a8b73" if cv.health_pct>50 else "#9b6460"
                self._add_ship_model(faces,gx,gy,gz,1.4,color,w,h,False)
                labels.append((gx,gy,gz+.78,f"LOGISTICS {cv.name} • {rng:.1f}nm • {cv.status}","#b9e7c5"))
            for base in self.campaign.bases.values():
                de=base.east_nm-self.physics.east_nm; dn=base.north_nm-self.physics.north_nm
                rng=math.hypot(de,dn)
                if rng>18.0 or (rng<0.5 and self.physics.moored): continue
                brg=(math.degrees(math.atan2(de,dn))%360.0) if rng>1e-6 else self.physics.heading_deg
                rel=math.radians((brg-self.physics.heading_deg)%360.0)
                visual_range=5.0+min(28.0,rng*2.6)
                gx=center_x+math.cos(rel)*visual_range; gy=center_y+math.sin(rel)*visual_range; gz=LAYERS["FLIGHT"].floor_z+.15
                if math.hypot(gx-self.x,gy-self.y)>38: continue
                self._add_box(faces,gx-1.0,gy-.6,gz,2.0,1.2,.5,"#756d55",w,h)
                labels.append((gx,gy,gz+.95,f"BASE {base.key} • {rng:.1f}nm • readiness {base.readiness:.0f}%","#e8d9a3"))
        # v1.5 persistent air-wing aircraft. Grounded/spotted aircraft are individual 3D objects; airborne missions appear outside.
        layer_now=current_layer(self.x,self.y,self.z)
        if layer_now and layer_now.key in ("HANGAR","FLIGHT"):
            floor=LAYERS[layer_now.key].floor_z
            visible=[a for a in self.air_wing.aircraft.values() if (a.deck==layer_now.key and a.status not in ("LOST","AIRBORNE","RETURNING"))]
            for a in visible[:24]:
                pose=self._aircraft_world_pose(a)
                if not pose: continue
                gx,gy,_=pose
                if math.hypot(gx-self.x,gy-self.y)>self.entity_radius+4.0: continue
                colr="#66767d" if a.condition>=75 else "#806761"
                self._add_aircraft_model(faces,gx,gy,floor,colr,w,h,.62)
                labels.append((gx,gy,floor+1.15,f"{a.key} • {a.status} • {a.condition:.0f}%","#d6dde5"))
        if layer_now and layer_now.outdoor and self._player_on_ship():
            center_x,center_y=SHIP_CENTER_X,SHIP_CENTER_Y
            airborne=[m for m in self.air_wing.missions.values() if m.status in ("AIRBORNE","RETURNING")]
            for idx,m in enumerate(airborne[:6]):
                ang=math.radians((self.physics.heading_deg+35+idx*42)%360)
                dist=7.5+idx*2.1
                gx=center_x+math.cos(ang)*dist; gy=center_y+math.sin(ang)*dist; gz=LAYERS["FLIGHT"].floor_z+4.0+idx*.55
                self._add_aircraft_model(faces,gx,gy,gz,"#527aa0",w,h,.32)
                labels.append((gx,gy,gz+.65,f"AIR GROUP {m.key} • {m.mission_type} • {m.status}","#a9d4ff"))
        # Objective beacon
        obj=self._objective_world_pose()
        if obj:
            ox,oy,oz,title=obj
            if math.hypot(ox-self.x,oy-self.y)<30:
                self._add_box(faces,ox-.08,oy-.08,oz+.15,.16,.16,2.4,"#c49b48",w,h)
                labels.append((ox,oy,oz+2.75,"OBJECTIVE", "#ffd77b"))
        faces.sort(key=lambda x:x[0],reverse=True)
        for depth,pts,fill,outline in faces:
            if len(pts)>=6: self.canvas.create_polygon(*pts,fill=fill,outline=outline,width=1)
        for x,y,z,text,color in labels:
            p=project_point(x,y,z,self.x,self.y,self.z,self.yaw,self.pitch,w,h)
            if p and 0<p[2]<12 and -100<p[0]<w+100 and -60<p[1]<h+60:
                self.canvas.create_text(p[0],p[1],text=text,fill=color,font=("Segoe UI Semibold",8),anchor="s")

    def _render_flight_cockpit(self,w:int,h:int):
        c=self.canvas; f=self.flight
        # Aircraft attitude moves the horizon; bank rotates it across the window.
        daylight=self.physical_world.daylight
        sky_top,sky_horizon,sea=sky_colors(self.physical_world)
        mid=h*.43 + f.pitch_deg*h/60.0
        slope=math.tan(math.radians(f.bank_deg))*w*.47
        ly,ry=int(mid-slope),int(mid+slope)
        c.create_polygon(0,0,w,0,w,ry,0,ly,fill=sky_top,outline="")
        c.create_polygon(0,ly,w,ry,w,h,0,h,fill=sea,outline="")
        # Atmospheric bands and moving water references.
        c.create_line(0,ly,w,ry,fill=sky_horizon,width=3)
        phase=(self.physical_world.elapsed*35+f.distance_nm*250)%60
        for yy in range(int(mid)+25,h,34):
            c.create_line(-30+phase,yy,w,yy+int(slope*.12),fill=shade(sea,1.30),width=1)
        # Carrier perspective cue when near Enterprise, and full deck view while still aboard.
        rng=math.hypot(f.east_nm-self.physics.east_nm,f.north_nm-self.physics.north_nm)
        rel=((math.degrees(math.atan2(self.physics.east_nm-f.east_nm,self.physics.north_nm-f.north_nm))-f.heading_deg+180)%360)-180 if rng>.0001 else 0.0
        if f.on_deck:
            deck_y=int(h*.46)
            c.create_polygon(w*.08,h,w*.92,h,w*.64,deck_y,w*.36,deck_y,fill="#34383d",outline="#818991",width=2)
            c.create_line(w/2,h,w/2,deck_y,fill="#d0c48d",width=3)
            c.create_rectangle(w*.66,deck_y-55,w*.76,deck_y+12,fill="#4b545b",outline="#8b969e")
            c.create_text(w*.71,deck_y-62,text="CV-6 ISLAND",fill="#dbe3e8",font=("Segoe UI Semibold",8))
        elif rng<6.0:
            px=w/2 + max(-w*.42,min(w*.42,rel/55*w*.34))
            scale=max(16,min(155,120/(rng+.35)))
            py=mid + max(-h*.25,min(h*.26,(f.altitude_ft/900.0-rng*.05)*-h*.18))
            c.create_polygon(px-scale,py+scale*.18,px+scale,py+scale*.18,px+scale*.55,py-scale*.10,px-scale*.55,py-scale*.10,fill="#3e454b",outline="#c3ccd1")
            c.create_rectangle(px+scale*.18,py-scale*.24,px+scale*.34,py-scale*.02,fill="#59626a",outline="")
            c.create_text(px,py+scale*.34,text=f"USS ENTERPRISE • {rng:.2f} nm",fill="#f0e1a7",font=("Segoe UI Semibold",9))
        # Nearby task-force contacts as simplified silhouettes in the flight world.
        for vessel in list(self.task_force.friendly.values())[:8]:
            de=vessel.east_nm-f.east_nm; dn=vessel.north_nm-f.north_nm; vr=math.hypot(de,dn)
            if vr<.05 or vr>5.0: continue
            brg=math.degrees(math.atan2(de,dn)); rr=((brg-f.heading_deg+180)%360)-180
            if abs(rr)>75: continue
            px=w/2+rr/75*w*.44; py=mid+35+min(90,vr*16); sz=max(3,14-vr*2)
            c.create_rectangle(px-sz,py-sz*.25,px+sz,py+sz*.25,fill="#69757d",outline="#aab7be")
        # v1.8 cockpit training contacts in the same global sea coordinate system.
        for contact in self.flight_combat.contacts.values():
            if not contact.active or contact.health <= 0:
                continue
            de=contact.east_nm-f.east_nm; dn=contact.north_nm-f.north_nm; crng=math.hypot(de,dn)
            if crng>10.0: continue
            brg=math.degrees(math.atan2(de,dn))%360.0
            rr=((brg-f.heading_deg+180)%360)-180
            if abs(rr)>72: continue
            px=w/2+rr/72*w*.43
            if contact.kind=="AIR":
                alt_delta=contact.altitude_ft-f.altitude_ft
                py=mid-alt_delta/6500.0*h*.52 + crng*3.0
                size=max(5,min(24,18/(crng+.18)))
                col="#ff8c7a" if contact.key==self.flight_combat.selected_contact else "#d27870"
                c.create_polygon(px,py-size,px+size,py+size,px-size,py+size,fill="",outline=col,width=2)
                c.create_line(px-size*1.4,py,px+size*1.4,py,fill=col,width=1)
            else:
                py=mid+20+min(70,crng*8)
                size=max(5,min(22,16/(crng+.2)))
                col="#ffb36f" if contact.key==self.flight_combat.selected_contact else "#bd895e"
                c.create_rectangle(px-size,py-size*.35,px+size,py+size*.35,outline=col,width=2)
            if contact.identified or contact.key==self.flight_combat.selected_contact:
                c.create_text(px,py+20,text=f"{contact.key} {crng:.2f}nm",fill=col,font=("Consolas",8))

        # Cockpit framing.
        c.create_polygon(0,0,w*.08,0,w*.28,h*.17,w*.22,h*.22,fill="#1a2025",outline="#4a5359")
        c.create_polygon(w,0,w*.92,0,w*.72,h*.17,w*.78,h*.22,fill="#1a2025",outline="#4a5359")
        c.create_polygon(0,h,w,h,w*.84,h*.68,w*.16,h*.68,fill="#12171c",outline="#4b555e")
        # Gunsight / attitude cue.
        c.create_oval(w/2-34,h*.37-34,w/2+34,h*.37+34,outline="#a7d9b4",width=2)
        c.create_line(w/2-48,h*.37,w/2-12,h*.37,fill="#a7d9b4",width=2); c.create_line(w/2+12,h*.37,w/2+48,h*.37,fill="#a7d9b4",width=2)
        c.create_line(w/2,h*.37-18,w/2,h*.37+18,fill="#a7d9b4",width=1)
        # Instrument panel.
        instruments=[("IAS",f"{f.airspeed_knots:.0f}"),("ALT",f"{f.altitude_ft:.0f}"),("HDG",f"{f.heading_deg:03.0f}"),("FUEL",f"{f.fuel_pct:.0f}%"),("THR",f"{f.throttle*100:.0f}%"),("VSI",f"{f.vertical_speed_fpm:+.0f}")]
        x0=w*.23; gap=w*.095
        for i,(lab,val) in enumerate(instruments):
            cx=x0+i*gap; cy=h*.81; r=min(38,w*.034)
            c.create_oval(cx-r,cy-r,cx+r,cy+r,fill="#080b0e",outline="#7d8b94",width=2)
            c.create_text(cx,cy-9,text=lab,fill="#9eabb2",font=("Consolas",8)); c.create_text(cx,cy+9,text=val,fill="#e8efe9",font=("Consolas",10,"bold"))
        c.create_text(18,18,text=f"FIRST-PERSON FLIGHT • {cockpit_summary(f,self.physics.east_nm,self.physics.north_nm)}",fill="#f0f4f6",font=("Consolas",10),anchor="nw")
        c.create_text(18,42,text=f"ENGINE {'RUN' if f.engine_running else 'OFF'} • BRAKES {'SET' if f.brakes else 'OFF'} • GEAR {'DOWN' if f.gear_down else 'UP'} • FLAPS {'DOWN' if f.flaps_down else 'UP'} • WIND O/D {self.shipboard.enterprise.wind_over_deck:.0f}kt",fill="#d5c889",font=("Consolas",9),anchor="nw")
        c.create_text(18,64,text=flight_navigation_solution(self.flight_combat,f,self.physics.east_nm,self.physics.north_nm),fill="#9ed7ff",font=("Consolas",9),anchor="nw")
        c.create_text(18,86,text=flight_contact_summary(self.flight_combat,f),fill="#f2b0a7",font=("Consolas",9),anchor="nw")
        c.create_text(18,108,text=f"GUN {f.gun_ammo} • BOMB {f.bombs} • TORP {f.torpedoes} • AIRFRAME {f.airframe_health:.0f}% • ENGINE {f.engine_health:.0f}% • CTRL {f.control_health:.0f}% • PILOT {f.pilot_health:.0f}%",fill="#e6d9a8",font=("Consolas",9),anchor="nw")
        c.create_text(w/2,h-18,text="W/S throttle • A/D bank • arrows pitch/yaw • SPACE guns • T ordnance • J target • M nav • Q radio • X escape • L recover • Esc help",fill="#b5c2ca",font=("Segoe UI",9),anchor="s")
        self._render_weather_overlay(w,h,True)
        if time.monotonic()<self.message_until:
            c.create_rectangle(30,h-88,w-30,h-50,fill="#080c10",outline="#69747b")
            c.create_text(w/2,h-69,text=self.message,fill="#f1f5f7",font=("Segoe UI",10))

    def _render_open_hud(self,w:int,h:int):
        c=self.canvas
        # Fine unobtrusive reticle; the 3D world is the primary visual now.
        c.create_line(w/2-7,h/2,w/2+7,h/2,fill="#d8e0e5")
        c.create_line(w/2,h/2-7,w/2,h/2+7,fill="#d8e0e5")
        layer=layer_label(self.x,self.y,self.z)
        heading=math.degrees(self.yaw)%360.0

        # Compact command strip. v2.4's 900x380 diagnostics panel covered most of the ship.
        c.create_rectangle(12,12,w-12,76,fill="#080d14",outline="#35424c")
        c.create_text(24,20,text=f"WAR SIMULATOR  v{VERSION}",fill="#d8c6ff",font=("Segoe UI Semibold",11),anchor="nw")
        c.create_text(24,44,text=f"{layer}  •  POS {self.x:05.1f}/{self.y:05.1f}  •  DECK {self.z-CAMERA_HEIGHT:+.1f}m",fill="#d9e1e6",font=("Consolas",8),anchor="nw")
        c.create_text(w/2,20,text=f"HDG {heading:03.0f}°   SHIP {self.physics.heading_deg:03.0f}° / {self.physics.speed_knots:04.1f} kt",fill="#e4cb87",font=("Consolas",10,"bold"),anchor="n")
        alert="GQ" if self.command.general_quarters else ("COMBAT" if self.combat.raid_active else "ROUTINE")
        c.create_text(w/2,46,text=f"{alert}  •  {self.visual_quality}  •  {self.fps:02d} FPS  •  F4 quality  •  TAB systems",fill="#91a8b7",font=("Segoe UI",8),anchor="n")
        c.create_text(w-24,20,text=needs_summary(self.life),fill="#d9e4ec",font=("Consolas",8),anchor="ne",width=min(430,w*.34))
        c.create_text(w-24,48,text=f"{self.profile.rank}  •  Hull {self.physics.hull_integrity:.0f}%  •  ENV {self.physical_world.weather_mode}",fill="#9fb7c6",font=("Consolas",8),anchor="ne")

        # A small operational card replaces twelve always-visible debug summaries.
        c.create_rectangle(12,88,390,158,fill="#090f16",outline="#303c45")
        c.create_text(24,98,text="CURRENT DUTY",fill="#7f96a5",font=("Segoe UI Semibold",8),anchor="nw")
        duty=self._objective_text()
        if len(duty)>100: duty=duty[:97]+"..."
        c.create_text(24,118,text=duty,fill="#e4e9ed",font=("Segoe UI",8),anchor="nw",width=352)
        openwo=sum(1 for x in self.life.work_orders.values() if not x.completed)
        c.create_text(24,140,text=f"Maintenance {openwo} open  •  Routine {self.life.routine_score:.0f}%",fill="#8ca3b0",font=("Consolas",7),anchor="nw")

        # Optional deep status panel for command/debug work; hidden by default.
        if self.hud_expanded:
            panel_w=min(690,w-40); x1=12; y1=170; y2=min(h-175,500)
            c.create_rectangle(x1,y1,x1+panel_w,y2,fill="#070c12",outline="#53616c")
            c.create_text(x1+14,y1+10,text="SYSTEMS / OPERATIONAL PICTURE",fill="#cdbaff",font=("Segoe UI Semibold",9),anchor="nw")
            rows=[
                (physics_summary(self.physics),"#e6c879"),
                (combat_summary(self.combat),"#e79d9d" if self.combat.raid_active else "#93a7b8"),
                (command_summary(self.command,self.profile.rank_index),"#d5b8ff"),
                (task_force_summary(self.task_force,self.physics),"#9fd0ff"),
                (campaign_summary(self.campaign,self.physics),"#a8ddb5"),
                (air_wing_summary(self.air_wing),"#d7dba0"),
                (ground_summary(self.ground_ops),"#d4c08a"),
                (warfare_summary(self.land_warfare),"#c7c89a"),
                (strategic_summary(self.strategic_war),"#d2a8cf"),
                (economy_summary(self.war_economy),"#d6be82"),
                (logistics_summary(self.logistics_network),"#8ec6d4"),
                (environment_summary(self.physical_world,self.life.minute_of_day),"#a9c9d8"),
            ]
            yy=y1+36
            for textv,col in rows:
                if yy>y2-16: break
                c.create_text(x1+14,yy,text=textv,fill=col,font=("Consolas",7),anchor="nw",width=panel_w-28)
                yy+=24

        prompt=self._interaction_prompt()
        if prompt:
            pw=min(760,w-80); x1=(w-pw)/2
            c.create_rectangle(x1,h-82,x1+pw,h-42,fill="#0a1017",outline="#7655a1")
            c.create_text(w/2,h-62,text=prompt,fill="#f2eaff",font=("Segoe UI Semibold",10))

        # Context-specific vehicle/combat cards stay compact and only appear when relevant.
        if self.land_warfare.player_vehicle_key:
            d=current_land_vehicle(self.land_warfare)
            c.create_rectangle(w-410,h-172,w-20,h-106,fill="#0a0f16",outline="#806b4e")
            c.create_text(w-34,h-160,text=f"{d.name} • {'RUN' if d.engine_running else 'OFF'} • {d.speed_mps*2.23694:.1f} mph • FUEL {d.fuel_pct:.0f}% • HULL {d.hull_pct:.0f}%",fill="#ecd69a",font=("Consolas",8),anchor="ne")
            c.create_text(w-34,h-136,text=f"MAIN {d.main_ammo} • MG {d.mg_ammo} • I engine • W/S throttle • A/D steer • B brake • SPACE fire • E dismount",fill="#b9b3a2",font=("Segoe UI",7),anchor="ne")
        if self.ground_ops.drive.active:
            d=self.ground_ops.drive
            c.create_rectangle(w-390,h-166,w-20,h-112,fill="#0a0f16",outline="#8a7652")
            c.create_text(w-34,h-154,text=f"GROUND VEHICLE • {'RUN' if d.engine_running else 'OFF'} • {d.speed_mps*2.23694:.1f} mph • FUEL {d.fuel_pct:.0f}%",fill="#e7d8a5",font=("Consolas",8),anchor="ne")
            c.create_text(w-34,h-132,text="I engine • W/S throttle • A/D steer • B brake • E exit",fill="#aeb7bf",font=("Segoe UI",7),anchor="ne")
        if self.ground_combat.player.active:
            pstate=self.ground_combat.player; weap=self.ground_combat.weapons[pstate.selected_weapon]
            c.create_polygon(w*.57,h,w*.66,h*.84,w*.76,h*.86,w*.82,h,fill="#31373b",outline="#778087")
            if self.ground_combat.muzzle_flash_seconds>0:
                mx,my=w*.665,h*.85
                c.create_polygon(mx,my,mx-18,my-12,mx-9,my+3,mx-25,my+12,mx,my+8,mx+17,my+16,mx+10,my,mx+22,my-10,fill="#ffd276",outline="")
            c.create_rectangle(w-410,h-246,w-20,h-174,fill="#0a0f16",outline="#8d665c")
            c.create_text(w-34,h-234,text=f"{weap.name} {weap.magazine_rounds}/{weap.reserve_rounds} • {pstate.stance} • HP {pstate.health:.0f}% • STAM {pstate.stamina:.0f}% • SUP {pstate.suppression:.0f}%",fill="#f1d4c7",font=("Consolas",8),anchor="ne")
            c.create_text(w-34,h-208,text="LMB/Space fire • RMB aim • R reload • C stance • T target • J squad order • H aid",fill="#aeb7bf",font=("Segoe UI",7),anchor="ne")

        # One short help line replaces the old full-screen keyboard legend.
        c.create_text(20,h-18,text="WASD move • E interact • F objective • F1 help • Esc pause",fill="#81919c",font=("Segoe UI",8),anchor="sw")
        if time.monotonic()<self.message_until:
            mw=min(w-80,960); x1=(w-mw)/2
            c.create_rectangle(x1,h-132,x1+mw,h-96,fill="#080e14",outline="#46545e")
            c.create_text(w/2,h-114,text=self.message,fill="#e8edf2",font=("Segoe UI",9),width=mw-24)

    def _interaction_prompt(self) -> str:
        aircraft=self._nearest_enterable_aircraft()
        if aircraft:
            ac,_,_,_=aircraft
            return f"[E] Enter cockpit • {ac.key} {ac.aircraft_type} • {ac.status} • condition {ac.condition:.0f}%"
        conn=nearby_connector(self.x,self.y,self.z)
        if conn:
            c,target=conn; direction="up" if target>(self.z-CAMERA_HEIGHT) else "down"
            return f"[E] Climb {direction}: {c.name} → {next((l.name for l in LAYERS.values() if abs(l.floor_z-target)<.1),'next deck')}"
        hatch=self._world_hatch()
        if hatch:
            key,_,_=hatch; return f"[E] {HATCHES[key].name} • {'OPEN' if self.shipboard.hatches.get(key,True) else 'SHUT'}"
        eq=self._world_ship_equipment()
        if eq: return f"[E] Operate {EQUIPMENT[eq[0]].name}"
        p=nearest_static_interaction(self.x,self.y,self.z)
        return f"[E] {p.name}" if p else ""

    # -------------------- overlays --------------------
    def _overlay_key(self,key:str):
        if self.overlay=="helm_physics":
            if key in ("escape","e"): self.overlay=None
            elif key=="left": self._set_message(set_rudder(self.physics,self.physics.rudder_deg-5),3)
            elif key=="right": self._set_message(set_rudder(self.physics,self.physics.rudder_deg+5),3)
            elif key in ("c","0"): self._set_message(set_rudder(self.physics,0),3)
            return
        if self.overlay=="engine_physics":
            orders={"0":0.0,"1":.16,"2":.34,"3":.67,"4":1.0,"b":-.25}
            if key in ("escape","e"): self.overlay=None
            elif key in orders: self._set_message(set_engine_order(self.physics,orders[key]),3)
            return
        if self.overlay=="combat_plot":
            if key in ("escape","e","b"): self.overlay=None
            elif key=="tab":
                t=cycle_track(self.combat); self._set_message("Selected " + (t.key if t else "no track") + ".",3)
            elif key=="a":
                _,msg=acquire_selected_track(self.combat); self._set_message(msg,4)
            elif key=="s":
                _,msg=calculate_solution(self.combat,self.physics); self._set_message(msg,4)
            elif key=="g": self._set_message(set_general_quarters(self.combat),4)
            elif key=="t":
                ok,msg=start_training_raid(self.combat)
                if ok:
                    self._last_combat_kills=self.combat.enemy_destroyed; self._last_combat_hits=self.combat.hits_taken
                self._set_message(msg,6)
            return
        if self.overlay=="weapons_control":
            if key in ("escape","e"): self.overlay=None
            elif key=="1": self._set_message(select_battery(self.combat,"FIVE_INCH"),3)
            elif key=="2": self._set_message(select_battery(self.combat,"MEDIUM_AA"),3)
            elif key=="3": self._set_message(select_battery(self.combat,"LIGHT_AA"),3)
            elif key=="tab":
                t=cycle_track(self.combat); self._set_message("Selected " + (t.key if t else "no track") + ".",3)
            elif key=="a":
                _,msg=acquire_selected_track(self.combat); self._set_message(msg,4)
            elif key=="s":
                _,msg=calculate_solution(self.combat,self.physics); self._set_message(msg,4)
            elif key in ("space","f"):
                _,msg=fire_selected_battery(self.combat,self.physics); self._set_message(msg,4)
            elif key=="g": self._set_message(set_general_quarters(self.combat),4)
            elif key=="t":
                ok,msg=start_training_raid(self.combat)
                if ok:
                    self._last_combat_kills=self.combat.enemy_destroyed; self._last_combat_hits=self.combat.hits_taken
                self._set_message(msg,6)
            return
        if self.overlay=="air_combat":
            if key in ("escape","e"): self.overlay=None
            elif key=="c":
                _,msg=launch_cap(self.combat,self.shipboard); self._set_message(msg,5)
            elif key=="r":
                _,msg=recover_cap(self.combat,self.shipboard); self._set_message(msg,5)
            elif key=="s":
                _,msg=launch_training_strike(self.combat,self.shipboard); self._set_message(msg,5)
            elif key=="g": self._set_message(set_general_quarters(self.combat),4)
            return
        if self.overlay=="magazine_combat":
            if key in ("escape","e"): self.overlay=None
            elif key=="h":
                _,msg=service_ammunition(self.combat); self._set_message(msg,5)
            elif key=="g": self._set_message(set_general_quarters(self.combat),4)
            return
        if self.overlay=="survivability_dc":
            if key in ("escape","e","f6"): self.overlay=None
            elif key=="tab":
                c=cycle_compartment(self.survivability); self._set_message(f"Selected casualty space: {c.name}.",3)
            elif key=="f":
                _,msg=survivability_fight_fire(self.survivability); self._set_message(msg,4)
            elif key=="p":
                _,msg=start_dewatering(self.survivability); self._set_message(msg,4)
            elif key=="h":
                _,msg=patch_breach(self.survivability); self._set_message(msg,4)
            elif key=="s":
                _,msg=shore_structure(self.survivability); self._set_message(msg,4)
            elif key=="v":
                _,msg=survivability_ventilation(self.survivability); self._set_message(msg,4)
            elif key=="t":
                msg=apply_impact(self.survivability,"TORPEDO",68,side="STARBOARD"); self._set_message("TRAINING INJECT — "+msg,6)
            elif key=="a":
                ok,msg=order_abandon_ship(self.survivability)
                if ok:
                    self.profile.abandon_ship_drills += 1
                    self.profile.add_log("Abandon-ship procedure initiated during survivability training.")
                self._set_message(msg,6)
            return
        if self.overlay=="survivability_boundaries":
            if key in ("escape","e"): self.overlay=None
            elif key=="tab":
                c=cycle_compartment(self.survivability); self._set_message(f"Boundary focus: {c.name}.",3)
            elif key in ("b","space"):
                _,msg=toggle_boundary_for_selected(self.survivability); self._set_message(msg,4)
            return
        if self.overlay=="survivability_medical":
            if key in ("escape","e"): self.overlay=None
            elif key in ("t","m","space"):
                ok,msg=treat_casualties(self.survivability)
                if ok: self.profile.casualties_treated_total += 1
                self._set_message(msg,5)
            return
        if self.overlay=="command_console":
            if key in ("escape","e","c"):
                self.overlay=None
            elif key=="tab":
                d=cycle_department(self.command); self._set_message(f"Command focus: {d.name} — {d.officer}, {d.billet}.",3)
            else:
                keymap={"0":"REPORT","1":"REPAIR","2":"WATERTIGHT","3":"MEDICAL","4":"ENGINEERING","5":"AIRDEF","6":"AIR","g":"GQ","m":"MUSTER","s":"SUPPLY","x":"STANDDOWN"}
                if key in keymap:
                    before=self.command.orders_issued
                    ok,msg=issue_order(self.command,self.profile.rank_index,keymap[key],self.life.minute_of_day,self.command.selected_department.key)
                    if ok and self.command.orders_issued>before:
                        self.profile.command_orders_issued += self.command.orders_issued-before
                        self.profile.add_log(f"Command order: {msg}")
                    route_living_crew(self.command,self.life)
                    self._set_message(msg,5)
            return
        if self.overlay in ("fleet_console","fleet_signal","fleet_logistics"):
            if key in ("escape","e","v"):
                self.overlay=None
                return
            if key=="tab":
                v=cycle_friendly(self.task_force); self._set_message(f"Selected friendly: {v.name if v else 'none'}.",3); return
            if key=="c":
                c=cycle_contact(self.task_force); self._set_message(f"Selected contact: {c.label if c else 'none'}.",3); return
            if key=="r":
                self._set_message(toggle_radio_silence(self.task_force),4); return
            auth=authority_level(self.profile.rank_index)
            if key in ("1","2","3","4","q","w","x","d","t","a","p") and auth < 4:
                self._set_message("FLEET ORDER DENIED — SHIP COMMAND WATCH authority is required. Observe, plot, and report through the chain of command.",5); return
            if key=="1": self._set_message(set_formation(self.task_force,"CARRIER SCREEN"),4)
            elif key=="2": self._set_message(set_formation(self.task_force,"COLUMN"),4)
            elif key=="3": self._set_message(set_formation(self.task_force,"DISPERSED"),4)
            elif key=="4": self._set_message(set_formation(self.task_force,"ASW SCREEN"),4)
            elif key=="q": self._set_message(order_selected_ship(self.task_force,"STATION")[1],4)
            elif key=="w": self._set_message(order_selected_ship(self.task_force,"SCREEN_AHEAD")[1],4)
            elif key=="x": self._set_message(order_selected_ship(self.task_force,"SCREEN_ASTERN")[1],4)
            elif key=="d": self._set_message(order_selected_ship(self.task_force,"DETACH")[1],4)
            elif key=="t":
                ok,msg=start_surface_training_problem(self.task_force,self.physics.east_nm,self.physics.north_nm,self.physics.heading_deg); self._set_message(msg,6)
            elif key=="a":
                ok,msg=engage_selected_contact(self.task_force); self._set_message(msg,5)
            elif key=="p":
                ok,msg=begin_replenishment(self.task_force); self._set_message(msg,5)
            return
        if self.overlay in ("campaign_console","campaign_logistics"):
            if key in ("escape","e","o"):
                self.overlay=None; return
            if key=="tab":
                m=cycle_mission(self.campaign); self._set_message(f"Selected mission: {m.title if m else 'none'}.",3); return
            if key=="b":
                b=cycle_base(self.campaign); self._set_message(f"Selected base: {b.name if b else 'none'}.",3); return
            if key=="c":
                c=cycle_convoy(self.campaign); self._set_message(f"Selected convoy: {c.name if c else 'none'}.",3); return
            if key=="f":
                v=cycle_friendly(self.task_force); self._set_message(f"Selected friendly for campaign support: {v.name if v else 'none'}.",3); return
            if key in ("1","2","3","4"):
                scale={"1":1,"2":5,"3":15,"4":30}[key]; self._set_message(set_time_compression(self.campaign,scale),4); return
            auth=authority_level(self.profile.rank_index)
            if key in ("a","s","r") and auth < 4:
                self._set_message("CAMPAIGN ORDER DENIED — SHIP COMMAND WATCH authority is required. Observe and report through the chain of command.",5); return
            if key=="a":
                ok,msg=accept_selected_mission(self.campaign); self._set_message(msg,5); return
            if key=="s":
                ok,msg=request_port_service(self.campaign,self.task_force,self.physics,self.survivability); self._set_message(msg,5); return
            if key=="r":
                ok,msg=dispatch_selected_for_repair(self.campaign,self.task_force); self._set_message(msg,5); return
            return
        if self.overlay=="strategic_command":
            if key in ("escape","e","f10"):
                self.overlay=None; return
            if key=="tab":
                f=cycle_strategic_formation(self.strategic_war); self._set_message(f"Selected theater formation: {f.name if f else 'none'}.",3); return
            if key=="b":
                sec=cycle_strategic_sector(self.strategic_war); self._set_message(f"Selected front-line sector: {sec.name if sec else 'none'}.",3); return
            if key=="d":
                dep=cycle_strategic_depot(self.strategic_war); self._set_message(f"Selected theater depot: {dep.name if dep else 'none'}.",3); return
            if key=="o":
                op=cycle_strategic_operation(self.strategic_war); self._set_message(f"Selected strategic operation: {op.title if op else 'none'}.",3); return
            auth=authority_level(self.profile.rank_index)
            if key in ("1","2","3","4","5","6","a","r","i","n","p","x") and auth < 4:
                self._set_message("STRATEGIC ORDER DENIED — operational command-watch authority is required. Junior personnel may observe, plot, and report.",5); return
            if key=="s":
                ok,msg=begin_strategic_campaign(self.strategic_war); self._set_message(msg,6); return
            ordermap={"1":"RESERVE","2":"DEFEND","3":"ATTACK","4":"RECON","5":"WITHDRAW","6":"RESUPPLY"}
            if key in ordermap:
                ok,msg=order_strategic_formation(self.strategic_war,ordermap[key]); self._set_message(msg,5); return
            if key=="a":
                ok,msg=accept_strategic_operation(self.strategic_war); self._set_message(msg,5); return
            if key=="r":
                ok,msg=strategic_recon(self.strategic_war); self._set_message(msg,5); return
            if key=="i":
                ok,msg=request_strategic_artillery(self.strategic_war,self.land_warfare); self._set_message(msg,5); return
            if key=="q":
                if auth < 4: self._set_message("STRATEGIC AIR ORDER DENIED — operational command authority required.",5); return
                ok,msg=request_air_interdiction(self.strategic_war,self.ground_ops); self._set_message(msg,5); return
            if key=="n":
                if auth < 4: self._set_message("STRATEGIC NAVAL FIRE ORDER DENIED — operational command authority required.",5); return
                ok,msg=request_coastal_naval_support(self.strategic_war,self.task_force); self._set_message(msg,5); return
            if key=="p":
                ok,msg=reinforce_selected_formation(self.strategic_war); self._set_message(msg,5); return
            if key=="x":
                ok,msg=repair_selected_bridge(self.strategic_war); self._set_message(msg,5); return
            return
        if self.overlay=="economy_console":
            if key in ("escape","e","f12"):
                self.overlay=None; return
            if key=="tab":
                f=cycle_economy_facility(self.war_economy); self._set_message(f"Selected industrial facility: {f.name if f else 'none'}.",3); return
            if key=="o":
                o=cycle_economy_order(self.war_economy); self._set_message(f"Selected production order: {o.title if o else 'none'}.",3); return
            if key=="r":
                q=cycle_economy_research(self.war_economy); self._set_message(f"Selected research project: {q.title if q else 'none'}.",3); return
            if key=="t":
                q=cycle_economy_training(self.war_economy); self._set_message(f"Selected training pipeline: {q.title if q else 'none'}.",3); return
            if key=="d":
                dest=cycle_economy_allocation(self.war_economy); self._set_message(f"National allocation destination: {dest}.",3); return
            auth=authority_level(self.profile.rank_index)
            if key in ("s","p","i","g","f","x","a") and auth < 5:
                self._set_message("WAR ECONOMY ORDER DENIED — national command authority (Captain or above in this training career model) is required. Junior personnel may inspect and report.",5); return
            if key=="s":
                ok,msg=begin_war_economy(self.war_economy); self._set_message(msg,6); return
            if key=="p":
                ok,msg=start_economy_order(self.war_economy); self._set_message(msg,5); return
            if key=="i":
                ok,msg=start_economy_research(self.war_economy); self._set_message(msg,5); return
            if key=="g":
                ok,msg=toggle_economy_training(self.war_economy); self._set_message(msg,5); return
            if key=="f":
                ok,msg=repair_economy_facility(self.war_economy); self._set_message(msg,5); return
            if key=="x":
                ok,msg=repair_economy_transport(self.war_economy); self._set_message(msg,5); return
            if key=="a":
                ok,msg=allocate_economy_stockpiles(self.war_economy,self.strategic_war,self.campaign,self.air_wing,self.land_warfare,self.task_force,self.logistics_network); self._set_message(msg,6); return
            return
        if self.overlay=="logistics_console":
            if key in ("escape","e","f5"):
                self.overlay=None; return
            if key=="tab":
                r=cycle_logistics_route(self.logistics_network); self._set_message(f"Selected transport route: {r.name if r else 'none'}.",3); return
            if key=="h":
                h=cycle_logistics_hub(self.logistics_network); self._set_message(f"Selected logistics hub: {h.name if h else 'none'}.",3); return
            if key=="p":
                q=cycle_logistics_package(self.logistics_network); self._set_message(f"Selected cargo package: {q.title if q else 'none'}.",3); return
            if key=="n":
                sh=cycle_logistics_shipment(self.logistics_network); self._set_message(f"Selected shipment: {sh.key if sh else 'none'}.",3); return
            if key=="g":
                pr=cycle_logistics_priority(self.logistics_network); self._set_message(f"Shipment priority set to {pr}.",3); return
            auth=authority_level(self.profile.rank_index)
            if key in ("s","a","c","x","f","i") and auth < 4:
                self._set_message("LOGISTICS ORDER DENIED — operational command-watch authority is required. Junior personnel may inspect routes, hubs, cargo and shipment status.",5); return
            if key=="s":
                ok,msg=begin_logistics_network(self.logistics_network); self._set_message(msg,6); return
            if key=="a":
                ok,msg=dispatch_logistics_shipment(self.logistics_network,self.war_economy); self._set_message(msg,6); return
            if key=="c":
                ok,msg=assign_logistics_escort(self.logistics_network,self.task_force); self._set_message(msg,5); return
            if key=="x":
                ok,msg=repair_logistics_route(self.logistics_network,self.war_economy); self._set_message(msg,5); return
            if key=="f":
                ok,msg=repair_logistics_hub(self.logistics_network,self.war_economy); self._set_message(msg,5); return
            if key=="i":
                ok,msg=issue_logistics_hub(self.logistics_network,self.strategic_war,self.campaign,self.air_wing,self.ground_ops,self.land_warfare,self.task_force); self._set_message(msg,6); return
            return
        if self.overlay=="land_command":
            if key in ("escape","e","f8"):
                self.overlay=None; return
            if key=="tab":
                u=cycle_land_unit(self.land_warfare); self._set_message(f"Selected battalion unit: {u.name if u else 'none'}.",3); return
            if key=="v":
                v=cycle_land_vehicle(self.land_warfare); self._set_message(f"Selected battlefield vehicle: {v.name if v else 'none'}.",3); return
            if key=="b":
                sec=cycle_land_sector(self.land_warfare); self._set_message(f"Selected sector: {sec.name if sec else 'none'}.",3); return
            if key=="t":
                c=cycle_land_contact(self.land_warfare); self._set_message(f"Selected battlefield contact: {c.label if c else 'none'}.",3); return
            auth=authority_level(self.profile.rank_index)
            if key in ("1","2","3","4","5","6","r","m") and auth < 3:
                self._set_message("LAND ORDER DENIED — division/team leadership authority is required. Junior personnel may observe and report.",5); return
            if key in ("a","q","n") and auth < 4:
                self._set_message("FIRE SUPPORT ORDER DENIED — ship/field command-watch authority is required for joint fires.",5); return
            if key=="o":
                ok,msg=begin_land_operation(self.land_warfare); self._set_message(msg,6); return
            ordermap={"1":"HOLD","2":"ADVANCE","3":"SUPPRESS","4":"ASSAULT","5":"DIG IN","6":"WITHDRAW"}
            if key in ordermap:
                ok,msg=order_land_unit(self.land_warfare,ordermap[key]); self._set_message(msg,5); return
            if key=="r":
                ok,msg=land_resupply(self.land_warfare); self._set_message(msg,5); return
            if key=="m":
                ok,msg=land_medevac(self.land_warfare); self._set_message(msg,5); return
            if key=="a":
                ok,msg=land_artillery_support(self.land_warfare); self._set_message(msg,5); return
            if key=="q":
                ok,msg=land_air_support(self.land_warfare,self.ground_ops); self._set_message(msg,5); return
            if key=="n":
                ok,msg=land_naval_support(self.land_warfare,self.task_force); self._set_message(msg,5); return
            return
        if self.overlay=="ground_combat_console":
            if key in ("escape","e","g"):
                self.overlay=None; return
            if key=="tab":
                c=cycle_ground_contact(self.ground_combat); self._set_message(f"Ground target: {c.label if c else 'none'}.",3); return
            if key in ("1","2","3"):
                self.ground_combat.player.selected_weapon={"1":"RIFLE","2":"AUTO","3":"SIDEARM"}[key]
                w=self.ground_combat.weapons[self.ground_combat.player.selected_weapon]; self._set_message(f"Selected {w.name}.",3); return
            if key=="c": self._set_message(cycle_ground_stance(self.ground_combat),3); return
            if key=="j":
                orders=("FOLLOW","HOLD","SUPPRESS","ASSAULT","FALL BACK")
                cur=self.ground_combat.selected_order if self.ground_combat.selected_order in orders else "FOLLOW"
                order=orders[(orders.index(cur)+1)%len(orders)]
                _,msg=order_ground_squad(self.ground_combat,order,self.x,self.y); self._set_message(msg,3); return
            if key=="h": _,msg=ground_first_aid(self.ground_combat); self._set_message(msg,4); return
            if key=="m": _,msg=treat_ground_casualty(self.ground_combat); self._set_message(msg,4); return
            if key=="5": _,msg=ground_air_support(self.ground_combat,self.ground_ops,self.x,self.y); self._set_message(msg,5); return
            if key=="6": _,msg=ground_naval_support(self.ground_combat,self.task_force,self.x,self.y); self._set_message(msg,5); return
            if key=="x": _,msg=end_ground_engagement(self.ground_combat); self._set_message(msg,4); return
            return
        if self.overlay in ("ground_combat_help","ground_combat_debrief"):
            if key in ("escape","e","h","return","space","g"):
                self.overlay=None
            return
        if self.overlay=="ground_console":
            if key in ("escape","e","g"):
                self.overlay=None; return
            if key=="tab":
                m=cycle_ground_mission(self.ground_ops); self._set_message(f"Selected ground mission: {m.title if m else 'none'}.",3); return
            if key=="c":
                u=cycle_ground_unit(self.ground_ops); self._set_message(f"Selected ground unit: {u.name if u else 'none'}.",3); return
            if key=="v":
                v=cycle_ground_vehicle(self.ground_ops); self._set_message(f"Selected ground vehicle: {v.name if v else 'none'}.",3); return
            if key=="b":
                a=cycle_ground_airfield(self.ground_ops); self._set_message(f"Selected airfield: {a.name if a else 'none'}.",3); return
            auth=authority_level(self.profile.rank_index)
            if key in ("a","j","y","s") and auth < 3:
                self._set_message("GROUND ORDER DENIED — division/team leadership authority is required. Junior personnel may observe and report.",5); return
            if key=="l" and auth < 4:
                self._set_message("AMPHIBIOUS ORDER DENIED — SHIP COMMAND WATCH authority is required for a landing evolution.",5); return
            if key=="a":
                ok,msg=accept_ground_mission(self.ground_ops); self._set_message(msg,5); return
            if key=="j":
                ok,msg=order_selected_unit_to_mission(self.ground_ops); self._set_message(msg,5); return
            if key=="y":
                ok,msg=order_selected_vehicle_to_mission(self.ground_ops); self._set_message(msg,5); return
            if key=="l":
                ok,msg=launch_amphibious_group(self.ground_ops); self._set_message(msg,6); return
            if key=="s":
                ok,msg=service_selected_airfield(self.ground_ops,self.campaign); self._set_message(msg,5); return
            return
        if self.overlay=="air_wing_console":
            if key in ("escape","e","k"):
                self.overlay=None; return
            if key=="tab":
                sq=cycle_squadron(self.air_wing); self._set_message(f"Selected {sq.key}: {sq.name}.",3); return
            if key=="m":
                mt=cycle_mission_type(self.air_wing); self._set_message(f"Air mission type: {mt}.",3); return
            if key in ("bracketleft","minus"):
                n=adjust_sortie_size(self.air_wing,-1); self._set_message(f"Planned sortie size: {n} aircraft.",3); return
            if key in ("bracketright","plus","equal"):
                n=adjust_sortie_size(self.air_wing,1); self._set_message(f"Planned sortie size: {n} aircraft.",3); return
            if key=="p":
                ok,msg=plan_selected_mission(self.air_wing,self.physics.east_nm,self.physics.north_nm,self.physics.heading_deg); self._set_message(msg,5); return
            if key=="l":
                deck_safe=not self.survivability.sunk and operational_factors(self.survivability)["aviation"]>35
                ok,msg=launch_selected_mission(self.air_wing,self.shipboard.enterprise.wind_over_deck,self.physics.speed_knots,deck_safe); self._set_message(msg,5); return
            if key=="r":
                deck_safe=not self.survivability.sunk and operational_factors(self.survivability)["aviation"]>35
                ok,msg=recover_selected_mission(self.air_wing,self.shipboard.enterprise.wind_over_deck,deck_safe); self._set_message(msg,5); return
            if key=="s":
                ok,msg=service_selected_squadron(self.air_wing); self._set_message(msg,5); return
            return
        if self.overlay=="navigation":
            if key in ("escape","e","n"): self.overlay=None
            elif key in ("bracketleft","minus"):
                self.physics.sea_state=max(0,self.physics.sea_state-1); self._set_message(f"Training sea state set to {self.physics.sea_state}.",3)
            elif key in ("bracketright","plus","equal"):
                self.physics.sea_state=min(9,self.physics.sea_state+1); self._set_message(f"Training sea state set to {self.physics.sea_state}.",3)
            return
        if self.overlay=="welcome_open":
            if key in ("escape","e","return","space"): self.overlay=None
            return
        if self.overlay=="help_open":
            if key in ("escape","e"): self.overlay=None
            return
        if self.overlay=="workboard":
            if key in ("escape","e"): self.overlay=None
            return
        if self.overlay=="pause_open":
            if key in ("escape","e"): self.overlay=None
            elif key=="s": save_profile(self.profile); self._set_message("Career saved.",3); self.overlay=None
            elif key=="q": self.on_close()
            return
        super()._overlay_key(key)

    def _render_overlay(self,w:int,h:int):
        if self.overlay in ("welcome_open","help_open","workboard","pause_open","helm_physics","engine_physics","navigation","combat_plot","weapons_control","air_combat","magazine_combat","survivability_dc","survivability_boundaries","survivability_medical","command_console","fleet_console","fleet_signal","fleet_logistics","campaign_console","campaign_logistics","ground_console","ground_combat_console","ground_combat_help","ground_combat_debrief","air_wing_console","flight_help","pilot_survival","ground_vehicle_help","land_command","land_vehicle_help","strategic_command","economy_console","logistics_console"):
            c=self.canvas; x1,y1,x2,y2=int(w*.12),int(h*.10),int(w*.88),int(h*.88)
            c.create_rectangle(x1,y1,x2,y2,fill="#080d14",outline="#7d62a8",width=2)
            title={"welcome_open":"WAR SIMULATOR v2.7 — ENTERPRISE 1942 RECONSTRUCTION","help_open":"OPEN WORLD / JOINT OPERATIONS HELP","workboard":"MAINTENANCE & DUTY WORK BOARD","pause_open":"PAUSED","helm_physics":"HELM — LIVE SHIP CONTROL","engine_physics":"ENGINE ORDER TELEGRAPH","navigation":"NAVIGATION / VESSEL MOTION BOARD","combat_plot":"CIC / RADAR — TACTICAL COMBAT PLOT","weapons_control":"FIRE CONTROL — WEAPONS DIRECTOR","air_combat":"AVIATION OPERATIONS — COMBAT AIR CYCLE","magazine_combat":"MAGAZINE / ORDNANCE CONTROL","survivability_dc":"DAMAGE CONTROL CENTRAL — STRUCTURAL SURVIVABILITY","survivability_boundaries":"WATERTIGHT BOUNDARY CONTROL","survivability_medical":"SICKBAY — MASS CASUALTY RECEIVING","command_console":"BRIDGE COMMAND DESK — CHAIN OF COMMAND","fleet_console":"TASK FORCE TACTICAL PLOT","fleet_signal":"SIGNAL BRIDGE / FLEET COMMUNICATIONS","fleet_logistics":"FLEET LOGISTICS & REPLENISHMENT","campaign_console":"OPERATIONAL CAMPAIGN PLANNING PLOT","campaign_logistics":"BASE / CONVOY LOGISTICS NETWORK","ground_console":"EXPEDITIONARY OPERATIONS — GROUND / AIRFIELD / AMPHIBIOUS","ground_combat_console":"COMBINED-ARMS FIRETEAM COMMAND / STATUS","ground_combat_help":"FIRST-PERSON INFANTRY CONTROLS","ground_combat_debrief":"COMBINED-ARMS FIELD EXERCISE DEBRIEF","ground_vehicle_help":"GROUND VEHICLE — MOTOR POOL TRAINING","air_wing_console":"AIR GROUP OPERATIONS — SQUADRONS / FLIGHT PLANNING","flight_help":"FIRST-PERSON AIR COMBAT — COCKPIT CONTROLS","pilot_survival":"PILOT DOWN — SEARCH & RESCUE","land_command":"BATTALION TACTICAL COMMAND — LARGE-SCALE LAND WARFARE","land_vehicle_help":"ARMORED / BATTLEFIELD VEHICLE DIRECT CONTROL","strategic_command":"THEATER STRATEGIC COMMAND — PERSISTENT FRONT LINE","economy_console":"NATIONAL WAR PRODUCTION / INDUSTRIAL COMMAND","logistics_console":"STRATEGIC MOBILITY / GLOBAL LOGISTICS COMMAND"}[self.overlay]
            c.create_text(x1+26,y1+28,text=title,fill="#d6c3ff",font=("Segoe UI Semibold",17),anchor="w")
            lines=[]
            if self.overlay=="welcome_open": lines=[
                "v2.4 adds a persistent strategic mobility network above the national war economy: rail, road, port and sea shipments must physically move produced cargo before fleets, airfields and front-line depots receive it.",
                "There are no normal room/deck scene changes. Walk through doors and passageways; use physical ladders to change elevation while the same renderer/state continues.",
                "The persistent Air Group now tracks individual aircraft and aircrew, squadron readiness, flight planning, spotting, launch, airborne missions, scouting reports, recovery and maintenance.",
                "WASD move (D is always strafe-right on foot) • Shift sprint • E interact/climb • F objective • F8 battalion • F10 strategic command • F12 war economy • F5 strategic logistics • G ground/infantry • K air wing • F6 damage control • N navigation • V task force • O campaign.",
                "Enterprise geometry remains a training schematic, not an exact 1942 deck plan. Historical events stay in the sourced historical layer.",
                "Press E / Enter / Space to begin.",
            ]
            elif self.overlay=="help_open": lines=[
                "NORMAL TRAVEL: walk from the training base east along the pier and directly through the gangway into Enterprise's Hangar Deck.",
                "VERTICAL TRAVEL: approach a ladder and press E. Your z-position moves continuously; there is no world reload.",
                "DAILY LIFE: eat in the mess, sleep in berthing, use sickbay, complete work orders, qualify at stations, and stand assigned historical duties.",
                "TIME: R advances ship routine and the Midway duty clock. The campaign plot can apply safe open-ocean navigation compression; combat/casualty/collision states force 1×.",
                "F shows the most important current objective and whether it is above/below you.",
                "SHIP HANDLING: use the physical Helm and Engine Telegraph on the Bridge; use the Hangar sea-detail station to cast off/moor and the Flight Deck forecastle control for anchor operations.",
                "Once cast off, the gangway disconnects and shore geometry no longer renders from the vessel frame. Return to the berth at low speed to reconnect it.",
                "F9 is emergency shore relocation only while moored; N opens the live navigation/motion board. D no longer opens any panel during normal movement; Damage Control is F6.",
                "AIR GROUP: physically use the Island Air Group Operations Room or Hangar Squadron Ready Room, or press K. Plan missions, launch, recover and service individual aircraft.",
                "COMMAND: physically use the Bridge command desk or press C. Orders are rank-gated and flow to autonomous departments rather than instantly completing.",
                "TASK FORCE: use the physical Bridge Task Force Plot / Signal Bridge / Fleet Logistics board or press V. Friendly ships have independent positions, fuel, damage, sensors, formation slots and collision-avoidance AI.",
                "CAMPAIGN: use the physical Bridge Operational Campaign Plot / Hangar Base-Convoy Logistics Board or press O. Missions, bases, supply convoys and repair-yard operations persist in the same sea coordinate system.",
                "GROUND / EXPEDITIONARY: walk south on the training base into the expeditionary district or press G. Ground units, airfields, vehicles, amphibious forces and logistics persist in the campaign coordinates.",
                "COMBINED ARMS v2.0: continue farther south to Infantry Armory / Fireteam Command / Field Aid / Training Village. During a live exercise use LMB/Space fire, RMB aim, R reload, C stance, T target, J squad order, H aid, 5 air support, 6 naval support.",
                "LAND WARFARE v2.1: continue south beyond the training village to Battalion Command, Armored Staging, Artillery FDC, Field Hospital and the maneuver sectors. F8 opens the battlefield board; orders remain rank-gated.",
                "STRATEGIC WAR v2.2: continue south beyond the battalion maneuver area to Theater Command, Intelligence and Theater Logistics. F10 opens the front-line board; strategic orders remain rank-gated and tactical battalion victories feed the selected strategic sector.",
                "WAR ECONOMY v2.3: continue farther south into the industrial district. F12 opens National War Production; factories consume raw reserves, training creates replacements, and allocations replenish theater, fleet, air, land and base stocks.",
                "STRATEGIC LOGISTICS v2.4: continue beyond the industrial district into Strategic Mobility Command. F5 opens the logistics board; dispatches reserve real stock, occupy damaged rail/road/sea routes, can be interdicted, and only replenish recipients after arrival.",
                "MOTOR POOL: approach the utility vehicle and press E. I starts engine, W/S changes throttle, A/D steer, B brake, E exit. D remains right-steer only while driving and right-strafe on foot.",
                "Fleet-changing orders require SHIP COMMAND WATCH authority; junior personnel can still observe the tactical picture and report through the chain of command.",
                "COMBAT: B opens the tactical plot. Physical CIC/Radar updates contacts; AA Director/Track Board controls weapons; Flight Control manages CAP/strike sorties; Ordnance handles ammunition hoists.",
                "T training raids are explicitly SIMULATED and do not alter the locked Midway historical timeline. F6 opens structural Damage Control; D remains normal right-strafe outside cockpit flight.",
            ]
            elif self.overlay=="economy_console":
                fac=self.war_economy.selected_facility; order=self.war_economy.selected_order; research=self.war_economy.selected_research; training=self.war_economy.selected_training
                active_orders=[x for x in self.war_economy.orders.values() if x.status in ("ACTIVE","MATERIAL HOLD")]
                lines=[
                    economy_summary(self.war_economy),
                    f"PLAYER AUTHORITY: {authority_label(self.profile.rank_index)} • allocation destination {self.war_economy.selected_allocation} • selected facility {fac.name if fac else 'NONE'}",
                    f"RAW RESERVES: STEEL {self.war_economy.reserves.get('STEEL',0):.0f} • ALUMINUM {self.war_economy.reserves.get('ALUMINUM',0):.0f} • OIL {self.war_economy.reserves.get('OIL',0):.0f} • EXPLOSIVES {self.war_economy.reserves.get('EXPLOSIVES',0):.0f} • FOOD {self.war_economy.reserves.get('FOOD',0):.0f}",
                    "--- NATIONAL STOCKPILES ---", *economy_stockpile_lines(self.war_economy),
                    "--- INDUSTRIAL FACILITIES ---", *economy_facility_lines(self.war_economy),
                    "--- SELECTED / ACTIVE PRODUCTION ---",
                    f"> {order.title if order else 'NONE'} • {order.status if order else ''} • {order.produced if order else 0:.0f}/{order.target_quantity if order else 0:.0f}",
                    *[f"  ACTIVE {o.key}: {o.title} {o.produced:.0f}/{o.target_quantity:.0f}" for o in active_orders[:4]],
                    f"RESEARCH: {research.title if research else 'NONE'} • {research.status if research else ''} • {research.progress if research else 0:.0f}%",
                    f"TRAINING: {training.title if training else 'NONE'} • {training.status if training else ''} • graduates {training.graduates if training else 0}",
                    f"TRANSPORT: rail damage {self.war_economy.network.rail_damage:.0f}% • road {self.war_economy.network.road_damage:.0f}% • port {self.war_economy.network.port_damage:.0f}% • throughput {self.war_economy.network.throughput:.0f}%",
                    "TAB facility • O production order • R research • T training • D allocation destination",
                    "S start war economy • P activate production • I start research • G start/pause training • F repair facility • X repair transport • A emergency/direct allocation (disabled after F5 logistics activation) • F12/E/Esc close",
                    "National facility names, rates, stock quantities and research/training timings are training abstractions, not historical production statistics.",
                ]
            elif self.overlay=="logistics_console":
                route=self.logistics_network.selected_route; hub=self.logistics_network.selected_hub; pkg=self.logistics_network.selected_package; ship=self.logistics_network.selected_shipment
                lines=[
                    logistics_summary(self.logistics_network),
                    f"PLAYER AUTHORITY: {authority_label(self.profile.rank_index)} • shipment priority {self.logistics_network.priority} • network {'ACTIVE' if self.logistics_network.active else 'STANDBY'}",
                    f"SELECTED ROUTE: {route.name if route else 'NONE'} • mode {route.mode if route else ''} • effective cap {route.effective_capacity if route else 0:.0f}% • damage {route.damage if route else 0:.0f}% • interdiction {route.interdiction if route else 0:.0f}%",
                    f"SELECTED HUB: {hub.name if hub else 'NONE'} • recipient {hub.recipient if hub else ''} • capacity {hub.effective_capacity if hub else 0:.0f}% • damage {hub.damage if hub else 0:.0f}%",
                    f"HUB STAGED INVENTORY: {', '.join(f'{k.replace(chr(95), chr(32))} {v:.0f}' for k,v in (hub.inventory.items() if hub else []) if v > 0.01) or 'EMPTY'}",
                    f"SELECTED CARGO: {pkg.title if pkg else 'NONE'} • SELECTED SHIPMENT: {ship.key if ship else 'NONE'} {ship.status if ship else ''}",
                    "--- TRANSPORT ROUTES ---", *logistics_route_lines(self.logistics_network),
                    "--- RECENT / ACTIVE SHIPMENTS ---", *logistics_shipment_lines(self.logistics_network),
                    "--- CARGO PACKAGES ---", *logistics_package_lines(self.logistics_network),
                    "TAB route • H hub • P cargo package • N shipment • G priority",
                    "S activate network • A dispatch cargo • C assign/release escort • I issue final-hub inventory • X repair route • F repair hub • F5/E/Esc close",
                    "MULTI-LEG RULE: cargo dispatches only from the selected route origin. Transit-hub cargo must be moved on a downstream route; final-hub cargo must be issued with I before an operational recipient receives it.",
                    "When this network is active, direct F12 economy allocations are disabled: national stock must physically traverse this transport layer before the recipient receives it.",
                    "Hub/route names, cargo quantities, speeds, distances and interdiction behavior are training abstractions, not historical logistics statistics.",
                ]
            elif self.overlay=="workboard": lines=[f"Ship routine score: {self.life.routine_score:.0f}%",*workboard_lines(self.life),"Complete each order at its physical shipboard maintenance station."]
            elif self.overlay=="helm_physics": lines=[
                physics_summary(self.physics),
                "LEFT / RIGHT — move rudder in 5° increments • C / 0 — rudder amidships",
                f"Steering integrity {self.physics.steering_integrity:.0f}% • yaw rate {self.physics.yaw_rate_deg_s:+.3f}°/s • turning radius {self.physics.turning_radius_nm:.2f} nm",
                "Rudder authority grows with speed; at very low speed a carrier will not answer the helm quickly.",
                "E / Esc — leave helm control",
            ]
            elif self.overlay=="engine_physics": lines=[
                physics_summary(self.physics),
                "0 STOP • 1 DEAD SLOW • 2 ONE-THIRD • 3 TWO-THIRDS • 4 FULL AHEAD • B BACKING",
                f"Propulsion integrity {self.physics.propulsion_integrity:.0f}% • current speed {self.physics.speed_knots:.1f} kt",
                "Acceleration/deceleration are inertial; the ship does not instantly match an engine order.",
                "E / Esc — leave telegraph control",
            ]
            elif self.overlay=="combat_plot": lines=[
                combat_summary(self.combat),
                *track_table_lines(self.combat),
                "TAB next contact • A acquire/update • S fire-control solution • G General Quarters • T start explicitly SIMULATED raid • B/E/Esc close",
                "Historical Midway data stays locked; T creates a training raid only and is not a historical attack claim.",
            ]
            elif self.overlay=="weapons_control": lines=[
                combat_summary(self.combat),
                f"Score {combat_score(self.combat):.1f}% • enemy defeated {self.combat.enemy_destroyed} • hits taken {self.combat.hits_taken} • rounds fired {self.combat.rounds_fired}",
                "1 5-inch DP • 2 Medium AA • 3 Light AA • TAB next target • A track update • S solution • SPACE/F fire",
                "G General Quarters • T start SIMULATED raid • E/Esc leave director",
                "Weapon ranges/effectiveness and ammunition quantities are gameplay training calibration, not archival CV-6 firing-trial data.",
            ]
            elif self.overlay=="air_combat": lines=[
                combat_summary(self.combat),
                f"Aviation fuel {self.combat.air.aviation_fuel_units:.0f} • fighter ammo {self.combat.air.fighter_ammo_units:.0f} • bombs {self.combat.air.bomb_units} • torpedoes {self.combat.air.torpedo_units}",
                f"CAP {'AIRBORNE' if self.combat.air.cap_airborne else 'NOT AIRBORNE'} • CAP kills {self.combat.air.cap_kills} • strike sorties {self.combat.air.strike_sorties} • recoveries {self.combat.air.recovery_cycles}",
                "C launch prepared F4F CAP • R recover CAP when defensive ring is clear • S launch prepared training strike • G General Quarters",
                "Aircraft must still be physically fueled, armed, moved by elevator and spotted before launch.",
            ]
            elif self.overlay=="magazine_combat": lines=[
                *ammunition_lines(self.combat),
                "H cycle ammunition hoists / replenish ready-service ammunition • G General Quarters • E/Esc close",
                "Combat stores are finite during the session; carrier-air sorties also consume aviation fuel and ordnance units.",
            ]
            elif self.overlay=="survivability_dc": lines=[
                casualty_summary(self.survivability),
                f"SELECTED: {selected_compartment(self.survivability).name}",
                *compartment_lines(self.survivability),
                "TAB next compartment • F firefight • P dewater • H patch breach • S shore structure • V ventilation • A abandon ship",
                "T injects an explicitly SIMULATED severe torpedo casualty for damage-control training • E/Esc close",
            ]
            elif self.overlay=="survivability_boundaries": lines=[
                casualty_summary(self.survivability),
                f"BOUNDARY FOCUS: {selected_compartment(self.survivability).name}",
                *[f"{b.key}: {self.survivability.compartments[b.a].name} ↔ {self.survivability.compartments[b.b].name} • {'OPEN' if b.open else 'SHUT'} • integrity {b.integrity:.0f}%" for b in self.survivability.boundaries.values()],
                "TAB next casualty compartment • B/Space operate adjacent watertight boundary • E/Esc close",
            ]
            elif self.overlay=="survivability_medical": lines=[
                casualty_summary(self.survivability),
                f"Medical load {self.survivability.medical_load_pct:.0f}% • treated {self.survivability.casualties_treated} • evacuation {self.survivability.evacuation_progress_pct:.0f}%",
                *[f"{c.name}: {c.wounded} wounded / {c.dead} dead" for c in self.survivability.compartments.values() if c.wounded or c.dead],
                "T / M / Space — treat casualties • E/Esc close",
            ]
            elif self.overlay=="command_console": lines=[
                command_summary(self.command,self.profile.rank_index),
                f"PLAYER: {self.profile.rank} • command authority {authority_label(self.profile.rank_index)} • selected {self.command.selected_department.name}",
                f"Department head: {self.command.selected_department.officer} — {self.command.selected_department.billet}",
                *department_lines(self.command),
                "--- ACTIVE / RECENT ORDERS ---",
                *order_lines(self.command,8),
                "--- LOGISTICS ---",
                *supply_lines(self.command),
                "TAB department • 0 report through chain • 1 repair • 2 watertight • 3 medical • 4 engineering • 5 air defense • 6 air ops",
                "G General Quarters • M muster • S replenish stores • X stand down • C/E/Esc close",
                "Orders are constrained by earned rank; NPC departments execute gradually according to readiness, fatigue, manpower and supplies.",
            ]
            elif self.overlay in ("fleet_console","fleet_signal","fleet_logistics"):
                sel=self.task_force.selected_friendly
                con=self.task_force.selected_contact
                lines=[
                    task_force_summary(self.task_force,self.physics),
                    f"PLAYER AUTHORITY: {authority_label(self.profile.rank_index)} • formation {self.task_force.formation} • signaling {self.task_force.signal_method}",
                    f"SELECTED FRIENDLY: {sel.name if sel else 'NONE'} • SELECTED CONTACT: {con.label if con else 'NONE'}",
                    "--- FRIENDLY TASK FORCE ---",
                    *friendly_lines(self.task_force,self.physics.east_nm,self.physics.north_nm),
                    "--- CONTACTS ---",
                    *contact_lines(self.task_force,self.physics.east_nm,self.physics.north_nm),
                    "--- LOGISTICS ---",
                    *logistics_lines(self.task_force),
                    "TAB next friendly • C next contact • R radio silence / tactical radio",
                    "1 carrier screen • 2 column • 3 dispersed • 4 ASW screen • Q resume station • W screen ahead • X screen astern • D detach",
                    "T start explicitly SIMULATED surface/submarine problem • A order escort engagement • P replenishment rendezvous • V/E/Esc close",
                    "TF16 ship names are sourced from the Midway manifest. Formation spacing, AI captains, sensor ranges, logistics quantities and training enemies are simulation abstractions.",
                ]
            elif self.overlay in ("campaign_console","campaign_logistics"): lines=[
                campaign_summary(self.campaign,self.physics),
                f"PLAYER AUTHORITY: {authority_label(self.profile.rank_index)} • selected base {self.campaign.selected_base.key if self.campaign.selected_base else 'NONE'} • selected convoy {self.campaign.selected_convoy.name if self.campaign.selected_convoy else 'NONE'}",
                "--- BASE NETWORK (TRAINING GEOGRAPHY) ---",
                *base_lines(self.campaign,self.physics.east_nm,self.physics.north_nm),
                "--- SUPPLY CONVOYS ---",
                *convoy_lines(self.campaign,self.physics.east_nm,self.physics.north_nm),
                "--- OPERATIONS ORDERS ---",
                *mission_lines(self.campaign),
                "TAB mission • B base • C convoy • F friendly ship • A accept mission • S port service • R send selected damaged escort to repair yard",
                "1 normal time • 2 5× • 3 15× • 4 30× operational navigation compression • O/E/Esc close",
                "Time compression automatically falls to 1× during combat, serious casualty or collision alarm. Bases, exact positions, stock quantities, schedules and missions are training abstractions.",
            ]
            elif self.overlay=="strategic_command": lines=[
                strategic_summary(self.strategic_war),
                f"PLAYER AUTHORITY: {authority_label(self.profile.rank_index)} • front shifts {self.strategic_war.front_shifts} • recon reports {self.strategic_war.recon_reports} • supply deliveries {self.strategic_war.supply_deliveries}",
                "--- FRONT-LINE SECTORS ---",
                *strategic_sector_lines(self.strategic_war),
                "--- FRIENDLY FORMATIONS ---",
                *strategic_formation_lines(self.strategic_war),
                "--- DEPOTS / ROUTES ---",
                *strategic_depot_lines(self.strategic_war),
                *strategic_route_lines(self.strategic_war),
                "--- OPERATIONS ---",
                *strategic_operation_lines(self.strategic_war),
                "TAB formation • B sector • D depot • O operation • S start campaign • A accept operation",
                "1 reserve • 2 defend • 3 attack • 4 recon formation • 5 withdraw • 6 resupply • R reconnaissance report",
                "I artillery network • Q air interdiction • N coastal naval fire • P reinforce/resupply formation • X repair selected bridge route • F10/E/Esc close",
                "Exact force sizes, commanders, sector geometry, routes, reinforcement timing and combat coefficients are TRAINING abstractions, not historical claims.",
            ]
            elif self.overlay=="land_command": lines=[
                warfare_summary(self.land_warfare),
                f"PLAYER AUTHORITY: {authority_label(self.profile.rank_index)} • command points {self.land_warfare.command_points:.0f} • phase {self.land_warfare.phase}",
                "--- BATTALION UNITS ---",
                *land_unit_lines(self.land_warfare),
                "--- ARMORED / SUPPORT VEHICLES ---",
                *land_vehicle_lines(self.land_warfare),
                "--- BATTLEFIELD SECTORS ---",
                *land_sector_lines(self.land_warfare),
                "--- CONTACTS ---",
                *land_contact_lines(self.land_warfare),
                "--- LOGISTICS / CASEVAC ---",
                *land_logistics_lines(self.land_warfare),
                "TAB unit • V vehicle • B sector • T contact • O begin operation • 1 hold • 2 advance • 3 suppress • 4 assault • 5 dig in • 6 withdraw",
                "R resupply selected unit • M CASEVAC • A artillery • Q joint air support • N naval gunfire • F8/E/Esc close",
                "Force strengths, vehicle performance, artillery effects, sector geometry and training opposition are gameplay abstractions—not claims about a specific historical battle.",
            ]
            elif self.overlay=="land_vehicle_help": lines=[
                warfare_summary(self.land_warfare),
                "I engine start/secure • W/S throttle • A/D steer • B brake • SPACE vehicle weapon • T cycle battlefield target • E dismount when stopped",
                "D is steering-right only while driving; it does not open Damage Control or any tactical panel.",
                "Vehicle armor, speed, ammunition and weapon effects are training calibration.",
                "E / Esc closes help while stopped.",
            ]
            elif self.overlay=="ground_combat_console": lines=[
                ground_combat_summary(self.ground_combat),
                f"PLAYER: health {self.ground_combat.player.health:.0f}% • stamina {self.ground_combat.player.stamina:.0f}% • suppression {self.ground_combat.player.suppression:.0f}% • stance {self.ground_combat.player.stance}",
                "--- FIRETEAM ---",
                *infantry_squad_lines(self.ground_combat),
                "--- CONTACTS / INTELLIGENCE ---",
                *infantry_contact_lines(self.ground_combat),
                "--- OBJECTIVES ---",
                *infantry_objective_lines(self.ground_combat),
                "TAB target • 1/2/3 weapon • C stance • J cycle fireteam order • H self aid • M treat squad casualty • 5 air support • 6 naval support",
                "X stand down • G/E/Esc close. Weapon/support coefficients and opposing-force behavior are training abstractions.",
            ]
            elif self.overlay=="ground_combat_help": lines=[
                ground_combat_summary(self.ground_combat),
                "FIRST-PERSON COMBINED-ARMS CONTROLS",
                "WASD move • Shift sprint • C standing/crouched/prone • Left mouse or Space fire • Right mouse aim • R reload",
                "1 Service Rifle • 2 Automatic Rifle • 3 Sidearm • T cycle detected target • J cycle fireteam order",
                "H self aid • M corpsman treats a wounded fireteam member • 5 request carrier-air support • 6 request simulated naval fire support",
                "F objective/navigation • G combat status • E interact • X stand down • Esc/E/H close help",
                "Contacts begin hidden and gain confidence through observation/proximity. Cover, range, stance, suppression, fatigue/ammunition and squad orders affect the exercise.",
                "All weapon effects, unit names, training contacts, support effects and range geometry are gameplay/training abstractions.",
            ]
            elif self.overlay=="ground_combat_debrief": lines=[
                "COMBINED-ARMS FIELD EXERCISE DEBRIEF",
                ground_combat_summary(self.ground_combat),
                f"Enemies neutralized {self.ground_combat.enemies_neutralized} • squad wounded {self.ground_combat.squad_wounded} • supports {self.ground_combat.supports_called} • casualties treated {self.ground_combat.casualties_treated}",
                f"Shots {self.ground_combat.player.shots_fired} • hits {self.ground_combat.player.hits} • player damage taken {self.ground_combat.player.damage_taken:.0f}",
                *infantry_objective_lines(self.ground_combat),
                "A score of 75% or better awards the Combined-Arms Fireteam Practical qualification.",
                "E / Enter / Space / Esc — return to the seamless world.",
            ]
            elif self.overlay=="ground_console": lines=[
                ground_summary(self.ground_ops),
                f"PLAYER AUTHORITY: {authority_label(self.profile.rank_index)} • selected mission {self.ground_ops.selected_mission.title if self.ground_ops.selected_mission else 'NONE'}",
                "--- EXPEDITIONARY UNITS ---",
                *ground_unit_lines(self.ground_ops),
                "--- GROUND VEHICLES / LOGISTICS ---",
                *ground_vehicle_lines(self.ground_ops),
                "--- EXPEDITIONARY AIRFIELDS ---",
                *ground_airfield_lines(self.ground_ops),
                "--- GROUND OPERATIONS ORDERS ---",
                *ground_mission_lines(self.ground_ops),
                "TAB mission • C unit • V vehicle • B airfield • A accept • J dispatch unit • Y dispatch vehicle • L amphibious launch • S service selected airfield",
                "G/E/Esc close • major ground orders are rank-gated. Exact manpower, vehicles, airfield stocks, mission geometry and combat coefficients are training abstractions.",
            ]
            elif self.overlay=="ground_vehicle_help": lines=[
                f"BASE UTILITY VEHICLE • engine {'RUNNING' if self.ground_ops.drive.engine_running else 'OFF'} • speed {self.ground_ops.drive.speed_mps*1.94384:.1f} kt-equivalent • fuel {self.ground_ops.drive.fuel_pct:.1f}% • distance {self.ground_ops.drive.distance_m:.0f} m",
                "I start/secure engine • W/S increase/decrease throttle • A/D steer • B brake • E exit when stopped",
                "This is a ground-handling training model inside the seamless shore base; vehicle coefficients are gameplay abstractions.",
                "Esc / E / H — close help",
            ]
            elif self.overlay=="pilot_survival": lines=[
                "EMERGENCY ESCAPE COMPLETE",
                self.flight_combat.last_event or "Survival beacon transmitting.",
                f"Search-and-rescue elapsed {self.flight_combat.rescue_seconds:.0f}s • {'RESCUED' if self.flight_combat.pilot_safe else 'RESCUE IN PROGRESS'}",
                "The training world continues running while friendly forces respond. Aircraft loss and pilot survival are persistent career events.",
            ]
            elif self.overlay=="air_wing_console": lines=[
                air_wing_summary(self.air_wing),
                f"SELECTED: {self.air_wing.selected_squadron} • mission {self.air_wing.selected_mission_type} • planned size {self.air_wing.selected_sortie_size} • deck cycle {self.air_wing.deck_cycle}",
                "--- SQUADRONS ---",
                *squadron_lines(self.air_wing),
                "--- SELECTED SQUADRON AIRCRAFT ---",
                *aircraft_lines(self.air_wing,10),
                "--- FLIGHT MISSIONS ---",
                *air_mission_lines(self.air_wing,8),
                "TAB squadron • M mission type • [ / ] sortie size • P plan • L launch • R recover • S service • K/E/Esc close",
                "Individual aircrew names, roster counts, sortie rates and stores are training abstractions; historical Midway events remain in the locked historical layer.",
            ]
            elif self.overlay=="flight_help": lines=[
                cockpit_summary(self.flight,self.physics.east_nm,self.physics.north_nm),
                "FIRST-PERSON TRAINING FLIGHT: approach a spotted individual aircraft on the Flight Deck and press E to enter the cockpit.",
                "I start/secure engine • W/S throttle • B wheel brakes • A/D bank • Up/Down pitch • Left/Right yaw",
                "G landing gear • F flaps • L attempt carrier recovery • E exit cockpit only after stopped on deck",
                "Takeoff requires engine running, brakes released, high throttle, sufficient airspeed and useful wind over deck.",
                "Recovery requires proximity to Enterprise, low altitude, gear/flaps down, safe deck, suitable speed, and broadly aligned heading.",
                "Flight coefficients are training calibration, not archival F4F/SBD/TBD flight-test performance data.",
                "Esc / E / H — close help",
            ]
            elif self.overlay=="navigation": lines=[
                physics_summary(self.physics),
                f"Navigation position: E {self.physics.east_nm:+.3f} nm / N {self.physics.north_nm:+.3f} nm • distance run {self.physics.distance_nm:.2f} nm",
                f"Wind FROM {self.physics.wind_from_deg:03.0f}° at {self.physics.wind_speed_knots:.0f} kt • Current TO {self.physics.current_to_deg:03.0f}° at {self.physics.current_speed_knots:.1f} kt",
                f"Sea state {self.physics.sea_state} • Roll {self.physics.roll_deg:+.1f}° • Pitch {self.physics.pitch_deg:+.1f}° • Heave {self.physics.heave_m:+.2f} m • balance load {self.physics.balance_load:.2f}",
                f"Depth under training chart: {training_depth_m(self.physics.east_nm,self.physics.north_nm):.1f} m • Draft {self.physics.draft_m:.1f} m • Hull {self.physics.hull_integrity:.1f}%",
                f"Status: {'GROUNDED' if self.physics.grounded else 'MOORED' if self.physics.moored else 'ANCHORED' if self.physics.anchor_deployed else 'UNDERWAY'} • Gangway {'CONNECTED' if self.physics.moored else 'DISCONNECTED'}",
                "[ / ] — decrease/increase training sea state • N / E / Esc — close",
                "Physics coefficients are gameplay training calibration; sourced historical events remain separate.",
            ]
            else: lines=["S — Save career","Q — Save and quit","Esc / E — Resume","The world clock is paused while this overlay is open."]
            yy=y1+78
            for line in lines:
                c.create_text(x1+28,yy,text=line,fill="#e2e8ee",font=("Segoe UI",10),anchor="nw",width=x2-x1-56)
                yy+=42 if len(line)>95 else 28
            return
        super()._render_overlay(w,h)

    def _sync_physics_profile(self):
        self.profile.ship_nav_east_nm = self.physics.east_nm
        self.profile.ship_nav_north_nm = self.physics.north_nm
        self.profile.ship_heading_deg = self.physics.heading_deg
        self.profile.ship_speed_knots = self.physics.speed_knots
        self.profile.ship_engine_order = self.physics.engine_order
        self.profile.ship_rudder_deg = self.physics.rudder_deg
        self.profile.ship_moored = self.physics.moored
        self.profile.ship_anchor_deployed = self.physics.anchor_deployed
        self.profile.ship_hull_integrity = self.physics.hull_integrity
        self.profile.ship_sea_state = self.physics.sea_state
        self.profile.player_world_x = self.x
        self.profile.player_world_y = self.y
        self.profile.player_world_z = self.z
        self.profile.player_world_yaw = self.yaw
        self.profile.player_world_pitch = self.pitch
        self.profile.ship_layout_version = 2
        self.profile.combat_snapshot = combat_to_dict(self.combat)
        self.profile.survivability_snapshot = survivability_to_dict(self.survivability)
        self.profile.command_snapshot = command_to_dict(self.command)
        self.profile.task_force_snapshot = task_force_to_dict(self.task_force)
        self.profile.campaign_snapshot = campaign_to_dict(self.campaign)
        self.profile.air_wing_snapshot = air_wing_to_dict(self.air_wing)
        self.profile.physical_world_snapshot = physical_world_to_dict(self.physical_world)
        self.profile.flight_ops_snapshot = flight_to_dict(self.flight)
        self.profile.flight_combat_snapshot = flight_combat_to_dict(self.flight_combat)
        self.profile.ground_ops_snapshot = ground_ops_to_dict(self.ground_ops)
        self.profile.ground_combat_snapshot = ground_combat_to_dict(self.ground_combat)
        self.profile.land_warfare_snapshot = land_warfare_to_dict(self.land_warfare)
        self.profile.strategic_war_snapshot = strategic_war_to_dict(self.strategic_war)
        self.profile.war_economy_snapshot = war_economy_to_dict(self.war_economy)
        self.profile.logistics_network_snapshot = logistics_network_to_dict(self.logistics_network)
        self.profile.ground_vehicle_distance_m = max(self.profile.ground_vehicle_distance_m, self.ground_ops.drive.distance_m)
        self.profile.land_warfare_best_score = max(self.profile.land_warfare_best_score, self.land_warfare.score if self.land_warfare.phase=="COMPLETE" else 0.0)
        self.profile.land_armored_kills = max(self.profile.land_armored_kills, self.land_warfare.armored_kills)
        self.profile.land_vehicle_distance_m = max(self.profile.land_vehicle_distance_m, sum(v.distance_m for v in self.land_warfare.vehicles.values()))
        self.profile.strategic_best_score = max(self.profile.strategic_best_score, self.strategic_war.strategic_score)
        self.profile.strategic_operations_completed = max(self.profile.strategic_operations_completed, self.strategic_war.operations_completed)
        self.profile.strategic_operations_failed = max(self.profile.strategic_operations_failed, self.strategic_war.operations_failed)
        self.profile.strategic_front_shifts = max(self.profile.strategic_front_shifts, self.strategic_war.front_shifts)
        self.profile.strategic_recon_reports = max(self.profile.strategic_recon_reports, self.strategic_war.recon_reports)
        self.profile.strategic_supply_deliveries = max(self.profile.strategic_supply_deliveries, self.strategic_war.supply_deliveries)
        self.profile.strategic_reinforcement_waves = max(self.profile.strategic_reinforcement_waves, self.strategic_war.reinforcement_waves)
        self.profile.strategic_bridges_repaired = max(self.profile.strategic_bridges_repaired, self.strategic_war.bridges_repaired)
        self.profile.economy_orders_completed = max(self.profile.economy_orders_completed, self.war_economy.orders_completed)
        self.profile.economy_allocations = max(self.profile.economy_allocations, self.war_economy.allocations)
        self.profile.economy_facilities_repaired = max(self.profile.economy_facilities_repaired, self.war_economy.facilities_repaired)
        self.profile.economy_research_completed = max(self.profile.economy_research_completed, self.war_economy.research_completed)
        self.profile.economy_personnel_graduated = max(self.profile.economy_personnel_graduated, self.war_economy.personnel_graduated)
        self.profile.economy_infrastructure_repairs = max(self.profile.economy_infrastructure_repairs, self.war_economy.infrastructure_repairs)
        self.profile.economy_best_score = max(self.profile.economy_best_score, self.war_economy.industrial_score)
        self.profile.logistics_shipments_delivered = max(self.profile.logistics_shipments_delivered, self.logistics_network.delivered_shipments)
        self.profile.logistics_shipments_lost = max(self.profile.logistics_shipments_lost, self.logistics_network.lost_shipments)
        self.profile.logistics_shipments_delayed = max(self.profile.logistics_shipments_delayed, self.logistics_network.delayed_shipments)
        self.profile.logistics_escorted_shipments = max(self.profile.logistics_escorted_shipments, self.logistics_network.escorted_shipments)
        self.profile.logistics_route_repairs = max(self.profile.logistics_route_repairs, self.logistics_network.route_repairs)
        self.profile.logistics_hub_repairs = max(self.profile.logistics_hub_repairs, self.logistics_network.hub_repairs)
        self.profile.logistics_hub_issues = max(self.profile.logistics_hub_issues, self.logistics_network.hub_issues)
        self.profile.logistics_cargo_delivered = max(self.profile.logistics_cargo_delivered, self.logistics_network.cargo_delivered)
        self.profile.logistics_best_score = max(self.profile.logistics_best_score, self.logistics_network.logistics_score)
        self.profile.ground_combat_best_score = max(self.profile.ground_combat_best_score, self.ground_combat.score if self.ground_combat.engagement_complete else 0.0)
        self.profile.ground_ops_best_score = max(self.profile.ground_ops_best_score, self.ground_ops.operational_score)
        self.profile.air_combat_sorties = max(self.profile.air_combat_sorties, self.flight_combat.mission_debriefs)
        self.profile.aerial_victories = max(self.profile.aerial_victories, self.flight_combat.aerial_victories)
        self.profile.air_to_surface_hits = max(self.profile.air_to_surface_hits, self.flight_combat.surface_hits)
        self.profile.pilot_bailouts = max(self.profile.pilot_bailouts, self.flight_combat.bailouts)
        self.profile.pilot_ditchings = max(self.profile.pilot_ditchings, self.flight_combat.ditchings)
        self.profile.pilot_rescues = max(self.profile.pilot_rescues, self.flight_combat.rescues)
        self.profile.cockpit_aircraft_losses = max(self.profile.cockpit_aircraft_losses, self.flight_combat.losses)
        self.profile.air_combat_best_score = max(self.profile.air_combat_best_score, self.flight_combat.score)
        self.profile.air_wing_aircraft_lost = max(self.profile.air_wing_aircraft_lost, self.air_wing.aircraft_lost)
        self.profile.air_wing_best_score = max(self.profile.air_wing_best_score, self.air_wing.operational_score)
        self.profile.campaign_missions_completed = max(self.profile.campaign_missions_completed, self.campaign.missions_completed)
        self.profile.campaign_convoy_deliveries = max(self.profile.campaign_convoy_deliveries, self.campaign.convoy_deliveries)
        self.profile.campaign_port_services = max(self.profile.campaign_port_services, self.campaign.port_services)
        self.profile.campaign_escort_repairs = max(self.profile.campaign_escort_repairs, self.campaign.escort_repairs)
        self.profile.campaign_best_score = max(self.profile.campaign_best_score, self.campaign.operational_score)
        self.profile.fleet_orders_issued = max(self.profile.fleet_orders_issued, self.task_force.formation_orders)
        self.profile.fleet_signals_sent = max(self.profile.fleet_signals_sent, self.task_force.signals_sent)
        self.profile.fleet_replenishments = max(self.profile.fleet_replenishments, self.task_force.logistics.replenishments)
        self.profile.fleet_collision_warnings = max(self.profile.fleet_collision_warnings, self.task_force.collision_warnings)
        self.profile.command_orders_issued = max(self.profile.command_orders_issued, self.command.orders_issued)
        self.profile.command_orders_completed = max(self.profile.command_orders_completed, self.command.orders_completed)
        self.profile.command_orders_failed = max(self.profile.command_orders_failed, self.command.orders_failed)
        self.profile.command_watch_reliefs = max(self.profile.command_watch_reliefs, self.command.watch_reliefs)
        self.profile.autonomous_crew_actions = max(self.profile.autonomous_crew_actions, self.command.autonomous_actions)
        self.profile.command_best_score = max(self.profile.command_best_score, self.command.command_score)

    def on_close(self):
        # Persist open-world/life progression and live ship navigation before base class save.
        self._sync_physics_profile()
        self.profile.open_world_minutes = getattr(self.profile,"open_world_minutes",0) + self.open_world_minutes
        self.profile.maintenance_completed = getattr(self.profile,"maintenance_completed",0) + self.life.maintenance_completed
        self.profile.meals_taken = getattr(self.profile,"meals_taken",0) + self.life.meals_eaten
        self.profile.sleep_periods = getattr(self.profile,"sleep_periods",0) + self.life.sleep_periods
        self.profile.life_routine_best = max(getattr(self.profile,"life_routine_best",0.0),self.life.routine_score)
        self.profile.seamanship_distance_nm = getattr(self.profile,"seamanship_distance_nm",0.0) + self.physics.distance_nm
        self.profile.underway_seconds = getattr(self.profile,"underway_seconds",0.0) + self.ship_motion_seconds
        self.profile.groundings = getattr(self.profile,"groundings",0) + (1 if self.physics.grounded else 0)
        if self.physics.distance_nm >= 0.5 and not self.physics.grounded:
            self.profile.qualifications["Basic Shiphandling Watch"] = True
        if self.command.orders_completed >= 5 and self.command.command_score >= 75 and self.profile.rank_index >= 4:
            self.profile.qualifications["Shipboard Chain of Command"] = True
        station_pct = 100.0 * sum(1 for v in self.task_force.friendly.values() if v.in_station) / max(1,len(self.task_force.friendly))
        self.profile.fleet_best_station_pct = max(self.profile.fleet_best_station_pct, station_pct)
        if station_pct >= 75 and self.task_force.formation_orders >= 2 and self.profile.rank_index >= 4:
            self.profile.qualifications["Task Force Formation Watch"] = True
        if self.campaign.missions_completed >= 2 and self.campaign.convoy_deliveries >= 1 and self.profile.rank_index >= 4:
            self.profile.qualifications["Naval Operational Planning Watch"] = True
        if self.land_warfare.operations_completed >= 1 and self.land_warfare.sectors_secured >= len(self.land_warfare.sectors) and self.profile.rank_index >= 3:
            self.profile.qualifications["Battalion Field Operations Practical"] = True
        if self.strategic_war.operations_completed >= 1 and self.strategic_war.recon_reports >= 1 and self.profile.rank_index >= 4:
            self.profile.qualifications["Theater Operational Planning Watch"] = True
        if self.war_economy.orders_completed >= 2 and (self.war_economy.allocations >= 1 or self.logistics_network.hub_issues >= 2) and self.profile.rank_index >= 14:
            self.profile.qualifications["National War Production Planning"] = True
        if self.logistics_network.hub_issues >= 2 and self.logistics_network.escorted_shipments >= 1 and self.profile.rank_index >= 4:
            self.profile.qualifications["Strategic Logistics & Mobility Watch"] = True
        super().on_close()


def run():
    SeamlessOpenWorld3DApp().mainloop()


if __name__=="__main__":
    run()
