# Historical / Simulation Data Packages

This directory contains auditable scenario, named-vessel, geometry-policy and simulation-layer manifests used by War Simulator.

- `midway_1942_manifest.json` — v0.3 Battle of Midway historical operations package.
- `enterprise_cv6_midway_station_duty.json` — v0.4 Enterprise station-duty layer tied to the Midway clock.
- `enterprise_cv6_walkthrough_v05.json` — v0.5 shipboard movement/training-schematic manifest.
- `enterprise_cv6_walkthrough_v06.json` — v0.6 equipment/hatch/fault policy extension.
- `first_person_3d_v07.json` — v0.7 first-person 3D policy/architecture manifest.
- `seamless_open_world_v08.json` — v0.8 continuous-world/living-ship manifest.
- `ship_physics_v09.json` — v0.9 vessel-physics training-calibration manifest.
- `naval_combat_v10.json` — v1.0 naval-combat / carrier-air-operations policy manifest.

The Enterprise geometry is **not** an exact 1942 deck plan. v1.0 combat training raids, weapon calibration values and resource pools are also explicitly separated from canonical Midway history. Historical scenarios can later replace training values with source-specific data without rewriting the career/open-world architecture.

### v1.2 command/crew manifest
`command_crew_v12.json` documents which command, crew, authority, manpower and logistics values are training abstractions so they remain separated from the locked historical Midway event layer.

- `task_force_v13.json` — v1.3 task-force/open-ocean feature manifest. Friendly TF16 names are linked to the sourced Midway manifest; formation, AI, logistics, sensors, and hostile training contacts are explicitly simulation abstractions.

- `campaign_v14.json` — v1.4 persistent naval-campaign feature manifest. Base geography, inventories, convoy schedules, repair rates, threat zones, missions and time compression are explicitly training abstractions; the locked Midway scenario remains separate.
- `air_wing_v15.json` — v1.5 air-wing source/training-abstraction manifest. VF-6/VB-6/VS-6/VT-6 labels and aircraft families are source-verified; exact roster counts, individual names, stores, rates and mission outcomes remain training abstractions.
- `physical_world_v16.json` — v1.6 environment/presentation manifest. Animated hatches, weather presets, effects, hull faceting and machinery animation remain training/presentation abstractions unless a historical scenario explicitly overrides them with sourced data.
- `flight_world_v17.json` — v1.7 first-person cockpit/animated-world source boundary. Historical identities are inherited; flight coefficients, cockpit geometry, crew gait, new door coordinates and fault visuals are training abstractions.


- `ground_ops_v19.json` — v1.9 expeditionary ground/airfield/amphibious training-data boundary and integration manifest.
- `ground_combat_v20.json` — v2.0 first-person combined-arms training boundary, explicitly separating gameplay weapon/contact/support values from locked historical scenarios.

## v2.2 strategic_war_v22.json
Persistent front-line / strategic-war gameplay manifest. All named sectors, formations, commanders, depots, routes, reinforcement timing and combat coefficients are training abstractions and do not modify locked historical scenario data.

## v2.3 war_economy_v23.json
Declares the national industry/production/research/training/transport layer as a training simulation abstraction. It is not a historical production-statistics dataset and does not modify locked Midway events.

## v2.4 logistics_v24.json
Declares the strategic-mobility / freight / convoy / rail / road layer as a training simulation abstraction. Hub and route identities, distances, transport speeds, cargo quantities, capacities, security and interdiction effects are not historical statistics and do not modify locked historical scenario data.


## v2.5 enterprise_realism_v25.json
Records the source-supported carrier scale reference points used by the Enterprise rebuild and explicitly separates them from procedural interior, collision, equipment and rendering geometry.

## v2.6 enterprise_1942_visual_v26.json
Visual reference boundary for the late-May/early-June 1942 Enterprise art target. It records source-driven dimensions/visible features separately from reconstruction-only mesh and texture decisions.


## v2.7 enterprise_1942_reconstruction_v27.json
Locks the visual target to Enterprise at Midway and separates official-photo / Yorktown-class-plan constraints from reconstruction-only hidden geometry. The v2.7 asset may be refined without promoting unsourced interior placement to historical fact.
