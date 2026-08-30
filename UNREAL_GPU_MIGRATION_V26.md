# War Simulator v2.6 — Unreal/GPU Migration Foundation

v2.6 is the point where the project stops pretending the Python/Tk software renderer can eventually become photorealistic. The simulation client remains usable and backward-compatible, but the visual target moves to a GPU engine.

## What is included

- `assets3d/Enterprise_CV6_1942_Midway.glb` — runtime GLB grouped into 12 material groups for low draw-call import.
- `assets3d/Enterprise_CV6_1942_Midway_EDITABLE.glb` — editable source scene with hundreds of named parts.
- `assets3d/Enterprise_CV6_1942_Midway.obj` — interchange fallback.
- `assets3d/textures/` — initial deck/hull PBR texture maps.
- `ue5/WarSimulatorUE5/` — C++ Unreal Engine 5 migration project.
- `IMPORT_ENTERPRISE_UE5.bat` — imports the GLB with Unreal Editor command line when UE5 is installed.
- `BUILD_UE5_WINDOWS.bat` — compiles/cooks/packages a Windows UE build when UE5 is installed.
- `OPEN_UE5_PROJECT.bat` — opens the project with the registered UE association.
- `OPEN_ENTERPRISE_3D_MODEL.bat` — opens the GLB in the Windows-associated 3D viewer.

## Renderer target

The UE project requests:

- DirectX 12 / Shader Model 6
- Nanite
- Lumen global illumination and reflections
- Virtual Shadow Maps
- first-person Character movement

These features are not available in the current execution environment, so v2.6 ships source/project files rather than falsely claiming that a UE Windows executable was compiled here.

## Simulation bridge

`UWarSimStateBridge` reads the existing `%LOCALAPPDATA%/WarSimulator/career.json` save and exposes core player/ship state to UE Blueprints/C++.

This is the beginning of migrating visual presentation while retaining the already-built career, ship physics, combat, crew, task force, campaign, air, ground, strategic, economy and logistics simulation data.

## Asset target

The model is aimed at Enterprise around the Battle of Midway, late May/early June 1942. Source-driven visible features are separated from reconstruction geometry in `historical_data/enterprise_1942_visual_v26.json`.

The model is not yet an archival-grade museum reconstruction. Exact hull station curves, island dimensions, mount coordinates, camouflage RGB values and interior partitions remain reconstruction work until traced from suitable plans.

## v2.7 continuation
v2.7 keeps the v2.6 migration foundation but replaces the one-asset strategy with streamable Hull/Deck/Hangar, Island, Weapons/Fittings, Deck Aircraft, Hangar, Bridge, CIC and Engineering modules. See `UE5_SHIP_PIPELINE_V27.md`.
