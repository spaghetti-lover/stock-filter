"use client";

import { useEffect } from "react";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function FullReportOverlay({ open, onClose }: Props) {
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[60] flex flex-col"
      role="dialog"
      aria-modal="true"
      aria-label="Full analysis report"
      style={{ background: "var(--color-bg)" }}
    >
      <header className="flex items-center justify-between border-b border-[var(--color-line)] bg-[var(--color-surface)] px-6 py-3">
        <div className="flex items-center gap-3">
          <span className="mono text-[10px] uppercase tracking-[0.24em] text-[var(--color-text-faint)]">
            ~/Project/TradingAgents
          </span>
          <span
            aria-hidden
            className="block h-2 w-2"
            style={{ background: "var(--color-ok)", boxShadow: "0 0 10px var(--color-ok)" }}
          />
          <span className="mono text-[11px] uppercase tracking-[0.22em] text-[var(--color-text-dim)]">
            full report · ready
          </span>
        </div>
        <button
          onClick={onClose}
          className="mono border border-[var(--color-line)] px-3 py-1.5 text-[11px] uppercase tracking-[0.2em] text-[var(--color-text-dim)] transition-colors hover:border-[var(--color-accent)] hover:text-[var(--color-accent)]"
        >
          close · esc
        </button>
      </header>

      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto flex max-w-[1100px] flex-col gap-8 px-6 py-10">
          <ReportTitle />

          <SectionDivider label="I. Analyst Team Reports" />
          <AgentBox name="Market Analyst" body={MARKET_ANALYST} />

          <SectionDivider label="II. Research Team Decision" />
          <AgentBox name="Bull Researcher" body={BULL_RESEARCHER} />
          <AgentBox name="Bear Researcher" body={BEAR_RESEARCHER} />
          <AgentBox name="Research Manager" body={RESEARCH_MANAGER} />

          <SectionDivider label="III. Trading Team Plan" />
          <AgentBox name="Trader" body={TRADER} />

          <SectionDivider label="IV. Risk Management Team Decision" />
          <AgentBox name="Aggressive Analyst" body={AGGRESSIVE_ANALYST} />
          <AgentBox name="Conservative Analyst" body={CONSERVATIVE_ANALYST} />
          <AgentBox name="Neutral Analyst" body={NEUTRAL_ANALYST} />

          <SectionDivider label="V. Portfolio Manager Decision" />
          <PortfolioManagerBox body={PORTFOLIO_MANAGER} />
        </div>
      </div>
    </div>
  );
}

function ReportTitle() {
  return (
    <div className="flex items-center gap-4">
      <span aria-hidden className="h-px flex-1 bg-[var(--color-line)]" />
      <span
        className="mono text-[12px] uppercase tracking-[0.28em]"
        style={{ color: "var(--color-text-dim)" }}
      >
        Complete Analysis Report
      </span>
      <span aria-hidden className="h-px flex-1 bg-[var(--color-line)]" />
    </div>
  );
}

function SectionDivider({ label }: { label: string }) {
  return (
    <section className="border border-[var(--color-line)] bg-[var(--color-surface)] px-5 py-3">
      <p
        className="mono text-[12px] uppercase tracking-[0.24em]"
        style={{ color: "var(--color-accent)" }}
      >
        {label}
      </p>
    </section>
  );
}

function AgentBox({ name, body }: { name: string; body: string }) {
  return (
    <section className="relative border border-[var(--color-line)] bg-[var(--color-bg)]">
      <div
        className="pointer-events-none absolute left-6 -top-2 px-2"
        style={{ background: "var(--color-bg)" }}
      >
        <span
          className="mono text-[10px] uppercase tracking-[0.24em]"
          style={{ color: "var(--color-text-dim)" }}
        >
          {name}
        </span>
      </div>
      <pre className="whitespace-pre-wrap px-5 py-5 font-mono text-[12.5px] leading-[1.65] text-[var(--color-text)]">
        {body}
      </pre>
    </section>
  );
}

function PortfolioManagerBox({ body }: { body: string }) {
  return (
    <section
      className="relative border border-[var(--color-accent)] bg-[var(--color-bg)]"
      style={{
        boxShadow:
          "inset 0 0 0 1px color-mix(in srgb, var(--color-accent) 16%, transparent)",
      }}
    >
      <div
        className="pointer-events-none absolute left-6 -top-2 px-2"
        style={{ background: "var(--color-bg)" }}
      >
        <span
          className="mono text-[10px] uppercase tracking-[0.24em]"
          style={{ color: "var(--color-accent)" }}
        >
          Portfolio Manager
        </span>
      </div>
      <pre className="whitespace-pre-wrap px-5 py-6 font-mono text-[12.5px] leading-[1.65] text-[var(--color-text)]">
        {body}
      </pre>
    </section>
  );
}

