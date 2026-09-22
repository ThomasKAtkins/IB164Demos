@echo off
setlocal
cd /d "%~dp0"

REM Rebuild docs\ from the current marimo exports and push to GitHub Pages.
REM
REM Run this after you re-export a notebook, e.g.:
REM   py -3.10 -m marimo export html-wasm lab4\peppered_moth.py ^
REM       -o lab4\_peppered_moth_app --mode run

echo.
echo === Rebuilding site ===
py -3.10 build_site.py
if errorlevel 1 (
    echo.
    echo Build FAILED - nothing was pushed.
    pause
    exit /b 1
)

echo.
echo === Publishing ===

git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
    echo This folder is not a git repository yet, so there is nothing to push.
    echo The site has been rebuilt in docs\ and you can preview it with:
    echo     preview_site.bat
    pause
    exit /b 0
)

REM Refuse to push if any oversized file somehow got staged.
git add -A
git diff --cached --name-only > "%TEMP%\ib164_staged.txt"
findstr /i ".tsv.bgz" "%TEMP%\ib164_staged.txt" >nul
if not errorlevel 1 (
    echo.
    echo STOPPED: a .tsv.bgz data file is staged. These are far too large
    echo for GitHub. Check .gitignore, then run: git reset
    del "%TEMP%\ib164_staged.txt" >nul 2>nul
    pause
    exit /b 1
)
del "%TEMP%\ib164_staged.txt" >nul 2>nul

git diff --cached --quiet
if not errorlevel 1 (
    echo No changes to publish - the site is already up to date.
    pause
    exit /b 0
)

set "MSG=%~1"
if "%MSG%"=="" set "MSG=Update demos"
git commit -m "%MSG%"
if errorlevel 1 (
    echo Commit failed.
    pause
    exit /b 1
)

git push
if errorlevel 1 (
    echo.
    echo Push failed. If this is the first push, set the remote first:
    echo     git remote add origin https://github.com/USERNAME/IB164.git
    echo     git push -u origin main
    pause
    exit /b 1
)

echo.
echo Done. GitHub Pages usually updates within a minute.
echo Students may need to refresh once to see the change.
pause
endlocal
