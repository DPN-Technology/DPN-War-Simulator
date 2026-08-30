# War Simulator v2.4 — Strategic Mobility & Global Logistics

v2.4 closes the gap between national production and operational availability. Once Strategic Mobility is activated, cargo must move through a persistent multi-leg transport network, stage at hubs, and be formally issued from a final operational hub before a fleet, airfield, theater depot or land formation receives it.

## Core rule: produced ≠ moved ≠ staged ≠ issued
The v2.3 economy can manufacture and stockpile equipment, ammunition, fuel, repair stores and trained replacements. v2.4 adds the movement chain:

1. Production enters the national stockpile.
2. A first-leg shipment can draw national stock only from the National Distribution Depot.
3. The shipment physically advances over its selected route and can be delayed, damaged or lost.
4. Arrival places surviving cargo in the destination hub's staged inventory. Arrival does **not** automatically replenish a combat formation.
5. If the destination is a transit hub (Strategic Port Delta or Railhead Echo), a downstream route must be selected and dispatched. That next shipment consumes the transit hub's staged inventory rather than national stock.
6. If the destination is a final operational hub (Forward Depot Foxtrot, Air Logistics Hub Golf or Fleet Anchorage Hotel), the player must select that hub and press `I` to issue its staged inventory.
7. Only the final issue transfers cargo into the theater, airfield/Air Group or Task Force systems.

When the v2.4 network is active, the old direct F12 economy-allocation shortcut is intentionally disabled.

## Logistics hubs
- National Distribution Depot — national source
- Strategic Port Delta — transit / sea staging
- Railhead Echo — transit / land staging
- Forward Depot Foxtrot — final theater receiving depot
- Air Logistics Hub Golf — final aviation receiving hub
- Fleet Anchorage Hotel — final fleet receiving anchorage

Every hub tracks capacity, damage, security, congestion, staged inventory and shipment arrivals.

## Transport routes
Modes include RAIL, ROAD and SEA. Routes track distance, speed, capacity, physical damage, bridge integrity, interdiction pressure, escort requirement, completed shipments and losses.

The initial network includes National Depot → Railhead, Railhead → Forward Depot, Forward Depot → Air Logistics Hub, National Depot → Strategic Port, Strategic Port → Forward Depot, and Strategic Port → Fleet Anchorage.

A badly damaged bridge, route or destination hub can reduce effective capacity below the dispatch threshold and stop movement.

## Cargo packages
Initial training packages include Fuel Allocation, Ammunition Allocation, Repair / Medical Allocation, Replacement Personnel, Air Group Replacement Package, and Land Force Replacement Package.

Cargo quantities are training values, not historical statistics.

## Escort and interdiction
Sea shipments can be assigned an existing serviceable Task Force vessel as protection. Escort status substantially reduces sea interdiction exposure but does not make a convoy invulnerable. Unescorted high-risk shipments can be damaged or destroyed, and lost cargo never reaches the next hub.

## Operational issue integration
Final-hub issue can feed:
- friendly theater depots and v2.1 land artillery/logistics;
- expeditionary airfield fuel/ammunition/repair/medical stocks and Carrier Air Group support stocks;
- Task Force bunker fuel, aviation fuel, ammunition and repair stores.

## Physical world
The seamless base map continues south of the v2.3 industrial district into a strategic-mobility zone containing Strategic Mobility & Distribution Command, National Depot Dispatch, Port Convoy Control, Railhead Movement Control, Forward Receiving Depot, Air-Logistics Receiving Hub, Fleet-Anchorage Logistics Control, a heavy-road/twin-rail freight spine, freight stacks, crane/warehouse geometry, and moving shipment markers.

## Controls
Open physically at Strategic Mobility Command or press `F5`.

- `TAB` — cycle route
- `H` — cycle hub
- `P` — cycle cargo package
- `N` — cycle active/recent shipment
- `G` — cycle shipment priority
- `S` — activate logistics network
- `A` — dispatch selected cargo from the selected route origin
- `C` — assign/release escort
- `I` — issue staged inventory from a final operational hub
- `X` — repair selected route / bridge
- `F` — repair selected logistics hub
- `F5` / `E` / `Esc` — close

Operational logistics orders are rank-gated. Junior personnel can inspect routes, hubs, inventories and shipment status but cannot dispatch, escort, repair or issue strategic cargo.

## Historical separation
All v2.4 hub/route labels, distances, speeds, cargo quantities, capacities, security values and interdiction coefficients are SIMULATED / GAMEPLAY abstractions. Historical scenarios remain in the separate sourced historical layer.
