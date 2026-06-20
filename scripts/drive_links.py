"""
drive_links.py  -  fetch clickable Google Drive web links for a job's files

Requires (one-time):
  1. Drive API enabled on the Google Cloud project.
  2. The Drive folder `config.drive.dir` basename (e.g. "JobApplications") shared
     with the service account (Viewer). For links that open without sign-in, set
     that folder to "Anyone with the link -> Viewer".

The files themselves are put in Drive by Google Drive for Desktop (you own them);
this script only READS their webViewLinks via the service account.

Usage:
  python drive_links.py <date> <slug>
    -> prints JSON: { "resume.pdf": "https://...", "resume.de.pdf": "...", ... }

Note: Drive Desktop sync isn't instant; if a file isn't found yet, retry shortly.
"""

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.json"


def drive_service(cfg):
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    creds = Credentials.from_service_account_file(
        str(ROOT / cfg["google"]["key_path"]),
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    return build("drive", "v3", credentials=creds)


def find_child(svc, name, parent_id=None):
    q = f"name = '{name}' and trashed = false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    res = svc.files().list(
        q=q, fields="files(id, name, mimeType, webViewLink)",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute()
    files = res.get("files", [])
    return files[0] if files else None


def list_children(svc, parent_id):
    res = svc.files().list(
        q=f"'{parent_id}' in parents and trashed = false",
        fields="files(id, name, webViewLink)",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute()
    return {f["name"]: f.get("webViewLink", "") for f in res.get("files", [])}


def get_links(date, slug):
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    root_name = Path(cfg["drive"]["dir"]).name  # e.g. "JobApplications"
    svc = drive_service(cfg)

    root = find_child(svc, root_name)
    if not root:
        raise SystemExit(f"Drive folder '{root_name}' not found/shared with service account.")
    date_folder = find_child(svc, date, root["id"])
    if not date_folder:
        return {}
    job_folder = find_child(svc, slug, date_folder["id"])
    if not job_folder:
        return {}
    return list_children(svc, job_folder["id"])


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    links = get_links(sys.argv[1], sys.argv[2])
    print(json.dumps(links, indent=2))


if __name__ == "__main__":
    main()
