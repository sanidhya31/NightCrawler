---
name: apply-prep-setup
description: Guided first-time setup for NightCrawler / apply-prep. Walks a new user through Python deps, Apify, Google Sheet + Drive, their resume, and the schedule. Use when the user says "set up apply-prep", "set up NightCrawler", or it's their first run and config is missing.
---

# apply-prep-setup — guided setup

Help a NON-technical user get NightCrawler running on their machine. Go ONE step at
a time, explain in plain language, run what you can for them, and STOP to ask when
you need something only they can provide (accounts, keys, browser logins).

Keep everything on the user's preferred drive (ask; default to the project's drive,
never bloat C: if they say otherwise).

## Pre-flight
- Confirm OS and that Python 3.11+ is installed (`python --version`).
- Confirm the project folder location.

## Step 1 — Python environment + dependencies
```
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m playwright install chromium
```
On Windows, point Playwright's Chromium off C: if the user wants:
set `PLAYWRIGHT_BROWSERS_PATH` to a project-local `.playwright` before installing
(build_resume.py already defaults to `<project>/.playwright`).

## Step 2 — Apify token (job data)
Ask the user to sign up at apify.com (free) and copy their API token
(Settings -> Integrations). Then:
```
cp .env.example .env
```
and put the token in `.env` as `APIFY_TOKENS=...`. Verify:
```
.venv\Scripts\python -c "import requests,os; ... GET https://api.apify.com/v2/users/me?token=<token>"
```
(confirm HTTP 200).

## Step 3 — Google Sheet + Drive
Walk them through (link them to console.cloud.google.com):
1. Create a project; enable **Google Sheets API** and **Drive API**.
2. Create a **Service Account**, download its JSON key to `.secrets/google-key.json`.
3. Create a Google Sheet; share it (Editor) with the service-account email
   (read it from the key file's `client_email`).
4. Install Google Drive for Desktop; share the chosen Drive folder with the same
   email and set "Anyone with link -> Viewer".
Then `cp config.example.json config.json` and fill `sheet_id` and `drive.dir`.
Verify with: `.venv\Scripts\python scripts/tracker.py --check`.

## Step 4 — Their resume (the source of truth)
```
cp base/base-resume.example.json base/base-resume.json
```
Then either let them paste their resume and YOU fill base-resume.json accurately
(locked facts = their real employers/dates/education/contact), or have them edit it.
Add their photo as `base/photo.png` (optional). Do a test render:
```
.venv\Scripts\python scripts/build_resume.py base/base-resume.json runs/preview/resume
```
and show them the PDF. Adjust accent color / photo size in `scripts/build_resume.py`
to taste.

## Step 5 — Filters & positioning
Walk them through `config.json` filters (keywords, location, volume_cap, weights,
german_penalty) and `base/tailoring-spec.md` (their target roles / positioning).

## Step 6 — Claude Code CLI (for unattended runs only)
If they want overnight scheduling:
- Install the native CLI (no Node): `irm https://claude.ai/install.ps1 | iex`
- If it can't find a shell, set `CLAUDE_CODE_GIT_BASH_PATH` to their Git bash.exe
  in `.claude/settings.json` (create from the scoped allowlist pattern).
- They run `claude` -> `/login` once.
- Copy `scripts/run_nightly.example.cmd` -> `scripts/run_nightly.cmd`, set the git
  bash path inside, and register a Task Scheduler job (see README / SETUP).

## Step 7 — First run
Offer to do a manual run now: invoke the **apply-prep** skill. Show them the digest,
the sheet, and the Drive files. Done.

## Rules
- Never commit or print secrets. `.env` and `.secrets/` are gitignored.
- Don't invent the user's resume facts — ask.
- Create machine-specific files (config.json, .env, base-resume.json, settings.json,
  run_nightly.cmd) locally; these are gitignored and must NOT be pushed.
