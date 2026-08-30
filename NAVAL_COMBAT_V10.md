# War Simulator v1.0 — Naval Combat & Carrier Air Operations

## Design goal

v1.0 adds a reusable combat framework without corrupting the historical simulation. Historical scenarios can later instantiate sourced opposing forces, attack geometry, weapons and timing; until then, the new live-fire problem is clearly labeled as a simulated training raid.

## Combat pipeline

1. A contact exists with bearing/range/altitude/speed and incomplete confidence.
2. CIC/Radar updates the track.
3. Confidence can cross the identification threshold.
4. General Quarters is set.
5. Fire Control calculates a solution affected by confidence, readiness, range and vessel motion.
6. A battery is selected according to range and ammunition state.
7. Firing consumes ready-service ammunition and starts a reload cycle.
8. Target damage accumulates; destroyed tracks are removed from the attack problem.
9. Surviving tracks continue closing and can attack.
10. Hits feed back into physical hull/equipment state.

## Batteries

The current v1.0 batteries are training abstractions:

- 5-inch dual-purpose battery — longest defensive range / slower reload / heavier per-salvo effect
- Medium AA battery — intermediate range and volume
- Light AA battery — close-range defensive layer

Their exact v1.0 ranges, ammunition totals and damage numbers are simulation calibration, not archival claims.

## Carrier aviation

CAP and strike aircraft are not spawned from a menu. They reuse the physical aircraft packages from the existing Hangar/Flight Deck system. A package must be fueled, armed, moved to an elevator, spotted on deck and launched from Flight Control.

CAP can intercept hostile simulated air tracks. It carries finite endurance and ammunition and must later recover. Recovered aircraft return in a service-required state.

Training strike launches consume aviation fuel and bomb/torpedo store units.

## Damage coupling

Combat hits can affect:

- Hull integrity
- Electrical load board
- Main engineering console
- Radio equipment
- Damage-control board
- AA director
- Flight-control equipment

Those are the same runtime equipment objects used by the first-person ship. This means a combat hit can reduce ship handling or combat capability until the player physically restores the affected station.

## Persistence

`CareerProfile.combat_snapshot` stores the current combat state so an active training engagement can survive save/reload. Career totals separately record training runs, best score, enemy contacts defeated, hits taken and carrier sorties.

## Historical boundary

The training raid is not inserted into the Battle of Midway canonical event list. `historical_lock` remains conceptually separate from combat training. Future historical combat scenarios should source their own attack timing, aircraft/ship order of battle, weapon fit, weather, damage and communication data before enabling historical mode.
