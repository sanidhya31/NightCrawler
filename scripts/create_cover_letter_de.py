"""
Creates cover-letter-DE.docx — German translation of cover-letter.pdf
Matches the original styling: bold name header with blue rule, gray contact line,
bold Re: line, justified body, Kind regards sign-off.
"""

import zipfile

OUTPUT = r"C:\Users\sanid\Desktop\temp\cover-letter-DE.docx"

# ── XML helpers ────────────────────────────────────────────────────────────────

def rpr_xml(bold=False, size=24, color=None, font="Calibri", italic=False):
    p = [f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}"/>',
         f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>']
    if bold:   p.append('<w:b/><w:bCs/>')
    if italic: p.append('<w:i/><w:iCs/>')
    if color:  p.append(f'<w:color w:val="{color}"/>')
    return '<w:rPr>' + ''.join(p) + '</w:rPr>'

def run(text, bold=False, size=24, color=None, font="Calibri", italic=False, preserve=False):
    sp = ' xml:space="preserve"' if (preserve or (' ' in text and (text.startswith(' ') or text.endswith(' ')))) else ''
    rp = rpr_xml(bold=bold, size=size, color=color, font=font, italic=italic)
    escaped = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return f'<w:r>{rp}<w:t{sp}>{escaped}</w:t></w:r>'

def hyperlink_run(text, rid, size=20, color="1155CC"):
    rp = f'<w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/><w:sz w:val="{size}"/><w:szCs w:val="{size}"/><w:color w:val="{color}"/><w:u w:val="single"/></w:rPr>'
    escaped = text.replace('&', '&amp;')
    return f'<w:hyperlink r:id="{rid}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><w:r>{rp}<w:t>{escaped}</w:t></w:r></w:hyperlink>'

def para(children, align=None, before=0, after=160, border_bottom=False):
    ppr = []
    if align:         ppr.append(f'<w:jc w:val="{align}"/>')
    if before or after != 160:
        ppr.append(f'<w:spacing w:before="{before}" w:after="{after}" w:line="276" w:lineRule="auto"/>')
    else:
        ppr.append('<w:spacing w:line="276" w:lineRule="auto"/>')
    if border_bottom:
        ppr.append('<w:pBdr><w:bottom w:val="single" w:sz="12" w:space="1" w:color="1F4E79"/></w:pBdr>')
    ppr_xml = '<w:pPr>' + ''.join(ppr) + '</w:pPr>' if ppr else ''
    return '<w:p>' + ppr_xml + ''.join(children) + '</w:p>'

def empty(after=80):
    return f'<w:p><w:pPr><w:spacing w:before="0" w:after="{after}"/></w:pPr></w:p>'

# ── document body ──────────────────────────────────────────────────────────────

body = []

# Name — large bold, with blue bottom border
body.append(para(
    [run('Sanidhya Purohit', bold=True, size=36, color='1F4E79', font='Calibri')],
    before=0, after=40, border_bottom=True
))

# Contact line — small gray, with hyperlinks for email/linkedin/github
contact_parts = [
    run('Trier, Deutschland · +49 17679216414 · ', size=18, color='595959'),
    hyperlink_run('sanidhyapurohit2@gmail.com', 'rId4', size=18),
    run(' · ', size=18, color='595959'),
    hyperlink_run('linkedin.com/in/sanidhya-purohit-6b6653198', 'rId5', size=18),
    run(' · ', size=18, color='595959'),
    hyperlink_run('github.com/sanidhya31', 'rId6', size=18),
]
body.append(para(contact_parts, before=60, after=200))

# Date
body.append(para([run('2026-06-21', size=22, color='000000')], before=0, after=80))

# Company
body.append(para([run('Siemens Mobility', size=22)], before=0, after=80))

# Empty line
body.append(empty(120))

# Re: subject — bold
body.append(para(
    [run('Betreff: Bewerbung als Werkstudent (w/m/d) Digitalisierung & KI im Projektmanagement', bold=True, size=22)],
    before=0, after=200
))

