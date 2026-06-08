# Model danych

## Źródło danych

**API:** CoinGecko v3 — `GET /api/v3/coins/markets`  
**Monety:** Bitcoin (`btc`), Ethereum (`eth`), Solana (`sol`)  
**Waluta bazowa:** USD  
**Plik lokalny:** `coingecko_response.json`

---

## Schemat odpowiedzi API

Odpowiedź to tablica (`array`) obiektów JSON — jeden obiekt na monetę.

### Pola rekordu

| Pole | Typ JSON | Nullable | Opis | Przykład (BTC) |
|------|----------|----------|------|----------------|
| `id` | `string` | ✗ | Unikalny identyfikator monety w CoinGecko | `"bitcoin"` |
| `symbol` | `string` | ✗ | Ticker giełdowy (lowercase) | `"btc"` |
| `name` | `string` | ✗ | Pełna nazwa | `"Bitcoin"` |
| `image` | `string` | ✗ | URL do logo (PNG, large) | `"https://coin-images..."` |
| `current_price` | `number` | ✗ | Aktualna cena w USD | `76182` |
| `market_cap` | `number` | ✗ | Kapitalizacja rynkowa (USD) | `1 525 437 558 394` |
| `market_cap_rank` | `integer` | ✗ | Pozycja w rankingu market cap | `1` |
| `fully_diluted_valuation` | `number` | ✓ | FDV — wycena przy max_supply w obiegu | `1 525 438 929 779` |
| `total_volume` | `number` | ✗ | Wolumen obrotu 24h (USD) | `34 007 864 832` |
| `high_24h` | `number` | ✗ | Najwyższa cena w ciągu 24h (USD) | `77 432` |
| `low_24h` | `number` | ✗ | Najniższa cena w ciągu 24h (USD) | `75 706` |
| `price_change_24h` | `number` | ✗ | Zmiana ceny 24h (wartość bezwzględna, USD) | `-619.75` |
| `price_change_percentage_24h` | `number` | ✗ | Zmiana ceny 24h (procent) | `-0.80695` |
| `market_cap_change_24h` | `number` | ✗ | Zmiana market cap 24h (USD) | `-12 759 531 947` |
| `market_cap_change_percentage_24h` | `number` | ✗ | Zmiana market cap 24h (procent) | `-0.82951` |
| `circulating_supply` | `number` | ✗ | Liczba monet aktualnie w obiegu | `20 022 003.0` |
| `total_supply` | `number` | ✓ | Całkowita istniejąca podaż | `20 022 021.0` |
| `max_supply` | `number` | ✓ | Maksymalna możliwa podaż | `21 000 000.0` |
| `ath` | `number` | ✗ | All-time high (USD) | `126 080` |
| `ath_change_percentage` | `number` | ✗ | Odległość od ATH (%) | `-39.57641` |
| `ath_date` | `string` (ISO 8601) | ✗ | Data i czas ATH | `"2025-10-06T18:57:42.558Z"` |
| `atl` | `number` | ✗ | All-time low (USD) | `67.81` |
| `atl_change_percentage` | `number` | ✗ | Wzrost od ATL (%) | `112247.90356` |
| `atl_date` | `string` (ISO 8601) | ✗ | Data i czas ATL | `"2013-07-06T00:00:00.000Z"` |
| `roi` | `object` \| `null` | ✓ | Return on Investment (tylko dla ETH) | `{times, currency, percentage}` |
| `last_updated` | `string` (ISO 8601) | ✗ | Czas ostatniej aktualizacji danych | `"2026-04-28T17:46:16.705Z"` |
| `price_change_percentage_24h_in_currency` | `number` | ✗ | Zmiana ceny 24h w walucie zapytania | `-0.8069524492506842` |
| `price_change_percentage_7d_in_currency` | `number` | ✗ | Zmiana ceny 7d w walucie zapytania | `0.4987149980680044` |

### Struktura pola `roi` (tylko Ethereum)

```json
{
    "times": 39.215005359380605,
    "currency": "btc",
    "percentage": 3921.5005359380607
}
```

| Podpole | Typ | Opis |
|---------|-----|------|
| `times` | `number` | Wielokrotność zwrotu (np. 39× zwrot) |
| `currency` | `string` | Waluta bazowa ROI |
| `percentage` | `number` | Procentowy zwrot z inwestycji |

---

## Przykładowe dane

### Bitcoin

```json
{
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin",
    "current_price": 76182,
    "market_cap": 1525437558394,
    "market_cap_rank": 1,
    "circulating_supply": 20022003.0,
    "max_supply": 21000000.0,
    "ath": 126080,
    "atl": 67.81,
    "roi": null,
    "last_updated": "2026-04-28T17:46:16.705Z",
    "price_change_percentage_24h_in_currency": -0.8069524492506842,
    "price_change_percentage_7d_in_currency": 0.4987149980680044
}
```