const MARKET_ANALYST = `All data has been collected. Here is the full, detailed analytical report for SPY as of May 12, 2026:

────────────────────────────────────────────────────────────────────────────
📊 SPY Technical Analysis Report — May 12, 2026
────────────────────────────────────────────────────────────────────────────

1. 🏦 Price Action Overview

SPY started 2026 near $681–693, traded in a tight sideways band through January and February (~$675–$695), then sold off sharply
through March and into early April, bottoming near $631.97 on March 30. From that bottom, SPY launched a powerful, sustained recovery
rally, climbing from ~$632 all the way to $739.30 on May 11 — a gain of nearly +17% in ~6 weeks. The momentum is clearly bullish, but
key overbought signals are now flashing.

────────────────────────────────────────────────────────────────────────────

2. 📈 Moving Averages Analysis

50 SMA (~$684.83 on May 11)
SPY's current price of ~$739.30 is trading ~$54 (or ~7.9%) above its 50-day SMA. The 50 SMA has been rising steadily throughout the
observation window, confirming the medium-term trend is firmly upward. The significant gap between price and the 50 SMA indicates that
price has pulled decisively ahead of its medium-term average — a sign of bullish strength but also potential overextension.

200 SMA (~$671.11 on May 11)
The long-term 200 SMA sits at ~$671, placing SPY approximately ~10.2% above this critical benchmark. Price is not only above the 200
SMA — it is moving higher and the spread is widening. This confirms the broader long-term bull market structure remains intact. There
is no sign of a death cross; the 50 SMA (~$684) is comfortably above the 200 SMA (~$671), forming a bullish golden cross alignment.

10 EMA (~$726.38 on May 11)
The short-term 10 EMA has been climbing rapidly — from ~$668 on April 13 to ~$726 by May 11 — tracking the steep rally very closely.
SPY's last close at $739.30 is ~$12.9 above the 10 EMA, suggesting the short-term trend still has upward momentum, but price is
stretched even from this fast-moving average.

────────────────────────────────────────────────────────────────────────────

3. 📉 MACD & Histogram Analysis

MACD Line (~14.82 on May 11)
The MACD line has been rising nearly continuously from ~1.51 on April 13 to ~14.82 on May 11 — a near 10x increase in just a month.
This is an extraordinary surge in bullish momentum. However, momentum expansion is now slowing: the MACD rose from 14.43 on May 8 to
only 14.82 on May 11, a deceleration compared to earlier weekly gains.

MACD Histogram (~1.49 on May 11)
The histogram tells a cautionary story. After peaking at a high of ~6.51 on April 17, the histogram has been consistently declining —
dropping from 6.51 → 5.10 → 3.80 → 2.57 → 1.48 → 1.49. This divergence between a rising MACD and a falling histogram signals that
bullish momentum is waning. The gap between MACD and its signal line is compressing, which is a classic early warning of a potential
trend slowdown or reversal. This is the most important cautionary signal currently visible.

────────────────────────────────────────────────────────────────────────────

4. 🔢 RSI (~76.14 on May 11)

RSI has been persistently overbought (above 70) since approximately April 17, and has hovered between 67 and 76 for the last four
weeks. The most recent reading of 76.14 is firmly in overbought territory. While RSI can stay overbought for extended periods in
strong bull trends, the fact that it has remained elevated without a meaningful reset heightens the risk of a pullback. RSI has not
broken above 77 convincingly either, suggesting the rally may be losing the ability to extend further without a consolidation phase.

────────────────────────────────────────────────────────────────────────────

5. 📊 Bollinger Bands Analysis

Bollinger Upper Band (~$740.61 on May 11)
SPY closed at $739.30 on May 11, which is just ~$1.31 below the Bollinger Upper Band of ~$740.61. This is an extreme proximity to the
upper band — SPY is effectively testing or riding the upper band. In strong bull trends, price can ride the upper band, but when
combined with the MACD histogram divergence and overbought RSI, this proximity suggests the rally is entering a high-risk zone.

Bollinger Lower Band (~$690.83 on May 11)
The lower band has been rising sharply from ~$621 in mid-April to ~$690 on May 11, reflecting the dramatic narrowing of the downside
cushion as the upper band expands. A potential mean-reversion pullback would target the Bollinger Middle Band (~$715–716) as an
initial support zone.

────────────────────────────────────────────────────────────────────────────

6. ⚡ ATR (Volatility) — ~7.46 on May 11

ATR has been declining steadily from a peak of ~9.87 on April 13 down to ~7.46 on May 11, a ~24% drop in daily volatility. This
indicates the market is calming down after the turbulent March–April volatility. Lower ATR is consistent with a maturing, smoother
rally. For risk management:
  • A 1x ATR stop-loss from current price (~$739) would be set near ~$731.84
  • A 2x ATR stop-loss would target ~$724.38
  • Position sizing should account for current ATR to control daily risk exposure

────────────────────────────────────────────────────────────────────────────

7. 🔍 Key Synthesis & Actionable Insights

✅ Bullish Evidence:
  • Price is above all three moving averages (10 EMA, 50 SMA, 200 SMA) — strongly bullish alignment
  • MACD is positive and rising — trend momentum confirmed
  • Both 50 SMA and 200 SMA are rising — bullish golden cross structure
  • ATR declining — orderly, low-stress uptrend

⚠ Warning Signs / Risk Factors:
  • RSI at 76 — overbought; elevated risk of short-term pullback
  • Price near Bollinger Upper Band ($739.30 vs $740.61) — limited upside headroom
  • MACD Histogram divergence — momentum expansion is clearly fading; histogram down from 6.51 to 1.49
  • Price is 7.9% above 50 SMA and 10.2% above 200 SMA — historically stretched
  • 10 EMA ($726) gap suggests potential for consolidation/reversion

🎯 Trading Scenarios:

  Scenario                Trigger                                             Target
  ───────────────────────────────────────────────────────────────────────────────────────────────────
  Bullish Continuation    Break & close above $741 (Boll UB)                  $750–$755
  Consolidation/Pullback  MACD histogram crosses zero or RSI breaks below 65  $715–$720 (Boll Middle)
  Deeper Correction       Close below 10 EMA ($726)                           $700–$710 (50 SMA zone)

────────────────────────────────────────────────────────────────────────────

📋 Summary Table

  Indicator             Current Value (May 11)  Signal             Interpretation
  ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Price (SPY)           $739.30                 🟢 Bullish         Near YTD high; strong uptrend
  10 EMA                $726.38                 🟢 Bullish         Price well above; short-term trend intact
  50 SMA                $684.83                 🟢 Bullish         Price ~7.9% above; medium-term trend rising
  200 SMA               $671.11                 🟢 Bullish         Price ~10.2% above; golden cross structure
  MACD                  +14.82                  🟢 Bullish         Positive & rising; strong trend momentum
  MACD Histogram        +1.49                   🟡 Caution         Falling sharply from +6.51; momentum waning
  RSI                   76.14                   🔴 Overbought      Above 70 since mid-April; pullback risk elevated
  Bollinger Upper Band  $740.61                 🔴 Caution         Price testing upper band; limited breakout room
  Bollinger Lower Band  $690.83                 🟢 Bullish         Rising LB confirms uptrend structure
  ATR                   7.46                    🟢 Low Volatility  Calming after March turbulence; orderly rally
  Stop Loss (1x ATR)    ~$731.84                ⚙ Risk Mgmt       Short-term stop level
  Stop Loss (2x ATR)    ~$724.38                ⚙ Risk Mgmt       Medium-term stop level

────────────────────────────────────────────────────────────────────────────

🏁 Overall Assessment

SPY is in a strong confirmed uptrend, but is showing multiple signs of being near-term overbought and overstretched. The MACD
histogram's persistent decline is the most important divergence signal — it warns that while the trend is up, the force behind it is
fading. RSI above 76 and price kissing the Bollinger Upper Band reinforce caution for new long entries at current levels.

▌ For existing long positions: Hold with tight stops near $731–$724 (1–2x ATR). Monitor for MACD histogram reversal or RSI drop
▌ below 65 as exit cues.
▌ For new entries: Wait for a pullback to the $715–$720 zone (Bollinger Middle / 10 EMA convergence) for a better risk/reward setup,
▌ rather than chasing at the upper band.

FINAL TRANSACTION PROPOSAL: HOLD`;

