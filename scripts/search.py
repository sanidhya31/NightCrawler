"""
search.py  -  multi-source job pull (LinkedIn + Indeed + XING + Arbeitnow)

Fetches each enabled source in config.search.sources, normalizes everything to the
common schema, dedupes the SAME job across sources (fuzzy company+title), and saves
to runs/<date>/jobs.json. Each job keeps a `sources` list with one apply-link per
site it was found on.

Token rotation: tries each APIFY_TOKENS entry; on a credit/usage error, falls back
to the next. Arbeitnow needs no token.

Usage: python search.py [YYYY-MM-DD]
"""

import sys
import re
import json
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetchers import FETCHERS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.json"
ENV = ROOT / ".env"


def load_tokens():
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("APIFY_TOKENS="):
            return [t.strip() for t in line.split("=", 1)[1].split(",") if t.strip()]
    return []


def is_credit_error(msg):
    m = str(msg).lower()
    return any(k in m for k in ["usage", "credit", "limit exceeded", "monthly", " 402", " 403"])


def fetch_source(src, search, tokens):
    fn = FETCHERS[src["type"]]
    count = int(src.get("count", 20))
    query = src.get("query")
    kwargs = {"query": query} if query is not None else {}
    if src["type"] == "arbeitnow":
        return fn(search, count, None)
    # apify sources: rotate tokens
    last = None
    for i, tok in enumerate(tokens, 1):
        try:
            return fn(search, count, tok, **kwargs) if kwargs else fn(search, count, tok)
        except Exception as e:
            last = e
            if is_credit_error(e):
                print(f"    token {i} out of credits, rotating...")
                continue
            raise
    raise RuntimeError(f"all tokens failed: {last}")


def norm_key(j):
    def clean(s):
        return re.sub(r"[^a-z0-9]", "", str(s or "").lower())
    title = clean(j.get("title"))[:30]
    comp = clean(j.get("companyName"))[:20]
    return f"{comp}|{title}"


def dedupe(jobs):
    """Merge same job across sources; keep richest description, collect all links."""
    merged = {}
    for j in jobs:
        k = norm_key(j)
        if k not in merged:
            j["sources"] = [{"source": j["source"], "link": j.get("link")}]
            merged[k] = j
        else:
            m = merged[k]
            have = {s.get("link") for s in m["sources"]}
            if j.get("link") not in have:
                m["sources"].append({"source": j["source"], "link": j.get("link")})
            if len(j.get("descriptionText", "")) > len(m.get("descriptionText", "")):
                m["descriptionText"] = j["descriptionText"]
            if j.get("applicantsCount") is not None and m.get("applicantsCount") is None:
                m["applicantsCount"] = j["applicantsCount"]
    return list(merged.values())


def main():
    run_date = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    search = cfg["search"]
    tokens = load_tokens()
    sources = [s for s in search.get("sources", []) if s.get("enabled", True)]

    all_jobs = []
    for src in sources:
        print(f"  source '{src['name']}' (count {src.get('count')})...")
        try:
            got = fetch_source(src, search, tokens)
            print(f"    got {len(got)}")
            all_jobs.extend(got)
        except Exception as e:
            print(f"    FAILED: {e}")

    deduped = dedupe(all_jobs)
    out_dir = ROOT / "runs" / run_date
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "jobs.json").write_text(json.dumps(deduped, indent=2, ensure_ascii=False), encoding="utf-8")
    multi = sum(1 for j in deduped if len(j["sources"]) > 1)
    print(f"Total {len(all_jobs)} fetched -> {len(deduped)} unique ({multi} found on 2+ sites). "
          f"-> {out_dir / 'jobs.json'}")


if __name__ == "__main__":
    main()
