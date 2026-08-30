# War Simulator v2.7

## USS Enterprise (CV-6) — Midway 1942 Reconstruction / Unreal Ship Pipeline

v2.7 is a ship-realism phase. It does not add another strategic subsystem. It keeps the complete v0.1–v2.6 simulation stack, while substantially increasing the Enterprise asset density and reorganizing the Unreal migration around independently streamable ship sections.

### Current playable client
The Python/Tk client remains the currently executable fallback. It keeps the v2.5/v2.6 carrier-scale layout, clipping/culling/performance work, Midway-period exterior cues, compact HUD and the permanent input rule: normal first-person `D` moves right; Damage Control remains `F6`.

### v2.7 Enterprise reconstruction asset
The primary editable asset is `assets3d/Enterprise_CV6_1942_Midway_EDITABLE.glb` and the batched runtime compatibility asset is `assets3d/Enterprise_CV6_1942_Midway.glb`.

Current generated exterior asset statistics:
- approximately 251.4 m overall reconstructed bounds
- 1,498 named editable objects
- 24,629 vertices
- 43,314 triangles
- 55 batched runtime groups
- three elevator assemblies
- full-length open-sided hangar framing
- photo-constrained island/mast/radar/crane/director cues
- Midway-period 8 x single 5in/38, 4 x quad 1.1in, and 30 modeled 20 mm positions
- human-scale deck fittings, safety-net lattice, tie-downs, fire lockers/hose reels, capstans, ladders, hull seam/scupper cues, island doors/portholes and signal rigging

### Streamable exterior modules
`assets3d/modules/` contains independent runtime modules:
- `CV6_HullDeck_Hangar.glb`
- `CV6_Island.glb`
- `CV6_Weapons_Fittings.glb`
- `CV6_DeckAircraft.glb`

These allow the island, weapon galleries or deck-aircraft set to be replaced by denser research-driven assets without rebuilding the whole 250 m carrier.

### Streamable interior reconstruction modules
`assets3d/interiors/` contains:
- Hangar interior
- Bridge / pilot house
- CIC reconstruction
- Machinery / engineering reconstruction

The interior modules now include more equipment at human scale—bridge helm/telegraphs/compass/pelorus/dials, CIC plot/scopes/phone racks/status boards, engineering boilers/turbines/generators/piping/gauges/catwalks/ladders, and hangar elevator rails/fire stations/workbenches/tow tractors.

These hidden layouts are **reconstruction**, not claimed exact Enterprise-specific June 1942 plans. See `historical_data/enterprise_1942_reconstruction_v27.json`.

### Unreal Engine 5 project
`ue5/WarSimulatorUE5/` now imports the ship as separate Hull/Deck/Hangar, Island, Weapons/Fittings, Deck Aircraft, Hangar Interior, Bridge, CIC and Engineering modules. The project includes:
- C++ first-person character foundation
- DX12 / Shader Model 6
- Nanite target
- Lumen GI/reflections
- Virtual Shadow Maps
- TSR
- physical `CV6WatertightDoorActor`
- physical `CV6CompartmentVolume` hooks for flooding/fire/smoke/power state
- legacy save bridge
- modular `EnterpriseCV6Actor`

The build environment used to create this package does **not** include Unreal Engine. The UE5 source/project/assets are therefore prepared and tested statically, but no UE5 Windows executable is falsely claimed.

### Start
- `TEST_AND_RUN.bat` — run all Python simulation tests, then launch the fallback client.
- `START_WAR_SIMULATOR.vbs` — normal no-console fallback launch.
- `IMPORT_ENTERPRISE_UE5.bat` — import the modular CV-6 assets on a Windows PC with UE5 installed.
- `OPEN_UE5_PROJECT.bat` — open the UE project.
- `BUILD_UE5_WINDOWS.bat` — compile/cook/package with a local UE5 install.
- `OPEN_ENTERPRISE_3D_MODEL.bat` — inspect the GLB in your installed 3D viewer.

See `ENTERPRISE_RECONSTRUCTION_V27.md`, `UE5_SHIP_PIPELINE_V27.md`, and `PLAYTEST_GUIDE.md`.