const BULL_RESEARCHER = `# 🐂 Bull Case for SPY — May 12, 2026

────────────────────────────────────────────────────────────────────────────

Let me be direct: the trend is your friend, and right now, every major trend indicator is pointing up.

The Core Bull Case Is Simple But Powerful

SPY just delivered a +17% rally in six weeks off the March lows. That's not noise — that's a market making a decisive statement. Price
is trading above the 10 EMA, 50 SMA, AND 200 SMA, all simultaneously rising, in a textbook golden cross alignment. You don't get that
kind of structural confirmation in a market that's about to roll over.

Think about what that March bottom represented — a shakeout, a washout, a moment of maximum fear. And the market responded by
launching one of the cleanest recovery rallies we've seen. That's institutional money stepping in with conviction.

────────────────────────────────────────────────────────────────────────────

Addressing the "Overbought" Concern Head-On

Yes, RSI is at 76. Yes, price is kissing the Bollinger Upper Band. I hear the bears on this. But here's what they're missing:

Overbought in a strong uptrend is not the same as a sell signal. RSI has been above 70 since mid-April — that's nearly a month of
sustained overbought readings. In weak markets, overbought conditions resolve quickly and violently. In strong bull markets, RSI can
ride elevated levels for extended periods because buying pressure simply doesn't relent. The data here is consistent with the latter.

Riding the Bollinger Upper Band? That's actually a sign of trend strength, not exhaustion. In momentum-driven bull moves, price hugs
that upper band like a rail. The bears want to call this a ceiling — I call it a launchpad confirmation.

────────────────────────────────────────────────────────────────────────────

The MACD Histogram — Let's Be Honest About What It's Saying

The bears will point to the histogram declining from 6.51 to 1.49 as their smoking gun. Fair observation, but let's contextualize it
properly.

The MACD line itself is still rising — sitting at +14.82, up from +1.51 just a month ago. The histogram declining simply means the
rate of acceleration is normalizing. That's healthy. No rally sustains parabolic momentum indefinitely. What you want to see in a
healthy uptrend is momentum that moderates and consolidates — not collapses. A histogram moving from 6.51 toward zero while price
continues climbing is called a maturing rally, not a dying one.

The alarm bell rings when the histogram crosses below zero. We're not there. We're at +1.49 with the trend intact.

────────────────────────────────────────────────────────────────────────────

The Bigger Picture: Structure Wins

  • ✅ 50 SMA rising, 200 SMA rising, golden cross confirmed
  • ✅ ATR declining to 7.46 — volatility compressing, rally becoming orderly
  • ✅ Price recovered everything lost in the March selloff and then some
  • ✅ Clean higher-highs, higher-lows structure off the $632 bottom

An orderly, low-volatility rally with all moving averages aligned bullishly is the ideal bull market signature. The bears are looking
at short-term oscillators and missing the forest for the trees.

────────────────────────────────────────────────────────────────────────────

My Bottom Line

The bull case here isn't about chasing — it's about respecting the trend until the trend breaks. Hold your longs with stops at
$724–$731 as your risk management anchor. A pullback to $715–$720 isn't a threat — it's a buying opportunity in a structurally bullish
market.

The bears need the MACD histogram to cross zero, RSI to crack below 65, and price to close below the 10 EMA before they have a real
argument. Until then? The trend belongs to the bulls. 🐂`;

