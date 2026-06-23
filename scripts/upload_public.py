"""
upload_public.py  -  upload a date's job PDFs to Google Cloud Storage (cc-apply bucket),
                     then update the sheet with clickable public HYPERLINK formulas.

GCS public URL: https://storage.googleapis.com/cc-apply/<date>/<slug>/filename.pdf
No Drive Desktop, no OAuth2, no quota issues — service account has full GCS access.

Usage:
  python upload_public.py <YYYY-MM-DD>
"""

import sys
import json
import gspread
from pathlib import Path
from google.oauth2.service_account import Credentials
from google.cloud import storage as gcs

ROOT   = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.json"
BUCKET = "cc-apply"

SLUGS_IN_ORDER = [
    "xitaso-software-dev",
    "sap-communications-media",
    "efly-sales-marketing",
    "renk-hr-data-analytics",
    "liebherr-data-ai",
    "1komma5-product-manager-growth",
    "selectry-sales-recruiting-ops",
    "wesort-data-ai",
    "bcause-international-partnerships",
    "greenpocket-projektmanagement",
]


def main():
    date = sys.argv[1] if len(sys.argv) > 1 else __import__("datetime").date.today().isoformat()
    cfg  = json.loads(CONFIG.read_text(encoding="utf-8"))
    key  = str(ROOT / cfg["google"]["key_path"])

    sa_creds = Credentials.from_service_account_file(
        key,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gcs_client = gcs.Client.from_service_account_json(key)
    bucket     = gcs_client.bucket(BUCKET)

    sh = gspread.authorize(sa_creds).open_by_key(cfg["google"]["sheet_id"])
    ws = sh.worksheet(date)

    run_dir = ROOT / "runs" / date

    def upload(local_path, blob_name):
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(local_path), content_type="application/pdf")
        # Bucket uses uniform public access — no per-object ACL needed
        return f"https://storage.googleapis.com/{BUCKET}/{blob_name}"

    def hl(url, label):
        return f'=HYPERLINK("{url}","{label}")'

    all_rows = ws.get_all_values()
    updates  = []

    for i, slug in enumerate(SLUGS_IN_ORDER):
        job_dir = run_dir / slug
        if not job_dir.exists():
            print(f"  skip (no folder): {slug}")
            continue

        sheet_row = i + 2
        company   = all_rows[i + 1][1] if len(all_rows) > i + 1 else slug
        print(f"[{i+1}/10] {company} ...", flush=True)

        prefix = f"{date}/{slug}"
        en  = job_dir / "resume.pdf"
        de  = job_dir / "resume.de.pdf"
        cov = job_dir / "cover_letter.pdf"

        en_link  = upload(en,  f"{prefix}/resume.pdf")         if en.exists()  else ""
        de_link  = upload(de,  f"{prefix}/resume.de.pdf")      if de.exists()  else ""
        cov_link = upload(cov, f"{prefix}/cover_letter.pdf")   if cov.exists() else ""

        updates.append({"range": f"E{sheet_row}:G{sheet_row}", "values": [[
            hl(en_link,  "Resume EN")    if en_link  else "",
            hl(de_link,  "Resume DE")    if de_link  else "",
            hl(cov_link, "Cover Letter") if cov_link else "",
        ]]})
        print(f"  EN: {en_link}")

    ws.batch_update(updates, value_input_option="USER_ENTERED")
    print(f"\nDone — {len(updates)} rows updated.")


if __name__ == "__main__":
    main()
