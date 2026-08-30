@echo off
setlocal enabledelayedexpansion
set "PROJ=%~dp0ue5\WarSimulatorUE5\WarSimulatorUE5.uproject"
if defined UE5_ROOT goto found
for %%V in (5.7 5.6 5.5 5.4) do if exist "C:\Program Files\Epic Games\UE_%%V\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" set "UE5_ROOT=C:\Program Files\Epic Games\UE_%%V"
:found
if not defined UE5_ROOT (
  echo Set UE5_ROOT to your Unreal Engine installation first.
  pause
  exit /b 1
)
"%UE5_ROOT%\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" "%PROJ%" -ExecutePythonScript="%~dp0ue5\WarSimulatorUE5\Content\Python\import_enterprise.py" -unattended -nop4
pause
