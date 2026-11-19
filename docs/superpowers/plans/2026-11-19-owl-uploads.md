# Owl Uploads Implementation Plan (build step 6)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Users upload PDF, DOCX, TXT and MD files on the Documents page; Owl checks them, turns them into searchable chunks with Voyage embeddings in the background, lists them with live status, and deletes them on request.

**Architecture:** A new `backend/app/documents/` package, one file per job: `validation.py` (checks at upload time), `extraction.py` (file → text sections), `chunking.py` (sections → ~500-word chunks), `embeddings.py` (chunks → vectors via Voyage's REST API), `processing.py` (the background task tying those together), `schemas.py` and `routes.py` (the HTTP API). The upload request only validates, hashes, saves a temporary file and creates a `processing` row; FastAPI's `BackgroundTasks` does the slow part after the response. The frontend replaces the sample documents with TanStack Query hooks that poll while anything is processing.

**Tech Stack:** FastAPI (`UploadFile`, `BackgroundTasks`), pypdf, python-docx, httpx (already installed with FastAPI), Voyage AI `voyage-4` (1,024 dimensions), pgvector; fpdf2 (tests only, to build sample PDFs). Frontend: TanStack Query, sonner toasts, Vitest + React Testing Library.

## Global Constraints

- Learner mode: before each task, explain the files and the new ideas in plain words; the owner checks each task before the next.
- Types: PDF, DOCX, TXT, MD. PDF and DOCX are checked by file contents (signature), not just the extension; TXT and MD must be valid UTF-8 text.
- Limits: 20 MB per file, 500 pages, 50 documents per user (configurable). DOCX decompressed size is capped.
- Duplicates: rejected if the same user already has a file with the same SHA-256 hash ("You already uploaded this file as 'X'"). If that copy is still `processing`: "This file is still being processed." If that copy is `failed`, the new upload replaces it in one transaction.
- The background task always deletes the temporary file when it ends (success or failure).
- A PDF with no extractable text fails with "No text found, scanned PDFs aren't supported yet."
- Split into ~500-word chunks with ~50-word overlap, each labelled with its page (PDF) or nearest heading; the position is always stored ("part 3 of 12" is built from it in step 7).
- Embed chunks with Voyage in batches (input type `document`). Before saving, check the document still exists; if it was deleted meanwhile, stop quietly.
- Every query is filtered by the logged-in user's ID. Another user's document answers 404, never 403.
- Errors are plain user-facing messages; technical detail goes only to server logs.
- Tests never call Voyage (a fake embedder stands in) and never touch the real `owl` database.
- RLS stays on for every public table. This step adds no tables and no migration.
- Out of scope here (build step 8): keeping originals in a bucket, the Download endpoint, the orphan-cleanup script.
- Expected test counts: backend 49 → 51 (T1) → 59 (T2) → 66 (T3) → 70 (T4) → 75 (T5) → 81 (T6) → 96 (T7). Frontend 9 → 15 (T8).

## File map

| File | New? | Responsibility |
|---|---|---|
| `backend/app/config.py` | change | Voyage key, model name, upload limits |
| `backend/app/documents/__init__.py` | new | Marks the package (empty) |
| `backend/app/documents/validation.py` | new | `UploadRejected`, file name and type checks, streaming save + SHA-256, contents check |
| `backend/app/documents/extraction.py` | new | `ExtractionError`, `Section`, `ExtractedText`, `extract_text()` |
| `backend/app/documents/chunking.py` | new | `ChunkDraft`, `split_into_chunks()` |
| `backend/app/documents/embeddings.py` | new | `Embedder` protocol, `VoyageEmbedder` (httpx, batches, retries), `get_embedder()` |
| `backend/app/documents/processing.py` | new | `process_document()`, the background task |
| `backend/app/documents/schemas.py` | new | `DocumentOut` (camelCase JSON) |
| `backend/app/documents/routes.py` | new | `POST/GET /api/documents`, `DELETE /api/documents/{id}`, size-limit middleware |
| `backend/app/startup.py`, `backend/app/main.py` | change | Clear leftover temporary uploads; register the router and middleware |
| `backend/tests/sample_files.py`, `backend/tests/fakes.py` | new | Build test PDFs/DOCX files; `FakeEmbedder` |
| `frontend/src/lib/api.ts`, `frontend/src/lib/apiTypes.ts` | change | FormData uploads; `OwlDocument` type |
| `frontend/src/hooks/useDocuments.ts` | new | List (with polling), upload, delete |
| `frontend/src/components/*`, `frontend/src/pages/DocumentsPage.tsx`, `frontend/src/data/sampleData.ts` | change | Real data; sample documents removed |

## Before Task 1: branch

```bash
git checkout -b feature/uploads
```

---

### Task 1: Settings and libraries

**What you'll learn:** adding libraries with uv, and why a required setting makes the app refuse to start without it.

**Files:**
- Modify: `backend/app/config.py`, `backend/tests/conftest.py`, `backend/tests/test_config.py`, `backend/.env.example`, `backend/README.md`, `backend/pyproject.toml` (via uv)

**Interfaces:**
- Produces: `Settings.voyage_api_key: str`, `Settings.embedding_model: str = "voyage-4"`, `Settings.max_upload_mb: int = 20`, `Settings.max_pdf_pages: int = 500`, `Settings.max_documents_per_user: int = 50`.

- [ ] **Step 1: Add the libraries**

```bash
cd backend
uv add pypdf python-docx
uv add --dev fpdf2
```

- [ ] **Step 2: Write the failing tests**

Add to the end of `backend/tests/test_config.py`:

```python
def test_upload_settings_have_the_spec_defaults():
    settings = Settings(_env_file=None, database_url="postgresql://u:p@h/db")

    assert settings.embedding_model == "voyage-4"
    assert settings.max_upload_mb == 20
    assert settings.max_pdf_pages == 500
    assert settings.max_documents_per_user == 50


def test_missing_voyage_key_is_an_error(monkeypatch):
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="postgresql://u:p@h/db")
```

In `backend/tests/conftest.py`, below the `os.environ["FRONTEND_URL"] = ...` line, add:

```python
# Tests never call Voyage (a fake embedder stands in), but the setting must exist.
os.environ["VOYAGE_API_KEY"] = "test-key-never-sent-to-voyage"
```

- [ ] **Step 3: Run them and watch them fail**

```bash
uv run pytest tests/test_config.py
```

Expected: FAIL (`'Settings' object has no attribute 'embedding_model'`, and the missing key raises nothing).

- [ ] **Step 4: Add the settings**

In `backend/app/config.py`, below the `frontend_url` line, add:

```python
    # Voyage AI turns text into embeddings (lists of numbers) so Owl can search by meaning.
    voyage_api_key: str = Field(min_length=1)
    embedding_model: str = "voyage-4"
    # Upload limits.
    max_upload_mb: int = Field(default=20, gt=0)
    max_pdf_pages: int = Field(default=500, gt=0)
    max_documents_per_user: int = Field(default=50, gt=0)
```

- [ ] **Step 5: Document the new settings**

Add to the end of `backend/.env.example`:

```
# Voyage AI turns document text into embeddings for search. Create a key at https://dashboard.voyageai.com/
# (.env.test can leave this out: the tests never call Voyage.)
VOYAGE_API_KEY=replace-me

# Optional. These are the defaults:
# EMBEDDING_MODEL=voyage-4
# MAX_UPLOAD_MB=20
# MAX_PDF_PAGES=500
# MAX_DOCUMENTS_PER_USER=50
```

In `backend/README.md`, replace step 2 of "First-time setup" with:

```markdown
2. Copy `.env.example` to `.env` (your **owl** Supabase project, plus your Voyage AI key) and to `.env.test` (your separate **owl-test** project).
```

- [ ] **Step 6: Add your Voyage key (owner)**

Create an API key at https://dashboard.voyageai.com/ and add a line `VOYAGE_API_KEY=...` to `backend/.env` yourself. Never paste the key into chat. Without it the backend now refuses to start.

- [ ] **Step 7: Run all tests**

```bash
uv run pytest
```

Expected: `51 passed`.

- [ ] **Step 8: Commit**

```bash
cd ..
git add backend
git commit -m "feat(backend): add Voyage and upload limit settings"
```

---

### Task 2: Upload checks

**What you'll learn:** reading a file in pieces (so a big upload never sits in memory at once), SHA-256 hashing, and checking what a file really is.

**Ideas:** `hashlib`, the walrus operator `:=`, `try` / `except` / `raise` to clean up, `zipfile` (a DOCX is a zip of XML files), dataclasses.

**Files:**
- Create: `backend/app/documents/__init__.py` (empty), `backend/app/documents/validation.py`, `backend/tests/test_upload_validation.py`

**Interfaces:**
- Produces (in `app.documents.validation`): `UPLOAD_DIR: Path`, `class UploadRejected(Exception)`, `too_large_message(max_mb: int) -> str`, `clean_filename(raw: str | None) -> str`, `file_type_from_name(filename: str) -> str` (one of `"pdf" | "docx" | "txt" | "md"`), `@dataclass SavedUpload(path: Path, content_hash: str, size: int)`, `save_upload(source: BinaryIO, max_mb: int) -> SavedUpload`, `check_contents(path: Path, file_type: str) -> None`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_upload_validation.py`:

```python
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
```

- [ ] **Step 2: Run them and watch them fail**

```bash
cd backend
uv run pytest tests/test_upload_validation.py
```

Expected: FAIL with `No module named 'app.documents'`.

- [ ] **Step 3: Write the checks**

Create the empty file `backend/app/documents/__init__.py`, then `backend/app/documents/validation.py`:

```python
"""Checks an upload before Owl accepts it: name, size, type and contents."""

import hashlib
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import BinaryIO

# Uploads wait here until the background task has read them.
UPLOAD_DIR = Path(tempfile.gettempdir()) / "owl-uploads"
ALLOWED_TYPES = ("pdf", "docx", "txt", "md")
READ_BLOCK_BYTES = 1024 * 1024
# A small DOCX can unpack into gigabytes (a "zip bomb"), so the unpacked size is capped too.
MAX_DOCX_UNPACKED_BYTES = 200 * 1024 * 1024


class UploadRejected(Exception):
    """The file can't be accepted. The message is shown to the user."""


@dataclass(frozen=True)
class SavedUpload:
    path: Path
    content_hash: str
    size: int


def too_large_message(max_mb: int) -> str:
    return f"Files can be at most {max_mb} MB."


def clean_filename(raw: str | None) -> str:
    # Some browsers send a full path such as C:\fakepath\Report.pdf. Keep only the last part.
    name = PurePath((raw or "").replace("\\", "/")).name.strip()
    return name[:255] or "untitled"


def file_type_from_name(filename: str) -> str:
    extension = PurePath(filename).suffix.lower().removeprefix(".")
    if extension not in ALLOWED_TYPES:
        raise UploadRejected("Owl accepts PDF, DOCX, TXT and MD files.")
    return extension


def save_upload(source: BinaryIO, max_mb: int) -> SavedUpload:
    """Copy the upload to a temporary file, hashing it on the way. Stops as soon as it's too big."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_DIR / f"{uuid.uuid4()}.upload"
    max_bytes = max_mb * 1024 * 1024
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("wb") as target:
            while block := source.read(READ_BLOCK_BYTES):
                size += len(block)
                if size > max_bytes:
                    raise UploadRejected(too_large_message(max_mb))
                digest.update(block)
                target.write(block)
        if size == 0:
            raise UploadRejected("This file is empty.")
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return SavedUpload(path=path, content_hash=digest.hexdigest(), size=size)


def check_contents(path: Path, file_type: str) -> None:
    """Make sure the contents match the name: a renamed program is not a PDF."""
    if file_type == "pdf":
        with path.open("rb") as file:
            if b"%PDF-" not in file.read(1024):
                raise UploadRejected("This file isn't a valid PDF.")
    elif file_type == "docx":
        _check_docx(path)
    else:
        try:
            path.read_bytes().decode("utf-8")
        except UnicodeDecodeError:
            raise UploadRejected("Text files must be saved as UTF-8.") from None


def _check_docx(path: Path) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            unpacked = sum(info.file_size for info in archive.infolist())
    except zipfile.BadZipFile:
        raise UploadRejected("This file isn't a valid DOCX.") from None
    if "word/document.xml" not in names:
        raise UploadRejected("This file isn't a valid DOCX.")
    if unpacked > MAX_DOCX_UNPACKED_BYTES:
        raise UploadRejected("This DOCX is too large once unpacked.")
```

- [ ] **Step 4: Run all tests**

```bash
uv run pytest
```

Expected: `59 passed`.

- [ ] **Step 5: Commit**

```bash
cd ..
git add backend
git commit -m "feat(backend): add upload checks for name, size, type and contents"
```

---

### Task 3: Text extraction

**What you'll learn:** how text comes out of PDFs (page by page) and Word files (paragraphs, headings, tables), and why each piece remembers where it came from (for citations later).

**Ideas:** `pypdf.PdfReader`, `python-docx`, regular expressions (`re`) for Markdown headings, test helper modules.

**Files:**
- Create: `backend/app/documents/extraction.py`, `backend/tests/sample_files.py`, `backend/tests/test_extraction.py`

**Interfaces:**
- Produces (in `app.documents.extraction`): `class ExtractionError(Exception)`, `@dataclass Section(text: str, page_number: int | None = None, heading: str | None = None)`, `@dataclass ExtractedText(sections: list[Section], page_count: int | None)`, `extract_text(path: Path, file_type: str, max_pdf_pages: int) -> ExtractedText`.
- Produces (in `tests.sample_files`): `make_pdf(pages: list[str]) -> bytes`, `make_docx(blocks: list[tuple[str, object]]) -> bytes`.

- [ ] **Step 1: Write the test helpers**

Create `backend/tests/sample_files.py`:

```python
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
```

- [ ] **Step 2: Write the failing tests**

Create `backend/tests/test_extraction.py`:

```python
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
    path = write(tmp_path, "\ufeffHello\x00 world".encode("utf-8"))

    extracted = extract_text(path, "txt", max_pdf_pages=500)

    assert extracted.sections == [Section("Hello world")]


def test_file_with_only_whitespace_has_no_text(tmp_path):
    path = write(tmp_path, b"  \n\n  ")

    with pytest.raises(ExtractionError, match="No text found"):
        extract_text(path, "txt", max_pdf_pages=500)
```

- [ ] **Step 3: Run them and watch them fail**

```bash
cd backend
uv run pytest tests/test_extraction.py
```

Expected: FAIL with `No module named 'app.documents.extraction'`.

- [ ] **Step 4: Write the extraction**

Create `backend/app/documents/extraction.py`:

```python
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
```

- [ ] **Step 5: Run all tests**

```bash
uv run pytest
```

Expected: `66 passed`.

- [ ] **Step 6: Commit**

```bash
cd ..
git add backend
git commit -m "feat(backend): extract text sections from PDF, DOCX, TXT and MD"
```

---

### Task 4: Chunking

**What you'll learn:** why answers search through ~500-word passages instead of whole files, and why neighbouring passages overlap.

**Files:**
- Create: `backend/app/documents/chunking.py`, `backend/tests/test_chunking.py`

**Interfaces:**
- Consumes: `Section` (Task 3).
- Produces (in `app.documents.chunking`): `CHUNK_WORDS = 500`, `OVERLAP_WORDS = 50`, `@dataclass ChunkDraft(text: str, position: int, page_number: int | None, heading: str | None)`, `split_into_chunks(sections: list[Section], chunk_words: int = CHUNK_WORDS, overlap_words: int = OVERLAP_WORDS) -> list[ChunkDraft]`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_chunking.py`:

```python
from app.documents.chunking import split_into_chunks
from app.documents.extraction import Section


def numbered_words(count: int) -> str:
    return " ".join(f"w{number}" for number in range(count))


def test_a_short_section_is_one_chunk_with_its_labels():
    chunks = split_into_chunks([Section("Refunds  take\n30 days.", page_number=4, heading=None)])

    assert len(chunks) == 1
    assert chunks[0].text == "Refunds take 30 days."
    assert chunks[0].page_number == 4
    assert chunks[0].position == 0


def test_a_long_section_is_split_with_overlap():
    chunks = split_into_chunks([Section(numbered_words(1200), heading="Refunds")])

    words = [chunk.text.split() for chunk in chunks]
    assert [len(chunk) for chunk in words] == [500, 500, 300]
    assert words[0][-50:] == words[1][:50]
    assert words[2][-1] == "w1199"
    assert all(chunk.heading == "Refunds" for chunk in chunks)


def test_exactly_one_chunk_of_words_makes_one_chunk():
    assert len(split_into_chunks([Section(numbered_words(500))])) == 1


def test_positions_continue_across_sections():
    chunks = split_into_chunks([Section("Page one.", page_number=1), Section("Page two.", page_number=2)])

    assert [(chunk.position, chunk.page_number) for chunk in chunks] == [(0, 1), (1, 2)]
```

- [ ] **Step 2: Run them and watch them fail**

```bash
cd backend
uv run pytest tests/test_chunking.py
```

Expected: FAIL with `No module named 'app.documents.chunking'`.

- [ ] **Step 3: Write the chunking**

Create `backend/app/documents/chunking.py`:

```python
"""Splits sections into overlapping ~500-word chunks: big enough to make sense, small enough to search."""

from dataclasses import dataclass

from app.documents.extraction import Section

CHUNK_WORDS = 500
# Each chunk repeats the last 50 words of the one before, so a sentence cut in two is still whole somewhere.
OVERLAP_WORDS = 50


@dataclass(frozen=True)
class ChunkDraft:
    text: str
    position: int
    page_number: int | None
    heading: str | None


def split_into_chunks(
    sections: list[Section], chunk_words: int = CHUNK_WORDS, overlap_words: int = OVERLAP_WORDS
) -> list[ChunkDraft]:
    step = chunk_words - overlap_words
    chunks: list[ChunkDraft] = []
    for section in sections:
        words = section.text.split()
        start = 0
        while True:
            window = words[start : start + chunk_words]
            chunks.append(ChunkDraft(" ".join(window), len(chunks), section.page_number, section.heading))
            if start + chunk_words >= len(words):
                break
            start += step
    return chunks
```

- [ ] **Step 4: Run all tests**

```bash
uv run pytest
```

Expected: `70 passed`.

- [ ] **Step 5: Commit**

```bash
cd ..
git add backend
git commit -m "feat(backend): split text into overlapping chunks"
```

---

### Task 5: Embeddings with Voyage

**What you'll learn:** calling a web API with httpx, sending work in batches, retrying only the errors worth retrying, and testing without the internet.

**Ideas:** `typing.Protocol` (any object with the right methods fits), `httpx.MockTransport` (a pretend server), injecting `sleep` so tests don't wait, `functools.lru_cache`.

**Voyage facts used here** (from docs.voyageai.com, checked 2026-11-19): `POST https://api.voyageai.com/v1/embeddings` with `Authorization: Bearer <key>`; body `{"input": [...], "model": "voyage-4", "input_type": "document" | "query", "output_dimension": 1024}`; reply `{"data": [{"embedding": [...], "index": 0}, ...]}`; at most 1,000 texts and 320K tokens per request for voyage-4; retry 429, 500, 502, 503, 504; don't retry 400, 401, 403.

**Files:**
- Create: `backend/app/documents/embeddings.py`, `backend/tests/fakes.py`, `backend/tests/test_embeddings.py`

**Interfaces:**
- Produces (in `app.documents.embeddings`): `BATCH_SIZE = 128`, `class EmbeddingError(Exception)`, `class Embedder(Protocol)` with `model: str` and `embed(texts: list[str], input_type: Literal["document", "query"]) -> list[list[float]]`, `class VoyageEmbedder(api_key, model, transport=None, sleep=time.sleep)`, `get_embedder() -> Embedder` (a FastAPI dependency).
- Produces (in `tests.fakes`): `FakeEmbedder` with `.model = "fake-embedder"`, `.calls: list[tuple[list[str], str]]`, `.fail: bool`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_embeddings.py`:

```python
import json

import httpx
import pytest

from app.documents.embeddings import BATCH_SIZE, EmbeddingError, VoyageEmbedder


def voyage_reply(request: httpx.Request) -> httpx.Response:
    """Answers like Voyage: one embedding per input, here [len(text)] * 3, deliberately out of order."""
    body = json.loads(request.content)
    data = [{"object": "embedding", "embedding": [float(len(text))] * 3, "index": i} for i, text in enumerate(body["input"])]
    return httpx.Response(200, json={"object": "list", "data": data[::-1], "model": body["model"], "usage": {"total_tokens": 1}})


def make_embedder(handler, sleeps: list[float]) -> VoyageEmbedder:
    return VoyageEmbedder("test-key", "voyage-4", transport=httpx.MockTransport(handler), sleep=sleeps.append)


def test_sends_the_right_request_and_keeps_input_order():
    requests: list[httpx.Request] = []

    def handler(request):
        requests.append(request)
        return voyage_reply(request)

    result = make_embedder(handler, []).embed(["ab", "hello"], input_type="document")

    assert result == [[2.0] * 3, [5.0] * 3]
    assert requests[0].headers["Authorization"] == "Bearer test-key"
    body = json.loads(requests[0].content)
    assert body == {"input": ["ab", "hello"], "model": "voyage-4", "input_type": "document", "output_dimension": 1024}


def test_many_texts_are_sent_in_batches():
    calls = []

    def handler(request):
        calls.append(request)
        return voyage_reply(request)

    result = make_embedder(handler, []).embed(["x"] * (BATCH_SIZE + 1), input_type="document")

    assert len(calls) == 2
    assert len(result) == BATCH_SIZE + 1


def test_rate_limit_is_retried_after_a_wait():
    answers = iter([httpx.Response(429, json={"detail": "slow down"})])
    sleeps: list[float] = []

    def handler(request):
        answer = next(answers, None)
        return answer if answer is not None else voyage_reply(request)

    result = make_embedder(handler, sleeps).embed(["hi"], input_type="query")

    assert result == [[2.0] * 3]
    assert sleeps == [1]


def test_bad_key_is_not_retried():
    calls = []
    sleeps: list[float] = []

    def handler(request):
        calls.append(request)
        return httpx.Response(401, json={"detail": "bad key"})

    with pytest.raises(EmbeddingError, match="401"):
        make_embedder(handler, sleeps).embed(["hi"], input_type="query")
    assert len(calls) == 1
    assert sleeps == []


def test_gives_up_after_repeated_server_errors():
    calls = []
    sleeps: list[float] = []

    def handler(request):
        calls.append(request)
        return httpx.Response(503)

    with pytest.raises(EmbeddingError, match="503"):
        make_embedder(handler, sleeps).embed(["hi"], input_type="query")
    assert len(calls) == 4
    assert sleeps == [1, 4, 10]
```

- [ ] **Step 2: Run them and watch them fail**

```bash
cd backend
uv run pytest tests/test_embeddings.py
```

Expected: FAIL with `No module named 'app.documents.embeddings'`.

- [ ] **Step 3: Write the embedder**

Create `backend/app/documents/embeddings.py`:

```python
"""Turns text into embeddings (lists of 1,024 numbers) with Voyage AI. Similar meaning, similar numbers."""

import time
from collections.abc import Callable
from functools import lru_cache
from typing import Literal, Protocol

import httpx

from app.config import get_settings
from app.models import EMBEDDING_DIMENSIONS

VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
# 128 chunks of ~500 words is roughly 90K tokens, well under Voyage's 320K-token limit per request.
BATCH_SIZE = 128
RETRY_STATUSES = {429, 500, 502, 503, 504}
RETRY_WAITS = (1, 4, 10)  # seconds to wait before the 2nd, 3rd and 4th try

InputType = Literal["document", "query"]


class EmbeddingError(Exception):
    """Voyage couldn't embed the text, even after retrying. Details are for the server log only."""


class Embedder(Protocol):
    """Anything with a model name and an embed method. Voyage in the app, a fake in tests."""

    model: str

    def embed(self, texts: list[str], input_type: InputType) -> list[list[float]]: ...


class VoyageEmbedder:
    def __init__(
        self,
        api_key: str,
        model: str,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.model = model
        self._client = httpx.Client(headers={"Authorization": f"Bearer {api_key}"}, timeout=60, transport=transport)
        self._sleep = sleep

    def embed(self, texts: list[str], input_type: InputType) -> list[list[float]]:
        embeddings: list[list[float]] = []
        for start in range(0, len(texts), BATCH_SIZE):
            embeddings.extend(self._embed_batch(texts[start : start + BATCH_SIZE], input_type))
        return embeddings

    def _embed_batch(self, texts: list[str], input_type: InputType) -> list[list[float]]:
        body = {"input": texts, "model": self.model, "input_type": input_type, "output_dimension": EMBEDDING_DIMENSIONS}
        problem = ""
        for wait in (*RETRY_WAITS, None):
            try:
                response = self._client.post(VOYAGE_URL, json=body)
            except httpx.TransportError as error:
                problem = f"network error: {error}"
            else:
                if response.status_code == 200:
                    items = sorted(response.json()["data"], key=lambda item: item["index"])
                    return [item["embedding"] for item in items]
                problem = f"HTTP {response.status_code}"
                if response.status_code not in RETRY_STATUSES:
                    break
            if wait is not None:
                self._sleep(wait)
        raise EmbeddingError(f"Voyage embedding failed: {problem}")


@lru_cache
def get_embedder() -> Embedder:
    """One shared embedder (and connection pool) for the whole app. Tests replace it with a fake."""
    settings = get_settings()
    return VoyageEmbedder(settings.voyage_api_key, settings.embedding_model)
```

- [ ] **Step 4: Write the fake for later tests**

Create `backend/tests/fakes.py`:

```python
"""Stand-ins for paid services, so tests need no network and cost nothing."""

from app.documents.embeddings import EmbeddingError
from app.models import EMBEDDING_DIMENSIONS


class FakeEmbedder:
    model = "fake-embedder"

    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str]] = []
        self.fail = False

    def embed(self, texts: list[str], input_type: str) -> list[list[float]]:
        self.calls.append((list(texts), input_type))
        if self.fail:
            raise EmbeddingError("Voyage embedding failed: HTTP 503")
        return [[0.0] * (EMBEDDING_DIMENSIONS - 1) + [1.0] for _ in texts]
