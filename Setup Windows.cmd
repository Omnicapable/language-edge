@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Install Python 3.11 from python.org first, including the Python launcher.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" py -3.11 -m venv .venv
if errorlevel 1 exit /b 1
echo Installing packages. GPU users: see README for the PyTorch CUDA install command.
".venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pip install -c constraints-tested.txt -e ".[generate]"
if errorlevel 1 (
  pause
  exit /b 1
)
echo Setup complete. Open Start Windows.cmd next.
".venv\Scripts\python.exe" scripts\install_demo.py
pause
