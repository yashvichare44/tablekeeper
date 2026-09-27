"""Tom the cat agent (LangGraph)."""

from __future__ import annotations

import asyncio
import logging

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver

from characters import generate_tom_prompt
from seats.llm import make_llm

from band import Agent, configure_logging
from band.adapters import LangGraphAdapter

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    load_dotenv()

    # Load Tom's credentials from agent_config.yaml
    # Create adapter with Tom's character prompt
    adapter = LangGraphAdapter(
        llm=make_llm(),
        checkpointer=InMemorySaver(),
        custom_section=generate_tom_prompt("Tom"),
    )

    logger.info("Tom is on the prowl, looking for Jerry...")
    async with Agent.from_config(
        "tom_agent",
        adapter=adapter,
    ) as agent:
        await agent.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
