@echo off
setlocal
cd /d "%~dp0"
python -m pip install python-docx pypdf reportlab
if errorlevel 1 (
  echo.
  echo Nao foi possivel instalar as dependencias opcionais.
  pause
  exit /b 1
)
echo.
echo Dependencias de Word/PDF instaladas.
pause
