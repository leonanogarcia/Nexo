@echo off
title Nexo - Gerar Instalador Windows (Setup)
cd /d "%~dp0\.."

echo ========================================================
echo   Nexo - Gerando Instalador Oficial para Windows
echo ========================================================
echo.

python installer\build_setup.py

echo.
if %errorlevel% equ 0 (
    echo [SUCESSO] Instalador disponivel na pasta: instaladores\
) else (
    echo [ERRO] Falha ao gerar o instalador.
)
echo.
pause
