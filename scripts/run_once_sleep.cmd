@echo off
REM One-time launcher: run the nightly pipeline, then put the laptop to sleep.
call "D:\Projects\claude stuff\scripts\run_nightly.cmd"
echo ==== sleeping laptop %date% %time% ==== >> "D:\Projects\claude stuff\runs\nightly.log"
rundll32.exe powrprof.dll,SetSuspendState 0,1,0
