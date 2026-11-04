from typing import Literal

from pydantic import BaseModel


class Health(BaseModel):
    status: Literal["ok"]
    llm_configured: bool
    embedding_model: str
    reranker_model: str
    version: str
