import json
from pathlib import Path

import requests


def main() -> None:
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

    print(f"Zapisano dane do pliku: {output_path}")

    if data:
        print("\nDostępne pola dla pierwszego rekordu:")
        for key in data[0].keys():
            print("-", key)


if __name__ == "__main__":
    main()