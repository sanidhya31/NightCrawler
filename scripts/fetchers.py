"""
fetchers.py  -  per-source job fetchers, each normalizing to our common schema.

Common job dict:
  {source, title, companyName, location, descriptionText, link, postedAt, applicantsCount}

Sources: linkedin / indeed / xing  (Apify, need token) and arbeitnow (free API).
"""

import re
import datetime
import urllib.parse
import requests

LINKEDIN_ACTOR = "curious_coder~linkedin-jobs-scraper"
INDEED_ACTOR = "borderline~indeed-scraper"
XING_ACTOR = "shahidirfan~Xing-Jobs-Scraper"


def _norm(source, title, company, location, desc, link, posted, applicants):
    return {
        "source": source, "title": title, "companyName": company,
        "location": location, "descriptionText": desc or "", "link": link,
        "postedAt": posted, "applicantsCount": applicants,
    }


def _apify(actor, token, body):
    r = requests.post(
        f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items",
        params={"token": token}, json=body, timeout=600,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"{actor} {r.status_code}: {r.text[:200]}")
    return r.json()


def _strip_html(s):
    return re.sub(r"<[^>]+>", " ", str(s or "")).strip()


def _int_or_none(v):
    return int(v) if str(v).isdigit() else None


def fetch_linkedin(search, count, token):
    kw = " OR ".join(search["keywords"])
    days = search.get("posted_within_days", 7)
    url = "https://www.linkedin.com/jobs/search/?" + urllib.parse.urlencode({
        "keywords": kw, "location": search.get("location", "Germany"),
        "f_TPR": f"r{days * 86400}", "sortBy": "DD",
    })
    data = _apify(LINKEDIN_ACTOR, token, {"urls": [url], "count": max(10, count), "scrapeCompany": False})
    return [_norm("linkedin", j.get("title"), j.get("companyName"), j.get("location"),
                  j.get("descriptionText", ""), j.get("link"), j.get("postedAt"),
                  _int_or_none(j.get("applicantsCount"))) for j in data]


def fetch_indeed(search, count, token, query=None):
    q = query or "werkstudent data analyst"
    body = {"country": "de", "query": q, "location": search.get("location", "Germany"),
            "maxRows": max(10, count), "fromDays": str(search.get("posted_within_days", 7))}
    out = []
    for j in _apify(INDEED_ACTOR, token, body):
        loc = j.get("location")
        loc = ", ".join(filter(None, [loc.get("city"), loc.get("country")])) if isinstance(loc, dict) else str(loc or "")
        out.append(_norm("indeed", j.get("title"), j.get("companyName"), loc,
                         j.get("descriptionText", ""), j.get("jobUrl"),
                         str(j.get("datePublished", ""))[:10], _int_or_none(j.get("numOfCandidates"))))
    return out


def fetch_xing(search, count, token, query=None):
    q = query or "werkstudent data"
    body = {"keyword": q, "location": search.get("location", "Germany"), "results_wanted": max(10, count)}
    out = []
    for j in _apify(XING_ACTOR, token, body):
        out.append(_norm("xing", j.get("title"), j.get("company"), j.get("location"),
                         j.get("description_text", ""), j.get("url"),
                         str(j.get("date_posted", ""))[:10], None))
    return out


def fetch_arbeitnow(search, count, token=None, query=None):
    """Free API, returns everything; we filter locally by keywords / werkstudent."""
    data = requests.get("https://www.arbeitnow.com/api/job-board-api", timeout=60).json().get("data", [])
    kws = [k.lower() for k in search.get("keywords", [])]
    levels = ["werkstudent", "working student", "praktikum", "praktikant", "intern"]
    out = []
    for j in data:
        title = str(j.get("title", "")).lower()
        text = title + " " + _strip_html(j.get("description", "")).lower()
        if not (any(k in text for k in kws) or any(w in title for w in levels)):
            continue
        posted = ""
        try:
            posted = datetime.datetime.fromtimestamp(int(j.get("created_at", 0))).date().isoformat()
        except Exception:
            pass
        out.append(_norm("arbeitnow", j.get("title"), j.get("company_name"), j.get("location"),
                         _strip_html(j.get("description", "")), j.get("url"), posted, None))
        if len(out) >= count:
            break
    return out


FETCHERS = {
    "linkedin": fetch_linkedin,
    "indeed": fetch_indeed,
    "xing": fetch_xing,
    "arbeitnow": fetch_arbeitnow,
}