const BEAR_RESEARCHER = `# 🐻 Bear Case for SPY — May 12, 2026

────────────────────────────────────────────────────────────────────────────

I'll give the bull credit for a well-structured argument. But let's call it what it is: a momentum chase dressed up as conviction. And
momentum chases at extremes are exactly how investors get hurt.

────────────────────────────────────────────────────────────────────────────

Let's Talk About What a +17% Rally in Six Weeks Actually Means

The bull wants you to see that move as institutional conviction. I want you to see it for what the data actually shows: a market that
has sprinted so far, so fast, that nearly every short-term indicator is screaming exhaustion.

You're 7.9% above the 50 SMA. You're 10.2% above the 200 SMA. Historically, when SPY stretches this far above its long-term averages,
mean reversion isn't a possibility — it's a gravitational inevitability. The question is never if you revert to the mean. It's when
and how violently.

The bull is celebrating the rally. I'm looking at the price tag of entering it right now at these levels.

────────────────────────────────────────────────────────────────────────────

The RSI Argument Cuts Both Ways — And Not in Your Favor

The bull says "overbought in a strong uptrend isn't a sell signal." Technically accurate. But here's what he glossed over: RSI has
been above 70 for nearly a month and hasn't been able to push meaningfully above 77. That's not sustained strength — that's a rally
that's been trying to extend and failing to do so.

In the strongest bull runs, RSI punches through 80, even 85. We're stalling at 76. That ceiling matters. The buying pressure isn't
relentless — it's fading at the margins, and the RSI is confirming exactly that.

────────────────────────────────────────────────────────────────────────────

The MACD Histogram Is My Smoking Gun — And He Knows It

The bull's rebuttal on the histogram was creative, but let me expose the sleight of hand. He says declining histogram momentum is
"healthy normalization." Fine. But look at the trajectory:

6.51 → 5.10 → 3.80 → 2.57 → 1.48 → 1.49

That's not normalization. That's a near-77% collapse in momentum expansion while price has continued climbing. That divergence —
rising price, collapsing histogram — is one of the most reliable early warning signals in technical analysis. The bull says the alarm
rings when histogram crosses zero. By then, you've already given back significant gains. The smart money reads the divergence before
the zero cross, not after.

And notice what the bull quietly admitted: the MACD line rose only from 14.43 to 14.82 between May 8 and May 11. That's essentially
flat. The engine is running on fumes.

────────────────────────────────────────────────────────────────────────────

That Bollinger Upper Band Isn't a Launchpad — It's a Wall

Price at $739.30 with the upper band at $740.61 — we're talking $1.31 of upside headroom before hitting a statistically significant
resistance level. The bull calls this a launchpad. I call it being pinned to the ceiling with nowhere to go but down.

For a breakout above the Bollinger Upper Band to be meaningful and sustained, you need expanding momentum behind it. What do we have?
Collapsing histogram, stalling RSI, and a MACD line that's gone nearly flat. Those aren't breakout conditions. Those are reversal
setup conditions.

────────────────────────────────────────────────────────────────────────────

The Orderly Rally Narrative Hides the Real Risk

The bull points to declining ATR as proof of an orderly, healthy uptrend. I'd agree — if we were in the middle of the rally. But
declining volatility at the top of a +17% run, pressed against the Bollinger Upper Band is actually a classic setup for a volatility
expansion shock. Markets coil. And when they've coiled this tight, this close to an extreme, the uncoiling tends to be sharp and
sudden.

────────────────────────────────────────────────────────────────────────────

What the Bull Needs You to Ignore

The bull's own stop-loss levels tell the real story. He's anchoring stops at $724–$731 — that's $8–$15 of downside risk from current
price on a position pressed against every short-term resistance level simultaneously. And his "buying opportunity" target of $715–$720
represents a ~2.6% pullback minimum.

So even the bull is quietly pricing in a drawdown. He's just hoping you don't notice he said it.

────────────────────────────────────────────────────────────────────────────

My Bottom Line

I'm not calling for a crash. I'm calling for what the data is plainly showing: a rally that has largely exhausted its near-term fuel.
The risk/reward for new entries at $739 is terrible. The histogram is dying, RSI can't break out, and you're $1 from a statistical
ceiling.

The bull needs you to believe this keeps going straight up. The data needs you to ask: at $739, who's left to buy? 🐻`;

