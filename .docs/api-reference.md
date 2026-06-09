# Referencja API modułów

> Pełna referencja (EN): [`DOCUMENTATION.md` §6](../DOCUMENTATION.md)  
> Raport akademicki: [`SPRAWOZDANIE.md` §6–7](../SPRAWOZDANIE.md)

---

## Moduły w projekcie

| Moduł | Status | Opis |
|-------|--------|------|
| **`app.py`** | **główny** | Aplikacja Streamlit — ETL + 6 stron wizualizacji |
| **`crypto_market_analysis.ipynb`** | **główny** | Notebook — te same funkcje DB/API w 11 etapach |
| `main.py` | legacy | Prosty fetcher JSON (3 monety, bez bazy) |
| `generate_sprawozdanie.py` | narzędzie | Generator raportu DOCX |

---

## `app.py` — aplikacja Streamlit

**Plik:** `app.py` (847 linii)  
**Uruchomienie:** `uv run streamlit run app.py`

### Stałe konfiguracyjne

| Stała | Wartość | Opis |
|-------|---------|------|
| `DB_PATH` | `"crypto_market.db"` | Ścieżka do pliku SQLite |
| `BASE_URL` | `"https://api.coingecko.com/api/v3"` | Bazowy URL CoinGecko API |
| `REQUEST_DELAY` | `10` | Opóźnienie (s) między żądaniami API |
| `COINS` | 5-elementowa lista | Śledzone kryptowaluty (`id`, `symbol`, `name`) |
| `METRIC_MAP` | dict | Mapowanie etykiet → kolumny DataFrame |
| `PERIOD_MAP` | dict | Mapowanie okresów → liczba dni |
| `AGG_MAP` | dict | Mapowanie agregacji → funkcja pandas |

### Funkcje bazy danych

#### `create_database() -> None`

Tworzy 3 tabele i indeksy (`CREATE TABLE IF NOT EXISTS`). Wstawia listę monet (`INSERT OR IGNORE`). Wywoływana przy starcie aplikacji w `main()`.

**Efekty uboczne:** tworzy/aktualizuje `crypto_market.db`.

---

#### `load_snapshots() -> pd.DataFrame`

Ładuje pełny JOIN `market_snapshots` + `cryptocurrencies` do DataFrame.

```sql
SELECT s.snapshot_date, s.price_usd, s.market_cap, s.total_volume,
       c.name, c.symbol
FROM market_snapshots s
JOIN cryptocurrencies c ON s.crypto_id = c.id
ORDER BY s.snapshot_date
```

**Cache:** `@st.cache_data(ttl=60)` — 60 sekund.

---

#### `load_db_stats() -> dict`

Zwraca słownik ze statystykami bazy:
- `cryptocurrencies`, `market_snapshots`, `market_current` — liczba wierszy
- `date_from`, `date_to` — zakres dat w `market_snapshots`

**Cache:** `@st.cache_data(ttl=60)`.

---

### Funkcje API / ETL

#### `fetch_market_chart(coin_id: str, days: int = 365) -> dict`

Pobiera dane historyczne z CoinGecko.

```
GET /coins/{coin_id}/market_chart?vs_currency=usd&days=365&interval=daily
```

**Zwraca:** `{prices: [[ts_ms, value], …], market_caps: [...], total_volumes: [...]}`  
**Wyjątki:** `HTTPError`, `Timeout`, `ConnectionError`

---

#### `fetch_markets_current() -> list`

Pobiera bieżące dane rynkowe dla wszystkich śledzonych monet.

```
GET /coins/markets?vs_currency=usd&ids=bitcoin,ethereum,solana,binancecoin,ripple&...
```

**Zwraca:** lista 5 słowników (po jednym na monetę).

---

#### `store_market_chart(coin_id: str, data: dict) -> int`

Parsuje odpowiedź API, konwertuje timestampy na daty i zapisuje do `market_snapshots`.

```python
INSERT OR REPLACE INTO market_snapshots
    (crypto_id, snapshot_date, price_usd, market_cap, total_volume)
VALUES (?, ?, ?, ?, ?)
```

**Zwraca:** liczba zapisanych wierszy (~366).

---

#### `store_current(data: list) -> None`

Wstawia bieżący snapshot do `market_current` z `collected_at = UTC now`.

```python
INSERT INTO market_current (crypto_id, collected_at, price_usd, ...)
VALUES (?, ?, ?, ...)
```

**Efekt:** 5 nowych wierszy (append-only).

---

### Funkcje pomocnicze

#### `fmt_pct(x: float) -> str`

Formatuje liczbę jako `▲ 3.14%` lub `▼ 1.23%`. Zwraca `"N/A"` dla NaN.

#### `build_dashboard_df(df: pd.DataFrame) -> pd.DataFrame`

Oblicza zmiany procentowe 24h/7d/30d z historycznych snapshotów. Zwraca DataFrame gotowy do dashboardu.

---

### Strony Streamlit

| Funkcja | Strona | Opis |
|---------|--------|------|
| `page_overview()` | Overview | KPI bazy, zakres dat, tabela nawigacji |
| `page_data_collection()` | Data Collection | Przyciski pobierania historycznego i live; podsumowanie DB |
| `page_time_series()` | Time Series | Wykres liniowy; 6 filtrów sidebar |
| `page_quantitative()` | Quantitative Analysis | Bar / Box / Violin; 6 filtrów |
| `page_market_dashboard()` | Market Dashboard | KPI, tabela, grouped bar, heatmap, treemap |
| `page_correlation()` | Correlation & Volatility | Macierz korelacji, zmienność, korelacja z BTC |

#### `main() -> None`

Punkt wejścia Streamlit. Wywołuje `create_database()`, konfiguruje sidebar i routuje do wybranej strony.

---

## `main.py` — legacy fetcher JSON

> **Status: legacy** — zastąpiony przez `app.py`. Pozostawiony jako referencja początkowego etapu projektu.

**Plik:** `main.py` (102 linie)  
**Uruchomienie:** `uv run python main.py`

### `main() -> None`

Pobiera 3 monety (BTC, ETH, SOL) z `/coins/markets` i zapisuje odpowiedź do `coingecko_response.json`.

**Parametry HTTP:**

| Parametr | Wartość |
|----------|---------|
| `vs_currency` | `"usd"` |
| `ids` | `"bitcoin,ethereum,solana"` |
| `price_change_percentage` | `"24h,7d"` |

**Efekty uboczne:**
- 1 żądanie HTTP GET (timeout 10s)
- Nadpisuje `coingecko_response.json`
- Wypisuje kod HTTP i nazwy pól na stdout

**Wyjątki:** `HTTPError`, `ConnectionError`, `Timeout`, `OSError`

---

## Generowanie dokumentacji HTML (pydoc)

```bash
# Dokumentacja legacy modułu main.py
uv run python -m pydoc -w main
# → main.html

# Podgląd w przeglądarce
uv run python -m pydoc -p 1234
```

Statyczna dokumentacja HTML: [`docs/index.html`](../docs/index.html)

---

*Architektura: [`architecture.md`](architecture.md) · Model danych: [`data-model.md`](data-model.md)*
