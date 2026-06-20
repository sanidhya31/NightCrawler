# Tailoring Spec — how to tailor a resume to a job

This is the rulebook the tailoring step MUST follow for every job. The goal:
re-angle the resume toward the target role **without ever inventing facts**.

## Inputs
- `base/base-resume.json` — the source of truth (locked facts).
- A job description (title, company, responsibilities, keywords).

## Candidate positioning (keep the core intact)
Read the candidate's positioning from `base-resume.json` — its `summary` and the
optional `_targeting` field (background, skill levels, and the type of roles they
target). Lead with the strengths that fit the target; never overstate a skill level
beyond what the base supports.

## Outputs (per job)
- `resume.tailored.json` — English tailored resume.
- `resume.tailored.de.json` — German translation of the tailored resume.
- Both rendered to PDF via `scripts/build_resume.py`.
- Both MUST pass `scripts/guard.py` before they count as done.

## What you MAY change
1. **Summary** — rewrite to lead with the angle the job wants. Stay truthful to the
   base facts. ~3-5 sentences.
2. **Bullet wording and order** — reword bullets to surface relevant skills first;
   reorder so the most relevant bullets lead. **Keep the content substantial and
   transparent — do NOT aggressively cut detail.** Keep essentially all real
   bullets for each role/project (you may drop at most 1 clearly-irrelevant one);
   reword for angle, but preserve the depth and specifics. A reader should see the
   full picture of what was done, not a thinned-out version.
3. **Skills grouping/labels/order** — regroup and relabel skill categories to match
   the job's language (e.g. "Project and Delivery" for a PM role). You may surface
   skills that are genuinely implied by the base resume. Do not invent tools the
   candidate has never used.
4. **Project selection/order and stack labels** — pick the most relevant projects
   first; relabel the stack line to highlight relevant tech (still truthful).

## What you MUST NOT change (LOCKED)
These must be byte-identical to `base-resume.json`:
- `candidate.name`, `email`, `phone`, `linkedin`, `github`, `location`, `photo`
- Every `workExperience[].company`, `role`, `dates`, `location`
- Every `education[]` entry (degree, institution, location, dates)
- Never add a job, employer, degree, or date that is not in the base.
- Never inflate metrics (the "~40%" stays "~40%", never becomes "60%").
- Never claim a language level or skill the base does not support.

## Bullet ids
Keep the base `id` on each bullet you reuse (e.g. `exp_001_b005`). This lets the
guard confirm you only used real bullets. Do not create new ids.

## Tone
Mix of professional + clear + slightly punchy. No fluff, no buzzword salad.
Use small hyphens "-", never em-dashes. Avoid unnecessary hyphenation.

## German version (`.de.json`)
- Translate `summary`, bullet `text`, skill category labels, skill values where
  natural, and language `level` (Fluent→Fließend, Beginner→Grundkenntnisse,
  Native→Muttersprache) into natural professional German.
- KEEP locked facts identical and in original form: company names, role titles,
  dates, locations, degree names, contact details. (Do NOT translate "Analyst",
  "M.Sc. Data Science", company names, etc.)
- Keep technical terms that German tech CVs normally keep in English
  (Python, Machine Learning, Stakeholder, Reporting, etc.).

## Definition of done
1. `resume.tailored.json` and `resume.tailored.de.json` both written.
2. `python scripts/guard.py base/base-resume.json <tailored.json>` → PASS for both.
3. Both PDFs render without error.
