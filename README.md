# 🪙 Cryptocurrency Market Analysis System

> **Advanced Databases – Final Project**  
> Automatyka i Robotyka II Stopnia · Informatyka w Sterowaniu i Zarządzaniu

**Team:** Michał Dusza · Szymon Bugajski · Mateusz Basiura

---

## Overview

A system that **automatically collects** cryptocurrency market data from the [CoinGecko REST API](https://www.coingecko.com/en/api), **stores it in a relational SQLite database**, and presents the collected data through **interactive statistical visualisations** inside a Jupyter Notebook.

### Analysis types implemented

| Type | Charts | Filters |
|------|--------|---------|
| **Time Series** | Line chart with optional moving average | 6 (coin, start date, end date, metric, MA window, log scale) |
| **Quantitative Analysis** | Bar chart / Box plot / Violin plot | 6 (coin, metric, period, aggregation, sort order, chart type) |
| **Market Overview** | Summary table · Grouped bar · Heatmap · Treemap | — |
| **Correlation & Volatility** | Correlation matrix · Annualised volatility bar | — |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.13 |
| Package manager | [uv](https://docs.astral.sh/uv/) |
| Database | SQLite 3 (file: `crypto_market.db`) |
| Data source | CoinGecko Public API v3 |
| Notebook | JupyterLab / Jupyter Notebook |
| Visualisation | Plotly 6, ipywidgets 8 |
| Data manipulation | pandas 3, numpy |

---

## Project Structure

```
coingeko_project/
├── crypto_market_analysis.ipynb   ← main notebook (all stages)
├── crypto_market.db               ← SQLite database (auto-created on first run)
├── pyproject.toml                 ← dependencies managed by uv
├── uv.lock                        ← locked dependency versions
├── .python-version                ← pinned Python 3.13
├── main.py                        ← standalone data-fetch script (reference)
└── README.md
```

---

## Quick Start (uv)

### 1 · Clone / open the project

```powershell
cd coingeko_project
```

### 2 · Install all dependencies

```powershell
uv sync
```

This creates a `.venv` folder and installs all packages declared in `pyproject.toml`
(pandas, plotly, ipywidgets, jupyter, requests, …).

### 3 · Register the Jupyter kernel *(first time only)*

```powershell
uv run python -m ipykernel install --user `
    --name crypto-market-analysis `
    --display-name "Python (crypto-market-analysis)"
```

### 4 · Launch JupyterLab

```powershell
uv run jupyter lab
```

Open `crypto_market_analysis.ipynb` and select the
**`Python (crypto-market-analysis)`** kernel (or the auto-detected `.venv`).

### 5 · Run the notebook

Execute cells top-to-bottom (**Run → Run All Cells**).  
Stage 5 fetches data from the API (~40 s due to rate-limit delays).  
All subsequent stages work entirely from the local database.

> **VS Code users:** open the `.ipynb` file directly. VS Code auto-detects the
> `.venv` created by `uv sync` and offers it as the kernel.

---

## Streamlit Web Application

As an alternative to the notebook, the project includes a fully interactive **Streamlit app** (`app.py`) that exposes all analyses through a web UI.

### Launch the app

```powershell
uv run streamlit run app.py
```

`uv run` automatically uses the project's `.venv` — no manual activation needed.  
The app opens in your default browser at **http://localhost:8501**.

### Pages

| Page | Description |
|------|-------------|
| **Overview** | DB statistics, row counts, navigation guide |
| **Data Collection** | Fetch historical & live data from CoinGecko API |
| **Time Series** | Interactive line chart with moving average (6 sidebar filters) |
| **Quantitative Analysis** | Bar / Box / Violin chart (6 sidebar filters) |
| **Market Dashboard** | KPI cards · grouped bar · heatmap · treemap |
| **Correlation & Volatility** | Correlation matrix · annualised volatility bar |

> The app reads from `crypto_market.db`. Run **Data Collection** first if the database is empty.

---

## Database Schema

```
crypto_market.db
│
├── cryptocurrencies          ← master list of tracked assets
│     id TEXT PK
│     symbol TEXT             (e.g. BTC)
│     name   TEXT             (e.g. Bitcoin)
│
├── market_snapshots          ← historical daily candles  [1 826 rows]
│     record_id   INTEGER PK AUTOINCREMENT
│     crypto_id   TEXT  FK → cryptocurrencies.id
│     snapshot_date DATE                          UNIQUE(crypto_id, snapshot_date)
│     price_usd   REAL
│     market_cap  REAL
│     total_volume REAL
│     INDEX idx_snapshots_date(snapshot_date)
│
└── market_current            ← live snapshots (one row per fetch per coin)
      record_id                INTEGER PK AUTOINCREMENT
      crypto_id                TEXT  FK → cryptocurrencies.id
      collected_at             DATETIME
      price_usd / market_cap / total_volume / high_24h / low_24h
      price_change_24h / price_change_percentage_24h / price_change_percentage_7d
      market_cap_rank / circulating_supply / total_supply / max_supply
      ath / ath_change_percentage
      INDEX idx_current_collected_at(collected_at)
```

### Current data volume

| Table | Rows |
|-------|------|
| `cryptocurrencies` | 5 |
| `market_snapshots` | 1 826 (366 days × 5 coins) |
| `market_current` | 10 (2 live fetches × 5 coins) |

---

## Coins Tracked

| Symbol | Name |
|--------|------|
| BTC | Bitcoin |
| ETH | Ethereum |
| SOL | Solana |
| BNB | BNB (Binance Coin) |
| XRP | XRP (Ripple) |

---

## Notebook Stages

| Stage | Cell(s) | Description |
|-------|---------|-------------|
| 1 | 3 | Dependencies note (managed by uv) |
| 2 | 5 | Imports, constants, `COINS` list |
| 3 | 7 | `CREATE TABLE` statements, indexes, FK constraints |
| 4 | 8 | Insert coin master list, verify |
| 5 | 10 | API helper functions (`fetch_market_chart`, `store_market_chart`, …) |
| 5 | 12 | **Fetch 365-day history** from CoinGecko + store in DB |
| 6 | 15 | Verify row counts & date ranges in DB |
| 7 | 17 | Load full dataset into a pandas DataFrame |
| 8 | 19 | **Time Series** interactive chart (6 filters) |
| 9 | 21 | **Quantitative Analysis** interactive chart (6 filters) |
| 10 | 23 | **Market Overview Dashboard** (table · bar · heatmap · treemap) |
| 11 | 25 | **Correlation matrix** + **Annualised Volatility** bar chart |

---

## API Details

| Item | Value |
|------|-------|
| Base URL | `https://api.coingecko.com/api/v3` |
| Endpoint (history) | `GET /coins/{id}/market_chart?vs_currency=usd&days=365&interval=daily` |
| Endpoint (live) | `GET /coins/markets?vs_currency=usd&ids=…` |
| Rate limit (free tier) | ~10–30 requests / minute |
| Auth required | No (public free tier) |
| Delay between calls | 10 s (configurable via `REQUEST_DELAY` in Stage 2) |

---

## Refreshing Data

Re-run **Stage 5** (cell 12) at any time.  
The `INSERT OR REPLACE` constraint on `(crypto_id, snapshot_date)` ensures
historical rows are never duplicated — only new dates are added.

```powershell
# One-liner refresh from CLI
uv run jupyter nbconvert --to notebook --execute crypto_market_analysis.ipynb
```

---

## Dependencies (`pyproject.toml`)

```toml
[project]
requires-python = ">=3.13"
dependencies = [
    "requests>=2.33",
    "pandas>=2.2",
    "plotly>=5.22",
    "ipywidgets>=8.1",
    "ipykernel>=6.29",
    "jupyter>=1.1",
    "nbformat>=5.10",
]
```

All versions are locked in `uv.lock` for fully reproducible installs.
