# Architektura systemu

## Przegląd

Projekt realizuje **warstwę ingestion danych** dla relacyjnej bazy danych notowań kryptowalut.  
Pobiera dane z zewnętrznego REST API, normalizuje je do formatu JSON i zapisuje lokalnie — stanowiąc punkt wejściowy dla dalszego ETL do bazy.

---

## Warstwy systemu

```
┌──────────────────────────────────────────────────────────────┐
│                     WARSTWA ZEWNĘTRZNA                       │
│                                                              │
│   ┌──────────────────────────────────────────────────────┐   │
│   │          CoinGecko REST API v3                       │   │
│   │   GET /api/v3/coins/markets?vs_currency=usd&...      │   │
│   └──────────────────────────────────────────────────────┘   │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTP/HTTPS (JSON)
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                   WARSTWA INGESTION (Python)                  │
│                                                              │
│   ┌──────────────────────────────────────────────────────┐   │
│   │                    main.py                           │   │
│   │                                                      │   │
│   │   main()                                             │   │
│   │   ├── buduje parametry zapytania                     │   │
│   │   ├── wykonuje requests.get(url, params, timeout)    │   │
│   │   ├── waliduje status HTTP (raise_for_status)        │   │
│   │   ├── parsuje JSON → lista słowników                 │   │
│   │   └── serializuje do pliku (json.dumps + write_text) │   │
│   └──────────────────────────────────────────────────────┘   │
└──────────────────────────────┬───────────────────────────────┘
                               │ zapis pliku
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                   WARSTWA PERSYSTENCJI (lokalny FS)           │
│                                                              │
│   coingecko_response.json                                    │
│   (sformatowany JSON, ~96 linii, 3 rekordy)                  │
└──────────────────────────────┬───────────────────────────────┘
                               │ [planowane]
                               ▼
┌──────────────────────────────────────────────────────────────┐
│               WARSTWA BAZY DANYCH (planowana)                 │
│                                                              │
│   PostgreSQL / SQLite                                        │
│   ├── tabela: coins                                          │
│   ├── tabela: market_snapshots                               │
│   └── tabela: roi_data                                       │
└──────────────────────────────────────────────────────────────┘
```

---

## Przepływ danych (Data Flow)

| Krok | Komponent | Akcja | Artefakt wyjściowy |
|------|-----------|-------|--------------------|
| 1 | `main.py` | Buduje URL + query params | `dict` params |
| 2 | `requests` | `GET /coins/markets` → timeout 10s | `Response` object |
| 3 | `main.py` | `raise_for_status()` — walidacja kodu HTTP | (wyjątek lub kontynuacja) |
| 4 | `main.py` | `response.json()` — deserializacja | `list[dict]` |
| 5 | `json` | `json.dumps(data, indent=4)` | `str` (sformatowany JSON) |
| 6 | `pathlib.Path` | `write_text(...)` | `coingecko_response.json` |
| 7 | `main.py` | Wypisuje pola pierwszego rekordu | stdout |

---

## Komponenty i odpowiedzialności

### `main.py` — moduł ingestion

**Odpowiedzialności:**
- Konfiguracja i wykonanie zapytania HTTP do CoinGecko API
- Obsługa błędów sieciowych i HTTP
- Serializacja danych do formatu JSON
- Zapis pliku wyjściowego

**Nie odpowiada za:**
- Parsowanie / transformację poszczególnych pól
- Ładowanie do bazy danych
- Walidację wartości (zakres, format daty itp.)
- Harmonogramowanie (cron / scheduler)

### `test.ipynb` — notebook eksploracyjny

**Cel:** szybka inspekcja odpowiedzi API bez uruchamiania pełnego skryptu.  
Różnice względem `main.py`:
- brak `timeout` w zapytaniu
- brak `raise_for_status()`
- brak zapisu do pliku
- wypisuje pełny pierwszy rekord (JSON)

---

## Stos technologiczny

| Kategoria | Technologia | Uzasadnienie |
|-----------|-------------|--------------|
| Język | Python 3.14 | Bogaty ekosystem, szybki prototyping |
| HTTP client | `requests` 2.33.1 | Najpopularniejszy klient HTTP w Pythonie |
| Serializacja | `json` (stdlib) | Brak zewnętrznych zależności |
| Ścieżki plików | `pathlib.Path` (stdlib) | Cross-platform, idiomatyczny Python |
| Zarządzanie pakietami | `uv` | Szybki, nowoczesny resolver zależności |
| Źródło danych | CoinGecko API v3 | Bezpłatne, publiczne API notowań krypto |
| Notebook | Jupyter | Eksploracja danych |

---

## Obsługa błędów

| Sytuacja | Mechanizm | Skutek |
|----------|-----------|--------|
| Kod HTTP 4xx / 5xx | `response.raise_for_status()` | `HTTPError` — skrypt kończy działanie z traceback |
| Brak połączenia sieciowego | `requests.exceptions.ConnectionError` | Propagacja wyjątku |
| Timeout (> 10s) | `timeout=10` w `requests.get` | `requests.exceptions.Timeout` |
| Błąd zapisu pliku | `OSError` z `Path.write_text` | Propagacja wyjątku |

---

## Ograniczenia obecnej implementacji

1. **Brak persystencji historycznej** — każde wywołanie nadpisuje `coingecko_response.json`.
2. **Hardkodowane monety** — lista `bitcoin,ethereum,solana` jest zakodowana na stałe.
3. **Brak walidacji danych** — pola nie są sprawdzane pod kątem poprawności typów / zakresów.
4. **Brak harmonogramowania** — skrypt musi być uruchamiany ręcznie.
5. **Brak bazy danych** — dane nie trafiają do RDBMS.

---

## Planowane rozszerzenia

```
main.py
  ├── fetch_markets(coins: list[str], currency: str) -> list[dict]   # parametryzacja
  └── save_to_json(data, path)                                        # wydzielenie I/O

etl.py  [planowane]
  ├── connect_db() -> Connection
  ├── upsert_coin(conn, record: dict) -> None
  └── upsert_snapshot(conn, record: dict) -> None

scheduler.py  [planowane]
  └── run_every(interval_minutes: int) -> None
```

---

*Szczegółowe diagramy sekwencji i klas — zob. [`diagrams.md`](diagrams.md).*