const RESEARCH_MANAGER = `Recommendation: Underweight

Rationale: Both sides made compelling arguments, but the bear's case carried more weight at current entry levels. The bull is right
that the broader trend structure is intact — golden cross confirmed, all major SMAs rising, and the +17% recovery off the March lows
is genuinely impressive institutional-grade price action. Those are not signals to dismiss lightly.

However, the bear landed the stronger punches on the near-term risk/reward question, which is ultimately what matters for a trader
sizing a position today at $739. Here's why the bear wins this round:

  1 MACD histogram divergence is the key tell. The bull tried to frame the 77% collapse in histogram momentum as "healthy
    normalization," but the trajectory — 6.51 → 1.49 over five periods while price continued climbing — is a textbook bearish
    divergence. The bull's own concession that the MACD line went nearly flat between May 8–11 confirms the engine is losing thrust.
    Waiting for a zero-cross to act means giving back meaningful gains.
  2 RSI stalling below 77 is a ceiling, not a consolidation. In the strongest momentum regimes, RSI punches to 80–85. The fact that
    this rally has been unable to break above 77 despite a month of elevated readings suggests fading marginal buying pressure, not
    sustained strength.
  3 Bollinger Band context is critical. With only $1.31 of headroom to the upper band and no expanding momentum to support a sustained
    breakout, the asymmetry is unfavorable: minimal upside before a statistical resistance wall, meaningful downside if the coil
    unwinds.
  4 Even the bull priced in a drawdown. Stop levels at $724–$731 and a "buying opportunity" at $715–$720 implicitly acknowledge 2–3%+
    of near-term downside risk from a position already at extremes. That's a poor entry proposition.

The bear is not calling for a crash, and neither are we. The structural bull trend remains intact. But the near-term risk/reward for
new or incremental exposure at $739 is skewed to the downside. Trim exposure, wait for the pullback the bull himself is expecting, and
re-engage at better levels.

Strategic Actions: Ticker: SPY

Stance: Underweight — Trim Near-Term Exposure, Await Better Entry

  1 Reduce existing long exposure by 20–30% at current levels (~$739). This is not a full exit — the structural bull trend is intact —
    but a tactical reduction to improve the risk/reward profile of the overall position.
  2 Do not initiate new long positions at current levels. The near-term setup (RSI stalling, histogram divergence, Bollinger Band
    ceiling) does not justify fresh capital deployment at $739.
  3 Re-entry target zone: $715–$724. This aligns with the bull's own support levels (10 EMA, lower Bollinger Band range) and represents
    the pullback zone where the risk/reward flips back in the buyer's favor. Scale back in gradually across this range — do not try to
    catch the exact bottom.
  4 Hard stop for remaining longs: $708–$710. A close below this level would signal the pullback is deepening beyond a healthy
    consolidation and would warrant a more aggressive reduction.
  5 Upside invalidation level: $743+. A clean, high-volume breakout and daily close above the Bollinger Upper Band (~$740.61) with
    expanding MACD histogram momentum would invalidate the bear thesis and signal resumption of the primary trend. If this occurs,
    reverse the trim and rebuild to full weight.
  6 Position sizing guidance: Underweight implies holding 50–70% of a full target allocation in SPY. Do not go to zero — the macro
    trend structure does not support a full exit. This is a trim-and-wait strategy, not a capitulation.`;

