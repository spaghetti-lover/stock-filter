"""Unified FastMCP tool catalog shared by chat agents and trading agents."""

from infrastructure.tools.catalog import CATALOG, SERVER_INSTANCES
from infrastructure.tools.toolset import (
    CHAT_ALL,
    FUNDAMENTALS_ANALYST,
    MARKET_ANALYST,
    NEWS_ANALYST,
    SOCIAL_ANALYST,
    ToolSet,
)
from infrastructure.tools.registry import McpToolRegistry

__all__ = [
    "CATALOG",
    "SERVER_INSTANCES",
    "ToolSet",
    "CHAT_ALL",
    "MARKET_ANALYST",
    "FUNDAMENTALS_ANALYST",
    "NEWS_ANALYST",
    "SOCIAL_ANALYST",
    "McpToolRegistry",
]
