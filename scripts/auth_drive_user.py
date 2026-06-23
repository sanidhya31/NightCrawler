"""
auth_drive_user.py  -  ONE-TIME SETUP: authorize your personal Google account for
                       Drive uploads, store a refresh token in .secrets/token.json.

Run this once. After that, upload_public.py uses the token automatically (no browser).

Steps before running:
  1. Go to https://console.cloud.google.com/apis/credentials
     (same project as the service account)
  2. Create Credentials > OAuth 2.0 Client ID > Desktop app
  3. Download the JSON and save it as .secrets/client_secret.json

Then run:
  python scripts/auth_drive_user.py
"""

from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
import json

ROOT = Path(__file__).resolve().parent.parent
SECRET = ROOT / ".secrets" / "client_secret.json"
TOKEN  = ROOT / ".secrets" / "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

if not SECRET.exists():
    raise SystemExit(
        f"Missing: {SECRET}\n"
        "Download your OAuth2 client secret from Google Cloud Console:\n"
        "  APIs & Services > Credentials > Create Credentials > OAuth 2.0 Client ID > Desktop app\n"
        "  Download JSON > save as .secrets/client_secret.json"
    )

flow = InstalledAppFlow.from_client_secrets_file(str(SECRET), scopes=SCOPES)
creds = flow.run_local_server(port=0)

TOKEN.write_text(creds.to_json(), encoding="utf-8")
print(f"Token saved to {TOKEN}")
print("You can now run upload_public.py — no more browser prompts needed.")
