"""
rank.py  -  filter, dedupe (no reposts), score, and bucket jobs per config.json

Input:  runs/<date>/jobs.json   (from search.py)
Output: runs/<date>/ranked.json with each kept job scored and bucketed:
          bucket = "tailor"  -> top `volume_cap`  (full resume + cover letter)
          bucket = "backlog" -> next `backlog_cap` (Backlog tab, link + score only)

Pipeline:
  1. DROP if older than recency.hard_cutoff_days
  2. DROP if applicantsCount > applicants.max
  3. DROP if the job link was seen in any previous run (no reposts/repeats)
  4. SCORE = match*w + fewer-applicants*w + recency*w  - german_penalty (if fluent
     German required, since candidate is a beginner)
  5. FLAG watchlist companies (kept, not dropped)
  6. Sort by score; bucket top volume_cap as tailor, next backlog_cap as backlog
  7. Record all fetched links to runs/seen_links.txt so they never resurface

Usage:
  python rank.py [YYYY-MM-DD]
"""

import sys
import csv
import json
import datetime
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.json"
SEEN = ROOT / "runs" / "seen_links.txt"

sys.path.insert(0, str(ROOT / "scripts"))
from cluster import assign_cluster  # noqa: E402

GERMAN_REQ = [
    "fließend deutsch", "fliessend deutsch", "fließende deutsch", "fließendes deutsch",
    "verhandlungssicher", "sehr gute deutschkenntnisse", "muttersprache deutsch",
    "fluent german", "fluent in german", "native german", "german (fluent",
    "deutsch (fließend", "sehr gutes deutsch",
]


def days_old(posted, today):
    try:
        return (today - datetime.date.fromisoformat(str(posted)[:10])).days
    except Exception:
        return 9999


def load_seen():
    if SEEN.exists():
        return {l.strip() for l in SEEN.read_text(encoding="utf-8").splitlines() if l.strip()}
    return set()


def save_seen(links):
    SEEN.parent.mkdir(parents=True, exist_ok=True)
    existing = load_seen()
    new = existing | {l for l in links if l}
    SEEN.write_text("\n".join(sorted(new)), encoding="utf-8")


def fit_score(job, profile_kw):
    text = (str(job.get("title", "")) + " " + str(job.get("jobFunction", "")) + " "
            + str(job.get("descriptionText", ""))).lower()
    matched = sum(1 for k in profile_kw if k.lower() in text)
    return min(matched, 8) / 8.0, matched   # normalized 0..1, raw count


def german_required(job):
    text = (str(job.get("title", "")) + " " + str(job.get("descriptionText", ""))).lower()
    return any(p in text for p in GERMAN_REQ)


def main():
    run_date = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    today = datetime.date.fromisoformat(run_date)
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    f = cfg["filters"]

    jobs = json.loads((ROOT / "runs" / run_date / "jobs.json").read_text(encoding="utf-8"))
    seen = load_seen()

    cutoff = f["recency"]["hard_cutoff_days"]
    max_appl = f["applicants"]["max"]
    profile_kw = f.get("profile_keywords", [])
    clusters = f.get("clusters", [])
    w = f.get("weights", {"match": 0.5, "applicants": 0.3, "recency": 0.2})
    gp = f.get("german_penalty", 0.25)
    watch = [x.lower() for x in f.get("watchlist_flag", [])]
    cap = int(f.get("volume_cap", 10))
    backlog_cap = int(f.get("backlog_cap", 40))

    kept = []
    dropped = {"old": 0, "too_many_applicants": 0, "repost_or_seen": 0}
    all_links = []

    for j in jobs:
        link = str(j.get("link", "")).strip()
        all_links.append(link)
        d = days_old(j.get("postedAt"), today)
        appl = j.get("applicantsCount")
        appl = int(appl) if str(appl).isdigit() else None

        if d > cutoff:
            dropped["old"] += 1; continue
        if appl is not None and appl > max_appl:
            dropped["too_many_applicants"] += 1; continue
        if link and link in seen:
            dropped["repost_or_seen"] += 1; continue

        fit, raw = fit_score(j, profile_kw)
        appl_norm = (max_appl - appl) / max_appl if appl is not None else 0.5
        appl_norm = max(0.0, min(1.0, appl_norm))
        recency_norm = max(0.0, 1.0 - d / cutoff)
        ger = german_required(j)
        score = (w["match"] * fit + w["applicants"] * appl_norm
                 + w["recency"] * recency_norm) - (gp if ger else 0.0)

        company = str(j.get("companyName", ""))
        kept.append({
            "title": j.get("title"), "company": company, "location": j.get("location"),
            "link": link, "sources": j.get("sources", []),
            "postedAt": j.get("postedAt"), "applicantsCount": appl,
            "descriptionText": j.get("descriptionText", ""),
            "cluster": assign_cluster(j, clusters)[0],
            "watchlist": any(x in company.lower() for x in watch),
            "german_required": ger,
            "match_estimate": round(fit * 10, 1),
            "score": round(score, 3),
        })

    kept.sort(key=lambda x: x["score"], reverse=True)
    for i, x in enumerate(kept):
        x["bucket"] = "tailor" if i < cap else ("backlog" if i < cap + backlog_cap else "drop")

    out_dir = ROOT / "runs" / run_date
    # ranked.json: ALL kept but SLIM (no long descriptions) -> used for backlog + overview
    slim = [{k: v for k, v in x.items() if k != "descriptionText"} for x in kept]
    (out_dir / "ranked.json").write_text(json.dumps(slim, indent=2, ensure_ascii=False), encoding="utf-8")
    # tailor.json: ONLY the top jobs, WITH descriptions -> the skill reads only this,
    # so Claude never loads the other jobs' descriptions (big token saver).
    tailor = [x for x in kept if x["bucket"] == "tailor"]
    (out_dir / "tailor.json").write_text(json.dumps(tailor, indent=2, ensure_ascii=False), encoding="utf-8")
    out = out_dir / "ranked.json"
    save_seen(all_links)

    n_tailor = sum(1 for x in kept if x["bucket"] == "tailor")
    n_backlog = sum(1 for x in kept if x["bucket"] == "backlog")
    print(f"Input {len(jobs)} | kept {len(kept)} | dropped {dropped}")
    print(f"-> tailor {n_tailor}, backlog {n_backlog}. {out}")
    print("TOP (to tailor):")
    for x in kept[:cap]:
        flags = ("[WATCH]" if x["watchlist"] else "") + ("[DE-req]" if x["german_required"] else "")
        print(f"  score={x['score']:.2f} match={x['match_estimate']} appl={x['applicantsCount']} "
              f"{str(x['title'])[:40]:<42}{x['company'][:20]} {flags}")


if __name__ == "__main__":
    main()
