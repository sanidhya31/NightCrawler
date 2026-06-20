"""
should_run.py  -  gate for the nightly launcher

Exit 0  -> today's run is NOT complete yet -> the launcher SHOULD run.
Exit 1  -> today's run already finished (runs/<today>/DONE exists) -> SKIP.

This lets one repeating scheduled task self-retry within a time window:
finished days are skipped, unfinished ones (e.g. after a token-limit reset)
get completed on the next repeat.
"""

import sys
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
today = datetime.date.today().isoformat()
done = ROOT / "runs" / today / "DONE"
sys.exit(1 if done.exists() else 0)
