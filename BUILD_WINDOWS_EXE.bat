@echo off
setlocal
cd /d "%~dp0"
set NOPAUSE=0
if /I "%~1"=="--no-pause" set NOPAUSE=1

echo ============================================================
echo WAR SIMULATOR v2.7 ENTERPRISE 1942 VISUAL REBUILD - WINDOWS BUILDER
echo ============================================================

where py >nul 2>nul
if not %errorlevel%==0 (
  echo ERROR: Python Launcher ^(py.exe^) was not found.
  echo Install Python 3.11+ from python.org and enable the Python launcher.
  goto :fail
)

py -3 -m pip install --upgrade pyinstaller
if not %errorlevel%==0 goto :fail

py -3 -m unittest discover -s tests -p "test_*.py" -v
if not %errorlevel%==0 goto :fail

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist "War Simulator.spec" del /q "War Simulator.spec"

py -3 -m PyInstaller --noconfirm --clean --onefile --windowed --name "War Simulator" --icon "assets\war_simulator.ico" main.py
if not %errorlevel%==0 goto :fail

echo.
echo ============================================================
echo BUILD COMPLETE - SEAMLESS JOINT / COMBINED-ARMS RUNTIME
echo EXE: %CD%\dist\War Simulator.exe
echo ============================================================
if "%NOPAUSE%"=="0" (
  explorer "%CD%\dist"
  pause
)
exit /b 0

:fail
echo.
echo ============================================================
echo BUILD FAILED - no release should be distributed.
echo ============================================================
if "%NOPAUSE%"=="0" pause
exit /b 1
