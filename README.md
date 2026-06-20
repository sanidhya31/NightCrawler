<div align="center">

# 🌙 NightCrawler

**Wake up to job applications that are already done.**

NightCrawler finds fresh werkstudent & internship jobs every night, ranks them by
real fit, and tailors a **resume + cover letter in English *and* German** for the
best matches — saved to your Drive and logged to a Google Sheet by morning.

*Built for [Claude Code](https://code.claude.com). It never auto-applies, and it
never invents facts about you.*

</div>

---

## ✨ What it does

```
   🔎 find            🧮 rank             ✍️ tailor           📥 deliver
 LinkedIn jobs  →  fit + fewest    →  resume + cover   →  Google Drive
 (via Apify)       applicants +       letter, EN + DE      + Google Sheet
                   recency            (honest, guarded)    (clickable links)
```

- **Honest by design** — a guard blocks any change to locked facts (employers,
  dates, education, contact). Tailoring only rewords summary, skills, and bullets.
- **Bilingual** — every resume and cover letter in English and German.
- **Ranked, not spammed** — newest + fewest applicants + best profile fit first;
  fluent-German-required roles are penalised if you're not fluent.
- **No repeats** — every job seen is remembered.
- **Backlog** — near-miss jobs are saved (links only) for you to promote.
- **Runs itself** — optional overnight schedule with self-retry.

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
