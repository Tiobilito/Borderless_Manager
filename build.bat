@echo off
echo Compilando Borderless Manager...
pyinstaller --noconfirm --onefile --windowed --add-data "resources/icon.ico;resources" main.py --name BorderlessManager
pause
