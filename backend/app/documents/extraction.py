"""Turns an uploaded file into plain-text sections, keeping page numbers or headings for citations."""

import re
from dataclasses import dataclass
from pathlib import Path

from docx import Document as open_docx
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader
from pypdf.errors import PdfReadError

# "## Refunds" or "## Refunds ##" -> "Refunds". "#hashtag" (no space) is not a heading.
MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")
MAX_HEADING_LENGTH = 500


class ExtractionError(Exception):
    """The file can't be turned into text. The message is shown to the user."""


@dataclass(frozen=True)
class Section:
    text: str
    page_number: int | None = None
    heading: str | None = None


@dataclass(frozen=True)
class ExtractedText:
    sections: list[Section]
    page_count: int | None


def extract_text(path: Path, file_type: str, max_pdf_pages: int) -> ExtractedText:
    if file_type == "pdf":
        return _extract_pdf(path, max_pdf_pages)
    if file_type == "docx":
        sections = _extract_docx(path)
    else:
        text = path.read_text(encoding="utf-8-sig")  # "-sig" drops the invisible BOM some editors add
        sections = _split_markdown(text) if file_type == "md" else [Section(text)]
    sections = _clean(sections)
    if not sections:
        raise ExtractionError("No text found in this file.")
    return ExtractedText(sections, page_count=None)


def _clean(sections: list[Section]) -> list[Section]:
    # Postgres can't store the NUL character, and some PDFs contain it. Empty sections are dropped.
    cleaned = [Section(s.text.replace("\x00", "").strip(), s.page_number, s.heading) for s in sections]
    return [section for section in cleaned if section.text]


def _extract_pdf(path: Path, max_pages: int) -> ExtractedText:
    try:
        reader = PdfReader(path)
        if reader.is_encrypted and not reader.decrypt(""):
            raise ExtractionError("This PDF is password-protected.")
        page_count = len(reader.pages)
        if page_count > max_pages:
            raise ExtractionError(f"PDFs can have at most {max_pages} pages.")
        sections = [
            Section(page.extract_text() or "", page_number=number)
            for number, page in enumerate(reader.pages, start=1)
        ]
    except PdfReadError:
        raise ExtractionError("This PDF couldn't be read.") from None
    sections = _clean(sections)
    if not sections:
        raise ExtractionError("No text found, scanned PDFs aren't supported yet.")
    return ExtractedText(sections, page_count)


def _extract_docx(path: Path) -> list[Section]:
    sections: list[Section] = []
    heading: str | None = None
    lines: list[str] = []
    # iter_inner_content gives paragraphs and tables in the order they appear.
    for block in open_docx(str(path)).iter_inner_content():
        if isinstance(block, Table):
            lines.extend(" | ".join(cell.text.strip() for cell in row.cells) for row in block.rows)
        elif _is_heading(block):
            sections.append(Section("\n".join(lines), heading=heading))
            heading, lines = block.text.strip()[:MAX_HEADING_LENGTH], []
        else:
            lines.append(block.text)
    sections.append(Section("\n".join(lines), heading=heading))
    return sections


def _is_heading(paragraph: Paragraph) -> bool:
    style = paragraph.style.name if paragraph.style is not None else ""
    return (style.startswith("Heading") or style == "Title") and bool(paragraph.text.strip())


def _split_markdown(text: str) -> list[Section]:
    sections: list[Section] = []
    heading: str | None = None
    lines: list[str] = []
    inside_code = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            inside_code = not inside_code
        match = None if inside_code else MARKDOWN_HEADING.match(line)
        if match:
            sections.append(Section("\n".join(lines), heading=heading))
            heading, lines = match.group(1)[:MAX_HEADING_LENGTH], []
        else:
            lines.append(line)
    sections.append(Section("\n".join(lines), heading=heading))
    return sections
