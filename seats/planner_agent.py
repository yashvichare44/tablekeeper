"""Planner seat — assigns work, does not write product code."""

from __future__ import annotations

import asyncio
import logging

from dotenv import load_dotenv

from band import Agent, configure_logging

from seats.common import make_adapter
from seats.workspace_tools import READ_TOOLS

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    load_dotenv()
    adapter = make_adapter("planner", READ_TOOLS)
    logger.info("Planner seat online")
    async with Agent.from_config("planner_agent", adapter=adapter) as agent:
        await agent.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
