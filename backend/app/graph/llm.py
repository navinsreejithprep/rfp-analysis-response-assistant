from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from app import config


@lru_cache(maxsize=1)
def get_chat_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=config.OPENAI_CHAT_MODEL,
        api_key=config.OPENAI_API_KEY,
        temperature=0.1,
    )


def structured(schema):
    """Return a runnable that calls the chat model and parses its output into `schema`."""
    return get_chat_model().with_structured_output(schema)
