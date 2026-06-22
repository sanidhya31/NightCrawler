"""
Creates Ganya_Maheshwarappa_NLI.docx matching the Machine Translation letterhead style.
Uses only Python standard library (zipfile + xml strings).
"""

import zipfile
import os

OUTPUT = r"D:\Downloads\Ganya_Maheshwarappa_NLI.docx"

# ── helpers ────────────────────────────────────────────────────────────────────

def rpr(bold=False, underline=False, size=24, font="Times New Roman", color=None, hyperlink=False):
    parts = [f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}"/>']
    parts.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    if bold:       parts.append('<w:b/><w:bCs/>')
    if underline:  parts.append('<w:u w:val="single"/>')
    if color:      parts.append(f'<w:color w:val="{color}"/>')
    if hyperlink:  parts.append('<w:rStyle w:val="Hyperlink"/>')
    return '<w:rPr>' + ''.join(parts) + '</w:rPr>'

def run(text, bold=False, underline=False, size=24, color=None, hyperlink=False, preserve=False):
    sp = ' xml:space="preserve"' if preserve else ''
    rp = rpr(bold=bold, underline=underline, size=size, color=color, hyperlink=hyperlink)
    return f'<w:r>{rp}<w:t{sp}>{text}</w:t></w:r>'

def para(children, align=None, spacing_before=0, spacing_after=120, indent_left=None):
    ppr_parts = []
    if align:                ppr_parts.append(f'<w:jc w:val="{align}"/>')
    if spacing_before or spacing_after:
        ppr_parts.append(f'<w:spacing w:before="{spacing_before}" w:after="{spacing_after}"/>')
    if indent_left:
        ppr_parts.append(f'<w:ind w:left="{indent_left}" w:hanging="360"/>')
    ppr = '<w:pPr>' + ''.join(ppr_parts) + '</w:pPr>' if ppr_parts else ''
    return f'<w:p>{ppr}{"".join(children)}</w:p>'

def bullet_para(label, text, size=24):
    """Bold label + normal explanation, indented bullet style."""
    children = [
        '<w:pPr>'
        '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
        f'<w:spacing w:before="60" w:after="60"/>'
        '</w:pPr>',
        run(label, bold=True, size=size),
        run(' ', preserve=True, size=size),
        run(text, size=size),
    ]
    return '<w:p>' + ''.join(children) + '</w:p>'

def sub_bullet_para(text, size=24):
    """Normal sub-bullet for continuation text after a bold label."""
    children = [
        '<w:pPr>'
        '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
        f'<w:spacing w:before="0" w:after="80"/>'
        '</w:pPr>',
        run(text, size=size),
    ]
    return '<w:p>' + ''.join(children) + '</w:p>'

def heading(text, size=24):
    return para([run(text, bold=True, size=size)], spacing_before=160, spacing_after=80)

def empty():
    return '<w:p><w:pPr><w:spacing w:before="0" w:after="80"/></w:pPr></w:p>'

# ── document body ──────────────────────────────────────────────────────────────

body = []

# Title
body.append(para([run('Trends in Natural Language Processing', bold=True, underline=True, size=28)],
                 align='center', spacing_before=0, spacing_after=40))
body.append(para([run('NLI (June 8th)', bold=True, underline=True, size=24)],
                 align='center', spacing_before=0, spacing_after=200))

# Student info — right aligned
body.append(para([run('Ganya Maheshwarappa', bold=True, size=24)], align='right', spacing_after=40))
body.append(para([run('Immatriculation number: 1867726', bold=True, size=24)], align='right', spacing_after=40))
body.append(para([run('s4gamahe@uni-trier.de', size=24, color='1155CC', hyperlink=True)], align='right', spacing_after=200))

# ── Q1 ──────────────────────────────────────────────────────────────────────
body.append(heading('1. List and describe some common application areas for NLI systems.'))

body.append(para([
    run('Natural Language Inference has grown well beyond the lab — it quietly powers a range of real-world tasks that require a system to understand the logical relationship between pieces of text. Here are some of the most prominent application areas:', size=24)
], spacing_before=0, spacing_after=100))

