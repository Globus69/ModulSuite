# 🗂️ Duplicate File Remover v2.0.1

Ein professionelles Python-Tool mit GUI zum Auffinden und Entfernen von exakten Datei-Duplikaten.

## ✨ Hauptfeatures

### Zwei Modi verfügbar:

#### 1️⃣ **Single Folder Mode**
- Findet und entfernt Duplikate innerhalb eines Ordners
- Intelligente Priorisierung (bevorzugt Dateien ohne "(1)" Nummerierung)
- User-Bestätigung bei ähnlichen Dateinamen

#### 2️⃣ **Primary/Secondary Mode** ⭐ NEU
- Vergleicht zwei Ordner miteinander
- **PRIMARY** = Referenz-Ordner (100% schreibgeschützt, niemals verändert)
- **SECONDARY** = Wird bereinigt (Duplikate werden gelöscht)
- Nur bei exakter Namens- UND Inhalts-Übereinstimmung

### Kern-Funktionen:

✅ **Bit-genaue Duplikaterkennung** - SHA-256 Hashing für 100% Genauigkeit
✅ **Zwei flexible Modi** - Single oder Primary/Secondary
✅ **PRIMARY Schutz** - Referenz-Ordner wird niemals verändert
✅ **Live Activity Log** - Sehe genau was passiert
✅ **Pause & Abort** - Scan jederzeit unterbrechen
✅ **Detaillierte Statistik** - Gesparte Speicherplatz, gelöschte Dateien
✅ **Verschachtelte Ordner** - Durchsucht alle Unterordner
✅ **Sichere Operationen** - Keine Löschung bei Unsicherheit

---

## 🚀 Installation & Start

### Voraussetzungen
- Python 3.6 oder höher
- Tkinter (normalerweise mit Python vorinstalliert)

### Start
```bash
# Einfachster Weg (Doppelklick im Finder)
./start.command

# Oder im Terminal
python3 duplicate_remover.py
```

---

## 📖 Verwendung

### Single Folder Mode

1. Wähle Radio Button: **"Single Folder"**
2. Klick auf **"Select Folder"**
3. Wähle den zu scannenden Ordner
4. Beobachte den Scan im Activity Log
5. Bei ähnlichen Dateinamen: Entscheide "Delete" oder "Keep Both"
6. Prüfe die finale Statistik

**Beispiel:**
```
Ordner/
├── photo.jpg          ← BEHALTEN
├── photo (1).jpg      ← GELÖSCHT (automatisch)
├── document_v1.pdf    ← User-Entscheidung erforderlich
└── document_v2.pdf    ← (ähnliche Namen)
```

### Primary/Secondary Mode ⭐

1. Wähle Radio Button: **"Primary/Secondary"**
2. Klick auf **"Select Primary Folder"** → Wähle Referenz-Ordner
3. Klick auf **"Select Secondary Folder"** → Wähle zu bereinigenden Ordner
4. Klick auf **"Start Scan"**
5. Beobachte den Vergleich im Activity Log
6. Prüfe die Statistik

**Beispiel:**
```
PRIMARY (Referenz)         SECONDARY (Wird bereinigt)
├── photo.jpg              ├── photo.jpg      → GELÖSCHT ✓
├── document.pdf           ├── document.pdf   → BLEIBT (anderer Inhalt)
└── video.mp4              ├── video.mp4      → GELÖSCHT ✓
                           └── backup.zip     → BLEIBT (nicht in PRIMARY)

Ergebnis:
- PRIMARY: Unverändert (3 Dateien)
- SECONDARY: Nur Unique (2 Dateien)
```

**Wichtig:**
- Nur Dateien mit **gleichem Namen** werden verglichen
- Nur bei **gleichem Namen UND Inhalt** wird gelöscht
- PRIMARY ist **100% geschützt** (nur Lese-Zugriff)

---

## 🔒 Sicherheits-Features

