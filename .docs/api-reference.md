# Module API Reference

> Extended reference: [`DOCUMENTATION.md` §6](../DOCUMENTATION.md)  
> Academic report: [`SPRAWOZDANIE.md` §6–7](../SPRAWOZDANIE.md)

---

## Project Modules

| Module | Status | Description |
|--------|--------|-------------|
| **`app.py`** | **main** | Streamlit app — ETL + 6 visualization pages |
| **`crypto_market_analysis.ipynb`** | **main** | Notebook — same DB/API functions in 11 stages |
| `main.py` | legacy | Simple JSON fetcher (3 coins, no DB) |
| `generate_sprawozdanie.py` | tool | DOCX report generator |

---

## `app.py` — Streamlit Application

**File:** `app.py` (847 lines)  
**Run:** `uv run streamlit run app.py`

### Configuration Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `DB_PATH` | `"crypto_market.db"` | Path to SQLite file |
| `BASE_URL` | `"https://api.coingecko.com/api/v3"` | CoinGecko API base URL |
| `REQUEST_DELAY` | `10` | Delay (seconds) between API requests |
| `COINS` | 5-element list | Tracked cryptocurrencies (`id`, `symbol`, `name`) |
| `METRIC_MAP` | dict | Label → DataFrame column mapping |
| `PERIOD_MAP` | dict | Period label → number of days |
| `AGG_MAP` | dict | Aggregation label → pandas function |

### Database Functions

#### `create_database() -> None`

Creates 3 tables and indexes (`CREATE TABLE IF NOT EXISTS`). Seeds coin list (`INSERT OR IGNORE`). Called at app startup in `main()`.

**Side effects:** creates/updates `crypto_market.db`.

---

#### `load_snapshots() -> pd.DataFrame`

Loads full `market_snapshots` JOIN `cryptocurrencies` into a DataFrame.

```sql
SELECT s.snapshot_date, s.price_usd, s.market_cap, s.total_volume,
       c.name, c.symbol
FROM market_snapshots s
JOIN cryptocurrencies c ON s.crypto_id = c.id
ORDER BY s.snapshot_date
```

**Cache:** `@st.cache_data(ttl=60)` — 60 seconds.

---

#### `load_db_stats() -> dict`

Returns a dictionary with DB statistics:
- `cryptocurrencies`, `market_snapshots`, `market_current` — row counts
- `date_from`, `date_to` — date range in `market_snapshots`

**Cache:** `@st.cache_data(ttl=60)`.

---

### API / ETL Functions

#### `fetch_market_chart(coin_id: str, days: int = 365) -> dict`

Fetches historical data from CoinGecko.

```
GET /coins/{coin_id}/market_chart?vs_currency=usd&days=365&interval=daily
```

**Returns:** `{prices: [[ts_ms, value], …], market_caps: [...], total_volumes: [...]}`  
**Exceptions:** `HTTPError`, `Timeout`, `ConnectionError`

---

#### `fetch_markets_current() -> list`

Fetches current market data for all tracked coins.

```
GET /coins/markets?vs_currency=usd&ids=bitcoin,ethereum,solana,binancecoin,ripple&...
```

**Returns:** list of 5 coin dictionaries.

---

#### `store_market_chart(coin_id: str, data: dict) -> int`

Parses API response, converts timestamps to dates, saves to `market_snapshots`.

```python
INSERT OR REPLACE INTO market_snapshots
    (crypto_id, snapshot_date, price_usd, market_cap, total_volume)
VALUES (?, ?, ?, ?, ?)
```

**Returns:** number of rows stored (~366).

---

#### `store_current(data: list) -> None`

Inserts live snapshot into `market_current` with `collected_at = UTC now`.

```python
INSERT INTO market_current (crypto_id, collected_at, price_usd, ...)
VALUES (?, ?, ?, ...)
```

**Effect:** 5 new rows (append-only).

---

### Helper Functions

#### `fmt_pct(x: float) -> str`

Formats a number as `▲ 3.14%` or `▼ 1.23%`. Returns `"N/A"` for NaN.

#### `build_dashboard_df(df: pd.DataFrame) -> pd.DataFrame`

Computes 24h/7d/30d percentage changes from historical snapshots. Returns dashboard-ready DataFrame.

---

### Streamlit Pages

| Function | Page | Description |
|----------|------|-------------|
| `page_overview()` | Overview | DB KPIs, date range, navigation table |
| `page_data_collection()` | Data Collection | Historical and live fetch buttons; DB summary |
| `page_time_series()` | Time Series | Line chart; 6 sidebar filters |
| `page_quantitative()` | Quantitative Analysis | Bar / Box / Violin; 6 filters |
| `page_market_dashboard()` | Market Dashboard | KPI, table, grouped bar, heatmap, treemap |
| `page_correlation()` | Correlation & Volatility | Correlation matrix, volatility, BTC correlation |

#### `main() -> None`

Streamlit entry point. Calls `create_database()`, configures sidebar, routes to selected page.

---

## `main.py` — Legacy JSON Fetcher

> **Status: legacy** — replaced by `app.py`. Kept as reference for the early project stage.

**File:** `main.py` (102 lines)  
**Run:** `uv run python main.py`

### `main() -> None`

Fetches 3 coins (BTC, ETH, SOL) from `/coins/markets` and saves response to `coingecko_response.json`.

**HTTP Parameters:**

| Parameter | Value |
|-----------|-------|
| `vs_currency` | `"usd"` |
| `ids` | `"bitcoin,ethereum,solana"` |
| `price_change_percentage` | `"24h,7d"` |

**Side effects:**
- 1 HTTP GET request (10 s timeout)
- Overwrites `coingecko_response.json`
- Prints HTTP status code and field names to stdout

**Exceptions:** `HTTPError`, `ConnectionError`, `Timeout`, `OSError`

---

## Generating HTML Documentation (pydoc)

```bash
# Legacy main.py module documentation
uv run python -m pydoc -w main
# → main.html

# Preview in browser
uv run python -m pydoc -p 1234
```

Static HTML documentation: [`docs/index.html`](../docs/index.html)

---

*Architecture: [`architecture.md`](architecture.md) · Data model: [`data-model.md`](data-model.md)*
