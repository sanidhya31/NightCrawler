"""
build_coverletter.py  -  render a cover letter to PDF (letterhead + body + regards)

Input JSON (per job), e.g. cover.json:
  {
    "lang": "en",
    "date": "2026-06-20",
    "company": "BMW Group",
    "role": "Praktikant ...",
    "greeting": "Dear Hiring Team,",
    "paragraphs": ["...", "...", "..."],
    "closing": "Kind regards,"
  }
Letterhead (name + contact) is pulled from base/base-resume.json (locked facts).

Usage:
  python build_coverletter.py <cover.json> <out_basename>
  -> writes <out>.pdf and <out>.md
"""

import os
import sys
import json
import base64
import html
from pathlib import Path

os.environ.setdefault(
    "PLAYWRIGHT_BROWSERS_PATH",
    str(Path(__file__).resolve().parent.parent / ".playwright"),
)

ROOT = Path(__file__).resolve().parent.parent
ACCENT = "#3f6b86"


def esc(v):
    return html.escape(str(v))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    cov = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out_base = Path(sys.argv[2]).resolve()
    out_base.parent.mkdir(parents=True, exist_ok=True)

    base = json.loads((ROOT / "base" / "base-resume.json").read_text(encoding="utf-8"))
    c = base["candidate"]
    contact = " &middot; ".join(filter(None, [
        c.get("location"), c.get("phone"), c.get("email"),
        c.get("linkedin"), c.get("github"),
    ]))

    is_de = cov.get("lang", "en") == "de"
    re_label = "Betreff: Bewerbung als" if is_de else "Re: Application for"
    paras = "".join(f"<p>{esc(p)}</p>" for p in cov.get("paragraphs", []))
    html_str = f"""<!doctype html><html><head><meta charset="utf-8"><style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  @page {{ size: A4; margin: 22mm 0; }}
  html {{ font-family: Arial, Helvetica, sans-serif; color: #2b2b2b; font-size: 10.5pt; line-height: 1.5; }}
  body {{ padding: 0 20mm; }}
  .name {{ font-size: 19pt; font-weight: 800; color: #1f1f1f; }}
  .rule {{ height: 3px; width: 64px; background: {ACCENT}; margin: 8px 0 6px; }}
  .contact {{ font-size: 9.3pt; color: #555; }}
  .meta {{ margin-top: 22px; font-size: 10pt; }}
  .meta .re {{ font-weight: 800; margin-top: 10px; }}
  .greet {{ margin-top: 18px; }}
  p {{ margin-top: 11px; text-align: justify; }}
  .close {{ margin-top: 20px; }}
  .sign {{ font-weight: 800; }}
</style></head><body>
  <div class="name">{esc(c['name'])}</div>
  <div class="rule"></div>
  <div class="contact">{contact}</div>
  <div class="meta">
    <div>{esc(cov.get('date',''))}</div>
    <div style="margin-top:8px;">{esc(cov.get('company',''))}</div>
    <div class="re">{re_label} {esc(cov.get("role",""))}</div>
  </div>
  <div class="greet">{esc(cov.get('greeting','Dear Hiring Team,'))}</div>
  {paras}
  <div class="close">{esc(cov.get('closing','Kind regards,'))}</div>
  <div class="sign">{esc(c['name'])}</div>
</body></html>"""

    html_file = Path(str(out_base) + ".html")
    html_file.write_text(html_str, encoding="utf-8")

    # also a plain .md for quick reading/editing
    md = (f"# {c['name']}\n{contact.replace(' &middot; ', ' · ')}\n\n"
          f"{cov.get('date','')}\n\n{cov.get('company','')}\n"
          f"{re_label} {cov.get('role','')}\n\n"
          f"{cov.get('greeting','')}\n\n" + "\n\n".join(cov.get("paragraphs", [])) +
          f"\n\n{cov.get('closing','')}\n{c['name']}\n")
    Path(str(out_base) + ".md").write_text(md, encoding="utf-8")

    from playwright.sync_api import sync_playwright
    pdf_file = Path(str(out_base) + ".pdf")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(html_file.as_uri())
        pg.pdf(path=str(pdf_file), format="A4", print_background=True, prefer_css_page_size=True)
        b.close()
    print(f"Cover letter -> {pdf_file}")


if __name__ == "__main__":
    main()
