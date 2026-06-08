# CryptoMarket DB — Projekt baz danych

> Ingestion danych rynkowych kryptowalut z API CoinGecko jako źródło do projektowania i zasilania relacyjnej bazy danych.

---

## Spis treści

- [Opis projektu](#opis-projektu)
- [Funkcjonalności](#funkcjonalności)
- [Struktura projektu](#struktura-projektu)
- [Instalacja](#instalacja)
- [Użycie](#użycie)
- [Format danych](#format-danych)
- [Dokumentacja](#dokumentacja)
- [Stos technologiczny](#stos-technologiczny)
- [Roadmap](#roadmap)

---

## Opis projektu

Projekt realizowany w ramach przedmiotu **Bazy Danych** (semestr 7).  
Celem jest zaprojektowanie i zaimplementowanie relacyjnej bazy danych przechowującej historyczne dane rynkowe kryptowalut.

**Faza 1 — Data ingestion (obecna):**  
Skrypt pobiera aktualne notowania Bitcoina, Ethereum i Solany z publicznego REST API [CoinGecko v3](https://api.coingecko.com/api/v3/), serializuje odpowiedź do pliku JSON i wypisuje dostępne pola.

**Docelowy przepływ danych:**

```
CoinGecko API  ──►  main.py  ──►  coingecko_response.json  ──►  [DB schema]  ──►  [SQL queries]
```

---

## Funkcjonalności

| # | Funkcjonalność | Status |
|---|----------------|--------|
| 1 | Pobieranie danych z CoinGecko API | ✅ Gotowe |
| 2 | Zapis odpowiedzi do pliku JSON | ✅ Gotowe |
| 3 | Inspekcja dostępnych pól rekordu | ✅ Gotowe |
| 4 | Projekt schematu relacyjnej bazy danych | 🔜 Planowane |
| 5 | Migracje / DDL (CREATE TABLE) | 🔜 Planowane |
| 6 | Ładowanie danych do bazy (ETL) | 🔜 Planowane |
| 7 | Zapytania analityczne (SQL) | 🔜 Planowane |

---

## Struktura projektu

```
project/
├── .docs/                          # Dokumentacja techniczna
│   ├── architecture.md             #   Architektura systemu
│   ├── data-model.md               #   Model danych (pola API, przyszły schemat)
│   ├── api-reference.md            #   Referencja API modułu (pydoc)
│   └── diagrams.md                 #   Diagramy: sekwencji, klas, przepływu
├── main.py                         # Główny moduł — fetcher danych
├── test.ipynb                      # Notebook eksploracyjny
├── coingecko_response.json         # Przykładowa odpowiedź API (3 monety)
├── pyproject.toml                  # Metadane projektu i zależności (uv)
├── uv.lock                         # Zablokowane wersje zależności
├── .python-version                 # Wymagana wersja Pythona (3.14)
├── .gitignore
└── README.md                       # Ten plik
```

---

## Instalacja

Projekt używa menedżera pakietów [**uv**](https://docs.astral.sh/uv/).

### Wymagania wstępne

- Python ≥ 3.14
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (lub pip)

### Kroki

```bash
# 1. Sklonuj repozytorium
git clone <repo-url>
cd project

# 2. Utwórz środowisko wirtualne i zainstaluj zależności
uv sync

# --- alternatywnie z pip ---
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install requests>=2.33.1
```

---

## Użycie

### Pobierz dane z API

```bash
uv run python main.py
# lub
python main.py
```

**Przykładowe wyjście:**

```
Status code: 200
Zapisano dane do pliku: coingecko_response.json

Dostępne pola dla pierwszego rekordu:
- id
- symbol
- name
- image
- current_price
- market_cap
- market_cap_rank
- fully_diluted_valuation
- total_volume
- high_24h
- low_24h
- price_change_24h
- price_change_percentage_24h
- market_cap_change_24h
- market_cap_change_percentage_24h
- circulating_supply
- total_supply
- max_supply
- ath
- ath_change_percentage
- ath_date
- atl
- atl_change_percentage
- atl_date
- roi
- last_updated
- price_change_percentage_24h_in_currency
- price_change_percentage_7d_in_currency
```

### Notebook eksploracyjny

```bash
uv run jupyter notebook test.ipynb
```

### Generowanie dokumentacji pydoc

```bash
uv run python -m pydoc -w main
# Tworzy plik main.html z dokumentacją modułu
```

---

## Format danych

Plik `coingecko_response.json` zawiera tablicę obiektów JSON, po jednym na monetę.

**Przykładowy rekord (Bitcoin):**

```json
{
    "id": "bitcoin",
    "symbol": "btc",
    "name": "Bitcoin",
    "current_price": 76182,
    "market_cap": 1525437558394,
    "market_cap_rank": 1,
    "high_24h": 77432,
    "low_24h": 75706,
    "price_change_percentage_24h": -0.80695,
    "price_change_percentage_7d_in_currency": 0.4987149980680044,
    "last_updated": "2026-04-28T17:46:16.705Z"
}
```

Pełny opis wszystkich pól — zob. [`.docs/data-model.md`](.docs/data-model.md).

---

## Dokumentacja

Pełna dokumentacja techniczna znajduje się w folderze [`.docs/`](.docs/):

| Plik | Zawartość |
|------|-----------|
| [`.docs/architecture.md`](.docs/architecture.md) | Architektura systemu, opis warstw, stos technologiczny |
| [`.docs/data-model.md`](.docs/data-model.md) | Schemat danych API, typy pól, opis semantyczny |
| [`.docs/api-reference.md`](.docs/api-reference.md) | Referencja funkcji i modułów (format pydoc) |
| [`.docs/diagrams.md`](.docs/diagrams.md) | Diagramy Mermaid: sekwencji, klas, przepływu |

---

## Stos technologiczny

| Komponent | Technologia | Wersja |
|-----------|-------------|--------|
| Język | Python | ≥ 3.14 |
| HTTP client | requests | ≥ 2.33.1 |
| Menedżer pakietów | uv | latest |
| Źródło danych | CoinGecko API v3 | public |
| Notebook | Jupyter | — |

---

## Roadmap

```
v0.1  ✅  Data ingestion — fetch & save JSON
v0.2  🔜  Schema design — DDL dla PostgreSQL/SQLite
v0.3  🔜  ETL pipeline — załadowanie JSON do bazy
v0.4  🔜  Analytical queries — SQL raportowanie
v0.5  🔜  Scheduling — cykliczne pobieranie danych (cron / APScheduler)
```

---

*Projekt akademicki — Wydział Informatyki, semestr 7, przedmiot: Bazy Danych.*
