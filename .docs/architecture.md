# System Architecture

> Full academic description: [`SPRAWOZDANIE.md` §5](../SPRAWOZDANIE.md)  
> Extended technical reference: [`DOCUMENTATION.md` §1](../DOCUMENTATION.md)

---

## Overview

The Cryptocurrency Market Analysis System is a complete end-to-end application that:

1. **Fetches** historical and live data from CoinGecko REST API v3.
2. **Stores** it in a normalised SQLite database (`crypto_market.db`).
3. **Presents** it in interactive Plotly visualizations — via Streamlit (`app.py`) or Jupyter (`crypto_market_analysis.ipynb`).

---

## 3-Tier Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                     │
│                                                         │
│   📓 crypto_market_analysis.ipynb    🌐 app.py          │
│   11 stages · ipywidgets             6 Streamlit pages  │
│   Plotly charts                      Plotly charts       │
└──────────────────────┬──────────────────────────────────┘
                       │ pd.read_sql (SELECT + JOIN)
┌──────────────────────▼──────────────────────────────────┐
│                   STORAGE LAYER                          │
│                                                         │
│         🗄️  SQLite 3 — crypto_market.db                 │
│         cryptocurrencies | market_snapshots              │
│         market_current                                  │
└──────────────────────┬──────────────────────────────────┘
                       │ INSERT OR REPLACE / INSERT
┌──────────────────────▼──────────────────────────────────┐
│                   DATA ACQUISITION LAYER                 │
│                                                         │
│   fetch_market_chart()        fetch_markets_current()   │
│   /coins/{id}/market_chart    /coins/markets            │
│               ↑                        ↑                │
│         CoinGecko Public REST API v3                    │
└─────────────────────────────────────────────────────────┘
```

---

## Components

### `app.py` — main application (Streamlit)

**Responsibilities:**
- Database initialisation (`create_database()`)
- API data fetching (`fetch_market_chart`, `fetch_markets_current`)
- SQLite writes (`store_market_chart`, `store_current`)
- Data reads and caching (`load_snapshots`, `load_db_stats`)
- 6 visualization pages (Overview, Data Collection, Time Series, Quantitative, Dashboard, Correlation)

**Run:** `uv run streamlit run app.py` → `http://localhost:8501`

### `crypto_market_analysis.ipynb` — analytical notebook

**Responsibilities:**
- Same DB/API functions as `app.py` (duplicated in cells)
- 11 stages: from DDL through ETL to ipywidgets visualizations
- Data exploration without a web server

**Run:** `uv run jupyter lab crypto_market_analysis.ipynb`

### `crypto_market.db` — SQLite database

- Created automatically on first run of `app.py` or the notebook (Stage 3)
- 3 tables, foreign keys, UNIQUE constraint, 2 explicit indexes
- Binary file in the project directory

### Legacy files

| File | Role |
|------|------|
| `main.py` | Simple fetcher: 3 coins → `coingecko_response.json` (no DB) |
| `test.ipynb` | Exploratory API response inspection |
| `coingecko_response.json` | Sample `/coins/markets` response |

---

## Data Flow

### Historical fetch

| Step | Component | Action |
|------|-----------|--------|
| 1 | UI (Streamlit / notebook) | User initiates fetch |
| 2 | `fetch_market_chart(coin_id, days=365)` | `GET /coins/{id}/market_chart` |
| 3 | API | Returns `{prices, market_caps, total_volumes}` as `[ts_ms, value]` arrays |
| 4 | `store_market_chart()` | Converts `ts_ms` → `YYYY-MM-DD` (UTC) |
| 5 | SQLite | `INSERT OR REPLACE INTO market_snapshots` (bulk `executemany`) |
| 6 | `time.sleep(10)` | Delay between coins (rate limit) |
| 7 | Repeat | For each of 5 coins |

### Live snapshot fetch

| Step | Component | Action |
|------|-----------|--------|
| 1 | `fetch_markets_current()` | `GET /coins/markets?ids=bitcoin,ethereum,solana,binancecoin,ripple` |
| 2 | API | Returns list of 5 live coin objects |
| 3 | `store_current()` | `INSERT INTO market_current` with `collected_at = UTC now` |

### Read for visualization

| Step | Component | Action |
|------|-----------|--------|
| 1 | `load_snapshots()` | `SELECT … FROM market_snapshots JOIN cryptocurrencies` |
| 2 | pandas | `pd.read_sql` → DataFrame |
| 3 | Plotly | Filter, aggregate, render chart |

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **SQLite** | Zero configuration, single file, full SQL + FK + indexes — ideal for local projects |
| **INSERT OR REPLACE** | Idempotent historical writes — re-fetching never duplicates rows |
| **`executemany` + `?`** | Parameterised queries — SQL injection protection |
| **`@st.cache_data(ttl=60)`** | Streamlit DB read cache — fewer queries on navigation |
| **`uv run`** | Automatic `.venv` usage without manual activation |
| **ETL / UI separation** | Notebook and Streamlit read from the same DB — independent layers |

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Language | Python 3.13 |
| Packages | uv (`pyproject.toml` + `uv.lock`) |
| HTTP | requests 2.33+ |
| Database | sqlite3 (stdlib) |
| Data | pandas 2.2+ |
| Charts | Plotly 6.7+ |
| Web UI | Streamlit 1.57+ |
| Notebook | JupyterLab 4 + ipywidgets 8.1+ |
| API | CoinGecko v3 (public, no API key) |

---

## Error Handling

| Situation | Mechanism | Result |
|-----------|-----------|--------|
| HTTP 4xx/5xx | `response.raise_for_status()` | `HTTPError` — message in UI |
| HTTP 429 (rate limit) | UI layer handling | "Try again shortly" message |
| Timeout (>20s) | `timeout=20` in `requests.get` | `Timeout` exception |
| No network | `ConnectionError` | Error in Streamlit / traceback in notebook |
| Empty database | UI check | Analysis pages show "no data" message |

---

## Limitations

1. **API rate limit** — 10 s delay between requests; full historical fetch takes ~50 s.
2. **Local database** — SQLite does not support concurrent writes from multiple processes.
3. **No scheduling** — data fetched manually (UI button or notebook re-run).
4. **5 hardcoded coins** — `COINS` list in `app.py` and notebook.
5. **No authentication** — Streamlit app available locally without login.

---

*Diagrams: [`diagrams.md`](diagrams.md) · DB schema: [`data-model.md`](data-model.md)*