body.append(bullet_para(
    'Fact Verification and Fake News Detection:',
    'One of the most impactful uses of NLI is checking whether a claim (the hypothesis) is supported or refuted by a reference text (the premise). Systems like FEVER use NLI to label claims as SUPPORTED, REFUTED, or NOT ENOUGH INFO based on Wikipedia evidence. In our notebook, the DeBERTa model correctly identified contradictions with 99.8% confidence — the same principle applies when verifying news headlines against source articles.'
))

body.append(bullet_para(
    'Semantic Search and Information Retrieval:',
    'Traditional keyword search struggles to capture meaning. NLI models can re-rank search results by checking whether a retrieved passage actually entails the query\'s intent. This moves retrieval from lexical matching to genuine semantic understanding.'
))

body.append(bullet_para(
    'Question Answering:',
    'NLI serves as a verification layer in QA pipelines. After a candidate answer span is extracted (as demonstrated in the notebook using DistilBERT on SQuAD), an NLI model can confirm whether the context truly entails that answer — catching cases where the span extraction is superficially plausible but logically incorrect.'
))

body.append(bullet_para(
    'Summarization Faithfulness Checking:',
    'Abstractive summarization models sometimes hallucinate facts not present in the source document. NLI provides a natural way to catch this: if the summary (hypothesis) is contradicted by the original text (premise), it contains a hallucination. This is increasingly used in production summarization pipelines.'
))

body.append(bullet_para(
    'Dialogue Systems and Chatbot Consistency:',
    'In multi-turn conversations, a chatbot should not contradict itself. NLI can detect when a new model response conflicts with something stated earlier in the conversation, helping maintain coherent and trustworthy dialogue.'
))

body.append(bullet_para(
    'Clinical and Legal Reasoning:',
    'In medicine, NLI can check whether a patient\'s symptoms (premise) entail a particular diagnosis (hypothesis). In law, it can assess whether a contract clause entails or contradicts a regulatory requirement. These domains benefit greatly from the three-way classification that NLI provides.'
))

body.append(empty())

# ── Q2 ──────────────────────────────────────────────────────────────────────
body.append(heading('2. Briefly describe the common benchmark datasets for NLI.'))

body.append(para([
    run('Several benchmark datasets have shaped how NLI models are trained and evaluated. Each brings a distinct character in terms of size, domain, and difficulty:', size=24)
], spacing_before=0, spacing_after=100))

body.append(bullet_para(
    'SNLI — Stanford Natural Language Inference (2015):',
    'The foundational NLI dataset. It contains approximately 570,000 premise-hypothesis pairs, where premises are image captions from the Flickr30k corpus and hypotheses were written by crowdworkers. Each pair is labeled as ENTAILMENT, CONTRADICTION, or NEUTRAL. SNLI was the first large-scale NLI benchmark and is still widely used as a baseline.'
))

body.append(bullet_para(
    'MultiNLI — Multi-Genre NLI (2018):',
    'An extension of SNLI that deliberately spans ten different genres of text, including fiction, government reports, telephone conversations, and travel writing. This makes it far more challenging than SNLI because models must generalize across writing styles and registers. It is the primary benchmark in the GLUE evaluation suite.'
))

body.append(bullet_para(
    'RTE — Recognizing Textual Entailment:',
    'A smaller, older benchmark included in GLUE and SuperGLUE. It uses a binary classification setup (entailment vs. non-entailment) and contains only a few thousand examples, making it a test of data efficiency. Despite its age, it remains a standard evaluation checkpoint.'
))

body.append(bullet_para(
    'ANLI — Adversarial NLI (2020):',
    'Collected through an adversarial human-in-the-loop process across three rounds of increasing difficulty. Annotators were shown model predictions and specifically crafted examples to fool the current best model. As a result, ANLI is significantly harder than SNLI or MultiNLI and exposes brittleness that standard benchmarks miss.'
))

body.append(bullet_para(
    'SciTail (2018):',
    'A domain-specific dataset built from science exam questions and web text. It uses a binary setup (entails vs. neutral) and is notable because the premises and hypotheses come from very different stylistic sources, making lexical overlap a less reliable shortcut.'
))

body.append(bullet_para(
    'FEVER — Fact Extraction and VERification (2018):',
    'Though technically a fact-verification dataset, FEVER is closely related to NLI. Claims are labeled as SUPPORTED, REFUTED, or NOT ENOUGH INFO based on Wikipedia evidence passages. It bridges NLI research with real-world misinformation detection.'
))

