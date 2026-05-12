"""Data-side helpers extracted from the original CLI.

Only the pieces used by the API surface (MessageBuffer mutators, message
classification, report saving) live here. The Rich/typer rendering layer
was dropped along with the CLI.
"""

from __future__ import annotations

import ast
import datetime
from collections import deque
from pathlib import Path


class MessageBuffer:
    """Captures progress of a TradingAgents run so the API can stream/serialise it.

    Mirrors the original CLI buffer minus any terminal-rendering concerns.
    """

    FIXED_AGENTS = {
        "Research Team": ["Bull Researcher", "Bear Researcher", "Research Manager"],
        "Trading Team": ["Trader"],
        "Risk Management": ["Aggressive Analyst", "Neutral Analyst", "Conservative Analyst"],
        "Portfolio Management": ["Portfolio Manager"],
    }

    ANALYST_MAPPING = {
        "market": "Market Analyst",
        "social": "Social Analyst",
        "news": "News Analyst",
        "fundamentals": "Fundamentals Analyst",
    }

    REPORT_SECTIONS = {
        "market_report": ("market", "Market Analyst"),
        "sentiment_report": ("social", "Social Analyst"),
        "news_report": ("news", "News Analyst"),
        "fundamentals_report": ("fundamentals", "Fundamentals Analyst"),
        "investment_plan": (None, "Research Manager"),
        "trader_investment_plan": (None, "Trader"),
        "final_trade_decision": (None, "Portfolio Manager"),
    }

    SECTION_TITLES = {
        "market_report": "Market Analysis",
        "sentiment_report": "Social Sentiment",
        "news_report": "News Analysis",
        "fundamentals_report": "Fundamentals Analysis",
        "investment_plan": "Research Team Decision",
        "trader_investment_plan": "Trading Team Plan",
        "final_trade_decision": "Portfolio Management Decision",
    }

    def __init__(self, max_length: int = 100) -> None:
        self.messages = deque(maxlen=max_length)
        self.tool_calls = deque(maxlen=max_length)
        self.current_report = None
        self.final_report = None
        self.agent_status: dict[str, str] = {}
        self.current_agent: str | None = None
        self.report_sections: dict[str, str | None] = {}
        self.selected_analysts: list[str] = []
        self._processed_message_ids: set = set()

    def init_for_analysis(self, selected_analysts: list[str]) -> None:
        self.selected_analysts = [a.lower() for a in selected_analysts]

        self.agent_status = {}
        for analyst_key in self.selected_analysts:
            if analyst_key in self.ANALYST_MAPPING:
                self.agent_status[self.ANALYST_MAPPING[analyst_key]] = "pending"

        for team_agents in self.FIXED_AGENTS.values():
            for agent in team_agents:
                self.agent_status[agent] = "pending"

        self.report_sections = {}
        for section, (analyst_key, _) in self.REPORT_SECTIONS.items():
            if analyst_key is None or analyst_key in self.selected_analysts:
                self.report_sections[section] = None

        self.current_report = None
        self.final_report = None
        self.current_agent = None
        self.messages.clear()
        self.tool_calls.clear()
        self._processed_message_ids.clear()

    def add_message(self, message_type: str, content) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.messages.append((timestamp, message_type, content))

    def add_tool_call(self, tool_name: str, args) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.tool_calls.append((timestamp, tool_name, args))

    def update_agent_status(self, agent: str, status: str) -> None:
        if agent in self.agent_status:
            self.agent_status[agent] = status
            self.current_agent = agent

    def update_report_section(self, section_name: str, content) -> None:
        if section_name in self.report_sections:
            self.report_sections[section_name] = content
            self._refresh_reports()

    def _refresh_reports(self) -> None:
        latest_section = None
        latest_content = None
        for section, content in self.report_sections.items():
            if content is not None:
                latest_section = section
                latest_content = content

        if latest_section and latest_content:
            self.current_report = f"### {self.SECTION_TITLES[latest_section]}\n{latest_content}"

        parts: list[str] = []
        analyst_sections = ["market_report", "sentiment_report", "news_report", "fundamentals_report"]
        if any(self.report_sections.get(s) for s in analyst_sections):
            parts.append("## Analyst Team Reports")
            for section in analyst_sections:
                value = self.report_sections.get(section)
                if value:
                    parts.append(f"### {self.SECTION_TITLES[section]}\n{value}")

        if self.report_sections.get("investment_plan"):
            parts.append("## Research Team Decision")
            parts.append(self.report_sections["investment_plan"])

        if self.report_sections.get("trader_investment_plan"):
            parts.append("## Trading Team Plan")
            parts.append(self.report_sections["trader_investment_plan"])

        if self.report_sections.get("final_trade_decision"):
            parts.append("## Portfolio Management Decision")
            parts.append(self.report_sections["final_trade_decision"])

        self.final_report = "\n\n".join(parts) if parts else None


_ANALYST_ORDER = ["market", "social", "news", "fundamentals"]
_ANALYST_AGENT_NAMES = {
    "market": "Market Analyst",
    "social": "Social Analyst",
    "news": "News Analyst",
    "fundamentals": "Fundamentals Analyst",
}
_ANALYST_REPORT_MAP = {
    "market": "market_report",
    "social": "sentiment_report",
    "news": "news_report",
    "fundamentals": "fundamentals_report",
}


