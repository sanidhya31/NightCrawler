---
name: apply-prep
description: Overnight job-application prep for werkstudent/internship roles in Germany. Pulls LinkedIn jobs via Apify, ranks them, tailors the resume (EN+DE) per job, logs everything to the Google Sheet tracker, and writes a morning digest. Use when the user says "run apply-prep", "find jobs", "do the overnight run", or on the nightly schedule.
---

# apply-prep — overnight job application prep

Prepares tailored applications so the user wakes up and just clicks apply.
**Never auto-applies.** The user applies manually.

## Environment
- Run everything with the D-drive venv: `./.venv/Scripts/python.exe`
- Project root: `D:\Projects\claude stuff`
- All paths relative to project root. Everything stays on D drive.

## Inputs (already configured)
- `config.json` — search keywords, filters, ranking rules, volume cap, Google sheet.
- `base/base-resume.json` — source of truth (locked facts).
- `base/tailoring-spec.md` — the rules for tailoring. READ THIS before tailoring.
- `.env` — Apify tokens (rotation handled by search.py).
- `.secrets/google-key.json` — Sheets service account.

## Steps (run in order)

### 0a. Skip if already done
If `runs/<today>/DONE` exists, today's run already completed — STOP immediately,
do nothing. (The launcher also checks this, but double-check here.)

### 0. Roll over the sheet (start of run)
```
./.venv/Scripts/python.exe scripts/tracker.py --rollover <YYYY-MM-DD>
```
Archives older daily tabs into `Past` and deletes them; creates today's tab.
The `Past` and `Backlog` tabs are preserved.

### 1. Pull jobs
```
./.venv/Scripts/python.exe scripts/search.py <YYYY-MM-DD>
```
Saves `runs/<date>/jobs.json`. Token rotation is automatic.

### 2. Filter + rank
```
./.venv/Scripts/python.exe scripts/rank.py <YYYY-MM-DD>
```
Saves `runs/<date>/ranked.json`. Each job has a `bucket`:
  - `"tailor"`  = top picks (count = config.filters.volume_cap) -> full resume + letter
  - `"backlog"` = next tier (config.filters.backlog_cap) -> Backlog tab, no resume
Scoring blends profile-match + fewest applicants + recency, minus a penalty for
fluent-German-required roles. No-reposts is automatic (seen_links.txt).

### 2b. Log the backlog (link + score only, no resume)
```
./.venv/Scripts/python.exe scripts/tracker.py --backlog-from runs/<date>/ranked.json
```

### 3. Tailor each top job — STRICT one-at-a-time delivery
Read `base/tailoring-spec.md` and `base/base-resume.json` first.

**CRITICAL ORDERING:** process jobs ONE AT A TIME and fully DELIVER each before
starting the next. For each job do steps a-i completely (tailor -> guard -> render
-> copy to Drive -> log to the sheet) and only THEN move to the next job. Never
batch (do not tailor several, then render several, then log several). This way, if
the token/session limit is hit mid-run, every job already started is fully finished
and in the sheet — the user always has complete results in hand.

