@echo off
rem Activate your conda environment (optional if you always build from an activated environment)
rem call conda activate <your_env_name>

echo Building Controller_Interface.exe...
pyinstaller ^
  --name Controller_Interface ^
  --icon "src\controller_interface\resources\slavus_leaf_logo.ico" ^
  --add-data "src\controller_interface\resources\slavus_leaf_logo.ico;resources" ^
  --add-data "src\controller_interface\resources\slavus_leaf_logo.png;resources" ^
  --add-data "src\controller_interface\gui\themes\common.qss;controller_interface/gui/themes" ^
  --noconsole ^
  --onefile ^
  --clean ^
  --noconfirm ^
  src\controller_interface\main.py
pause
