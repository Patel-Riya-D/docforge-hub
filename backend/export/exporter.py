from docx import Document as DocxDocument
from io import BytesIO
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch



def generate_docx(draft):
    doc = DocxDocument()

    doc.add_heading(draft["source_document"]["document_name"], level=1)

    for section in draft["sections"]:
        doc.add_heading(section["name"], level=2)

        for block in section["blocks"]:

            if block["type"] == "paragraph":
                doc.add_paragraph(block["content"])

            elif block["type"] == "table":
                headers = block.get("headers", [])
                rows = block.get("rows", [])

                table = doc.add_table(rows=1, cols=len(headers))

                for i, header in enumerate(headers):
                    table.rows[0].cells[i].text = str(header)

                for row in rows:
                    row_cells = table.add_row().cells
                    for i, cell in enumerate(row):
                        row_cells[i].text = str(cell)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)

    return buffer

def generate_pdf(draft):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []

    styles = getSampleStyleSheet()

    elements.append(Paragraph(draft.document_name, styles["Heading1"]))
    elements.append(Spacer(1, 0.5 * inch))

    for section in draft["sections"]:
        elements.append(Paragraph(section["name"], styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))

        for block in section["blocks"]:

            if block["type"] == "paragraph":
                elements.append(Paragraph(block["content"], styles["Normal"]))
                elements.append(Spacer(1, 0.2 * inch))

            elif block["type"] == "table":
                from reportlab.platypus import Table

                data = [block["headers"]] + block["rows"]
                table = Table(data)

                elements.append(table)
                elements.append(Spacer(1, 0.3 * inch))

    doc.build(elements)
    buffer.seek(0)

    return buffer


def generate_xls(draft):
    data = []

    for section in draft["sections"]:
        combined = " ".join(
            block["content"]
            for block in section["blocks"]
            if block["type"] == "paragraph"
        )

        data.append({
            "Section": section["name"],
            "Content": combined
        })
    df = pd.DataFrame(data)

    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    return buffer
