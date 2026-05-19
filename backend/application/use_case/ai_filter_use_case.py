"""AI Filter use case: parse (NL -> JSON DSL) and apply (DSL -> stock list)."""

import json
import re
from typing import Any

from application.dto.ai_filter_dto import (
    AIFilterApplyRequest,
    AIFilterCondition,
    AIFilterParseRequest,
    AIFilterParseResponse,
)
from application.dto.stock_dto import FilteredStocksResponse
from application.mappers.stock_mapper import StockMapper
from application.services.ai_filter_catalog import CATALOG, public_catalog
from application.services.ai_filter_engine import apply_ai_conditions
from domain.agents.agent_provider import AgentProvider
from domain.repositories.layer1_stock_repository import Layer1StockRepository
from logger import get_logger

log = get_logger(__name__)


def _build_system_prompt() -> str:
    catalog_json = json.dumps(
        [e.model_dump() for e in public_catalog()],
        ensure_ascii=False,
        indent=2,
    )
    return f"""You translate a user's stock-filter request (often Vietnamese) into a strict JSON object.

Allowed condition keys come from this catalog. Each entry has key, label_template, description, and a params schema:

{catalog_json}

Output schema (return EXACTLY one JSON object, no markdown, no commentary):
{{
  "conditions": [
    {{
      "key": "<one of the catalog keys>",
      "label": "<English label, fill the catalog's label_template with the chosen params>",
      "params": {{ /* param name -> value, types per the catalog */ }}
    }}
  ],
  "summary": "<one short English sentence describing the filter>",
  "unsupported": [ "<any condition the user asked for that has no matching key>" ]
}}

Rules:
- Understand Vietnamese and English prompts.
- Labels and summary MUST be English even if the user writes Vietnamese.
- Only use keys present in the catalog. If a user request has no match, leave conditions empty and add a short description to unsupported.
- Use the catalog defaults unless the user gave a specific number.
- When the user mentions tỷ / billion / B → param is in billions.

Examples:

User: "Lọc cổ phiếu thanh khoản cao"
Output: {{"conditions":[{{"key":"high_liquidity","label":"High liquidity (GTGD20 ≥ 20.0B VND)","params":{{"min_billion":20.0}}}}],"summary":"Filter stocks with high liquidity","unsupported":[]}}

User: "Cổ phiếu HOSE biến động thấp, GTGD trên 50 tỷ"
Output: {{"conditions":[{{"key":"exchange_in","label":"Exchange in ['HOSE']","params":{{"exchanges":["HOSE"]}}}},{{"key":"stable_cv","label":"Low volatility (CV < 100.0%)","params":{{"cv_cap":100.0}}}},{{"key":"high_liquidity","label":"High liquidity (GTGD20 ≥ 50.0B VND)","params":{{"min_billion":50.0}}}}],"summary":"HOSE stocks with low volatility and GTGD20 above 50B","unsupported":[]}}

User: "Lọc cổ phiếu vượt đỉnh 52 tuần"
Output: {{"conditions":[],"summary":"52-week high not supported in demo","unsupported":["52-week high breakout"]}}
"""


_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def _strip_fences(text: str) -> str:
    m = _FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    return text.strip()


def _scan_json_objects(text: str) -> list[str]:
    """Yield substrings of balanced {...} blocks (string-aware)."""
    out: list[str] = []
    depth = 0
    start = -1
    in_str = False
    esc = False
    for i, ch in enumerate(text):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start >= 0:
                    out.append(text[start : i + 1])
                    start = -1
    return out


def _extract_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = _strip_fences(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Pick the largest valid JSON object found anywhere in the text.
    candidates = _scan_json_objects(cleaned) or _scan_json_objects(text)
    candidates.sort(key=len, reverse=True)
    for c in candidates:
        try:
            obj = json.loads(c)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None


class AIFilterUseCase:
    def __init__(self, provider: AgentProvider, repo: Layer1StockRepository):
        self._provider = provider
        self._repo = repo

    async def parse(self, request: AIFilterParseRequest) -> AIFilterParseResponse:
        system_prompt = _build_system_prompt()
        messages = [{"role": "user", "content": request.prompt}]

        raw = await self._provider.chat(messages=messages, system_prompt=system_prompt)

        if raw.startswith("Error:"):
            log.error("AI filter parse: provider error: %s", raw[:500])
            return AIFilterParseResponse(
                conditions=[],
                summary=f"Provider error: {raw[len('Error:'):].strip() or 'unknown'}",
                unsupported=["provider_error"],
            )

        parsed = _extract_json(raw)

        if parsed is None:
            log.warning("AI filter parse: invalid JSON, retrying once. Raw=%r", raw[:500])
            retry_messages = [
                {"role": "user", "content": request.prompt},
                {"role": "assistant", "content": raw},
                {"role": "user", "content": "Your previous reply was not valid JSON. Reply again with ONLY the JSON object."},
            ]
            raw = await self._provider.chat(messages=retry_messages, system_prompt=system_prompt)
            if raw.startswith("Error:"):
                return AIFilterParseResponse(
                    conditions=[],
                    summary=f"Provider error: {raw[len('Error:'):].strip() or 'unknown'}",
                    unsupported=["provider_error"],
                )
            parsed = _extract_json(raw)

        if parsed is None:
            return AIFilterParseResponse(
                conditions=[],
                summary="Could not parse AI response",
                unsupported=["parse_failed"],
            )

        raw_conditions = parsed.get("conditions") or []
        valid: list[AIFilterCondition] = []
        unsupported: list[str] = list(parsed.get("unsupported") or [])

        for item in raw_conditions:
            if not isinstance(item, dict):
                continue
            key = item.get("key")
            if not isinstance(key, str):
                continue
            entry = CATALOG.get(key)
            if entry is None:
                unsupported.append(key)
                continue
            params = item.get("params") or {}
            if not isinstance(params, dict):
                params = {}
            label = item.get("label") or entry.render_label(params)
            valid.append(AIFilterCondition(key=key, label=label, params=params))

        summary = parsed.get("summary") or "Filtered stocks"
        if not isinstance(summary, str):
            summary = "Filtered stocks"

        return AIFilterParseResponse(
            conditions=valid,
            summary=summary,
            unsupported=unsupported,
        )

    async def apply(self, request: AIFilterApplyRequest) -> FilteredStocksResponse:
        stocks, _ = await self._repo.list_stocks()
        responses = StockMapper.to_response_list(stocks)
        passed, rejected = apply_ai_conditions(responses, request.conditions)
        return FilteredStocksResponse(passed=passed, rejected=rejected, market_regime=None)
