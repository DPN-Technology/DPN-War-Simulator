# War Simulator v0.8 — Seamless Open World Architecture

## Design rule

A room or deck is no longer a game scene. All implemented spaces exist in one global coordinate system.

## Global world

Approximate implemented span: more than 140 horizontal world units plus 16 vertical world units across the base, pier and carrier.

### Shore layer

`BASE` — floor Z +3.2

Contains training/admin buildings, support spaces, exterior base area and the pier approach.

### USS Enterprise layers

- `LOWER` — Z -3.2
- `ENGINEERING` — Z 0.0
- `HANGAR` — Z +3.2
- `FLIGHT` — Z +6.4
- `ISLAND` — Z +9.6
- `BRIDGE` — Z +12.8

The base and Hangar Deck share elevation so the pier/gangway can be crossed by ordinary horizontal movement.

## Continuous traversal

`world_walkable(x, y, camera_z)` resolves collision against the physical layer beneath the player.

The gangway crosses directly from base geometry into Hangar Deck geometry.

Vertical connectors have two physical endpoints in the same coordinate world. Using one interpolates camera Z over time; it does not change a scene identifier or recreate simulation state.

## Geometry policy

The carrier geometry is a training schematic. It is designed to support:

- physical traversal
- station placement
- multi-deck systems
- crew movement
- damage-control gameplay
- career training
- historical operational duties

It is not represented as an exact reconstruction of Enterprise's 1942 internal arrangement.

## Operational integration

`SHIP_EQUIPMENT_WORLD` maps mature v0.4-v0.7 Enterprise equipment logic into physical world positions. Interacting with the physical console invokes the existing station/task logic rather than duplicating or replacing the historical engine.

Dynamic shipboard hatches similarly map the existing hatch state into world collision and rendering.

## Rendering

The standard-library renderer perspective-projects:

- floors
- ceilings
- exposed bulkhead faces
- equipment boxes
- hatches
- ladders/connectors
- NPCs
- aircraft
- objective beacons
- exterior water planes

Only the current and immediately adjacent vertical decks are rendered at normal range to keep the software renderer usable while preserving the visual continuity of shafts/access points.

## State continuity

The following persist while the player moves between spaces:

- player career
- Enterprise duty state
- Midway historical state
- crew readiness
- aircraft state
- equipment faults
- hatch state
- ship-system trainer state
- daily-life state
- work orders
- needs
- objective state

This is the key architectural difference from v0.7.
