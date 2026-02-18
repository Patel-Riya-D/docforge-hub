"""
docx_formatter.py
─────────────────────────────────────────────────────────────────
Converts a DocForge draft dict into a properly formatted .docx file.

Place this at:  backend/export/docx_formatter.py

Usage:
    from backend.export.docx_formatter import build_docx
    docx_bytes = build_docx(draft)

The draft dict is the same object returned by generator.py:
    {
        "source_document": { "document_name", "internal_type", "department", ... },
        "version": "v1.0",
        "sections": [
            { "name": "Section Name", "content": "markdown text...", "mandatory": True },
            ...
        ]
    }
"""

import io
import re
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


# ════════════════════════════════════════════════════════════
# COLOUR PALETTE  (change these to match your brand)
# ════════════════════════════════════════════════════════════

BRAND_DARK   = RGBColor(0x1F, 0x35, 0x64)   # Dark navy   — cover title, H1
BRAND_MID    = RGBColor(0x2E, 0x75, 0xB6)   # Mid blue    — H2, table headers
BRAND_LIGHT  = RGBColor(0xD6, 0xE4, 0xF0)   # Light blue  — table header bg
BRAND_ACCENT = RGBColor(0x70, 0xAD, 0x47)   # Green       — "Ready for Approval" badge
TEXT_DARK    = RGBColor(0x1A, 0x1A, 0x2E)   # Near-black  — body text
TEXT_MID     = RGBColor(0x44, 0x44, 0x44)   # Dark grey   — sub text
WHITE        = RGBColor(0xFF, 0xFF, 0xFF)


# ════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ════════════════════════════════════════════════════════════

def _set_cell_bg(cell, hex_color: str):
    """Set table cell background colour via raw XML."""
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)


def _set_cell_borders(cell, color="CCCCCC", size="4"):
    """Add thin borders to a table cell."""
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for side in ("top", "left", "bottom", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"),   "single")
        el.set(qn("w:sz"),    size)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        tcBorders.append(el)
    tcPr.append(tcBorders)


def _paragraph_border_bottom(para, color="2E75B6", size="6"):
    """Add a bottom border line under a paragraph (used after H1)."""
    pPr  = para._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bot  = OxmlElement("w:bottom")
    bot.set(qn("w:val"),   "single")
    bot.set(qn("w:sz"),    size)
    bot.set(qn("w:space"), "1")
    bot.set(qn("w:color"), color)
    pBdr.append(bot)
    pPr.append(pBdr)


def _set_run_font(run, font_name="Calibri"):
    run.font.name = font_name
    r = run._r
    rPr = r.get_or_add_rPr()
    rFonts = OxmlElement("w:rFonts")
    rFonts.set(qn("w:ascii"),    font_name)
    rFonts.set(qn("w:hAnsi"),   font_name)
    rFonts.set(qn("w:eastAsia"), font_name)
    rPr.insert(0, rFonts)


def _add_page_break(doc):
    para = doc.add_paragraph()
    run  = para.add_run()
    run.add_break(docx_break_type())
    return para


def docx_break_type():
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "page")
    return br


def _add_page_break_proper(doc):
    """Add a proper page break paragraph."""
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after  = Pt(0)
    run = para.add_run()
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    br = OxmlElement("w:br")
    br.set(qn("w:type"), "page")
    run._r.append(br)
    return para


# ════════════════════════════════════════════════════════════
# COVER PAGE
# ════════════════════════════════════════════════════════════

