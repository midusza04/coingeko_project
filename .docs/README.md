# Dokumentacja techniczna — CryptoMarket DB

Indeks dokumentacji projektu.

## Zawartość folderu `.docs/`

| Plik | Opis |
|------|------|
| [`architecture.md`](architecture.md) | Architektura systemu — warstwy, przepływ danych, stos technologiczny, obsługa błędów, ograniczenia i plany rozszerzeń |
| [`data-model.md`](data-model.md) | Model danych — pełny opis pól odpowiedzi CoinGecko API, typy, nullable, przykłady; proponowany schemat SQL (DDL) |
| [`api-reference.md`](api-reference.md) | Referencja API modułu `main.py` w formacie pydoc — opis funkcji, parametrów, wyjątków, efektów ubocznych |
| [`diagrams.md`](diagrams.md) | Diagramy Mermaid: sekwencji, przepływu, klas/modułów, ERD, komponentów C4, ETL |

## Szybki start — generowanie dokumentacji HTML

```bash
# Dokumentacja pydoc modułu main.py
python -m pydoc -w main
open main.html   # macOS
start main.html  # Windows
```

## Linki zewnętrzne

- [CoinGecko API v3 Docs](https://docs.coingecko.com/v3.0.1/reference/introduction)
- [requests — dokumentacja](https://requests.readthedocs.io/)
- [Mermaid — live editor](https://mermaid.live/)
- [uv — menedżer pakietów](https://docs.astral.sh/uv/)