```

- [ ] **Step 5: Run all tests**

```bash
uv run pytest
```

Expected: `75 passed`.

- [ ] **Step 6: Commit**

```bash
cd ..
git add backend
git commit -m "feat(backend): add Voyage embedder with batching and retries"
```

---

### Task 6: Background processing

**What you'll learn:** the background half of an upload: one function that runs after the response, keeps database transactions short, and always cleans up.

**Ideas:** `try` / `finally`, `try` / `except` / `else`, row locks (`with_for_update`), logging.

**Files:**
- Create: `backend/app/documents/processing.py`, `backend/tests/test_processing.py`

**Interfaces:**
- Consumes: `extract_text`, `ExtractionError` (Task 3); `split_into_chunks` (Task 4); `Embedder`, `EmbeddingError` (Task 5); `SessionLocal`; `Document`, `Chunk`.
- Produces (in `app.documents.processing`): `EMBEDDING_FAILED: str`, `UNEXPECTED_FAILURE: str`, `process_document(document_id: uuid.UUID, path: Path, embedder: Embedder) -> None`.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_processing.py`:

```python
import uuid

from sqlalchemy import delete, select

from app.database import SessionLocal
from app.documents.processing import EMBEDDING_FAILED, process_document
from app.models import Chunk, Document, User
from tests.fakes import FakeEmbedder
from tests.sample_files import make_pdf


def make_document(db, tmp_path, file_type: str, content: bytes):
    user = User(email="reader@example.com", password_hash="not-a-real-hash")
    db.add(user)
    db.commit()
    document = Document(
        user_id=user.id, filename=f"file.{file_type}", file_type=file_type, content_hash="a" * 64, status="processing"
    )
    db.add(document)
    db.commit()
    path = tmp_path / "upload"
    path.write_bytes(content)
    return document, path


def chunks_of(db, document_id):
    return db.scalars(select(Chunk).where(Chunk.document_id == document_id).order_by(Chunk.position)).all()


def test_pdf_becomes_ready_with_one_chunk_per_page(db, tmp_path):
    document, path = make_document(db, tmp_path, "pdf", make_pdf(["Refunds take 30 days.", "Annual plans are pro rata."]))
    embedder = FakeEmbedder()

    process_document(document.id, path, embedder)

    db.refresh(document)
    chunks = chunks_of(db, document.id)
    assert document.status == "ready"
    assert document.page_count == 2
    assert [(chunk.position, chunk.page_number) for chunk in chunks] == [(0, 1), (1, 2)]
    assert all(chunk.user_id == document.user_id for chunk in chunks)
    assert all(chunk.embedding_model == "fake-embedder" for chunk in chunks)
    assert embedder.calls[0][1] == "document"
    assert not path.exists()


def test_markdown_chunks_keep_their_headings(db, tmp_path):
    document, path = make_document(db, tmp_path, "md", b"# Refunds\nWithin 30 days.\n# Annual\nPro rata.")

    process_document(document.id, path, FakeEmbedder())

    assert [chunk.heading for chunk in chunks_of(db, document.id)] == ["Refunds", "Annual"]


def test_scanned_pdf_fails_with_a_reason(db, tmp_path):
    document, path = make_document(db, tmp_path, "pdf", make_pdf([""]))

    process_document(document.id, path, FakeEmbedder())

    db.refresh(document)
    assert document.status == "failed"
    assert document.failure_reason == "No text found, scanned PDFs aren't supported yet."
    assert chunks_of(db, document.id) == []
    assert not path.exists()


def test_voyage_trouble_fails_with_a_friendly_reason(db, tmp_path):
    document, path = make_document(db, tmp_path, "txt", b"Some notes.")
    embedder = FakeEmbedder()
    embedder.fail = True

    process_document(document.id, path, embedder)

    db.refresh(document)
    assert document.status == "failed"
    assert document.failure_reason == EMBEDDING_FAILED
    assert chunks_of(db, document.id) == []


def test_document_deleted_during_processing_is_left_alone(db, tmp_path):
    document, path = make_document(db, tmp_path, "txt", b"Some notes.")

    class DeleteWhileEmbedding(FakeEmbedder):
        def embed(self, texts, input_type):
            with SessionLocal() as session:
                session.execute(delete(Document).where(Document.id == document.id))
                session.commit()
            return super().embed(texts, input_type)

    process_document(document.id, path, DeleteWhileEmbedding())  # no error

    # A fresh query, not db.get: db.get would return the copy this session already holds in memory.
    assert db.scalar(select(Document).where(Document.id == document.id)) is None
    assert chunks_of(db, document.id) == []
    assert not path.exists()


def test_document_deleted_before_processing_skips_all_work(tmp_path):
    path = tmp_path / "upload"
    path.write_bytes(b"Some notes.")
    embedder = FakeEmbedder()

    process_document(uuid.uuid4(), path, embedder)

    assert embedder.calls == []
    assert not path.exists()
```

