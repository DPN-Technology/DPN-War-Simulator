# v0.6 Shipboard Interaction Systems

## Dynamic access state
`HATCHES` defines training-schematic watertight access points. Each walkthrough state owns open/shut status. `tile_walkable(..., state)` includes those statuses in collision checks, so a shut hatch affects both player motion and ray-cast line of sight.

## Equipment runtime state
Every interactive `EquipmentNode` receives an `EquipmentRuntime` containing health, power, fault text and reset count. Training faults are deterministic so regression tests and playtests can reproduce them.

## Training-vs-history policy
Training injects are not inserted into the canonical Midway event list. They are walkthrough exercise events and are labeled `SIMULATED` in code, UI, logs and the v0.6 manifest.

## Live crew layer
`CrewAvatar` uses the same crew keys and station assignments as `EnterpriseDutyState`. The renderer visualizes those watchstanders while their performance data continues to come from the existing crew/proficiency/fatigue/stress model.

## Objective layer
The objective resolver examines open Enterprise station tasks ordered by deadline and maps the required action to its physical walkthrough equipment node. The HUD then provides deck/station guidance or local range/bearing.
