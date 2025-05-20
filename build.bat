@echo off
echo Compilando Borderless Manager...
pyinstaller --noconfirm --onefile --windowed --add-data "resources/icon.png;resources" main.py --name BorderlessManager
pause
