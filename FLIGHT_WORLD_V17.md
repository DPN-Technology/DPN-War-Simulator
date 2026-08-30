# War Simulator v1.7 — First-Person Carrier Flight & Animated Ship World

## Scope
v1.7 extends the seamless Enterprise/open-ocean runtime with a physically entered cockpit training loop and a denser animated shipboard presentation. The new flight model is a **training simulation calibration**. It is not represented as archival F4F, SBD, or TBD flight-test performance data.

## Physical cockpit loop
1. Use Air Group Operations (`K` or the physical planning rooms) to plan a mission so individual aircraft are spotted on the Flight Deck.
2. Walk to a physically rendered individual aircraft.
3. Press `E` to enter the cockpit.
4. Press `I` to start the engine.
5. Release wheel brakes with `B`.
6. Use `W/S` for throttle, `A/D` for bank, Up/Down for pitch, and Left/Right for yaw.
7. Carrier takeoff occurs only after sufficient engine power, acceleration and usable wind-over-deck conditions.
8. In flight, global east/north position, heading, altitude, airspeed, fuel, pitch, bank and vertical speed evolve continuously.
9. Configure `G` gear and `F` flaps, return near Enterprise, and press `L` to attempt recovery.
10. A recovery is accepted only inside the training landing envelope. Stop on deck and press `E` to leave the cockpit back into the same seamless Flight Deck world.

## Animated physical-world upgrades
- Articulated procedural sailors use a simple leg/arm gait while moving to watches, battle stations and routine destinations.
- Six additional physical compartment/fire-boundary doors expand the animated hatch network.
- Electrical/equipment casualties produce visible arcing or steam effects near the failed equipment.
- Engineering/command-space electrical casualties dim the environment and activate emergency red-light presentation.
- Existing rain, storm, lightning, smoke, fire, flooding, hull-breach, radar, propeller and machinery animation remain active.

## Persistence
The career save now stores the cockpit/flight snapshot plus cumulative cockpit sessions, carrier takeoffs, carrier landings and pilot distance.

## Historical separation
Historical squadron identities and the locked Midway timeline remain in the sourced historical layer. Exact cockpit handling coefficients, takeoff speeds, landing envelope, individual roster data, flight fuel consumption and the procedural 3D geometry remain gameplay/training abstractions unless a separate source manifest says otherwise.
