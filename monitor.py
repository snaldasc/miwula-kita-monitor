name: MiWuLa KiTa Monitor

on:
  workflow_dispatch:

jobs:
  check-kita:
    runs-on: ubuntu-latest

    permissions:
      contents: write

    steps:
      - name: Repository auschecken
        uses: actions/checkout@v4

      - name: Python einrichten
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Abhängigkeiten installieren
        run: pip install -r requirements.txt

      - name: MiWuLa Seite prüfen
        run: python monitor.py

      - name: Zustand speichern
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
