@echo off
title Nexo - Subir para o GitHub
cd /d "%~dp0"
set "PATH=C:\Users\Leonan\AppData\Local\Programs\Git\cmd;C:\Users\Leonan\AppData\Local\Programs\Git\mingw64\bin;%PATH%"

echo ========================================================
echo   Nexo - Enviando atualizacoes para o GitHub
echo ========================================================
echo.
echo Executando: git push origin main
echo.

git push origin main

echo.
if %errorlevel% equ 0 (
    echo [SUCESSO] Atualizacoes enviadas para o GitHub com sucesso!
) else (
    echo [AVISO] Se uma janela do navegador abriu, complete o login do GitHub nela.
)
echo.
pause