# Salutation
body.append(para([run('Sehr geehrtes Recruiting-Team bei Siemens Mobility,', size=22)], before=0, after=160))

# P1
body.append(para([run(
    'ich bin Masterstudent im Bereich Data Science (Schwerpunkt NLP) an der Universität Trier und bewerbe mich für die Werkstudentenstelle im Bereich Digitalisierung & KI im Projektmanagement. Die Kombination aus KI-Anwendung und Projektmanagement-Aufgaben entspricht genau meinem Zielprofil: Ich möchte Automatisierung und KI-Denken in strukturierte Projektumgebungen einbringen – und nicht nur isoliert Tools entwickeln.',
    size=22)], align='both', before=0, after=160))

# P2
body.append(para([run(
    'Bei Merkle war ich technischer Hauptverantwortlicher für wichtige Kundenkonten und habe dabei mehr als 100 Marktforschungsprojekte end-to-end koordiniert, während ich gleichzeitig Python-Automatisierungsbibliotheken entwickelte, die den manuellen Arbeitsaufwand um ca. 40 % reduzierten. Zudem habe ich gemeinsam mit anderen eine JavaScript-Browsererweiterung entwickelt, die repetitive Abläufe in unserer Projektabwicklung automatisierte. Zuletzt entwickelte ich einen KI-gestützten Automatisierungs-Bot mit Python und Playwright, um zu zeigen, wie schnell praxistaugliche Tools entstehen können, wenn man KI-Werkzeuge mit einer klaren Problemdefinition kombiniert.',
    size=22)], align='both', before=0, after=160))

# P3
body.append(para([run(
    'Das Engagement von Siemens Mobility, die Schieneninfrastruktur durch Digitalisierung intelligenter und nachhaltiger zu gestalten, spricht mich sehr an. Der Projektmanagement-Kontext hier geht über reine Koordination hinaus – es geht darum, schnellere und besser informierte Entscheidungen in komplexen Ingenieurprogrammen zu ermöglichen. Genau dort können KI-Tools echten Mehrwert schaffen, und ich würde mich freuen, zur Identifikation und Entwicklung solcher Lösungen beizutragen.',
    size=22)], align='both', before=0, after=160))

# Closing sentence
body.append(para([run(
    'Ich freue mich darauf, diese Möglichkeit in einem persönlichen Gespräch zu besprechen. Vielen Dank für Ihre Zeit und Ihre Berücksichtigung.',
    size=22)], before=0, after=240))

# Sign-off
body.append(para([run('Mit freundlichen Grüßen,', size=22)], before=0, after=80))
body.append(para([run('Sanidhya Purohit', bold=True, size=22)], before=0, after=0))

# ── static XML files ───────────────────────────────────────────────────────────

CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
</Types>'''

RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

WORD_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="mailto:sanidhyapurohit2@gmail.com" TargetMode="External"/>
  <Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://linkedin.com/in/sanidhya-purohit-6b6653198" TargetMode="External"/>
  <Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://github.com/sanidhya31" TargetMode="External"/>
</Relationships>'''

STYLES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/>
        <w:sz w:val="22"/><w:szCs w:val="22"/>
        <w:color w:val="000000"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:spacing w:before="0" w:after="160" w:line="276" w:lineRule="auto"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
</w:styles>'''

SETTINGS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:defaultTabStop w:val="720"/>
</w:settings>'''

doc_body = '\n'.join(body)

DOCUMENT = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:body>
    {doc_body}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1080" w:right="1080" w:bottom="1080" w:left="1080"/>
    </w:sectPr>
  </w:body>
</w:document>'''

with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', CONTENT_TYPES)
    z.writestr('_rels/.rels', RELS)
    z.writestr('word/_rels/document.xml.rels', WORD_RELS)
    z.writestr('word/document.xml', DOCUMENT)
    z.writestr('word/styles.xml', STYLES)
    z.writestr('word/settings.xml', SETTINGS)

print(f"Saved: {OUTPUT}")
