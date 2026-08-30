# Enterprise Walkthrough Architecture — v0.6 (cumulative)

## State composition

`ShipboardWalkState`

contains / references:

- `EnterpriseDutyState` — shared historical clock, duty tasks, crew, readiness, contact state;
- player deck / X / Y / facing;
- watch period;
- qualification progress;
- elevator states;
- aircraft handling packages;
- walkthrough log / interaction counters.

## Rendering separation

`warsim.walkship.raycast()` generates ray distances only. Tk rendering lives in `warsim.ui`.

This intentionally separates simulation state from graphics so the renderer can later be replaced by a 3D engine without rewriting the historical/career systems.

## Geometry policy

`DECK_MAPS` are collision maps for training gameplay.

`ZONES` identify operational areas.

`EQUIPMENT` identifies interaction nodes.

None of those coordinate values are treated as archival deck-plan measurements.

## Direct interaction flow

1. player moves through collision grid;
2. `nearby_equipment()` resolves the nearest usable node;
3. `interact()` maps the equipment to either:
   - a station action in `EnterpriseDutyState`,
   - deck transition,
   - aircraft elevator control,
   - aircraft handling,
   - station qualification step;
4. station action uses the existing v0.4 task/readiness logic;
5. practical progress and career awards remain separate from historical event truth.

## Aircraft workflow

Training aircraft packages use state flags:

- deck
- position
- fueled
- armed
- spotted
- launched
- status

Handling controls modify those states and synchronize aggregate aviation readiness back into the Enterprise station-duty state.

## Future migration path

A later 3D engine can consume the same:

- historical manifests;
- Enterprise task state;
- station/action identifiers;
- career qualifications;
- aircraft state;
- crew state;
- equipment action IDs.

Only the geometry/renderer/input adapters would need replacement.


## v0.6 additions
Dynamic hatch state now participates in collision/raycasting; equipment has runtime fault/health state; live watchstander avatars use Enterprise crew assignments; active Enterprise station tasks resolve to physical objective nodes. Training injects remain separate from historical events.
