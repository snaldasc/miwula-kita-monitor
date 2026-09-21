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

    print("Seite erfolgreich abgerufen.")
    print()

    if "Ups, Ihr seid zu früh dran!" in text:
        print("STATUS: Noch keine KiTa-Termine veröffentlicht.")
    else:
        print("STATUS: Die Seite hat sich verändert!")
        print()
        print("Bitte Termine prüfen.")

    print()
    print("Seitenlänge:", len(response.text), "Zeichen")


if __name__ == "__main__":
    check_kita_page()