### Single Mode:
- Intelligente Dateiauswahl (bevorzugt Originale)
- User-Popups bei unsicheren Fällen
- Keine Löschung bei 1-Byte-Unterschied

### Dual Mode:
- **PRIMARY absolut geschützt** (nur Lese-Zugriff)
- Ordner-Überlappung wird verhindert
- Namens-Vergleich ist Pflicht (kein "ähnliche Namen" Modus)
- Nur bit-exakte Übereinstimmung führt zu Löschung

---

## 🧪 Testen

### Testdaten erstellen:
```bash
cd TESTS_VALIDATION
python3 create_dual_test_data.py
```

### Im GUI testen:
1. Starte die Anwendung
2. Wähle **"Primary/Secondary"** Mode
3. PRIMARY: `TESTS_VALIDATION/TEST_PRIMARY`
4. SECONDARY: `TESTS_VALIDATION/TEST_SECONDARY`
5. Klick **"Start Scan"**

**Erwartete Ergebnisse:**
- PRIMARY: 10 Dateien (unverändert)
- SECONDARY: 11 → 5 Dateien (6 gelöscht)
- Freigegebener Speicher: ~102 KB

### Alle Tests ausführen:
```bash
cd TESTS_VALIDATION
python3 test_corrections.py
python3 test_gui_functions.py
python3 test_primary_protection.py
```

---

## 📊 GUI Elemente

### Mode-Auswahl (oben):
- 🔘 **Single Folder** - Duplikate in einem Ordner finden
- 🔘 **Primary/Secondary** - Zwei Ordner vergleichen

### Single Mode:
- Button: **"Select Folder"**

### Dual Mode:
- Button: **"Select Primary Folder"** (blau markiert)
- Button: **"Select Secondary Folder"** (rot markiert)
- Button: **"Start Scan"** (wird aktiv nach beiden Auswahlen)

### Allgemein:
- **Progress Label** - Zeigt aktuellen Fortschritt
- **Activity Log** - Detaillierte Aktionen mit Zeitstempel
- **Pause** - Scan pausieren/fortsetzen
- **Abort** - Scan abbrechen
- **Status** - Ready/Scanning/Paused/Error

---

## 📈 Statistik-Beispiele

### Single Mode:
```
📊 SCAN STATISTICS 📊

Mode:                     Single Folder
Total files scanned:      30
Duplicate groups found:   10
Files deleted:            15
Files kept:               15
Space freed:              12.45 KB
User decisions required:  2
Errors encountered:       0
```

### Dual Mode:
```
📊 SCAN STATISTICS 📊

Mode:                     Primary/Secondary
Primary files (protected): 10
Secondary files (scanned): 11
Files deleted:            6
Files kept in secondary:  5
Space freed:              102.50 KB
Errors encountered:       0
```

---

## 💡 Anwendungsfälle

### Use Case 1: Download-Ordner aufräumen
```bash
Mode: Primary/Secondary
PRIMARY:   ~/Documents/Photos (Haupt-Sammlung)
SECONDARY: ~/Downloads (Download-Ordner)
Ergebnis:  Bereits archivierte Fotos aus Downloads entfernt
```

### Use Case 2: Backup-Ordner bereinigen
```bash
Mode: Primary/Secondary
PRIMARY:   ~/Documents (Master)
SECONDARY: /Volumes/Backup/Documents
Ergebnis:  Nur unterschiedliche Versionen bleiben in Backup
```

### Use Case 3: Ordner aufräumen
```bash
Mode: Single Folder
Ordner:    ~/Downloads
Ergebnis:  Alle Duplikate innerhalb des Ordners entfernt
```

---

## 🔍 Mode-Vergleich