const TRADER = `Action: Sell

Reasoning: The research plan recommends an underweight stance on SPY at current levels (~$739), driven by three converging technical
warning signals: (1) a sharp MACD histogram collapse (6.51 → 1.49 over five periods) representing textbook bearish divergence even as
price continued higher; (2) RSI stalling below 77 — failing to reach the 80–85 range typical of sustained momentum regimes —
indicating fading marginal buying pressure; and (3) only $1.31 of headroom to the Bollinger Band upper boundary (~$740.61) with no
expanding momentum to support a breakout, creating an asymmetric risk/reward skewed to the downside. While the structural bull trend
(golden cross, rising SMAs, +17% recovery) remains intact and does not warrant a full exit, the near-term entry proposition at $739 is
poor. The plan calls for a tactical trim of 20–30% of existing long exposure to reduce risk, with a re-entry target zone of $715–$724
where risk/reward improves materially.

Entry Price: 739.0

Stop Loss: 708.0

Position Sizing: Reduce existing long exposure by 20–30%; retain 50–70% of full target allocation (do not go to zero). No new long
positions at current levels.

FINAL TRANSACTION PROPOSAL: SELL`;

const AGGRESSIVE_ANALYST = `Alright, let me make the case here because this sell decision is actually the RIGHT aggressive move, and here's
why that might seem counterintuitive but hear me out.

First, nobody has weighed in yet with a conservative or neutral argument, so let me preemptively dismantle the case for holding or
buying more at these levels, because those arguments are coming and they're going to be wrong.

The bulls are going to point to the golden cross, the rising 200 SMA, the MACD still positive at 14.82, and the +17% recovery as
reasons to stay long and strong. And sure, structurally those signals are real. But here's what aggressive trading actually means - it
means recognizing WHEN the edge disappears. And right now at $739, the edge is gone.

Think about what the MACD histogram is screaming at you. It collapsed from 6.51 to 1.49 in five periods while price kept climbing.
That is the definition of a momentum trap. The engine is sputtering even as the car rolls forward on inertia. Anyone who holds here
thinking that positive MACD justifies staying long is confusing the direction of momentum with the strength of it. Those are two
completely different things and conflating them is how you give back gains.

The Bollinger Band situation is not a minor detail either. You have literally $1.31 of upside headroom before hitting the upper band
ceiling, with no expanding volatility to support a breakout. ATR is declining. That means the market is not gearing up for a explosive
move through $741, it's exhausting itself at resistance. The asymmetry here is brutal - you're risking a $15 to $30 pullback to
potentially capture $1.31 of upside. That's not aggressive trading, that's gambling with bad odds.

RSI failing to punch through 77 and reach that 80-85 momentum regime range tells you the buying pressure is actually fading at the
margins. Strong momentum regimes accelerate into overbought territory. This one is stalling. That's your signal.

Now here's the aggressive case for THIS sell decision. Trimming 20-30% here isn't being a coward, it's being a predator. You're
banking gains at the upper band, preserving dry powder, and setting yourself up to re-enter aggressively in the $715-$724 zone where
the risk-reward completely flips in your favor. That re-entry zone represents a potential 2-3% discount with clear technical support
from the Bollinger middle band and 10 EMA convergence. You come back in there with conviction and you're positioned for the next leg
up within a confirmed bull trend.

The traders who will underperform here are the ones who hold at $739 out of fear of missing a breakout to $750, only to ride the
inevitable consolidation back down to $715 and then panic sell at the bottom. Don't be that trader.

The sell is the aggressive play because it maximizes your position for the next high-conviction entry. That is how you compound
aggressively.`;

