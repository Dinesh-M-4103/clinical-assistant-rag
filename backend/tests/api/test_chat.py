import pytest
from fastapi.testclient import TestClient

from app.rag.errors import LLMUnavailableError
from app.rag.types import DoneEvent, ErrorEvent, Role, TokenEvent, Turn
from tests.fakes import FakePipeline, sample_answer
from tests.helpers import UHID, parse_sse

CHAT_URL = f"/api/v1/patients/{UHID}/chat"
STREAM_URL = f"{CHAT_URL}/stream"
QUESTION = {"question": "What is the latest HbA1c?"}


def test_chat_returns_answer_citations_and_trace(
    client: TestClient, patient: dict[str, object], pipeline: FakePipeline
) -> None:
    response = client.post(CHAT_URL, json=QUESTION)

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "HbA1c was 7.8% on 2025-03-02 [C1]."
    assert [(c["id"], c["cited"]) for c in body["citations"]] == [("C1", True), ("C2", False)]
    assert body["citations"][0]["page"] == 2
    trace = body["trace"]
    assert trace["intent"] == "question"
    assert trace["candidates"][0] == {
        "id": "C1",
        "dense_rank": 1,
        "bm25_rank": 3,
        "fused_score": 0.031,
        "rerank_score": 0.91,
    }
    assert trace["models"] == {
        "llm": "fake-llm",
        "embedding": "fake-embed",
        "reranker": "fake-rerank",
    }
    assert trace["tokens"] == {"prompt": 1200, "completion": 180}
    assert pipeline.questions == [(UHID, QUESTION["question"], [])]


def test_chat_passes_only_the_last_ten_turns(
    client: TestClient, patient: dict[str, object], pipeline: FakePipeline
) -> None:
    roles: list[Role] = ["user", "assistant"]
    turns = [Turn(role=roles[i % 2], content=f"turn {i}") for i in range(14)]
    history = [{"role": t.role, "content": t.content} for t in turns]

    client.post(CHAT_URL, json=QUESTION | {"history": history})

    [(_, _, received)] = pipeline.questions
    assert received == turns[-10:]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"question": ""},
        {"question": "   "},
        {"question": "x" * 2001},
        {"question": "hi", "history": [{"role": "system", "content": "x"}]},
    ],
)
def test_invalid_chat_request_is_422(
    client: TestClient, patient: dict[str, object], payload: dict[str, object]
) -> None:
    response = client.post(CHAT_URL, json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_chat_for_unknown_patient_is_404(client: TestClient, pipeline: FakePipeline) -> None:
    response = client.post("/api/v1/patients/NOPE1/chat", json=QUESTION)

    assert response.status_code == 404
    assert pipeline.questions == []


def test_llm_outage_maps_to_502(
    client: TestClient, patient: dict[str, object], pipeline: FakePipeline
) -> None:
    pipeline.answer_error = LLMUnavailableError("quota exhausted for key AQ.secret")

    response = client.post(CHAT_URL, json=QUESTION)

    assert response.status_code == 502
    error = response.json()["error"]
    assert error["code"] == "llm_unavailable"
    assert "AQ.secret" not in error["message"]


def test_stream_emits_events_in_contract_order(
    client: TestClient, patient: dict[str, object]
) -> None:
    response = client.post(STREAM_URL, json=QUESTION)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    names = [name for name, _ in events]
    assert names[:2] == ["meta", "citations"]
    assert names[-1] == "done"
    assert set(names[2:-1]) == {"token"}
    assert events[0][1] == {"intent": "question", "rewritten_query": "latest HbA1c value"}
    assert [c["id"] for c in events[1][1]] == ["C1", "C2"]
    assert all(c["cited"] is False for c in events[1][1])
    streamed = "".join(payload["text"] for name, payload in events if name == "token")
    assert streamed.strip() == sample_answer().answer
    final = events[-1][1]
    assert final["answer"] == sample_answer().answer
    assert final["citations"][0]["cited"] is True
    assert final["trace"]["timings_ms"]["generation"] == 900


def test_stream_forwards_pipeline_error_event_and_stops(
    client: TestClient, patient: dict[str, object], pipeline: FakePipeline
) -> None:
    pipeline.stream_events = [
        TokenEvent(text="partial "),
        ErrorEvent(code="llm_unavailable", message="Model unavailable."),
        TokenEvent(text="never sent"),
    ]

    events = parse_sse(client.post(STREAM_URL, json=QUESTION).text)

    assert events == [
        ("token", {"text": "partial "}),
        ("error", {"code": "llm_unavailable", "message": "Model unavailable."}),
    ]


def test_stream_stops_after_done(
    client: TestClient, patient: dict[str, object], pipeline: FakePipeline
) -> None:
    answer = sample_answer()
    pipeline.stream_events = [
        DoneEvent(answer=answer.answer, citations=[], trace=answer.trace),
        TokenEvent(text="late"),
    ]

    events = parse_sse(client.post(STREAM_URL, json=QUESTION).text)

    assert [name for name, _ in events] == ["done"]


def test_stream_turns_rag_exception_into_error_event(
    client: TestClient, patient: dict[str, object], pipeline: FakePipeline
) -> None:
    pipeline.stream_error = LLMUnavailableError("rate limited")

    events = parse_sse(client.post(STREAM_URL, json=QUESTION).text)

    assert [name for name, _ in events] == ["meta", "error"]
    assert events[-1][1]["code"] == "llm_unavailable"


def test_stream_hides_unexpected_exception_details(
    client: TestClient, patient: dict[str, object], pipeline: FakePipeline
) -> None:
    pipeline.stream_error = RuntimeError(r"Traceback D:\secret\path")

    events = parse_sse(client.post(STREAM_URL, json=QUESTION).text)

    assert events[-1] == (
        "error",
        {"code": "internal_error", "message": "An unexpected error occurred."},
    )


def test_stream_for_unknown_patient_is_a_plain_404(client: TestClient) -> None:
    response = client.post("/api/v1/patients/NOPE1/chat/stream", json=QUESTION)

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["error"]["code"] == "not_found"
