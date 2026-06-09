# Diagrams

> All diagrams in [Mermaid](https://mermaid.js.org/) format — render natively on GitHub, GitLab, and Mermaid-capable editors.

Architecture details: [`architecture.md`](architecture.md) · DB schema: [`data-model.md`](data-model.md)

---

## 1. System Architecture (3 Layers)

```mermaid
flowchart TD
    subgraph EXTERNAL ["External Source"]
        API["🌐 CoinGecko REST API v3\n(public, no API key)"]
    end

    subgraph COLLECT ["Data Acquisition Layer"]
        F1["fetch_market_chart()\n/coins/{id}/market_chart"]
        F2["fetch_markets_current()\n/coins/markets"]
        S1["store_market_chart()"]
        S2["store_current()"]
    end

    subgraph STORAGE ["Storage Layer"]
        DB[("🗄️ SQLite 3\ncrypto_market.db")]
    end

    subgraph PRESENT ["Presentation Layer"]
        NB["📓 crypto_market_analysis.ipynb\n11 stages · ipywidgets"]
        APP["🌐 app.py — Streamlit\n6 pages · Plotly"]
    end

    API -->|HTTP GET| F1
    API -->|HTTP GET| F2
    F1 --> S1
    F2 --> S2
    S1 -->|"INSERT OR REPLACE\nmarket_snapshots"| DB
    S2 -->|"INSERT\nmarket_current"| DB
    DB -->|"SELECT + JOIN\npd.read_sql"| NB
    DB -->|"SELECT + JOIN\npd.read_sql"| APP
```

---

## 2. ERD — Implemented SQLite Schema

```mermaid
erDiagram
    cryptocurrencies {
        TEXT id PK "e.g. bitcoin"
        TEXT symbol NOT_NULL "e.g. BTC"
        TEXT name NOT_NULL "e.g. Bitcoin"
    }

    market_snapshots {
        INTEGER record_id PK "AUTOINCREMENT"
        TEXT crypto_id FK "→ cryptocurrencies.id"
        DATE snapshot_date NOT_NULL "YYYY-MM-DD"
        REAL price_usd "closing price USD"
        REAL market_cap "market cap USD"
        REAL total_volume "24h volume USD"
    }

    market_current {
        INTEGER record_id PK "AUTOINCREMENT"
        TEXT crypto_id FK "→ cryptocurrencies.id"
        DATETIME collected_at NOT_NULL "UTC"
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

    cryptocurrencies ||--o{ market_snapshots : "has daily snapshots"
    cryptocurrencies ||--o{ market_current : "has live snapshots"
```

---

## 3. Sequence Diagram — Historical Data Fetch

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Streamlit / Notebook
    participant App as app.py
    participant API as CoinGecko API
    participant DB as SQLite

    User->>UI: Click "Fetch Historical Data"
    UI->>App: Initiate fetch

    loop For each of 5 coins
        App->>API: GET /coins/{id}/market_chart?days=365
        alt HTTP 200
            API-->>App: JSON {prices, market_caps, total_volumes}
            App->>App: Convert ts_ms → YYYY-MM-DD
            App->>DB: INSERT OR REPLACE market_snapshots (~366 rows)
            DB-->>App: OK
            App->>App: sleep(10s) — rate limit
        else HTTP 429
            API-->>App: 429 Too Many Requests
            App-->>UI: Error message
        else Timeout / network error
            App-->>UI: Exception + message
        end
    end

    App-->>UI: "All historical data stored!"
    UI-->>User: Summary (row count)
```

---

## 4. Sequence Diagram — Live Fetch + Visualization

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Streamlit
    participant App as app.py
    participant API as CoinGecko API
    participant DB as SQLite

    Note over User,DB: Live snapshot fetch
    User->>UI: Click "Fetch Live Snapshot"
    App->>API: GET /coins/markets?ids=bitcoin,ethereum,...
    API-->>App: JSON list of 5 objects
    App->>DB: INSERT INTO market_current (5 rows)
    App-->>UI: "Stored live snapshot for 5 coins"

    Note over User,DB: Visualization
    User->>UI: Navigate → Time Series
    UI->>App: load_snapshots()
    App->>DB: SELECT … JOIN cryptocurrencies
    DB-->>App: ResultSet
    App->>App: pandas DataFrame + filtering
    App-->>UI: Plotly chart
    UI-->>User: Interactive chart
```

---

## 5. Flow Diagram — Historical ETL

```mermaid
flowchart LR
    subgraph E["Extract"]
        E1["GET /coins/{id}/market_chart\n?days=365&interval=daily"]
        E2["response.json()\n{prices, market_caps, total_volumes}"]
        E1 --> E2
    end

    subgraph T["Transform"]
        T1["For each [ts_ms, value] pair:\nts_ms / 1000 → UTC datetime\n→ strftime('%Y-%m-%d')"]
        T2["Build tuple list:\n(crypto_id, date, price, mcap, volume)"]
        E2 --> T1 --> T2
    end

    subgraph L["Load"]
        L1["executemany(\nINSERT OR REPLACE\nmarket_snapshots\nVALUES (?,?,?,?,?)\n)"]
        L2["commit()"]
        T2 --> L1 --> L2
    end
```

---

## 6. Flow Diagram — `create_database()` Logic

```mermaid
flowchart TD
    START([▶ start app.py / Stage 3]) --> CONNECT[sqlite3.connect DB_PATH]
    CONNECT --> T1[CREATE TABLE IF NOT EXISTS cryptocurrencies]
    T1 --> T2[CREATE TABLE IF NOT EXISTS market_snapshots\n+ UNIQUE + FK]
    T2 --> I1[CREATE INDEX IF NOT EXISTS idx_snapshots_date]
    I1 --> T3[CREATE TABLE IF NOT EXISTS market_current\n+ FK]
    T3 --> I2[CREATE INDEX IF NOT EXISTS idx_current_collected_at]
    I2 --> SEED[INSERT OR IGNORE cryptocurrencies\n× 5 coins]
    SEED --> COMMIT[conn.commit + close]
    COMMIT --> END([✓ Database ready])
```

---

## 7. Component Diagram — Modules and Dependencies

```mermaid
classDiagram
    class app_py {
        <<module — main>>
        +create_database() None
        +load_snapshots() DataFrame
        +load_db_stats() dict
        +fetch_market_chart(coin_id, days) dict
        +fetch_markets_current() list
        +store_market_chart(coin_id, data) int
        +store_current(data) None
        +page_overview() None
        +page_data_collection() None
        +page_time_series() None
        +page_quantitative() None
        +page_market_dashboard() None
        +page_correlation() None
        +main() None
    }

    class notebook {
        <<crypto_market_analysis.ipynb>>
        +11 analytical stages
        +same DB/API functions
    }

    class main_py {
        <<module — legacy>>
        +main() None
    }

    class sqlite3 {
        <<stdlib>>
        +connect(path) Connection
    }

    class requests {
        <<PyPI>>
        +get(url, params, timeout) Response
    }

    class streamlit {
        <<PyPI>>
        +cache_data sidebar pages
    }

    class plotly {
        <<PyPI>>
        +px.line px.bar px.imshow
    }

    class CoinGeckoAPI {
        <<REST API v3>>
        +GET market_chart
        +GET coins/markets
    }

    app_py --> sqlite3 : read/write
    app_py --> requests : HTTP
    app_py --> streamlit : UI
    app_py --> plotly : charts
    notebook --> sqlite3 : read/write
    notebook --> requests : HTTP
    notebook --> plotly : charts
    requests --> CoinGeckoAPI : HTTPS
    main_py --> requests : HTTP (legacy)
```

---

## 8. Flow Diagram — Legacy `main.py`

> Legacy module — replaced by `app.py`. Kept as reference for the early project stage.

```mermaid
flowchart TD
    START([▶ python main.py]) --> GET[requests.get /coins/markets\n3 coins: BTC, ETH, SOL]
    GET -->|2xx| PARSE[response.json → list]
    GET -->|error| ERR([✗ HTTPError / Timeout])
    PARSE --> WRITE[Path.write_text\ncoingecko_response.json]
    WRITE --> PRINT[Print fields to stdout]
    PRINT --> END([✓ Done — no DB write])
```

---

*Documentation index: [`.docs/README.md`](README.md)*
