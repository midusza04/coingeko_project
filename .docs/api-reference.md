# API Reference — dokumentacja modułu

> Dokumentacja generowana na podstawie docstringów w formacie zgodnym z `pydoc`.  
> Aby wygenerować plik HTML: `python -m pydoc -w main`

---

## Moduł `main`

**Plik:** `main.py`  
**Wersja projektu:** 0.1.0

### Opis

Moduł ingestion danych rynkowych kryptowalut z CoinGecko API.

Pobiera aktualne notowania Bitcoina, Ethereum i Solany z publicznego REST API
CoinGecko v3 i zapisuje odpowiedź jako sformatowany plik JSON.  
Stanowi warstwę kolekcji danych dla projektu akademickiego z przedmiotu
Bazy Danych — zebrane rekordy JSON są materiałem źródłowym do projektowania
i zasilania schematu relacyjnej bazy danych.

**Typowe użycie:**

```bash
python main.py
```

**Używany endpoint API:**

```
https://api.coingecko.com/api/v3/coins/markets
```

**Plik wyjściowy:**

```
coingecko_response.json  (tworzony / nadpisywany w bieżącym katalogu)
```

---

### Importy

| Symbol | Źródło | Cel |
|--------|--------|-----|
| `json` | stdlib | Serializacja i formatowanie danych JSON |
| `Path` | `pathlib` (stdlib) | Cross-platformowe operacje na ścieżkach plików |
| `requests` | PyPI | Wykonywanie żądań HTTP GET |

---

### Funkcje

---

#### `main() -> None`

```
main()
```

Pobiera dane rynkowe kryptowalut z CoinGecko i zapisuje je lokalnie.

Wysyła pojedyncze żądanie GET do endpointu `/coins/markets` publicznego API
CoinGecko v3, żądając statystyk rynkowych wyrażonych w USD dla Bitcoina,
Ethereum i Solany.  Surowa odpowiedź JSON jest formatowana (indent=4) i
zapisywana do pliku `coingecko_response.json` w bieżącym katalogu roboczym.
Nazwy pól pierwszego rekordu są wypisywane na stdout w celach inspekcyjnych.

**Parametry zapytania HTTP:**

| Parametr | Wartość | Opis |
|----------|---------|------|
| `vs_currency` | `"usd"` | Wszystkie wartości monetarne w dolarach amerykańskich |
| `ids` | `"bitcoin,ethereum,solana"` | Monety do pobrania |
| `order` | `"market_cap_desc"` | Sortowanie malejąco po kapitalizacji |
| `per_page` | `10` | Maksymalna liczba wyników na stronę |
| `page` | `1` | Numer strony paginacji |
| `sparkline` | `"false"` | Pomija dane sparkline (wykres 7-dniowy) |
| `price_change_percentage` | `"24h,7d"` | Dodatkowe pola zmian procentowych |

**Efekty uboczne:**

- Wykonuje jedno wychodzące żądanie HTTP GET (timeout: 10 sekund).
- Tworzy / nadpisuje plik `coingecko_response.json` w CWD.
- Wypisuje na stdout: kod statusu HTTP, ścieżkę pliku wyjściowego,
  listę dostępnych nazw pól JSON.

**Wyjątki:**

| Wyjątek | Kiedy |
|---------|-------|
| `requests.exceptions.HTTPError` | Serwer zwrócił kod 4xx lub 5xx (`raise_for_status()`) |
| `requests.exceptions.ConnectionError` | Brak połączenia sieciowego lub niedostępność hosta |
| `requests.exceptions.Timeout` | Serwer nie odpowiedział w ciągu 10 sekund |
| `OSError` | Błąd zapisu pliku (brak uprawnień, brak miejsca na dysku itp.) |

**Zwraca:** `None`

**Przykład wywołania:**

```python
from main import main

main()
# Status code: 200
# Zapisano dane do pliku: coingecko_response.json
#
# Dostępne pola dla pierwszego rekordu:
# - id
# - symbol
# - name
# ...
```

---

### Punkt wejścia

```python
if __name__ == "__main__":
    main()
```

Wywołanie `main()` gdy moduł uruchamiany jest bezpośrednio (`python main.py`).
Nie wykonuje żadnych akcji przy importowaniu modułu.

---

## Generowanie dokumentacji HTML (pydoc)

### Lokalnie w przeglądarce

```bash
# Serwer HTTP z dokumentacją na http://localhost:1234
python -m pydoc -p 1234
```

### Zapis do pliku HTML

```bash
python -m pydoc -w main
# Tworzy: main.html
```

### Podgląd w terminalu

```bash
python -m pydoc main
```

---

## Konwencje docstringów

Projekt używa formatu **Google Style** (kompatybilny z pydoc, pdoc, Sphinx).

Szablon dla nowych funkcji:

```python
def fetch_markets(coins: list[str], currency: str = "usd") -> list[dict]:
    """Pobierz dane rynkowe dla podanych monet.

    Krótki opis w jednej linii.

    Dłuższy opis jeśli potrzebny. Może się rozciągać
    na kilka linii.

    Args:
        coins: Lista identyfikatorów CoinGecko, np. ``["bitcoin", "ethereum"]``.
        currency: Kod waluty bazowej (domyślnie ``"usd"``).

    Returns:
        Lista słowników z danymi rynkowymi — po jednym na monetę.

    Raises:
        requests.exceptions.HTTPError: Jeśli API zwróci błąd HTTP.
        requests.exceptions.Timeout: Jeśli zapytanie przekroczy limit czasu.

    Example:
        >>> data = fetch_markets(["bitcoin"])
        >>> data[0]["name"]
        'Bitcoin'
    """
```

---

*Architektura systemu — zob. [`architecture.md`](architecture.md).*  
*Model danych — zob. [`data-model.md`](data-model.md).*
