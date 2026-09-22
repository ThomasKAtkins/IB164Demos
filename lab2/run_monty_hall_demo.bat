@echo off
setlocal

set "APPDIR=%~dp0_monty_hall_app"
set "PORT=8780"
set "URL=http://localhost:%PORT%/monty_hall.html"

REM Pick a Python launcher that actually works on this machine.
set "PYCMD="
for %%P in ("py -3" "python" "python3") do (
    if not defined PYCMD (
        %%~P -c "print(1)" >nul 2>nul
        if not errorlevel 1 set "PYCMD=%%~P"
    )
)

if not defined PYCMD (
    echo Could not find a working Python interpreter on PATH.
    echo Please install Python or add it to PATH, then re-run this file.
    pause
    exit /b 1
)

echo Starting local server for the Monty Hall demo...
echo   Folder: %APPDIR%
echo   URL:    %URL%
echo.
echo Leave this window open while you use the notebook.
echo Close it (or press Ctrl+C) when you're done.
echo.

cd /d "%APPDIR%"
start "" cmd /c "timeout /t 2 >nul & start "" "%URL%""
%PYCMD% -m http.server %PORT%

endlocal
