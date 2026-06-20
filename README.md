<div align="center">

# 🌙 NightCrawler

**Wake up to job applications that are already done.**

NightCrawler finds fresh werkstudent & internship jobs every night from **multiple
job boards**, ranks them by real fit, **groups similar jobs and reuses one resume
per group**, and writes a **resume + cover letter in English *and* German** for the
best matches — saved to your Drive and logged to a Google Sheet by morning.

*Built for [Claude Code](https://code.claude.com). It never auto-applies, and it
never invents facts about you.*

</div>

---

## ✨ What it does

```
 🔎 find (4 sources)   🧮 rank+group        ♻️ reuse            📥 deliver
 LinkedIn · Indeed  →  fit + fewest    →  one resume per   →  Google Drive +
 XING · Arbeitnow      applicants +       work-cluster        Google Sheet
 (dedup same job)      recency + fit      (library cache)     (merged links)
```

- **Multi-source** — LinkedIn, Indeed, XING (via Apify) + Arbeitnow (free API). The
  same job found on several boards is merged into one row with all apply-links.
- **Honest by design** — a guard blocks any change to locked facts (employers,
  dates, education, contact). Tailoring only rewords summary, skills, and bullets.
- **Bilingual** — every resume and cover letter in English and German.
- **Ranked, not spammed** — newest + fewest applicants + best profile fit first;
  fluent-German-required roles are penalised if you're not fluent.
- **Reusable resumes (token-smart)** — jobs are grouped into work-clusters (e.g.
  Data, Automation, Software, Management-tech); each cluster reuses **one** resume.
  10 jobs typically need ~3-4 resumes, not 10.
- **No repeats** — every job seen is remembered.
- **Backlog** — near-miss jobs are saved (links only) and the closest ones are
  flagged red so you can promote them.
- **Runs itself** — optional overnight schedule with self-retry.

## 🏗️ Architecture

```
search.py     pull all sources -> normalize -> dedupe same job across boards
rank.py       drop old/over-applied/seen -> score (fit·0.5 + few-applicants·0.3
              + recency·0.2 - german-penalty) -> assign work-cluster -> top N
cluster.py    group jobs by work-similarity (title-weighted keyword match)
library.py    one reusable resume per cluster, cached on disk (manifest + hash)
build_resume / build_coverletter   JSON -> HTML -> pixel-accurate PDF (Chromium)
guard.py      verify locked facts are byte-identical before anything ships
tracker.py    Google Sheet: per-day tab + Past archive + Backlog (+ red near-miss)
drive_links / refresh_links        clickable Drive links in the sheet
```

## ♻️ Token-smart by design (reusable resumes)

The expensive step is writing resume text with the LLM. NightCrawler minimises it:

- **One resume per cluster, not per job.** Similar jobs share a resume, so 10 jobs
  cost ~3-4 generations instead of 10.
- **A disk-cached library.** Generated resumes are stored as files in `library/`
  with a `manifest.json`. Reusing one is a **file copy — zero LLM tokens**. The
  library is *not* held in the model's context; it costs nothing to "remember".
- **Reuse across days.** A resume made today is reused tomorrow for matching jobs.
  It is **only regenerated when you edit `base-resume.json`** (the manifest stores a
  hash of your base resume and auto-detects changes).
- **Per-job delivery.** Each job is tailored/copied and logged one at a time, so a
  token-limit cut-off still leaves every finished job complete in your sheet.
- Run tailoring on **Sonnet** (set in the launcher) to stay light on usage limits.

## 🚀 Setup in one line

Install [Claude Code](https://code.claude.com/docs/en/setup), clone this repo, open
it, and say:

> **"set up apply-prep"**

Claude walks you through everything (accounts, keys, your resume). Prefer to do it by
hand? See the manual steps below.

<details>
<summary><b>Manual setup</b></summary>

You'll need three free accounts: **Apify** (jobs), a **Google Cloud** service account
(Sheet + Drive), and **Claude Code** (the brain).

```bash
# 1. Python deps (local, no admin)
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m playwright install chromium

# 2. Secrets & config (fill in your values)
cp .env.example .env                       # Apify token
cp config.example.json config.json         # sheet id + drive folder
cp base/base-resume.example.json base/base-resume.json   # your real resume
```

Then enable the **Google Sheets + Drive APIs**, drop the service-account key at
`.secrets/google-key.json`, share your Sheet + Drive folder with its email, and run:

```bash
.venv\Scripts\python scripts/tracker.py --check        # verify Google
.venv\Scripts\python scripts/build_resume.py base/base-resume.json runs/preview/resume   # test PDF
```
</details>

## 🏃 Run it

| | |
|---|---|
| **Manually** | In Claude Code, say **"run apply-prep"** |
| **Overnight** | Register the scheduled launcher — see `SETUP.md` |

## 🎛️ Make it yours

| Change | Where |
|---|---|
| Keywords, filters, ranking weights, volume, schedule | `config.json` |
| Your facts (the source of truth) | `base/base-resume.json` |
| Resume design (colour, photo, layout) | `scripts/build_resume.py` |
| Cover-letter style | `base/cover-letter-template.md` |
| Tailoring rules & positioning | `base/tailoring-spec.md` |

## 🔒 Privacy

Your resume, photo, tokens, keys, sheet id, and all generated output are gitignored —
**nothing personal is ever committed.** Everyone runs it on their own data.

## ⚖️ Notes

- Uses your Claude subscription (no API cost). Heavy nights may hit usage limits; the
  schedule self-retries.
- Apify's free tier comfortably covers nightly use.
- You apply manually — NightCrawler prepares, it never submits.

<div align="center"><sub>Built with Claude Code 🤖</sub></div>
