from app.chat.claude import NOT_FOUND_REPLY, AnswerEnd, CitedPassage, TextChunk, get_chat_model
from app.chat.demo import DemoChatModel
from app.chat.retrieval import Passage
from app.config import get_settings

PASSAGES = [
    Passage(document_id=None, filename="terms.pdf", text="Refunds take 30 days.", location="p. 4"),
    Passage(document_id=None, filename="notes.md", text="Annual plans are pro rata.", location="Annual"),
]


def answer_text(events):
    return "".join(event.text for event in events if isinstance(event, TextChunk))


def test_demo_answer_quotes_the_best_passage_with_its_citation():
    events = list(DemoChatModel().stream_answer([], PASSAGES, "Refunds?"))

    assert answer_text(events) == 'From terms.pdf (p. 4):\n"Refunds take 30 days."'
    assert len([event for event in events if isinstance(event, TextChunk)]) > 1  # streamed in pieces
    assert CitedPassage(0, "Refunds take 30 days.") in events
    assert events[-1] == AnswerEnd(refused=False)


def test_demo_answer_without_passages_says_not_found():
    events = list(DemoChatModel().stream_answer([], [], "Capital of France?"))

    assert answer_text(events) == NOT_FOUND_REPLY
    assert not any(isinstance(event, CitedPassage) for event in events)


def test_demo_keeps_the_question_and_titles_from_its_first_words():
    demo = DemoChatModel()

    assert demo.rewrite_question([{"role": "user", "content": "Hi"}], "And annual?") == "And annual?"
    assert demo.make_title("How long do I have to get a refund?", "…") == "How long do I have to…"
    assert demo.make_title("Refunds?", "…") == "Refunds?"


def test_demo_setting_picks_the_demo_model(monkeypatch):
    monkeypatch.setattr(get_settings(), "chat_model", "demo")
    get_chat_model.cache_clear()
    try:
        assert isinstance(get_chat_model(), DemoChatModel)
    finally:
        get_chat_model.cache_clear()
