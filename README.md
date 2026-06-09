# Cryptocurrency Market Analysis System

> **Zaawansowane Bazy Danych — projekt końcowy**  
> Automatyka i Robotyka II Stopnia · Informatyka w Sterowaniu i Zarządzaniu

**Zespół:** Michał Dusza · Szymon Bugajski · Mateusz Basiura

---

## Opis

System **automatycznie pobiera** dane rynkowe kryptowalut z publicznego API [CoinGecko](https://www.coingecko.com/en/api), **przechowuje je w relacyjnej bazie SQLite** (`crypto_market.db`) i prezentuje w postaci **interaktywnych wizualizacji** — w notebooku Jupyter oraz w aplikacji webowej Streamlit.

```
CoinGecko API  ──►  app.py / notebook  ──►  crypto_market.db  ──►  Plotly charts
```

**Śledzone monety:** BTC · ETH · SOL · BNB · XRP (5 monet)  
**Dane historyczne:** 365 dni × 5 monet ≈ 1 826 rekordów w `market_snapshots`  
**Python:** 3.13 · **Menedżer pakietów:** [uv](https://docs.astral.sh/uv/)

---

## Szybki start

```powershell
# 1. Zainstaluj zależności
uv sync

# 2a. Uruchom aplikację webową (zalecane)
uv run streamlit run app.py
# → http://localhost:8501

# 2b. Lub uruchom notebook analityczny
uv run jupyter lab crypto_market_analysis.ipynb
```

> Przy pierwszym uruchomieniu przejdź do strony **Data Collection** w Streamlit (lub Stage 5 w notebooku), aby pobrać dane z API do bazy.

---

## Funkcjonalności

| Moduł | Co robi |
|-------|---------|
| **Pozyskiwanie danych** | 365-dniowa historia (cena, kapitalizacja, wolumen) + bieżący snapshot rynkowy |
| **Baza danych** | 3 tabele SQLite: `cryptocurrencies`, `market_snapshots`, `market_current` — FK, UNIQUE, indeksy, 3NF |
| **Szeregi czasowe** | Wykres liniowy z filtrowaniem po monecie, dacie, metryce; średnia krocząca; skala log |
| **Analiza ilościowa** | Wykres słupkowy / pudełkowy / skrzypcowy z agregacjami (mean, max, min, std) |
| **Dashboard rynkowy** | KPI, tabela, grouped bar, heatmapa zmian, treemap kapitalizacji |
| **Korelacja i zmienność** | Macierz korelacji, roczna zmienność, krocząca korelacja z BTC |

---

## Struktura repozytorium

```
project/
│
├── app.py                          # Główna aplikacja Streamlit (ETL + 6 stron UI)
├── crypto_market_analysis.ipynb    # Notebook analityczny (11 etapów)
├── crypto_market.db                  # Baza SQLite (tworzona automatycznie)
│
├── pyproject.toml                    # Zależności projektu (uv)
├── uv.lock                           # Zablokowane wersje pakietów
├── .python-version                   # Python 3.13
│
├── SPRAWOZDANIE.md                   # Raport akademicki (PL) — główny opis projektu
├── DOCUMENTATION.md                  # Dokumentacja techniczna (EN) — DDL, SQL, moduły
├── README.md                         # Ten plik — szybki start i indeks dokumentacji
│
├── .docs/                            # Dokumentacja techniczna (PL, skrócona)
│   ├── README.md                     #   Indeks folderu .docs
│   ├── architecture.md               #   Architektura 3-warstwowa
│   ├── data-model.md                 #   Schemat SQLite + mapowanie API
│   ├── api-reference.md              #   Referencja funkcji app.py i main.py
│   └── diagrams.md                   #   Diagramy Mermaid
│
├── docs/                             # Statyczna dokumentacja HTML
│   ├── index.html                    #   Portal dokumentacji
│   └── main.html                     #   Referencja legacy modułu main.py
│
├── main.py                           # [legacy] Prosty fetcher JSON → coingecko_response.json
├── test.ipynb                        # [legacy] Eksploracyjny notebook API (3 monety)
├── coingecko_response.json           # [legacy] Przykładowa odpowiedź API
│
├── generate_sprawozdanie.py          # Generator raportu DOCX ze SPRAWOZDANIE.md
├── SPRAWOZDANIE.docx                 # Raport Word (wygenerowany)
└── raport_cryptomarket_db.docx       # Starszy raport Word (v0.1)
```

---

## Stos technologiczny

| Komponent | Technologia |
|-----------|-------------|
| Język | Python 3.13 |
| Menedżer pakietów | uv |
| Baza danych | SQLite 3 (stdlib) |
| Źródło danych | CoinGecko API v3 (publiczne) |
| Aplikacja webowa | Streamlit 1.57 |
| Notebook | JupyterLab 4 + ipywidgets 8 |
| Wizualizacja | Plotly 6 |
| Dane | pandas 2.2+ |

---

## Baza danych

```
crypto_market.db
│
├── cryptocurrencies          ← słownik monet (5 wierszy)
│     id TEXT PK · symbol · name
│
├── market_snapshots          ← historia dzienna (~1 826 wierszy)
│     record_id PK · crypto_id FK · snapshot_date
│     price_usd · market_cap · total_volume
│     UNIQUE(crypto_id, snapshot_date)
│     INDEX idx_snapshots_date
│
└── market_current            ← bieżące snapshoty (append-only)
      record_id PK · crypto_id FK · collected_at
      price_usd · market_cap · high_24h · low_24h
      price_change_* · market_cap_rank · supply · ath
      INDEX idx_current_collected_at
```

Szczegóły DDL, ograniczeń i normalizacji → [`SPRAWOZDANIE.md` §4](SPRAWOZDANIE.md) lub [`.docs/data-model.md`](.docs/data-model.md).

---

## Aplikacja Streamlit (`app.py`)

```powershell
uv run streamlit run app.py
```

| Strona | Opis |
|--------|------|
| **Overview** | Statystyki bazy, zakres dat, nawigacja |
| **Data Collection** | Pobieranie danych historycznych i live z CoinGecko |
| **Time Series** | Wykres liniowy (6 filtrów w sidebarze) |
| **Quantitative Analysis** | Bar / Box / Violin (6 filtrów) |
| **Market Dashboard** | KPI · tabela · grouped bar · heatmap · treemap |
| **Correlation & Volatility** | Macierz korelacji · zmienność · korelacja z BTC |

---

## Notebook (`crypto_market_analysis.ipynb`)

| Etap | Opis |
|------|------|
| 1–2 | Środowisko, importy, stałe (`COINS`, `METRIC_MAP`) |
| 3–4 | DDL bazy, wstawienie listy monet |
| 5 | Pobieranie 365-dniowej historii z API + zapis do DB |
| 6–7 | Weryfikacja DB, wczytanie do pandas DataFrame |
| 8 | Szeregi czasowe (ipywidgets + Plotly) |
| 9 | Analiza ilościowa |
| 10 | Dashboard rynkowy |
| 11 | Korelacja i zmienność |

---

## Dokumentacja — co jest do czego

| Plik | Język | Dla kogo | Zawartość |
|------|-------|----------|-----------|
| **[`SPRAWOZDANIE.md`](SPRAWOZDANIE.md)** | PL | Ocena / prezentacja | Pełny raport akademicki: cel, schemat DB, architektura, implementacja, wizualizacje, problemy, wnioski |
| **[`DOCUMENTATION.md`](DOCUMENTATION.md)** | EN | Deweloperzy | DDL, zapytania SQL, przepływ danych, referencja modułów, konfiguracja |
| **[`.docs/`](.docs/)** | PL | Szybki przegląd | Skrócona dokumentacja techniczna podzielona na tematy |
| **[`docs/index.html`](docs/index.html)** | PL | Przeglądarka | Statyczny portal HTML z linkami do wszystkich sekcji |
| **`SPRAWOZDANIE.docx`** | PL | Druk / oddanie | Wygenerowany raport Word (`generate_sprawozdanie.py`) |

### Folder `.docs/` — szczegóły

| Plik | Zawartość |
|------|-----------|
| [`.docs/README.md`](.docs/README.md) | Indeks dokumentacji technicznej |
| [`.docs/architecture.md`](.docs/architecture.md) | 3 warstwy: pozyskiwanie → SQLite → prezentacja |
| [`.docs/data-model.md`](.docs/data-model.md) | Schemat SQLite, mapowanie pól API → kolumny DB |
| [`.docs/api-reference.md`](.docs/api-reference.md) | Funkcje `app.py` (główne) i `main.py` (legacy) |
| [`.docs/diagrams.md`](.docs/diagrams.md) | Diagramy Mermaid: ERD, sekwencji, ETL, architektura |

---

## Pliki legacy (początek projektu)

| Plik | Opis |
|------|------|
| `main.py` | Prosty skrypt: pobiera 3 monety z API → zapisuje `coingecko_response.json` (bez bazy) |
| `test.ipynb` | Eksploracyjny notebook — inspekcja odpowiedzi API |
| `coingecko_response.json` | Przykładowa odpowiedź API (BTC, ETH, SOL) |

Główny system (`app.py` + notebook) zastąpił te pliki — pozostawione jako referencja.

---

## Odświeżanie danych

W Streamlit: strona **Data Collection** → przyciski *Fetch Historical* / *Fetch Live Snapshot*.  
W notebooku: ponownie uruchom **Stage 5** (cell 12).

`INSERT OR REPLACE` na `(crypto_id, snapshot_date)` gwarantuje idempotentny zapis — ponowne pobieranie nie tworzy duplikatów.

---

*Projekt akademicki — Zaawansowane Bazy Danych, Maj 2026.*
