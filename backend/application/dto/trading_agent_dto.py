from typing import Any

from pydantic import BaseModel


class StartRunRequest(BaseModel):
    ticker: str
    analysis_date: str
    analysts: list[str]
    research_depth: int
    llm_provider: str
    shallow_thinker: str
    deep_thinker: str
    output_language: str | None = "English"
    backend_url: str | None = None
    google_thinking_level: str | None = None
    openai_reasoning_effort: str | None = None
    anthropic_effort: str | None = None
    checkpoint_enabled: bool = False
    youtube_urls: list[str] | None = None


class StartRunResponse(BaseModel):
    run_id: str


class SaveReportRequest(BaseModel):
    save_path: str | None = None


class SaveReportResponse(BaseModel):
    saved_to: str
    save_path: str


class AnnouncementsResponse(BaseModel):
    announcements: list[str]
    require_attention: bool


class CatalogChoice(BaseModel):
    label: str
    value: str


class DepthOption(BaseModel):
    label: str
    hint: str
    value: int


class ProviderOption(BaseModel):
    label: str
    key: str
    backend_url: str | None


class CatalogResponse(BaseModel):
    analysts: list[str]
    languages: list[str]
    depths: list[DepthOption]
    providers: list[ProviderOption]
    models: dict[str, dict[str, list[CatalogChoice]]]


class RunSnapshotResponse(BaseModel):
    run_id: str
    status: str
    started_at: str
    elapsed_seconds: int
    config: dict[str, Any]
    selected_analysts: list[str]
    agents: dict[str, str]
    reports: dict[str, str]
    messages: list[dict[str, str]]
    tool_calls: list[dict[str, str]]
    stats: dict[str, int]
    error: str | None
    has_final_state: bool


class RunReportResponse(BaseModel):
    run_id: str
    status: str
    ticker: str | None
    analysis_date: str | None
    reports: dict[str, str]
    final_state: dict[str, Any] | None