- [ ] **Step 2: Run them and watch them fail**

```bash
cd backend
uv run pytest tests/test_processing.py
```

Expected: FAIL with `No module named 'app.documents.processing'`.

- [ ] **Step 3: Write the background task**

Create `backend/app/documents/processing.py`:

```python
"""The background half of an upload: read the file, split it, embed it, save the chunks."""

import logging
import uuid
from pathlib import Path

from app.config import get_settings
from app.database import SessionLocal
from app.documents.chunking import split_into_chunks
from app.documents.embeddings import Embedder, EmbeddingError
from app.documents.extraction import ExtractionError, extract_text
from app.models import Chunk, Document

logger = logging.getLogger("owl.documents")

EMBEDDING_FAILED = "Owl couldn't process this file right now. Please upload it again later."
UNEXPECTED_FAILURE = "Something went wrong while processing this file. Please upload it again."


def process_document(document_id: uuid.UUID, path: Path, embedder: Embedder) -> None:
    """Runs after the upload response is sent. Always deletes the temporary file."""
    try:
        _process(document_id, path, embedder)
    finally:
        path.unlink(missing_ok=True)


def _process(document_id: uuid.UUID, path: Path, embedder: Embedder) -> None:
    # 1. A quick read, then the database connection goes back to the pool during the slow work.
    with SessionLocal() as session:
        document = session.get(Document, document_id)
        if document is None:
            return  # deleted before we started
        file_type, user_id = document.file_type, document.user_id

    # 2. The slow part, outside any database transaction.
    failure_reason: str | None = None
    try:
        extracted = extract_text(path, file_type, get_settings().max_pdf_pages)
        drafts = split_into_chunks(extracted.sections)
        embeddings = embedder.embed([draft.text for draft in drafts], input_type="document")
        if len(embeddings) != len(drafts):
            raise EmbeddingError(f"expected {len(drafts)} embeddings, got {len(embeddings)}")
    except ExtractionError as error:
        failure_reason = str(error)
    except EmbeddingError:
        logger.exception("Embedding failed for document %s", document_id)
        failure_reason = EMBEDDING_FAILED
    except Exception:
        logger.exception("Processing failed for document %s", document_id)
        failure_reason = UNEXPECTED_FAILURE

    # 3. Save. The row lock means a delete waits until we finish (or we see that it already happened).
    with SessionLocal() as session:
        document = session.get(Document, document_id, with_for_update=True)
        if document is None:
            return  # deleted while we were working: stop quietly
        if failure_reason is None:
            session.add_all(
                Chunk(
                    user_id=user_id,
                    document_id=document_id,
                    text=draft.text,
                    page_number=draft.page_number,
                    heading=draft.heading,
                    position=draft.position,
                    embedding=embedding,
                    embedding_model=embedder.model,
                )
                for draft, embedding in zip(drafts, embeddings)
            )
            document.page_count = extracted.page_count
            document.status = "ready"
        else:
            document.status = "failed"
            document.failure_reason = failure_reason
        session.commit()
```

