@echo off
echo Compilando BorderlessApp...
pyinstaller --noconfirm --onefile --windowed main.py --name Borderless_Fail
pause