Read `runs/<date>/tailor.json` (ONLY the top jobs, with their descriptions — do NOT
read ranked.json for tailoring; it's the slim/backlog file and loading it wastes
tokens). For EACH job in tailor.json, in order:

  a. Make folder `runs/<date>/<slug>/` where slug = `<company>-<short-title>`
     (lowercase, hyphens, no special chars).
  b. Write `job.md` with title, company, location, link, applicantsCount,
     postedAt, the JD (descriptionText), and a one-line "why it matched".
  c. Produce **two** tailored resumes following tailoring-spec.md, using the job's
     `descriptionText` as the target:
       - `resume.tailored.json`      (English)
       - `resume.tailored.de.json`   (German; include `"lang": "de"`)
     Change ONLY summary, bullet wording/order, skills grouping, project order.
     Keep all locked facts byte-identical. Keep base bullet ids.
  d. Guard BOTH (must PASS — fix and retry if it fails):
     ```
     ./.venv/Scripts/python.exe scripts/guard.py base/base-resume.json runs/<date>/<slug>/resume.tailored.json
     ./.venv/Scripts/python.exe scripts/guard.py base/base-resume.json runs/<date>/<slug>/resume.tailored.de.json
     ```
  e. Render BOTH to PDF:
     ```
     ./.venv/Scripts/python.exe scripts/build_resume.py runs/<date>/<slug>/resume.tailored.json    runs/<date>/<slug>/resume
     ./.venv/Scripts/python.exe scripts/build_resume.py runs/<date>/<slug>/resume.tailored.de.json runs/<date>/<slug>/resume.de
     ```
  f. Generate cover letters per `base/cover-letter-template.md`: write `cover.json`
     (EN) and `cover.de.json` (DE) — letterhead pulled from base, body tailored to
     the job, honest (German = beginner). Then render:
     ```
     ./.venv/Scripts/python.exe scripts/build_coverletter.py runs/<date>/<slug>/cover.json    runs/<date>/<slug>/cover-letter
     ./.venv/Scripts/python.exe scripts/build_coverletter.py runs/<date>/<slug>/cover.de.json runs/<date>/<slug>/cover-letter.de
     ```
  g. Copy outputs to Drive (if config.drive.enabled): copy this job's resume PDFs
     and cover-letter PDFs to `<config.drive.dir>/<date>/<slug>/` so Drive Desktop
     syncs them. Keep the same per-job folder structure.
  h. Get clickable Drive links (if Drive API is set up): after the copy, fetch
     web links (allow a short retry for sync):
     ```
     ./.venv/Scripts/python.exe scripts/drive_links.py <date> <slug>
     ```
     Use the returned URLs for resume_en/resume_de/cover_letter in the row json.
     If links aren't available yet, fall back to the Drive file paths.
  i. Log the job:
     Write a row json (date, company, role, job_link, resume_en, resume_de,
     cover_letter [use Drive links from step h], match_score, status "New",
     notes incl. [WATCHLIST] if job.watchlist) then:
     ```
     ./.venv/Scripts/python.exe scripts/tracker.py --job runs/<date>/<slug>/job-row.json
     ```

### 4. Write the morning digest
Create `runs/<date>/digest.md`:
  - Top section: the tailored jobs (ranked), each with company, role, why-matched,
    applicantsCount, postedAt, links to the local PDFs and the job posting.
    Mark any [WATCHLIST] company (from config.filters.watchlist_flag) clearly.
  - Bottom section: the remaining kept-but-not-tailored jobs as a quick list
    (title, company, link) in case the user wants more.

### 4b. Refresh Drive links (clickable URLs in the sheet)
After all jobs are delivered, Drive Desktop has had time to sync. Upgrade the sheet's
Resume/Cover columns from local paths to clickable Drive web links:
```
./.venv/Scripts/python.exe scripts/refresh_links.py <YYYY-MM-DD>
```
If it reports nothing found yet (Drive still syncing), wait ~1 min and run it again.

### 5. Summarize to the user
Report: how many found / kept / tailored, any watchlist hits, where the digest is,
and confirm the Google Sheet was updated.

### 6. Mark done (CRITICAL for the self-retry schedule)
Only after EVERY tailor-bucket job has been rendered, copied, and logged
successfully, create an empty marker file `runs/<today>/DONE`.
If the run was cut short (e.g. token/usage limit hit before all jobs finished),
do NOT create DONE — leave it missing so the next scheduled repeat resumes the
remaining jobs (dedup prevents repeats).

## Hard rules
- Never invent facts, inflate metrics, or change locked fields. The guard enforces
  this — if it fails, the tailoring is wrong, not the guard.
- Never auto-apply or submit anything.
- Keep all work on the D drive.
- If Apify returns 0 jobs (bad night), write a digest saying so and stop gracefully.