- [ ] **Step 4: Run all tests**

```bash
uv run pytest
```

Expected: `81 passed`.

- [ ] **Step 5: Commit**

```bash
cd ..
git add backend
git commit -m "feat(backend): process uploads in the background into embedded chunks"
```

---

### Task 7: Document routes

**What you'll learn:** receiving a file upload in FastAPI, starting background work, the duplicate and limit rules, and proving one user can never touch another's files.

**Ideas:** `UploadFile` (multipart form uploads), `BackgroundTasks`, HTTP 201 / 204 / 400 / 404 / 409 / 413, `app.dependency_overrides`, pydantic aliases (`file_type` in Python, `fileType` in JSON), middleware.

**Files:**
- Create: `backend/app/documents/schemas.py`, `backend/app/documents/routes.py`, `backend/tests/test_document_routes.py`
- Modify: `backend/app/startup.py`, `backend/app/main.py`, `backend/tests/conftest.py`, `backend/tests/test_startup.py`

**Interfaces:**
- Consumes: everything from Tasks 2–6; `CurrentUser`, `DbSession` (`app.auth.dependencies`).
- Produces: `POST /api/documents` (multipart field `file`) → 201 `DocumentOut`; `GET /api/documents` → `list[DocumentOut]`, newest first; `DELETE /api/documents/{id}` → 204 or 404. `DocumentOut` JSON keys: `id, filename, fileType, status, failureReason, pageCount, createdAt`. `clear_upload_folder(folder: Path = UPLOAD_DIR) -> int` (in `app.startup`). Test fixture `fake_embedder`.