def _build_cover_page(doc, draft: dict):
    """
    Builds a professional cover page:
    - Document title centred, large, dark navy
    - Subtitle (document type + department)
    - Meta table: Version, Date, Status, Risk Level
    - Horizontal rule
    """
    meta = draft.get("source_document", {})
    doc_name   = meta.get("document_name", "Document")
    doc_type   = meta.get("internal_type", "")
    department = meta.get("department", "")
    version    = draft.get("version", "v1.0")
    status     = draft.get("status", "DRAFT")
    risk       = meta.get("risk_level", "MEDIUM")
    generated  = draft.get("generation_metadata", {}).get("generated_at", "")

    # ── Spacer ─────────────────────────────────────────────
    for _ in range(6):
        sp = doc.add_paragraph()
        sp.paragraph_format.space_after = Pt(0)

    # ── Document type label ────────────────────────────────
    type_para = doc.add_paragraph()
    type_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    type_run = type_para.add_run(doc_type.upper())
    type_run.font.size  = Pt(11)
    type_run.font.bold  = True
    type_run.font.color.rgb = BRAND_MID
    type_run.font.name  = "Calibri"
    type_para.paragraph_format.space_after = Pt(8)

    # ── Document title ─────────────────────────────────────
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_para.add_run(doc_name)
    title_run.font.size  = Pt(28)
    title_run.font.bold  = True
    title_run.font.color.rgb = BRAND_DARK
    title_run.font.name  = "Calibri"
    title_para.paragraph_format.space_after = Pt(6)

    # ── Underline rule ─────────────────────────────────────
    rule_para = doc.add_paragraph()
    rule_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _paragraph_border_bottom(rule_para, color="2E75B6", size="12")
    rule_para.paragraph_format.space_after = Pt(16)

    # ── Department ─────────────────────────────────────────
    dept_para = doc.add_paragraph()
    dept_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    dept_run = dept_para.add_run(f"{department} Department")
    dept_run.font.size  = Pt(13)
    dept_run.font.color.rgb = TEXT_MID
    dept_run.font.name  = "Calibri"
    dept_para.paragraph_format.space_after = Pt(40)

    # ── Meta info table ────────────────────────────────────
    table = doc.add_table(rows=1, cols=4)
    table.style = "Table Grid"

    # Format date
    try:
        dt = datetime.fromisoformat(generated.replace("Z", "+00:00"))
        date_str = dt.strftime("%B %d, %Y")
    except Exception:
        date_str = datetime.now().strftime("%B %d, %Y")

    meta_items = [
        ("Version",    version),
        ("Date",       date_str),
        ("Status",     status),
        ("Risk Level", risk),
    ]

    row = table.rows[0]
    for i, (label, value) in enumerate(meta_items):
        cell = row.cells[i]
        _set_cell_bg(cell, "1F3564")
        _set_cell_borders(cell, color="1F3564")
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

        label_para = cell.paragraphs[0]
        label_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        label_run = label_para.add_run(label + "\n")
        label_run.font.size  = Pt(8)
        label_run.font.bold  = True
        label_run.font.color.rgb = WHITE
        label_run.font.name  = "Calibri"

        val_run = label_para.add_run(value)
        val_run.font.size  = Pt(11)
        val_run.font.bold  = True
        val_run.font.color.rgb = WHITE
        val_run.font.name  = "Calibri"

        label_para.paragraph_format.space_before = Pt(6)
        label_para.paragraph_format.space_after  = Pt(6)

    # ── Page break after cover ─────────────────────────────
    _add_page_break_proper(doc)


# ════════════════════════════════════════════════════════════
# HEADER  &  FOOTER
# ════════════════════════════════════════════════════════════

def _add_header(doc, draft: dict):
    """Adds a header with document name left and version right."""
    meta     = draft.get("source_document", {})
    doc_name = meta.get("document_name", "Document")
    version  = draft.get("version", "v1.0")

    section  = doc.sections[0]
    header   = section.header
    header.is_linked_to_previous = False

    para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    para.clear()
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT

    # Left: document name
    left_run = para.add_run(doc_name)
    left_run.font.size  = Pt(9)
    left_run.font.color.rgb = TEXT_MID
    left_run.font.name  = "Calibri"

    # Tab to right edge
    para.add_run("\t")

    # Right: version
    right_run = para.add_run(version)
    right_run.font.size  = Pt(9)
    right_run.font.color.rgb = TEXT_MID
    right_run.font.name  = "Calibri"

    # Tab stop at right margin
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    pPr    = para._p.get_or_add_pPr()
    tabs   = OxmlElement("w:tabs")
    tab    = OxmlElement("w:tab")
    tab.set(qn("w:val"), "right")
    tab.set(qn("w:pos"), "9360")   # Right margin DXA
    tabs.append(tab)
    pPr.append(tabs)

    # Bottom border on header
    _paragraph_border_bottom(para, color="2E75B6", size="4")


