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
