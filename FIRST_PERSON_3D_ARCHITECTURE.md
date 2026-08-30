# v0.7 First-Person 3D Architecture

## Renderer

`warsim/firstperson3d.py` contains the new primary runtime.

It provides:

- 3D camera position, yaw and pitch
- perspective projection
- near-plane rejection
- depth-sorted polygon faces
- 3D wall/floor/ceiling generation from collision maps
- axis-aligned 3D equipment geometry
- 3D hatches
- 3D crew bodies
- low-poly aircraft package representations
- 3D objective beacon
- diegetic terminal overlays

No external game engine or graphics dependency is required.

## Game-world modes

- HUB — fictional Naval Training & Career Center
- BRIDGE — 3D practical simulator
- DAMAGE — 3D damage-control trainer
- SYSTEMS — 3D full-ship casualty trainer
- ENTERPRISE — USS Enterprise training-schematic shipboard environment tied to Midway

## Separation of geometry and history

3D geometry and historical truth are separate layers.

The Enterprise geometry is not treated as primary historical evidence. The existing sourced event/intelligence/order-of-battle layer continues to own historical claims.

This makes it possible to replace schematic geometry with researched deck plans later without rewriting career, station, Midway, crew or qualification logic.

## v1.7 — First-person aircraft sub-runtime
v1.7 adds a cockpit state without launching a second application or replacing the persistent naval simulation. The carrier/task-force/campaign world continues to advance while the player's view/control context moves into an individually tracked aircraft. Flight position is maintained in the same global east/north nautical coordinate convention used by Enterprise and the task force.

The player physically enters a spotted aircraft on the seamless Flight Deck. Takeoff, airborne motion and recovery update the aircraft/flight snapshot while the ship, crew, combat, weather and operational world continue to exist underneath. Recovery returns the player to the same Flight Deck coordinate system.

## v1.8 cockpit operations extension
The first-person aircraft runtime now shares the same global east/north nautical coordinate system as Enterprise, Task Force 16, campaign bases, and logistics traffic. Cockpit target markers, mission waypoints, radio bearings, aircraft damage, emergency escape, and search-and-rescue are runtime state rather than separate scenes. Training air/surface contacts are explicitly non-historical simulation entities.


## v1.9 seamless expeditionary shore extension
The BASE layer is physically extended south without creating a new scene. The same perspective renderer, collision system, player position, input state and save system continue into a Ground Operations Center, motor pool, expeditionary airfield operations area, training runway/apron, amphibious control and supply staging.

A motor-pool utility vehicle uses a context-specific ground-drive state while remaining in the BASE collision grid. On foot, `D` remains strafe-right; while driving, `D` becomes right steering. Neither context maps `D` to a global panel.

The strategic ground-force layer shares the v1.4 operational coordinates and clock with the fleet/campaign, while the physical shore district provides first-person interaction and training representation.

## v2.0 — Seamless Combined-Arms District

The `BASE` layer was extended south to more than 100 grid rows. Infantry armory, fireteam command, field aid and a multi-building training village occupy the same coordinate system as the original training center, expeditionary district, pier and Enterprise gangway. Ground combat does not load a separate FPS scene; player movement, contacts, fireteam members, objectives and support effects operate inside `SeamlessOpenWorld3DApp`.

## v2.2 Theater expansion

The BASE layer now continues south beyond the battalion maneuver area to y≈245 in the same world coordinate system. Theater Command, Intelligence, Logistics, strategic terrain, bridges, sectors, depots and formation markers are rendered without scene replacement. F10 opens the strategic board; D remains normal right-strafe while no overlay is open.

## v2.3 Industrial district
The seamless BASE grid extends south into a physically walkable national industrial district. Production offices, shipyard control, refinery, training command, and rail/port logistics are in the same coordinate system as the training base, expeditionary areas, battlefield, and Theater Command. F12 is a shortcut to the same economy board; normal D movement remains unchanged.

## v2.4 Strategic Mobility district
The seamless BASE grid extends again south of the v2.3 industrial zone into dispatch, port, railhead, forward-depot, air-logistics and fleet-anchorage facilities. Freight road/rail geometry, hub structures and active shipment markers render in the same perspective renderer and collision world as every earlier shore district. F5 opens the Strategic Mobility board; outside an overlay, `D` remains right-strafe on foot and right-steer in vehicles.

The physical shipment marker is a local visualization of a much longer operational route. The logistics simulation retains its own route distance in kilometers; the renderer interpolates the shipment between the physical hub representations so the player can see that the lift is in transit without pretending the base map itself is hundreds of kilometers long.

## v2.7 dual-renderer / modular carrier architecture
The Tk client remains the backward-compatible executable simulation client and continues to use the optimized v2.5/v2.6 carrier-scale fallback geometry. The Unreal migration now treats Enterprise as a modular actor rather than one mesh: Hull/Deck/Hangar, Island, Weapons/Fittings, Deck Aircraft, Hangar Interior, Bridge, CIC and Engineering are independent asset modules. This is the long-term path for realistic visibility, collision, LOD/streaming and compartment VFX while retaining the same simulation state.
