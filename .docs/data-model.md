# Model danych

> Pełny opis akademicki: [`SPRAWOZDANIE.md` §4](../SPRAWOZDANIE.md)  
> DDL i zapytania SQL (EN): [`DOCUMENTATION.md` §2–3](../DOCUMENTATION.md)

---

## Przegląd

Baza `crypto_market.db` (SQLite 3) składa się z **3 tabel** w modelu gwiazdy:

- **`cryptocurrencies`** — wymiar (dimension): słownik śledzonych monet
- **`market_snapshots`** — fakt historyczny: dzienne wartości ceny, kapitalizacji, wolumenu
- **`market_current`** — fakt bieżący: bogaty snapshot live z API `/coins/markets`

Schemat spełnia **3NF** (Trzecią Postać Normalną).

---

## Diagram ERD

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
        DATETIME collected_at NOT_NULL "czas pobrania UTC"
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

    cryptocurrencies ||--o{ market_snapshots : "ma snapshoty"
    cryptocurrencies ||--o{ market_current : "ma snapshoty live"
```

---

## DDL — definicje tabel

```sql
CREATE TABLE IF NOT EXISTS cryptocurrencies (
    id     TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    name   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS market_snapshots (
    record_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    crypto_id     TEXT    NOT NULL,
    snapshot_date DATE    NOT NULL,
    price_usd     REAL,
    market_cap    REAL,
    total_volume  REAL,
    UNIQUE (crypto_id, snapshot_date),
    FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies(id)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_date
    ON market_snapshots(snapshot_date);

CREATE TABLE IF NOT EXISTS market_current (
    record_id                   INTEGER  PRIMARY KEY AUTOINCREMENT,
    crypto_id                   TEXT     NOT NULL,
    collected_at                DATETIME NOT NULL,
    price_usd                   REAL,
    market_cap                  REAL,
    total_volume                REAL,
    high_24h                    REAL,
    low_24h                     REAL,
    price_change_24h            REAL,
    price_change_percentage_24h REAL,
    price_change_percentage_7d  REAL,
    market_cap_rank             INTEGER,
    circulating_supply          REAL,
    total_supply                REAL,
    max_supply                  REAL,
    ath                         REAL,
    ath_change_percentage       REAL,
    FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies(id)
);

CREATE INDEX IF NOT EXISTS idx_current_collected_at
    ON market_current(collected_at);
```

---

## Opis tabel

### `cryptocurrencies` — słownik monet

| Kolumna | Typ | Ograniczenia | Opis |
|---------|-----|-------------|------|
| `id` | TEXT | PRIMARY KEY | Identyfikator CoinGecko, np. `bitcoin` |
| `symbol` | TEXT | NOT NULL | Ticker, np. `BTC` |
| `name` | TEXT | NOT NULL | Pełna nazwa, np. `Bitcoin` |

**Dane:** 5 wierszy (BTC, ETH, SOL, BNB, XRP). Wstawiane przez `INSERT OR IGNORE` w `create_database()`.

### `market_snapshots` — historia dzienna

| Kolumna | Typ | Ograniczenia | Opis |
|---------|-----|-------------|------|
| `record_id` | INTEGER | PK, AUTOINCREMENT | Klucz surogatowy |
| `crypto_id` | TEXT | NOT NULL, FK | → `cryptocurrencies.id` |
| `snapshot_date` | DATE | NOT NULL | Data `YYYY-MM-DD` (UTC) |
| `price_usd` | REAL | — | Cena zamknięcia w USD |
| `market_cap` | REAL | — | Kapitalizacja rynkowa w USD |
| `total_volume` | REAL | — | Wolumen obrotu 24h w USD |

**Źródło:** `GET /coins/{id}/market_chart?days=365&interval=daily`  
**Zapis:** `INSERT OR REPLACE` — idempotentny, ~366 wierszy na monetę  
**Objętość:** ~1 826 wierszy (366 dni × 5 monet)

### `market_current` — bieżące snapshoty

| Kolumna | Typ | Opis |
|---------|-----|------|
| `record_id` | INTEGER PK | Klucz surogatowy |
| `crypto_id` | TEXT FK | → `cryptocurrencies.id` |
| `collected_at` | DATETIME | Czas pobrania (UTC) |
| `price_usd` | REAL | Bieżąca cena |
| `market_cap` | REAL | Kapitalizacja |
| `total_volume` | REAL | Wolumen 24h |
| `high_24h` / `low_24h` | REAL | Min/max cena 24h |
| `price_change_24h` | REAL | Zmiana ceny 24h (USD) |
| `price_change_percentage_24h` | REAL | Zmiana ceny 24h (%) |
| `price_change_percentage_7d` | REAL | Zmiana ceny 7d (%) |
| `market_cap_rank` | INTEGER | Ranking globalny |
| `circulating_supply` | REAL | Podaż w obiegu |
| `total_supply` / `max_supply` | REAL | Podaż całkowita / maksymalna |
| `ath` | REAL | All-time high (USD) |
| `ath_change_percentage` | REAL | Odległość od ATH (%) |

**Źródło:** `GET /coins/markets?ids=…`  
**Zapis:** `INSERT` (append-only — każde pobranie dodaje nowe wiersze)

---

## Ograniczenia integralności

| Ograniczenie | Tabela | Definicja | Cel |
|-------------|--------|-----------|-----|
| PRIMARY KEY | wszystkie | `id` lub `record_id` | Jednoznaczna identyfikacja |
| FOREIGN KEY | `market_snapshots`, `market_current` | `crypto_id → cryptocurrencies.id` | Brak rekordów osieroconych |
| UNIQUE | `market_snapshots` | `(crypto_id, snapshot_date)` | Jeden rekord na monetę na dzień |
| NOT NULL | `market_snapshots` | `crypto_id`, `snapshot_date` | Klucz naturalny zawsze podany |
| NOT NULL | `market_current` | `crypto_id`, `collected_at` | Identyfikacja snapshotu |

---

## Indeksy

| Indeks | Tabela | Kolumny | Cel |
|--------|--------|---------|-----|
| PK autoindex | wszystkie | `record_id` / `id` | Lookup po kluczu głównym |
| `sqlite_autoindex_…` | `market_snapshots` | `(crypto_id, snapshot_date)` | Filtr po monecie + zakres dat (z UNIQUE) |
| `idx_snapshots_date` | `market_snapshots` | `snapshot_date` | Filtr po samej dacie |
| `idx_current_collected_at` | `market_current` | `collected_at` | Filtr po czasie pobrania |

---

## Mapowanie API → baza danych

### Endpoint historyczny: `/coins/{id}/market_chart`

| Pole API | Tabela | Kolumna DB | Transformacja |
|----------|--------|------------|---------------|
| `prices[i][0]` | `market_snapshots` | `snapshot_date` | `ts_ms / 1000` → `YYYY-MM-DD` UTC |
| `prices[i][1]` | `market_snapshots` | `price_usd` | bezpośrednio |
| `market_caps[i][1]` | `market_snapshots` | `market_cap` | bezpośrednio |
| `total_volumes[i][1]` | `market_snapshots` | `total_volume` | bezpośrednio |
| (parametr URL) | `market_snapshots` | `crypto_id` | `coin_id` z zapytania |

### Endpoint live: `/coins/markets`

| Pole API | Tabela | Kolumna DB |
|----------|--------|------------|
| `id` | `market_current` | `crypto_id` |
| `current_price` | `market_current` | `price_usd` |
| `market_cap` | `market_current` | `market_cap` |
| `total_volume` | `market_current` | `total_volume` |
| `high_24h` | `market_current` | `high_24h` |
| `low_24h` | `market_current` | `low_24h` |
| `price_change_24h` | `market_current` | `price_change_24h` |
| `price_change_percentage_24h` | `market_current` | `price_change_percentage_24h` |
| `price_change_percentage_7d_in_currency` | `market_current` | `price_change_percentage_7d` |
| `market_cap_rank` | `market_current` | `market_cap_rank` |
| `circulating_supply` | `market_current` | `circulating_supply` |
| `total_supply` | `market_current` | `total_supply` |
| `max_supply` | `market_current` | `max_supply` |
| `ath` | `market_current` | `ath` |
| `ath_change_percentage` | `market_current` | `ath_change_percentage` |
| (generowane) | `market_current` | `collected_at` | `datetime.utcnow()` |

### Słownik monet

| Pole API (`/coins/markets`) | Tabela | Kolumna DB |
|-----------------------------|--------|------------|
| `id` | `cryptocurrencies` | `id` |
| `symbol` | `cryptocurrencies` | `symbol` (uppercase) |
| `name` | `cryptocurrencies` | `name` |

---

## Normalizacja (3NF)

| Tabela | 1NF | 2NF | 3NF | Uwagi |
|--------|:---:|:---:|:---:|-------|
| `cryptocurrencies` | ✅ | ✅ | ✅ | Prosta tabela słownikowa |
| `market_snapshots` | ✅ | ✅ | ✅ | Tabela faktów; brak kolumn pochodnych |
| `market_current` | ✅ | ✅ | ✅ | Wartości surowe z API, nie pochodne z innych kolumn |

Metadane monety (`symbol`, `name`) przechowywane wyłącznie w `cryptocurrencies` — tabele faktów zawierają tylko klucz obcy `crypto_id`.

---

## Objętość danych (stan projektu)

| Tabela | Wiersze | Opis |
|--------|---------|------|
| `cryptocurrencies` | 5 | BTC, ETH, SOL, BNB, XRP |
| `market_snapshots` | ~1 826 | 366 dni × 5 monet |
| `market_current` | ~10 | 2 pobrania × 5 monet |

---

*Architektura: [`architecture.md`](architecture.md) · Diagramy: [`diagrams.md`](diagrams.md)*
