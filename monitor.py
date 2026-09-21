import json
import os
import smtplib
from email.message import EmailMessage
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


def send_email():
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    mail_to = os.environ["MAIL_TO"]

    message = EmailMessage()

    message["Subject"] = "🚨 MiWuLa KiTa-Termine veröffentlicht!"
    message["From"] = smtp_user
    message["To"] = mail_to

    message.set_content(
        f"""Hallo,

auf der MiWuLa-KiTa-Seite wurden offenbar neue Termine veröffentlicht.

Bitte prüfe die Seite:

{URL}

Viele Grüße
Dein MiWuLa KiTa Monitor
"""
    )
    
    print(f"SMTP Host: {smtp_host!r}")
    print(f"SMTP Port: {smtp_port!r}")

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)

    print("E-Mail erfolgreich versendet.")

def main():
    print("Sende Test-E-Mail...")
    send_email()
    print("Test abgeschlossen.")

    return

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

    status_changed = (
        previous_status is not None
        and previous_status != current_status
    )

    if status_changed:
        print("⚠️ STATUSÄNDERUNG ERKANNT!")

        if current_status == "TERMINES_AVAILABLE":
            send_email()
    else:
        print("Keine relevante Änderung.")

    save_state(current_status)

    print()
    print("Zustand gespeichert.")
    print("=" * 50)


if __name__ == "__main__":
    main()
