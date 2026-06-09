# Project Report — Cryptocurrency Market Analysis System

---

| | |
|---|---|
| **Subject** | Advanced Databases |
| **Degree programme** | Automation and Robotics (Master's) |
| **Specialisation** | Computer Science in Control and Management |
| **Authors** | Michał Dusza · Szymon Bugajski · Mateusz Basiura |
| **Date** | May 2026 |

### Related documentation

| File | Purpose |
|------|---------|
| [`README.md`](README.md) | Quick start, repository structure, documentation index |
| [`DOCUMENTATION.md`](DOCUMENTATION.md) | Technical documentation: DDL, SQL, modules |
| [`.docs/`](.docs/) | Concise technical documentation split by topic |
| [`docs/index.html`](docs/index.html) | HTML portal — browse docs in the browser |

---

## Table of contents

1. [Introduction and project objectives](#1-introduction-and-project-objectives)
2. [Functional scope](#2-functional-scope)
3. [Technologies used](#3-technologies-used)
4. [Database design](#4-database-design)
   - 4.1 [Conceptual model (ERD)](#41-conceptual-model-erd)
   - 4.2 [Table descriptions](#42-table-descriptions)
   - 4.3 [Integrity constraints](#43-integrity-constraints)
   - 4.4 [Indexes and query optimisation](#44-indexes-and-query-optimisation)
   - 4.5 [Normalisation](#45-normalisation)
5. [System architecture](#5-system-architecture)
6. [Implementation — data layer](#6-implementation--data-layer)
   - 6.1 [Database initialisation](#61-database-initialisation)
   - 6.2 [Fetching data from the API](#62-fetching-data-from-the-api)
   - 6.3 [Writing and reading data](#63-writing-and-reading-data)
7. [Implementation — presentation layer](#7-implementation--presentation-layer)
   - 7.1 [Jupyter notebook (11 stages)](#71-jupyter-notebook-11-stages)
   - 7.2 [Streamlit web application (6 pages)](#72-streamlit-web-application-6-pages)
8. [Analyses and visualisations](#8-analyses-and-visualisations)
9. [Data collected in the project](#9-data-collected-in-the-project)
10. [Run instructions](#10-run-instructions)
11. [Problems encountered and solutions](#11-problems-encountered-and-solutions)
12. [Conclusions](#12-conclusions)
13. [References and sources](#13-references-and-sources)

---

## 1. Introduction and project objectives

### 1.1 Context

The cryptocurrency market is characterised by exceptionally high volatility and generates vast amounts of data in real time. Monitoring and analysing this data requires reliable storage infrastructure and tools for interactive exploration. The project addresses this need by combining data retrieval via a REST API, relational storage in an SQLite database, and interactive visualisations.

### 1.2 Project objectives

The aim of the project was to design and implement a system that:

1. **Automatically retrieves** historical and current cryptocurrency market data from the public CoinGecko API.
2. **Stores** data in a normalised relational SQLite database with properly defined keys, constraints, and indexes.
3. **Presents** the collected data as interactive statistical visualisations — both in a Jupyter notebook environment and through a browser-based Streamlit web application.

### 1.3 Motivation for the chosen topic

Cryptocurrencies are an excellent use case for time-series-oriented database systems:
- data have a **periodic** character (daily updates),
- they require **idempotent writes** (the same record must not be duplicated on re-fetch),
- statistical analyses (correlations, volatility, distributions) are natural operations on this kind of data.

---

## 2. Functional scope

The project includes the following functionality:

| Module | Functionality |
|--------|---------------|
| **Data acquisition** | Retrieval of 365-day historical data (price, market cap, volume) from the CoinGecko API |
| **Data acquisition** | Retrieval of the current market snapshot (24h high/low, ATH, rank, supply) |
| **Database** | Three relational tables with foreign keys, UNIQUE constraints, and indexes |
| **Time series analysis** | Interactive line chart with filtering by coin, date range, and metric; optional moving average and logarithmic scale |
| **Quantitative analysis** | Bar / box / violin charts with aggregations (mean, max, min, std) for different time horizons |
| **Market dashboard** | KPI cards with prices and changes, summary table, grouped bar chart, change heatmap, market cap treemap |
| **Correlation and volatility analysis** | Matrix of daily return correlations, annualised volatility, 30-day rolling correlation with Bitcoin |

---

## 3. Technologies used

| Component | Technology | Version | Rationale |
|-----------|------------|---------|-----------|
| Programming language | Python | 3.13 | Data-science ecosystem, standard-library support for SQLite |
| Package manager | uv | 0.10.9+ | Fast dependency resolver, isolated `.venv` environment, deterministic `uv.lock` |
| Database | SQLite 3 | stdlib | Zero-configuration, single-file database ideal for local projects; full SQL, foreign key, and index support |
| Data source | CoinGecko API v3 | public | Free access without an API key, rich historical and current data |
| Notebook | JupyterLab | 4.x | Interactive data analysis environment, ipywidgets support |
| Visualisation | Plotly | 6.7 | Interactive, responsive charts; `plotly_dark` template; rich chart library |
| Notebook interactivity | ipywidgets | 8.1 | Native widgets (sliders, dropdowns, date pickers) without an external server |
| Web application | Streamlit | 1.57 | Rapid data-science app development; `@st.cache_data` caching; responsive layout |
| Data manipulation | pandas | 2.2+ | DataFrame as an intermediate layer between SQL and visualisation; `pd.read_sql` |

---

## 4. Database design

### 4.1 Conceptual model (ERD)

```mermaid
erDiagram
    cryptocurrencies {
        TEXT id PK "CoinGecko key, e.g. bitcoin"
        TEXT symbol NOT_NULL "ticker, e.g. BTC"
        TEXT name NOT_NULL "full name, e.g. Bitcoin"
    }

    market_snapshots {
        INTEGER record_id PK "AUTOINCREMENT"
        TEXT crypto_id FK "→ cryptocurrencies.id"
        DATE snapshot_date NOT_NULL "YYYY-MM-DD"
        REAL price_usd "closing price in USD"
        REAL market_cap "market capitalisation in USD"
        REAL total_volume "24h volume in USD"
    }

    market_current {
        INTEGER record_id PK "AUTOINCREMENT"
        TEXT crypto_id FK "→ cryptocurrencies.id"
        DATETIME collected_at NOT_NULL "fetch timestamp UTC"
        REAL price_usd
        REAL market_cap
        REAL total_volume
        REAL high_24h
        REAL low_24h
        REAL price_change_24h
        REAL price_change_percentage_24h
        REAL price_change_percentage_7d
        INTEGER market_cap_rank
        REAL circulating_supply
        REAL total_supply
        REAL max_supply
        REAL ath
        REAL ath_change_percentage
    }

    cryptocurrencies ||--o{ market_snapshots : "has snapshots"
    cryptocurrencies ||--o{ market_current   : "has live snapshots"
```

### 4.2 Table descriptions

#### `cryptocurrencies` — lookup list of tracked coins

Reference (lookup) table containing one record for each tracked cryptocurrency. It serves as the dimension table in a star schema.

| Column | Type | Constraints | Description |
|--------|-----|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | Canonical CoinGecko identifier (lowercase), e.g. `bitcoin` |
| `symbol` | TEXT | NOT NULL | Exchange ticker, e.g. `BTC` |
| `name` | TEXT | NOT NULL | Full display name, e.g. `Bitcoin` |

#### `market_snapshots` — historical daily data

Fact table storing daily price, market capitalisation, and trading volume values. One record = one day for one coin.

| Column | Type | Constraints | Description |
|--------|-----|-------------|-------------|
| `record_id` | INTEGER | PK, AUTOINCREMENT | Surrogate key |
| `crypto_id` | TEXT | NOT NULL, FK | Reference to `cryptocurrencies.id` |
| `snapshot_date` | DATE | NOT NULL | Snapshot date in `YYYY-MM-DD` format (UTC) |
| `price_usd` | REAL | — | Closing price in USD |
| `market_cap` | REAL | — | Total market capitalisation in USD |
| `total_volume` | REAL | — | 24-hour trading volume in USD |

#### `market_current` — current (live) snapshots

Fact table storing rich data from the current market state. Each call to the fetch function adds a new set of rows with the current timestamp — data are not overwritten, creating a history of successive fetches.

| Column | Type | Description |
|--------|-----|-------------|
| `record_id` | INTEGER PK | Surrogate key |
| `crypto_id` | TEXT FK | Reference to `cryptocurrencies.id` |
| `collected_at` | DATETIME | Fetch timestamp (UTC) |
| `price_usd` | REAL | Current price in USD |
| `market_cap` | REAL | Market capitalisation |
| `total_volume` | REAL | 24h volume |
| `high_24h` | REAL | Maximum price within 24h |
| `low_24h` | REAL | Minimum price within 24h |
| `price_change_24h` | REAL | Absolute price change over 24h (USD) |
| `price_change_percentage_24h` | REAL | Percentage price change over 24h |
| `price_change_percentage_7d` | REAL | Percentage price change over 7 days |
| `market_cap_rank` | INTEGER | Global rank by market cap |
| `circulating_supply` | REAL | Coins in circulation |
| `total_supply` | REAL | Total supply |
| `max_supply` | REAL | Maximum possible supply (NULL if unlimited) |
| `ath` | REAL | All-time high (ATH) price in USD |
| `ath_change_percentage` | REAL | Distance from ATH in percent (negative = below ATH) |

### 4.3 Integrity constraints

| Constraint | Table | Definition | Purpose |
|------------|-------|------------|---------|
| PRIMARY KEY | all | `id` or `record_id` | Unambiguous row identification |
| FOREIGN KEY | `market_snapshots` | `crypto_id → cryptocurrencies.id` | No orphan records — every snapshot must have a corresponding coin |
| FOREIGN KEY | `market_current` | `crypto_id → cryptocurrencies.id` | same as above |
| UNIQUE | `market_snapshots` | `(crypto_id, snapshot_date)` | One record per coin per day; enables idempotent `INSERT OR REPLACE` |
| NOT NULL | `market_snapshots` | `crypto_id`, `snapshot_date` | Natural key must always be provided |
| NOT NULL | `market_current` | `crypto_id`, `collected_at` | Identifying key must always be provided |

**Historical data write strategy:**

Using `INSERT OR REPLACE` (SQLite: deletes the conflicting row and inserts a new one) on the `UNIQUE(crypto_id, snapshot_date)` constraint makes re-running data retrieval safe — it does not create duplicates, but only updates values for days that already exist in the database.

```sql
-- Safe for repeated runs:
INSERT OR REPLACE INTO market_snapshots
    (crypto_id, snapshot_date, price_usd, market_cap, total_volume)
VALUES (?, ?, ?, ?, ?);
```

### 4.4 Indexes and query optimisation

The schema uses three indexing mechanisms:

**1. Primary key index (automatic)**  
SQLite automatically creates a B-tree on the `PRIMARY KEY` column of each table. Used when looking up by `record_id`.

**2. Composite index from the UNIQUE constraint**  
The `UNIQUE(crypto_id, snapshot_date)` constraint on `market_snapshots` creates a hidden composite index (`sqlite_autoindex_market_snapshots_1`). This index efficiently supports queries with an equality condition on `crypto_id` AND a date range on `snapshot_date`:

```sql
-- Query plan: SEARCH market_snapshots
-- USING INDEX sqlite_autoindex_market_snapshots_1
-- (crypto_id=? AND snapshot_date>? AND snapshot_date<?)
SELECT snapshot_date, price_usd
FROM market_snapshots
WHERE crypto_id = 'bitcoin'
  AND snapshot_date BETWEEN '2025-01-01' AND '2025-12-31';
```

**3. Explicit additional indexes**

```sql
-- Optimises sorting and filtering by date without a crypto_id condition
CREATE INDEX idx_snapshots_date ON market_snapshots(snapshot_date);

-- Optimises historical queries on market_current by fetch time
CREATE INDEX idx_current_collected_at ON market_current(collected_at);
```

| Index | Table | Columns | Supported query type |
|-------|-------|---------|------------------------|
| PK autoindex | all | `record_id` | Lookup by primary key |
| `sqlite_autoindex_...` | `market_snapshots` | `(crypto_id, snapshot_date)` | Filter by coin + date range |
| `idx_snapshots_date` | `market_snapshots` | `snapshot_date` | Filter by date alone |
| `idx_current_collected_at` | `market_current` | `collected_at` | Filter by fetch time |

### 4.5 Normalisation

The schema satisfies **Third Normal Form (3NF)** requirements:

**1NF (First Normal Form)** — satisfied.  
All column values are atomic (indivisible). No repeating groups or multi-valued attributes.

**2NF (Second Normal Form)** — satisfied.  
Tables `market_snapshots` and `market_current` use surrogate keys (`record_id`), so every attribute depends on the entire key. In `cryptocurrencies`, attributes `symbol` and `name` are fully functionally dependent on `id`.

**3NF (Third Normal Form)** — satisfied.  
No transitive dependencies. Coin metadata (`symbol`, `name`) is stored only in `cryptocurrencies` — fact tables contain only the foreign key `crypto_id`, without duplicating name or symbol. All fact-table attributes depend directly on the primary key.

| Table | 1NF | 2NF | 3NF | Notes |
|-------|:---:|:---:|:---:|-------|
| `cryptocurrencies` | ✅ | ✅ | ✅ | Simple lookup table |
| `market_snapshots` | ✅ | ✅ | ✅ | Fact table; no derived columns |
| `market_current` | ✅ | ✅ | ✅ | Wide fact table; values taken directly from the API |

> Note: columns `price_change_24h` and `price_change_percentage_24h` in `market_current` could technically be computed from `market_snapshots`, but they are stored as raw values from the API (calculated on the CoinGecko server side), not as derived values — this does not violate 3NF.

---

## 5. System architecture

The system is built on a three-layer architecture:

```
┌─────────────────────────────────────────────────────────┐
│                   PRESENTATION LAYER                     │
│                                                         │
│   📓 Jupyter Notebook          🌐 Streamlit Web App     │
│   crypto_market_analysis.ipynb      app.py              │
│   11 stages · ipywidgets        6 pages · Plotly        │
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
│   fetch_market_chart()     fetch_markets_current()      │
│   /coins/{id}/market_chart  /coins/markets              │
│               ↑                        ↑                │
│         CoinGecko Public REST API v3                    │
└─────────────────────────────────────────────────────────┘
```

**Data flow — historical retrieval:**

1. The user initiates retrieval (notebook Stage 5 or a button in Streamlit).
2. For each of the 5 coins, a request is sent: `GET /coins/{id}/market_chart?days=365`.
3. The JSON response contains arrays of `[timestamp_ms, value]` pairs for price, market cap, and volume.
4. The millisecond timestamp is converted to a `YYYY-MM-DD` date (UTC).
5. Rows are written using `INSERT OR REPLACE` into `market_snapshots`.
6. A 10-second delay is applied between successive requests (API rate limit).

**Data flow — current snapshot:**

1. A single request: `GET /coins/markets?ids=bitcoin,ethereum,solana,binancecoin,ripple`.
2. The API returns a list of 5 objects with current market data.
3. Data are inserted into `market_current` with the current UTC timestamp.

---

## 6. Implementation — data layer

### 6.1 Database initialisation

The `create_database()` function is called on every system startup (notebook: Stage 3; Streamlit: `main()`). It uses `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS`, making the operation idempotent — safe for repeated runs:

```python
def create_database() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS market_snapshots (
            record_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            crypto_id     TEXT    NOT NULL,
            snapshot_date DATE    NOT NULL,
            price_usd     REAL,
            market_cap    REAL,
            total_volume  REAL,
            UNIQUE(crypto_id, snapshot_date),
            FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies(id)
        )
    """)
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_snapshots_date "
        "ON market_snapshots(snapshot_date)"
    )
    # … similarly for market_current …
    conn.commit()
    conn.close()
```

### 6.2 Fetching data from the API

```python
def fetch_market_chart(coin_id: str, days: int = 365) -> dict:
    r = requests.get(
        f"{BASE_URL}/coins/{coin_id}/market_chart",
        params={"vs_currency": "usd", "days": days, "interval": "daily"},
        timeout=20,
    )
    r.raise_for_status()   # raises HTTPError on 4xx/5xx codes
    return r.json()
```

API rate limit handling: `time.sleep(REQUEST_DELAY)` = 10 seconds between successive requests. The CoinGecko free tier allows ~10–30 requests/minute; a 10-second delay provides a safe margin.

### 6.3 Writing and reading data

**Historical write (idempotent):**

```python
conn.executemany(
    "INSERT OR REPLACE INTO market_snapshots "
    "(crypto_id, snapshot_date, price_usd, market_cap, total_volume) "
    "VALUES (?,?,?,?,?)",
    rows,          # list of tuples prepared from the API response
)
conn.commit()
```

Using `executemany` with positional parameters (`?`) prevents SQL injection.

**Read into DataFrame:**

```python
@st.cache_data(ttl=60)        # 60 s cache — avoids unnecessary DB queries
def load_snapshots() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT s.snapshot_date, s.price_usd, s.market_cap, s.total_volume,
               c.name, c.symbol
        FROM market_snapshots s
        JOIN cryptocurrencies c ON s.crypto_id = c.id
        ORDER BY s.snapshot_date
    """, conn)
    conn.close()
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
    return df
```

The JOIN eliminates the need for multiple queries — data are fetched once as a denormalised DataFrame, then filtered in memory for interactive analyses.

---

## 7. Implementation — presentation layer

### 7.1 Jupyter notebook (11 stages)

The `crypto_market_analysis.ipynb` notebook is divided into 11 numbered stages, each with a descriptive Markdown cell and code cells:

| Stage | Description | Key elements |
|-------|-------------|--------------|
| 1 | Environment | Documentation of package management via `uv` |
| 2 | Imports and constants | `DB_PATH`, `BASE_URL`, `REQUEST_DELAY=10`, `COINS`, `METRIC_MAP` |
| 3 | DB initialisation | `create_database()` — all `CREATE TABLE / INDEX` |
| 4 | Lookup data | `populate_cryptocurrencies()` + SELECT verification |
| 5 | API functions + fetch loop | `fetch_market_chart`, `store_market_chart`; loop over 5 coins; 1826 rows |
| 6 | DB verification | Row counts, date range, consistency checks |
| 7 | DataFrame loading | `pd.read_sql` with JOIN; type casting |
| 8 | Time series analysis | 6 ipywidgets; Plotly line chart |
| 9 | Quantitative analysis | 6 ipywidgets; bar/box/violin |
| 10 | Market dashboard | `build_dashboard_df()`; 4 Plotly charts |
| 11 | Correlation and volatility | `pct_change()`, `corr()`, annual volatility, 30-day rolling correlation |

**Notebook interactivity** — ipywidgets used:

| Widget | Type | Use |
|--------|-----|-----|
| `SelectMultiple` | Multi-select list | Coin selection for analysis |
| `DatePicker` | Date picker | Date range |
| `Dropdown` | Dropdown | Metric, period, aggregation, chart type |
| `IntSlider` | Slider | Moving average (MA) window |
| `ToggleButton` | Toggle | Logarithmic scale |
| `Output` | Container | Rendering Plotly charts inside `interact()` |

### 7.2 Streamlit web application (6 pages)

The `app.py` application, available at `http://localhost:8501`, offers all notebook analyses in the browser, without requiring a Jupyter environment.

**Navigation:** left sidebar with `st.radio` buttons for switching pages.

#### Page 1: Overview

Displays database metrics (number of coins, daily snapshots, live snapshots) and the date range of available data. Includes a navigation table with descriptions of all pages.

#### Page 2: Data Collection

Two independent buttons trigger retrieval:
- **Historical**: loop over 5 coins with a progress bar; `time.sleep(10)` between requests; `INSERT OR REPLACE`.
- **Live**: single batch request to `/coins/markets`; `INSERT` with UTC timestamp.

After retrieval completes: `load_snapshots.clear()` + `load_db_stats.clear()` + `st.rerun()` — automatic metric refresh.

Below the buttons: SQL summary table of data in the database (`COUNT`, `MIN/MAX/AVG` price per coin).

#### Page 3: Time Series

Sidebar filters:
1. Coin multiselect
2. Start date (date_input)
3. End date (date_input)
4. Metric (price / market cap / volume)
5. MA window (slider 0–30 days)
6. Logarithmic scale (checkbox)

Chart: `px.line` with `hovermode="x unified"` — unified tooltips on the X axis.

#### Page 4: Quantitative Analysis

Sidebar filters:
1. Coin multiselect
2. Metric
3. Period (7 / 30 / 90 / 180 / 365 days)
4. Aggregation (mean / max / min / last / std)
5. Sort order
6. Chart type (Bar / Box / Violin)

#### Page 5: Market Dashboard

- **KPI cards** (`st.metric`): price and 24h change for each coin.
- **Summary table**: price, market cap, volume, 24h/7d/30d changes.
- **Grouped bar chart**: percentage price changes across 3 horizons.
- **Change heatmap**: `px.imshow` on an RdYlGn scale (green = increase, red = decrease).
- **Treemap**: size = market capitalisation; colour = 24h change.

Percentage changes are computed from `market_snapshots` via `build_dashboard_df()` — differences between the latest price and the price 1/7/30 days earlier.

#### Page 6: Correlation & Volatility

- **Pearson correlation matrix** of daily log returns (`pct_change()`).
- **Annualised volatility**: `std(daily_returns) × √365 × 100 [%]`
- **30-day rolling correlation** of each coin with Bitcoin (if BTC is selected).
- **Descriptive statistics** of daily returns (expandable section).

---

## 8. Analyses and visualisations

### 8.1 Time series analysis

The line chart shows the evolution of the selected metric over time. The **moving average** (MA) option smooths short-term noise and reveals trends. A logarithmic scale enables comparison of coins with very different prices (e.g. BTC ~$90,000 vs XRP ~$2).

```python
# MA calculation
filtered[metric_col] = filtered.groupby("name")[metric_col].transform(
    lambda x: x.rolling(ma_window, min_periods=1).mean()
)
```

### 8.2 Quantitative analysis

**Bar chart** — comparison of aggregated values (e.g. average price over the last 90 days).  
**Box plot** — value distribution: median, quartiles, outliers.  
**Violin plot** — same as above + estimated density of the distribution.

### 8.3 Correlation matrix

Pearson correlation is computed on daily returns (not directly on prices), which removes the trend and focuses on co-movement:

```python
price_pivot = df.pivot(index="snapshot_date", columns="name", values="price_usd")
returns     = price_pivot.pct_change().dropna()
corr        = returns.corr()    # n×n Pearson matrix
```

Values close to +1 indicate strong positive correlation (coins move together), close to 0 — no correlation, negative — inverse correlation.

### 8.4 Annualised volatility

Standard measure of financial volatility:

$$\sigma_{annual} = \sigma_{daily} \times \sqrt{365} \times 100\%$$

where $\sigma_{daily}$ is the standard deviation of daily log returns.

---

## 9. Data collected in the project

### Database state after running the project

| Table | Row count | Description |
|-------|-----------|-------------|
| `cryptocurrencies` | 5 | Bitcoin, Ethereum, Solana, BNB, XRP |
| `market_snapshots` | 1,826 | 366 days × 5 coins (one year of history) |
| `market_current` | 10 | 2 live fetches × 5 coins |

### Historical data range

- **First date:** 2025-05-26
- **Last date:** 2026-05-26
- **Total:** 366 days (leap year)

### Tracked cryptocurrencies

| Symbol | Name | Type |
|--------|------|------|
| BTC | Bitcoin | Proof-of-Work, first cryptocurrency |
| ETH | Ethereum | Smart contracts, Proof-of-Stake |
| SOL | Solana | High-throughput PoS |
| BNB | BNB (Binance Coin) | Exchange token |
| XRP | XRP (Ripple) | Payment settlement |

The selection covers the five largest cryptocurrencies by market capitalisation, representing different technologies and use cases.

---

## 10. Run instructions

### Prerequisites

- Python 3.13 (recommended management via `uv`)
- `uv` — installation: `pip install uv` or [docs.astral.sh/uv](https://docs.astral.sh/uv/)
- Internet access (CoinGecko API)

### Step 1 — Navigate to the project directory

```powershell
cd coingeko_project
```

### Step 2 — Install dependencies

```powershell
uv sync
```

Creates `.venv` and installs all packages according to `uv.lock`.

### Step 3a — Run the Jupyter notebook

```powershell
# Register kernel (once only):
uv run python -m ipykernel install --user `
    --name crypto-market-analysis `
    --display-name "Python (crypto-market-analysis)"

# Start JupyterLab:
uv run jupyter lab
```

Open `crypto_market_analysis.ipynb` and select the `Python (crypto-market-analysis)` kernel.  
Run cells from top to bottom (**Run → Run All Cells**).

### Step 3b — Run the Streamlit application

```powershell
uv run streamlit run app.py
```

Application available at: **http://localhost:8501**

On first launch, go to the **📥 Data Collection** page and fetch historical data.

---

## 11. Problems encountered and solutions

| Problem | Cause | Solution applied |
|---------|-------|------------------|
| `ModuleNotFoundError` on kernel start | `pyproject.toml` required Python 3.14, which was not installed | Changed `requires-python = ">=3.14"` to `">=3.13"`; updated `.python-version` |
| HTTP 429 (Too Many Requests) | CoinGecko free tier limit ~10–30 req/min; previous request too close | Increased `REQUEST_DELAY` to 10 s; added retry with delay |
| Empty dashboard (Stage 10) | `market_current` table was empty during analysis; dashboard relied solely on that table | Rebuilt Stage 10 and `build_dashboard_df()` — percentage changes computed from `market_snapshots` (historical data always available) |
| `AttributeError: DataFrame has no attribute 'applymap'` | `applymap` removed in pandas 2.1; replaced by `map` | Changed `.applymap(...)` to `.map(...)` in `app.py` |
| `DeprecationWarning` in `pyproject.toml` | Obsolete `[tool.uv.dev-dependencies]` section | Migrated to new `[dependency-groups]` syntax |
| `KeyboardInterrupt` during `time.sleep(20)` | User interrupted waiting between API requests | Added dedicated retry cell; live data eventually fetched successfully |

---

## 12. Conclusions

### Achievements

1. **Complete end-to-end system**: from raw data retrieval via REST API, through a relational database, to interactive visualisations — in two independent interfaces (Jupyter and Streamlit).

2. **Sound database design**: schema satisfies 3NF, includes foreign keys, a UNIQUE constraint on the natural key `(crypto_id, snapshot_date)`, and indexes supporting the most common queries.

3. **Idempotent data retrieval**: `INSERT OR REPLACE` ensures that re-running the script never duplicates data — it only updates existing rows and adds new ones.

4. **Environment reproducibility**: `uv` + `uv.lock` guarantee an identical environment on every machine.

### Possible extensions

- **Increase the number of monitored coins** — extend the `COINS` list.
- **Automated fetch schedule** — Celery, APScheduler, or a Windows Task Scheduler job calling `uv run python -c "..."`.
- **PostgreSQL instead of SQLite** — for more concurrent users or when data size exceeds several hundred MB.
- **Export to CSV/Excel** — download button in Streamlit (`st.download_button`).
- **Price alerts** — email or webhook alerts when price crosses a defined threshold.

### Final remarks

The project demonstrates that SQLite is fully adequate for local analytical applications at moderate scale — a database with 1,826 rows handles all queries in under 50 ms. Proper index planning (including using the UNIQUE constraint as a composite index) is essential for query performance with date-range filtering.

---

## 13. References and sources

1. **CoinGecko API Documentation** — https://www.coingecko.com/en/api/documentation
2. **SQLite Documentation** — https://www.sqlite.org/docs.html
3. **pandas Documentation** — https://pandas.pydata.org/docs/
4. **Plotly Python Documentation** — https://plotly.com/python/
5. **Streamlit Documentation** — https://docs.streamlit.io/
6. **uv Documentation** — https://docs.astral.sh/uv/
7. **ipywidgets Documentation** — https://ipywidgets.readthedocs.io/
8. E. F. Codd, *A Relational Model of Data for Large Shared Data Banks*, Communications of the ACM, 1970.
9. C. J. Date, *An Introduction to Database Systems*, Addison-Wesley, 8th ed., 2003.
10. W. McKinney, *Python for Data Analysis*, O'Reilly, 3rd ed., 2022.

---

*Report prepared as part of the Advanced Databases course.*  
*Authors: Michał Dusza · Szymon Bugajski · Mateusz Basiura · May 2026*
