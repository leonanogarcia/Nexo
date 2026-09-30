@echo off
setlocal
cd /d "%~dp0"
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
  set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
)
python -m pip install pillow requests python-docx pypdf reportlab
if errorlevel 1 (
  echo.
  echo Nao foi possivel instalar as dependencias opcionais.
  pause
  exit /b 1
)
echo.
echo Dependencias de Word/PDF instaladas.
pause
