"""Builds small real PDF and Word files for tests."""

import io

from docx import Document as WordDocument
from fpdf import FPDF


def make_pdf(pages: list[str]) -> bytes:
    """One PDF page per string. An empty string makes a page with no text, like a scan."""
    pdf = FPDF()
    pdf.set_font("Helvetica", size=12)
    for text in pages:
        pdf.add_page()
        if text:
            pdf.multi_cell(0, 10, text)
    return bytes(pdf.output())


def make_docx(blocks: list[tuple[str, object]]) -> bytes:
    """Blocks are ("Heading 1", "text"), ("Normal", "text") or ("table", [["a", "b"], ["c", "d"]])."""
    document = WordDocument()
    for kind, content in blocks:
        if kind == "table":
            rows = content
            table = document.add_table(rows=len(rows), cols=len(rows[0]))
            for row_number, row in enumerate(rows):
                for column_number, value in enumerate(row):
                    table.cell(row_number, column_number).text = value
        elif kind.startswith("Heading"):
            document.add_heading(content, level=int(kind.split()[1]))
        else:
            document.add_paragraph(content)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()
