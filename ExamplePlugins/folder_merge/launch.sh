#!/bin/bash

echo "📂 Folder Merge wird gestartet..."
echo "========================================"
echo ""
echo "Öffne GUI-Anwendung..."
echo ""

# Starte das Python-Tool im Hintergrund
python3 "$(dirname "$0")/file_merge.py" &

echo "✅ Folder Merge GUI wurde geöffnet!"
echo ""
echo "Features:"
echo "  • Mehrere Ordner in einen zusammenführen"
echo "  • Bitgenaue Duplikat-Erkennung"
echo "  • Intelligentes Ordner-Matching"
echo "  • Automatisches Aufräumen leerer Ordner"
echo ""
echo "Die Anwendung läuft jetzt in einem separaten Fenster."
