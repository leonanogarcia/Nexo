@echo off
setlocal
cd /d "%~dp0"
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto :erro
pyinstaller --noconfirm --clean --onefile --windowed --name Nexo --icon nexo_icon.ico main.py
if errorlevel 1 goto :erro
echo.
echo Pronto: dist\Nexo.exe
pause
exit /b 0
:erro
echo.
echo Ocorreu um erro durante a compilacao.
pause
exit /b 1