- [ ] **Step 1: Add the test fixture**

Add to the end of `backend/tests/conftest.py`:

```python
@pytest.fixture
def fake_embedder():
    """Routes get a FakeEmbedder instead of Voyage for the length of one test."""
    from app.documents.embeddings import get_embedder
    from app.main import app
    from tests.fakes import FakeEmbedder

    embedder = FakeEmbedder()
    app.dependency_overrides[get_embedder] = lambda: embedder
    yield embedder
    app.dependency_overrides.pop(get_embedder, None)
```

- [ ] **Step 2: Write the failing tests**

Add to the end of `backend/tests/test_startup.py` (and add `clear_upload_folder` to its `from app.startup import ...` line):

```python
def test_leftover_temporary_uploads_are_removed(tmp_path):
    (tmp_path / "old.upload").write_bytes(b"left from a crash")

    assert clear_upload_folder(tmp_path) == 1
    assert list(tmp_path.iterdir()) == []
```

Create `backend/tests/test_document_routes.py`:

```python
import hashlib
import uuid

from sqlalchemy import func, select

from app.config import get_settings
from app.models import Chunk, Document, User
from tests.sample_files import make_pdf

NOTES = b"# Refunds\nWithin 30 days."


def sign_up(client, email="reader@example.com"):
    client.post("/api/auth/signup", json={"email": email, "password": "correct horse battery"})


def upload(client, filename, content):
    return client.post("/api/documents", files={"file": (filename, content)})


def test_upload_is_processed_and_listed(client, fake_embedder):
    sign_up(client)

    response = upload(client, "notes.md", NOTES)

    assert response.status_code == 201
    assert response.json()["status"] == "processing"
    listed = client.get("/api/documents").json()
    assert set(listed[0]) == {"id", "filename", "fileType", "status", "failureReason", "pageCount", "createdAt"}
    assert listed[0]["filename"] == "notes.md"
    assert listed[0]["fileType"] == "md"
    assert listed[0]["status"] == "ready"
    assert listed[0]["failureReason"] is None


def test_pdf_upload_records_its_page_count(client, fake_embedder):
    sign_up(client)

    upload(client, "report.pdf", make_pdf(["Page one.", "Page two."]))

    assert client.get("/api/documents").json()[0]["pageCount"] == 2


def test_upload_needs_a_login(client, fake_embedder):
    assert upload(client, "notes.md", NOTES).status_code == 401


def test_unsupported_type_is_rejected(client, fake_embedder):
    sign_up(client)

    response = upload(client, "setup.exe", b"MZ program")

    assert response.status_code == 400
    assert response.json() == {"detail": "Owl accepts PDF, DOCX, TXT and MD files."}


def test_fake_pdf_is_rejected_and_not_listed(client, fake_embedder):
    sign_up(client)

    response = upload(client, "report.pdf", b"not really a pdf")

    assert response.json() == {"detail": "This file isn't a valid PDF."}
    assert client.get("/api/documents").json() == []


def test_file_over_the_size_limit_is_rejected(client, fake_embedder, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_mb", 1)
    sign_up(client)

    response = upload(client, "big.txt", b"x" * (1024 * 1024 + 1))

    assert response.status_code == 400
    assert response.json() == {"detail": "Files can be at most 1 MB."}


def test_huge_upload_is_stopped_before_it_is_read(client, fake_embedder, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_mb", 1)
    sign_up(client)

    response = upload(client, "huge.txt", b"x" * (2 * 1024 * 1024))

    assert response.status_code == 413
    assert response.json() == {"detail": "Files can be at most 1 MB."}


def test_same_file_twice_is_refused(client, fake_embedder):
    sign_up(client)
    upload(client, "notes.md", NOTES)

    response = upload(client, "copy-of-notes.md", NOTES)

    assert response.status_code == 409
    assert response.json() == {"detail": "You already uploaded this file as 'notes.md'."}


def test_same_file_while_still_processing_is_refused(client, fake_embedder, db):
    sign_up(client)
    user = db.scalar(select(User))
    db.add(
        Document(
            user_id=user.id,
            filename="notes.md",
            file_type="md",
            content_hash=hashlib.sha256(NOTES).hexdigest(),
            status="processing",
        )
    )
    db.commit()

    response = upload(client, "notes.md", NOTES)

    assert response.status_code == 409
    assert response.json() == {"detail": "This file is still being processed."}


def test_failed_copy_is_replaced_by_a_new_upload(client, fake_embedder):
    sign_up(client)
    fake_embedder.fail = True
    upload(client, "notes.md", NOTES)
    assert client.get("/api/documents").json()[0]["status"] == "failed"
    fake_embedder.fail = False

    response = upload(client, "notes.md", NOTES)

    assert response.status_code == 201
    assert [document["status"] for document in client.get("/api/documents").json()] == ["ready"]


def test_document_limit_per_user(client, fake_embedder, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_documents_per_user", 2)
    sign_up(client)
    upload(client, "a.md", b"first")
    upload(client, "b.md", b"second")

    response = upload(client, "c.md", b"third")

    assert response.status_code == 409
    assert response.json() == {"detail": "You've reached the limit of 2 documents. Delete one to upload more."}


def test_users_never_see_or_delete_each_others_documents(client, fake_embedder, db):
    sign_up(client, "a@example.com")
    document_id = upload(client, "a.md", NOTES).json()["id"]
    client.cookies.clear()
    sign_up(client, "b@example.com")

    assert client.get("/api/documents").json() == []
    assert client.delete(f"/api/documents/{document_id}").status_code == 404
    assert db.get(Document, uuid.UUID(document_id)) is not None


def test_two_users_may_upload_the_same_file(client, fake_embedder):
    sign_up(client, "a@example.com")
    upload(client, "notes.md", NOTES)
    client.cookies.clear()
    sign_up(client, "b@example.com")

    assert upload(client, "notes.md", NOTES).status_code == 201


def test_delete_removes_the_document_and_its_chunks(client, fake_embedder, db):
    sign_up(client)
    document_id = upload(client, "notes.md", NOTES).json()["id"]
    assert db.scalar(select(func.count()).select_from(Chunk)) > 0

    assert client.delete(f"/api/documents/{document_id}").status_code == 204

    assert client.get("/api/documents").json() == []
    assert db.scalar(select(func.count()).select_from(Chunk)) == 0
```

