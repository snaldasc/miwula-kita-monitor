import json
import os
import re
import smtplib
from email.message import EmailMessage
from pathlib import Path
from urllib.parse import urljoin

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


def save_state(appointments):
    data = {
        "appointments": appointments
    }

    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def check_kita_page():
    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    appointments = []

    # Alle Links der Kita-Seite untersuchen
    for link in soup.find_all("a", href=True):
        text = link.get_text(" ", strip=True)
        href = urljoin(URL, link["href"])

        if not text:
            continue

        # Nach typischen Datumsangaben suchen.
        # Unterstützt z.B.:
        # 01.12.2026
        # 1.12.2026
        # 01.12.
        date_matches = re.findall(
            r"\b\d{1,2}\.\d{1,2}(?:\.\d{2,4})?\b",
            text
        )

        if date_matches:
            appointments.append({
                "text": text,
                "url": href
            })

    # Falls die Seite keine einzelnen Datumslinks enthält,
    # prüfen wir zusätzlich den Seitentext.
    if not appointments:
        text = soup.get_text(" ", strip=True)

        date_matches = re.findall(
            r"\b\d{1,2}\.\d{1,2}(?:\.\d{2,4})?\b",
            text
        )

        for date in date_matches:
            appointments.append({
                "text": date,
                "url": URL
            })

    # Duplikate entfernen
    unique_appointments = []
    seen = set()

    for appointment in appointments:
        key = (
            appointment["text"],
            appointment["url"]
        )

        if key not in seen:
            seen.add(key)
            unique_appointments.append(appointment)

    return unique_appointments


def send_email(new_appointments):
    smtp_host = "smtp.gmail.com"
    smtp_port = 587

    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    mail_to = os.environ["MAIL_TO"]

    message = EmailMessage()

    message["Subject"] = "🚨 MiWuLa KiTa-Termine veröffentlicht!"
    message["From"] = smtp_user
    message["To"] = mail_to

    appointment_lines = []

    for appointment in new_appointments:
        appointment_lines.append(
            f"- {appointment['text']}\n"
            f"  {appointment['url']}"
        )

    appointments_text = "\n\n".join(appointment_lines)

    message.set_content(
        f"""Hallo,

auf der MiWuLa-KiTa-Seite wurden neue Termine gefunden.

Gefundene Termine:

{appointments_text}

Zur KiTa-Seite:
{URL}

Viele Grüße
Dein MiWuLa KiTa Monitor
"""
    )

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)

    print("📧 E-Mail erfolgreich versendet.")


def main():
    current_appointments = check_kita_page()
    previous_state = load_previous_state()

    previous_appointments = []

    if previous_state:
        previous_appointments = previous_state.get(
            "appointments",
            []
        )

    print("MiWuLa KiTa Monitor")
    print("=" * 50)

    print(f"Aktuelle Termine: {len(current_appointments)}")
    print(f"Vorherige Termine: {len(previous_appointments)}")
    print()

    for appointment in current_appointments:
        print(f"TERMIN: {appointment['text']}")
        print(f"LINK:  {appointment['url']}")
        print("-" * 50)

    # Termine anhand von Text + URL vergleichen
    previous_keys = {
        (
            appointment["text"],
            appointment["url"]
        )
        for appointment in previous_appointments
    }

    new_appointments = [
        appointment
        for appointment in current_appointments
        if (
            appointment["text"],
            appointment["url"]
        ) not in previous_keys
    ]

    if new_appointments:
        print()
        print("🚨 NEUE TERMINE ERKANNT!")
        print()

        for appointment in new_appointments:
            print(f"- {appointment['text']}")
            print(f"  {appointment['url']}")

        send_email(new_appointments)

    elif current_appointments:
        print("Keine neuen Termine.")

    else:
        print("Keine Termine gefunden.")

    save_state(current_appointments)

    print()
    print("Zustand gespeichert.")
    print("=" * 50)


if __name__ == "__main__":
    main()
