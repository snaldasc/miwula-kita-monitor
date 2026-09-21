name: MiWuLa KiTa Monitor

on:
  workflow_dispatch:

  schedule:
    - cron: "*/10 * * * *"

jobs:
  check-kita:
    runs-on: ubuntu-latest

    permissions:
      contents: write

    env:
      SMTP_USER: ${{ secrets.SMTP_USER }}
      SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
      MAIL_TO: ${{ secrets.MAIL_TO }}
      TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
      TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}

    steps:

      # --------------------------------------------------
      # Gesamten GitHub-Job starten
      # --------------------------------------------------

      - name: Gesamtstartzeit erfassen
        run: |
          echo "START_TIME=$(date +%s.%N)" >> "$GITHUB_ENV"

      # --------------------------------------------------
      # Repository
      # --------------------------------------------------

      - name: Repository auschecken
        uses: actions/checkout@v4

      # --------------------------------------------------
      # Python
      # --------------------------------------------------

      - name: Python einrichten
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      # --------------------------------------------------
      # Abhängigkeiten
      # --------------------------------------------------

      - name: Abhängigkeiten installieren
        run: |
          pip install -r requirements.txt

      # --------------------------------------------------
      # Monitor
      # --------------------------------------------------

      - name: MiWuLa Seite prüfen
        id: monitor
        run: |
          python monitor.py

      # --------------------------------------------------
      # Zustand speichern
      # --------------------------------------------------

      - name: Zustand speichern
        if: success()
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          git add state.json

          if git diff --cached --quiet; then
            echo "Keine Änderung am Zustand."
          else
            git commit -m "Update MiWuLa KiTa status"
            git push
          fi

      # --------------------------------------------------
      # Gesamtlaufzeit berechnen
      # --------------------------------------------------

      - name: Gesamtlaufzeit berechnen
        if: always()
        run: |

          END_TIME=$(date +%s.%N)

          TOTAL_RUNTIME=$(python -c "
          start = float('$START_TIME')
          end = float('$END_TIME')
          print(f'{end - start:.2f}')
          ")

          echo "TOTAL_RUNTIME=$TOTAL_RUNTIME" >> "$GITHUB_ENV"

          echo "======================================"
          echo "Gesamtlaufzeit: $TOTAL_RUNTIME Sekunden"
          echo "======================================"

      # --------------------------------------------------
      # Telegram Status
      # --------------------------------------------------

      - name: Telegram Status senden
        if: always()
        run: |

          if [ "${{ job.status }}" = "success" ]; then
            STATUS="🟢 Erfolgreich"
            TERMINES="Termine: ${{ steps.monitor.outputs.appointment_count }}"
            NEUE_TERMINE="Neue Termine: ${{ steps.monitor.outputs.new_appointment_count }}"
            PYTHON_TIME="${{ steps.monitor.outputs.python_runtime }} Sekunden"
          else
            STATUS="🔴 FEHLER"
            TERMINES="Termine: nicht verfügbar"
            NEUE_TERMINE="Neue Termine: nicht verfügbar"
            PYTHON_TIME="nicht verfügbar"
          fi

          MESSAGE="MiWuLa KiTa Monitor

          ${STATUS}

          📅 ${TERMINES}
          🚨 ${NEUE_TERMINE}

          ⏱️ Python: ${PYTHON_TIME}
          ⏱️ Gesamt: ${TOTAL_RUNTIME} Sekunden

          🔢 Run: ${{ github.run_number }}"

          curl -sS \
            -X POST \
            "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_CHAT_ID}" \
            --data-urlencode "text=${MESSAGE}"
