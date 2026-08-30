@echo off
cd /d "%~dp0"
where pyw >nul 2>nul
if %errorlevel%==0 (
  start "War Simulator v2.7 Enterprise 1942" pyw -3 WarSimulator.pyw
  exit /b 0
)
where pythonw >nul 2>nul
if %errorlevel%==0 (
  start "War Simulator v2.7 Enterprise 1942" pythonw WarSimulator.pyw
  exit /b 0
)
echo Python 3.11+ was not found.
pause
exit /b 1
