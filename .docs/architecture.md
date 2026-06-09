# Architektura systemu

> Pełny opis akademicki: [`SPRAWOZDANIE.md` §5](../SPRAWOZDANIE.md)  
> Wersja angielska: [`DOCUMENTATION.md` §1](../DOCUMENTATION.md)

---

## Przegląd

System Analizy Rynku Kryptowalut to kompletna aplikacja end-to-end:

1. **Pobiera** dane historyczne i bieżące z CoinGecko REST API v3.
2. **Przechowuje** je w znormalizowanej bazie SQLite (`crypto_market.db`).
3. **Prezentuje** w interaktywnych wizualizacjach Plotly — przez Streamlit (`app.py`) lub Jupyter (`crypto_market_analysis.ipynb`).

---

## Architektura 3-warstwowa

```
┌─────────────────────────────────────────────────────────┐
│                   WARSTWA PREZENTACJI                    │
│                                                         │
│   📓 crypto_market_analysis.ipynb    🌐 app.py          │
│   11 etapów · ipywidgets             6 stron Streamlit │
│   Plotly charts                      Plotly charts       │
└──────────────────────┬──────────────────────────────────┘
                       │ pd.read_sql (SELECT + JOIN)
┌──────────────────────▼──────────────────────────────────┐
│                   WARSTWA PRZECHOWYWANIA                 │
│                                                         │
│         🗄️  SQLite 3 — crypto_market.db                 │
│         cryptocurrencies | market_snapshots              │
│         market_current                                  │
└──────────────────────┬──────────────────────────────────┘
                       │ INSERT OR REPLACE / INSERT
┌──────────────────────▼──────────────────────────────────┐
│                   WARSTWA POZYSKIWANIA DANYCH            │
│                                                         │
│   fetch_market_chart()        fetch_markets_current()   │
│   /coins/{id}/market_chart    /coins/markets            │
│               ↑                        ↑                │
│         CoinGecko Public REST API v3                    │
└─────────────────────────────────────────────────────────┘
```

---

## Komponenty

### `app.py` — główna aplikacja (Streamlit)

**Odpowiedzialności:**
- Inicjalizacja bazy (`create_database()`)
- Pobieranie danych z API (`fetch_market_chart`, `fetch_markets_current`)
- Zapis do SQLite (`store_market_chart`, `store_current`)
- Odczyt i cache danych (`load_snapshots`, `load_db_stats`)
- 6 stron wizualizacji (Overview, Data Collection, Time Series, Quantitative, Dashboard, Correlation)

**Uruchomienie:** `uv run streamlit run app.py` → `http://localhost:8501`

### `crypto_market_analysis.ipynb` — notebook analityczny

**Odpowiedzialności:**
- Te same funkcje DB/API co `app.py` (zduplikowane w komórkach)
- 11 etapów: od DDL przez ETL po wizualizacje z ipywidgets
- Środowisko eksploracji danych bez serwera webowego

**Uruchomienie:** `uv run jupyter lab crypto_market_analysis.ipynb`

### `crypto_market.db` — baza SQLite

- Tworzona automatycznie przy pierwszym uruchomieniu `app.py` lub notebooka (Stage 3)
- 3 tabele, klucze obce, UNIQUE, 2 jawne indeksy
- Plik binarny w katalogu projektu (nie commitowany do repo w pełnej wersji)

### Pliki legacy

| Plik | Rola |
|------|------|
| `main.py` | Prosty fetcher: 3 monety → `coingecko_response.json` (bez bazy) |
| `test.ipynb` | Eksploracyjna inspekcja odpowiedzi API |
| `coingecko_response.json` | Przykładowa odpowiedź `/coins/markets` |

---

## Przepływ danych

### Pobieranie historyczne

