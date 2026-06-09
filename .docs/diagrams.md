# Diagramy

> Wszystkie diagramy w formacie [Mermaid](https://mermaid.js.org/) — renderują się na GitHub, GitLab i w edytorach z obsługą Mermaid.

Pełny opis architektury: [`architecture.md`](architecture.md) · Schemat DB: [`data-model.md`](data-model.md)

---

## 1. Architektura systemu (3 warstwy)

```mermaid
flowchart TD
    subgraph EXTERNAL ["Źródło zewnętrzne"]
        API["🌐 CoinGecko REST API v3\n(publiczne, bez klucza)"]
    end

    subgraph COLLECT ["Warstwa pozyskiwania danych"]
        F1["fetch_market_chart()\n/coins/{id}/market_chart"]
        F2["fetch_markets_current()\n/coins/markets"]
        S1["store_market_chart()"]
        S2["store_current()"]
    end

    subgraph STORAGE ["Warstwa przechowywania"]
        DB[("🗄️ SQLite 3\ncrypto_market.db")]
    end

    subgraph PRESENT ["Warstwa prezentacji"]
        NB["📓 crypto_market_analysis.ipynb\n11 etapów · ipywidgets"]
        APP["🌐 app.py — Streamlit\n6 stron · Plotly"]
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

## 2. Diagram ERD — zaimplementowany schemat SQLite

```mermaid
erDiagram
    cryptocurrencies {
        TEXT id PK "np. bitcoin"
        TEXT symbol NOT_NULL "np. BTC"
        TEXT name NOT_NULL "np. Bitcoin"
    }

    market_snapshots {
        INTEGER record_id PK "AUTOINCREMENT"
        TEXT crypto_id FK "→ cryptocurrencies.id"
        DATE snapshot_date NOT_NULL "RRRR-MM-DD"
        REAL price_usd "cena zamknięcia USD"
        REAL market_cap "kapitalizacja USD"
        REAL total_volume "wolumen 24h USD"
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

    cryptocurrencies ||--o{ market_snapshots : "ma snapshoty dzienne"
    cryptocurrencies ||--o{ market_current : "ma snapshoty live"
```

---

## 3. Diagram sekwencji — pobieranie danych historycznych

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Streamlit / Notebook
    participant App as app.py
    participant API as CoinGecko API
    participant DB as SQLite

    User->>UI: Klik "Fetch Historical Data"
    UI->>App: Inicjacja pobierania

    loop Dla każdej z 5 monet
        App->>API: GET /coins/{id}/market_chart?days=365
        alt HTTP 200
            API-->>App: JSON {prices, market_caps, total_volumes}
            App->>App: Konwersja ts_ms → YYYY-MM-DD
            App->>DB: INSERT OR REPLACE market_snapshots (~366 wierszy)
            DB-->>App: OK
            App->>App: sleep(10s) — rate limit
        else HTTP 429
            API-->>App: 429 Too Many Requests
            App-->>UI: Komunikat błędu
        else Timeout / błąd sieci
            App-->>UI: Wyjątek + komunikat
        end
    end

    App-->>UI: "All historical data stored!"
    UI-->>User: Podsumowanie (liczba wierszy)
```

---

## 4. Diagram sekwencji — pobieranie live + wizualizacja

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Streamlit
    participant App as app.py
    participant API as CoinGecko API
    participant DB as SQLite

    Note over User,DB: Pobieranie bieżącego snapshotu
    User->>UI: Klik "Fetch Live Snapshot"
    App->>API: GET /coins/markets?ids=bitcoin,ethereum,...
    API-->>App: JSON lista 5 obiektów
    App->>DB: INSERT INTO market_current (5 wierszy)
    App-->>UI: "Stored live snapshot for 5 coins"

    Note over User,DB: Wizualizacja
    User->>UI: Nawigacja → Time Series
    UI->>App: load_snapshots()
    App->>DB: SELECT … JOIN cryptocurrencies
    DB-->>App: ResultSet
    App->>App: pandas DataFrame + filtrowanie
    App-->>UI: Plotly chart
    UI-->>User: Interaktywny wykres
```

---

## 5. Diagram przepływu — ETL historyczny

```mermaid
flowchart LR
    subgraph E["Extract"]
        E1["GET /coins/{id}/market_chart\n?days=365&interval=daily"]
        E2["response.json()\n{prices, market_caps, total_volumes}"]
        E1 --> E2
    end

    subgraph T["Transform"]
        T1["Dla każdej pary [ts_ms, value]:\nts_ms / 1000 → datetime UTC\n→ strftime('%Y-%m-%d')"]
        T2["Zbuduj listę tupli:\n(crypto_id, date, price, mcap, volume)"]
        E2 --> T1 --> T2
    end

    subgraph L["Load"]
        L1["executemany(\nINSERT OR REPLACE\nmarket_snapshots\nVALUES (?,?,?,?,?)\n)"]
        L2["commit()"]
        T2 --> L1 --> L2
    end
```

---

## 6. Diagram przepływu — logika `create_database()`

```mermaid
flowchart TD
    START([▶ start app.py / Stage 3]) --> CONNECT[sqlite3.connect DB_PATH]
    CONNECT --> T1[CREATE TABLE IF NOT EXISTS cryptocurrencies]
    T1 --> T2[CREATE TABLE IF NOT EXISTS market_snapshots\n+ UNIQUE + FK]
    T2 --> I1[CREATE INDEX IF NOT EXISTS idx_snapshots_date]
    I1 --> T3[CREATE TABLE IF NOT EXISTS market_current\n+ FK]
    T3 --> I2[CREATE INDEX IF NOT EXISTS idx_current_collected_at]
    I2 --> SEED[INSERT OR IGNORE cryptocurrencies\n× 5 monet]
    SEED --> COMMIT[conn.commit + close]
    COMMIT --> END([✓ Baza gotowa])
```

---

## 7. Diagram komponentów — moduły i zależności

```mermaid
classDiagram
    class app_py {
        <<module — główny>>
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
        +11 etapów analitycznych
        +te same funkcje DB/API
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

## 8. Diagram przepływu — legacy `main.py`

> Moduł legacy — zastąpiony przez `app.py`. Zachowany jako referencja początkowego etapu.

```mermaid
flowchart TD
    START([▶ python main.py]) --> GET[requests.get /coins/markets\n3 monety: BTC, ETH, SOL]
    GET -->|2xx| PARSE[response.json → list]
    GET -->|błąd| ERR([✗ HTTPError / Timeout])
    PARSE --> WRITE[Path.write_text\ncoingecko_response.json]
    WRITE --> PRINT[Wypisz pola na stdout]
    PRINT --> END([✓ Koniec — bez zapisu do DB])
```

---

*Indeks dokumentacji: [`.docs/README.md`](README.md)*