| Feature | Single Mode | Primary/Secondary |
|---------|-------------|-------------------|
| **Ordner-Anzahl** | 1 | 2 |
| **Löschen aus** | Gleicher Ordner | Nur SECONDARY |
| **PRIMARY Schutz** | N/A | ✅ 100% |
| **Vergleichs-Methode** | Hash-basiert | Name + Hash |
| **User-Popups** | ✅ Bei ähnlichen Namen | ❌ Automatisch |
| **Nummerierungs-Erkennung** | ✅ (1), (2) etc. | ❌ Nein |
| **Use Case** | Ordner aufräumen | Ordner vergleichen |

---

## 📚 Dokumentation

- **README.md** - Diese Datei (Haupt-Dokumentation)
- **DUAL_MODE_GUIDE.md** - Ausführliche Anleitung für Dual Mode
- **README_NEW_FEATURES.md** - Neue Features in v2.0
- **FEHLERANALYSE_UND_KORREKTUREN.md** - Test-Report
- **TEST_SUMMARY.md** - Test-Zusammenfassung

---

## ⚠️ Wichtige Hinweise

### Vor dem ersten Einsatz:
1. **Erstelle immer ein Backup** wichtiger Daten
2. **Teste zuerst** mit den mitgelieferten Testdaten
3. **Lies die Dokumentation** für deinen Use Case

### Einschränkungen:
- Versteckte Dateien (beginnend mit ".") werden übersprungen
- Groß-/Kleinschreibung wird beachtet
- Im Dual Mode: Nur exakte Namens-Übereinstimmung

### Performance:
- Hash-Berechnung: ~100-500 Dateien/Sekunde
- Größere PRIMARY-Ordner benötigen mehr Zeit
- Pause/Abort jederzeit möglich

---

## 🆘 Problemlösung

**Q: PRIMARY wurde verändert?**
A: Unmöglich - der Code greift nur lesend auf PRIMARY zu. Prüfe das Activity Log.

**Q: Datei wurde nicht gelöscht obwohl identisch?**
A: Im Dual Mode muss der **Dateiname exakt gleich** sein (inkl. Groß-/Kleinschreibung).

**Q: Scan dauert sehr lange?**
A: Viele Dateien = länger. Nutze Pause oder wähle kleineren Ordner.

**Q: "Similar Filenames" Popup erscheint nicht im Dual Mode?**
A: Korrekt - im Dual Mode gibt es keine User-Popups. Nur exakte Matches werden gelöscht.

---

## 🔧 Technische Details

- **Sprache:** Python 3.6+
- **GUI:** Tkinter
- **Hash:** SHA-256 (bit-genau)
- **Threading:** Daemon Threads für GUI-Responsiveness
- **Dateigröße:** Keine Limits
- **Ordner-Tiefe:** Unbegrenzt (rekursiv)

---

## 📝 Changelog

### Version 2.0.1 (Current)
- ✅ Dual Mode implementiert (Primary/Secondary)
- ✅ PRIMARY Schutz (100% schreibgeschützt)
- ✅ Threading Race Condition behoben
- ✅ Ordner-Überlappungs-Prüfung hinzugefügt
- ✅ Ordner-Existenz-Validierung
- ✅ Umfassende Tests (34/34 passed)
- ✅ Vollständige Dokumentation

### Version 1.0
- ✅ Single Folder Mode
- ✅ Intelligente Duplikat-Erkennung
- ✅ User-Popups bei ähnlichen Namen

---

## 📞 Support

Bei Fragen oder Problemen:

1. **Dual Mode Details:** Siehe `DUAL_MODE_GUIDE.md`
2. **Neue Features:** Siehe `README_NEW_FEATURES.md`
3. **Test-Report:** Siehe `FEHLERANALYSE_UND_KORREKTUREN.md`
4. **Activity Log prüfen:** Zeigt alle Aktionen und Fehler

---

## 📄 Lizenz

Frei verwendbar für private und kommerzielle Zwecke.

---

**Version:** 2.0.1
**Status:** ✅ Production Ready
**Letzte Aktualisierung:** 11. Februar 2026

🎉 **Bereit für den Einsatz!**
