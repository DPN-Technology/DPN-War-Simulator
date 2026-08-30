@echo off
setlocal
set PROJ=%~dp0ue5\WarSimulatorUE5\WarSimulatorUE5.uproject
if not exist "%PROJ%" (
  echo Unreal project not found: %PROJ%
  pause
  exit /b 1
)
start "" "%PROJ%"
