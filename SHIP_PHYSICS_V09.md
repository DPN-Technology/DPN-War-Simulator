# War Simulator v0.9 — Ship Physics & Seamanship

v0.9 adds a continuous vessel-motion model to the existing seamless first-person world. The carrier interior remains a vessel-local reference frame so the player can walk naturally while the ship moves through a global navigation space.

## Implemented physics

- Global east/north navigation position in nautical miles
- True heading, course over ground (COG), speed through water (STW), and speed over ground (SOG)
- Engine-order inertia: the carrier accelerates/decelerates over time instead of instantly changing speed
- Ahead and backing engine orders
- Rudder angle, speed-dependent steering authority, yaw rate, and turning-radius calculation
- Propulsion and steering integrity tied to existing equipment-runtime faults
- Wind-induced weather helm at low speed
- Ocean-current vector added to vessel through-water velocity
- Sea-state-driven roll, pitch, and heave
- Turn/acceleration inertial loads
- Player balance/movement penalties in rough conditions and hard maneuvering
- Mooring/cast-off state and gangway availability
- Anchor deployment, anchor drag, and anchor recovery
- Training bathymetry with a charted shoal and grounding risk
- Grounding load, hull-integrity damage, alarm state, and backing-off recovery
- Seamless underway exterior: shore geometry is removed from the ship-local view after cast-off while the carrier world stays loaded
- Persistent ship navigation state and player shipboard position/orientation across save/reload

## Physical first-person controls

### Bridge Helm
Walk to the physical helm and press `E`.

- Left Arrow — 5° more port rudder
- Right Arrow — 5° more starboard rudder
- `C` / `0` — rudder amidships
- `E` / `Esc` — leave helm

### Engine Telegraph
Walk to the physical engine telegraph and press `E`.

- `0` — Stop
- `1` — Dead Slow Ahead
- `2` — One-Third Ahead
- `3` — Two-Thirds Ahead
- `4` — Full Ahead
- `B` — Backing

Engine commands are rejected while moored. Full-ahead power is limited while the anchor is down.

### Mooring / Sea Detail
The physical sea-detail station is located near the Hangar Deck gangway.

- While secured: pressing `E` casts off and disconnects the gangway.
- When back at the home berth below 0.5 knots: pressing `E` secures the vessel and reconnects the gangway.

### Anchor
The forecastle anchor control is on the Flight Deck.

The ship must be at or below 4 knots before the anchor can be let go.

### Navigation / Motion Board
A physical navigation board is on the Bridge. `N` is also a testing shortcut.

It displays:

- True heading
- STW / SOG
- COG
- East/North training position
- Distance run
- Rudder / engine order
- Turning radius
- Wind/current
- Roll / pitch / heave
- Balance load
- Charted depth / draft
- Hull integrity
- Mooring/anchor/grounding state

`[` and `]` adjust the **training** sea state so rough-weather ship handling can be tested.

## Historical-accuracy boundary

The motion equations and maneuvering coefficients are **training-simulation calibration**, not a claim that they reproduce an archival USS Enterprise CV-6 maneuvering trial or exact hydrodynamic coefficients.

The existing sourced Battle of Midway chronology, intelligence delays, order of battle, and historical lock remain separate from the gameplay physics layer. The carrier interior also remains labeled a training schematic rather than an exact 1942 compartment reconstruction.
