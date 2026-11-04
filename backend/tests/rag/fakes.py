"""In-memory stand-ins for the RAG package's Protocols, so unit tests need no models or network."""

import hashlib
import math
import re
from collections.abc import Iterator, Sequence

from app.rag.llm import LLMDelta, LLMResult
from app.rag.types import Chunk, Prompt, TokenUsage

_WORD = re.compile(r"[a-z0-9]+")
_DIMENSIONS = 64


def _words(text: str) -> list[str]:
    return _WORD.findall(text.lower())


class FakeEmbedder:
    """Hashed bag-of-words vectors: texts sharing words are close, unrelated texts are not."""

    def __init__(self, model_name: str = "fake-embedder") -> None:
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    def count_tokens(self, text: str) -> int:
        return len(text.split())

    @staticmethod
    def _vector(text: str) -> list[float]:
        vector = [0.0] * _DIMENSIONS
        for word in _words(text):
            vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % _DIMENSIONS] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


class InMemoryVectorStore:
    """Per-patient dict of chunks; the same structure as the Chroma store's isolation."""

    def __init__(self) -> None:
        self._data: dict[str, list[tuple[Chunk, Sequence[float]]]] = {}

    def add_chunks(
        self, patient_id: str, chunks: Sequence[Chunk], embeddings: Sequence[Sequence[float]]
    ) -> None:
        self._data.setdefault(patient_id, []).extend(zip(chunks, embeddings, strict=True))

    def search(self, patient_id: str, embedding: Sequence[float], k: int) -> list[Chunk]:
        rows = self._data.get(patient_id, [])
        ranked = sorted(
            rows, key=lambda row: -sum(a * b for a, b in zip(row[1], embedding, strict=True))
        )
        return [chunk for chunk, _ in ranked[:k]]

    def all_chunks(self, patient_id: str) -> list[Chunk]:
        return [chunk for chunk, _ in self._data.get(patient_id, [])]

    def delete_report(self, patient_id: str, report_id: str) -> None:
        rows = self._data.get(patient_id, [])
        self._data[patient_id] = [row for row in rows if row[0].report_id != report_id]

    def delete_patient(self, patient_id: str) -> None:
        self._data.pop(patient_id, None)


class FailingVectorStore(InMemoryVectorStore):
    """A store whose searches fail, to exercise the pipeline's error handling."""

    def __init__(self, error: Exception) -> None:
        super().__init__()
        self._error = error

    def search(self, patient_id: str, embedding: Sequence[float], k: int) -> list[Chunk]:
        raise self._error


class OverlapReranker:
    """Scores a passage by the share of query words it contains (0 when unrelated)."""

    model_name = "fake-reranker"

    def score(self, query: str, passages: Sequence[str]) -> list[float]:
        query_words = set(_words(query))
        return [
            len(query_words & set(_words(passage))) / len(query_words) if query_words else 0.0
            for passage in passages
        ]


class ScriptedLLM:
    """Returns canned text and records every prompt it was given."""

    model_name = "fake-llm"

    def __init__(self, reply: str = "Answer [C1].", *, fail_with: Exception | None = None) -> None:
        self.reply = reply
        self.fail_with = fail_with
        self.prompts: list[Prompt] = []

    def generate(self, prompt: Prompt) -> LLMResult:
        self.prompts.append(prompt)
        if self.fail_with:
            raise self.fail_with
        return LLMResult(self.reply, TokenUsage(prompt=10, completion=5))

    def stream(self, prompt: Prompt) -> Iterator[LLMDelta]:
        self.prompts.append(prompt)
        if self.fail_with:
            raise self.fail_with
        for word in self.reply.split(" "):
            yield LLMDelta(word + " ")
        yield LLMDelta("", TokenUsage(prompt=10, completion=5))


def make_chunk(
    chunk_id: str = "r1:0",
    text: str = "Metformin 500 mg twice daily.",
    *,
    report_id: str = "r1",
    report_name: str = "Prescription",
    page: int = 1,
    section: str | None = "Medications",
) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        report_id=report_id,
        report_name=report_name,
        category="prescription",
        page=page,
        section=section,
        text=text,
    )
