@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Building portable Archaeo Map...
if not exist "venv\Scripts\python.exe" (
    echo Run run_desktop.bat first to create venv.
    pause
    exit /b 1
)

venv\Scripts\python.exe -m pip install -q pyinstaller
venv\Scripts\pyinstaller.exe --noconfirm ^
    --onedir ^
    --windowed ^
    --name "ArchaeoMap" ^
    --paths . ^
    --hidden-import "archaeo" ^
    --hidden-import "archaeo.io" ^
    --hidden-import "archaeo.config" ^
    --hidden-import "archaeo.crs" ^
    --hidden-import "archaeo.exporting" ^
    --hidden-import "archaeo.plots" ^
    --hidden-import "archaeo.processing" ^
    --hidden-import "archaeo.quality" ^
    desktop_app.py

if exist "dist\ArchaeoMap\ArchaeoMap.exe" (
    echo.
    echo Done. Copy folder dist\ArchaeoMap to any PC and run ArchaeoMap.exe
    echo No Python needed on target PC.
) else (
    echo Build failed.
)
pause
