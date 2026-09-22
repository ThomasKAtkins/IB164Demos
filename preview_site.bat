@echo off
setlocal
cd /d "%~dp0"

REM Preview the built site locally, exactly as students will see it.

if not exist "docs\index.html" (
    echo No built site found. Building it now...
    py -3.10 build_site.py
    if errorlevel 1 (
        echo Build failed.
        pause
        exit /b 1
    )
)

set "PORT=8770"
set "URL=http://localhost:%PORT%/"

echo.
echo Previewing the IB164 demo site at %URL%
echo.
echo Leave this window open while you look at the site.
echo Close it (or press Ctrl+C) when you are done.
echo.

cd /d "%~dp0docs"
start "" cmd /c "timeout /t 2 >nul & start "" "%URL%""
py -3.10 -m http.server %PORT%

endlocal