def _add_footer(doc):
    """Adds a footer with page numbers centred."""
    section = doc.sections[0]
    footer  = section.footer
    footer.is_linked_to_previous = False

    para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    para.clear()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # "Page X of Y"
    pre_run = para.add_run("Page ")
    pre_run.font.size = Pt(9)
    pre_run.font.color.rgb = TEXT_MID
    pre_run.font.name = "Calibri"

    # Page number field
    from docx.oxml import OxmlElement
    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.text = " PAGE "
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "separate")
    fldChar3 = OxmlElement("w:fldChar")
    fldChar3.set(qn("w:fldCharType"), "end")

    run = para.add_run()
    run.font.size = Pt(9)
    run.font.color.rgb = TEXT_MID
    run.font.name = "Calibri"
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)

    of_run = para.add_run(" of ")
    of_run.font.size = Pt(9)
    of_run.font.color.rgb = TEXT_MID
    of_run.font.name = "Calibri"

    # Total pages field
    fldChar4 = OxmlElement("w:fldChar")
    fldChar4.set(qn("w:fldCharType"), "begin")
    instrText2 = OxmlElement("w:instrText")
    instrText2.text = " NUMPAGES "
    fldChar5 = OxmlElement("w:fldChar")
    fldChar5.set(qn("w:fldCharType"), "separate")
    fldChar6 = OxmlElement("w:fldChar")
    fldChar6.set(qn("w:fldCharType"), "end")

    run2 = para.add_run()
    run2.font.size = Pt(9)
    run2.font.color.rgb = TEXT_MID
    run2.font.name = "Calibri"
    run2._r.append(fldChar4)
    run2._r.append(instrText2)
    run2._r.append(fldChar5)
    run2._r.append(fldChar6)


# ════════════════════════════════════════════════════════════
# MARKDOWN TABLE PARSER
# ════════════════════════════════════════════════════════════

def _parse_md_table(lines: list) -> tuple:
    """
    Parse a markdown table into (headers, rows).
    Handles | col | col | format.
    Returns: (list[str], list[list[str]])
    """
    data_rows = [l for l in lines if l.strip().startswith("|") and "---" not in l]
    if not data_rows:
        return [], []

    def parse_row(line):
        parts = [c.strip() for c in line.strip().strip("|").split("|")]
        return parts

    headers = parse_row(data_rows[0])
    rows    = [parse_row(r) for r in data_rows[1:]]
    return headers, rows


def _render_table(doc, headers: list, rows: list):
    """
    Renders a properly formatted Word table.
    - Header row: dark blue background, white bold text
    - Data rows: alternating light blue / white
    - All cells have borders and padding
    """
    if not headers:
        return

    col_count  = len(headers)
    page_width = 9360   # DXA: A4 with 1" margins
    col_width  = page_width // col_count

    table = doc.add_table(rows=1 + len(rows), cols=col_count)
    table.style = "Table Grid"

    # Set overall table width
    tbl    = table._tbl
    tblPr  = tbl.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)
    tblW   = OxmlElement("w:tblW")
    tblW.set(qn("w:w"),    str(page_width))
    tblW.set(qn("w:type"), "dxa")
    tblPr.append(tblW)

    # ── Header row ─────────────────────────────────────────
    hdr_row = table.rows[0]
    for i, hdr_text in enumerate(headers):
        cell = hdr_row.cells[i]
        _set_cell_bg(cell, "2E75B6")
        _set_cell_borders(cell, color="1F3564", size="6")

        # Set cell width
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        tcW  = OxmlElement("w:tcW")
        tcW.set(qn("w:w"),    str(col_width))
        tcW.set(qn("w:type"), "dxa")
        tcPr.append(tcW)

        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run  = para.add_run(str(hdr_text))
        run.font.bold      = True
        run.font.size      = Pt(10)
        run.font.color.rgb = WHITE
        run.font.name      = "Calibri"
        para.paragraph_format.space_before = Pt(4)
        para.paragraph_format.space_after  = Pt(4)

    # ── Data rows ──────────────────────────────────────────
    for r_idx, row_data in enumerate(rows):
        row  = table.rows[r_idx + 1]
        fill = "EBF3FB" if r_idx % 2 == 0 else "FFFFFF"

        for c_idx in range(col_count):
            cell      = row.cells[c_idx]
            cell_text = row_data[c_idx] if c_idx < len(row_data) else ""

            _set_cell_bg(cell, fill)
            _set_cell_borders(cell, color="CCCCCC", size="4")

            # Set cell width
            tc   = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tcW  = OxmlElement("w:tcW")
            tcW.set(qn("w:w"),    str(col_width))
            tcW.set(qn("w:type"), "dxa")
            tcPr.append(tcW)

            para = cell.paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run  = para.add_run(str(cell_text))
            run.font.size      = Pt(10)
            run.font.color.rgb = TEXT_DARK
            run.font.name      = "Calibri"
            para.paragraph_format.space_before = Pt(3)
            para.paragraph_format.space_after  = Pt(3)

    # Spacer after table
    sp = doc.add_paragraph()
    sp.paragraph_format.space_after = Pt(6)


