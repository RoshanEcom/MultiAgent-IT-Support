"""Single place to construct LLM and embedding clients. All agents go through here
so the model can be swapped without touching agent code."""
from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.config import SETTINGS


@lru_cache(maxsize=1)
def get_chat_llm(temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(
        model=SETTINGS.openai_llm_model,
        temperature=temperature,
        api_key=SETTINGS.openai_api_key,
    )


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=SETTINGS.openai_embedding_model,
        api_key=SETTINGS.openai_api_key,
    )
