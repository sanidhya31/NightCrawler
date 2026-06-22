"""
upload_drive.py  -  upload a job folder's PDFs to Google Drive (VPS replacement for
                    Google Drive for Desktop).

Creates the folder hierarchy <drive.dir>/<date>/<slug>/ if it doesn't exist,
then uploads every *.pdf in the local job folder, skipping files already present.
Prints a JSON map of { filename: webViewLink } for each uploaded/existing file.

Requires the service account to have Editor access on the root Drive folder
(change from Viewer — right-click the folder in Drive > Share > add the service
account email with Editor role).

Usage:
  python upload_drive.py <date> <slug>
  python upload_drive.py runs/2026-06-21/company-role/   # infers date+slug from path
"""

import sys
import json
import mimetypes
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.json"


def drive_service(cfg):
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_service_account_file(
        str(ROOT / cfg["google"]["key_path"]),
        scopes=["https://www.googleapis.com/auth/drive"],
    )
    return build("drive", "v3", credentials=creds)


def find_or_create_folder(svc, name, parent_id=None):
    q = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    res = svc.files().list(
        q=q, fields="files(id, name)",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]
    meta = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        meta["parents"] = [parent_id]
    f = svc.files().create(body=meta, fields="id", supportsAllDrives=True).execute()
    return f["id"]


def list_existing(svc, folder_id):
    res = svc.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        fields="files(id, name, webViewLink)",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute()
    return {f["name"]: f.get("webViewLink", "") for f in res.get("files", [])}


def upload_file(svc, local_path, folder_id):
    from googleapiclient.http import MediaFileUpload

    mime = mimetypes.guess_type(local_path.name)[0] or "application/octet-stream"
    media = MediaFileUpload(str(local_path), mimetype=mime, resumable=False)
    meta = {"name": local_path.name, "parents": [folder_id]}
    f = svc.files().create(
        body=meta, media_body=media, fields="id, webViewLink",
        supportsAllDrives=True,
    ).execute()
    return f.get("webViewLink", "")


def upload_job(date, slug):
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    root_name = Path(cfg["drive"]["dir"]).name
    job_dir = ROOT / "runs" / date / slug

    if not job_dir.exists():
        raise SystemExit(f"Job folder not found: {job_dir}")

    svc = drive_service(cfg)

    root_res = svc.files().list(
        q=f"name = '{root_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        fields="files(id)", supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute()
    root_files = root_res.get("files", [])
    if not root_files:
        raise SystemExit(f"Drive root folder '{root_name}' not found or not shared with service account.")
    root_id = root_files[0]["id"]

    date_id = find_or_create_folder(svc, date, root_id)
    job_id = find_or_create_folder(svc, slug, date_id)

    existing = list_existing(svc, job_id)
    links = dict(existing)

    for pdf in sorted(job_dir.glob("*.pdf")):
        if pdf.name in existing:
            print(f"  skip (exists): {pdf.name}")
            continue
        print(f"  uploading: {pdf.name} ...")
        link = upload_file(svc, pdf, job_id)
        links[pdf.name] = link
        print(f"    -> {link}")

    return links


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    arg = sys.argv[1]
    if len(sys.argv) >= 3:
        date, slug = sys.argv[1], sys.argv[2]
    else:
        p = Path(arg)
        parts = p.parts
        if len(parts) >= 2:
            slug = parts[-1]
            date = parts[-2]
        else:
            raise SystemExit("Pass <date> <slug> or a path like runs/<date>/<slug>/")

    links = upload_job(date, slug)
    print(json.dumps(links, indent=2))


if __name__ == "__main__":
    main()
