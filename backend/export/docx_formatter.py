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

    # --- Title Page ---
    doc.add_paragraph("\n\n\n")

    title = doc.add_heading(doc_name, level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph("\n")

    meta_para = doc.add_paragraph()
    meta_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

    meta_para.add_run(f"Department: {department}\n")
    meta_para.add_run(f"Version: {version}\n")
    meta_para.add_run(f"Generated On: {datetime.now().strftime('%Y-%m-%d')}\n")

    doc.add_paragraph("\n\n")

    company_name = draft.get("source_document", {}).get("company_name", "")
    if company_name:
        company_para = doc.add_paragraph()
        company_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        company_para.add_run(company_name).bold = True

    doc.add_page_break()

    # ── Sections ───────────────────────────────
    for section in draft.get("sections", []):

        section_name = section.get("name", "")
        blocks = section.get("blocks", [])

        heading = doc.add_heading(section_name, level=1)
        heading.runs[0].bold = True

        doc.add_paragraph("")  # spacing

        # Remove duplicated heading from first paragraph if present
        if blocks and blocks[0].get("type") == "paragraph":
            first_text = blocks[0].get("content", "").strip()

            if first_text.lower().startswith(section_name.lower()):
                blocks[0]["content"] = first_text[len(section_name):].strip()

        for block in blocks:

            if not isinstance(block, dict):
                continue

            # 🔹 Special formatting for Definitions section
            if block.get("type") == "paragraph":

                if section_name.lower() == "definitions":
                    items = block.get("content", "").split(". ")
                    for item in items:
                        cleaned = item.strip()
                        if cleaned:
                            doc.add_paragraph(cleaned, style="List Bullet")
                else:
                    doc.add_paragraph(block.get("content", ""))

            elif block.get("type") == "table":
                headers = block.get("headers", [])
                rows = block.get("rows", [])

                if not headers:
                    continue

                table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
                table.style = "Table Grid"   # 👈 also add this for clean borders

                # Header row
                for col_idx, header in enumerate(headers):
                    table.rows[0].cells[col_idx].text = str(header)

                # Data rows
                for row_idx, row in enumerate(rows):
                    for col_idx, cell in enumerate(row):
                        table.rows[row_idx + 1].cells[col_idx].text = str(cell)

    # ── Save ───────────────────────────────────
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.read()