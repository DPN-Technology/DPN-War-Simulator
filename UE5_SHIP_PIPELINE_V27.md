# War Simulator v2.7 — Unreal Ship Pipeline

## Why the ship is modular
A 250 m carrier should not be treated as one indivisible mesh. v2.7 separates the ship so areas can be streamed, culled, collision-authored and historically refined independently.

## Exterior modules
- Hull / Flight Deck / Hangar exterior
- Island
- Weapons / deck fittings
- Deck aircraft

## Interior modules
- Hangar
- Bridge / pilot house
- CIC
- Engineering / machinery

## Unreal actor structure
`AEnterpriseCV6Actor` exposes individual mesh components for each major exterior and interior section. It retains a monolithic compatibility mesh as a fallback but automatically prefers the modular hull/deck asset when available.

Blueprint-callable visibility controls allow the project to hide high-detail modules based on player location, streaming state or performance budget.

## Physical ship hooks
`ACV6WatertightDoorActor` provides a collision-aware animated watertight door foundation.

`ACV6CompartmentVolume` carries compartment identity plus flooding, fire, smoke and electrical-power state. This is the bridge between the existing Python simulation concepts and future UE material/VFX/audio behavior.

## Renderer target
The project requests DirectX 12 / SM6, Nanite, Lumen GI/reflections, Virtual Shadow Maps and TSR. Imported static meshes attempt Nanite enablement and complex collision as an initial authoring fallback.

For a production-quality build, interior collision should gradually be replaced with authored simple collision and compartment portal/occlusion volumes rather than relying permanently on complex-as-simple collision.

## Import
Run `IMPORT_ENTERPRISE_UE5.bat` on a Windows machine with Unreal Engine 5 installed. The importer loads all exterior/interior modules into stable `/Game/Enterprise/...` folders.

## Current limitation
UE5 is not installed in the build environment that produced this package, so the Unreal project has not been compiled/cooked here. Static project validation is included in the automated tests, but final UE runtime validation must be performed on a UE5-capable Windows machine.
