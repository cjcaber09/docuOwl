from types import SimpleNamespace

import anthropic

from app.chat.claude import (
    ANSWER_MODEL,
    DEFAULT_TITLE,
    HELPER_MODEL,
    AnswerEnd,
    CitedPassage,
    ClaudeChatModel,
    TextChunk,
    build_answer_request,
    translate_stream_event,
)
from app.chat.retrieval import Passage

PASSAGES = [
    Passage(document_id=None, filename="terms.pdf", text="Refunds take 30 days.", location="p. 4"),
    Passage(document_id=None, filename="notes.md", text="Annual plans are pro rata.", location="Annual"),
]


def text_event(text):
    return SimpleNamespace(type="content_block_delta", delta=SimpleNamespace(type="text_delta", text=text))


def citation_event(index, quote):
    citation = SimpleNamespace(type="content_block_location", document_index=index, cited_text=quote)
    return SimpleNamespace(type="content_block_delta", delta=SimpleNamespace(type="citations_delta", citation=citation))


class FakeStream:
    def __init__(self, events, stop_reason):
        self.events, self.stop_reason = events, stop_reason

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def __iter__(self):
        return iter(self.events)

    def get_final_message(self):
        return SimpleNamespace(stop_reason=self.stop_reason)


class FakeAnthropic:
    """Just enough of the SDK client for ClaudeChatModel, recording every request."""

    def __init__(self, stream=None, reply=None, error=None):
        self.requests, self._stream, self._reply, self._error = [], stream, reply, error
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._record_stream))
        self.messages = SimpleNamespace(create=self._record_create)

    def _record_stream(self, **request):
        self.requests.append(request)
        return self._stream

    def _record_create(self, **request):
        self.requests.append(request)
        if self._error:
            raise self._error
        return self._reply


def reply(text, stop_reason="end_turn"):
    return SimpleNamespace(stop_reason=stop_reason, content=[SimpleNamespace(type="text", text=text)])


def test_answer_request_sends_cited_documents_and_the_question_last():
    history = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]

    request = build_answer_request(history, PASSAGES, "How long do refunds take?")

    assert request["model"] == ANSWER_MODEL == "claude-opus-5-5"
    assert request["output_config"] == {"effort": "low"}
    assert request["fallbacks"] == "default"
    assert request["betas"] == ["server-side-fallback-2026-07-01"]
    assert request["messages"][:2] == history
    content = request["messages"][2]["content"]
    assert content[0] == {
        "type": "document",
        "source": {"type": "content", "content": [{"type": "text", "text": "Refunds take 30 days."}]},
        "title": "terms.pdf",
        "context": "From terms.pdf, p. 4",
        "citations": {"enabled": True},
    }
    assert content[-1] == {"type": "text", "text": "How long do refunds take?"}


def test_stream_events_become_answer_events():
    assert translate_stream_event(text_event("Hi")) == TextChunk("Hi")
    assert translate_stream_event(citation_event(1, "pro rata")) == CitedPassage(1, "pro rata")
    assert translate_stream_event(SimpleNamespace(type="message_start")) is None


def test_a_refused_answer_ends_with_refused():
    client = FakeAnthropic(stream=FakeStream([text_event("Sorry")], stop_reason="refusal"))

    events = list(ClaudeChatModel(client).stream_answer([], PASSAGES, "?"))

    assert events == [TextChunk("Sorry"), AnswerEnd(refused=True)]


def test_follow_up_question_is_rewritten_by_haiku_without_fallbacks():
    client = FakeAnthropic(reply=reply("What is the refund period for annual plans?"))
    history = [{"role": "user", "content": "Refunds?"}, {"role": "assistant", "content": "30 days."}]

    rewritten = ClaudeChatModel(client).rewrite_question(history, "And annual?")

    assert rewritten == "What is the refund period for annual plans?"
    assert client.requests[0]["model"] == HELPER_MODEL == "claude-haiku-5-5"
    assert "fallbacks" not in client.requests[0]


def test_rewrite_falls_back_to_the_original_question():
    failing = FakeAnthropic(error=anthropic.APIConnectionError(request=None))
    refusing = FakeAnthropic(reply=reply("", stop_reason="refusal"))

    assert ClaudeChatModel(failing).rewrite_question([], "And annual?") == "And annual?"
    assert ClaudeChatModel(refusing).rewrite_question([], "And annual?") == "And annual?"


def test_titles_are_cleaned_and_have_a_fallback():
    assert ClaudeChatModel(FakeAnthropic(reply=reply('"Refund policy"\n'))).make_title("q", "a") == "Refund policy"
    assert ClaudeChatModel(FakeAnthropic(reply=reply(""))).make_title("q", "a") == DEFAULT_TITLE
