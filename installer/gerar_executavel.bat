@echo off
title Nexo - Gerar Executavel Windows (.exe)
cd /d "%~dp0\.."

echo ========================================================
echo   Nexo - Empacotando Executavel Windows (PyInstaller)
echo ========================================================
echo.

python -m pip install --upgrade pyinstaller pillow

python -m PyInstaller --noconfirm --onedir --windowed ^
    --name "Nexo" ^
    --icon "nexo_icon.ico" ^
    --add-data "ui_assets;ui_assets" ^
    --add-data "nexo_icon.ico;." ^
    --add-data "nexo_icon.png;." ^
    --add-data "nexo_logo.png;." ^
    main.py

echo.
if %errorlevel% equ 0 (
    echo [SUCESSO] Executavel gerado em: dist\Nexo\Nexo.exe
    echo O banco de dados da versao instalada sera salvo automaticamente em %%LOCALAPPDATA%%\Nexo
) else (
    echo [ERRO] Falha ao gerar o executavel.
)
echo.
pause

