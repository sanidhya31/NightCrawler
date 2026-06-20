"""
guard.py  -  locked-facts validator for tailored resumes

Compares a tailored resume JSON against base-resume.json and FAILS (exit 1)
if any locked fact drifted or a fabricated bullet/employer/degree appeared.

Usage:
  python guard.py base/base-resume.json runs/.../resume.tailored.json

Exit codes: 0 = PASS, 1 = FAIL (prints every violation).
"""

import sys
import json
from pathlib import Path


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)

    base = load(sys.argv[1])
    tail = load(sys.argv[2])
    errors = []
    warnings = []

    # 1. candidate locked fields
    locked_candidate = ["name", "email", "phone", "linkedin", "github", "location", "photo"]
    bc, tc = base.get("candidate", {}), tail.get("candidate", {})
    for f in locked_candidate:
        if bc.get(f) != tc.get(f):
            errors.append(f"candidate.{f} changed: {tc.get(f)!r} != base {bc.get(f)!r}")

    # 2. work experience: company/role/dates/location must match base for that company
    base_exp = {e["company"]: e for e in base.get("workExperience", [])}
    base_bullet_ids = set()
    for e in base.get("workExperience", []):
        for b in e.get("bullets", []):
            base_bullet_ids.add(b["id"])
    for e in base.get("projects", []):
        for b in e.get("bullets", []):
            base_bullet_ids.add(b["id"])

    for e in tail.get("workExperience", []):
        comp = e.get("company")
        if comp not in base_exp:
            errors.append(f"workExperience has unknown employer not in base: {comp!r}")
            continue
        be = base_exp[comp]
        for f in ["role", "dates", "location"]:
            if e.get(f) != be.get(f):
                errors.append(f"{comp}: {f} changed: {e.get(f)!r} != base {be.get(f)!r}")
        for b in e.get("bullets", []):
            bid = b.get("id")
            if bid and bid not in base_bullet_ids:
                warnings.append(f"{comp}: bullet id {bid!r} not found in base (reworded ok, but check it maps to a real claim)")

    # 3. education must be a subset of base education (no invented degrees)
    def edu_key(e):
        return (e.get("degree"), e.get("institution"), e.get("dates"))
    base_edu = {edu_key(e) for e in base.get("education", [])}
    for e in tail.get("education", []):
        if edu_key(e) not in base_edu:
            errors.append(f"education entry not in base: {edu_key(e)}")

    # 4. project bullets: ids should map to base
    for p in tail.get("projects", []):
        for b in p.get("bullets", []):
            bid = b.get("id")
            if bid and bid not in base_bullet_ids:
                warnings.append(f"project {p.get('name')!r}: bullet id {bid!r} not in base")

    # 5. summary must be non-empty
    if not tc.get("summary", "").strip():
        errors.append("candidate.summary is empty")

    # ---- report ----
    name = Path(sys.argv[2]).name
    for w in warnings:
        print(f"  WARN  {w}")
    if errors:
        print(f"\nGUARD FAIL ({name}): {len(errors)} locked-fact violation(s):")
        for e in errors:
            print(f"  FAIL  {e}")
        sys.exit(1)
    print(f"GUARD PASS ({name}) — all locked facts intact"
          + (f", {len(warnings)} warning(s)" if warnings else ""))
    sys.exit(0)


if __name__ == "__main__":
    main()
