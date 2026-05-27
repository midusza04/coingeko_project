# Sprawozdanie z projektu — System Analizy Rynku Kryptowalut

---

| | |
|---|---|
| **Przedmiot** | Zaawansowane Bazy Danych |
| **Kierunek** | Automatyka i Robotyka II Stopnia |
| **Specjalność** | Informatyka w Sterowaniu i Zarządzaniu |
| **Autorzy** | Michał Dusza · Szymon Bugajski · Mateusz Basiura |
| **Data** | Maj 2026 |

---

## Spis treści

1. [Wstęp i cel projektu](#1-wstęp-i-cel-projektu)
2. [Zakres funkcjonalny](#2-zakres-funkcjonalny)
3. [Zastosowane technologie](#3-zastosowane-technologie)
4. [Projekt bazy danych](#4-projekt-bazy-danych)
   - 4.1 [Model konceptualny (ERD)](#41-model-konceptualny-erd)
   - 4.2 [Opis tabel](#42-opis-tabel)
   - 4.3 [Ograniczenia integralności](#43-ograniczenia-integralności)
   - 4.4 [Indeksy i optymalizacja zapytań](#44-indeksy-i-optymalizacja-zapytań)
   - 4.5 [Normalizacja](#45-normalizacja)
5. [Architektura systemu](#5-architektura-systemu)
6. [Implementacja — warstwa danych](#6-implementacja--warstwa-danych)
   - 6.1 [Inicjalizacja bazy danych](#61-inicjalizacja-bazy-danych)
   - 6.2 [Pobieranie danych z API](#62-pobieranie-danych-z-api)
   - 6.3 [Zapis i odczyt danych](#63-zapis-i-odczyt-danych)
7. [Implementacja — warstwa prezentacji](#7-implementacja--warstwa-prezentacji)
   - 7.1 [Notebook Jupyter (11 etapów)](#71-notebook-jupyter-11-etapów)
   - 7.2 [Aplikacja webowa Streamlit (6 stron)](#72-aplikacja-webowa-streamlit-6-stron)
8. [Opis analiz i wizualizacji](#8-opis-analiz-i-wizualizacji)
9. [Dane zebrane w projekcie](#9-dane-zebrane-w-projekcie)
10. [Instrukcja uruchomienia](#10-instrukcja-uruchomienia)
11. [Napotkane problemy i rozwiązania](#11-napotkane-problemy-i-rozwiązania)
12. [Wnioski](#12-wnioski)
13. [Literatura i źródła](#13-literatura-i-źródła)

---

## 1. Wstęp i cel projektu

### 1.1 Kontekst

Rynek kryptowalut charakteryzuje się wyjątkowo wysoką zmiennością i generuje ogromną ilość danych w czasie rzeczywistym. Monitorowanie i analiza tych danych wymaga niezawodnej infrastruktury do ich przechowywania oraz narzędzi do interaktywnej eksploracji. Projekt odpowiada na to zapotrzebowanie, łącząc pobieranie danych przez REST API, relacyjne przechowywanie w bazie SQLite oraz interaktywne wizualizacje.

### 1.2 Cel projektu

Celem projektu było zaprojektowanie i zaimplementowanie systemu, który:

1. **Automatycznie pobiera** historyczne i bieżące dane rynkowe kryptowalut z publicznego API CoinGecko.
2. **Przechowuje** dane w znormalizowanej relacyjnej bazie danych SQLite z właściwie zdefiniowanymi kluczami, ograniczeniami i indeksami.
3. **Prezentuje** zebrane dane w postaci interaktywnych wizualizacji statystycznych — zarówno w środowisku notebooka Jupyter, jak i przez przeglądarkową aplikację webową Streamlit.

### 1.3 Motywacja wyboru tematu

Kryptowaluty stanowią doskonały przypadek użycia dla systemów baz danych zorientowanych na szeregi czasowe:
- dane mają charakter **cykliczny** (codzienne aktualizacje),
- wymagają **idempotentnego zapisu** (ten sam rekord nie może być zduplikowany przy ponownym pobieraniu),
- analizy statystyczne (korelacje, zmienność, rozkłady) są naturalnymi operacjami na tego rodzaju danych.

---

## 2. Zakres funkcjonalny

Projekt obejmuje następujące funkcjonalności:

| Moduł | Funkcjonalność |
|-------|---------------|
| **Pozyskiwanie danych** | Pobieranie 365-dniowych danych historycznych (cena, kapitalizacja, wolumen) z CoinGecko API |
| **Pozyskiwanie danych** | Pobieranie bieżącego snapshotu rynkowego (24h high/low, ATH, rank, supply) |
| **Baza danych** | Trzy tabele relacyjne z kluczami obcymi, ograniczeniami UNIQUE i indeksami |
| **Analiza szeregów czasowych** | Interaktywny wykres liniowy z filtrowaniem po monecie, zakresie dat, metryce; opcja średniej kroczącej i skali logarytmicznej |
| **Analiza ilościowa** | Wykresy słupkowy / pudełkowy / skrzypcowy z agregacjami (mean, max, min, std) dla różnych horyzontów czasowych |
| **Dashboard rynkowy** | Karty KPI z cenami i zmianami, tabela podsumowująca, zgrupowany wykres słupkowy, heatmapa zmian, mapa drzewa (treemap) kapitalizacji |
| **Analiza korelacji i zmienności** | Macierz korelacji dziennych zwrotów, roczna zmienność (annualised volatility), krocząca 30-dniowa korelacja z Bitcoinem |

---

## 3. Zastosowane technologie

| Komponent | Technologia | Wersja | Uzasadnienie wyboru |
|-----------|------------|--------|---------------------|
| Język programowania | Python | 3.13 | Ekosystem data-science, wsparcie dla SQLite w bibliotece standardowej |
| Menedżer pakietów | uv | 0.10.9+ | Szybki resolver zależności, izolowane środowisko `.venv`, deterministyczny `uv.lock` |
| Baza danych | SQLite 3 | stdlib | Zero-konfiguracyjna, jednolikowa baza idealna dla projektów lokalnych; pełna obsługa SQL, kluczy obcych i indeksów |
| Źródło danych | CoinGecko API v3 | publiczne | Darmowy dostęp bez klucza API, bogate dane historyczne i bieżące |
| Notebook | JupyterLab | 4.x | Interaktywne środowisko do analizy danych, obsługa ipywidgets |
| Wizualizacja | Plotly | 6.7 | Interaktywne, responsywne wykresy; `plotly_dark` template; bogata biblioteka wykresów |
| Interaktywność notebooka | ipywidgets | 8.1 | Natywne widgety (suwaki, listy wyboru, daty) bez potrzeby zewnętrznego serwera |
| Aplikacja webowa | Streamlit | 1.57 | Szybkie tworzenie aplikacji data-science; caching `@st.cache_data`; responsywny layout |
| Manipulacja danymi | pandas | 2.2+ | DataFrame jako warstwa pośrednia między SQL a wizualizacją; `pd.read_sql` |

---

## 4. Projekt bazy danych

### 4.1 Model konceptualny (ERD)

```mermaid
erDiagram
    cryptocurrencies {
        TEXT id PK "klucz CoinGecko, np. bitcoin"
        TEXT symbol NOT_NULL "ticker, np. BTC"
        TEXT name NOT_NULL "pełna nazwa, np. Bitcoin"
    }

    market_snapshots {
        INTEGER record_id PK "AUTOINCREMENT"
        TEXT crypto_id FK "→ cryptocurrencies.id"
        DATE snapshot_date NOT_NULL "RRRR-MM-DD"
        REAL price_usd "cena zamknięcia w USD"
        REAL market_cap "kapitalizacja rynkowa w USD"
        REAL total_volume "wolumen 24h w USD"
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
    cryptocurrencies ||--o{ market_current   : "ma snapshoty live"
```

### 4.2 Opis tabel

#### `cryptocurrencies` — słownikowa lista śledzonych monet

Tabela referencyjna (lookup table) zawierająca jeden rekord dla każdej śledzonej kryptowaluty. Pełni rolę wymiaru (dimension) w modelu gwiazdy.

| Kolumna | Typ | Ograniczenia | Opis |
|---------|-----|-------------|------|
| `id` | TEXT | PRIMARY KEY | Kanoniczny identyfikator CoinGecko (małe litery), np. `bitcoin` |
| `symbol` | TEXT | NOT NULL | Ticker giełdowy, np. `BTC` |
| `name` | TEXT | NOT NULL | Pełna nazwa wyświetlana, np. `Bitcoin` |

#### `market_snapshots` — historyczne dane dzienne

Tabela faktów (fact table) przechowująca dzienne wartości ceny, kapitalizacji i wolumenu obrotu. Jeden rekord = jeden dzień dla jednej monety.

| Kolumna | Typ | Ograniczenia | Opis |
|---------|-----|-------------|------|
| `record_id` | INTEGER | PK, AUTOINCREMENT | Klucz surogatowy |
| `crypto_id` | TEXT | NOT NULL, FK | Odwołanie do `cryptocurrencies.id` |
| `snapshot_date` | DATE | NOT NULL | Data snapshotu w formacie `YYYY-MM-DD` (UTC) |
| `price_usd` | REAL | — | Cena zamknięcia w USD |
| `market_cap` | REAL | — | Całkowita kapitalizacja rynkowa w USD |
| `total_volume` | REAL | — | Wolumen obrotu w ciągu 24h w USD |

#### `market_current` — bieżące snapshoty (live)

Tabela faktów przechowująca bogate dane z bieżącego stanu rynku. Każde wywołanie funkcji pobierania dodaje nowy zestaw wierszy z aktualnym znacznikiem czasu — dane nie są nadpisywane, tworząc historię kolejnych pobrań.

| Kolumna | Typ | Opis |
|---------|-----|------|
| `record_id` | INTEGER PK | Klucz surogatowy |
| `crypto_id` | TEXT FK | Odwołanie do `cryptocurrencies.id` |
| `collected_at` | DATETIME | Znacznik czasu pobrania (UTC) |
| `price_usd` | REAL | Bieżąca cena w USD |
| `market_cap` | REAL | Kapitalizacja rynkowa |
| `total_volume` | REAL | Wolumen 24h |
| `high_24h` | REAL | Maksymalna cena w ciągu 24h |
| `low_24h` | REAL | Minimalna cena w ciągu 24h |
| `price_change_24h` | REAL | Bezwzględna zmiana ceny w 24h (USD) |
| `price_change_percentage_24h` | REAL | Procentowa zmiana ceny w 24h |
| `price_change_percentage_7d` | REAL | Procentowa zmiana ceny w 7 dniach |
| `market_cap_rank` | INTEGER | Globalny ranking wg kapitalizacji |
| `circulating_supply` | REAL | Liczba monet w obiegu |
| `total_supply` | REAL | Całkowita podaż |
| `max_supply` | REAL | Maksymalna możliwa podaż (NULL jeśli nieograniczona) |
| `ath` | REAL | Historyczne maksimum ceny (ATH) w USD |
| `ath_change_percentage` | REAL | Odległość od ATH w procentach (ujemna = poniżej ATH) |

### 4.3 Ograniczenia integralności

| Ograniczenie | Tabela | Definicja | Cel |
|-------------|--------|-----------|-----|
| PRIMARY KEY | wszystkie | `id` lub `record_id` | Jednoznaczna identyfikacja wiersza |
| FOREIGN KEY | `market_snapshots` | `crypto_id → cryptocurrencies.id` | Brak rekordów osieroconych — każdy snapshot musi mieć odpowiadającą monetę |
| FOREIGN KEY | `market_current` | `crypto_id → cryptocurrencies.id` | j.w. |
| UNIQUE | `market_snapshots` | `(crypto_id, snapshot_date)` | Jeden rekord na monetę na dzień; umożliwia idempotentny `INSERT OR REPLACE` |
| NOT NULL | `market_snapshots` | `crypto_id`, `snapshot_date` | Klucz naturalny musi zawsze być podany |
| NOT NULL | `market_current` | `crypto_id`, `collected_at` | Klucz identyfikujący musi zawsze być podany |

**Strategia zapisu historycznych danych:**

Zastosowanie `INSERT OR REPLACE` (SQLite: usuwa konfliktujący wiersz i wstawia nowy) na ograniczeniu `UNIQUE(crypto_id, snapshot_date)` sprawia, że ponowne uruchomienie pobierania danych jest bezpieczne — nie tworzy duplikatów, a jedynie aktualizuje wartości dla dni, które już istnieją w bazie.

```sql
-- Bezpieczne dla wielokrotnego uruchomienia:
INSERT OR REPLACE INTO market_snapshots
    (crypto_id, snapshot_date, price_usd, market_cap, total_volume)
VALUES (?, ?, ?, ?, ?);
```

### 4.4 Indeksy i optymalizacja zapytań

Schemat wykorzystuje trzy mechanizmy indeksowania:

**1. Indeks z klucza głównego (automatyczny)**  
SQLite automatycznie tworzy B-drzewo na kolumnie `PRIMARY KEY` każdej tabeli. Używany przy wyszukiwaniu po `record_id`.

**2. Indeks złożony z ograniczenia UNIQUE**  
Ograniczenie `UNIQUE(crypto_id, snapshot_date)` na tabeli `market_snapshots` tworzy ukryty indeks złożony (`sqlite_autoindex_market_snapshots_1`). Ten indeks obsługuje wydajnie zapytania z warunkiem równości na `crypto_id` ORAZ zakresem dat na `snapshot_date`:

```sql
-- Plan zapytania: SEARCH market_snapshots
-- USING INDEX sqlite_autoindex_market_snapshots_1
-- (crypto_id=? AND snapshot_date>? AND snapshot_date<?)
SELECT snapshot_date, price_usd
FROM market_snapshots
WHERE crypto_id = 'bitcoin'
  AND snapshot_date BETWEEN '2025-01-01' AND '2025-12-31';
```

**3. Jawne indeksy dodatkowe**

```sql
-- Optymalizuje sortowanie i filtrowanie po dacie bez warunku na crypto_id
CREATE INDEX idx_snapshots_date ON market_snapshots(snapshot_date);

-- Optymalizuje zapytania historyczne na market_current po czasie pobrania
CREATE INDEX idx_current_collected_at ON market_current(collected_at);
```

| Indeks | Tabela | Kolumny | Typ zapytania wspierany |
|--------|--------|---------|------------------------|
| PK autoindex | wszystkie | `record_id` | Lookup po kluczu głównym |
| `sqlite_autoindex_...` | `market_snapshots` | `(crypto_id, snapshot_date)` | Filtr po monecie + zakres dat |
| `idx_snapshots_date` | `market_snapshots` | `snapshot_date` | Filtr po samej dacie |
| `idx_current_collected_at` | `market_current` | `collected_at` | Filtr po czasie pobrania |

### 4.5 Normalizacja

Schemat spełnia wymagania **Trzeciej Postaci Normalnej (3NF)**:

**1NF (Pierwsza Postać Normalna)** — spełniona.  
Wszystkie wartości kolumn są atomowe (niepodzielne). Brak grup powtarzających się i wielowartościowych atrybutów.

**2NF (Druga Postać Normalna)** — spełniona.  
Tabele `market_snapshots` i `market_current` używają kluczy surogatowych (`record_id`), więc każdy atrybut zależy od całego klucza. W tabeli `cryptocurrencies` atrybuty `symbol` i `name` są w pełnej zależności funkcyjnej od `id`.

**3NF (Trzecia Postać Normalna)** — spełniona.  
Brak przechodnich zależności. Metadane monety (`symbol`, `name`) przechowywane są wyłącznie w `cryptocurrencies` — tabele faktów zawierają tylko klucz obcy `crypto_id`, nie powielają nazwy ani symbolu. Wszystkie atrybuty tabel faktów zależą bezpośrednio od klucza głównego.

| Tabela | 1NF | 2NF | 3NF | Uwagi |
|--------|:---:|:---:|:---:|-------|
| `cryptocurrencies` | ✅ | ✅ | ✅ | Prosta tabela słownikowa |
| `market_snapshots` | ✅ | ✅ | ✅ | Tabela faktów; brak kolumn pochodnych |
| `market_current` | ✅ | ✅ | ✅ | Szeroka tabela faktów; wartości bezpośrednio z API |

> Uwaga: kolumny `price_change_24h` i `price_change_percentage_24h` w `market_current` są technicznie możliwe do wyliczenia z `market_snapshots`, jednak są one przechowywane jako wartości surowe z API (obliczone po stronie serwera CoinGecko), a nie jako wartości pochodne — nie narusza to 3NF.

---

## 5. Architektura systemu

System zbudowany jest w oparciu o trójwarstwową architekturę:

```
┌─────────────────────────────────────────────────────────┐
│                   WARSTWA PREZENTACJI                    │
│                                                         │
│   📓 Jupyter Notebook          🌐 Streamlit Web App     │
│   crypto_market_analysis.ipynb      app.py              │
│   11 etapów · ipywidgets        6 stron · Plotly        │
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
│   fetch_market_chart()     fetch_markets_current()      │
│   /coins/{id}/market_chart  /coins/markets              │
│               ↑                        ↑                │
│         CoinGecko Public REST API v3                    │
└─────────────────────────────────────────────────────────┘
```

**Przepływ danych — pobieranie historyczne:**

1. Użytkownik inicjuje pobieranie (notebook Stage 5 lub przycisk w Streamlit).
2. Dla każdej z 5 monet wysyłane jest żądanie `GET /coins/{id}/market_chart?days=365`.
3. Odpowiedź JSON zawiera tablice par `[timestamp_ms, value]` dla ceny, kapitalizacji i wolumenu.
4. Timestamp milisekundowy konwertowany jest na datę `YYYY-MM-DD` (UTC).
5. Wiersze zapisywane są za pomocą `INSERT OR REPLACE` do `market_snapshots`.
6. Między kolejnymi żądaniami stosowane jest opóźnienie 10 sekund (limit API).

**Przepływ danych — bieżący snapshot:**

1. Jedno żądanie `GET /coins/markets?ids=bitcoin,ethereum,solana,binancecoin,ripple`.
2. API zwraca listę 5 obiektów z aktualnymi danymi rynkowymi.
3. Dane wstawiane są do `market_current` z bieżącym znacznikiem czasu UTC.

---

## 6. Implementacja — warstwa danych

### 6.1 Inicjalizacja bazy danych

Funkcja `create_database()` wywoływana jest przy każdym uruchomieniu systemu (notebook: Stage 3; Streamlit: `main()`). Stosuje `CREATE TABLE IF NOT EXISTS` i `CREATE INDEX IF NOT EXISTS`, co sprawia, że operacja jest idempotentna — bezpieczna dla wielokrotnego uruchomienia:

```python
def create_database() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS market_snapshots (
            record_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            crypto_id     TEXT    NOT NULL,
            snapshot_date DATE    NOT NULL,
            price_usd     REAL,
            market_cap    REAL,
            total_volume  REAL,
            UNIQUE(crypto_id, snapshot_date),
            FOREIGN KEY (crypto_id) REFERENCES cryptocurrencies(id)
        )
    """)
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_snapshots_date "
        "ON market_snapshots(snapshot_date)"
    )
    # … analogicznie dla market_current …
    conn.commit()
    conn.close()
```

### 6.2 Pobieranie danych z API

```python
def fetch_market_chart(coin_id: str, days: int = 365) -> dict:
    r = requests.get(
        f"{BASE_URL}/coins/{coin_id}/market_chart",
        params={"vs_currency": "usd", "days": days, "interval": "daily"},
        timeout=20,
    )
    r.raise_for_status()   # rzuca HTTPError przy kodach 4xx/5xx
    return r.json()
```

Obsługa limitów API: `time.sleep(REQUEST_DELAY)` = 10 sekund między kolejnymi żądaniami. Tier bezpłatny CoinGecko dopuszcza ~10–30 żądań/minutę; 10-sekundowe opóźnienie zapewnia bezpieczny margines.

### 6.3 Zapis i odczyt danych

**Zapis historyczny (idempotentny):**

```python
conn.executemany(
    "INSERT OR REPLACE INTO market_snapshots "
    "(crypto_id, snapshot_date, price_usd, market_cap, total_volume) "
    "VALUES (?,?,?,?,?)",
    rows,          # lista tupli przygotowanych z odpowiedzi API
)
conn.commit()
```

Użycie `executemany` z parametrami pozycyjnymi (`?`) zapobiega SQL Injection.

**Odczyt do DataFrame:**

```python
@st.cache_data(ttl=60)        # cache 60 s — unika zbędnych zapytań do DB
def load_snapshots() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("""
        SELECT s.snapshot_date, s.price_usd, s.market_cap, s.total_volume,
               c.name, c.symbol
        FROM market_snapshots s
        JOIN cryptocurrencies c ON s.crypto_id = c.id
        ORDER BY s.snapshot_date
    """, conn)
    conn.close()
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
    return df
```

JOIN eliminuje potrzebę wielokrotnych zapytań — dane są pobierane jednorazowo jako denormalizowany DataFrame, który następnie filtrowany jest w pamięci pod kątem interaktywnych analiz.

---

## 7. Implementacja — warstwa prezentacji

### 7.1 Notebook Jupyter (11 etapów)

Notebook `crypto_market_analysis.ipynb` podzielony jest na 11 numerowanych etapów, każdy z opisową komórką Markdown i komórkami kodu:

| Etap | Opis | Kluczowe elementy |
|------|------|------------------|
| 1 | Środowisko | Dokumentacja zarządzania pakietami przez `uv` |
| 2 | Importy i stałe | `DB_PATH`, `BASE_URL`, `REQUEST_DELAY=10`, `COINS`, `METRIC_MAP` |
| 3 | Inicjalizacja DB | `create_database()` — wszystkie `CREATE TABLE / INDEX` |
| 4 | Dane słownikowe | `populate_cryptocurrencies()` + weryfikacja SELECT |
| 5 | Funkcje API + pętla pobierania | `fetch_market_chart`, `store_market_chart`; pętla po 5 monetach; 1826 wierszy |
| 6 | Weryfikacja DB | Liczniki wierszy, zakres dat, kontrola spójności |
| 7 | Ładowanie DataFrame | `pd.read_sql` z JOIN; rzutowanie typów |
| 8 | Analiza szeregów czasowych | 6 widgetów ipywidgets; wykres liniowy Plotly |
| 9 | Analiza ilościowa | 6 widgetów ipywidgets; bar/box/violin |
| 10 | Dashboard rynkowy | `build_dashboard_df()`; 4 wykresy Plotly |
| 11 | Korelacja i zmienność | `pct_change()`, `corr()`, zmienność roczna, krocząca korelacja 30-dniowa |

**Interaktywność notebooka** — zastosowane widgety ipywidgets:

| Widget | Typ | Zastosowanie |
|--------|-----|-------------|
| `SelectMultiple` | Lista wielokrotnego wyboru | Wybór monet do analizy |
| `DatePicker` | Datownik | Zakres dat |
| `Dropdown` | Lista rozwijana | Metryka, okres, agregacja, typ wykresu |
| `IntSlider` | Suwak | Okno średniej kroczącej (MA) |
| `ToggleButton` | Przełącznik | Skala logarytmiczna |
| `Output` | Kontener | Renderowanie wykresów Plotly wewnątrz `interact()` |

### 7.2 Aplikacja webowa Streamlit (6 stron)

Aplikacja `app.py` dostępna pod adresem `http://localhost:8501` oferuje wszystkie analizy notebooka w przeglądarce, bez potrzeby posiadania środowiska Jupyter.

**Nawigacja:** lewy pasek boczny z przyciskami `st.radio` do przełączania stron.

#### Strona 1: Overview (Przegląd)

Wyświetla metryki bazy danych (liczba monet, dziennych snapshotów, snapshotów live) oraz zakres dat dostępnych danych. Zawiera tabelę nawigacji z opisami wszystkich stron.

#### Strona 2: Data Collection (Zbieranie danych)

Dwa niezależne przyciski wyzwalające pobieranie:
- **Historyczne**: pętla po 5 monetach z paskiem postępu; `time.sleep(10)` między żądaniami; `INSERT OR REPLACE`.
- **Live**: jedno zbiorowe żądanie `/coins/markets`; `INSERT` z timestamp UTC.

Po zakończeniu pobierania: `load_snapshots.clear()` + `load_db_stats.clear()` + `st.rerun()` — automatyczne odświeżenie metryk.

Poniżej przycisków: tabela SQL z podsumowaniem danych w bazie (`COUNT`, `MIN/MAX/AVG` ceny per moneta).

#### Strona 3: Time Series (Szeregi czasowe)

Filtry w sidebarze:
1. Multiselect monet
2. Data początkowa (date_input)
3. Data końcowa (date_input)
4. Metryka (cena / kapitalizacja / wolumen)
5. Okno MA (slider 0–30 dni)
6. Skala logarytmiczna (checkbox)

Wykres: `px.line` z `hovermode="x unified"` — unifikacja tooltipów na osi X.

#### Strona 4: Quantitative Analysis (Analiza ilościowa)

Filtry w sidebarze:
1. Multiselect monet
2. Metryka
3. Okres (7 / 30 / 90 / 180 / 365 dni)
4. Agregacja (mean / max / min / last / std)
5. Kolejność sortowania
6. Typ wykresu (Bar / Box / Violin)

#### Strona 5: Market Dashboard

- **Karty KPI** (`st.metric`): cena i zmiana 24h dla każdej monety.
- **Tabela podsumowująca**: cena, kap. rynkowa, wolumen, zmiany 24h/7d/30d.
- **Grupowany wykres słupkowy**: procentowe zmiany ceny w 3 horyzontach.
- **Heatmapa zmian**: `px.imshow` na skali RdYlGn (zielony = wzrost, czerwony = spadek).
- **Mapa drzewa (Treemap)**: rozmiar = kapitalizacja rynkowa; kolor = zmiana 24h.

Dane do zmian procentowych obliczane są z `market_snapshots` przez funkcję `build_dashboard_df()` — różnice między ostatnią ceną a ceną 1/7/30 dni wcześniej.

#### Strona 6: Correlation & Volatility (Korelacja i zmienność)

- **Macierz korelacji Pearsona** dziennych zwrotów logarytmicznych (`pct_change()`).
- **Roczna zmienność**: `std(daily_returns) × √365 × 100 [%]`
- **Krocząca 30-dniowa korelacja** każdej monety z Bitcoinem (jeśli BTC jest wybrany).
- **Statystyki opisowe** dziennych zwrotów (rozwijana sekcja).

---

## 8. Opis analiz i wizualizacji

### 8.1 Analiza szeregów czasowych

Wykres liniowy prezentuje ewolucję wybranej metryki w czasie. Opcja **średniej kroczącej** (MA) wygładza szum krótkoterminowy i ujawnia trendy. Skala logarytmiczna umożliwia porównywanie monet o bardzo różnych cenach (np. BTC ~$90 000 vs XRP ~$2).

```python
# Obliczanie MA
filtered[metric_col] = filtered.groupby("name")[metric_col].transform(
    lambda x: x.rolling(ma_window, min_periods=1).mean()
)
```

### 8.2 Analiza ilościowa

**Wykres słupkowy** — porównanie zagregowanych wartości (np. średnia cena w ostatnich 90 dniach).  
**Wykres pudełkowy (Box plot)** — rozkład wartości: mediana, kwartyle, wartości odstające.  
**Wykres skrzypcowy (Violin plot)** — j.w. + szacowanie gęstości rozkładu.

### 8.3 Macierz korelacji

Korelacja Pearsona obliczana jest na dziennych zwrotach (nie bezpośrednio na cenach), co eliminuje trend i skupia się na współzależności ruchów:

```python
price_pivot = df.pivot(index="snapshot_date", columns="name", values="price_usd")
returns     = price_pivot.pct_change().dropna()
corr        = returns.corr()    # macierz Pearsona n×n
```

Wartości bliskie +1 oznaczają silną dodatnią korelację (monety poruszają się razem), bliskie 0 — brak korelacji, ujemne — korelację odwrotną.

### 8.4 Zmienność roczna (Annualised Volatility)

Standardowa miara zmienności finansowej:

$$\sigma_{roczna} = \sigma_{dzienna} \times \sqrt{365} \times 100\%$$

gdzie $\sigma_{dzienna}$ to odchylenie standardowe dziennych zwrotów logarytmicznych.

---

## 9. Dane zebrane w projekcie

### Stan bazy danych po uruchomieniu projektu

| Tabela | Liczba wierszy | Opis |
|--------|---------------|------|
| `cryptocurrencies` | 5 | Bitcoin, Ethereum, Solana, BNB, XRP |
| `market_snapshots` | 1 826 | 366 dni × 5 monet (rok historii) |
| `market_current` | 10 | 2 pobierania live × 5 monet |

### Zakres danych historycznych

- **Data pierwsza:** 2025-05-26
- **Data ostatnia:** 2026-05-26
- **Łącznie:** 366 dni (rok przestępny)

### Śledzone kryptowaluty

| Symbol | Nazwa | Typ |
|--------|-------|-----|
| BTC | Bitcoin | Proof-of-Work, pierwsza kryptowaluta |
| ETH | Ethereum | Smart contracts, Proof-of-Stake |
| SOL | Solana | High-throughput PoS |
| BNB | BNB (Binance Coin) | Exchange token |
| XRP | XRP (Ripple) | Payment settlement |

Wybór obejmuje pięć największych kryptowalut pod względem kapitalizacji rynkowej, reprezentujących różne technologie i przypadki użycia.

---

## 10. Instrukcja uruchomienia

### Wymagania wstępne

- Python 3.13 (zalecane zarządzanie przez `uv`)
- `uv` — instalacja: `pip install uv` lub [docs.astral.sh/uv](https://docs.astral.sh/uv/)
- Dostęp do internetu (CoinGecko API)

### Krok 1 — Przejście do katalogu projektu

```powershell
cd coingeko_project
```

### Krok 2 — Instalacja zależności

```powershell
uv sync
```

Tworzy `.venv` i instaluje wszystkie pakiety zgodnie z `uv.lock`.

### Krok 3a — Uruchomienie notebooka Jupyter

```powershell
# Rejestracja kernela (tylko raz):
uv run python -m ipykernel install --user `
    --name crypto-market-analysis `
    --display-name "Python (crypto-market-analysis)"

# Uruchomienie JupyterLab:
uv run jupyter lab
```

Otwórz `crypto_market_analysis.ipynb` i wybierz kernel `Python (crypto-market-analysis)`.  
Wykonaj komórki od góry (**Run → Run All Cells**).

### Krok 3b — Uruchomienie aplikacji Streamlit

```powershell
uv run streamlit run app.py
```

Aplikacja dostępna pod: **http://localhost:8501**

Po pierwszym uruchomieniu przejdź do strony **📥 Data Collection** i pobierz dane historyczne.

---

## 11. Napotkane problemy i rozwiązania

| Problem | Przyczyna | Zastosowane rozwiązanie |
|---------|-----------|------------------------|
| `ModuleNotFoundError` przy starcie kernela | `pyproject.toml` wymagał Pythona 3.14, który nie był zainstalowany | Zmiana `requires-python = ">=3.14"` na `">=3.13"`; aktualizacja `.python-version` |
| HTTP 429 (Too Many Requests) | Darmowy tier CoinGecko ma limit ~10–30 req/min; poprzednie żądanie zbyt bliskie | Zwiększono `REQUEST_DELAY` do 10 s; dodano retry z opóźnieniem |
| Pusty dashboard (Stage 10) | Tabela `market_current` była pusta podczas analizy; dashboard bazował wyłącznie na tej tabeli | Przebudowa Stage 10 i funkcji `build_dashboard_df()` — obliczanie zmian procentowych z `market_snapshots` (dane historyczne zawsze dostępne) |
| `AttributeError: DataFrame has no attribute 'applymap'` | `applymap` usunięty w pandas 2.1; zastąpiony przez `map` | Zmiana `.applymap(...)` na `.map(...)` w `app.py` |
| `DeprecationWarning` w `pyproject.toml` | Przestarzała sekcja `[tool.uv.dev-dependencies]` | Migracja do nowej składni `[dependency-groups]` |
| `KeyboardInterrupt` podczas `time.sleep(20)` | Użytkownik przerwał oczekiwanie między żądaniami API | Dodano dedykowaną komórkę retry; dane live ostatecznie pobrane pomyślnie |

---

## 12. Wnioski

### Osiągnięcia

1. **Kompletny system end-to-end**: od pobrania surowych danych przez REST API, przez relacyjną bazę danych, do interaktywnych wizualizacji — w dwóch niezależnych interfejsach (Jupyter i Streamlit).

2. **Poprawny projekt bazy danych**: schemat spełnia 3NF, zawiera klucze obce, ograniczenie UNIQUE na kluczu naturalnym `(crypto_id, snapshot_date)` oraz indeksy wspierające najczęstsze zapytania.

3. **Idempotentne pobieranie danych**: `INSERT OR REPLACE` sprawia, że ponowne uruchomienie skryptu nigdy nie duplikuje danych — tylko aktualizuje istniejące i dodaje nowe.

4. **Reprodukowalność środowiska**: `uv` + `uv.lock` gwarantują identyczne środowisko na każdej maszynie.

### Możliwe rozszerzenia

- **Zwiększenie liczby monitorowanych monet** — wystarczy rozszerzyć listę `COINS`.
- **Harmonogram automatycznego pobierania** — Celery, APScheduler lub zadanie Windows Task Scheduler wywołujące `uv run python -c "..."`.
- **PostgreSQL zamiast SQLite** — dla większej liczby użytkowników jednoczesnych lub gdy rozmiar danych przekroczy kilkaset MB.
- **Eksport do CSV/Excel** — przycisk pobierania w Streamlit (`st.download_button`).
- **Powiadomienia cenowe** — alerty mailowe lub przez webhook gdy cena przekroczy zdefiniowany próg.

### Uwagi końcowe

Projekt pokazuje, że SQLite jest w pełni wystarczający do analitycznych zastosowań lokalnych o umiarkowanej skali — baza z 1826 wierszami obsługuje wszystkie zapytania poniżej 50 ms. Prawidłowe zaplanowanie indeksów (w tym wykorzystanie ograniczenia UNIQUE jako indeksu złożonego) jest kluczowe dla wydajności zapytań z filtrowaniem zakresowym na datach.

---

## 13. Literatura i źródła

1. **CoinGecko API Documentation** — https://www.coingecko.com/en/api/documentation
2. **SQLite Documentation** — https://www.sqlite.org/docs.html
3. **pandas Documentation** — https://pandas.pydata.org/docs/
4. **Plotly Python Documentation** — https://plotly.com/python/
5. **Streamlit Documentation** — https://docs.streamlit.io/
6. **uv Documentation** — https://docs.astral.sh/uv/
7. **ipywidgets Documentation** — https://ipywidgets.readthedocs.io/
8. E. F. Codd, *A Relational Model of Data for Large Shared Data Banks*, Communications of the ACM, 1970.
9. C. J. Date, *An Introduction to Database Systems*, Addison-Wesley, 8th ed., 2003.
10. W. McKinney, *Python for Data Analysis*, O'Reilly, 3rd ed., 2022.

---

*Sprawozdanie przygotowane w ramach przedmiotu Zaawansowane Bazy Danych.*  
*Autorzy: Michał Dusza · Szymon Bugajski · Mateusz Basiura · Maj 2026*
