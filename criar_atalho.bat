@echo off
setlocal
cd /d "%~dp0"
if not exist "dist\Nexo.exe" (
  echo Primeiro execute build_windows.bat.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws=New-Object -ComObject WScript.Shell; $s=$ws.CreateShortcut([Environment]::GetFolderPath('Desktop')+'\Nexo.lnk'); $s.TargetPath=(Join-Path $PWD 'dist\Nexo.exe'); $s.WorkingDirectory=(Join-Path $PWD 'dist'); $s.IconLocation=(Join-Path $PWD 'nexo_icon.ico'); $s.Description='Nexo - Gestão de Custos e Precificação'; $s.Save()"
echo Atalho Nexo criado na Area de Trabalho.
pause
