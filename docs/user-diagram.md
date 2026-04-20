# System Architecture Diagrams

## Overview

This document shows the data flow for the 3 main components: **Daily Crawl**, **Layer 1 Filtering**, **Layer 2 Scoring**, and how the **Scheduler** orchestrates them.

---

## 1. Daily Crawl (Scheduled 16:00 VN time)

```mermaid
sequenceDiagram
    participant Sched as APScheduler
    participant Crawl as CrawlUseCase
    participant Repo as CrawlRepositoryImpl
    participant DB as PostgreSQL
    participant VN as vnstock API

    Note over Sched: Daily at 16:00 Asia/Ho_Chi_Minh

    Sched->>Crawl: execute()
    Crawl->>DB: log_crawl_start() → crawl_id

    Crawl->>Repo: crawl_all_stocks()
    Repo->>VN: list_by_exchange() (HOSE, HNX)
    VN-->>Repo: all symbols

    loop For each symbol (concurrent)
        Repo->>VN: ohlcv(symbol, 100d)
        Repo->>VN: intraday(symbol)
        VN-->>Repo: history + ticks
        Repo->>Repo: compute metrics (gtgd20, cv, intraday_ratio...)
    end

    Repo-->>Crawl: Stock[] with computed metrics
    Crawl->>DB: save_stocks() → stock_metrics (all passed=FALSE)
    Crawl->>DB: log_crawl_success(crawl_id, total)

    Note over DB: stock_metrics table refreshed daily
```

---

## 2. Layer 1 — Stock Filtering

```mermaid
sequenceDiagram
    actor User
    participant FE as Streamlit Frontend
    participant API as FastAPI Backend
    participant L1 as Layer1UseCase
    participant Filter as StockFilterService
    participant RepoDB as Layer1StockRepositoryDB
    participant DB as PostgreSQL

    User->>FE: Open Layer 1 page
    FE->>API: GET /layer1?exchanges=HOSE,HNX&min_gtgd=5

    API->>L1: execute(exchanges, min_gtgd, ...)

    L1->>L1: Check market regime (VN-Index gate)
    L1->>RepoDB: list_stocks()
    RepoDB->>DB: SELECT * FROM stock_metrics WHERE exchange IN (...)
    DB-->>RepoDB: Stock rows
    RepoDB-->>L1: (stocks[], early_rejected[])

    L1->>Filter: apply_filters(stocks, rules...)
    Note over Filter: Rules: exchange, GTGD20, status,<br/>history_sessions, price_floor,<br/>intraday_ratio, volume, CV,<br/>ceiling/floor exclusion

    Filter-->>L1: (passed[], rejected[])

    L1->>DB: UPDATE stock_metrics SET passed=TRUE WHERE symbol IN (passed)

    L1-->>API: FilteredStocksResponse
    API-->>FE: {passed: [...], rejected: [...], market_regime: {...}}
    FE-->>User: Display passed/rejected tables + market regime
```

---

## 3. Layer 2 — Buy Score (Auto-refresh every 5 minutes)

```mermaid
sequenceDiagram
    actor User
    participant FE as Streamlit Frontend
    participant API as FastAPI Backend
    participant Sched as APScheduler
    participant L2 as Layer2UseCase
    participant Repo as Layer2ScoreRepositoryDB
    participant DB as PostgreSQL
    participant VN as vnstock API

    Note over Sched: Every 5 minutes (*/5), coalesce=True, max_instances=1

    loop Every 5 minutes
        Sched->>L2: execute(refresh=True)
        L2->>Repo: get_passed_symbols()
        Repo->>DB: SELECT symbol, exchange FROM stock_metrics WHERE passed=TRUE
        DB-->>Repo: passed symbols

        alt No passed symbols
            L2-->>Sched: Skip (log warning: "No Layer 1 data")
        else Symbols found
            L2->>VN: get_vnindex_history(100 sessions)
            VN-->>L2: VN-Index OHLCV

            loop For each passed symbol (Semaphore concurrency)
                L2->>VN: ohlcv(symbol, 100d)
                L2->>VN: intraday(symbol)
                VN-->>L2: history + intraday ticks
                L2->>L2: cal_buy_score(history, intraday, vnindex, minutes_elapsed)
                Note over L2: Score = 0.35×Liquidity + 0.30×Momentum + 0.35×Breakout
            end

            L2->>Repo: save_scores(scores)
            Repo->>DB: TRUNCATE layer2_scores
            Repo->>DB: INSERT scores + scored_at = NOW()
        end
    end

    Note over FE: User opens page or FE auto-polls after countdown

    User->>FE: Open Layer 2 page
    FE->>API: GET /layer2/latest
    API->>DB: SELECT * FROM layer2_scores
    DB-->>API: scores[], scored_at

    API-->>FE: {scores: [...], scored_at, next_refresh_in}
    FE-->>User: Display score table + countdown "Next refresh in Xm"

    Note over FE: After next_refresh_in seconds, FE re-polls API
```

---

## 4. Scheduler Overview

```mermaid
graph TD
    subgraph APScheduler
        A[Daily Crawl Job<br/>CronTrigger 16:00 VN] -->|calls| B[CrawlUseCase.execute]
        C[Layer2 Refresh Job<br/>CronTrigger */5 min] -->|calls| D[Layer2UseCase.execute<br/>refresh=True]
    end

    B --> E[vnstock API<br/>fetch all symbols + metrics]
    E --> F[(stock_metrics table<br/>passed=FALSE)]

    F -->|Layer 1 filters set passed=TRUE| G[Layer 1 passed symbols]
    G --> D

    D --> H[vnstock API<br/>history + intraday per symbol]
    H --> I[cal_buy_score<br/>Liquidity / Momentum / Breakout]
    I --> J[(layer2_scores table)]

    J -->|GET /layer2/latest| K[Streamlit Frontend]
    F -->|GET /layer1| K
```

---

## 5. Score Breakdown (Layer 2)

```mermaid
graph LR
    subgraph "BUY Score (0-100)"
        A[Liquidity<br/>35%] --> FINAL[Final Score]
        B[Momentum<br/>30%] --> FINAL
        C[Breakout<br/>35%] --> FINAL
    end

    subgraph Liquidity
        A1[GTGD20 Score 55%]
        A2[Intraday Activity 30%]
        A3[CV Stability 15%]
    end

    subgraph Momentum
        B1[Price Volatility 30%]
        B2[Moving Average 20%]
        B3[Relative Strength 20%]
        B4[Accumulation/Distribution 15%]
        B5[Technical Confirmation 15%]
    end

    subgraph Breakout
        C1[Price Breakout 30%]
        C2[Volume Confirmation 25%]
        C3[Volume Dry-up 20%]
        C4[Base Quality 15%]
        C5[Holding Ratio 10%]
    end

    A1 & A2 & A3 --> A
    B1 & B2 & B3 & B4 & B5 --> B
    C1 & C2 & C3 & C4 & C5 --> C
```
