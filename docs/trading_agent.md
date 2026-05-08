# TradingAgents — Architecture & Sequence Reference

Snapshot of the current system, sufficient to rebuild and to plug an upstream
stock-filter in front of it. Source-of-truth files are referenced inline so you
can verify any block against the code.

---

## 1. Architecture Overview

```mermaid
flowchart TB
    subgraph Entry["Entry Layer"]
        CLI["cli/main.py<br/>(Typer)"]
        API["main.py / programmatic<br/>TradingAgentsGraph.propagate(ticker, date)"]
    end

    subgraph Orchestration["Orchestration — tradingagents/graph/"]
        TG["TradingAgentsGraph<br/>trading_graph.py"]
        SETUP["GraphSetup<br/>setup.py"]
        PROP["Propagator<br/>propagation.py"]
        COND["Conditional Logic<br/>conditional_logic.py"]
        SIG["SignalProcessor<br/>signal_processing.py"]
        CKPT["LangGraph Checkpoint<br/>(crash resume)"]
    end

    subgraph State["Shared State — agents/utils/agent_states.py"]
        AS["AgentState<br/>messages, ticker, date,<br/>past_context, *_report,<br/>investment_plan,<br/>trader_investment_plan,<br/>final_trade_decision,<br/>InvestDebateState,<br/>RiskDebateState"]
    end

    subgraph P1["Phase I — Analyst Team (parallel-capable, run sequentially)"]
        MA["Market Analyst"]
        SA["Social Analyst"]
        NA["News Analyst"]
        FA["Fundamentals Analyst"]
        TN["ToolNodes (4)<br/>market / social / news / fundamentals"]
    end

    subgraph P2["Phase II — Research Debate"]
        BULL["Bull Researcher"]
        BEAR["Bear Researcher"]
        RM["Research Manager (deep LLM)<br/>→ ResearchPlan (structured)"]
    end

    subgraph P3["Phase III — Trading"]
        TR["Trader (quick LLM)<br/>→ TraderProposal (structured)"]
    end

    subgraph P4["Phase IV — Risk Debate"]
        AGG["Aggressive Debator"]
        CON["Conservative Debator"]
        NEU["Neutral Debator"]
        PM["Portfolio Manager (deep LLM)<br/>→ PortfolioDecision (structured)"]
    end

    subgraph Data["Data Layer — tradingagents/dataflows/"]
        ROUTE["route_to_vendor()<br/>interface.py"]
        YF["yfinance"]
        AV["Alpha Vantage"]
    end

    subgraph LLM["LLM Layer"]
        PROV["Providers: OpenAI / Google / Anthropic<br/>deep_think_llm + quick_think_llm"]
    end

    subgraph Mem["Memory & Persistence"]
        TML["TradingMemoryLog<br/>memory.py<br/>(store → resolve → inject)"]
        LOGS["Reports & full_states_log<br/>~/.tradingagents/logs/{ticker}/{date}/"]
        MMD["trading_memory.md"]
    end


    CLI --> TG
    API --> TG
    TG --> SETUP
    TG --> PROP
    TG --> CKPT
    SETUP --> COND
    PROP --> AS
    TML -- past_context --> AS

    AS --> MA --> TN --> MA
    MA --> SA --> TN --> SA
    SA --> NA --> TN --> NA
    NA --> FA --> TN --> FA
    FA --> BULL
    BULL <--> BEAR
    BEAR --> RM --> TR
    TR --> AGG
    AGG --> CON --> NEU --> AGG
    NEU --> PM --> SIG
    SIG --> TML
    SIG --> LOGS
    TML --> MMD

    TN --> ROUTE --> YF
    ROUTE -. fallback .-> AV
    MA & SA & NA & FA & BULL & BEAR & RM & TR & AGG & CON & NEU & PM --> PROV
```

### Component roles (one-line)

