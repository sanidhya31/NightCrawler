"""
refresh_links.py  -  upgrade a date's sheet rows to clickable Google Drive links.

For each job folder of a run date, fetch the Drive web links (webViewLink) of the
synced PDFs and update that job's row (Resume EN / Resume DE / Cover letter columns)
in the date's sheet tab. Matches rows by the LinkedIn job link (column D).

Run this at the END of a nightly run (after Drive Desktop has synced), or manually
anytime. Safe to re-run.

Usage: python refresh_links.py <YYYY-MM-DD>
"""

import sys, re, json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from drive_links import get_links  # noqa: E402

date = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
run_dir = ROOT / "runs" / date


def job_link_for(folder: Path):
    jr = folder / "job-row.json"
    if jr.exists():
        return json.loads(jr.read_text(encoding="utf-8")).get("job_link", "").strip()
    md = (folder / "job.md").read_text(encoding="utf-8") if (folder / "job.md").exists() else ""
    m = re.search(r"\*\*Link:\*\*\s*(\S+)", md)
    return m.group(1).strip() if m else ""


# Map LinkedIn job link -> Drive web links for resume/de/cover
link_map = {}
for d in run_dir.iterdir():
    if not d.is_dir() or not (d / "resume.pdf").exists():
        continue
    jl = job_link_for(d)
    if not jl:
        continue
    try:
        links = get_links(date, d.name)
    except Exception as e:
        print(f"  (drive lookup failed for {d.name}: {e})")
        continue
    web = (
        links.get("resume.pdf", ""),
        links.get("resume.de.pdf", ""),
        links.get("cover-letter.pdf") or links.get("cover-letter.de.pdf", ""),
    )
    if any(web):
        link_map[jl] = web

if not link_map:
    print("No Drive links found yet (Drive may still be syncing). Try again shortly.")
    sys.exit(0)

import gspread
from google.oauth2.service_account import Credentials
creds = Credentials.from_service_account_file(str(ROOT / cfg["google"]["key_path"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets"])
ws = gspread.authorize(creds).open_by_key(cfg["google"]["sheet_id"]).worksheet(date)

rows = ws.get_all_values()
updated = 0
for i, r in enumerate(rows[1:], start=2):
    key = r[3].strip() if len(r) > 3 else ""
    if key not in link_map:
        continue
    new = link_map[key]
    cur = (r[4] if len(r) > 4 else "", r[5] if len(r) > 5 else "", r[6] if len(r) > 6 else "")
    merged = [new[k] or cur[k] for k in range(3)]  # keep existing if no new link
    ws.update([merged], f"E{i}:G{i}")
    updated += 1
print(f"Refreshed {updated} row(s) to clickable Drive links in tab '{date}'.")
