@echo off
REM ============================================================
REM  NightCrawler nightly launcher (portable template)
REM  Copy to run_nightly.cmd (the setup skill does this for you).
REM  Runs the whole pipeline headless via the Claude Code CLI.
REM ============================================================

cd /d "%~dp0.."

REM Point this at your Git-for-Windows bash.exe if needed:
if not defined CLAUDE_CODE_GIT_BASH_PATH set "CLAUDE_CODE_GIT_BASH_PATH=C:\Program Files\Git\bin\bash.exe"

set "CLAUDE=%USERPROFILE%\.local\bin\claude.exe"
if not exist "%CLAUDE%" set "CLAUDE=claude"

REM Skip if today already completed
".venv\Scripts\python.exe" scripts\should_run.py
if errorlevel 1 (
  echo %date% %time% - already done today, skipping >> "runs\nightly.log"
  exit /b 0
)

echo. >> "runs\nightly.log"
echo ==== run start %date% %time% ==== >> "runs\nightly.log"

"%CLAUDE%" -p "Run the apply-prep skill for today, following .claude/skills/apply-prep/SKILL.md exactly. As the final step, when all tailored jobs are logged to the sheet, create an empty marker file at runs/<today>/DONE." --model sonnet >> "runs\nightly.log" 2>&1

echo ==== run end %date% %time% (exit %errorlevel%) ==== >> "runs\nightly.log"