| Component | File | Role |
|---|---|---|
| `TradingAgentsGraph` | `tradingagents/graph/trading_graph.py` | Public façade; `propagate(ticker, date) → (state, decision)` |
| `GraphSetup` | `tradingagents/graph/setup.py` | Builds the LangGraph DAG from selected analysts |
| `Propagator` | `tradingagents/graph/propagation.py` | Seeds initial `AgentState` with ticker/date/past memory |
| `Conditional Logic` | `tradingagents/graph/conditional_logic.py` | Tool-call routing, debate-loop counters |
| `SignalProcessor` | `tradingagents/graph/signal_processing.py` | Parses Portfolio Manager output → 5-tier rating |
| Analysts (×4) | `tradingagents/agents/analysts/` | Pull data via tools, write `*_report` |
| Researchers (Bull/Bear) | `tradingagents/agents/researchers/` | Adversarial debate over the four reports |
| Research Manager | `tradingagents/agents/managers/research_manager.py` | Synthesizes debate → `ResearchPlan` |
| Trader | `tradingagents/agents/trader/` | Converts plan → entry/exit/size proposal |
| Risk Debators (×3) | `tradingagents/agents/risk_mgmt/` | Aggressive / Conservative / Neutral round-robin |
| Portfolio Manager | `tradingagents/agents/managers/portfolio_manager.py` | Final structured decision + rating |
| Data routing | `tradingagents/dataflows/interface.py` | `route_to_vendor()` with rate-limit fallback |
| Memory | `tradingagents/agents/utils/memory.py` | Stores decisions, resolves PnL, injects lessons |

### Rating taxonomy
`Buy | Overweight | Hold | Underweight | Sell` — produced by Portfolio Manager, extracted by `parse_rating()` in `tradingagents/graph/rating.py`.

---

## 2. Sequence Diagram — One Full Run

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant CLI as CLI / Caller
    participant TG as TradingAgentsGraph
    participant Prop as Propagator
    participant Mem as TradingMemoryLog
    participant Graph as LangGraph Runtime
    participant MA as Market Analyst
    participant SA as Social Analyst
    participant NA as News Analyst
    participant FA as Fundamentals Analyst
    participant Tools as ToolNode → route_to_vendor
    participant Vendor as yfinance / Alpha Vantage
    participant Bull as Bull Researcher
    participant Bear as Bear Researcher
    participant RM as Research Manager
    participant Tr as Trader
    participant Risk as Risk Debate (Agg→Con→Neu)
    participant PM as Portfolio Manager
    participant Sig as SignalProcessor
    participant FS as Disk (logs + memory.md)

    User->>CLI: run(ticker, date, analysts, depth, provider)
    CLI->>TG: propagate(ticker, date)
    TG->>Mem: get_past_context(ticker)
    Mem-->>TG: prior decisions + reflections
    TG->>Prop: build initial AgentState
    Prop-->>Graph: AgentState{ticker,date,past_context}

    rect rgb(238,246,255)
    note over Graph,FA: Phase I — Analyst Team (sequential, with tool loops)
    Graph->>MA: invoke
    loop until no tool_calls
        MA->>Tools: tool_calls (get_stock_data, get_indicators)
        Tools->>Vendor: API call
        Vendor-->>Tools: data (fallback to AV on rate-limit)
        Tools-->>MA: ToolMessage
    end
    MA-->>Graph: market_report, then Msg-Clear

    Graph->>SA: invoke (loop tools_social) → sentiment_report
    Graph->>NA: invoke (loop tools_news) → news_report
    Graph->>FA: invoke (loop tools_fundamentals) → fundamentals_report
    end

    rect rgb(255,247,232)
    note over Graph,RM: Phase II — Research Debate (≤ 2·max_debate_rounds turns)
    loop alternating
        Graph->>Bull: respond using 4 reports + bear_history
        Bull-->>Graph: bull_history += turn
        Graph->>Bear: respond using 4 reports + bull_history
        Bear-->>Graph: bear_history += turn
    end
    Graph->>RM: synthesize (deep LLM)
    RM-->>Graph: investment_plan = ResearchPlan(rating, rationale)
    end

    rect rgb(240,253,244)
    note over Graph,Tr: Phase III — Trader
    Graph->>Tr: build proposal (quick LLM)
    Tr-->>Graph: trader_investment_plan = TraderProposal(entry,exit,size)
    end

    rect rgb(253,242,248)
    note over Graph,PM: Phase IV — Risk Debate (≤ 3·max_risk_discuss_rounds turns)
    loop round-robin
        Graph->>Risk: Aggressive turn
        Graph->>Risk: Conservative turn
        Graph->>Risk: Neutral turn
    end
    Graph->>PM: synthesize (deep LLM, with past_context)
    PM-->>Graph: final_trade_decision = PortfolioDecision
    end

    Graph-->>TG: terminal AgentState
    TG->>Sig: extract rating from final_trade_decision
    Sig-->>TG: rating ∈ {Buy,Overweight,Hold,Underweight,Sell}
    TG->>Mem: store_pending(ticker,date,decision)
    Mem->>Mem: resolve prior pending entries (fetch realized return → reflection)
    TG->>FS: write reports/, full_states_log_{date}.json, trading_memory.md
    TG-->>CLI: (final_state, rating)
    CLI-->>User: rendered report + decision
