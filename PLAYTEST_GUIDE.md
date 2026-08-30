# War Simulator v2.4 Playtest Guide

## 1. Start safely
On Windows, extract the ZIP and run `TEST_AND_RUN.bat`. The game only launches if the automated suite passes.

## 2. Confirm the D-key regression fix
With no terminal open, press/hold `D` while on foot. The player must strafe right and no menu/panel should open. Damage Control remains `F6`.

## 3. Reach the new Strategic Mobility district
From the original training base, continue south through the expeditionary, combined-arms, battalion, theater and v2.3 industrial districts. The new logistics area begins immediately south of National War Production.

Physical stations include:
- Strategic Mobility & Distribution Command
- National Distribution Depot Dispatch
- Strategic Port Delta Convoy Control
- Railhead Echo Movement Control
- Forward Depot Foxtrot Receiving
- Air Logistics Hub Golf
- Fleet Anchorage Hotel Logistics

The entire route is in the same BASE world; there is no normal scene-loading transition.

## 4. Open Strategic Mobility Command
Use the physical Strategic Mobility & Distribution Command terminal or press `F5`.

Inspection controls work at any rank:
- `TAB` route
- `H` hub
- `P` cargo package
- `N` shipment
- `G` priority

Operational dispatch/escort/repair/issue commands require operational command-watch authority.

## 5. Activate the logistics network
Press `S` from the logistics board. Once active, the direct allocation command on the F12 National War Production board is intentionally blocked. This verifies the v2.4 rule that production does not equal delivery.

## 6. Dispatch cargo
Select a route and cargo package, then press `A`.

Check that:
- a first-leg dispatch from National Distribution Depot decreases the national stockpile immediately;
- a downstream dispatch decreases the selected origin hub's staged inventory instead;
- a shipment appears as EN ROUTE;
- progress, health, route and escort status are visible;
- the operational recipient does not receive cargo merely because the shipment arrived.

## 7. Test a sea convoy escort
Select a SEA route and dispatch cargo. Press `C` to assign/release escort. A serviceable Task Force vessel is required for sea escort assignment.

Unescorted sea shipments accumulate substantially more simulated interdiction exposure and can be destroyed. An escorted shipment is safer but not invulnerable.

## 8. Test route and hub damage
Damage a route/bridge or hub through a developer/test profile, then verify dispatch or movement becomes delayed/blocked as effective capacity falls. `X` repairs the selected route/bridge and `F` repairs the selected hub, consuming national repair stores.

## 9. Verify multi-leg staging and final issue
For a true multi-leg check, send national cargo to Railhead Echo or Port Delta. Confirm the arrival only increases that hub's staged inventory. Then select a downstream route whose origin is that hub and dispatch again; the downstream shipment must consume the staged hub inventory.

At Forward Depot Foxtrot, Air Logistics Hub Golf, or Fleet Anchorage Hotel, select the final hub with `H` and press `I` to issue its staged inventory. Only then confirm the appropriate operational system receives surviving cargo:
- THEATER → strategic depot / land logistics
- AIRFIELD → expeditionary airfield / Carrier Air Group support stocks
- FLEET → Task Force fuel/ammunition/repair stocks

Shipment health determines how much cargo survives each transport leg.

## 10. Persistence
Save/exit and reload. Active/recent shipments, route damage, hub damage, staged hub inventories, hub issues, escort flags, arrivals, losses, delays and the logistics score should persist.

## 11. Qualification
With sufficient command authority, completing at least two final operational hub issues and at least one escorted shipment can earn `Strategic Logistics & Mobility Watch` when the career is saved/closed.

## Historical boundary
The v2.4 hubs, route names, distances, speeds, cargo quantities, capacities and interdiction coefficients are training/gameplay abstractions. They must not be read as archival historical logistics statistics.

# v2.5 Enterprise Realism / Performance Playtest

## First run
1. Extract the archive.
2. Run `TEST_AND_RUN.bat`.
3. At the training base, walk to the pier and visually inspect Enterprise from shore.
4. Board the ship and move through Hangar, Flight Deck, Island/Bridge, Engineering and Lower Deck.