| Krok | Komponent | Akcja |
|------|-----------|-------|
| 1 | UI (Streamlit / notebook) | Użytkownik inicjuje pobieranie |
| 2 | `fetch_market_chart(coin_id, days=365)` | `GET /coins/{id}/market_chart` |
| 3 | API | Zwraca `{prices, market_caps, total_volumes}` jako tablice `[ts_ms, value]` |
| 4 | `store_market_chart()` | Konwersja `ts_ms` → `YYYY-MM-DD` (UTC) |
| 5 | SQLite | `INSERT OR REPLACE INTO market_snapshots` (bulk `executemany`) |
| 6 | `time.sleep(10)` | Opóźnienie między monetami (rate limit) |
| 7 | Powtórz | Dla każdej z 5 monet |

### Pobieranie bieżącego snapshotu

| Krok | Komponent | Akcja |
|------|-----------|-------|
| 1 | `fetch_markets_current()` | `GET /coins/markets?ids=bitcoin,ethereum,solana,binancecoin,ripple` |
| 2 | API | Zwraca listę 5 obiektów z danymi live |
| 3 | `store_current()` | `INSERT INTO market_current` z `collected_at = UTC now` |

### Odczyt do wizualizacji

| Krok | Komponent | Akcja |
|------|-----------|-------|
| 1 | `load_snapshots()` | `SELECT … FROM market_snapshots JOIN cryptocurrencies` |
| 2 | pandas | `pd.read_sql` → DataFrame |
| 3 | Plotly | Filtrowanie, agregacja, renderowanie wykresu |

---

## Kluczowe decyzje projektowe

| Decyzja | Uzasadnienie |
|---------|--------------|
| **SQLite** | Zero konfiguracji, jeden plik, pełne SQL + FK + indeksy — idealne dla projektu lokalnego |
| **INSERT OR REPLACE** | Idempotentny zapis historyczny — ponowne pobieranie nie duplikuje wierszy |
| **`executemany` + `?`** | Bezpieczne parametryzowane zapytania — ochrona przed SQL injection |
| **`@st.cache_data(ttl=60)`** | Cache odczytu DB w Streamlit — mniej zapytań przy nawigacji |
| **`uv run`** | Automatyczne użycie `.venv` bez ręcznej aktywacji |
| **Oddzielenie ETL od UI** | Notebook i Streamlit czytają z tej samej bazy — warstwy niezależne |

---

## Stos technologiczny

| Warstwa | Technologie |
|---------|-------------|
| Język | Python 3.13 |
| Pakiety | uv (`pyproject.toml` + `uv.lock`) |
| HTTP | requests 2.33+ |
| Baza | sqlite3 (stdlib) |
| Dane | pandas 2.2+ |
| Wykresy | Plotly 6.7+ |
| Web UI | Streamlit 1.57+ |
| Notebook | JupyterLab 4 + ipywidgets 8.1+ |
| API | CoinGecko v3 (publiczne, bez klucza) |

---

## Obsługa błędów

| Sytuacja | Mechanizm | Skutek |
|----------|-----------|--------|
| HTTP 4xx/5xx | `response.raise_for_status()` | `HTTPError` — komunikat w UI |
| HTTP 429 (rate limit) | Obsługa w warstwie UI | Komunikat „spróbuj ponownie za chwilę” |
| Timeout (>20s) | `timeout=20` w `requests.get` | `Timeout` exception |
| Brak sieci | `ConnectionError` | Komunikat błędu w Streamlit / traceback w notebooku |
| Pusta baza | Sprawdzenie w UI | Strony analiz pokazują komunikat „brak danych” |

---

## Ograniczenia

1. **Rate limit API** — 10 s opóźnienia między żądaniami; pełne pobieranie historyczne trwa ~50 s.
2. **Lokalna baza** — SQLite nie obsługuje współbieżnych zapisów z wielu procesów.
3. **Brak harmonogramowania** — dane pobierane ręcznie (przycisk w UI lub re-run notebooka).
4. **5 monet hardkodowanych** — lista `COINS` w `app.py` i notebooku.
5. **Brak autentykacji** — aplikacja Streamlit dostępna lokalnie bez logowania.

---

*Diagramy: [`diagrams.md`](diagrams.md) · Schemat DB: [`data-model.md`](data-model.md)*
