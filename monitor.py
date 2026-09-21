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

URL = "https://miniatur-wunderland.de"
STATE_FILE = Path("state.json")
HEADERS = {"User-Agent": "MiWuLa-Kita-Monitor/1.0"}

def load_previous_state():
    if not STATE_FILE.exists():
        return None
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return None

def save_state(appointments):
    data = {"appointments": appointments}
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

def check_kita_page():
    response = requests.get(URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    appointments = []

    for link in soup.find_all("a", href=True):
        text = link.get_text(" ", strip=True)
        href = urljoin(URL, link["href"])
        if not text:
            continue
        date_matches = re.findall(r"\b\d{1,2}\.\d{1,2}(?:\.\d{2,4})?\b", text)
        if date_matches:
            appointments.append({"text": text, "url": href})

    if not appointments:
        text = soup.get_text(" ", strip=True)
        date_matches = re.findall(r"\b\d{1,2}\.\d{1,2}(?:\.\d{2,4})?\b", text)
        for date in date_matches:
            appointments.append({"text": date, "url": URL})

    unique_appointments = []
    seen = set()
    for appointment in appointments:
        key = (appointment["text"], appointment["url"])
        if key not in seen:
            seen.add(key)
            unique_appointments.append(appointment)
    return unique_appointments

def send_email(new_appointments):
    smtp_host = "://gmail.com"
    smtp_port = 587
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    mail_to = os.environ.get("MAIL_TO", "")

    if not smtp_user or not smtp_password or not mail_to:
        print("📧 E-Mail-Variablen fehlen. Überspringe E-Mail-Versand.")
        return

    message = EmailMessage()
    message["Subject"] = "🚨 MiWuLa KiTa-Termine veröffentlicht!"
    message["From"] = smtp_user
    message["To"] = mail_to

    appointment_lines = [f"- {app['text']}\n  {app['url']}" for app in new_appointments]
    appointments_text = "\n\n".join(appointment_lines)

    message.set_content(f"""Hallo,
auf der MiWuLa-KiTa-Seite wurden neue Termine gefunden.
Gefundene Termine:
{appointments_text}

Zur KiTa-Seite:
{URL}

Viele Grüße
Dein MiWuLa KiTa Monitor
""")

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(message)
    print("📧 E-Mail erfolgreich versendet.")

def main():
    start_time = time.perf_counter()
    current_appointments = check_kita_page()
    previous_state = load_previous_state()
    previous_appointments = previous_state.get("appointments", []) if previous_state else []

    print("MiWuLa KiTa Monitor")
    print("=" * 50)
    print(f"Aktuelle Termine: {len(current_appointments)}")
    print(f"Vorherige Termine: {len(previous_appointments)}\n")

    for appointment in current_appointments:
        print(f"TERMIN: {appointment['text']}")
        print(f"LINK:  {appointment['url']}")
        print("-" * 50)

    previous_keys = {(app["text"], app["url"]) for app in previous_appointments}
    new_appointments = [app for app in current_appointments if (app["text"], app["url"]) not in previous_keys]

    if new_appointments:
        print("\n🚨 NEUE TERMINE ERKANNT!\n")
        for appointment in new_appointments:
            print(f"- {appointment['text']}\n  {appointment['url']}")
        send_email(new_appointments)
    else:
        print("Keine neuen Termine.")

    save_state(current_appointments)
    python_runtime = time.perf_counter() - start_time
    print(f"\nPython-Laufzeit: {python_runtime:.2f} Sekunden")
    print("Zustand gespeichert.")
    print("=" * 50)

if __name__ == "__main__":
    try:
        # 1. Den eigentlichen Webseiten-Check ausführen
        main()
        
        # ==================================================
        # AUTOMATISCHER TELEGRAM & GITHUB DISPATCH RERUN
        # ==================================================
        # HIER DEINE GEFUNDENE ZAHLEN-ID VOM CLICKALGO-FINDER EINTRAGEN:
        CHAT_ID = "HIER_DEINE_REINE_NUMMERN_CHAT_ID_EINTRAGEN"
        BOT_TOKEN = "8849293486:AAF34D4gOgXT4_7s-KnTt4PJBaEvoO3hVQI"
        loop_token = os.environ.get("LOOP_TOKEN")

        # Telegram Nachricht absenden
        if CHAT_ID != "5866136191":
            msg = "🟢 MiWuLa KiTa Monitor: Prüfung erfolgreich durchgelaufen!"
            telegram_url = f"https://telegram.org{BOT_TOKEN}/sendMessage"
            try:
                res = requests.post(telegram_url, data={"chat_id": CHAT_ID, "text": msg})
                if res.status_code == 200:
                    print("Telegram Nachricht erfolgreich gesendet.")
                else:
                    print(f"Telegram API Fehler: Status {res.status_code}")
            except Exception as e:
                print(f"Fehler bei Telegram: {e}")

        # GitHub Loop triggern
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
