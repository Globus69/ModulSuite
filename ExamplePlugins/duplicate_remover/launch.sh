#!/bin/bash

echo "🗂️  Duplicate Remover wird gestartet..."
echo "========================================"
echo ""
echo "Öffne GUI-Anwendung..."
echo ""

# Starte das Python-Tool im Hintergrund
python3 "$(dirname "$0")/duplicate_remover.py" &

echo "✅ Duplicate Remover GUI wurde geöffnet!"
echo ""
echo "Features:"
echo "  • Single Folder Mode - Duplikate in einem Ordner finden"
echo "  • Primary/Secondary Mode - Zwei Ordner vergleichen"
echo "  • SHA-256 Hashing für 100% Genauigkeit"
echo "  • Live Activity Log"
echo ""
echo "Die Anwendung läuft jetzt in einem separaten Fenster."
