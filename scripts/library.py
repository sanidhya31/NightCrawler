"""
library.py  -  persistent resume library for cluster reuse.

Stores ONE angle-tailored resume per cluster in library/, plus a manifest. A cluster
resume is reused across days/jobs until base-resume.json changes (hash mismatch), at
which point it is marked stale and regenerated.

Layout:
  library/manifest.json
  library/<cluster-slug>.tailored.json / .tailored.de.json / .pdf / .de.pdf

Commands:
  python library.py --status                  # show clusters: fresh / stale / missing
  python library.py --need "<Cluster Name>"    # exit 0 if it needs (re)generating, else 1
  python library.py --get  "<Cluster Name>"    # print JSON of stored file paths (for reuse)
  python library.py --record "<Cluster Name>"  # mark cluster as built from current base
"""

import sys
import json
import hashlib
import datetime
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "base" / "base-resume.json"
LIB = ROOT / "library"
MANIFEST = LIB / "manifest.json"


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def base_hash():
    return hashlib.md5(BASE.read_bytes()).hexdigest()[:12]


def load_manifest():
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"base_hash": "", "clusters": {}}


def save_manifest(m):
    LIB.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")


def files_for(cluster):
    s = slug(cluster)
    return {
        "json": f"library/{s}.tailored.json",
        "json_de": f"library/{s}.tailored.de.json",
        "pdf_en": f"library/{s}.pdf",
        "pdf_de": f"library/{s}.de.pdf",
    }


def needs(cluster):
    m = load_manifest()
    cur = base_hash()
    entry = m["clusters"].get(cluster)
    if not entry:
        return True
    if entry.get("base_hash") != cur:
        return True  # base resume changed -> regenerate
    # all expected files must exist
    return not all((ROOT / p).exists() for p in files_for(cluster).values())


def record(cluster):
    m = load_manifest()
    m["base_hash"] = base_hash()
    m["clusters"][cluster] = {
        "base_hash": base_hash(),
        "built_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "files": files_for(cluster),
    }
    save_manifest(m)


def main():
    if "--status" in sys.argv:
        m = load_manifest()
        cur = base_hash()
        print(f"base_hash (current): {cur}")
        if not m["clusters"]:
            print("  (library empty)")
        for cl, e in m["clusters"].items():
            state = "fresh" if e.get("base_hash") == cur and all((ROOT / p).exists() for p in files_for(cl).values()) else "STALE -> regenerate"
            print(f"  {cl}: {state} (built {e.get('built_at')})")
        return
    if "--need" in sys.argv:
        cl = sys.argv[sys.argv.index("--need") + 1]
        sys.exit(0 if needs(cl) else 1)
    if "--get" in sys.argv:
        cl = sys.argv[sys.argv.index("--get") + 1]
        print(json.dumps(files_for(cl), indent=2))
        return
    if "--record" in sys.argv:
        cl = sys.argv[sys.argv.index("--record") + 1]
        record(cl)
        print(f"recorded '{cl}' at base_hash {base_hash()}")
        return
    print(__doc__)


if __name__ == "__main__":
    main()
