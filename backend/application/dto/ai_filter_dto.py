from typing import Any

from pydantic import BaseModel, Field


class AIFilterCondition(BaseModel):
    key: str
    label: str
    params: dict[str, Any] = Field(default_factory=dict)


class AIFilterParseRequest(BaseModel):
    prompt: str
    provider: str = "claude"


class AIFilterParseResponse(BaseModel):
    conditions: list[AIFilterCondition]
    summary: str
    unsupported: list[str] = Field(default_factory=list)


class AIFilterApplyRequest(BaseModel):
    conditions: list[AIFilterCondition]


class AIFilterParamSpec(BaseModel):
    name: str
    type: str
    default: Any = None
    description: str | None = None


class AIFilterCatalogEntry(BaseModel):
    key: str
    label_template: str
    description: str
    params: list[AIFilterParamSpec]


class AIFilterCatalogResponse(BaseModel):
    entries: list[AIFilterCatalogEntry]
