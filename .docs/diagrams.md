# Diagramy

Wszystkie diagramy zapisane w formacie [Mermaid](https://mermaid.js.org/) — renderują się natywnie na GitHub, GitLab i w edytorach obsługujących Mermaid.

---

## 1. Diagram sekwencji — wywołanie `main()`

Przedstawia pełny przepływ wykonania funkcji `main()`, od startu do zakończenia.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Script as main.py
    participant Requests as requests (HTTP)
    participant CoinGecko as CoinGecko API
    participant FS as System plików

    User->>Script: python main.py
    Script->>Script: buduje params dict
    Script->>Requests: requests.get(url, params, timeout=10)
    Requests->>CoinGecko: GET /api/v3/coins/markets?vs_currency=usd&ids=bitcoin,ethereum,solana&...
    
    alt Sukces (HTTP 200)
        CoinGecko-->>Requests: 200 OK + JSON body (tablica 3 obiektów)
        Requests-->>Script: Response object
        Script->>Script: response.raise_for_status() — brak wyjątku
        Script->>Script: data = response.json() → list[dict]
        Script->>Script: json.dumps(data, indent=4)
        Script->>FS: Path("coingecko_response.json").write_text(...)
        FS-->>Script: plik zapisany
        Script->>User: print("Status code: 200")
        Script->>User: print("Zapisano dane do pliku: ...")
        Script->>User: print(pola pierwszego rekordu)
    else Błąd HTTP (4xx / 5xx)
        CoinGecko-->>Requests: 4xx / 5xx + body
        Requests-->>Script: Response object
        Script->>Script: response.raise_for_status()
        Script->>User: raises HTTPError
    else Timeout (> 10s)
        Requests->>Script: raises Timeout
        Script->>User: propaguje Timeout
    else Brak sieci
        Requests->>Script: raises ConnectionError
        Script->>User: propaguje ConnectionError
    end
```

---

## 2. Diagram przepływu — logika funkcji `main()`

```mermaid
flowchart TD
    START([▶ Start: python main.py]) --> BUILD[Zbuduj URL i params dict]
    BUILD --> GET[requests.get\nurl, params, timeout=10]
    GET --> STATUS{Kod HTTP?}

    STATUS -- "2xx" --> PRINT_CODE[print Status code: 200]
    STATUS -- "4xx / 5xx" --> RAISE_HTTP[raise_for_status\n→ HTTPError]
    RAISE_HTTP --> END_ERR([✗ Zakończ z wyjątkiem])

    GET -- "Timeout" --> RAISE_TIMEOUT([✗ Timeout])
    GET -- "ConnectionError" --> RAISE_CONN([✗ ConnectionError])

    PRINT_CODE --> PARSE[data = response.json\n→ list of dicts]
    PARSE --> SERIALIZE[json.dumps\nindent=4, ensure_ascii=False]
    SERIALIZE --> WRITE[Path.write_text\ncoingecko_response.json]
    WRITE --> PRINT_PATH[print Zapisano dane do pliku]
    PRINT_PATH --> CHECK{len data > 0?}
    CHECK -- Tak --> PRINT_KEYS[Wypisz nazwy pól\npierwszego rekordu]
    CHECK -- Nie --> END_OK
    PRINT_KEYS --> END_OK([✓ Zakończ normalnie])
```

---

## 3. Diagram klas / modułów

> Projekt nie definiuje klas OOP — diagram przedstawia **moduły, funkcje i zewnętrzne zależności**.

```mermaid
classDiagram
    class main {
        <<module>>
        +main() None
    }

    class requests {
        <<external library>>
        +get(url, params, timeout) Response
    }

    class Response {
        <<requests.models>>
        +status_code : int
        +raise_for_status() None
        +json() list[dict]
    }

    class json {
        <<stdlib module>>
        +dumps(obj, indent, ensure_ascii) str
    }

    class Path {
        <<pathlib.Path>>
        +write_text(data, encoding) None
    }

    class CoinGeckoAPI {
        <<external REST API>>
        +GET /api/v3/coins/markets
        -vs_currency : str
        -ids : str
        -order : str
        -per_page : int
        -page : int
        -sparkline : str
        -price_change_percentage : str
    }

    main --> requests : używa
    main --> json : używa
    main --> Path : używa
    requests --> Response : zwraca
    requests --> CoinGeckoAPI : HTTP GET
```

---

## 4. Diagram ERD — planowany schemat bazy danych

```mermaid
erDiagram
    COINS {
        text    id              PK  "identyfikator CoinGecko"
        text    symbol              "ticker (btc, eth, sol)"
        text    name                "pełna nazwa"
        text    image_url           "URL logo"
        numeric max_supply          "maks. podaż (nullable)"
        timestamptz created_at      "czas dodania rekordu"
    }

    MARKET_SNAPSHOTS {
        bigint      snapshot_id     PK  "klucz główny (autoincrement)"
        text        coin_id         FK  "→ coins.id"
        timestamptz fetched_at          "czas pobrania przez skrypt"
        timestamptz last_updated        "czas aktualizacji wg API"
        numeric     current_price
        numeric     high_24h
        numeric     low_24h
        bigint      market_cap
        integer     market_cap_rank
        bigint      fully_diluted_valuation
        bigint      total_volume
        numeric     circulating_supply
        numeric     total_supply
        numeric     price_change_24h
        numeric     price_change_pct_24h
        numeric     market_cap_change_24h
        numeric     market_cap_change_pct_24h
        numeric     price_change_pct_24h_in_currency
        numeric     price_change_pct_7d_in_currency
        numeric     ath
        numeric     ath_change_percentage
        timestamptz ath_date
        numeric     atl
        numeric     atl_change_percentage
        timestamptz atl_date
    }

    ROI_DATA {
        bigint  roi_id          PK  "klucz główny (autoincrement)"
        bigint  snapshot_id     FK  "→ market_snapshots.snapshot_id"
        numeric times               "wielokrotność zwrotu"
        text    currency            "waluta bazowa ROI"
        numeric percentage          "procentowy zwrot"
    }

    COINS ||--o{ MARKET_SNAPSHOTS : "posiada wiele snapshotów"
    MARKET_SNAPSHOTS ||--o| ROI_DATA : "opcjonalne dane ROI"
```

---

## 5. Diagram komponentów — architektura systemu

```mermaid
C4Component
    title Architektura — CryptoMarket DB Ingestion

    Person(user, "Użytkownik", "Uruchamia skrypt ręcznie lub przez cron")

    System_Boundary(ingestion, "Warstwa Ingestion") {
        Component(main, "main.py", "Python module", "Pobiera dane z API i zapisuje JSON")
        Component(notebook, "test.ipynb", "Jupyter Notebook", "Eksploracja i inspekcja danych API")
    }

    System_Boundary(storage, "Warstwa Przechowywania") {
        ComponentDb(jsonfile, "coingecko_response.json", "Plik JSON", "Lokalna kopia odpowiedzi API")
        ComponentDb(db, "Baza danych", "PostgreSQL / SQLite", "Planowana — coins, market_snapshots, roi_data")
    }

    System_Ext(coingecko, "CoinGecko API", "REST API v3 — /coins/markets")

    Rel(user, main, "Uruchamia", "CLI")
    Rel(user, notebook, "Otwiera", "Jupyter")
    Rel(main, coingecko, "GET /coins/markets", "HTTPS/JSON")
    Rel(main, jsonfile, "Zapisuje", "write_text")
    Rel(notebook, coingecko, "GET /coins/markets", "HTTPS/JSON")
    Rel(jsonfile, db, "ETL (planowane)", "INSERT / UPSERT")
```

---

## 6. Diagram aktywności — planowany ETL

Przyszły przepływ ETL (Extract → Transform → Load) do bazy danych.

```mermaid
flowchart LR
    subgraph E[Extract]
        E1[requests.get\nCoinGecko API]
        E2[response.json\nlist of dicts]
        E1 --> E2
    end

    subgraph T[Transform]
        T1[Wyodrębnij pola\ncoins statyczne]
        T2[Wyodrębnij pola\nmarket_snapshots]
        T3[Sprawdź roi != null\n→ roi_data]
        T4[Konwertuj daty\nISO 8601 → TIMESTAMPTZ]
        E2 --> T1
        E2 --> T2
        E2 --> T3
        T2 --> T4
    end

    subgraph L[Load]
        L1[UPSERT coins]
        L2[INSERT market_snapshots]
        L3[INSERT roi_data\njeśli roi != null]
        T1 --> L1
        T4 --> L2
        T3 --> L3
        L1 --> L2
        L2 --> L3
    end
```

---

*Opis architektury — zob. [`architecture.md`](architecture.md).*  
*Model danych — zob. [`data-model.md`](data-model.md).*
