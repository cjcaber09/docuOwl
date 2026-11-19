import hashlib
import io
import zipfile

import pytest

from app.documents.validation import (
    UPLOAD_DIR,
    UploadRejected,
    check_contents,
    clean_filename,
    file_type_from_name,
    save_upload,
)

ONE_MB = 1024 * 1024


def test_clean_filename_keeps_only_the_name():
    assert clean_filename("C:\\fakepath\\Report.pdf") == "Report.pdf"
    assert clean_filename("../../etc/notes.md") == "notes.md"
    assert clean_filename("") == "untitled"


def test_file_type_comes_from_the_extension():
    assert file_type_from_name("Q3.PDF") == "pdf"
    with pytest.raises(UploadRejected, match="PDF, DOCX, TXT and MD"):
        file_type_from_name("setup.exe")


def test_save_upload_hashes_and_measures_the_file():
    saved = save_upload(io.BytesIO(b"hello"), max_mb=1)
    try:
        assert saved.size == 5
        assert saved.content_hash == hashlib.sha256(b"hello").hexdigest()
        assert saved.path.read_bytes() == b"hello"
    finally:
        saved.path.unlink()


def test_too_large_upload_is_rejected_and_leaves_no_file():
    before = set(UPLOAD_DIR.glob("*")) if UPLOAD_DIR.exists() else set()

    with pytest.raises(UploadRejected, match="at most 1 MB"):
        save_upload(io.BytesIO(b"x" * (ONE_MB + 1)), max_mb=1)

    assert set(UPLOAD_DIR.glob("*")) == before


def test_empty_upload_is_rejected():
    with pytest.raises(UploadRejected, match="empty"):
        save_upload(io.BytesIO(b""), max_mb=1)


def test_a_renamed_program_is_not_a_pdf(tmp_path):
    fake = tmp_path / "fake.pdf"
    fake.write_bytes(b"MZ this is really a program")

    with pytest.raises(UploadRejected, match="valid PDF"):
        check_contents(fake, "pdf")


def test_docx_must_be_a_word_zip(tmp_path):
    not_word = tmp_path / "a.docx"
    with zipfile.ZipFile(not_word, "w") as archive:
        archive.writestr("hello.txt", "hi")

    with pytest.raises(UploadRejected, match="valid DOCX"):
        check_contents(not_word, "docx")


def test_text_files_must_be_utf8(tmp_path):
    latin = tmp_path / "a.txt"
    latin.write_bytes("café".encode("latin-1"))
    good = tmp_path / "b.md"
    good.write_text("# café", encoding="utf-8")

    with pytest.raises(UploadRejected, match="UTF-8"):
        check_contents(latin, "txt")
    check_contents(good, "md")  # no error
