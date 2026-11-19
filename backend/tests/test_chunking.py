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
