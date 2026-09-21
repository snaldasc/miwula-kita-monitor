import requests
from bs4 import BeautifulSoup

URL = "https://service.miniatur-wunderland.de/kita/"

HEADERS = {
    "User-Agent": "MiWuLa-Kita-Monitor/1.0"
}


def check_kita_page():
    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text(" ", strip=True)

    if "Ups, Ihr seid zu früh dran!" in text:
        status = "NO_TERMINES"
    else:
        status = "TERMINES_AVAILABLE"

    print("MiWuLa KiTa Monitor")
    print("=" * 50)
    print(f"Status: {status}")
    print(f"URL: {URL}")

    if status == "NO_TERMINES":
        print("Noch keine KiTa-Termine veröffentlicht.")
    else:
        print("⚠️ KiTa-Termine könnten veröffentlicht worden sein!")
        print()
        print("Relevanter Seiteninhalt:")
        print(text)

    print("=" * 50)

    return status


if __name__ == "__main__":
    check_kita_page()
