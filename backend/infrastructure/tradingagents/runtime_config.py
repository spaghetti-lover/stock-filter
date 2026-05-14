"""Process-wide runtime config singleton for trading-agent runs.

Lightweight replacement for the deleted ``dataflows.config`` module. Stores
the active config dict so analyst factories can read settings (e.g.
``output_language``) without each call site threading the config through.
"""

from typing import Any

from infrastructure.tradingagents.default_config import DEFAULT_CONFIG


_config: dict[str, Any] = DEFAULT_CONFIG.copy()


def set_config(config: dict[str, Any]) -> None:
    _config.clear()
    _config.update(DEFAULT_CONFIG)
    _config.update(config)


def get_config() -> dict[str, Any]:
    return _config.copy()
