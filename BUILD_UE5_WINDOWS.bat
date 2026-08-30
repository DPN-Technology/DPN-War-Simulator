@echo off
setlocal enabledelayedexpansion
set "PROJ=%~dp0ue5\WarSimulatorUE5\WarSimulatorUE5.uproject"
if defined UE5_ROOT goto found
for %%V in (5.7 5.6 5.5 5.4) do (
  if exist "C:\Program Files\Epic Games\UE_%%V\Engine\Build\BatchFiles\Build.bat" set "UE5_ROOT=C:\Program Files\Epic Games\UE_%%V"
)
:found
if not defined UE5_ROOT (
  echo Unreal Engine 5 was not found automatically.
  echo Set UE5_ROOT to your UE installation, for example:
  echo set UE5_ROOT=C:\Program Files\Epic Games\UE_5.6
  pause
  exit /b 1
)
echo Using %UE5_ROOT%
call "%UE5_ROOT%\Engine\Build\BatchFiles\Build.bat" WarSimulatorUE5 Win64 Development -Project="%PROJ%" -WaitMutex -FromMsBuild
if errorlevel 1 exit /b %errorlevel%
call "%UE5_ROOT%\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun -project="%PROJ%" -noP4 -platform=Win64 -clientconfig=Development -build -cook -stage -pak -archive -archivedirectory="%~dp0UE5_Build"
if errorlevel 1 exit /b %errorlevel%
echo.
echo UE5 Windows build complete under UE5_Build.
pause
