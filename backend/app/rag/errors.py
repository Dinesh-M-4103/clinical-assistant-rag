"""Domain errors raised by the RAG package.

Each error carries a stable snake_case ``code`` so callers (the HTTP layer, the
streaming pipeline) can translate it without inspecting messages.
"""


class RagError(Exception):
    """Base class for every error the RAG package raises on purpose."""

    code = "rag_error"


class InvalidPdfError(RagError):
    """The file could not be opened as a PDF (corrupt or encrypted)."""

    code = "invalid_pdf"


class NoExtractableTextError(RagError):
    """The PDF opened fine but holds no text layer (for example a scanned image)."""

    code = "no_extractable_text"


class EmbeddingModelMismatchError(RagError):
    """A stored collection was built with a different embedding model than the active one.

    Mixing vector spaces silently returns nonsense, and silently deleting the
    collection would destroy data, so the operator has to decide (re-ingest).
    """

    code = "embedding_model_mismatch"


class LLMUnavailableError(RagError):
    """The language model is not configured, unreachable, rate limited or returned nothing."""

    code = "llm_unavailable"
