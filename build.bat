@echo off
echo ================================
echo Compilando Borderless Manager...
echo  - Modo: one-dir (sin extracción en memoria)
echo  - UPX desactivado
echo ================================

pyinstaller ^
  --noconfirm ^
  --onedir ^
  --windowed ^
  --noupx ^
  --icon "resources\icon.ico" ^
  --add-data "resources\icon.ico;resources" ^
  main.py ^
  --name BorderlessManager

if errorlevel 1 (
  echo.
  echo ERROR: Falló la compilación con PyInstaller
) else (
  echo.
  echo Compilación completada. Revisa la carpeta dist\BorderlessManager
)

pause
