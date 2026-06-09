"""CoinGecko market data fetcher.

This module retrieves current cryptocurrency market data for Bitcoin, Ethereum,
and Solana from the public CoinGecko REST API and persists the response as a
formatted JSON file.  It serves as the data-ingestion layer for the university
databases course project — the collected JSON records are the source material
for designing and populating a relational database schema.

Typical usage::

    python main.py

API endpoint used:
    https://api.coingecko.com/api/v3/coins/markets

Output file:
    coingecko_response.json  (created / overwritten in the current directory)

Dependencies:
    requests >= 2.33.1
"""

import json
from pathlib import Path

import requests


def main() -> None:
    """Fetch cryptocurrency market data from CoinGecko and save it locally.

    Sends a single GET request to the ``/coins/markets`` endpoint of the
    CoinGecko v3 public API, requesting USD-denominated market statistics for
    Bitcoin, Ethereum, and Solana.  The raw JSON response is pretty-printed and
    written to ``coingecko_response.json`` in the current working directory.
    Field names from the first record are echoed to stdout for quick inspection.

    The query parameters used:

    * ``vs_currency`` – ``"usd"`` — all monetary values expressed in US dollars.
    * ``ids`` – ``"bitcoin,ethereum,solana"`` — coins to fetch.
    * ``order`` – ``"market_cap_desc"`` — results sorted by market capitalisation.
    * ``per_page`` / ``page`` – pagination (10 results, page 1).
    * ``sparkline`` – ``"false"`` — omit 7-day sparkline image data.
    * ``price_change_percentage`` – ``"24h,7d"`` — include 24-hour and 7-day
      percentage change fields in the response.

    Side effects:
        * Performs one outbound HTTP GET request (10-second timeout).
        * Writes / overwrites ``coingecko_response.json`` in the CWD.
        * Prints the HTTP status code, the output file path, and the list of
          available JSON field names to stdout.

    Raises:
        requests.exceptions.HTTPError: If the server returns a 4xx or 5xx
            status code (triggered via ``response.raise_for_status()``).
        requests.exceptions.ConnectionError: If the network is unavailable or
            the CoinGecko host cannot be reached.
        requests.exceptions.Timeout: If the server does not respond within
            10 seconds.

    Returns:
        None
    """
    url = "https://api.coingecko.com/api/v3/coins/markets"

    params = {
        "vs_currency": "usd",
        "ids": "bitcoin,ethereum,solana",
        "order": "market_cap_desc",
        "per_page": 10,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h,7d",
    }

    response = requests.get(url, params=params, timeout=10)

    print("Status code:", response.status_code)

    response.raise_for_status()

    data = response.json()

    output_path = Path("coingecko_response.json")

    output_path.write_text(
        json.dumps(data, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Saved data to file: {output_path}")

    if data:
        print("\nAvailable fields for the first record:")
        for key in data[0].keys():
            print("-", key)


if __name__ == "__main__":
    main()