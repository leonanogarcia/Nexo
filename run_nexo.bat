@echo off
setlocal
cd /d "%~dp0"
python main.py
if errorlevel 1 (
  echo.
  echo O Nexo encontrou um erro ao iniciar.
  pause
)
