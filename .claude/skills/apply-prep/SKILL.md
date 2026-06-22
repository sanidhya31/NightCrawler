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

### 3. Build cluster resumes (the library — REUSE first, generate only if needed)
Read `runs/<date>/tailor.json` (top jobs; each has `cluster`, `sources`, and its JD).
Collect the DISTINCT clusters among the top jobs. For EACH distinct cluster:
  - Check whether it needs (re)generating:
    ```
    ./.venv/Scripts/python.exe scripts/library.py --need "<Cluster Name>"
    ```
    Exit 0 = generate it. Exit 1 = a fresh one already exists -> REUSE, skip generation.
  - If it needs generating: following `base/tailoring-spec.md`, tailor
    `base/base-resume.json` toward the CLUSTER ANGLE (use the cluster's theme/keywords
    from config as the target — NOT one company). Keep ALL bullets (full, descriptive
    — do not trim). Write `library/<slug>.tailored.json` (EN) and
    `library/<slug>.tailored.de.json` (DE, `"lang":"de"`), guard both, render both
    (`build_resume.py library/<slug>.tailored.json library/<slug>` and the `.de`),
    then `./.venv/Scripts/python.exe scripts/library.py --record "<Cluster Name>"`.
  This makes at most ~4 resumes for all 10 jobs (the big token saver). A resume is
  reused across days until `base-resume.json` changes (the library auto-detects).

### 4. Deliver each top job — STRICT one-at-a-time, with per-job resume tweaks
For EACH job in tailor.json, in rank order, FULLY deliver before starting the next
(if the token limit hits mid-run, every delivered job is complete in the sheet):
  a. slug = `<company>-<short-title>`. Make `runs/<date>/<slug>/` only (NO G Drive folder).
     Write `job.md` (title, company, link(s), JD, cluster, why matched).
  b. PER-JOB resume tweak (start from cluster base, layer job-specific adjustments):
     - Get the cluster base via `library.py --get "<cluster>"` — read the cluster's
       `.tailored.json` as the STARTING POINT (not base-resume.json).
     - Apply LIGHT per-job tweaks following `base/tailoring-spec.md`:
         * Reorder bullets within each role so the most JD-relevant ones lead.
         * Tweak the summary (~3-5 sentences) to reflect this specific role's angle.
         * Reorder skills to surface the most relevant group/keywords first.
         * Do NOT drop bullets, invent facts, or change any locked fields.
     - Write the tweaked EN version to `runs/<date>/<slug>/resume.tailored.json`
       and the DE version to `runs/<date>/<slug>/resume.tailored.de.json`.
     - Guard BOTH: `scripts/guard.py base/base-resume.json <tweaked.json>` → must PASS.
     - Render BOTH: `build_resume.py runs/<date>/<slug>/resume.tailored.json
       runs/<date>/<slug>/resume` and the `.de` variant.
     - The library cluster files are NEVER modified — they stay as the reusable base.
  c. Generate a per-JOB cover letter (this company + role swapped in, personal touch),
     EN and/or DE, via build_coverletter.py into `runs/<date>/<slug>/cover_letter.pdf`.
  d. Log ONE row for this job via `tracker.py --job runs/<date>/<slug>/job-row.json`:
     - `job_link` = raw URL only (no "LinkedIn:" / "Indeed:" prefix). If multiple
       sources, use the best single URL.
     - `role` = the job title (NOT "title" — tracker reads the "role" key).
     - `resume_en` / `resume_de` / `cover_letter` = leave blank for now; step 4b fills them.
     - `notes` = cluster name + [WATCHLIST] if job.watchlist.

### 4. Write the morning digest
Create `runs/<date>/digest.md`:
  - Top section: the tailored jobs (ranked), each with company, role, why-matched,
    applicantsCount, postedAt, links to the local PDFs and the job posting.
    Mark any [WATCHLIST] company (from config.filters.watchlist_flag) clearly.
  - Bottom section: the remaining kept-but-not-tailored jobs as a quick list
    (title, company, link) in case the user wants more.

### 4b. Upload PDFs to cloud + write Drive links into sheet
After all jobs are delivered, upload every job's PDFs via the Drive API (no Desktop
sync needed) and write clickable public links directly into the sheet:
```
./.venv/Scripts/python.exe scripts/upload_public.py <YYYY-MM-DD>
```
This uploads to the service account's own Drive space, makes each file publicly
viewable, and updates Resume EN / Resume DE / Cover Letter columns with
`=HYPERLINK(...)` formulas. No G Drive Desktop, no sync lag.

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
