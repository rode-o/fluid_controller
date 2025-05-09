@echo off
rem -------------------------------------------------------------------
rem Optional: switch into the env you normally run the GUI with.
rem Comment it out if you’re calling build.bat from an already-active env.
rem -------------------------------------------------------------------
call conda activate pid

rem -------------------------------------------------------------------
rem Make sure we’re sitting in the repo’s root (the folder that
rem contains *this* batch file).  %~dp0 expands to that directory.
rem -------------------------------------------------------------------
cd /d "%~dp0"

echo.
echo ===============================================================
echo   Building Controller_Interface.exe with PyInstaller …
echo ===============================================================
echo.

pyinstaller ^
  --name=Controller_Interface ^
  --icon="controller_interface\resources\salvus_logo_white.ico" ^
  --add-data="controller_interface\resources\salvus_full_logo_color.png;resources" ^
  --add-data="controller_interface\view\themes\common.qss;controller_interface/view/themes" ^
  --noconsole ^
  --onefile ^
  --clean ^
  --noconfirm ^
  controller_interface\main.py

echo.
echo Build finished.  The executable should be in the .\dist folder.
pause
