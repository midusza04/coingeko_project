# Indeks dokumentacji technicznej

> System Analizy Rynku Kryptowalut — Zaawansowane Bazy Danych  
> Michał Dusza · Szymon Bugajski · Mateusz Basiura

---

## Mapa całej dokumentacji projektu

Projekt ma kilka warstw dokumentacji — każda służy innemu celowi:

```
┌─────────────────────────────────────────────────────────────────┐
│  README.md              Szybki start, struktura repo, indeks    │
├─────────────────────────────────────────────────────────────────┤
│  SPRAWOZDANIE.md        Raport akademicki (PL) — GŁÓWNY OPIS    │
│  DOCUMENTATION.md       Dokumentacja techniczna (EN) — DDL/SQL  │
├─────────────────────────────────────────────────────────────────┤
│  .docs/                 Skrócona dokumentacja techniczna (PL)    │
│    architecture.md        architektura 3-warstwowa               │
│    data-model.md          schemat SQLite + mapowanie API          │
│    api-reference.md       referencja funkcji app.py / main.py     │
│    diagrams.md            diagramy Mermaid                        │
├─────────────────────────────────────────────────────────────────┤
│  docs/index.html        Portal HTML (otwórz w przeglądarce)       │
│  docs/main.html         Referencja legacy modułu main.py          │
├─────────────────────────────────────────────────────────────────┤
│  SPRAWOZDANIE.docx      Raport Word (wygenerowany skryptem)       │
│  generate_sprawozdanie.py   generator DOCX                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Który dokument czytać?

| Chcę… | Czytaj |
|-------|--------|
| Zrozumieć cały projekt (ocena, prezentacja) | [`SPRAWOZDANIE.md`](../SPRAWOZDANIE.md) |
| Uruchomić projekt od zera | [`README.md`](../README.md) → sekcja *Szybki start* |
| Zobaczyć DDL, zapytania SQL, moduły (EN) | [`DOCUMENTATION.md`](../DOCUMENTATION.md) |
| Zrozumieć architekturę warstw | [`architecture.md`](architecture.md) |
| Poznać schemat bazy i mapowanie API | [`data-model.md`](data-model.md) |
| Sprawdzić sygnatury funkcji | [`api-reference.md`](api-reference.md) |
| Zobaczyć diagramy (ERD, sekwencji, ETL) | [`diagrams.md`](diagrams.md) |
| Przeglądać docs w przeglądarce | [`docs/index.html`](../docs/index.html) |
| Wygenerować raport Word | `uv run python generate_sprawozdanie.py` |

---

## Zawartość folderu `.docs/`

| Plik | Opis |
|------|------|
| [`architecture.md`](architecture.md) | Architektura 3-warstwowa: pozyskiwanie danych → SQLite → prezentacja (Streamlit + Jupyter) |
| [`data-model.md`](data-model.md) | Zaimplementowany schemat SQLite (`cryptocurrencies`, `market_snapshots`, `market_current`), ograniczenia, indeksy, normalizacja 3NF, mapowanie pól API |
| [`api-reference.md`](api-reference.md) | Referencja funkcji `app.py` (główna aplikacja) oraz `main.py` (legacy) |
| [`diagrams.md`](diagrams.md) | Diagramy Mermaid: ERD, sekwencji, przepływu, ETL, architektura komponentów |

---

## Pliki źródłowe systemu

| Plik | Rola | Status |
|------|------|--------|
| `app.py` | Aplikacja Streamlit — ETL + 6 stron wizualizacji | **główny** |
| `crypto_market_analysis.ipynb` | Notebook analityczny — 11 etapów | **główny** |
| `crypto_market.db` | Baza SQLite (tworzona przy pierwszym uruchomieniu) | **główny** |
| `main.py` | Prosty fetcher JSON (3 monety, bez bazy) | legacy |
| `test.ipynb` | Eksploracyjna inspekcja API | legacy |
| `coingecko_response.json` | Przykładowa odpowiedź API | legacy |

---

## Linki zewnętrzne

- [CoinGecko API v3](https://docs.coingecko.com/v3.0.1/reference/introduction)
- [Streamlit docs](https://docs.streamlit.io/)
- [Plotly Python](https://plotly.com/python/)
- [uv — menedżer pakietów](https://docs.astral.sh/uv/)
- [Mermaid live editor](https://mermaid.live/)
