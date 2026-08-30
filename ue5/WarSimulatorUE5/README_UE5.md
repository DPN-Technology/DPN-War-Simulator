# War Simulator — Unreal Engine migration foundation (v2.7)

This is the first GPU-engine migration drop. It is intentionally source-first rather than claiming a finished UE executable from an environment that does not contain Unreal Engine.

## Target
USS Enterprise (CV-6), late May / early June 1942 (Midway configuration).

## Open
1. Install Unreal Engine 5.5+ with C++ game-development support.
2. Open `WarSimulatorUE5.uproject` and select your installed UE5 version if prompted.
3. Allow Unreal to compile the C++ module.
4. In the Unreal Editor, enable Python Editor Script Plugin if it is not already enabled.
5. Run `Content/Python/import_enterprise.py` in the Unreal Python console/editor scripting environment.
6. The imported static mesh path is `/Game/Enterprise/SM_Enterprise_CV6_1942`.
7. Set/keep `WarSimGameMode` as the project game mode.

The project defaults to DX12 / Shader Model 6 and requests Nanite, Lumen GI/reflections, and Virtual Shadow Maps. These features require compatible hardware and an appropriate UE5 installation.

The v2.5–v2.7 Python game remains the currently executable simulation client while systems are migrated into the GPU client incrementally.
