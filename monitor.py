import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup


URL = "https://service.miniatur-wunderland.de/kita/"
STATE_FILE = Path("state.json")

HEADERS = {
    "User-Agent": "MiWuLa-Kita-Monitor/1.0"
}


def load_previous_state():
    if not STATE_FILE.exists():
        return None

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return None


def save_state(status):
    data = {
        "status": status
    }

    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


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

    return status


def main():
    current_status = check_kita_page()
    previous_state = load_previous_state()

    previous_status = (
        previous_state["status"]
        if previous_state
        else None
    )

    print("MiWuLa KiTa Monitor")
    print("=" * 50)
    print(f"Vorheriger Status: {previous_status}")
    print(f"Aktueller Status:  {current_status}")
    print()

    if previous_status is None:
        print("Erster Lauf.")
    elif previous_status != current_status:
        print("⚠️ STATUSÄNDERUNG ERKANNT!")
    else:
        print("Keine Änderung.")

    save_state(current_status)

    print()
    print("Zustand gespeichert.")
    print("=" * 50)


if __name__ == "__main__":
    main()
