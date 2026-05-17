#!/bin/bash
cd "$(dirname "$0")"

echo "=== DEBUG ==="
echo "Verzeichnis: $(pwd)"
echo "Python: $(which python3)"
echo "Datei: $(ls -la file_merge.py)"
echo "============="
echo ""

if ! command -v python3 &>/dev/null; then
    echo "Fehler: Python 3 ist nicht installiert."
    echo "Drücke eine Taste zum Schließen..."
    read -n 1
    exit 1
fi

python3 file_merge.py

if [ $? -ne 0 ]; then
    echo ""
    echo "Das Programm wurde mit einem Fehler beendet."
    echo "Drücke eine Taste zum Schließen..."
    read -n 1
fi
