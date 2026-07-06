@echo off
setlocal

if not exist "..\venv\Scripts\python.exe" (
    echo [ERROR] venv not found at ..\venv\Scripts\python.exe
    echo Create it first with: py -3.11 -m venv ..\venv
    exit /b 1
)

echo [1/3] Upgrading pip inside venv...
"..\venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

echo [2/3] Installing base requirements...
"..\venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo [3/3] Installing face-recognition without dependency resolution (Windows workaround)...
"..\venv\Scripts\python.exe" -m pip install face-recognition==1.3.0 --no-deps
if errorlevel 1 exit /b 1

echo [OK] Backend dependencies installed successfully in venv.
endlocal
