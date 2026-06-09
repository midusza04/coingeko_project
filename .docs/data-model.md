# Data Model

> Full academic description: [`SPRAWOZDANIE.md` §4](../SPRAWOZDANIE.md)  
> DDL and SQL queries: [`DOCUMENTATION.md` §2–3](../DOCUMENTATION.md)

---

## Overview

The `crypto_market.db` database (SQLite 3) consists of **3 tables** in a star schema:

- **`cryptocurrencies`** — dimension: lookup table of tracked coins
- **`market_snapshots`** — historical fact: daily price, market cap, volume
- **`market_current`** — live fact: rich snapshot from `/coins/markets` API

The schema satisfies **Third Normal Form (3NF)**.

---

## ERD Diagram

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
        DATETIME collected_at NOT_NULL "fetch time UTC"
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
    cryptocurrencies ||--o{ market_current : "has live snapshots"
```

---

## DDL — Table Definitions

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

## Table Descriptions

### `cryptocurrencies` — coin lookup

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | TEXT | PRIMARY KEY | CoinGecko ID, e.g. `bitcoin` |
| `symbol` | TEXT | NOT NULL | Ticker, e.g. `BTC` |
| `name` | TEXT | NOT NULL | Full name, e.g. `Bitcoin` |

**Data:** 5 rows (BTC, ETH, SOL, BNB, XRP). Inserted via `INSERT OR IGNORE` in `create_database()`.

### `market_snapshots` — daily history

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `record_id` | INTEGER | PK, AUTOINCREMENT | Surrogate key |
| `crypto_id` | TEXT | NOT NULL, FK | → `cryptocurrencies.id` |
| `snapshot_date` | DATE | NOT NULL | Date `YYYY-MM-DD` (UTC) |
| `price_usd` | REAL | — | Closing price in USD |
| `market_cap` | REAL | — | Market capitalisation in USD |
| `total_volume` | REAL | — | 24h trading volume in USD |

**Source:** `GET /coins/{id}/market_chart?days=365&interval=daily`  
**Write:** `INSERT OR REPLACE` — idempotent, ~366 rows per coin  
**Volume:** ~1,826 rows (366 days × 5 coins)

### `market_current` — live snapshots

| Column | Type | Description |
|--------|------|-------------|
| `record_id` | INTEGER PK | Surrogate key |
| `crypto_id` | TEXT FK | → `cryptocurrencies.id` |
| `collected_at` | DATETIME | Fetch timestamp (UTC) |
| `price_usd` | REAL | Current price |
| `market_cap` | REAL | Market cap |
| `total_volume` | REAL | 24h volume |
| `high_24h` / `low_24h` | REAL | 24h min/max price |
| `price_change_24h` | REAL | 24h price change (USD) |
| `price_change_percentage_24h` | REAL | 24h price change (%) |
| `price_change_percentage_7d` | REAL | 7d price change (%) |
| `market_cap_rank` | INTEGER | Global rank |
| `circulating_supply` | REAL | Circulating supply |
| `total_supply` / `max_supply` | REAL | Total / max supply |
| `ath` | REAL | All-time high (USD) |
| `ath_change_percentage` | REAL | Distance from ATH (%) |

**Source:** `GET /coins/markets?ids=…`  
**Write:** `INSERT` (append-only — each fetch adds new rows)

---

## Integrity Constraints

| Constraint | Table | Definition | Purpose |
|------------|-------|------------|---------|
| PRIMARY KEY | all | `id` or `record_id` | Unique row identification |
| FOREIGN KEY | `market_snapshots`, `market_current` | `crypto_id → cryptocurrencies.id` | No orphan records |
| UNIQUE | `market_snapshots` | `(crypto_id, snapshot_date)` | One record per coin per day |
| NOT NULL | `market_snapshots` | `crypto_id`, `snapshot_date` | Natural key always present |
| NOT NULL | `market_current` | `crypto_id`, `collected_at` | Snapshot identification |

---

## Indexes

| Index | Table | Columns | Purpose |
|-------|-------|---------|---------|
| PK autoindex | all | `record_id` / `id` | Primary key lookup |
| `sqlite_autoindex_…` | `market_snapshots` | `(crypto_id, snapshot_date)` | Coin + date range filter (from UNIQUE) |
| `idx_snapshots_date` | `market_snapshots` | `snapshot_date` | Date-only filter |
| `idx_current_collected_at` | `market_current` | `collected_at` | Fetch time filter |

---

## API → Database Mapping

### Historical endpoint: `/coins/{id}/market_chart`

| API Field | Table | DB Column | Transformation |
|-----------|-------|-----------|----------------|
| `prices[i][0]` | `market_snapshots` | `snapshot_date` | `ts_ms / 1000` → `YYYY-MM-DD` UTC |
| `prices[i][1]` | `market_snapshots` | `price_usd` | direct |
| `market_caps[i][1]` | `market_snapshots` | `market_cap` | direct |
| `total_volumes[i][1]` | `market_snapshots` | `total_volume` | direct |
| (URL param) | `market_snapshots` | `crypto_id` | `coin_id` from request |

### Live endpoint: `/coins/markets`

| API Field | Table | DB Column |
|-----------|-------|-----------|
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
| (generated) | `market_current` | `collected_at` | `datetime.utcnow()` |

### Coin lookup

| API Field (`/coins/markets`) | Table | DB Column |
|------------------------------|-------|-----------|
| `id` | `cryptocurrencies` | `id` |
| `symbol` | `cryptocurrencies` | `symbol` (uppercase) |
| `name` | `cryptocurrencies` | `name` |

---

## Normalisation (3NF)

| Table | 1NF | 2NF | 3NF | Notes |
|-------|:---:|:---:|:---:|-------|
| `cryptocurrencies` | ✅ | ✅ | ✅ | Simple lookup table |
| `market_snapshots` | ✅ | ✅ | ✅ | Fact table; no derived columns |
| `market_current` | ✅ | ✅ | ✅ | Raw API values, not derived from other columns |

Coin metadata (`symbol`, `name`) stored only in `cryptocurrencies` — fact tables contain only the `crypto_id` foreign key.

---

## Data Volume (project state)

| Table | Rows | Description |
|-------|------|-------------|
| `cryptocurrencies` | 5 | BTC, ETH, SOL, BNB, XRP |
| `market_snapshots` | ~1,826 | 366 days × 5 coins |
| `market_current` | ~10 | 2 fetches × 5 coins |

---

*Architecture: [`architecture.md`](architecture.md) · Diagrams: [`diagrams.md`](diagrams.md)*
