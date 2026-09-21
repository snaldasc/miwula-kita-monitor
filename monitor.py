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

    print("Seite erfolgreich abgerufen.")
    print("=" * 60)

    # Alle Links der Seite anzeigen
    links = soup.find_all("a")

    print(f"Gefundene Links: {len(links)}")
    print()

    for link in links:
        text = link.get_text(" ", strip=True)
        href = link.get("href")

        if text or href:
            print(f"TEXT: {text}")
            print(f"HREF: {href}")
            print("-" * 40)

    print("=" * 60)


if __name__ == "__main__":
    check_kita_page()
