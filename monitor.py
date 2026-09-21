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

    # Den sichtbaren Text der Seite ausgeben
    text = soup.get_text("\n", strip=True)

    print(text)

    print("=" * 60)
    print("Seitenlänge:", len(response.text), "Zeichen")


if __name__ == "__main__":
    check_kita_page()
