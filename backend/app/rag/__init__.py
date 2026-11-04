"""Patient-scoped retrieval-augmented generation over clinical PDF reports.

The API layer only needs :class:`app.rag.pipeline.RagPipeline`. Map of the package:

    ingestion/     PDF -> clean pages -> sections -> sentence-aware chunks
    embeddings.py  text -> vectors (BGE, local)
    vectorstore.py one ChromaDB collection per patient
    retrieval/     dense + BM25 -> RRF fusion -> cross-encoder rerank -> relevance gate
    query.py       small-talk router and follow-up rewriting
    prompts.py     every prompt and canned reply
    llm.py         Gemini client (streaming, retries)
    citations.py   verifies [C#] markers against what was retrieved
    pipeline.py    ties the stages together and records a trace
"""
