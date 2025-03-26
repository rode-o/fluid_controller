@echo off

rem -------------------------------------------------------------------
rem Activate your conda environment. Make sure "MyCondaEnv" exists.
rem If not needed or it doesn't exist, you can remove or change this line.
rem -------------------------------------------------------------------
call conda activate MyCondaEnv

echo Building Controller_Interface.exe...

pyinstaller ^
  --name=Controller_Interface ^
  --icon="src\controller_interface\resources\salvus_logo_white.ico" ^
  --add-data="src\controller_interface\resources\salvus_full_logo_color.png;resources" ^
  --add-data="src\controller_interface\gui\themes\common.qss;controller_interface/gui/themes" ^
  --noconsole ^
  --onefile ^
  --clean ^
  --noconfirm ^
  src\controller_interface\main.py

pause
