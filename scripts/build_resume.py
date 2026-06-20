"""
build_resume.py  -  Phase 1 resume renderer (D-drive only)

Reads a resume JSON (base-resume.json or a tailored variant) and produces:
  1. <out>.html  - the v4 "centered" design, photo embedded as base64
  2. <out>.pdf   - pixel-accurate A4 PDF via Playwright (Chromium)

Usage:
  python build_resume.py <resume.json> <out_basename> [--html-only]

Example:
  python build_resume.py ../base/base-resume.json ../runs/preview/resume
"""

import os
import sys
import json
import base64
import html
from pathlib import Path

# Force Playwright to use the D-drive Chromium (never C). Set before any
# playwright import so overnight/cron runs find the browser without env setup.
os.environ.setdefault(
    "PLAYWRIGHT_BROWSERS_PATH",
    str(Path(__file__).resolve().parent.parent / ".playwright"),
)

ACCENT = "#3f6b86"      # steel blue accent (change here to restyle)
NAME_COLOR = "#1f1f1f"
INK = "#2b2b2b"
MUTED = "#555555"
BAR_BG = "#eef1f4"

# ---- tiny inline SVG icons (self-contained, render in PDF offline) ----
ICONS = {
    "mail": '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>',
    "phone": '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L16 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/></svg>',
    "linkedin": '<svg width="11" height="11" viewBox="0 0 24 24" fill="{c}"><path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5M3 9h4v12H3zM9 9h3.8v1.7h.05c.53-1 1.83-2.05 3.77-2.05 4.03 0 4.78 2.65 4.78 6.1V21H21v-5.4c0-1.3 0-2.95-1.8-2.95s-2.07 1.4-2.07 2.85V21H13z"/></svg>',
    "pin": '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-6-5.5-6-10a6 6 0 0 1 12 0c0 4.5-6 10-6 10"/><circle cx="12" cy="11" r="2"/></svg>',
    "github": '<svg width="11" height="11" viewBox="0 0 24 24" fill="{c}"><path d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.46-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.53 2.36 1.09 2.94.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.65 0 0 .84-.27 2.75 1.02a9.5 9.5 0 0 1 5 0c1.91-1.29 2.75-1.02 2.75-1.02.55 1.38.2 2.4.1 2.65.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.69-4.57 4.94.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2"/></svg>',
}


SECTION_TITLES = {
    "en": {
        "summary": "Summary",
        "experience": "Professional Experience",
        "projects": "Projects",
        "education": "Education",
        "publications": "Publications",
        "skills": "Skills",
        "languages": "Languages",
    },
    "de": {
        "summary": "Profil",
        "experience": "Berufserfahrung",
        "projects": "Projekte",
        "education": "Ausbildung",
        "publications": "Veröffentlichungen",
        "skills": "Kenntnisse",
        "languages": "Sprachen",
    },
}


def esc(v):
    return html.escape(str(v))


def icon(name):
    return ICONS[name].replace("{c}", ACCENT)


def _href(kind, val):
    if kind == "mail":
        return "mailto:" + val
    if kind in ("linkedin", "github"):
        v = val if val.startswith(("http://", "https://")) else "https://" + val
        return v
    return None  # phone, location: no link


def contact_row(c):
    items = [
        ("mail", c["email"]),
        ("phone", c["phone"]),
        ("linkedin", c.get("linkedin", "")),
        ("pin", c["location"]),
        ("github", c.get("github", "")),
    ]
    # Show clean labels for profile links (the URL is the clickable target).
    labels = {"linkedin": "LinkedIn", "github": "GitHub"}
    cells = ""
    for ic, val in items:
        if not val:
            continue
        href = _href(ic, val)
        text = labels.get(ic, val)
        inner = (f'<a href="{esc(href)}" style="color:inherit; text-decoration:none;">{esc(text)}</a>'
                 if href else esc(text))
        cells += f'<div class="c-item"><span class="c-ic">{icon(ic)}</span>{inner}</div>'
    return cells


def bar(title):
    return f'<div class="bar">{esc(title)}</div>'


def experience_block(items):
    out = ""
    for e in items:
        bullets = "".join(f"<li>{esc(b['text'])}</li>" for b in e["bullets"])
        out += f"""
    <div class="row">
      <div class="left">{esc(e['dates'])}<br>{esc(e.get('location',''))}</div>
      <div class="right">
        <div class="rh"><span class="org">{esc(e['company'])},</span> <span class="role">{esc(e['role'])}</span></div>
        <ul>{bullets}</ul>
      </div>
    </div>"""
    return out


def projects_block(items):
    out = ""
    for p in items:
        bullets = "".join(f"<li>{esc(b['text'])}</li>" for b in p["bullets"])
        stack = ", ".join(p.get("stack", [])[:4])
        out += f"""
    <div class="row">
      <div class="left">{esc(stack)}</div>
      <div class="right">
        <div class="rh"><span class="org">{esc(p['name'])}</span></div>
        <ul>{bullets}</ul>
      </div>
    </div>"""
    return out


def education_block(items):
    out = ""
    for e in items:
        out += f"""
    <div class="row">
      <div class="left">{esc(e['dates'])}<br>{esc(e.get('location',''))}</div>
      <div class="right"><span class="org">{esc(e['degree'])},</span> <span class="role">{esc(e['institution'])}</span></div>
    </div>"""
    return out


def skills_block(skills):
    cells = ""
    for label, vals in skills.items():
        cells += f'<div><span class="sk-l">{esc(label)}:</span> {esc(", ".join(vals))}</div>'
    return f'<div class="skills">{cells}</div>'


