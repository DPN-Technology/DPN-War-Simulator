# War Simulator v2.2 — Persistent Front Lines & Strategic War Command

v2.2 adds a theater-level simulation above the existing v2.1 battalion battlefield. It is a training/gameplay abstraction layer, not a historical order-of-battle claim.

## Persistent theater state

The strategic layer tracks six front-line sectors, friendly and opposing formations, supply depots, roads/bridges, reinforcement waves, intelligence confidence, simultaneous operations, command points, victory value, and operational score.

Front-line sectors can change between FRIENDLY, CONTESTED, and ENEMY control. Formation strength, readiness, morale, supplies, ammunition, fuel, fortification, route capacity, bridge integrity, and intelligence all affect the operational situation.

## Physical Theater Command district

The existing seamless shore world now continues south beyond the battalion maneuver area into:

- Theater Strategic Command / Front Line Plot
- Theater Intelligence & Reconnaissance Center
- Theater Logistics / Reinforcement Control
- Persistent Front Line Maneuver Area

No new scene loads are used. These spaces are part of the same BASE coordinate system as the carrier pier, expeditionary base, training village, and battalion battlefield.

## Strategic command controls

Open the physical Theater Command board or press F10.

- TAB: cycle friendly formation
- B: cycle strategic sector
- D: cycle friendly depot while the board is open
- O: cycle operation
- S: start persistent strategic campaign
- A: accept selected operation
- 1: reserve
- 2: defend
- 3: attack
- 4: recon formation order
- 5: withdraw
- 6: resupply
- R: request reconnaissance report
- I: request artillery-network fire plan
- Q: request air interdiction
- N: request coastal naval fire support
- P: reinforce/resupply selected formation
- X: repair a damaged bridge route

Normal first-person D remains strafe-right. D is only a depot-cycle command while the strategic overlay is already open.

## Tactical-to-strategic link

A completed v2.1 battalion field operation feeds its result into the currently selected strategic sector. The tactical victory improves control, reduces opposing strength, and lowers fortification instead of existing as an isolated minigame.

## Logistics and infrastructure

Friendly depots have finite fuel, ammunition, medical supplies, replacements, repair stocks, and throughput. Formations consume supply as they move and fight. Road capacity, bridge integrity, and interdiction reduce supply flow. Engineer bridge repair consumes repair stocks.

## Reconnaissance

Strategic sectors have an intelligence-confidence value and report age. Reconnaissance raises confidence and provides a role-limited estimate of enemy strength, fortification, and supply. Intelligence decays over time.

## Enemy operational AI

The training opposing force can choose pressure sectors, move formations, interdict routes, and damage bridges. It does not have access to hidden player-only information; this is a deterministic training AI, not a historical commander recreation.

## Historical separation

The following are TRAINING / GAMEPLAY abstractions:

- sector names and geometry
- force sizes
- commander names
- reinforcement timing
- road/bridge capacities
- depot quantities
- combat coefficients
- strategic AI behavior
- operation deadlines

Historical scenarios remain in the separate sourced historical layer.
