"""
tracker.py  -  logs job rows to a Google Sheet, one tab per day + a "Past" archive

Layout:
  - Each day's jobs go to a worksheet named by date, e.g. "2026-06-20".
  - On rollover, any older date tabs are merged into the archive tab ("Past")
    and then deleted, so the sheet always shows: today's tab + Past.

Commands:
  python tracker.py --check                 # verify connection
  python tracker.py --rollover [YYYY-MM-DD] # archive all tabs except today + Past
  python tracker.py --job <job-row.json>    # append one job to today's tab (+ CSV)

Every job is ALSO mirrored to runs/tracker.csv.
"""

import sys
import csv
import json
import datetime
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.json"
CSV_MIRROR = ROOT / "runs" / "tracker.csv"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

HEADERS = [
    "Date found", "Company", "Role", "Job link",
    "Resume EN", "Resume DE", "Cover letter",
    "Match score", "Status", "Notes",
]


def load_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def open_spreadsheet(cfg):
    import gspread
    from google.oauth2.service_account import Credentials

    g = cfg["google"]
    creds = Credentials.from_service_account_file(
        str(ROOT / g["key_path"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    return gspread.authorize(creds).open_by_key(g["sheet_id"])


def get_or_create_ws(sh, title):
    import gspread
    try:
        ws = sh.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=1000, cols=len(HEADERS))
    if ws.row_values(1) != HEADERS:
        ws.update([HEADERS], "A1")
    return ws


def row_from_job(job):
    return [
        job.get("date", datetime.date.today().isoformat()),
        job.get("company", ""), job.get("role", ""), job.get("job_link", ""),
        job.get("resume_en", ""), job.get("resume_de", ""), job.get("cover_letter", ""),
        job.get("match_score", ""), job.get("status", "New"), job.get("notes", ""),
    ]


def mirror_csv(row):
    CSV_MIRROR.parent.mkdir(parents=True, exist_ok=True)
    new = not CSV_MIRROR.exists()
    with CSV_MIRROR.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(HEADERS)
        w.writerow(row)


def rollover(cfg, today):
    """Merge all date tabs that are not `today` into the archive tab, then delete them.
    The archive tab and the Backlog tab are never touched."""
    sh = open_spreadsheet(cfg)
    archive_title = cfg["google"].get("archive_tab", "Past")
    backlog_title = cfg["google"].get("backlog_tab", "Backlog")
    archive = get_or_create_ws(sh, archive_title)
    moved = 0
    for ws in sh.worksheets():
        title = ws.title
        # Only archive OLD daily date tabs (YYYY-MM-DD). Preserve today's tab,
        # Past, Backlog, and any custom tab (e.g. "Tech Picks").
        if not DATE_RE.match(title) or title == today:
            continue
        # archive any non-today tab that has data (date tabs and the old "Jobs" tab)
        rows = ws.get_all_values()
        data = [r for r in rows[1:] if any(c.strip() for c in r)] if rows else []
        if data:
            archive.append_rows(data, value_input_option="USER_ENTERED")
            moved += len(data)
        sh.del_worksheet(ws)
    # make sure today's tab exists after cleanup
    get_or_create_ws(sh, today)
    print(f"Rollover done: archived {moved} row(s) into '{archive_title}'. Active tab: '{today}'.")


def main():
    cfg = load_config()

    if "--check" in sys.argv:
        sh = open_spreadsheet(cfg)
        print(f"Connected. Spreadsheet: '{sh.title}'. Tabs: {[w.title for w in sh.worksheets()]}")
        return

    if "--rollover" in sys.argv:
        i = sys.argv.index("--rollover")
        today = sys.argv[i + 1] if len(sys.argv) > i + 1 and DATE_RE.match(sys.argv[i + 1]) \
            else datetime.date.today().isoformat()
        rollover(cfg, today)
        return

    if "--backlog-from" in sys.argv:
        ranked_path = Path(sys.argv[sys.argv.index("--backlog-from") + 1])
        ranked = json.loads(ranked_path.read_text(encoding="utf-8"))
        backlog = [x for x in ranked if x.get("bucket") == "backlog"]
        date = ranked_path.parent.name
        # near-miss = backlog jobs scoring within `margin` of the lowest tailored job
        tailor_scores = [x.get("score", 0) for x in ranked if x.get("bucket") == "tailor"]
        cutoff = min(tailor_scores) if tailor_scores else None
        margin = cfg["filters"].get("near_miss_margin", 0.04)

        rows, near_idx = [], []
        for x in backlog:
            near = cutoff is not None and x.get("score", 0) >= cutoff - margin
            if near:
                near_idx.append(len(rows))
            note = (f"{x.get('cluster','')} | score {x.get('score','')}"
                    + (" [WATCH]" if x.get("watchlist") else "")
                    + (" [DE-req]" if x.get("german_required") else "")
                    + (" *** NEAR-MISS, could be top 10 ***" if near else ""))
            rows.append([
                date, x.get("company", ""), x.get("title", ""), x.get("link", ""),
                f"reuse: {x.get('cluster','')} resume", "", "",
                str(x.get("match_estimate", "")), "Backlog", note,
            ])
        if not rows:
            print("No backlog jobs to log.")
            return
        sh = open_spreadsheet(cfg)
        ws = get_or_create_ws(sh, cfg["google"].get("backlog_tab", "Backlog"))
        start = len(ws.get_all_values()) + 1  # row where this batch begins
        ws.append_rows(rows, value_input_option="USER_ENTERED")
        # red-highlight the near-miss rows
        red = {"backgroundColor": {"red": 0.96, "green": 0.80, "blue": 0.80}}
        for i in near_idx:
            r = start + i
            ws.format(f"A{r}:J{r}", red)
        print(f"Logged {len(rows)} backlog job(s) to '{ws.title}' ({len(near_idx)} near-miss, marked red).")
        return

    if "--job" in sys.argv:
        job_path = Path(sys.argv[sys.argv.index("--job") + 1])
        job = json.loads(job_path.read_text(encoding="utf-8"))
        row = row_from_job(job)
        mirror_csv(row)
        today = job.get("date", datetime.date.today().isoformat())
        try:
            sh = open_spreadsheet(cfg)
            ws = get_or_create_ws(sh, today)
            ws.append_row(row, value_input_option="USER_ENTERED")
            print(f"Logged to tab '{today}' + CSV: {job.get('company')} / {job.get('role')}")
        except Exception as e:
            print(f"Sheet append failed ({e}); row saved to {CSV_MIRROR}")
        return

    print(__doc__)


if __name__ == "__main__":
    main()
