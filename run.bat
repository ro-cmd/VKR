@echo off
chcp 65001 >nul
cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe --version >nul 2>&1
    if errorlevel 1 (
        echo Recreating venv...
        rmdir /s /q venv 2>nul
        goto create_venv
    )
    goto run_app
)

:create_venv
echo Creating venv...
py -3 -m venv venv 2>nul
if errorlevel 1 python -m venv venv 2>nul
if not exist "venv\Scripts\python.exe" (
    echo Python not found. Install from python.org
    pause
    exit /b 1
)
venv\Scripts\python.exe -m ensurepip --upgrade 2>nul
echo Installing dependencies...
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo Install failed.
    pause
    exit /b 1
)

:run_app
venv\Scripts\python.exe -c "import geopandas" 2>nul
if errorlevel 1 (
    echo Installing geopandas...
    venv\Scripts\python.exe -m ensurepip --upgrade 2>nul
    venv\Scripts\python.exe -m pip install -r requirements.txt
)
venv\Scripts\python.exe archaeo_mapper.py --config config.ini
pause
