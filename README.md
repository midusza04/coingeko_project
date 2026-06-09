# Cryptocurrency Market Analysis System

> **Advanced Databases — Final Project**  
> Master's in Automation and Robotics · Computer Science in Control and Management

**Team:** Michał Dusza · Szymon Bugajski · Mateusz Basiura

---

## Overview

The system **automatically fetches** cryptocurrency market data from the public [CoinGecko](https://www.coingecko.com/en/api) API, **stores it in a relational SQLite database** (`crypto_market.db`), and presents it through **interactive visualizations** — in a Jupyter notebook and a Streamlit web application.

```
CoinGecko API  ──►  app.py / notebook  ──►  crypto_market.db  ──►  Plotly charts
```

**Tracked coins:** BTC · ETH · SOL · BNB · XRP (5 coins)  
**Historical data:** 365 days × 5 coins ≈ 1,826 records in `market_snapshots`  
**Python:** 3.13 · **Package manager:** [uv](https://docs.astral.sh/uv/)

---

## Quick Start

```powershell
# 1. Install dependencies
uv sync

# 2a. Run the web app (recommended)
uv run streamlit run app.py
# → http://localhost:8501

# 2b. Or run the analytical notebook
uv run jupyter lab crypto_market_analysis.ipynb
```

> On first run, go to **Data Collection** in Streamlit (or Stage 5 in the notebook) to fetch data from the API into the database.

---

## Features

| Module | Description |
|--------|-------------|
| **Data acquisition** | 365-day history (price, market cap, volume) + live market snapshot |
| **Database** | 3 SQLite tables: `cryptocurrencies`, `market_snapshots`, `market_current` — FK, UNIQUE, indexes, 3NF |
| **Time series** | Line chart with coin, date, metric filters; moving average; log scale |
| **Quantitative analysis** | Bar / box / violin charts with aggregations (mean, max, min, std) |
| **Market dashboard** | KPI cards, table, grouped bar, change heatmap, market cap treemap |
| **Correlation & volatility** | Correlation matrix, annualised volatility, rolling BTC correlation |

---

## Repository Structure

```
project/
│
├── app.py                          # Main Streamlit app (ETL + 6 UI pages)
├── crypto_market_analysis.ipynb    # Analytical notebook (11 stages)
├── crypto_market.db                # SQLite database (auto-created)
│
├── pyproject.toml                  # Project dependencies (uv)
├── uv.lock                         # Locked package versions
├── .python-version                 # Python 3.13
│
├── SPRAWOZDANIE.md                 # Academic report — main project description
├── DOCUMENTATION.md                # Technical documentation — DDL, SQL, modules
├── README.md                       # This file — quick start and doc index
│
├── .docs/                          # Concise technical documentation
│   ├── README.md                   #   .docs folder index
│   ├── architecture.md             #   3-tier architecture
│   ├── data-model.md               #   SQLite schema + API mapping
│   ├── api-reference.md            #   app.py and main.py function reference
│   └── diagrams.md                 #   Mermaid diagrams
│
├── docs/                           # Static HTML documentation
│   ├── index.html                  #   Documentation portal
│   └── main.html                   #   Legacy main.py reference
│
├── main.py                         # [legacy] Simple JSON fetcher → coingecko_response.json
├── test.ipynb                      # [legacy] Exploratory API notebook (3 coins)
├── coingecko_response.json         # [legacy] Sample API response
│
├── generate_sprawozdanie.py        # DOCX report generator
├── SPRAWOZDANIE.docx               # Generated Word report
└── raport_cryptomarket_db.docx     # Older Word report (v0.1)
```

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.13 |
| Package manager | uv |
| Database | SQLite 3 (stdlib) |
| Data source | CoinGecko API v3 (public) |
| Web app | Streamlit 1.57 |
| Notebook | JupyterLab 4 + ipywidgets 8 |
| Visualization | Plotly 6 |
| Data | pandas 2.2+ |

---

## Database

```
crypto_market.db
│
├── cryptocurrencies          ← coin lookup table (5 rows)
│     id TEXT PK · symbol · name
│
├── market_snapshots          ← daily history (~1,826 rows)
│     record_id PK · crypto_id FK · snapshot_date
│     price_usd · market_cap · total_volume
│     UNIQUE(crypto_id, snapshot_date)
│     INDEX idx_snapshots_date
│
└── market_current            ← live snapshots (append-only)
      record_id PK · crypto_id FK · collected_at
      price_usd · market_cap · high_24h · low_24h
      price_change_* · market_cap_rank · supply · ath
      INDEX idx_current_collected_at
```

DDL, constraints, and normalisation details → [`SPRAWOZDANIE.md` §4](SPRAWOZDANIE.md) or [`.docs/data-model.md`](.docs/data-model.md).

---

## Streamlit App (`app.py`)

```powershell
uv run streamlit run app.py
```

| Page | Description |
|------|-------------|
| **Overview** | DB statistics, date range, navigation |
| **Data Collection** | Fetch historical and live data from CoinGecko |
| **Time Series** | Line chart (6 sidebar filters) |
| **Quantitative Analysis** | Bar / Box / Violin (6 filters) |
| **Market Dashboard** | KPI · table · grouped bar · heatmap · treemap |
| **Correlation & Volatility** | Correlation matrix · volatility · BTC correlation |

---

## Notebook (`crypto_market_analysis.ipynb`)

| Stage | Description |
|-------|-------------|
| 1–2 | Environment, imports, constants (`COINS`, `METRIC_MAP`) |
| 3–4 | DB DDL, coin master list insertion |
| 5 | Fetch 365-day history from API + save to DB |
| 6–7 | DB verification, load into pandas DataFrame |
| 8 | Time series (ipywidgets + Plotly) |
| 9 | Quantitative analysis |
| 10 | Market dashboard |
| 11 | Correlation and volatility |

---

## Documentation — what is what

| File | Audience | Contents |
|------|----------|----------|
| **[`SPRAWOZDANIE.md`](SPRAWOZDANIE.md)** | Evaluation / presentation | Full academic report: goals, DB schema, architecture, implementation, visualizations, issues, conclusions |
| **[`DOCUMENTATION.md`](DOCUMENTATION.md)** | Developers | DDL, SQL queries, data flow, module reference, configuration |
| **[`.docs/`](.docs/)** | Quick reference | Concise technical docs split by topic |
| **[`docs/index.html`](docs/index.html)** | Browser | Static HTML portal with links to all sections |
| **`SPRAWOZDANIE.docx`** | Print / submission | Generated Word report (`generate_sprawozdanie.py`) |

### `.docs/` folder details

| File | Contents |
|------|----------|
| [`.docs/README.md`](.docs/README.md) | Technical documentation index |
| [`.docs/architecture.md`](.docs/architecture.md) | 3 layers: acquisition → SQLite → presentation |
| [`.docs/data-model.md`](.docs/data-model.md) | SQLite schema, API field → DB column mapping |
| [`.docs/api-reference.md`](.docs/api-reference.md) | `app.py` (main) and `main.py` (legacy) functions |
| [`.docs/diagrams.md`](.docs/diagrams.md) | Mermaid diagrams: ERD, sequence, ETL, architecture |

---

## Legacy Files (early project stage)

| File | Description |
|------|-------------|
| `main.py` | Simple script: fetches 3 coins from API → saves `coingecko_response.json` (no DB) |
| `test.ipynb` | Exploratory notebook — API response inspection |
| `coingecko_response.json` | Sample API response (BTC, ETH, SOL) |

The main system (`app.py` + notebook) replaced these files — kept as reference.

---

## Refreshing Data

In Streamlit: **Data Collection** page → *Fetch Historical* / *Fetch Live Snapshot* buttons.  
In the notebook: re-run **Stage 5** (cell 12).

`INSERT OR REPLACE` on `(crypto_id, snapshot_date)` ensures idempotent writes — re-fetching never creates duplicates.

---

*Academic project — Advanced Databases, May 2026.*
