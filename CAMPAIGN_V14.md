# War Simulator v1.4 — Persistent Naval Campaign, Bases & Logistics Network

## Purpose
v1.4 turns the v1.3 open-ocean task-force simulation into a persistent operational layer. Enterprise, escorts, supply traffic, bases, finite inventories, repair routing and missions share the same nautical coordinate system and remain alive while the player moves around the seamless first-person ship.

## Training-data policy
The v1.4 base names, exact coordinates, stock quantities, convoy schedules, operational mission geometry, interdiction zone, repair rates and time-compression rules are **TRAINING SIMULATION ABSTRACTIONS**. They are not presented as exact 1942 historical geography or logistics records. The locked Battle of Midway historical layer remains separate.

## Operational network
The training sea room contains four persistent support nodes:
- Naval Training Base — Home Port
- Forward Operating Base Able
- Fleet Fuel Anchorage Baker
- Fleet Repair Yard Charlie

Each base tracks finite fuel, aviation fuel, ammunition, repair stores, provisions and medical inventory plus its own repair capacity.

## Supply convoys
Two persistent logistics groups transit between support nodes. Convoys have their own position, speed, health, destination, cargo and escort state. Cargo is physically delivered when a convoy reaches its destination and replenishes that base's finite stock.

A deterministic training interdiction area makes escort protection matter. A convoy that remains in the threat area without Enterprise/task-force protection can accumulate damage and can eventually be lost.

## Missions
The campaign layer includes persistent operational orders such as:
- Patrol Sector Able
- Escort Supply Convoy A-1
- Forward Base Logistics Inspection
- Fleet Repair Yard Readiness Visit

Mission progress is based on Enterprise's actual nautical position and time on station. Missions are not completed by pressing a menu button.

## Repair-yard operations
Damaged task-force ships can be detached and routed to a repair-capable base. The ship must travel there, enter repair status, consume finite repair stores, restore hull/propulsion/steering/sensors over time, then return to formation.

## Port service
When Enterprise is inside a selected base's service radius and at 1 knot or less, the player can request port service. It transfers finite base inventory into task-force fuel/ammunition/repair stocks and can restore some ship structural condition.

## Operational time compression
Long-range transit can be run at 1×, 5×, 15× or 30× navigation compression. Player first-person movement remains normal. Ship/navigation/fleet/campaign movement advances faster only while the situation is safe.

Combat, serious structural casualty, or collision/grounding alarm automatically forces effective navigation time back to 1×.

## Physical first-person stations
- Operational Campaign Planning Plot — Bridge
- Base / Convoy Logistics Board — Hangar Deck

Shortcut: `O`

## Controls
Inside the campaign board:
- `TAB` — cycle mission
- `B` — cycle base
- `C` — cycle convoy
- `F` — cycle friendly task-force ship
- `A` — accept selected mission
- `S` — request selected-base port service
- `R` — dispatch selected damaged friendly to repair yard
- `1` — 1× navigation time
- `2` — 5× navigation time
- `3` — 15× navigation time
- `4` — 30× navigation time
- `O` / `E` / `Esc` — close

Mission acceptance, port-service orders and repair detachment require SHIP COMMAND WATCH authority. Junior players can still inspect the campaign picture.

## Persistence
The career save now retains:
- all base inventories
- convoy positions/health/destinations/deliveries
- active/completed mission state
- time-compression selection
- campaign hours
- operational score
- port services
- escort repairs
- campaign totals and qualifications
