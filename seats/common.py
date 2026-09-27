"""Shared Band seat bootstrap."""

from __future__ import annotations

from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver

from band import AdapterFeatures, Emit
from band.adapters import LangGraphAdapter

from seats.llm import make_llm

MANDATES = Path(__file__).resolve().parent.parent / "mandates"


def load_mandate(name: str) -> str:
    return (MANDATES / f"{name}.md").read_text(encoding="utf-8")


def make_adapter(mandate_name: str, additional_tools: list) -> LangGraphAdapter:
    return LangGraphAdapter(
        llm=make_llm(),
        checkpointer=InMemorySaver(),
        custom_section=load_mandate(mandate_name),
        additional_tools=additional_tools,
        features=AdapterFeatures(emit={Emit.TOOL_CALLS}),
    )
