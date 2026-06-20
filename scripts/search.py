"""
search.py  -  pull LinkedIn jobs via Apify (with token-rotation fallback)

Builds a LinkedIn jobs search URL from config.json, runs the Apify actor
curious_coder/linkedin-jobs-scraper, and saves raw results to:
    runs/<YYYY-MM-DD>/jobs.json

Token rotation: reads APIFY_TOKENS (comma-separated) from .env and tries each
in order; if one is out of monthly credits, it falls back to the next.

Usage:
  python search.py                 # uses today's date folder
  python search.py 2026-06-19      # explicit run date
"""

import sys
import json
import datetime
import urllib.parse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.json"
ENV = ROOT / ".env"
ACTOR = "curious_coder~linkedin-jobs-scraper"


def load_tokens():
    tokens = []
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("APIFY_TOKENS="):
            tokens = [t.strip() for t in line.split("=", 1)[1].split(",") if t.strip()]
    if not tokens:
        raise SystemExit("No APIFY_TOKENS in .env")
    return tokens


def build_url(search):
    kw = " OR ".join(search["keywords"])
    days = search.get("posted_within_days", 7)
    params = {
        "keywords": kw,
        "location": search.get("location", "Germany"),
        "f_TPR": f"r{days * 86400}",   # posted within N days
        "sortBy": "DD",                # most recent first
    }
    return "https://www.linkedin.com/jobs/search/?" + urllib.parse.urlencode(params)


def run_actor(token, url, count):
    body = {"urls": [url], "count": count, "scrapeCompany": False}
    r = requests.post(
        f"https://api.apify.com/v2/acts/{ACTOR}/run-sync-get-dataset-items",
        params={"token": token}, json=body, timeout=600,
    )
    return r


def is_credit_error(resp):
    # 402 / usage-limit style errors -> rotate to next token
    if resp.status_code in (402, 403):
        return True
    try:
        msg = json.dumps(resp.json()).lower()
        return any(k in msg for k in ["usage", "credit", "limit exceeded", "monthly"])
    except Exception:
        return False


def main():
    run_date = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    search = cfg["search"]
    count = max(10, int(search.get("fetch_count", 50)))
    url = build_url(search)
    print(f"Search URL: {url}")
    print(f"Fetching up to {count} jobs...")

    tokens = load_tokens()
    data = None
    for i, tok in enumerate(tokens, 1):
        print(f"  trying token {i}/{len(tokens)}...")
        resp = run_actor(tok, url, count)
        if resp.status_code in (200, 201):
            data = resp.json()
            print(f"  OK on token {i}")
            break
        if is_credit_error(resp):
            print(f"  token {i} out of credits, rotating...")
            continue
        # other error: show and stop
        raise SystemExit(f"Actor error (token {i}): {resp.status_code} {resp.text[:300]}")

    if data is None:
        raise SystemExit("All tokens exhausted or failed.")

    out_dir = ROOT / "runs" / run_date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "jobs.json"
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(data)} jobs -> {out_file}")


if __name__ == "__main__":
    main()
