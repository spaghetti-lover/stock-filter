"""Layer 3 — Multi-agent trading decision pipeline."""

import os
import time

import requests
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


def _start_run(symbol: str, horizon: str, provider: str = "claude") -> dict | None:
    try:
        resp = requests.post(
            f"{API_BASE}/trading-agent/run",
            json={"symbol": symbol, "horizon": horizon, "provider": provider},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        st.error(f"Failed to start pipeline: {exc}", icon=":material/error:")
        return None
    return _fetch_run(resp.json()["run_id"])


def _fetch_run(run_id: str) -> dict | None:
    try:
        resp = requests.get(f"{API_BASE}/trading-agent/status/{run_id}", timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        st.error(f"Failed to fetch run status: {exc}", icon=":material/error:")
        return None
    return resp.json()


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
# Main
# ---------------------------------------------------------------------------

_init_state()
render_header()

symbol, horizon, run_clicked = render_input_bar()

if run_clicked and symbol:
    started = _start_run(symbol, horizon)
    if started is not None:
        st.session_state["pipeline_run"] = started
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

if run["status"] == "running":
    time.sleep(1.0)
    refreshed = _fetch_run(run["run_id"])
    if refreshed is not None:
        st.session_state["pipeline_run"] = refreshed
    st.rerun()
elif run["status"] in ("done", "error") and not any(
    h.get("run_id") == run.get("run_id") for h in st.session_state["pipeline_history"]
):
    st.session_state["pipeline_history"].append(run)
    if run["status"] == "error" and run.get("error"):
        st.error(f"Pipeline failed: {run['error']}", icon=":material/error:")