```

---

## 3. Public Integration Surface

A pre-stage stock-filter only needs to call the façade per surviving ticker:

```python
from tradingagents.graph.trading_graph import TradingAgentsGraph

ta = TradingAgentsGraph(
    selected_analysts=["market", "social", "news", "fundamentals"],
    config={
        "llm_provider": "openai",
        "deep_think_llm":  "gpt-...",     # used by Research Mgr & Portfolio Mgr
        "quick_think_llm": "gpt-...mini", # analysts, researchers, trader, risk
        "max_debate_rounds": 2,
        "max_risk_discuss_rounds": 1,
        "data_vendors": {"core_stock_apis": "yfinance"},
        "checkpoint_enabled": True,
    },
)

final_state, rating = ta.propagate(ticker="NVDA", trade_date="2026-05-01")
```

`propagate` is idempotent per `(ticker, date)` when checkpointing is on — safe
to retry. The filter can fan tickers out in parallel processes; each run is
self-contained (state + memory keyed by ticker).

### State fields the filter can read after a run
- `final_trade_decision` — full structured PortfolioDecision
- `investment_plan` — Research Manager's plan (entry candidate)
- `trader_investment_plan` — entry/exit/size
- `market_report`, `sentiment_report`, `news_report`, `fundamentals_report`

### Artifacts on disk (per run)
- `~/.tradingagents/logs/{ticker}/{date}/reports/*.md`
- `~/.tradingagents/logs/{ticker}/TradingAgentsStrategy_logs/full_states_log_{date}.json`
- `~/.tradingagents/memory/trading_memory.md` (rolling, cross-ticker)

Override locations via `TRADINGAGENTS_RESULTS_DIR` and `TRADINGAGENTS_MEMORY_LOG_PATH`.

---

## 4. Rebuild Checklist

1. **State schema** — recreate `AgentState` (messages + reports + two debate sub-states + final decision).
2. **Graph builder** — DAG: 4 analysts (each with tool loop + msg-clear) → bull/bear loop → research mgr → trader → 3-way risk loop → portfolio mgr.
3. **Tool layer** — `route_to_vendor` dispatcher with primary + rate-limit fallback; tool categories: stock, indicators, fundamentals (4 statements), news (3 variants).
4. **LLM layer** — split deep vs quick model; structured-output Pydantic schemas for `ResearchPlan`, `TraderProposal`, `PortfolioDecision`; graceful fallback to free-text when provider lacks structured mode.
5. **Loop control** — counter-based conditional edges: debate ≤ `2·max_debate_rounds`, risk ≤ `3·max_risk_discuss_rounds`.
6. **Signal extraction** — deterministic regex on Portfolio Manager output → 5-tier rating.
7. **Memory** — store-pending → resolve-on-next-run (fetch realized return, generate reflection) → inject top-K same-ticker + cross-ticker lessons into PM prompt.
8. **Persistence** — per-run report dir + serialized full state JSON + checkpoint store for crash resume.
