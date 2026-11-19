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