# ════════════════════════════════════════════════════════════
# CONTENT PARSER
# Converts LLM markdown output into Word elements
# ════════════════════════════════════════════════════════════

def _render_content(doc, raw_content: str):
    """
    Parses LLM markdown output and renders into the Word document.

    Handles:
    - ### H3 headings
    - #### H4 headings
    - **bold** inline
    - Bullet lists (- item)
    - Numbered lists (1. item)
    - Markdown tables (| col | col |)
    - Plain paragraphs
    - Horizontal rules (---)
    """
    lines = raw_content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── Skip empty lines ───────────────────────────────
        if not stripped:
            i += 1
            continue

        # ── H3 heading ─────────────────────────────────────
        if stripped.startswith("### "):
            text = stripped[4:].strip()
            para = doc.add_paragraph(style="Heading 3")
            run  = para.add_run(text)
            run.font.bold  = True
            run.font.size  = Pt(12)
            run.font.color.rgb = BRAND_MID
            run.font.name  = "Calibri"
            para.paragraph_format.space_before = Pt(12)
            para.paragraph_format.space_after  = Pt(4)
            i += 1
            continue

        # ── H4 heading ─────────────────────────────────────
        if stripped.startswith("#### "):
            text = stripped[5:].strip()
            para = doc.add_paragraph()
            run  = para.add_run(text)
            run.font.bold  = True
            run.font.size  = Pt(11)
            run.font.color.rgb = TEXT_DARK
            run.font.name  = "Calibri"
            para.paragraph_format.space_before = Pt(8)
            para.paragraph_format.space_after  = Pt(2)
            i += 1
            continue

        # ── Horizontal rule ────────────────────────────────
        if stripped in ("---", "___", "***"):
            para = doc.add_paragraph()
            _paragraph_border_bottom(para, color="CCCCCC", size="4")
            para.paragraph_format.space_before = Pt(4)
            para.paragraph_format.space_after  = Pt(4)
            i += 1
            continue

        # ── Markdown table ─────────────────────────────────
        if stripped.startswith("|"):
            # Collect all table lines
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            headers, rows = _parse_md_table(table_lines)
            if headers:
                _render_table(doc, headers, rows)
            continue

        # ── Bullet list ─────────────────────────────────────
        if stripped.startswith("- ") or stripped.startswith("* "):
            text = stripped[2:].strip()
            para = doc.add_paragraph(style="List Bullet")
            _add_inline_formatted_run(para, text)
            para.paragraph_format.space_before = Pt(2)
            para.paragraph_format.space_after  = Pt(2)
            i += 1
            continue

        # ── Numbered list ───────────────────────────────────
        num_match = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if num_match:
            text = num_match.group(2).strip()
            para = doc.add_paragraph(style="List Number")
            _add_inline_formatted_run(para, text)
            para.paragraph_format.space_before = Pt(2)
            para.paragraph_format.space_after  = Pt(2)
            i += 1
            continue

        # ── Plain paragraph ────────────────────────────────
        para = doc.add_paragraph()
        _add_inline_formatted_run(para, stripped)
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after  = Pt(6)
        i += 1


def _add_inline_formatted_run(para, text: str):
    """
    Adds text to a paragraph, handling inline **bold** and *italic*.
    """
    # Split by **bold** and *italic* markers
    parts = re.split(r"(\*\*.*?\*\*|\*.*?\*)", text)
    for part in parts:
        if part.startswith("**") and part.endswith("**"):
            run = para.add_run(part[2:-2])
            run.font.bold = True
            run.font.size = Pt(11)
            run.font.name = "Calibri"
            run.font.color.rgb = TEXT_DARK
        elif part.startswith("*") and part.endswith("*"):
            run = para.add_run(part[1:-1])
            run.font.italic = True
            run.font.size   = Pt(11)
            run.font.name   = "Calibri"
            run.font.color.rgb = TEXT_DARK
        elif part:
            run = para.add_run(part)
            run.font.size = Pt(11)
            run.font.name = "Calibri"
            run.font.color.rgb = TEXT_DARK


# ════════════════════════════════════════════════════════════
# SECTION HEADING
# ════════════════════════════════════════════════════════════

def _add_section_heading(doc, section_name: str):
    """
    Renders an H2 section heading:
    - Bold, 14pt, brand mid-blue
    - Bottom border rule
    """
    para = doc.add_paragraph(style="Heading 2")
    run  = para.add_run(section_name)
    run.font.bold      = True
    run.font.size      = Pt(14)
    run.font.color.rgb = BRAND_DARK
    run.font.name      = "Calibri"
    para.paragraph_format.space_before = Pt(16)
    para.paragraph_format.space_after  = Pt(6)
    _paragraph_border_bottom(para, color="2E75B6", size="6")


