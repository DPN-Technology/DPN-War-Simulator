@echo off
setlocal
cd /d "%~dp0"

call BUILD_WINDOWS_EXE.bat --no-pause
if not %errorlevel%==0 (
  echo Build failed. Game was not launched.
  pause
  exit /b 1
)

if exist "dist\War Simulator.exe" (
  start "War Simulator" "dist\War Simulator.exe"
  exit /b 0
)

echo ERROR: Release executable was not found after build.
pause
exit /b 1
