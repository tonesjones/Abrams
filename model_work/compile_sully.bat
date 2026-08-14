@echo off
REM Compile Sully Abrams model via CSDK resourcecompiler (project CSDK only).
REM Does NOT modify Steam Deadlock files.
setlocal
set CSDK=C:\TestCode\Abrams\tools\Reduced_CSDK_12
set BIN=%CSDK%\game\bin_tools\win64
set GAME=%CSDK%\game\citadel
set VMDL=%CSDK%\content\citadel_addons\sully_abrams\models\heroes_wip\abrams\abrams.vmdl
set PATH=%BIN%;%SystemRoot%\System32;%SystemRoot%
cd /d %BIN%
echo Compiling %VMDL%
resourcecompiler.exe -game "%GAME%" -f -nop4 "%VMDL%"
echo Exit code %ERRORLEVEL%
if exist "%CSDK%\game\citadel_addons\sully_abrams\models\heroes_wip\abrams\abrams.vmdl_c" (
  echo SUCCESS: compiled vmdl_c found
) else (
  echo FAILED: no vmdl_c - CSDK schema mismatch may need DepotDownloader update
  echo See https://deadlockmodding.pages.dev/modding-tools/csdk-12 Full Game Files section
)
pause
