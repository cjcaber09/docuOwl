import pytest

from app.documents.extraction import ExtractionError, Section, extract_text
from tests.sample_files import make_docx, make_pdf


def write(tmp_path, content: bytes):
    path = tmp_path / "upload"
    path.write_bytes(content)
    return path


def test_pdf_text_keeps_its_page_numbers(tmp_path):
    path = write(tmp_path, make_pdf(["Refunds take 30 days.", "Annual plans are pro rata."]))

    extracted = extract_text(path, "pdf", max_pdf_pages=500)

    assert extracted.page_count == 2
    assert [section.page_number for section in extracted.sections] == [1, 2]
    assert "Refunds take 30 days." in extracted.sections[0].text


def test_pdf_without_text_is_treated_as_a_scan(tmp_path):
    path = write(tmp_path, make_pdf([""]))

    with pytest.raises(ExtractionError, match="scanned PDFs"):
        extract_text(path, "pdf", max_pdf_pages=500)


def test_pdf_with_too_many_pages_is_refused(tmp_path):
    path = write(tmp_path, make_pdf(["a", "b", "c"]))

    with pytest.raises(ExtractionError, match="at most 2 pages"):
        extract_text(path, "pdf", max_pdf_pages=2)


def test_docx_sections_follow_headings_and_keep_tables(tmp_path):
    path = write(
        tmp_path,
        make_docx(
            [
                ("Heading 1", "Refunds"),
                ("Normal", "Within 30 days."),
                ("table", [["Plan", "Price"], ["Pro", "$10"]]),
                ("Heading 2", "Annual"),
                ("Normal", "Pro rata."),
            ]
        ),
    )

    extracted = extract_text(path, "docx", max_pdf_pages=500)

    assert extracted.page_count is None
    assert extracted.sections == [
        Section("Within 30 days.\nPlan | Price\nPro | $10", heading="Refunds"),
        Section("Pro rata.", heading="Annual"),
    ]


def test_markdown_sections_follow_headings_but_not_inside_code(tmp_path):
    text = "Intro line\n# Refunds\nWithin 30 days.\n```\n# not a heading\n```\n## Annual ##\nPro rata."
    path = write(tmp_path, text.encode("utf-8"))

    extracted = extract_text(path, "md", max_pdf_pages=500)

    assert extracted.sections == [
        Section("Intro line"),
        Section("Within 30 days.\n```\n# not a heading\n```", heading="Refunds"),
        Section("Pro rata.", heading="Annual"),
    ]


def test_plain_text_is_one_section_without_bom_or_nul(tmp_path):
    path = write(tmp_path, "﻿Hello\x00 world".encode("utf-8"))

    extracted = extract_text(path, "txt", max_pdf_pages=500)

    assert extracted.sections == [Section("Hello world")]


def test_file_with_only_whitespace_has_no_text(tmp_path):
    path = write(tmp_path, b"  \n\n  ")

    with pytest.raises(ExtractionError, match="No text found"):
        extract_text(path, "txt", max_pdf_pages=500)
