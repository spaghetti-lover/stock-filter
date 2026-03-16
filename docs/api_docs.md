# API Documentation — Vietnam Stock Filter

## Overview

The frontend requires a single API endpoint to fetch stock list data. Currently implemented as a fake/simulated module (`fake_api.py`); in production this would be an HTTP call to a market data provider.

---

## Endpoints

### `GET /stocks`

Fetch the full list of stocks with their metadata and trading statistics.

**Current implementation:** `fetch_stock_list()` in `frontend/fake_api.py`

#### Request

No parameters required.

#### Response

Returns a JSON array of stock objects.

```json
[
  {
    "symbol": "VCB",
    "exchange": "HOSE",
    "status": "normal",
    "current_price": 90000,
    "gtgd20": 150000000000,
    "history_sessions": 200,
    "today_value": 85000000000,
    "avg_intraday_expected": 72000000000
  },
  ...
]
```

#### Response Fields

| Field                  | Type    | Unit | Description |
|------------------------|---------|------|-------------|
| `symbol`               | string  | —    | Stock ticker symbol (e.g. `"VCB"`) |
| `exchange`             | string  | —    | Exchange the stock is listed on: `"HOSE"`, `"HNX"`, or `"UPCOM"` |
| `status`               | string  | —    | Trading status: `"normal"`, `"warning"`, `"control"`, or `"restriction"` |
| `current_price`        | integer | VND  | Latest closing/current price |
| `gtgd20`               | float   | VND  | Average trading value over the last 20 sessions (GTGD20) |
| `history_sessions`     | integer | sessions | Number of trading sessions of available historical data |
| `today_value`          | float   | VND  | Total trading value so far today |
| `avg_intraday_expected`| float   | VND  | Expected cumulative trading value by the current time of day, based on the 20-session average and intraday time-of-day distribution |

---

## Data Notes

### Trading Status Values

| Value         | Meaning |
|---------------|---------|
| `normal`      | No restrictions |
| `warning`     | Stock under exchange warning |
| `control`     | Stock under exchange control |
| `restriction` | Trading restricted |

### Intraday Expected Value

`avg_intraday_expected` represents how much of the daily average volume (GTGD20) is typically traded by the current time of day. It is computed using a cumulative intraday distribution over Vietnam market hours (09:00–11:30, 13:00–15:00).

Used by the frontend to compute the **intraday activity ratio**:

```
intraday_ratio = today_value / avg_intraday_expected
```

---

## Filter Criteria (Frontend Reference)

The frontend applies the following filters to the stock list returned by the API:

| Filter              | Default        | Description |
|---------------------|----------------|-------------|
| Exchange            | HOSE, HNX      | Only include stocks on selected exchanges |
| Min GTGD20          | 20B VND        | `gtgd20 >= threshold` |
| Trading status      | normal         | `status` must be in allowed set |
| Min history         | 60 sessions    | `history_sessions >= threshold` |
| Min price           | 5,000 VND      | `current_price >= threshold` |
| Min intraday ratio  | 30%            | `today_value / avg_intraday_expected >= threshold` |
| Min volume          | 5M VND         | `today_value >= threshold` |
