# War Simulator v2.5 Changelog

## v2.4 — Strategic Mobility, Convoy Warfare & Global Logistics
- Added `warsim/logistics_network.py` persistent strategic-mobility simulation.
- Added six physical logistics hubs and six rail/road/sea transport routes.
- Added finite cargo packages, dispatch/reservation, shipment progress, health, delays, congestion and interdiction exposure.
- Added Task Force escort assignment for sea shipments.
- Added shipment damage/loss: destroyed cargo does not reach operational recipients.
- Added route/bridge and hub damage/repair using national repair stores.
- Added true multi-leg staging: arrivals add cargo to destination-hub inventory; downstream dispatch consumes origin-hub inventory; only final-hub ISSUE transfers cargo into theater depots, land logistics/artillery, expeditionary airfields, Carrier Air Group or Task Force stocks.
- Once v2.4 logistics is activated, legacy direct v2.3 economy allocations are disabled so national output must travel through the logistics network.
- Expanded the seamless base from 312 to 382 grid rows and added a Strategic Mobility / freight / port / rail district south of the industrial area.
- Added F5 Strategic Mobility Command, physical dispatch/convoy/railhead/receiving terminals, staged-inventory display and `I` final-hub issue control.
- Added persistent logistics career snapshot/statistics.
- Added 18 v2.4 automated tests and `GUI_SMOKE_V24`.
- Preserved all v0.1–v2.3 systems and the permanent D-key movement fix.

## v2.5 — Enterprise Realism & Performance Rebuild
- Rebuilt Enterprise from the 72 x 28 prototype footprint to a ~245 x 30 m carrier-scale seamless layout.
- Rescaled all six ship levels, equipment, hatches, connectors, living-ship stations, aircraft placement and damage positions.
- Added one-time backward-compatible migration for old on-ship player coordinates (`ship_layout_version = 2`).
- Added tapered/faceted multi-strake hull, long flight-deck silhouette, hangar openings, elevator plates, sponsons, arresting wires, chamfered island tiers, bridge glazing, funnel and mast.
- Carrier exterior now renders while standing ashore/pier-side.
- Added near-plane polygon clipping to eliminate close-surface popping.
- Merged floor/ceiling spans and exposed bulkhead runs to reduce per-frame Canvas object creation.
- Added distance/detail/entity culling and reduced procedural cylinder tessellation in non-HIGH modes.
- Added frame-budgeted loop and adaptive detail reduction in BALANCED mode.
- Added F4 PERFORMANCE / BALANCED / HIGH visual-quality modes.
- Replaced the oversized default diagnostics HUD with a compact gameplay HUD; TAB toggles the full systems picture.
- Reduced shipboard walk speed to human-scale values while retaining sprint.
- Moved conflicting physical operations stations so intended `E` interactions no longer get stolen by nearby hatches/consoles.
- Added 15 v2.5 automated tests and `GUI_SMOKE_V25`.
- Preserved the permanent D-key movement fix and all v0.1-v2.4 systems.

## v2.6 — Midway 1942 Enterprise Visual Rebuild + Unreal/GPU Migration

- Locked the new art target to late May / early June 1942 Enterprise rather than a generic wartime carrier.
- Added a standalone full-scale Enterprise GLB/OBJ asset and initial PBR texture package.
- Runtime GLB is grouped into a small material set for GPU import; editable GLB retains hundreds of named components.
- Added period-specific exterior cues: CXAM-style radar, aircraft crane, searchlights, 5in/38 galleries, 1.1in quads, 20 mm battery, deck markings, catwalks, rafts/boats and representative Midway aircraft.
- Reworked the generated 3D asset hangar from an opaque slab to an open-sided framed structure.
- Improved legacy fallback rendering with the same Midway-period AA/crane/searchlight cues without removing the v2.5 performance work.
- Added C++ Unreal Engine migration project with first-person controls, Enterprise actor, DX12/SM6 defaults, Nanite/Lumen/VSM settings and automated GLB import script.
- Added UE legacy-save bridge for existing `%LOCALAPPDATA%/WarSimulator/career.json` state.
- Added `IMPORT_ENTERPRISE_UE5.bat`, `OPEN_UE5_PROJECT.bat`, `BUILD_UE5_WINDOWS.bat`, and `OPEN_ENTERPRISE_3D_MODEL.bat`.
- Added 20 v2.6 automated tests plus `GUI_SMOKE_V26`.

## v2.7 — Enterprise CV-6 Midway Reconstruction / Modular Unreal Ship
- Increased editable Enterprise asset from the v2.6 foundation to 1,498 named components and 43,314 triangles.
- Added human-scale exterior fittings: deck tie-downs, arresting-gear housings, barrier stanchions, safety-net lattice, hose reels/fire lockers, capstans, hull seam/scupper cues, island doors/portholes, bridge-wing rails, signal halyards, gallery ladders and ready lockers.
- Deepened Hangar, Bridge, CIC and Engineering reconstruction modules with additional equipment, ladders, gauges, phone racks, fire stations, elevator rails, tow tractors and machinery-space details.
- Split the Unreal exterior into Hull/Deck/Hangar, Island, Weapons/Fittings and Deck-Aircraft GLBs for independent streaming/occlusion/refinement.
- Expanded `AEnterpriseCV6Actor` to modular exterior/interior components with Blueprint visibility controls.
- Added physical UE foundations for watertight doors and compartment flooding/fire/smoke/power state.
- Added `historical_data/enterprise_1942_reconstruction_v27.json` with explicit source/photo/class-plan vs reconstruction-only boundaries.
- Added cutaway interior-module preview and new v2.7 reconstruction documentation.
- Added 24 v2.7 automated reconstruction tests and `GUI_SMOKE_V27`.
- Preserved all prior simulation systems, old saves and the permanent D-key movement guarantee.