- [ ] **Step 3: Run them and watch them fail**

```bash
cd backend
uv run pytest tests/test_document_routes.py tests/test_startup.py
```

Expected: FAIL (`cannot import name 'clear_upload_folder'`; the routes answer 404).

- [ ] **Step 4: Write the response shape**

Create `backend/app/documents/schemas.py`:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class DocumentOut(BaseModel):
    """What the Documents page sees. Python names (file_type) leave as camelCase JSON (fileType)."""

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, validate_by_name=True, serialize_by_alias=True)

    id: uuid.UUID
    filename: str
    file_type: str
    status: str
    failure_reason: str | None
    page_count: int | None
    created_at: datetime
```

- [ ] **Step 5: Write the routes**

Create `backend/app/documents/routes.py`:

```python
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, DbSession
from app.config import get_settings
from app.documents.embeddings import Embedder, get_embedder
from app.documents.processing import process_document
from app.documents.schemas import DocumentOut
from app.documents.validation import (
    UploadRejected,
    check_contents,
    clean_filename,
    file_type_from_name,
    save_upload,
    too_large_message,
)
from app.models import Document

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Room for the form's own bytes around the file (boundaries, field names).
MULTIPART_OVERHEAD_BYTES = 64 * 1024


async def reject_oversized_uploads(request: Request, call_next):
    """Refuses a huge upload from its declared size, before FastAPI copies it to disk."""
    if request.method == "POST" and request.url.path == "/api/documents":
        max_mb = get_settings().max_upload_mb
        declared = request.headers.get("content-length", "")
        if declared.isdigit() and int(declared) > max_mb * 1024 * 1024 + MULTIPART_OVERHEAD_BYTES:
            return JSONResponse({"detail": too_large_message(max_mb)}, status_code=status.HTTP_413_CONTENT_TOO_LARGE)
    return await call_next(request)


@router.get("")
def list_documents(user: CurrentUser, db: DbSession) -> list[DocumentOut]:
    documents = db.scalars(
        select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())
    )
    return [DocumentOut.model_validate(document) for document in documents]


@router.post("", status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile,
    user: CurrentUser,
    db: DbSession,
    background: BackgroundTasks,
    embedder: Annotated[Embedder, Depends(get_embedder)],
) -> DocumentOut:
    settings = get_settings()
    filename = clean_filename(file.filename)
    try:
        file_type = file_type_from_name(filename)
        saved = save_upload(file.file, settings.max_upload_mb)
    except UploadRejected as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error))

    try:
        check_contents(saved.path, file_type)
        document = create_document_row(
            db, user.id, filename, file_type, saved.content_hash, settings.max_documents_per_user
        )
    except UploadRejected as error:
        saved.path.unlink(missing_ok=True)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error))
    except Exception:
        saved.path.unlink(missing_ok=True)
        raise

    # Runs after the response is sent; the browser polls the list to see it finish.
    background.add_task(process_document, document.id, saved.path, embedder)
    return DocumentOut.model_validate(document)


def create_document_row(
    db: Session, user_id: uuid.UUID, filename: str, file_type: str, content_hash: str, max_documents: int
) -> Document:
    """Applies the duplicate and limit rules, then saves the new row, all in one transaction."""
    existing = db.scalar(select(Document).where(Document.user_id == user_id, Document.content_hash == content_hash))
    if existing is not None:
        if existing.status == "ready":
            raise HTTPException(status.HTTP_409_CONFLICT, f"You already uploaded this file as '{existing.filename}'.")
        if existing.status == "processing":
            raise HTTPException(status.HTTP_409_CONFLICT, "This file is still being processed.")
        db.delete(existing)  # a failed copy is replaced by the new upload
        db.flush()  # send the DELETE now, before the INSERT below needs the same hash

    count = db.scalar(select(func.count()).select_from(Document).where(Document.user_id == user_id))
    if count >= max_documents:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"You've reached the limit of {max_documents} documents. Delete one to upload more.",
        )

    document = Document(
        user_id=user_id, filename=filename, file_type=file_type, content_hash=content_hash, status="processing"
    )
    db.add(document)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()  # the same file arrived twice at the same moment
        raise HTTPException(status.HTTP_409_CONFLICT, "This file is still being processed.")
    return document


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: uuid.UUID, user: CurrentUser, db: DbSession) -> None:
    # Filtering by user_id too means another user's document looks exactly like a missing one.
    result = db.execute(delete(Document).where(Document.id == document_id, Document.user_id == user.id))
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found.")
```

- [ ] **Step 6: Clear leftovers at startup**

In `backend/app/startup.py`, add these imports at the top:

```python
import shutil
from pathlib import Path

from app.documents.validation import UPLOAD_DIR
```

and this function at the end:

```python
def clear_upload_folder(folder: Path = UPLOAD_DIR) -> int:
    """Temporary uploads left by a previous run belong to documents just marked failed."""
    if not folder.exists():
        return 0
    leftovers = list(folder.iterdir())
    for path in leftovers:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
    return len(leftovers)
```

- [ ] **Step 7: Register everything in the app**

In `backend/app/main.py`:

Replace the imports

```python
from app.auth.csrf import require_same_origin
from app.auth.routes import router as auth_router
from app.database import SessionLocal, database_is_reachable
from app.startup import check_database, mark_interrupted_documents
```

with

```python
from app.auth.csrf import require_same_origin
from app.auth.routes import router as auth_router
from app.database import SessionLocal, database_is_reachable
from app.documents.routes import reject_oversized_uploads
from app.documents.routes import router as documents_router
from app.startup import check_database, clear_upload_folder, mark_interrupted_documents
```

In `lifespan`, below the `if interrupted:` block, add:

```python
    clear_upload_folder()