const CONSERVATIVE_ANALYST = `The Aggressive Analyst and I are actually in strong agreement on the core decision here, and I want to be clear
about why that alignment exists from a pure risk management standpoint, because the reasoning matters even if the conclusion is the
same.

What strikes me most is that the Aggressive Analyst is framing this as a predatory move to maximize re-entry positioning. I see it
differently, and I think the distinction is important for how we manage this going forward. This trim isn't primarily about capturing
a better entry. It's about the fact that we are sitting on nearly 17% of unrealized gains accumulated in six weeks, and the risk
profile of holding that full position at current levels has materially deteriorated. That is a capital preservation argument, not an
opportunistic one.

Here is what concerns me that the Aggressive Analyst glossed over. The stop loss on this position is set at $708, which is $31 below
current price. That represents a potential drawdown of over 4% on whatever exposure we retain. Given that the MACD histogram has now
compressed to 1.49 from 6.51, the probability of that stop being tested has increased meaningfully. We are not in a low-probability
tail risk scenario anymore. A move to the 50 SMA zone near $684 is entirely plausible in a momentum reversal, and that would represent
roughly 7.5% of downside from here. On a large position, that is a very real loss of previously secured gains.

The Aggressive Analyst is comfortable with that risk because he sees a clean re-entry setup. But that assumes the pullback is orderly
and stops at $715 to $724. I would caution that markets do not always deliver textbook retracements. If sentiment shifts and we see a
close below the 10 EMA at $726, the next technical support cluster is near $700 to $710, which is the 50 SMA zone. That is not a
catastrophic outcome but it is well below the re-entry target being cited, and anyone who trimmed expecting to reload at $718 may find
themselves chasing again at $712 or lower.

My conservative endorsement of this trim is straightforward. We protect the gains we have earned, we reduce exposure to a
deteriorating risk-reward setup, and we do so without abandoning the structural bull trend. The 20 to 30 percent reduction is
disciplined and appropriate. Where I would push back on the Aggressive Analyst is the implication that re-entry at $715 to $724 should
be done with conviction and increased sizing. I would say re-entry there should be measured and staged, not aggressive, because if
momentum has genuinely broken down we could easily pass through that zone on the way to $700.

The conservative path here is exactly what the trader proposed. Trim, protect gains, hold the structural position, and wait for
confirmation before adding back. That is sound risk management and I fully support it.`;

const NEUTRAL_ANALYST = `Both analysts have converged on the same conclusion, which is the trim, and I want to push back on how comfortable
everyone seems to be with that consensus, because agreement between the aggressive and conservative camps doesn't automatically make a
position correct. It can just mean both sides are anchoring to the same set of visible signals while missing what those signals don't
tell you.

Let me start with the Aggressive Analyst. The framing of this trim as a predatory setup for re-entry at $715 to $724 is doing a lot of
heavy lifting in that argument, and I don't think it holds up under scrutiny. You're essentially telling the trader to sell now and
buy back cheaper, which sounds elegant, but you're treating a technical re-entry zone as if it's a guaranteed destination. The data
doesn't support that certainty. The Bollinger middle band sits near $715 to $716, yes, but a mean reversion to that level requires the
current momentum to actually break down in a controlled, predictable way. The ATR is at 7.46 and declining. That's actually telling
you the market is calming, not collapsing. A declining ATR in an uptrend is not a bearish signal, it's a sign of trend maturation.
You're reading exhaustion into what might just be consolidation. The predator re-entry thesis requires a pullback that the volatility
environment isn't strongly signaling will happen on the schedule you're expecting.

Now to the Conservative Analyst. I actually have more sympathy for the capital preservation framing, but the argument has a different
problem. You correctly flag that the $708 stop represents 4% drawdown risk on retained exposure, and you're right that pullbacks don't
always stop at textbook support zones. But then you endorse the exact same 20 to 30 percent trim as the aggressive analyst while
adding the caveat that re-entry should be staged and measured. That's not a meaningfully different position, it's just a more anxious
version of the same trade. What you haven't addressed is the cost of being wrong in the other direction. If this is consolidation
rather than reversal, and SPY breaks cleanly above $741, the trader who trimmed 30 percent has given up real upside in a confirmed
bull trend while waiting for a pullback that never arrives. That's not a catastrophic outcome, but it's also not free. Opportunity
cost is a real risk and the conservative framing consistently underweights it.

Here's where I think the balanced view actually adds something neither of them addressed. The most important data point in this entire
report is the one everyone is treating as the ceiling, which is the Bollinger Upper Band at $740.61 with only $1.31 of headroom. Both
analysts treat this as obvious resistance. But the report itself notes that in strong bull trends, price can ride the upper band. And
the structural conditions here, golden cross, all three moving averages rising, MACD still deeply positive at 14.82, are consistent
with exactly that kind of regime. The histogram compression is real and worth respecting, but histogram compression in a strong trend
often precedes consolidation, not reversal. The difference between those two outcomes matters enormously for how aggressively you
should trim.

The moderate position I'd advocate is this. The 20 to 30 percent trim is directionally reasonable but I would anchor it closer to 20
percent rather than 30 percent, and I would set the re-entry trigger not at a price zone but at a confirmed signal, specifically a
MACD histogram that stops declining and turns back up, or an RSI reset to the 65 to 68 range. That way you're not guessing that the
pullback lands at $718. You're responding to what the market actually shows you. The stop at $708 on retained exposure is appropriate
but I'd also want a contingency plan if we break above $741 with expanding volume, because that changes the picture entirely and
neither analyst has a framework for that scenario. The balanced approach keeps you in the trend, respects the warning signals, but
doesn't over-rotate into a defensive stance based on signals that are cautionary rather than conclusive.`;