body.append(empty())

# ── Q3 ──────────────────────────────────────────────────────────────────────
body.append(heading('3. How do current NLI approaches compare to human performance on NLI datasets?'))

body.append(para([
    run('The short answer is: on standard benchmarks, models now match or exceed human-reported accuracy — but this headline number is misleading. The picture is more nuanced once you look at adversarial and out-of-distribution settings.', size=24)
], spacing_before=0, spacing_after=100))

body.append(bullet_para(
    'On Standard Benchmarks — Models Surpass Humans:',
    'Human accuracy on SNLI is typically reported at around 87–91%, reflecting genuine annotator disagreement. State-of-the-art models such as DeBERTa (the same model used in our notebook) and RoBERTa now achieve over 91–93% on SNLI and around 90% on MultiNLI, technically exceeding the human baseline. Our notebook confirmed this capability: DeBERTa correctly classified all three examples with confidence above 99%, assigning ENTAILMENT, CONTRADICTION, and NEUTRAL with high precision.'
))

body.append(bullet_para(
    'Models Exploit Spurious Correlations:',
    'Despite their impressive scores, models are known to rely on shortcuts rather than true reasoning. Studies have shown that words like "not," "never," and "nobody" are strong predictors of CONTRADICTION, while high lexical overlap between premise and hypothesis strongly signals ENTAILMENT. A model that has learned these surface patterns can score well without understanding the actual logical relationship.'
))

body.append(bullet_para(
    'On Adversarial Datasets — A Significant Gap Remains:',
    'When evaluated on ANLI, model accuracy drops sharply — often to the 40–65% range depending on the round of adversarial collection — while human performance stays well above 80%. The HANS dataset further revealed that models fail dramatically on structurally valid but lexically misleading examples that humans handle effortlessly. This gap is the clearest evidence that high benchmark scores do not equal genuine language understanding.'
))

body.append(bullet_para(
    'What This Means in Practice:',
    'Current NLI systems are powerful tools but fragile reasoners. They work well on in-distribution data (as our notebook experiment showed) but should be combined with additional safeguards when deployed in high-stakes domains. The field is actively working on making models more robust through adversarial training, counterfactual data augmentation, and improved pretraining objectives.'
))

body.append(empty())

# ── assemble XML ──────────────────────────────────────────────────────────────

CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
  <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
</Types>'''

RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

WORD_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
</Relationships>'''

STYLES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>
        <w:sz w:val="24"/><w:szCs w:val="24"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr>
        <w:jc w:val="both"/>
        <w:spacing w:before="0" w:after="120"/>
      </w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="character" w:styleId="Hyperlink">
    <w:name w:val="Hyperlink"/>
    <w:rPr>
      <w:color w:val="1155CC"/>
      <w:u w:val="single"/>
    </w:rPr>
  </w:style>
</w:styles>'''

NUMBERING = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:abstractNum w:abstractNumId="0">
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/>
      <w:numFmt w:val="bullet"/>
      <w:lvlText w:val="&#x2022;"/>
      <w:lvlJc w:val="left"/>
      <w:pPr>
        <w:ind w:left="720" w:hanging="360"/>
      </w:pPr>
      <w:rPr>
        <w:rFonts w:ascii="Symbol" w:hAnsi="Symbol"/>
        <w:sz w:val="24"/>
      </w:rPr>
    </w:lvl>
  </w:abstractNum>
  <w:num w:numId="1">
    <w:abstractNumId w:val="0"/>
  </w:num>
</w:numbering>'''

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
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
    </w:sectPr>
  </w:body>
</w:document>'''

# ── write zip ─────────────────────────────────────────────────────────────────

with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', CONTENT_TYPES)
    z.writestr('_rels/.rels', RELS)
    z.writestr('word/_rels/document.xml.rels', WORD_RELS)
    z.writestr('word/document.xml', DOCUMENT)
    z.writestr('word/styles.xml', STYLES)
    z.writestr('word/numbering.xml', NUMBERING)
    z.writestr('word/settings.xml', SETTINGS)

print(f"Created: {OUTPUT}")
