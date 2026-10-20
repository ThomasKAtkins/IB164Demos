@echo off
setlocal
cd /d "%~dp0"

REM Rebuild all the Lab 7 demos after editing texts.txt (or a notebook).
REM
REM   1. copies the texts in texts.txt into each notebook
REM   2. checks and re-exports each notebook to its _<name>_app\ folder
REM   3. rebuilds the site in ..\docs\
REM
REM It does NOT publish. Preview with ..\preview_site.bat, then publish with
REM ..\update_site.bat "Update lab 7 texts".

echo.
echo === Embedding texts.txt into the notebooks ===
py -3.10 embed_texts.py
if errorlevel 1 goto :fail

for %%N in (shotgun_assembly repeats_long_reads genotyping) do (
    echo.
    echo === %%N ===
    py -3.10 -m marimo check %%N.py
    if errorlevel 1 goto :fail
    py -3.10 -m marimo export html-wasm %%N.py -o _%%N_app --mode run -f
    if errorlevel 1 goto :fail
    REM marimo writes index.html, but the launcher and the site expect
    REM <name>.html.
    if exist "_%%N_app\index.html" move /y "_%%N_app\index.html" "_%%N_app\%%N.html" >nul
)

echo.
echo === Rebuilding the site ===
cd /d "%~dp0.."
py -3.10 build_site.py
if errorlevel 1 goto :fail

echo.
echo Done. Preview with preview_site.bat, publish with update_site.bat.
pause
exit /b 0

:fail
echo.
echo FAILED - see the messages above. Nothing was published.
pause
exit /b 1
