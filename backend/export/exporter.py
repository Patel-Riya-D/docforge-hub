from docx import Document as DocxDocument
from io import BytesIO
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch



def generate_docx(draft):
    doc = DocxDocument()

    doc.add_heading(draft.document_name, level=1)

    for section in draft.sections:
        doc.add_heading(section.section_name, level=2)
        doc.add_paragraph(section.content)

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

    for section in draft.sections:
        elements.append(Paragraph(section.section_name, styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph(section.content, styles["Normal"]))
        elements.append(Spacer(1, 0.5 * inch))

    doc.build(elements)
    buffer.seek(0)

    return buffer


def generate_xls(draft):
    data = []

    for section in draft.sections:
        data.append({
            "Section": section.section_name,
            "Content": section.content
        })

    df = pd.DataFrame(data)

    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    return buffer