## What should feel different
- The carrier should no longer end after a short 72-unit run. Flight Deck and internal centerline runs are roughly full carrier scale.
- The starboard island/funnel/mast should remain visible down the long deck instead of popping out at the normal close-detail distance.
- Walking close to walls/hatches should not make whole faces disappear.
- The default HUD should be compact. Press `TAB` to show/hide the deep systems picture.
- `F4` cycles PERFORMANCE -> BALANCED -> HIGH.
- Shipboard walk speed is slower/more human-scale; hold Shift to sprint.

## Performance check
Start in BALANCED. Walk through the Hangar and Engineering spaces for several minutes.

If the system is still struggling:
- press `F4` until PERFORMANCE appears in the top HUD;
- verify FPS improves and nearby equipment remains usable;
- do not treat HIGH as the recommended mode for low-end hardware.

If the system is strong enough, use HIGH to extend close visual detail and curved-geometry tessellation.

## D-key regression
At several locations on shore and aboard Enterprise:
1. Hold `D`.
2. Confirm the player strafes right.
3. Confirm no Damage Control screen opens.

Damage Control must remain on `F6`.

## Ship interaction regression
Physically test:
- all three Hangar <-> Flight Deck elevator/ladder points;
- Flight Deck <-> Island access;
- Island <-> Bridge access;
- Task Force plot / Signal Bridge / Fleet Logistics;
- Campaign plot / port logistics;
- Air Group Operations / Ready Room;
- Engineering and Damage Control equipment.

## Save migration
For an older save that was aboard the old short Enterprise:
- load the career once;
- confirm the player appears aboard the new full-scale ship rather than in open water/a wall;
- save, quit, reload;
- confirm the position is not stretched a second time.

# v2.6 Enterprise 1942 / Unreal migration playtest

## Current Python client
1. Start with `TEST_AND_RUN.bat`.
2. Walk to the Flight Deck and use `F4` to compare PERFORMANCE / BALANCED / HIGH.
3. Approach the island and inspect the new period AA/crane/searchlight silhouette cues.
4. Verify `D` moves right and does not open a screen; Damage Control is still `F6`.
5. Use `TAB` to ensure the detailed systems HUD remains optional.

## Standalone 3D asset
Run `OPEN_ENTERPRISE_3D_MODEL.bat`. Windows should open `assets3d/Enterprise_CV6_1942_Midway.glb` in the associated 3D viewer if one is installed.

The runtime GLB is grouped by material for GPU efficiency. `Enterprise_CV6_1942_Midway_EDITABLE.glb` keeps the named component structure for asset work.

## Unreal Engine migration
Requires a local Unreal Engine 5 installation.

1. Run `IMPORT_ENTERPRISE_UE5.bat` after setting `UE5_ROOT` if auto-detection fails.
2. Run `OPEN_UE5_PROJECT.bat`.
3. Allow C++ compilation.
4. Verify first-person WASD movement and that D is only MoveRight.
5. Verify `/Game/Enterprise/SM_Enterprise_CV6_1942` imports and the Enterprise actor resolves it.
6. Use `BUILD_UE5_WINDOWS.bat` to cook/package a Win64 Development build.

The container used to create v2.6 does not contain Unreal Engine, so the UE compile/cook step must be run on a machine with UE5 installed.

# v2.7 Enterprise reconstruction / Unreal ship pipeline playtest

1. Run `TEST_AND_RUN.bat`. Confirm the complete automated suite passes before the fallback client starts.
2. On foot, press `D`. It must strafe right and must not open Damage Control. `F6` remains Damage Control.
3. Board Enterprise and inspect the long carrier-scale Flight Deck and island area; the fallback client must still render and interact normally.
4. Inspect `assets3d/Enterprise_CV6_1942_Midway_preview.png` and `assets3d/Enterprise_CV6_1942_InteriorModules_preview.png` for the current 3D reconstruction/cutaway views.
5. Inspect `assets3d/modules/` and `assets3d/interiors/`. Four exterior and four interior GLBs must be present.
6. If Unreal Engine 5 is installed on Windows, run `IMPORT_ENTERPRISE_UE5.bat`, then open `ue5/WarSimulatorUE5/WarSimulatorUE5.uproject`. Confirm the importer creates separate Enterprise exterior/interior folders and enables Nanite where supported.
7. Treat Bridge/CIC/Engineering hidden layouts as reconstruction unless a future manifest marks an element Enterprise-specific/source-traced.
