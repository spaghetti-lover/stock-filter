"""Layer 3 — Multi-agent trading decision pipeline (UI shell, demo data)."""

import os
import time

import streamlit as st


API_BASE = os.environ.get("BACKEND_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Pipeline definition
# ---------------------------------------------------------------------------

PHASES = [
    {
        "key": "analysts",
        "title": "Analyst Team",
        "icon": ":material/groups:",
        "subtitle": "Parallel data gathering across four lenses",
        "agents": [
            {"key": "fundamental", "name": "Fundamental", "icon": ":material/account_balance:",
             "desc": "Company fundamentals & mispricing"},
            {"key": "sentiment", "name": "Sentiment", "icon": ":material/forum:",
             "desc": "Social media & public mood"},
            {"key": "news", "name": "News", "icon": ":material/newspaper:",
             "desc": "Macro headlines & catalysts"},
            {"key": "technical", "name": "Technical", "icon": ":material/show_chart:",
             "desc": "Indicators, trends, chart structure"},
        ],
    },
    {
        "key": "research",
        "title": "Research Debate",
        "icon": ":material/balance:",
        "subtitle": "Bull vs. Bear dialectic, moderated by Research Manager",
        "agents": [
            {"key": "bull", "name": "Bull", "icon": ":material/trending_up:",
             "desc": "Champions upside thesis"},
            {"key": "bear", "name": "Bear", "icon": ":material/trending_down:",
             "desc": "Stress-tests downside risks"},
            {"key": "research_manager", "name": "Manager", "icon": ":material/gavel:",
             "desc": "Synthesizes investment plan"},
        ],
    },
    {
        "key": "trader",
        "title": "Trading",
        "icon": ":material/storefront:",
        "subtitle": "Translates research into a concrete proposal",
        "agents": [
            {"key": "trader", "name": "Trader", "icon": ":material/handshake:",
             "desc": "Sets timing, sizing, action"},
        ],
    },
    {
        "key": "risk",
        "title": "Risk & Approval",
        "icon": ":material/security:",
        "subtitle": "Three risk perspectives reconciled by the Portfolio Manager",
        "agents": [
            {"key": "aggressive", "name": "Aggressive", "icon": ":material/local_fire_department:",
             "desc": "Pushes for higher exposure"},
            {"key": "conservative", "name": "Conservative", "icon": ":material/shield:",
             "desc": "Defends capital preservation"},
            {"key": "neutral", "name": "Neutral", "icon": ":material/scale:",
             "desc": "Mediates between extremes"},
            {"key": "portfolio_manager", "name": "Portfolio Mgr", "icon": ":material/verified_user:",
             "desc": "Final approval & execution"},
        ],
    },
]

VERDICT_STYLES = {
    "BUY":  {"color": "green",  "icon": ":material/arrow_upward:"},
    "HOLD": {"color": "orange", "icon": ":material/pause:"},
    "SELL": {"color": "red",    "icon": ":material/arrow_downward:"},
}

STATUS_BADGE = {
    "pending":  ("gray",  ":material/schedule:",     "Pending"),
    "running":  ("blue",  ":material/autorenew:",    "Running"),
    "done":     ("green", ":material/check_circle:", "Done"),
    "error":    ("red",   ":material/error:",        "Error"),
}


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

def _init_state():
    st.session_state.setdefault("pipeline_run", None)
    st.session_state.setdefault("pipeline_history", [])
    st.session_state.setdefault("selected_phase", 0)


def _new_run(symbol: str, horizon: str) -> dict:
    return {
        "symbol": symbol,
        "horizon": horizon,
        "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "running",
        "agents": {},
        "verdict": None,
    }


def _agent_status(run: dict, key: str) -> str:
    return run["agents"].get(key, {}).get("status", "pending")


def _phase_status(run: dict, phase: dict) -> str:
    statuses = [_agent_status(run, a["key"]) for a in phase["agents"]]
    if any(s == "error" for s in statuses):
        return "error"
    if all(s == "done" for s in statuses):
        return "done"
    if any(s == "running" for s in statuses):
        return "running"
    return "pending"


def _current_phase_index(run: dict) -> int:
    """Index of the first non-done phase, or last phase if all done."""
    for i, phase in enumerate(PHASES):
        if _phase_status(run, phase) != "done":
            return i
    return len(PHASES) - 1


# ---------------------------------------------------------------------------
# Rendering — header & input
# ---------------------------------------------------------------------------

def render_header():
    st.title(":material/smart_toy: Multi-agent trading decision", anchor=False)
    st.caption(
        "Specialized LLM agents collaborate through structured reports and "
        "dialectical debate to recommend BUY / HOLD / SELL on a single ticker."
    )


def render_input_bar() -> tuple[str, str, bool]:
    with st.container(border=True):
        col_sym, col_horizon, col_run = st.columns([2, 2, 1], vertical_alignment="bottom")
        with col_sym:
            symbol = st.text_input(
                "Ticker symbol",
                value=st.session_state.get("agent_symbol", "FPT"),
                placeholder="e.g. FPT, VCB, HPG",
                help="Enter a Vietnamese stock symbol from HOSE / HNX / UPCOM",
            ).strip().upper()
        with col_horizon:
            horizon = st.selectbox(
                "Horizon",
                options=["Intraday", "Swing (1-5d)", "Position (1-4w)"],
                index=1,
            )
        with col_run:
            run_clicked = st.button(
                "Run pipeline",
                type="primary",
                use_container_width=True,
                icon=":material/play_arrow:",
            )
    return symbol, horizon, run_clicked


# ---------------------------------------------------------------------------
# Rendering — stepper
# ---------------------------------------------------------------------------

CIRCLED = ["①", "②", "③", "④"]


def render_stepper(run: dict) -> int:
    """Render the 4-step stepper. Returns the index of the selected phase."""
    cols = st.columns(len(PHASES))
    for i, (col, phase) in enumerate(zip(cols, PHASES)):
        status = _phase_status(run, phase)
        color, icon, label = STATUS_BADGE[status]
        with col:
            with st.container(border=True):
                st.markdown(f"**{CIRCLED[i]} {phase['icon']} {phase['title']}**")
                st.markdown(f":{color}-badge[{icon} {label}]")

    # Selector — defaults to the active phase
    options = list(range(len(PHASES)))
    current = _current_phase_index(run)
    if "phase_pick" not in st.session_state:
        st.session_state["phase_pick"] = current

    selected = st.segmented_control(
        "Inspect phase",
        options=options,
        format_func=lambda i: f"{CIRCLED[i]} {PHASES[i]['title']}",
        default=st.session_state["phase_pick"],
        key="phase_pick_widget",
        label_visibility="collapsed",
    )
    if selected is None:
        selected = current
    st.session_state["phase_pick"] = selected
    return selected


# ---------------------------------------------------------------------------
# Rendering — agent reports
# ---------------------------------------------------------------------------

def render_agent_body(run: dict, agent: dict):
    state = run["agents"].get(agent["key"], {})
    status = state.get("status", "pending")
    color, icon, label = STATUS_BADGE[status]

    head = st.columns([5, 2, 2], vertical_alignment="center")
    with head[0]:
        st.markdown(f"### {agent['icon']} {agent['name']}")
        st.caption(agent["desc"])
    with head[1]:
        st.markdown(f":{color}-badge[{icon} {label}]")
    with head[2]:
        if state.get("duration"):
            st.caption(f":material/timer: {state['duration']:.1f}s")

    st.divider()

    if status == "pending":
        st.info("Waiting for upstream agents to finish...", icon=":material/hourglass_empty:")
    elif status == "running":
        with st.spinner(f"{agent['name']} is reasoning..."):
            time.sleep(0.05)  # cosmetic
    elif status == "error":
        st.error(state.get("error", "Agent failed"), icon=":material/error:")
    else:
        st.markdown(state.get("report", "_No report._"))


def render_phase_panel(run: dict, phase_index: int):
    phase = PHASES[phase_index]
    with st.container(border=True):
        head = st.columns([6, 2], vertical_alignment="center")
        with head[0]:
            st.markdown(f"### {phase['icon']} {phase['title']}")
            st.caption(phase["subtitle"])
        with head[1]:
            color, icon, label = STATUS_BADGE[_phase_status(run, phase)]
            st.markdown(f":{color}-badge[{icon} {label}]")

        agents = phase["agents"]
        if len(agents) == 1:
            render_agent_body(run, agents[0])
        else:
            tabs = st.tabs([f"{a['icon']} {a['name']}" for a in agents])
            for tab, agent in zip(tabs, agents):
                with tab:
                    render_agent_body(run, agent)


# ---------------------------------------------------------------------------
# Rendering — verdict & history
# ---------------------------------------------------------------------------

def render_progress(run: dict):
    total = sum(len(p["agents"]) for p in PHASES)
    done = sum(1 for s in run["agents"].values() if s.get("status") == "done")
    pct = done / total if total else 0
    st.progress(pct, text=f"Pipeline progress — {done}/{total} agents complete")


def render_verdict(run: dict):
    v = run.get("verdict")
    if not v:
        return
    style = VERDICT_STYLES.get(v["action"], VERDICT_STYLES["HOLD"])

    with st.container(border=True):
        st.markdown(f"### {style['icon']} Final decision")
        cols = st.columns([2, 1, 1, 1], vertical_alignment="center")
        with cols[0]:
            st.markdown(f"## :{style['color']}-background[**{v['action']} {run['symbol']}**]")
        with cols[1]:
            st.metric("Confidence", f"{v['confidence']:.0%}", border=True)
        with cols[2]:
            st.metric("Target", v.get("target", "—"), border=True)
        with cols[3]:
            st.metric("Stop", v.get("stop", "—"), border=True)

        st.divider()
        st.markdown("**Rationale**")
        st.markdown(v.get("rationale", "_No rationale provided._"))

        with st.expander("Show structured plan", icon=":material/list_alt:"):
            st.json(v)


def render_sidebar(run: dict | None):
    with st.sidebar:
        st.header("Pipeline", anchor=False)
        if run:
            st.caption(f"**{run['symbol']}** · {run['horizon']}")
            st.caption(f":material/schedule: started {run['started_at']}")
            color, icon, label = STATUS_BADGE[
                "done" if run["status"] == "done" else "running"
            ]
            st.markdown(f":{color}-badge[{icon} {label}]")
            st.divider()

        history = st.session_state.get("pipeline_history", [])
        st.subheader("Recent runs", anchor=False)
        if not history:
            st.caption("No completed runs yet.")
            return
        for item in history[-10:][::-1]:
            v = item.get("verdict") or {}
            action = v.get("action", "—")
            style = VERDICT_STYLES.get(action, {"color": "gray", "icon": ":material/help:"})
            st.markdown(
                f":{style['color']}-badge[{style['icon']} {action}] "
                f"**{item['symbol']}** · {item['started_at'][-8:]}"
            )


# ---------------------------------------------------------------------------
# Demo executor — drives the run client-side until a backend exists.
# ---------------------------------------------------------------------------

DEMO_REPORT_TEMPLATES = {
    "fundamental": (
        "**{symbol}** trades at a P/E discount to sector peers with stable "
        "ROE > 15%. Free cash flow is positive over the trailing 4 quarters.\n\n"
        "- Valuation: cheap on relative basis\n"
        "- Earnings momentum: positive\n"
        "- Balance sheet: low leverage\n"
    ),
    "sentiment": (
        "Retail chatter on **{symbol}** is constructive: positive mention ratio "
        "around 1.8× over the past week, no flagged controversies.\n\n"
        "- Bullish posts: 64%\n"
        "- Bearish posts: 21%\n"
        "- Neutral: 15%\n"
    ),
    "news": (
        "Recent headlines for **{symbol}** lean positive — earnings beat, new "
        "contract announced, sector tailwind from policy update.\n\n"
        "- Catalyst calendar: dividend record date in 2 weeks\n"
        "- Macro: rates stable, FX neutral\n"
    ),
    "technical": (
        "**{symbol}** holds above 20/50-day MAs; RSI at 58 (room to run); MACD "
        "histogram positive and expanding. Volume confirms the breakout.\n\n"
        "- Pattern: cup-with-handle resolved\n"
        "- Support: prior pivot −3%\n"
        "- Resistance: ATH +8%\n"
    ),
    "bull": (
        "I see a clear setup on **{symbol}**: cheap, improving fundamentals, "
        "constructive sentiment, and a confirmed technical breakout. The risk/"
        "reward is asymmetric to the upside.\n"
    ),
    "bear": (
        "Counterpoint: liquidity may dry up at higher levels and a sector "
        "rotation is brewing. **{symbol}** has run quickly — chasing here "
        "exposes us to a pullback.\n"
    ),
    "research_manager": (
        "Synthesizing both views, the bull case prevails on weight of evidence. "
        "Plan: enter on a controlled pullback, half-size first, scale on "
        "confirmation. Invalidation below the 20-day MA.\n"
    ),
    "trader": (
        "**Action: BUY {symbol}**. Initial 1.5% NAV at market; add 1.5% on a "
        "close above prior pivot. Stop 3% below entry. Target +8.5% (1.5R).\n"
    ),
    "aggressive": (
        "Push for full size now — the setup is rare and momentum compounds. "
        "Cut quickly if the thesis breaks.\n"
    ),
    "conservative": (
        "Half-size only. Equity beta is elevated and a single name should not "
        "exceed 3% of NAV regardless of conviction.\n"
    ),
    "neutral": (
        "Stage the entry: 1.5% now, 1.5% on confirmation. This balances "
        "conviction with capital preservation.\n"
    ),
    "portfolio_manager": (
        "Approved: 3% staged entry on **{symbol}**, stop at −3%, target +8.5%. "
        "Logged to the simulated book and flagged for end-of-week review.\n"
    ),
}


def step_demo(run: dict):
    """Advance one agent per call: pending→running→done. Returns True if finished."""
    for phase in PHASES:
        for agent in phase["agents"]:
            state = run["agents"].setdefault(agent["key"], {"status": "pending"})
            if state["status"] in ("done", "error"):
                continue
            if state["status"] == "pending":
                state["status"] = "running"
                return False
            if state["status"] == "running":
                state["status"] = "done"
                tpl = DEMO_REPORT_TEMPLATES.get(agent["key"], "**{symbol}** report.")
                state["report"] = tpl.format(symbol=run["symbol"])
                state["duration"] = 1.2
                return False

    run["verdict"] = {
        "action": "BUY",
        "confidence": 0.72,
        "target": "+8.5%",
        "stop": "-3.0%",
        "size": "3% of NAV",
        "horizon": run["horizon"],
        "rationale": (
            f"Analyst consensus on **{run['symbol']}** is constructive across "
            "fundamentals, sentiment, news, and technicals. The bull thesis "
            "prevailed against the bear's liquidity concern, and the risk team "
            "approved a staged entry sized to 3% of NAV."
        ),
    }
    run["status"] = "done"
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

_init_state()
render_header()

symbol, horizon, run_clicked = render_input_bar()

if run_clicked and symbol:
    st.session_state["pipeline_run"] = _new_run(symbol, horizon)
    st.session_state["agent_symbol"] = symbol
    st.session_state["phase_pick"] = 0  # focus on first phase on a fresh run

run = st.session_state.get("pipeline_run")
render_sidebar(run)

if not run:
    st.info(
        "Enter a ticker and press **Run pipeline** to launch the multi-agent debate.",
        icon=":material/info:",
    )
    st.stop()

st.markdown(f"#### Run for **{run['symbol']}** · {run['horizon']} · started {run['started_at']}")
render_progress(run)

selected_phase = render_stepper(run)
render_phase_panel(run, selected_phase)

if run.get("verdict"):
    st.divider()
    render_verdict(run)

# Demo loop — replace with backend polling later.
if run["status"] == "running":
    finished = step_demo(run)
    if finished and run not in st.session_state["pipeline_history"]:
        st.session_state["pipeline_history"].append(run)
    time.sleep(0.6)
    st.rerun()
