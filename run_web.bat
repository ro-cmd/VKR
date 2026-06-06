@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" goto create_venv
venv\Scripts\python.exe --version >nul 2>&1
if errorlevel 1 goto create_venv
goto run_app

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
venv\Scripts\python.exe -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing Flask...
    venv\Scripts\python.exe -m pip install flask werkzeug
)
echo Starting at http://127.0.0.1:5000
venv\Scripts\python.exe web_app\app.py
pause
