@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo WAR SIMULATOR v2.7 ENTERPRISE 1942 VISUAL REBUILD - TEST AND RUN
echo ============================================================

where py >nul 2>nul
if not %errorlevel%==0 (
  echo ERROR: Python Launcher ^(py.exe^) was not found.
  echo Install Python 3.11+ from python.org and enable the Python launcher.
  pause
  exit /b 1
)

py -3 -m unittest discover -s tests -p "test_*.py" -v
if not %errorlevel%==0 (
  echo.
  echo TESTS FAILED - GAME WILL NOT LAUNCH.
  pause
  exit /b 1
)

echo.
echo ALL TESTS PASSED - LAUNCHING SEAMLESS JOINT / STRATEGIC WAR WORLD.
start "War Simulator v2.7 Enterprise 1942" pyw -3 WarSimulator.pyw
exit /b 0
