#!/bin/bash

echo "📁 FILE COUNTER"
echo "================================"
echo "Analysiere Home-Verzeichnis..."
echo ""

TOTAL=$(find ~ -type f 2>/dev/null | wc -l | xargs)
DIRS=$(find ~ -type d 2>/dev/null | wc -l | xargs)

echo "Dateien:      $TOTAL"
echo "Verzeichnisse: $DIRS"
echo ""
echo "Top 5 Dateitypen:"
echo "--------------------------------"
find ~ -type f -name "*.*" 2>/dev/null | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -5 | awk '{print "  " $2 ": " $1 " Dateien"}'
echo "================================"
