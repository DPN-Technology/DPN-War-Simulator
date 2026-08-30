# War Simulator v1.3 — Task Force & Open-Ocean Operations

## Purpose
v1.3 expands the seamless first-person Enterprise simulation into a task-force environment. USS Enterprise remains the player vessel and live physics reference frame, while surrounding friendly ships have independent global navigation states and autonomous formation behavior.

## Historical vs. training data
The friendly Task Force 16 ship names are taken from the existing sourced Battle of Midway scenario manifest. The following are explicitly gameplay/training abstractions unless a later scenario supplies sourced values:

- Exact formation geometry and spacing
- AI commanding-officer identities
- Sensor ranges and detection curves
- Fuel/ammunition quantities and burn rates
- Replenishment transfer rates
- Surface-fire/depth-charge effectiveness
- Simulated enemy surface and submarine contacts
- Damage coefficients for escort ships

The v1.3 surface/submarine problem is labeled a SIMULATED TRAINING INJECT and does not modify the locked Midway historical timeline.

## Friendly task force
The runtime currently models these independently moving friendly units around Enterprise:

- USS Hornet (CV-8)
- USS Northampton
- USS Vincennes
- USS Pensacola
- USS Minneapolis
- USS New Orleans
- USS Atlanta
- USS Worden
- USS Monaghan
- USS Phelps
- USS Maury

Additional TF16 destroyers remain represented in the sourced order-of-battle data and can be promoted into full moving entities in later builds.

Each active ship tracks position, heading, speed, max speed, formation slot, fuel, ammunition, hull condition, propulsion, steering, sensors, collision-avoidance state, current order, ASW stores, and surface-fire stores.

## Formation AI
Every escort maintains a desired bearing/range relative to Enterprise's live heading and position. The ship does not teleport when Enterprise turns. It steers and changes speed to regain station.

Available training formations:

1. Carrier Screen
2. Column
3. Dispersed
4. ASW Screen

Individual ships can also be ordered to resume station, screen ahead, screen astern, or detach for independent maneuver.

## Collision avoidance
The fleet continuously calculates separation among Enterprise and escorts. When separation becomes unsafe, an escort performs a training collision-avoidance maneuver and the event is logged. Closest observed separation and collision-warning count are tracked.

## Sensors and contacts
Enterprise and escorts contribute to fleet detection. Detected contacts have confidence and identification state. Submerged contacts are intentionally harder to detect than surface contacts.

The training problem currently supports:

- Simulated hostile cruiser group
- Simulated hostile destroyer
- Simulated submerged submarine

These maneuver in global sea coordinates rather than remaining static icons.

## Escort combat
Once detected, a selected contact can be assigned to an escort:

- Cruisers/destroyers can conduct simulated surface engagement.
- Destroyers can conduct simulated ASW attacks using finite depth-charge stores.
- If an enemy penetrates the screen, an escort can take simulated damage.

This fleet combat is a training framework, not a claim about historical Midway surface/submarine engagements around Enterprise.

## Fleet communications
The Signal Bridge supports tactical radio or radio silence. During radio silence, fleet signaling switches to a visual signal abstraction (flags/lamp). Signal state and signal count persist.

## Replenishment
The Fleet Logistics board can order a selected friendly ship into a training replenishment rendezvous. The receiving ship must close the formation to transfer distance and Enterprise must be at a safe training speed (12 knots or less). Completed transfers restore fuel and ammunition.

The transfer quantities and rates are training values, not historical replenishment curves.

## Rank authority
Fleet-changing orders are restricted to SHIP COMMAND WATCH authority in the current career model. Junior personnel can view the tactical picture and report through the existing chain of command, but cannot change the formation, detach ships, order engagements, or start replenishment.

## Physical stations
The seamless world now includes:

- Task Force Tactical Plot — Bridge
- Signal Bridge / Fleet Communications — Island
- Fleet Logistics & Replenishment Board — Hangar Deck

The global `V` key is a development/convenience shortcut to the task-force plot.

## Persistence
The career save stores the full task-force snapshot, including friendly vessel positions/states, contacts, logistics, formation, signaling mode, training-problem status, combat outcomes, and fleet statistics.