def publications_block(pubs):
    rows = ""
    for p in pubs:
        url = p.get("url", "")
        link = p.get("linkText", "View Publication")
        link_html = (
            f' | <a href="{esc(url)}" style="color:{ACCENT};">{esc(link)}</a>'
            if url and not url.startswith("PASTE_")
            else ""
        )
        rows += (
            f'<div style="margin-top:4px;"><span style="font-weight:800;">{esc(p["title"])}</span>'
            f' | {esc(p.get("venue",""))}{link_html}</div>'
        )
    return rows


def languages_block(langs):
    cells = "".join(
        f'<div><span class="dot">&bull;</span> {esc(l["name"])}: {esc(l["level"])}</div>'
        for l in langs
    )
    return f'<div class="langs">{cells}</div>'


def build_html(resume, photo_b64):
    c = resume["candidate"]
    t = SECTION_TITLES.get(resume.get("lang", "en"), SECTION_TITLES["en"])
    photo_tag = (
        f'<img class="photo" src="data:image/png;base64,{photo_b64}" alt="photo">'
        if photo_b64
        else '<div class="photo photo-ph">photo</div>'
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  @page {{ size: A4; margin: 14mm 0; }}
  html {{ font-family: Arial, Helvetica, sans-serif; color: {INK}; font-size: 10.2pt; line-height: 1.42; }}
  body {{ padding: 0 15mm; }}
  .head {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 18px; }}
  h1 {{ font-size: 21pt; font-weight: 800; color: {NAME_COLOR}; }}
  .contact {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px 22px; margin-top: 11px; font-size: 9.7pt; color: #333; }}
  .c-item {{ display: flex; align-items: center; }}
  .c-ic {{ display: inline-flex; width: 15px; }}
  .photo {{ width: 42mm; height: 42mm; border-radius: 50%; object-fit: cover; border: 1px solid #c3ccd6; flex: 0 0 auto; margin-right: 8mm; }}
  .photo-ph {{ background: #dfe5ec; display: flex; align-items: center; justify-content: center; color: #8a97a6; font-size: 9pt; }}
  .bar {{ text-align: center; background: {BAR_BG}; font-weight: 800; letter-spacing: .5px; padding: 4px; margin-top: 13px; break-after: avoid; }}
  .summary {{ margin-top: 7px; font-size: 9.8pt; line-height: 1.5; color: #333; }}
  .row {{ display: flex; gap: 15px; margin-top: 8px; break-inside: avoid; }}
  .left {{ width: 26mm; flex: 0 0 auto; color: {ACCENT}; font-size: 9.2pt; overflow-wrap: break-word; word-break: break-word; hyphens: auto; }}
  .right {{ flex: 1; min-width: 0; }}
  .rh {{ margin-bottom: 2px; }}
  .org {{ font-weight: 800; }}
  .role {{ font-style: italic; color: {MUTED}; }}
  ul {{ padding-left: 15px; margin-top: 2px; }}
  li {{ margin-top: 2px; }}
  .skills {{ display: grid; grid-template-columns: 1fr 1fr; gap: 3px 24px; margin-top: 7px; }}
  .sk-l {{ font-weight: 800; }}
  .langs {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 3px 18px; margin-top: 7px; }}
  .dot {{ color: {ACCENT}; }}
</style></head>
<body>
  <div class="head">
    <div style="min-width:0; flex:1;">
      <h1>{esc(c['name'])}</h1>
      <div class="contact">{contact_row(c)}</div>
    </div>
    {photo_tag}
  </div>

  {bar(t['summary'])}
  <div class="summary">{esc(c['summary'])}</div>

  {bar(t['experience'])}
  {experience_block(resume['workExperience'])}

  {bar(t['projects'])}
  {projects_block(resume['projects'])}

  {bar(t['education'])}
  {education_block(resume['education'])}
  {(bar(t['publications']) + publications_block(resume['publications'])) if resume.get('publications') else ''}

  {bar(t['skills'])}
  {skills_block(resume['skills'])}

  {bar(t['languages'])}
  {languages_block(resume['languages'])}
</body></html>"""


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    html_only = "--html-only" in sys.argv
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)

    json_path = Path(args[0]).resolve()
    out_base = Path(args[1]).resolve()
    out_base.parent.mkdir(parents=True, exist_ok=True)

    resume = json.loads(json_path.read_text(encoding="utf-8"))

    # embed photo: check next to the JSON, then the project's base/ folder
    # (project root = scripts/.. , so base photo is always found regardless of
    # where the tailored JSON lives, e.g. runs/<date>/<job>/).
    photo_b64 = ""
    photo_name = resume.get("candidate", {}).get("photo", "photo.png")
    project_root = Path(__file__).resolve().parent.parent
    candidates = [
        json_path.parent / photo_name,
        project_root / "base" / photo_name,
    ]
    for cand in candidates:
        if cand.exists():
            photo_b64 = base64.b64encode(cand.read_bytes()).decode("ascii")
            break

    # Append extensions as strings (not with_suffix) so basenames containing
    # dots like "resume.de" keep the ".de" instead of having it stripped.
    html_str = build_html(resume, photo_b64)
    html_file = Path(str(out_base) + ".html")
    html_file.write_text(html_str, encoding="utf-8")
    print(f"HTML -> {html_file}")

    if html_only:
        return

    from playwright.sync_api import sync_playwright

    pdf_file = Path(str(out_base) + ".pdf")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(html_file.as_uri())
        page.pdf(
            path=str(pdf_file),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
        )
        browser.close()
    print(f"PDF  -> {pdf_file}")


if __name__ == "__main__":
    main()
