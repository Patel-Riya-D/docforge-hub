import io
import re
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def build_docx(draft: dict) -> bytes:
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()

    # ── Title Page ─────────────────────────────
    meta = draft.get("source_document", {})
    doc_name = meta.get("document_name", "Document")
    department = meta.get("department", "")
    version = draft.get("version", "v1.0")

    title = doc.add_heading(doc_name, level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(f"Department: {department}")
    doc.add_paragraph(f"Version: {version}")

    # ── Sections ───────────────────────────────
    for section in draft.get("sections", []):
        section_name = section.get("name", "")
        content = section.get("content", "")

        if not content.strip():
            continue

        # Section Heading
        doc.add_heading(section_name, level=1)

        # Section Body
        for line in content.split("\n"):
            if line.strip():
                doc.add_paragraph(line.strip())

        doc.add_page_break()

    # ── Save ───────────────────────────────────
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()
