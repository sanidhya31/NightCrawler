"""
finish_delivery.py  -  deliver already-tailored jobs that didn't get logged.

For a given run date, finds job folders that have resume.pdf but are not yet in
tracker.csv, copies their PDFs to Drive, and logs a row to the date's sheet tab
(+ CSV mirror). One-shot recovery for a run that was cut off before logging.

Usage: python finish_delivery.py <YYYY-MM-DD>
"""

import sys, csv, json, re, shutil, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
date = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
run_dir = ROOT / "runs" / date
drive_root = Path(cfg["drive"]["dir"]) / date
csv_path = ROOT / "runs" / "tracker.csv"

logged_links = set()
if csv_path.exists():
    for r in csv.DictReader(csv_path.open(encoding="utf-8")):
        if r.get("Job link"):
            logged_links.add(r["Job link"].strip())

def meta(d):
    jr = d / "job-row.json"
    if jr.exists():
        j = json.loads(jr.read_text(encoding="utf-8"))
        return j.get("company", ""), j.get("role", ""), j.get("job_link", ""), str(j.get("match_score", ""))
    md = (d / "job.md").read_text(encoding="utf-8") if (d / "job.md").exists() else ""
    role = (re.search(r"^#\s*(.+)", md, re.M) or [None, d.name])[1].strip() if md else d.name
    comp = (re.search(r"\*\*Company:\*\*\s*(.+)", md) or [None, ""])[1].strip() if md else ""
    link = (re.search(r"\*\*Link:\*\*\s*(\S+)", md) or [None, ""])[1].strip() if md else ""
    return comp, role, link, ""

rows = []
for d in sorted(p for p in run_dir.iterdir() if p.is_dir()):
    if not (d / "resume.pdf").exists():
        continue
    company, role, link, score = meta(d)
    if link and link in logged_links:
        continue  # already delivered (e.g. the manual BMW row)
    dest = drive_root / d.name
    dest.mkdir(parents=True, exist_ok=True)
    for f in ["resume.pdf", "resume.de.pdf", "cover-letter.pdf", "cover-letter.de.pdf", "job.md"]:
        if (d / f).exists():
            shutil.copy2(d / f, dest / f)
    rows.append([
        date, company, role, link,
        str(dest / "resume.pdf"), str(dest / "resume.de.pdf"), str(dest / "cover-letter.pdf"),
        score, "New", "recovered from 4:40 run",
    ])

if not rows:
    print("Nothing to deliver.")
    sys.exit(0)

# CSV mirror
new = not csv_path.exists()
HEADERS = ["Date found","Company","Role","Job link","Resume EN","Resume DE","Cover letter","Match score","Status","Notes"]
with csv_path.open("a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    if new: w.writerow(HEADERS)
    w.writerows(rows)

# Sheet append
import gspread
from google.oauth2.service_account import Credentials
creds = Credentials.from_service_account_file(str(ROOT / cfg["google"]["key_path"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets"])
sh = gspread.authorize(creds).open_by_key(cfg["google"]["sheet_id"])
try:
    ws = sh.worksheet(date)
except gspread.WorksheetNotFound:
    ws = sh.add_worksheet(title=date, rows=1000, cols=len(HEADERS))
    ws.update([HEADERS], "A1")
ws.append_rows(rows, value_input_option="USER_ENTERED")
print(f"Delivered {len(rows)} job(s) -> Drive + sheet tab '{date}' + CSV:")
for r in rows:
    print(f"  {r[1]} | {r[2][:45]}")