const PORTFOLIO_MANAGER = `Rating: Underweight

Executive Summary: Tactically reduce SPY long exposure by 20–25% at current levels (~$739), preserving the structural long position
while improving risk/reward. Do not initiate new longs here. Re-entry should be signal-driven — look for MACD histogram stabilization
and upturn or RSI reset to 65–68 — with a price re-entry zone of $715–$724. Hard stop on retained exposure at $708; upside
invalidation on a confirmed high-volume daily close above $741 with expanding histogram momentum.

Investment Thesis: All three analysts converged on a trim, and the weight of evidence supports an Underweight rating — though with
important nuance contributed by the Neutral Analyst that prevents over-rotating into a fully defensive stance.

Why the trim is justified: The Aggressive Analyst correctly identified the MACD histogram collapse (6.51 → 1.49 over five periods) as
the central warning signal. This is not a minor fluctuation — it represents a 77% compression in momentum thrust while price continued
higher, a classic bearish divergence pattern. The Aggressive Analyst's point that "positive MACD" and "strong MACD momentum" are
entirely different things is analytically sound and must not be glossed over. Additionally, with only $1.31 of headroom to the
Bollinger Upper Band (~$740.61) and a declining ATR of 7.46, the asymmetry is unfavorable: negligible statistical upside before
resistance, meaningful downside if the coil unwinds. RSI stalling sub-77 — failing to reach the 80–85 range characteristic of the
strongest momentum regimes — further confirms fading marginal buying pressure.

Why the Conservative Analyst's framing adds discipline: The Conservative Analyst rightly reframes this not as an opportunistic
re-entry setup but as capital preservation on a +17% gain accumulated over six weeks. The $708 stop represents a 4%+ drawdown risk on
retained exposure, and the Conservative Analyst's caution that pullbacks don't always terminate at textbook support ($715–$724) is
well-taken — a close below the 10 EMA at ~$726 opens the door to the 50 SMA zone near $700–$710, well below the Aggressive Analyst's
re-entry target.

Why the Neutral Analyst's pushback prevents over-trimming: The Neutral Analyst made the most underappreciated point in the debate: a
declining ATR in an uptrend signals trend maturation, not necessarily collapse. In strong structural regimes — golden cross confirmed,
all major SMAs rising, MACD still deeply positive at 14.82 — price can ride the Bollinger Upper Band rather than reverse from it.
Histogram compression in strong trends often precedes consolidation, not reversal. This is why the trim should anchor closer to 20%
rather than 30%, and why re-entry should be triggered by confirmed signals (histogram upturn, RSI reset to 65–68) rather than a price
zone that may or may not materialize. The Neutral Analyst also correctly flagged the missing upside scenario: a clean break above $741
on expanding volume invalidates the bear thesis entirely, and a framework for that outcome must be in place.

Synthesis: The structural bull trend in SPY is intact and does not warrant abandonment. However, the near-term risk/reward at $739 is
demonstrably skewed to the downside based on converging technical warnings. A disciplined 20–25% trim — not the full 30% — balances
capital preservation against opportunity cost, keeps the trader in the trend, and creates dry powder for a higher-conviction re-entry
at better levels or on confirmed signal improvement.

Price Target: 724.0

Time Horizon: 2–6 weeks`;