```

Replace

```python
app.middleware("http")(require_same_origin)
app.include_router(auth_router)
```

with

```python
app.middleware("http")(reject_oversized_uploads)
app.middleware("http")(require_same_origin)  # added last, so it runs first
app.include_router(auth_router)
app.include_router(documents_router)
```

- [ ] **Step 8: Run all tests**

```bash
uv run pytest
```

Expected: `96 passed`.

- [ ] **Step 9: Commit**

```bash
cd ..
git add backend
git commit -m "feat(backend): add upload, list and delete document routes"
```

---

### Task 8: Connect the Documents page

**What you'll learn:** sending files from the browser (`FormData`), polling while something is processing, and invalidating a query after a change.

**Ideas (React/TypeScript):** `FormData`, `refetchInterval` as a function, `invalidateQueries`, `useIsMutating`, passing callbacks as props.

**Files:**
- Create: `frontend/src/hooks/useDocuments.ts`, `frontend/src/components/StatusBadge.test.tsx`, `frontend/src/components/DeleteDocumentDialog.test.tsx`
- Modify: `frontend/src/lib/api.ts`, `frontend/src/lib/api.test.ts`, `frontend/src/lib/apiTypes.ts`, `frontend/src/components/StatusBadge.tsx`, `frontend/src/components/DeleteDocumentDialog.tsx`, `frontend/src/components/UploadDropzone.tsx`, `frontend/src/pages/DocumentsPage.tsx`, `frontend/src/data/sampleData.ts`

**Interfaces:**
- Consumes: `GET/POST /api/documents`, `DELETE /api/documents/{id}` (Task 7).
- Produces: `apiFetch` accepts `FormData` bodies; `type DocumentStatus`, `type OwlDocument` (in `@/lib/apiTypes`); `DOCUMENTS_KEY`, `useDocuments()`, `useUploadDocument()`, `useUploadsInProgress()`, `useDeleteDocument()` (in `@/hooks/useDocuments`); `DeleteDocumentDialog({ filename, onConfirm })`; `UploadDropzone({ onFiles })`.

- [ ] **Step 1: Write the failing tests**

In `frontend/src/lib/api.test.ts`, give the fake `fetch` typed parameters so tests can read what was sent. Replace

```ts
  const fetchMock = vi.fn(
    async () =>
```

with

```ts
  const fetchMock = vi.fn(
    async (_url: string, _init?: RequestInit) =>
```

and add inside `describe("apiFetch", ...)`, after the last test:

```ts
  it("sends FormData as-is so the browser can set the upload headers", async () => {
    const fetchMock = stubFetch(201, { id: "d1" })
    const form = new FormData()
    form.append("file", new File(["hello"], "notes.md"))

    await apiFetch("/documents", { method: "POST", body: form })

    const init = fetchMock.mock.calls[0][1]
    expect(init?.body).toBe(form)
    expect(init?.headers).toBeUndefined()
  })
```

Create `frontend/src/components/StatusBadge.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react"
import { describe, expect, it } from "vitest"
import { StatusBadge } from "@/components/StatusBadge"

describe("StatusBadge", () => {
  it.each([
    ["processing", "Processing"],
    ["ready", "Ready"],
    ["failed", "Failed"],
  ] as const)("shows %s as %s", (status, label) => {
    render(<StatusBadge status={status} />)

    expect(screen.getByText(label)).toBeInTheDocument()
  })
})
```

Create `frontend/src/components/DeleteDocumentDialog.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"
import { DeleteDocumentDialog } from "@/components/DeleteDocumentDialog"

describe("DeleteDocumentDialog", () => {
  it("does nothing when the user cancels", async () => {
    const onConfirm = vi.fn()
    render(<DeleteDocumentDialog filename="Q3.pdf" onConfirm={onConfirm} />)

    fireEvent.click(screen.getByRole("button", { name: "Delete Q3.pdf" }))
    fireEvent.click(await screen.findByRole("button", { name: "Cancel" }))

    expect(onConfirm).not.toHaveBeenCalled()
  })

  it("deletes after the user confirms", async () => {
    const onConfirm = vi.fn()
    render(<DeleteDocumentDialog filename="Q3.pdf" onConfirm={onConfirm} />)

    fireEvent.click(screen.getByRole("button", { name: "Delete Q3.pdf" }))
    fireEvent.click(await screen.findByRole("button", { name: "Delete" }))

    expect(onConfirm).toHaveBeenCalledOnce()
  })
})
```

- [ ] **Step 2: Run them and watch them fail**

```bash
cd frontend
npm test
```

Expected: FAIL. The FormData test fails (the body is JSON text), and `DeleteDocumentDialog` has no `onConfirm` (nothing is called). `StatusBadge` passes already.

- [ ] **Step 3: Let apiFetch send files**

In `frontend/src/lib/api.ts`, add above `apiFetch`:

```ts
function requestBody(body: unknown): { body?: BodyInit; headers?: HeadersInit } {
  if (body === undefined) return {}
  // For files, the browser writes the multipart Content-Type (with its boundary) itself.
  if (body instanceof FormData) return { body }
  return { body: JSON.stringify(body), headers: { "Content-Type": "application/json" } }
}
```

and replace

```ts
  const hasBody = options.body !== undefined
  const response = await fetch(`/api${path}`, {
    method: options.method ?? "GET",
    credentials: "same-origin",
    headers: hasBody ? { "Content-Type": "application/json" } : undefined,
    body: hasBody ? JSON.stringify(options.body) : undefined,
  })
```

with

```ts
  const response = await fetch(`/api${path}`, {
    method: options.method ?? "GET",
    credentials: "same-origin",
    ...requestBody(options.body),
  })
```

- [ ] **Step 4: Add the document type**

Add to the end of `frontend/src/lib/apiTypes.ts`:

```ts
export type DocumentStatus = "processing" | "ready" | "failed"

// Named OwlDocument so it never gets mixed up with the browser's built-in `Document`.
export type OwlDocument = {
  id: string
  filename: string
  fileType: string
  status: DocumentStatus
  failureReason: string | null
  pageCount: number | null
  createdAt: string
}
```

In `frontend/src/components/StatusBadge.tsx`, replace `import type { DocumentStatus } from "@/data/sampleData"` with:

```ts
import type { DocumentStatus } from "@/lib/apiTypes"
```

- [ ] **Step 5: Write the hooks**

Create `frontend/src/hooks/useDocuments.ts`:

```ts
import { useIsMutating, useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { toast } from "sonner"
import { apiFetch } from "@/lib/api"
import type { OwlDocument } from "@/lib/apiTypes"

export const DOCUMENTS_KEY = ["documents"] as const
const UPLOAD_KEY = ["upload-document"] as const
const POLL_WHILE_PROCESSING_MS = 3000

export function useDocuments() {
  return useQuery({
    queryKey: DOCUMENTS_KEY,
    queryFn: () => apiFetch<OwlDocument[]>("/documents"),
    // Ask again every few seconds while any file is still processing, then stop.
    refetchInterval: (query) =>
      query.state.data?.some((document) => document.status === "processing") ? POLL_WHILE_PROCESSING_MS : false,
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: UPLOAD_KEY,
    mutationFn: (file: File) => {
      const form = new FormData()
      form.append("file", file)
      return apiFetch<OwlDocument>("/documents", { method: "POST", body: form })
    },
    // These run for every file, even when several upload at once.
    onError: (error, file) => toast.error(`${file.name}: ${error.message}`),
    onSettled: () => queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY }),
  })
}

/** How many uploads are still being sent. */
export function useUploadsInProgress() {
  return useIsMutating({ mutationKey: UPLOAD_KEY })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => apiFetch<null>(`/documents/${id}`, { method: "DELETE" }),
    onError: (error) => toast.error(error.message),
    onSettled: () => queryClient.invalidateQueries({ queryKey: DOCUMENTS_KEY }),
  })
}
```

- [ ] **Step 6: Let the components report what the user did**

In `frontend/src/components/DeleteDocumentDialog.tsx`:

Delete the line `import { notConnected } from "@/lib/notConnected"`.

Replace `export function DeleteDocumentDialog({ filename }: { filename: string }) {` with:

```tsx
export function DeleteDocumentDialog({ filename, onConfirm }: { filename: string; onConfirm: () => void }) {
```

Replace `<AlertDialogAction onClick={() => notConnected("Deleting files")}>Delete</AlertDialogAction>` with:

```tsx
          <AlertDialogAction onClick={onConfirm}>Delete</AlertDialogAction>
```

Replace `frontend/src/components/UploadDropzone.tsx` with:

```tsx
import { useRef, useState, type DragEvent } from "react"
import { Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function UploadDropzone({ onFiles }: { onFiles: (files: File[]) => void }) {
  // Only this component needs to know about dragging, so it's local state, not Zustand.
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setIsDragging(false)
    if (event.dataTransfer.files.length) onFiles(Array.from(event.dataTransfer.files))
  }

  return (
    <div
      onDragOver={(event) => {
        event.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={handleDrop}
      className={cn(
        "flex flex-col items-center gap-3 rounded-lg border-2 border-dashed p-8 text-center transition-colors",
        isDragging ? "border-primary bg-primary/5" : "border-border",
      )}
    >
      <Upload className="size-8 text-muted-foreground" />
      <div>
        <p className="font-medium">Drop files here to upload</p>
        <p className="text-sm text-muted-foreground">PDF, DOCX, TXT or MD · up to 20 MB each</p>
      </div>
      <Button variant="outline" onClick={() => fileInputRef.current?.click()}>
        Choose files
      </Button>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.txt,.md"
        multiple
        className="hidden"
        onChange={(event) => {
          if (event.target.files?.length) onFiles(Array.from(event.target.files))
          event.target.value = ""
        }}
      />
    </div>
  )
}
```

- [ ] **Step 7: Show real documents**

Replace `frontend/src/pages/DocumentsPage.tsx` with:

```tsx
import { Download, FileText } from "lucide-react"
import { DeleteDocumentDialog } from "@/components/DeleteDocumentDialog"
import { StatusBadge } from "@/components/StatusBadge"
import { UploadDropzone } from "@/components/UploadDropzone"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useAppConfig } from "@/hooks/useAppConfig"
import { useDeleteDocument, useDocuments, useUploadDocument, useUploadsInProgress } from "@/hooks/useDocuments"
import type { OwlDocument } from "@/lib/apiTypes"
import { formatDate } from "@/lib/format"
import { notConnected } from "@/lib/notConnected"

export function DocumentsPage() {
  const storageEnabled = useAppConfig().data?.storageEnabled ?? false
  const documents = useDocuments()
  const upload = useUploadDocument()
  const uploading = useUploadsInProgress()
  const deleteDocument = useDeleteDocument()

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 p-4 md:p-8">
      <div>
        <h1 className="text-2xl font-semibold">Documents</h1>
        <p className="text-muted-foreground">Owl answers questions using only these files.</p>
      </div>

      <UploadDropzone onFiles={(files) => files.forEach((file) => upload.mutate(file))} />
      {uploading > 0 && (
        <p className="text-sm text-muted-foreground">
          Uploading {uploading} {uploading === 1 ? "file" : "files"}…
        </p>
      )}

      {documents.isPending ? (
        <p className="text-muted-foreground">Loading your documents…</p>
      ) : documents.isError ? (
        <p className="text-destructive">Couldn't load your documents. {documents.error.message}</p>
      ) : documents.data.length === 0 ? (
        <p className="text-muted-foreground">No documents yet. Upload a file to get started.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="hidden sm:table-cell">Pages</TableHead>
              <TableHead className="hidden sm:table-cell">Uploaded</TableHead>
              <TableHead className="text-right">
                <span className="sr-only">Actions</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {documents.data.map((document: OwlDocument) => (
              <TableRow key={document.id}>
                <TableCell className="whitespace-normal">
                  <div className="flex items-start gap-2">
                    <FileText className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
                    <div className="min-w-0">
                      <p className="font-medium break-all">{document.filename}</p>
                      {document.failureReason && <p className="text-sm text-destructive">{document.failureReason}</p>}
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <StatusBadge status={document.status} />
                </TableCell>
                <TableCell className="hidden sm:table-cell">{document.pageCount ?? "—"}</TableCell>
                <TableCell className="hidden sm:table-cell">{formatDate(document.createdAt)}</TableCell>
                <TableCell>
                  <div className="flex justify-end gap-1">
                    {storageEnabled && document.status === "ready" && (
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`Download ${document.filename}`}
                        onClick={() => notConnected("Downloading")}
                      >
                        <Download />
                      </Button>
                    )}
                    <DeleteDocumentDialog
                      filename={document.filename}
                      onConfirm={() => deleteDocument.mutate(document.id)}
                    />
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  )
}
```

- [ ] **Step 8: Remove the sample documents**

In `frontend/src/data/sampleData.ts`, delete the `DocumentStatus` type, the `SampleDocument` type and the whole `sampleDocuments` array. Check nothing still uses them:

```bash
grep -rn "sampleDocuments\|SampleDocument\|DocumentStatus.*sampleData" src
```

Expected: no output.

- [ ] **Step 9: Run tests, build and lint**

```bash
npm test
npm run build
npm run lint
```

Expected: `15 passed`; build succeeds; lint shows no errors (the same 4 warnings in shadcn's generated files are fine).

- [ ] **Step 10: Commit**

```bash
cd ..
git add frontend
git commit -m "feat(frontend): connect uploads, document list and delete"
```

---

### Task 9: Try the whole flow, then merge

**What you'll learn:** how the background work looks from the browser, and how to check what landed in the database.

**Files:** none (fixes only if a check fails).

- [ ] **Step 1: Start both servers** (backend on port 8000, frontend on 5173), log in as `owner-test@example.com`.

- [ ] **Step 2: Walk through it at http://localhost:5173/documents**

These steps call Voyage with your key (a few cents at most) and store chunks in your **owl** database.

- [ ] The page says "No documents yet."
- [ ] Upload a small `.md` file with two `#` headings → it shows **Processing**, then **Ready** within a few seconds without reloading.
- [ ] Upload a text PDF → **Ready**, with its page count.
- [ ] Upload a scanned PDF (or a PDF of only images) → **Failed** with "No text found, scanned PDFs aren't supported yet."
- [ ] Upload a `.exe` or `.png` renamed to `.pdf` → a red toast: "This file isn't a valid PDF." Nothing is added to the list.
- [ ] Upload the same `.md` again under another name → toast "You already uploaded this file as '…'."
- [ ] Drop three files at once → all three appear.
- [ ] Delete one → the confirmation dialog appears; Cancel keeps it; Delete removes it.
- [ ] Log out, sign up as `owner-test-2@example.com` → the list is empty.
- [ ] Check the chunks in the database (from `backend/`, read-only):

```bash
uv run python -c "from sqlalchemy import func, select; from app.database import SessionLocal; from app.models import Chunk, Document; s = SessionLocal(); print('documents', s.scalar(select(func.count()).select_from(Document)), 'chunks', s.scalar(select(func.count()).select_from(Chunk)), 'models', s.scalars(select(Chunk.embedding_model).distinct()).all())"
```

Expected: one or more chunks per Ready document; model `voyage-4`.

- [ ] **Step 3: Run every test one last time**

```bash
cd backend && uv run pytest && cd ..
cd frontend && npm test && npm run build && npm run lint && cd ..
```

Expected: backend `96 passed`; frontend `15 passed`; build and lint clean.

- [ ] **Step 4: Merge into main** (when the owner says so)

```bash
git checkout main
git merge --ff-only feature/uploads
git branch -d feature/uploads
```
