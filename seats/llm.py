"""OpenAI-compatible chat model used by every factory seat."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI


def make_llm() -> ChatOpenAI:
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")
    if not base_url or not model:
        raise RuntimeError("LLM_BASE_URL and LLM_MODEL must be set in .env")

    return ChatOpenAI(
        model=model,
        api_key=os.getenv("LLM_API_KEY", "not-needed"),
        base_url=base_url,
        max_retries=6,
        timeout=180,
        temperature=0.2,
        max_tokens=4096,
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    )
