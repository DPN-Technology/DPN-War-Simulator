# Historical Scenario Package Schema — v0.6 (cumulative)

Every new verified scenario should define:

- `scenario_id`
- `title`
- historical date/time window
- player branch / role / station
- Historical Lock or clearly labeled sandbox mode
- cited source register
- force/order-of-battle entries with per-entry source references
- environment/weather zones and source references
- canonical event list
- occurrence time
- report/receipt time when known or intentionally simulated
- audience / role visibility
- contact updates with confidence/uncertainty rather than omniscient truth
- mission/watch objectives
- doctrine profiles with separate knowledge states
- explicitly marked simulation abstractions
- career scoring/qualification hooks
- regression tests for timeline immutability and information boundaries

A new battle should remain catalog-only until this package is sufficiently populated and reviewed.


## Named-vessel station-duty extension

v0.4 adds `historical_data/enterprise_cv6_midway_station_duty.json` with:

- named ship identity and role;
- explicit historical-lock rules;
- Enterprise-specific source registry;
- station definitions;
- initial duty-task definitions;
- inherited canonical Midway event keys;
- explicit simulation-abstraction notes.

Named-vessel packages must state whether geometry, crew identities, system percentages, and casualty events are archival facts or simulation abstractions.


## v0.5 movement-layer manifest

`historical_data/enterprise_cv6_walkthrough_v05.json` adds a renderer-independent interaction manifest with:

- deck collision grids;
- named gameplay zones;
- station/equipment action IDs;
- qualification-step IDs;
- training aircraft-package definitions;
- an explicit geometry policy flag.

The walkthrough manifest does not redefine canonical historical events. It composes with the v0.3 Midway and v0.4 Enterprise station-duty packages.

`geometry_policy = TRAINING_SCHEMATIC_NOT_EXACT_DECK_PLAN` is mandatory for this v0.5 package so gameplay geometry cannot be mistaken for archival measurement.


## v0.6 walkthrough manifest
`enterprise_cv6_walkthrough_v06.json` extends the movement layer with `training_fault_policy = SIMULATED_INJECTS_NOT_HISTORICAL_CASUALTIES` while retaining `historical_lock = true` and the training-schematic geometry policy.

---

# v1.0 Combat Scenario Extension

Historical scenario packages can optionally attach a combat layer with:

- contact definitions (side, type, bearing, range, altitude, speed, course)
- confidence / identification rules
- weapon-battery availability and scenario-specific calibration
- ammunition / logistics state
- CAP and strike sortie resources
- attack thresholds and physical damage hooks
- historical-vs-training classification

Until a scenario supplies sourced combat data, the built-in raid is classified `SIMULATED_NON_HISTORICAL_INJECT` and must not be merged into canonical event timelines.

## v2.0 Combined-Arms Ground Exercise State

The live ground exercise is not a historical scenario record. It is persisted separately through `ground_combat_snapshot` with player state, weapon inventories, fireteam state, detected training contacts, objective progress, support usage and exercise score. Historical scenarios continue to use the existing locked historical-event/report model.

## v2.4 Strategic Logistics State
The v2.4 transport system is persisted separately through `logistics_network_snapshot` and is not a canonical historical event timeline. It stores:

- logistics hubs with capacity/damage/security/congestion/inventory;
- rail/road/sea routes with distance, speed, capacity, damage, bridge integrity and interdiction;
- cargo-package definitions;
- in-transit shipments with cargo, progress, health, escort, priority, delay and interdiction exposure;
- delivery/loss/repair statistics and event log.

Historical scenario packages can later replace training route values with sourced logistics data, but must explicitly distinguish archival facts from gameplay abstractions.
