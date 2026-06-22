"""
upload_public.py  -  upload a date's job PDFs to the service account's Drive,
                     make each file publicly accessible, then update the sheet
                     with clickable HYPERLINK formulas.

No shared-folder editor permissions needed — files go into the service account's
own Drive space and are made 'anyone with link can view'.

Usage:
  python upload_public.py <YYYY-MM-DD>
"""

import sys
import json
import gspread
from pathlib import Path
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.json"

SLUGS_IN_ORDER = [
    "letmeship-ki-solutions",
    "philips-ki-automatisierung",
    "infinitcx-kundenanalyse",
    "govradar-ai-transformation",
    "deloitte-ai-data-strategy",
    "siemens-ai-digital-tools",
    "renesas-intern",
    "verolt-automotive-testing",
    "gea-supply-chain-analytics",
    "infinitcx-it-projektmanagement",
]


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else __import__("datetime").date.today().isoformat()
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))

    scopes = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/spreadsheets",
    ]
    creds = Credentials.from_service_account_file(str(ROOT / cfg["google"]["key_path"]), scopes=scopes)
    svc = build("drive", "v3", credentials=creds)
    sh  = gspread.authorize(creds).open_by_key(cfg["google"]["sheet_id"])
    ws  = sh.worksheet(date)

    run_dir = ROOT / "runs" / date

    def upload_public(path, name):
        media = MediaFileUpload(str(path), mimetype="application/pdf", resumable=False)
        f = svc.files().create(body={"name": name}, media_body=media, fields="id,webViewLink").execute()
        svc.permissions().create(fileId=f["id"], body={"type": "anyone", "role": "reader"}).execute()
        return f["webViewLink"]

    def hl(url, label):
        return f'=HYPERLINK("{url}","{label}")'

    # read sheet to find rows by slug (match company column or just go in order)
    all_rows = ws.get_all_values()
    updates = []

    for i, slug in enumerate(SLUGS_IN_ORDER):
        job_dir = run_dir / slug
        if not job_dir.exists():
            print(f"  skip (no folder): {slug}")
            continue

        sheet_row = i + 2  # row 1 = header
        company = all_rows[i + 1][1] if len(all_rows) > i + 1 else slug
        print(f"[{i+1}/10] {company} ...", flush=True)

        en  = job_dir / "resume.pdf"
        de  = job_dir / "resume.de.pdf"
        cov = job_dir / "cover_letter.pdf"

        en_link  = upload_public(en,  f"{company} - Resume EN.pdf")  if en.exists()  else ""
        de_link  = upload_public(de,  f"{company} - Resume DE.pdf")  if de.exists()  else ""
        cov_link = upload_public(cov, f"{company} - Cover Letter.pdf") if cov.exists() else ""

        updates.append({"range": f"E{sheet_row}:G{sheet_row}", "values": [[
            hl(en_link,  "Resume EN")    if en_link  else "",
            hl(de_link,  "Resume DE")    if de_link  else "",
            hl(cov_link, "Cover Letter") if cov_link else "",
        ]]})
        print(f"  EN: {en_link[:60]}...")

    ws.batch_update(updates, value_input_option="USER_ENTERED")
    print(f"\nDone — {len(updates)} rows updated with public Drive links.")


if __name__ == "__main__":
    main()