def update_analyst_statuses(message_buffer: MessageBuffer, chunk: dict) -> None:
    """Mark each selected analyst as completed/in_progress/pending based on accumulated reports."""
    selected = message_buffer.selected_analysts
    found_active = False

    for analyst_key in _ANALYST_ORDER:
        if analyst_key not in selected:
            continue

        agent_name = _ANALYST_AGENT_NAMES[analyst_key]
        report_key = _ANALYST_REPORT_MAP[analyst_key]

        if chunk.get(report_key):
            message_buffer.update_report_section(report_key, chunk[report_key])

        has_report = bool(message_buffer.report_sections.get(report_key))
        if has_report:
            message_buffer.update_agent_status(agent_name, "completed")
        elif not found_active:
            message_buffer.update_agent_status(agent_name, "in_progress")
            found_active = True
        else:
            message_buffer.update_agent_status(agent_name, "pending")

    if not found_active and selected:
        if message_buffer.agent_status.get("Bull Researcher") == "pending":
            message_buffer.update_agent_status("Bull Researcher", "in_progress")


def _extract_content_string(content) -> str | None:
    def is_empty(val) -> bool:
        if val is None or val == "":
            return True
        if isinstance(val, str):
            s = val.strip()
            if not s:
                return True
            try:
                return not bool(ast.literal_eval(s))
            except (ValueError, SyntaxError):
                return False
        return not bool(val)

    if is_empty(content):
        return None

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, dict):
        text = content.get("text", "")
        return text.strip() if not is_empty(text) else None

    if isinstance(content, list):
        parts = [
            item.get("text", "").strip() if isinstance(item, dict) and item.get("type") == "text"
            else (item.strip() if isinstance(item, str) else "")
            for item in content
        ]
        result = " ".join(p for p in parts if p and not is_empty(p))
        return result if result else None

    return str(content).strip() if not is_empty(content) else None


def classify_message_type(message) -> tuple[str, str | None]:
    """Classify a LangChain message into (type, content) where type ∈ {User, Agent, Data, Control, System}."""
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    content = _extract_content_string(getattr(message, "content", None))

    if isinstance(message, HumanMessage):
        if content and content.strip() == "Continue":
            return ("Control", content)
        return ("User", content)

    if isinstance(message, ToolMessage):
        return ("Data", content)

    if isinstance(message, AIMessage):
        return ("Agent", content)

    return ("System", content)


def format_tool_args(args, max_length: int = 80) -> str:
    result = str(args)
    if len(result) > max_length:
        return result[: max_length - 3] + "..."
    return result


def save_report_to_disk(final_state: dict, ticker: str, save_path: Path) -> Path:
    """Persist a finished run's per-section markdown plus a consolidated report."""
    save_path.mkdir(parents=True, exist_ok=True)
    sections: list[str] = []

    analysts_dir = save_path / "1_analysts"
    analyst_parts: list[tuple[str, str]] = []
    for key, label, filename in (
        ("market_report", "Market Analyst", "market.md"),
        ("sentiment_report", "Social Analyst", "sentiment.md"),
        ("news_report", "News Analyst", "news.md"),
        ("fundamentals_report", "Fundamentals Analyst", "fundamentals.md"),
    ):
        value = final_state.get(key)
        if value:
            analysts_dir.mkdir(exist_ok=True)
            (analysts_dir / filename).write_text(value, encoding="utf-8")
            analyst_parts.append((label, value))
    if analyst_parts:
        content = "\n\n".join(f"### {name}\n{text}" for name, text in analyst_parts)
        sections.append(f"## I. Analyst Team Reports\n\n{content}")

    if final_state.get("investment_debate_state"):
        research_dir = save_path / "2_research"
        debate = final_state["investment_debate_state"]
        research_parts: list[tuple[str, str]] = []
        for key, label, filename in (
            ("bull_history", "Bull Researcher", "bull.md"),
            ("bear_history", "Bear Researcher", "bear.md"),
            ("judge_decision", "Research Manager", "manager.md"),
        ):
            value = debate.get(key)
            if value:
                research_dir.mkdir(exist_ok=True)
                (research_dir / filename).write_text(value, encoding="utf-8")
                research_parts.append((label, value))
        if research_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in research_parts)
            sections.append(f"## II. Research Team Decision\n\n{content}")

    if final_state.get("trader_investment_plan"):
        trading_dir = save_path / "3_trading"
        trading_dir.mkdir(exist_ok=True)
        (trading_dir / "trader.md").write_text(final_state["trader_investment_plan"], encoding="utf-8")
        sections.append(
            f"## III. Trading Team Plan\n\n### Trader\n{final_state['trader_investment_plan']}"
        )

    if final_state.get("risk_debate_state"):
        risk_dir = save_path / "4_risk"
        risk = final_state["risk_debate_state"]
        risk_parts: list[tuple[str, str]] = []
        for key, label, filename in (
            ("aggressive_history", "Aggressive Analyst", "aggressive.md"),
            ("conservative_history", "Conservative Analyst", "conservative.md"),
            ("neutral_history", "Neutral Analyst", "neutral.md"),
        ):
            value = risk.get(key)
            if value:
                risk_dir.mkdir(exist_ok=True)
                (risk_dir / filename).write_text(value, encoding="utf-8")
                risk_parts.append((label, value))
        if risk_parts:
            content = "\n\n".join(f"### {name}\n{text}" for name, text in risk_parts)
            sections.append(f"## IV. Risk Management Team Decision\n\n{content}")

        if risk.get("judge_decision"):
            portfolio_dir = save_path / "5_portfolio"
            portfolio_dir.mkdir(exist_ok=True)
            (portfolio_dir / "decision.md").write_text(risk["judge_decision"], encoding="utf-8")
            sections.append(
                f"## V. Portfolio Manager Decision\n\n### Portfolio Manager\n{risk['judge_decision']}"
            )

    header = (
        f"# Trading Analysis Report: {ticker}\n\n"
        f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    )
    out_file = save_path / "complete_report.md"
    out_file.write_text(header + "\n\n".join(sections), encoding="utf-8")
    return out_file
