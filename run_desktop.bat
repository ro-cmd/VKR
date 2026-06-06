@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY="
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe --version >nul 2>&1
    if not errorlevel 1 set "PY=venv\Scripts\python.exe"
)

if not defined PY goto find_python
goto run_app

:find_python
echo Checking for Python...
for %%P in (py python python3) do (
    %%P --version >nul 2>&1
    if not errorlevel 1 (
        %%P -3 -m venv venv 2>nul
        if exist "venv\Scripts\python.exe" goto venv_ok
        %%P -m venv venv 2>nul
        if exist "venv\Scripts\python.exe" goto venv_ok
    )
)

echo Python not found. Installing via winget...
winget install Python.Python.3.12 --accept-source-agreements --accept-package-agreements --silent --scope user 2>nul
if errorlevel 1 winget install Python.Python.3.11 --accept-source-agreements --accept-package-agreements --silent --scope user 2>nul

timeout /t 5 /nobreak >nul
for %%D in (312 311 310 39) do (
    if exist "%LOCALAPPDATA%\Programs\Python\Python3%%D\python.exe" (
        "%LOCALAPPDATA%\Programs\Python\Python3%%D\python.exe" -m venv venv 2>nul
        if exist "venv\Scripts\python.exe" goto venv_ok
    )
)
for %%D in (312 311 310 39) do (
    if exist "%ProgramFiles%\Python3%%D\python.exe" (
        "%ProgramFiles%\Python3%%D\python.exe" -m venv venv 2>nul
        if exist "venv\Scripts\python.exe" goto venv_ok
    )
)
py -3 -m venv venv 2>nul
python -m venv venv 2>nul
python3 -m venv venv 2>nul

:venv_ok
if not exist "venv\Scripts\python.exe" (
    echo.
    echo Python not found. Install manually: https://python.org
    echo Or run in new terminal: winget install Python.Python.3.12
    echo Then run this file again.
    pause
    exit /b 1
)

echo Creating venv and installing dependencies...
venv\Scripts\python.exe -m ensurepip --upgrade 2>nul
venv\Scripts\python.exe -m pip install -q --upgrade pip 2>nul
venv\Scripts\python.exe -m pip install -q -r requirements.txt
if errorlevel 1 (
    echo Retrying pip install...
    venv\Scripts\python.exe -m pip install -r requirements.txt
)
set "PY=venv\Scripts\python.exe"

:run_app
venv\Scripts\python.exe -c "import numpy" 2>nul
if errorlevel 1 (
    echo Fixing numpy...
    venv\Scripts\python.exe -m pip install --force-reinstall numpy
)
echo Starting Archaeo Map...
"%PY%" desktop_app.py
echo.
echo Exit code: %errorlevel%
pause