### Ethereum (z polem roi)

```json
{
    "id": "ethereum",
    "symbol": "eth",
    "name": "Ethereum",
    "current_price": 2291.26,
    "market_cap": 276468152043,
    "market_cap_rank": 2,
    "max_supply": null,
    "roi": {
        "times": 39.215005359380605,
        "currency": "btc",
        "percentage": 3921.5005359380607
    },
    "last_updated": "2026-04-28T17:46:16.654Z"
}
```

---

## Proponowany schemat relacyjnej bazy danych

Poniżej zaproponowany podział na tabele dla PostgreSQL / SQLite.

### Tabela `coins`

Dane statyczne / wolno zmieniające się — jeden wiersz na monetę.

```sql
CREATE TABLE coins (
    id          TEXT        PRIMARY KEY,   -- "bitcoin", "ethereum", "solana"
    symbol      TEXT        NOT NULL,      -- "btc", "eth", "sol"
    name        TEXT        NOT NULL,      -- "Bitcoin"
    image_url   TEXT,                      -- URL do logo
    max_supply  NUMERIC,                   -- NULL dla ETH, SOL
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### Tabela `market_snapshots`

Dane czasowe — jeden wiersz na (monetę, chwilę) — wstawiane przy każdym pobraniu.

```sql
CREATE TABLE market_snapshots (
    snapshot_id                     BIGSERIAL   PRIMARY KEY,
    coin_id                         TEXT        NOT NULL REFERENCES coins(id),
    fetched_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated                    TIMESTAMPTZ NOT NULL,

    -- ceny
    current_price                   NUMERIC     NOT NULL,
    high_24h                        NUMERIC,
    low_24h                         NUMERIC,

    -- kapitalizacja i wolumen
    market_cap                      BIGINT,
    market_cap_rank                 INTEGER,
    fully_diluted_valuation         BIGINT,
    total_volume                    BIGINT,

    -- podaż
    circulating_supply              NUMERIC,
    total_supply                    NUMERIC,

    -- zmiany 24h
    price_change_24h                        NUMERIC,
    price_change_percentage_24h             NUMERIC,
    market_cap_change_24h                   NUMERIC,
    market_cap_change_percentage_24h        NUMERIC,

    -- zmiany w walucie zapytania
    price_change_pct_24h_in_currency        NUMERIC,
    price_change_pct_7d_in_currency         NUMERIC,

    -- ATH / ATL
    ath                     NUMERIC,
    ath_change_percentage   NUMERIC,
    ath_date                TIMESTAMPTZ,
    atl                     NUMERIC,
    atl_change_percentage   NUMERIC,
    atl_date                TIMESTAMPTZ
);
```

### Tabela `roi_data`

Dane ROI — obecne tylko dla Ethereum; relacja 0..1 do `market_snapshots`.

```sql
CREATE TABLE roi_data (
    roi_id      BIGSERIAL   PRIMARY KEY,
    snapshot_id BIGINT      NOT NULL REFERENCES market_snapshots(snapshot_id),
    times       NUMERIC     NOT NULL,
    currency    TEXT        NOT NULL,
    percentage  NUMERIC     NOT NULL
);
```

### Diagram ERD (tekstowy)

```
coins (1) ─────────── (N) market_snapshots (1) ─── (0..1) roi_data
  id (PK)                   snapshot_id (PK)                roi_id (PK)
  symbol                    coin_id (FK)                    snapshot_id (FK)
  name                      fetched_at                      times
  image_url                 last_updated                    currency
  max_supply                current_price                   percentage
                            market_cap
                            ...
```

---

## Mapowanie pól API → kolumny DB

| Pole API | Tabela | Kolumna DB | Uwagi |
|----------|--------|------------|-------|
| `id` | `coins` | `id` | PK |
| `symbol` | `coins` | `symbol` | |
| `name` | `coins` | `name` | |
| `image` | `coins` | `image_url` | |
| `max_supply` | `coins` | `max_supply` | NULL dla ETH, SOL |
| `current_price` | `market_snapshots` | `current_price` | |
| `market_cap` | `market_snapshots` | `market_cap` | |
| `last_updated` | `market_snapshots` | `last_updated` | ISO 8601 → TIMESTAMPTZ |
| `roi.times` | `roi_data` | `times` | tylko gdy `roi != null` |
| `roi.currency` | `roi_data` | `currency` | |
| `roi.percentage` | `roi_data` | `percentage` | |

---

*Szczegółowe diagramy — zob. [`diagrams.md`](diagrams.md).*
