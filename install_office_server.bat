@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python 3.10 or later is required. Install Python from https://www.python.org/downloads/windows/
  pause
  exit /b 1
)
py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
  echo Package installation failed. Check internet connection and requirements.txt.
  pause
  exit /b 1
)
if not exist data mkdir data
if not exist backups mkdir backups
echo Installation complete. Run start_office_server.bat to start the office server.
pause