# ════════════════════════════════════════════════════════════
# DOCUMENT STYLES SETUP
# ════════════════════════════════════════════════════════════

def _setup_styles(doc):
    """Configure base document styles."""
    # Default body font
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    # Page margins: 1 inch all sides
    for section in doc.sections:
        section.top_margin    = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin   = Inches(1)
        section.right_margin  = Inches(1)


# ════════════════════════════════════════════════════════════
# CONTENT CLEANER
# Strips LLM prompt leaks before rendering
# ════════════════════════════════════════════════════════════

def _clean_content(content: str) -> str:
    """
    Removes prompt artifacts that should never appear in the final doc.
    Add more patterns here as you discover new leaks.
    """
    patterns = [
        # Instruction leaks
        r"_Instructions:.*?_",
        r"\*Instructions:.*?\*",
        # Example blocks
        r"_Example:?_[\s\S]*?(?=\n##|\Z)",
        r"\*\*Example:?\*\*[\s\S]*?(?=\n##|\Z)",
        r"\\-\\-\\-\\\n\\\\\\*\\\\\\*Example",
        # Policy contamination (wrong doc type bleed)
        r"_?This section constitutes a binding policy requirement\.[^_]*_?",
        r"_?All employees are subject to this policy from their start date\._?",
        r"_?This policy is reviewed annually by the Compliance team\._?",
        r"_?Violations of this policy may result in disciplinary action[^_\n]*_?",
        r"_?This document confirms your receipt[^_\n]*_?",
        r"By signing below, you acknowledge[^\n]*\n",
        # Reference framework lines
        r"_?Reference Framework: SOC 2_?",
        r"_?This section references(?: the)? SOC 2[^_\n]*_?",
        r"_?This section aligns with SOC 2[^_\n]*_?",
        r"_?This policy aligns with SOC 2[^_\n]*_?",
        r"_?Reference: SOC 2[^_\n]*_?",
        # Italicised prompt artifacts
        r"\\\_[^\\]*\\\_",
    ]

    for pattern in patterns:
        content = re.sub(pattern, "", content, flags=re.IGNORECASE | re.MULTILINE)

    # Clean up multiple blank lines left after removals
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


# ════════════════════════════════════════════════════════════
# MAIN PUBLIC FUNCTION
# ════════════════════════════════════════════════════════════

def build_docx(draft: dict) -> bytes:
    """
    Converts a DocForge draft dict into a fully formatted .docx file.

    Args:
        draft: The draft dict returned by generator.generate_draft()

    Returns:
        bytes: The .docx file as bytes (ready for HTTP response or disk write)

    Example:
        docx_bytes = build_docx(draft)
        with open("output.docx", "wb") as f:
            f.write(docx_bytes)
    """
    doc = Document()
    _setup_styles(doc)

    # ── Cover page ─────────────────────────────────────────
    _build_cover_page(doc, draft)

    # ── Header + Footer ────────────────────────────────────
    _add_header(doc, draft)
    _add_footer(doc)

    # ── Sections ───────────────────────────────────────────
    sections = draft.get("sections", [])

    for idx, section in enumerate(sections):
        section_name = section.get("name", f"Section {idx + 1}")
        raw_content  = section.get("content", "")

        if not raw_content.strip():
            continue

        # Clean prompt artifacts first
        cleaned_content = _clean_content(raw_content)

        # Section heading (H2)
        _add_section_heading(doc, section_name)

        # Section body
        _render_content(doc, cleaned_content)

        # Page break after each section (except last)
        if idx < len(sections) - 1:
            _add_page_break_proper(doc)

    # ── Save to bytes ──────────────────────────────────────
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()


# ════════════════════════════════════════════════════════════
# FASTAPI EXPORT ROUTE  (add this to your main.py / router)
# ════════════════════════════════════════════════════════════
"""
Add this to your FastAPI router:

from fastapi import Response
from backend.export.docx_formatter import build_docx
from backend.db import get_draft_by_id   # your DB fetch function

@app.get("/documents/export/{draft_id}/docx")
def export_docx(draft_id: str):
    draft = get_draft_by_id(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    docx_bytes = build_docx(draft)
    filename   = draft["source_document"]["document_name"].replace(" ", "_") + ".docx"

    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
"""