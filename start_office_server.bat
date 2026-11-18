@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Python environment not found. Run install_office_server.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
if not exist data mkdir data
if not exist backups mkdir backups
echo Starting Staff Management Server on port 5000...
echo Keep this window open while staff are using the application.
echo On other office PCs, open http://SERVER-IP:5000
waitress-serve --listen=0.0.0.0:5000 --threads=8 app:app
pause
