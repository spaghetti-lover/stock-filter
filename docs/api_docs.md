# API Documentation — Vietnam Stock Filter

## Overview

The backend exposes a FastAPI server at `http://localhost:8000`. All data is fetched live from the vnstock API — no database is used.

---

## Endpoints

### `GET /stocks`

Fetch the full filtered list of stocks with trading statistics.

#### Query Parameters

| Parameter           | Type             | Default              | Description |
|---------------------|------------------|----------------------|-------------|
| `exchanges`         | list[str]        | HOSE, HNX, UPCOM     | Exchanges to include |
| `min_gtgd`          | float            | 0.0                  | Minimum GTGD20 in VND |
| `statuses`          | list[str] \| null | null                 | Allowed trading statuses |
| `min_history`       | int              | 0                    | Minimum history sessions |
| `min_price`         | float            | 0.0                  | Minimum price in VND |
| `min_intraday_ratio`| float            | 0.0                  | Minimum intraday activity ratio (0–1) |
| `min_volume`        | float            | 0.0                  | Minimum today's trading value in VND |
| `use_exchange`      | bool             | true                 | Toggle exchange filter |
| `use_gtgd20`        | bool             | true                 | Toggle GTGD20 filter |
| `use_status`        | bool             | true                 | Toggle status filter |
| `use_history`       | bool             | true                 | Toggle history filter |
| `use_price`         | bool             | true                 | Toggle price filter |
| `use_intraday`      | bool             | true                 | Toggle intraday ratio filter |
| `use_volume`        | bool             | true                 | Toggle volume filter |

#### Response

```json
{
  "passed": [...],
  "rejected": [...]
}
```

Each stock object:

```json
{
  "symbol": "VCB",
  "exchange": "HOSE",
  "status": "normal",
  "price": 90.0,
  "gtgd20": 150000000000,
  "history_sessions": 200,
  "today_value": 85000000000,
  "avg_intraday_expected": 72000000000,
  "intraday_ratio": 1.18
}
```

#### Response Fields

| Field                   | Type    | Unit     | Description |
|-------------------------|---------|----------|-------------|
| `symbol`                | string  | —        | Stock ticker (e.g. `"VCB"`) |
| `exchange`              | string  | —        | `"HOSE"`, `"HNX"`, or `"UPCOM"` |
| `status`                | string  | —        | Trading status: `"normal"`, `"warning"`, `"control"`, `"restriction"` |
| `price`                 | float   | thousand VND | Latest closing price |
| `gtgd20`                | float   | VND      | Average trading value over last 20 sessions |
| `history_sessions`      | int     | sessions | Number of available trading sessions |
| `today_value`           | float   | VND      | Total trading value today (from intraday ticks) |
| `avg_intraday_expected` | float   | VND      | Expected value by current time of day based on GTGD20 |
| `intraday_ratio`        | float \| null | — | `today_value / avg_intraday_expected`; null before market open |

---

### `GET /stocks/stream`

Same parameters as `GET /stocks`. Returns a Server-Sent Events stream.

**Event types:**

```
data: {"type": "progress", "processed": 10, "total": 700, "symbol": "VCB"}
data: {"type": "result", "data": {"passed": [...], "rejected": [...]}}
data: {"type": "error", "detail": "..."}
```

---

### `POST /chat`

Send a message to an AI agent with access to live stock data tools.

#### Request Body

```json
{
  "message": "What is the current price of VCB?",
  "history": [],
  "provider": "claude"
}
```

| Field      | Type   | Default   | Description |
|------------|--------|-----------|-------------|
| `message`  | string | required  | User message |
| `history`  | list   | `[]`      | Prior conversation turns `[{"role": "user/assistant", "content": "..."}]` |
| `provider` | string | `"claude"`| LLM provider: `"claude"`, `"gemini"`, or `"openai"` |

#### Response

```json
{
  "response": "VCB is currently trading at 90.0 thousand VND..."
}
```

---

## Filter Criteria (Frontend Reference)

| Filter              | Default     | Description |
|---------------------|-------------|-------------|
| Exchange            | HOSE, HNX   | Only include stocks on selected exchanges |
| Min GTGD20          | 20B VND     | `gtgd20 >= threshold` |
| Trading status      | normal      | `status` must be in allowed set |
| Min history         | 60 sessions | `history_sessions >= threshold` |
| Min price           | 5,000 VND   | `price >= threshold` |
| Min intraday ratio  | 30%         | `today_value / avg_intraday_expected >= threshold` |
| Min volume          | 5M VND      | `today_value >= threshold` |

---

## Intraday Expected Value

`avg_intraday_expected` is computed from `GTGD20 × cumulative_fraction(current_time)` using a hardcoded intraday distribution over Vietnam market hours (09:00–11:30, 13:00–15:00):

```python
INTRADAY_TIME_SLOTS  = [(9,0),(9,30),(10,0),(10,30),(11,0),(11,30),(13,0),(13,30),(14,0),(14,30),(15,0)]
INTRADAY_CUMULATIVE  = [0.12, 0.22, 0.30,  0.37,  0.43,  0.48,  0.56,  0.65,  0.75,  0.86,  1.00]
```
