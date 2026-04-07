# Feature Roadmap

Portfolio feature plan targeting Qualcomm AI Residency (Engineering & Researcher) and NVIDIA AI internships (NMT, TAO Multi-Modal, BioNemo).

---

## Top 5 Features (Strict Execution Order)

### Feature 1 — Intraday Pattern Model (Replace INTRADAY_CUMULATIVE)

**What:** Train a small model on historical intraday data to learn the cumulative volume distribution curve, replacing the hardcoded array in `backend/infrastructure/stock_repository_impl.py`:

```python
INTRADAY_CUMULATIVE = [0.12, 0.22, 0.30, 0.37, 0.43, 0.48, 0.56, 0.65, 0.75, 0.86, 1.00]
```

Export to ONNX. Benchmark FP32 → FP16 → INT8 → ONNX Runtime.

**Why it's the hidden gem:** The git diff tells the story itself — "deleted hardcoded array, replaced with learned model." No other applicant will have "I replaced a production heuristic with a quantized model benchmarked on real Vietnamese intraday data."

**README benchmark table (target output):**

| Format  | Size (KB) | Latency (ms) | MAE vs actual |
|---------|-----------|--------------|---------------|
| FP32    |           |              |               |
| FP16    |           |              |               |
| INT8    |           |              |               |
| ONNX RT |           |              |               |

**Targets:** Qualcomm Engineering (efficient AI / quantization pipeline), all four roles.

**Implementation:**
- `backend/ml/intraday_model.py` — PyTorch feedforward or 1-layer LSTM
- `backend/ml/quantize.py` — FP32→FP16→INT8 via `torch.quantization`
- `backend/ml/export_onnx.py` — ONNX export + ORT benchmark
- Replace `INTRADAY_CUMULATIVE` in `stock_repository_impl.py` with model inference

---

### Feature 2 — Reusable Quantization + Benchmark Pipeline

**What:** Build `backend/ml/quantization.py` with a `benchmark_model(model, sample_input, export_path)` function that runs the full compression pipeline and outputs a Markdown table. Apply to Feature 1 (intraday model) and Feature 4 (PhoBERT).

**Targets:** Qualcomm Engineering (this is the job description), Qualcomm Research, NVIDIA Engineering.

**Implementation:**
```python
# backend/ml/quantization.py
def benchmark_model(model, sample_input, export_path) -> dict:
    """Returns {format: {size_kb, latency_ms, metric}} for FP32/FP16/INT8/ONNX."""
```
- Wire into CI so benchmark tables auto-update in README

---

### Feature 3 — Price Band Proximity Detector (Trần/Sàn)

**What:** Compute each stock's distance from its daily price ceiling/floor using Vietnam's regulatory limits:
- HOSE: ±7% from reference price
- HNX: ±10%
- UPCOM: ±15%

Display as a color-coded column in Streamlit (red near ceiling, blue near floor). Zero new API calls — exchange and prior close are already fetched.

**Why distinctive:** No Western screener has this concept because Western markets have no daily price limits.

**Targets:** All roles (domain differentiation), strong interview talking point.

**Implementation:**
```python
# backend/ml/price_band.py
def compute_price_band(exchange: str, ref_price: float, current_price: float) -> dict:
    limits = {"HOSE": 0.07, "HNX": 0.10, "UPCOM": 0.15}
    pct = limits[exchange]
    ceiling = round(ref_price * (1 + pct), 1)
    floor   = round(ref_price * (1 - pct), 1)
    proximity = (current_price - ref_price) / (ceiling - ref_price)  # -1 to +1
    return {"ceiling": ceiling, "floor": floor, "proximity": proximity}
```
- Add `ceiling`, `floor`, `band_proximity` fields to the `Stock` entity
- Add color-coded column to Streamlit table

---

### Feature 4 — PhoBERT Vietnamese Financial Sentiment

**What:** Fine-tune `vinai/phobert-base-v2` on Vietnamese financial headlines scraped from CafeF/VnExpress. Use weak labels from same-day price movements (>+2% = positive, <-2% = negative, else neutral). Release the labeled dataset on HuggingFace Hub as `vifinsent` — **no public Vietnamese financial sentiment dataset currently exists**.

**Targets:** NVIDIA NMT intern (Vietnamese NLP), NVIDIA TAO (fine-tuning pipeline), Qualcomm (model to run through Feature 2 quantization pipeline).

**Implementation:**
- Add news scraper for CafeF RSS per symbol
- `backend/ml/sentiment.py` — PhoBERT fine-tuning with HuggingFace `Trainer`
- New API route: `GET /stocks/{symbol}/sentiment`
- Push dataset: `huggingface-cli upload your-username/vifinsent`
- Apply Feature 2 quantization pipeline to the fine-tuned model

**Data strategy:** ~3,000–5,000 weakly labeled headlines is enough for a demo fine-tune.

---

### Feature 5 — Foreign Room Exhaustion Monitor

**What:** Track foreign ownership percentage vs. the Foreign Ownership Limit (FOL) cap under Vietnamese Decree 60/2015 — 49% for most sectors, 30% for banks. Alert when room remaining < 1% or when room dropped >5% in a week (large institutional accumulation signal).

**Why distinctive:** Requires knowing Vietnam's FOL regulatory framework. No equivalent concept exists in US/EU markets.

**Targets:** All roles (deep domain knowledge), Qualcomm Research (market microstructure).

**Implementation:**
- Extend provider to call `stock.ownership.foreign_current_holding()`
- Add `foreign_room` fields to `Stock` entity
- Add "Foreign Room" alert column to Streamlit UI

---

## Coherent Portfolio Narrative

> "I built a production stock filter for the Vietnamese market with Clean Architecture. I found a hand-tuned heuristic in the codebase and replaced it with a trained model — benchmarked through a full FP32→INT8→ONNX quantization pipeline. I applied the same pipeline to a PhoBERT model I fine-tuned on Vietnamese financial headlines — where no dataset existed, so I created and released one on HuggingFace."

**Through-line:** domain data → learned model → efficient deployment → measured results.

---

## What NOT to Build

| Idea | Why to Skip |
|------|------------|
| GNN Forecasting | 3–6 month research project; shallow implementation hurts more than helps |
| Full RAG System | Entire project on its own; "chatbot over docs" is every GenAI applicant |
| Self-Supervised Foundation Model | 16+ weeks; too thin data (700 symbols) to be convincing |
| MLflow + DVC | Overkill for 1–2 models; a Markdown benchmark table beats a 3-run dashboard |
| VN-Index HMM Regime Classifier | Needs years of macro data; output not visually impressive enough |
| Conformal Prediction / Normalizing Flows | Mathematically elegant but Vietnamese data too thin to shine |

---

## Execution Timeline

| Week | Work |
|------|------|
| 1 | Feature 3: Price band proximity (quick win, distinctive UI) |
| 2–3 | Feature 1: Intraday pattern model replaces INTRADAY_CUMULATIVE |
| 3–4 | Feature 2: Quantization pipeline applied to intraday model → README table |
| 5–7 | Feature 4: CafeF scraper + PhoBERT fine-tune + HuggingFace dataset release |
| 7–8 | Feature 2 again: Quantize PhoBERT, add second benchmark table |
| 8 | Feature 5: Foreign room monitor |
| 9 | Polish README with all benchmark tables + record 2-min demo video |

**Start applying after Week 4** — intraday model + quantization benchmark is sufficient for the Qualcomm Engineering Residency application.
