"""Reviewer seat — re-runs checks and can block."""

from __future__ import annotations

import asyncio
import logging

from dotenv import load_dotenv

from band import Agent, configure_logging

from seats.common import make_adapter
from seats.workspace_tools import REVIEW_TOOLS

configure_logging(logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    load_dotenv()
    adapter = make_adapter("reviewer", REVIEW_TOOLS)
    logger.info("Reviewer seat online")
    async with Agent.from_config("reviewer_agent", adapter=adapter) as agent:
        await agent.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
