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
