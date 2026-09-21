import json
import os
import re
import smtplib
import time
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
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )


def check_kita_page():
    response = requests.get(
        URL,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    appointments = []

    for link in soup.find_all("a", href=True):
        text = link.get_text(" ", strip=True)
        href = urljoin(URL, link["href"])

        if not text:
            continue

        date_matches = re.findall(
            r"\b\d{1,2}\.\d{1,2}(?:\.\d{2,4})?\b",
            text
        )

        if date_matches:
            appointments.append({
                "text": text,
                "url": href
            })

    if not appointments:
        text = soup.get_text(
            " ",
            strip=True
        )

        date_matches = re.findall(
            r"\b\d{1,2}\.\d{1,2}(?:\.\d{2,4})?\b",
            text
        )

        for date in date_matches:
            appointments.append({
                "text": date,
                "url": URL
            })

    unique_appointments = []
    seen = set()

    for appointment in appointments:
        key = (
            appointment["text"],
            appointment["url"]
        )

        if key not in seen:
            seen.add(key)
            unique_appointments.append(
                appointment
            )

    return unique_appointments


def send_telegram(message):
    bot_token = os.environ[
        "TELEGRAM_BOT_TOKEN"
    ]

    chat_id = os.environ[
        "TELEGRAM_CHAT_ID"
    ]

    telegram_url = (
        f"https://api.telegram.org/"
        f"bot{bot_token}/sendMessage"
    )

    response = requests.post(
        telegram_url,
        data={
            "chat_id": chat_id,
            "text": message
        },
        timeout=30
    )

    response.raise_for_status()

    print(
        "📱 Telegram-Nachricht erfolgreich gesendet."
    )


def send_email(new_appointments):
    smtp_host = "smtp.gmail.com"
    smtp_port = 587

    smtp_user = os.environ[
        "SMTP_USER"
    ]

    smtp_password = os.environ[
        "SMTP_PASSWORD"
    ]

    mail_to = os.environ[
        "MAIL_TO"
    ]

    message = EmailMessage()

    message["Subject"] = (
        "🚨 MiWuLa KiTa-Termine veröffentlicht!"
    )

    message["From"] = smtp_user
    message["To"] = mail_to

    appointment_lines = []

    for appointment in new_appointments:
        appointment_lines.append(
            f"- {appointment['text']}\n"
            f"  {appointment['url']}"
        )

    appointments_text = "\n\n".join(
        appointment_lines
    )

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

    with smtplib.SMTP(
        smtp_host,
        smtp_port
    ) as server:

        server.starttls()

        server.login(
            smtp_user,
            smtp_password
        )

        server.send_message(message)

    print(
        "📧 E-Mail erfolgreich versendet."
    )


def format_runtime(seconds):
    if seconds < 60:
        return f"{seconds:.2f} Sekunden"

    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60

    return (
        f"{minutes} Min. "
        f"{remaining_seconds:.1f} Sek."
    )


def main():
    # Startzeit nur für monitor.py
    python_start = time.perf_counter()

    current_appointments = (
        check_kita_page()
    )

    previous_state = (
        load_previous_state()
    )

    previous_appointments = []

    if previous_state:
        previous_appointments = (
            previous_state.get(
                "appointments",
                []
            )
        )

    print("MiWuLa KiTa Monitor")
    print("=" * 50)

    print(
        f"Aktuelle Termine: "
        f"{len(current_appointments)}"
    )

    print(
        f"Vorherige Termine: "
        f"{len(previous_appointments)}"
    )

    print()

    for appointment in current_appointments:
        print(
            f"TERMIN: "
            f"{appointment['text']}"
        )

        print(
            f"LINK:  "
            f"{appointment['url']}"
        )

        print("-" * 50)

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
        print(
            "🚨 NEUE TERMINE ERKANNT!"
        )

        for appointment in new_appointments:
            print(
                f"- {appointment['text']}"
            )

            print(
                f"  {appointment['url']}"
            )

        # Neue Termine per E-Mail melden
        send_email(
            new_appointments
        )

    else:
        print(
            "Keine neuen Termine."
        )

    # Python-Laufzeit messen
    python_runtime = (
        time.perf_counter()
        - python_start
    )

    # Zustand speichern
    save_state(
        current_appointments
    )

    print()

    print(
        "Python-Laufzeit: "
        f"{format_runtime(python_runtime)}"
    )

    print(
        "Zustand gespeichert."
    )

    print("=" * 50)

    # Python-Laufzeit an GitHub Actions übergeben
    github_output = os.environ.get(
        "GITHUB_OUTPUT"
    )

    if github_output:

        with open(
            github_output,
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                f"python_runtime={python_runtime:.2f}\n"
            )

            file.write(
                f"appointment_count="
                f"{len(current_appointments)}\n"
            )

            file.write(
                f"new_appointment_count="
                f"{len(new_appointments)}\n"
            )

    return {
        "python_runtime": python_runtime,
        "appointment_count": len(
            current_appointments
        ),
        "new_appointment_count": len(
            new_appointments
        )
    }


if __name__ == "__main__":

    try:
        main()

    except Exception as error:

        print()
        print(
            "🔴 FEHLER:"
        )

        print(
            f"{type(error).__name__}: "
            f"{error}"
        )

        # Fehler an GitHub Actions zurückgeben.
        # Telegram wird vom Workflow verschickt,
        # damit nur eine Nachricht entsteht.
        raise
