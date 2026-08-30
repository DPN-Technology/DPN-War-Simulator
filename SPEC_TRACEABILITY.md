# War Simulator v2.0 — Master Design Traceability

## Source-derived direction

The Master Game Design states that War Simulator spans naval, land and air conflict across many eras; includes Army, Marine Corps, Air Force and other appropriate branches; requires earned qualifications/career progression; and ultimately targets persistent armies, fleets, air wings and logistics chains with players occupying coordinated roles.

It also states success is broader than kill count and should include mission accomplishment, survival, leadership, decision making, discipline, efficiency and professionalism.

## v2.0 implementation mapping

| Master-design direction | v2.0 implementation |
| --- | --- |
| Multiple military branches / land warfare | Expanded seamless shore world with infantry/fireteam operations |
| Teamwork / coordination | Four-person fireteam with explicit orders and autonomous response |
| Consequences | Health, wounds, suppression, finite ammo, casualties, failed exercise state |
| Leadership development | Fireteam order system and combined-arms support decisions |
| Qualification system | `Combined-Arms Fireteam Practical` earned through performance |
| Persistent world | Training village exists inside the existing continuous base world |
| Entire armies / air wings / fleets | Ground combat is tied to existing ground units, carrier Air Group and task force |
| Logistics | Ammunition finite; air support points and escort ammunition are consumed |
| Medical | Player self-aid, corpsman treatment and field-aid location |
| Mission accomplishment | Sequential checkpoint, village-security and accountability objectives |

## Explicit simulation abstractions

The following v2.0 data are not represented as historical facts:

- Training-village layout
- Fireteam names and exact composition
- Opposing-force names/positions
- Weapon magazine sizes/performance/effects
- Cover/suppression coefficients
- Casualty and medical coefficients
- Naval/air support effects
- Exact exercise timing

The locked Midway historical scenario remains separate.

## v2.2 Persistent Front Lines & Strategic War Command

- Persistent sector control and multiple operational formations extend the document's persistent-world / entire-armies concept.
- Theater depots, routes, bridges, reinforcements, finite supply flow and interdiction extend the document's fuel/ammunition/repairs/maintenance/supply-chain requirements.
- Reconnaissance confidence and decaying reports preserve the design principle that players should not receive perfect information.
- Tactical v2.1 battalion outcomes feed selected strategic sectors so mission performance has larger campaign consequences.
- The theater map, unit sizes, commanders and coefficients are explicitly training abstractions; locked historical scenario data remains separate.

## v2.3 National War Economy & Industrial Production
- Economy / fuel / ammunition / repairs / maintenance / supply chains / food / medical / replacement-personnel direction: implemented through persistent national reserves, finished stockpiles, facilities, production queues, research, training and transport throughput.
- National logistics influence prolonged conflict: strategic reinforcement waves can be delayed by shortages while v2.3 economy is active.
- Entire logistics chains: national output can be allocated into theater depots, naval forces, air wing, land forces and campaign bases.
- Historical separation: exact economy values and facility identities are training abstractions recorded in `historical_data/war_economy_v23.json`.

## v2.4 Strategic Mobility & Global Logistics
- Supply-chain direction: implemented as persistent multi-leg rail, road, port and sea transport between national stockpiles, transit hubs, final hubs and operational recipients.
- Logistics consequences: first-leg dispatch removes cargo from national inventory; later legs consume staged origin-hub inventory; arrivals stage cargo; only final-hub issue creates operational receipt. Delayed/damaged/lost shipments prevent or reduce eventual front-line receipt.
- Entire logistics chains: national production → national dispatch → transit hub → downstream dispatch → final hub → operational issue → theater/land/air/naval recipient is now an explicit simulation chain rather than an instant allocation.
- Fleet coordination: sea shipments can use existing Task Force vessels as escort assets.
- Infrastructure: route damage, bridge integrity, hub damage, congestion and repair capacity determine movement throughput.
- Persistent war: shipment state, route damage, hub damage, delivery history and losses persist in career saves.
- Historical separation: hub names, route distances/speeds, cargo sizes, security and interdiction coefficients are training abstractions recorded in `historical_data/logistics_v24.json`.

## v2.5 Enterprise Realism & Performance Rebuild

The master design requires fully simulated ships with meaningful Bridge, CIC, Engineering, medical, berthing, machinery, steering, ammunition, Damage Control, Hangar, Flight Deck and Radio spaces; it also requires hatches/systems to matter and physical damage/weather presentation.

v2.5 addresses the physical-world foundation underneath those systems:
- full carrier-scale coordinate envelope rather than the short proof-of-concept hull
- long, connected deck/hangar/engineering/lower-deck traversal
- three physical aircraft-elevator points
- relocated operational equipment and ship-life stations
- recognizable carrier exterior silhouette and starboard island
- physical hull/damage mapping across the full ship length
- near-plane clipping and merged surface rendering for stable close-quarters movement
- performance/quality controls so increasing ship detail does not require rendering every object at maximum range
- compact HUD so physical spaces remain visible during normal play

Historical-scale references are separated from procedural interior/visual approximations in `HISTORICAL_SOURCES.md` and `ENTERPRISE_REALISM_V25.md`.

## v2.6 Unreal/GPU visual migration

The master design requires a seamless, physical warship in which compartments, hatches, equipment and damage matter. v2.6 changes the rendering/asset foundation so those systems can eventually be presented with a modern GPU pipeline rather than the limited Tk Canvas renderer.

- Current simulation logic remains backward-compatible.
- A full-scale 1942 Enterprise GLB/OBJ becomes the external visual source asset.
- UE5 C++ project scaffolding provides first-person movement and the beginning of a save-state bridge.
- Historical visual cues are tracked separately from art reconstruction assumptions.

## v2.7 Enterprise realism / physical ship traceability
The master design requires a fully simulated ship with physically meaningful bridge, CIC, machinery, fire-control, steering, ammunition, damage-control, hangar, flight-deck and radio spaces, plus fire/smoke/flooding/equipment failures and realistic weather. v2.7 advances the visual/physical foundation by turning Enterprise into independently streamable exterior/interior modules and by adding UE watertight-door and compartment-state actors that can receive the existing simulation's flooding/fire/smoke/power state.

v2.7 does not claim the reconstruction-only interior modules are exact 1942 Enterprise deck plans. The architecture is deliberately modular so exact archival room reconstructions can replace provisional modules one at a time.
