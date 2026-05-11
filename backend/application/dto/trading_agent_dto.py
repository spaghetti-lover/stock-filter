from typing import Any

from pydantic import BaseModel


class RunRequest(BaseModel):
    symbol: str
    horizon: str = "Swing (1-5d)"
    provider: str = "claude"


class RunStartResponse(BaseModel):
    run_id: str


class RunStatusResponse(BaseModel):
    run_id: str
    symbol: str
    horizon: str
    started_at: str
    status: str
    agents: dict[str, Any]
    verdict: dict[str, Any] | None = None
    error: str | None = None
