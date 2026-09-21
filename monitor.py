if __name__ == "__main__":
    try:
        main()
        
        # ==================================================
        # RADIKALE LÖSUNG OHNE VARIABLE / SECRETS / BASH
        # ==================================================
        
        # 1. Telegram Nachricht absenden
        # Wir nutzen dein echtes Token und deine Chat-ID direkt als Text!
        # (Ersetze die Werte in den Anführungszeichen, falls du sie geändert hast)
        BOT_TOKEN = "8849293486:AAF34D4gOgXT4_7s-KnTt4PJBaEvoO3hVQI"
        CHAT_ID = "5866136191" 
        
        telegram_url = f"https://telegram.org{BOT_TOKEN}/sendMessage"
        msg = f"🟢 MiWuLa KiTa Monitor Run: Prüfung erfolgreich durchgelaufen!"
        
        try:
            res = requests.post(telegram_url, data={"chat_id": CHAT_ID, "text": msg})
            if res.status_code == 200:
                print("Telegram Nachricht erfolgreich gesendet.")
            else:
                print(f"Telegram API Fehler: Status {res.status_code}, Antwort: {res.text}")
        except Exception as e:
            print(f"Fehler bei Telegram: {e}")

        # 2. GitHub Loop triggern
        # Wir laden den LOOP_TOKEN direkt aus dem Secret, weil dieser geheim bleiben muss,
        # aber wir schreiben die URL fest als Text rein!
        loop_token = os.environ.get("LOOP_TOKEN")
        
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
        else:
            print("LOOP_TOKEN fehlt in den Umgebungsvariablen.")

    except Exception as error:
        print("🔴 FEHLER:")
        print(str(error))
        raise
