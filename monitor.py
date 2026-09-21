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

    # Links auf der Kita-Seite durchsuchen
    for link in soup.find_all("a", href=True):
        text = link.get_text(" ", strip=True)
        href = urljoin(URL, link["href"])

        if not text:
            continue

        # Datumsangaben erkennen
        date_matches = re.findall(
            r"\b\d{1,2}\.\d{1,2}(?:\.\d{2,4})?\b",
            text
        )

        if date_matches:
            appointments.append({
                "text": text,
                "url": href
            })

    # Falls keine Datumslinks gefunden wurden,
    # gesamten Seitentext durchsuchen
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
            unique_appointments.append(
                appointment
            )

    return unique_appointments


def send_email(new_appointments):
    smtp_host = "smtp.gmail.com"
    smtp_port = 587

    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    mail_to = os.environ["MAIL_TO"]

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

    print("📧 E-Mail erfolgreich versendet.")


def main():
    start_time = time.perf_counter()

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

    print(
        f"Aktuelle Termine: "
        f"{len(current_appointments)}"
    )

    print(
        f"Vorherige Termine: "
        f"{len(previous_appointments)}"
    )

    print()

    # Gefundene Termine ausgeben
    for appointment in current_appointments:
        print(
            f"TERMIN: {appointment['text']}"
        )

        print(
            f"LINK:  {appointment['url']}"
        )

        print("-" * 50)

    # Vorherige Termine als Schlüssel
    previous_keys = {
        (
            appointment["text"],
            appointment["url"]
        )
        for appointment in previous_appointments
    }

    # Nur neue Termine herausfiltern
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
            print(
                f"- {appointment['text']}"
            )

            print(
                f"  {appointment['url']}"
            )

        # E-Mail nur bei neuen Terminen
        send_email(new_appointments)

    else:
        print("Keine neuen Termine.")

    # Zustand speichern
    save_state(current_appointments)

    # Python-Laufzeit
    python_runtime = (
        time.perf_counter() - start_time
    )

    print()
    print(
        f"Python-Laufzeit: "
        f"{python_runtime:.2f} Sekunden"
    )

    print("Zustand gespeichert.")
    print("=" * 50)

    # GitHub Workflow kann diese Werte verwenden
    print(
        f"NEW_APPOINTMENTS={len(new_appointments)}"
    )

    print(
        f"APPOINTMENTS={len(current_appointments)}"
    )

    print(
        f"PYTHON_RUNTIME={python_runtime:.2f}"
    )

    # Daten für GitHub Actions bereitstellen
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
                f"new_appointments="
                f"{len(new_appointments)}\n"
            )

            file.write(
                f"appointments="
                f"{len(current_appointments)}\n"
            )

            file.write(
                f"python_runtime="
                f"{python_runtime:.2f}\n"
            )
if __name__ == "__main__":
    try:
        main()
        
        # ==================================================
        # LÖSUNG OHNE SECRETS: DIREKTE TEXT-WERTE
        # ==================================================
        # Trage hier dein echtes Token ein (Beispiel von vorhin):
        echtes_telegram_token = "8849293486:AAF34D4gOgXT4_7s-KnTt4PJBaEvoO3hVQI"
        
        # Holen der restlichen Variablen aus der GitHub-Umgebung
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        loop_token = os.environ.get("LOOP_TOKEN")

        # 1. Telegram Nachricht absenden (Absolut sichere URL-Generierung)
        if chat_id:
            msg = "🟢 MiWuLa KiTa Monitor: Prüfung erfolgreich durchgelaufen!"
            telegram_url = f"https://telegram.org{echtes_telegram_token}/sendMessage"
            
            try:
                res = requests.post(telegram_url, data={"chat_id": chat_id, "text": msg})
                if res.status_code == 200:
                    print("Telegram Nachricht erfolgreich gesendet.")
                else:
                    print(f"Telegram API Fehler: Status {res.status_code}, Antwort: {res.text}")
            except Exception as e:
                print(f"Fehler bei Telegram: {e}")

        # 2. GitHub Loop triggern
        if loop_token:
            github_url = "https://github.com"
            headers = {
                "Authorization": f"token {loop_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            data = {"event_type": "loop-check"}
            try:
                res = requests.post(github_url, json=data, headers=headers)
                print(f"GitHub Rerun signalisiert. Status: {res.status_code}")
            except Exception as e:
                print(f"Fehler beim GitHub Rerun: {e}")

    except Exception as error:
        print("🔴 FEHLER:")
        print(str(error))
        raise

