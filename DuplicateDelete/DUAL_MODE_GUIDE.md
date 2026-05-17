# 🔄 Primary/Secondary Mode - Benutzerhandbuch

## Übersicht

Der **Primary/Secondary Modus** ermöglicht es, einen Referenz-Ordner (PRIMARY) mit einem zu bereinigenden Ordner (SECONDARY) zu vergleichen.

### Funktionsweise

```
PRIMARY (Referenz)          SECONDARY (Wird bereinigt)
├── file.txt                ├── file.txt ← WIRD GELÖSCHT (Duplikat)
├── photo.jpg               ├── photo.jpg ← WIRD GELÖSCHT (Duplikat)
└── document.pdf            ├── document.pdf ← BLEIBT (anderer Inhalt)
                            └── backup.zip ← BLEIBT (nicht in PRIMARY)
```

## 🔒 Wichtige Regeln

1. **PRIMARY wird NIEMALS verändert** - Schreibgeschützt, nur Referenz
2. **Nur gleiche Dateinamen werden verglichen** - "file.txt" nur mit "file.txt"
3. **Bit-exakter Vergleich** - SHA-256 Hash-Prüfung
4. **Nur bei Namens- UND Inhalts-Übereinstimmung wird gelöscht**

## 📋 Vergleichs-Logik

### Schritt 1: Namens-Check
```
PRIMARY/photo.jpg  vs  SECONDARY/photo.jpg  ✓ Namen identisch
PRIMARY/photo.jpg  vs  SECONDARY/image.jpg  ✗ Namen unterschiedlich → SKIP
```

### Schritt 2: Hash-Check (nur bei gleichem Namen)
```
PRIMARY/file.txt  (Hash: abc123)
SECONDARY/file.txt (Hash: abc123)  → LÖSCHEN (identisch)

PRIMARY/file.txt  (Hash: abc123)
SECONDARY/file.txt (Hash: xyz789)  → BEHALTEN (unterschiedlich)
```

## 🎯 Verwendung

### 1. Mode auswählen
- Radio Button: "Primary/Secondary (clean secondary)" wählen

### 2. PRIMARY Ordner auswählen
- Klick auf "Select Primary Folder"
- Wähle den Referenz-Ordner (z.B. dein Haupt-Archiv)
- ✓ Grünes Häkchen erscheint

### 3. SECONDARY Ordner auswählen
- Klick auf "Select Secondary Folder"
- Wähle den zu bereinigenden Ordner (z.B. Backup-Ordner)
- ✓ Grünes Häkchen erscheint

### 4. Scan starten
- "Start Scan" Button wird aktiv
- Klick auf "Start Scan"
- Beobachte den Fortschritt im Activity Log

## 📊 Activity Log Beispiel

```
[14:30:00] ℹ️ Starting DUAL FOLDER scan
[14:30:00] ℹ️ PRIMARY (Reference): /path/to/primary
[14:30:00] ⚠️ SECONDARY (Clean):   /path/to/secondary
[14:30:01] ℹ️ Phase 1: Collecting PRIMARY folder files...
[14:30:01] ℹ️ Found 100 files in PRIMARY folder
[14:30:02] ℹ️ Phase 2: Hashing PRIMARY files...
[14:30:05] ℹ️ Phase 3: Scanning SECONDARY folder...
[14:30:05] ℹ️ Found 150 files in SECONDARY folder
[14:30:06] ℹ️ Phase 4: Comparing SECONDARY files with PRIMARY...
[14:30:07] 🗑️ DELETE: /secondary/document.txt
[14:30:07] ℹ️   → Duplicate of PRIMARY: /primary/document.txt
[14:30:07] ✓   → Freed: 1.25 KB
[14:30:08] 📌 KEEP: /secondary/report.txt (same name, different content)
[14:30:10] ✓ Dual folder scan completed successfully!
[14:30:10] ✓ PRIMARY folder is UNCHANGED (protected)
[14:30:10] ✓ SECONDARY folder cleaned of 45 duplicates
```

## 📈 Statistik

Nach dem Scan wird eine Statistik angezeigt:

```
📊 SCAN STATISTICS 📊

Mode:                     Primary/Secondary
Primary files (protected): 100
Secondary files (scanned): 150
Files deleted:            45
Files kept in secondary:  105
Space freed:              12.45 MB
Errors encountered:       0
```

## 🧪 Testen

### Testdaten erstellen:
```bash
cd TESTS_VALIDATION
python3 create_dual_test_data.py
```

### Erwartete Ergebnisse:
- **10 Testfälle** erstellt
- **PRIMARY:** 10 Dateien (bleiben unverändert)
- **SECONDARY:** 11 Dateien → 7 werden gelöscht, 3 bleiben

### Im GUI testen:
1. Starte Anwendung
2. Wähle "Primary/Secondary" Mode
3. PRIMARY: `TESTS_VALIDATION/TEST_PRIMARY`
4. SECONDARY: `TESTS_VALIDATION/TEST_SECONDARY`
5. Klick "Start Scan"

## ✅ Anwendungsfälle

### Use Case 1: Backup-Ordner bereinigen
```
PRIMARY:   /Users/Me/Documents (Haupt-Archiv)
SECONDARY: /Volumes/Backup/Documents (Backup)

Ergebnis: Alle Duplikate aus Backup entfernt, nur Unique bleibt
```

### Use Case 2: Download-Ordner aufräumen
```
PRIMARY:   /Users/Me/Photos (Haupt-Sammlung)
SECONDARY: /Users/Me/Downloads (Download-Ordner)

Ergebnis: Alle bereits vorhandenen Fotos aus Downloads entfernt
```

### Use Case 3: Projekt-Synchronisation
```
PRIMARY:   /Projects/Main (Master-Version)
SECONDARY: /Projects/Backup (Alte Kopien)

Ergebnis: Nur unterschiedliche Versionen bleiben in Backup
```

## ⚠️ Wichtige Hinweise

### Sicherheit
- ✅ PRIMARY wird **NIEMALS** verändert - zu 100% sicher
- ⚠️ SECONDARY wird bereinigt - **Backup vorher erstellen!**
- ✅ Nur bit-identische Dateien werden gelöscht
- ✅ Bei unterschiedlichem Inhalt → Datei bleibt

### Performance
- Hash-Berechnung: ~100-500 Dateien/Sekunde
- Größere PRIMARY-Ordner brauchen länger (alle werden gehasht)
- Pause/Abort jederzeit möglich

### Einschränkungen
- ❌ Keine User-Popups bei ähnlichen Namen (automatisch)
- ❌ Keine "Nummerierungs-Erkennung" (1), (2) im Dual-Modus
- ✅ Nur exakte Namens- und Inhalts-Übereinstimmung

## 🔍 Vergleich: Single vs. Dual Mode

| Feature | Single Mode | Dual Mode |
|---------|-------------|-----------|
| Ordner | 1 | 2 (Primary + Secondary) |
| Löschen aus | Gleicher Ordner | Nur Secondary |
| Primary Schutz | N/A | ✅ 100% geschützt |
| User-Popups | ✅ Bei ähnlichen Namen | ❌ Nein |
| Nummerierungs-Erkennung | ✅ Ja | ❌ Nein |
| Namens-Vergleich | Optional | ✅ Immer (Pflicht) |

## 💡 Tipps

1. **Immer Backup erstellen** vor dem ersten Scan
2. **Teste zuerst** mit den Test-Daten
3. **PRIMARY = wichtiger Ordner**, SECONDARY = zu bereinigen
4. **Activity Log beobachten** während des Scans
5. **Pause nutzen** wenn etwas unklar ist

## 🆘 Problemlösung

**Q: PRIMARY wurde verändert?**
A: Das ist unmöglich - der Code greift nur lesend auf PRIMARY zu.

**Q: Datei wurde gelöscht obwohl Inhalt anders?**
A: Unmöglich - nur bei identischem Hash wird gelöscht. Prüfe Activity Log.

**Q: Datei wurde nicht gelöscht obwohl identisch?**
A: Prüfe ob der **Dateiname** exakt gleich ist (inkl. Groß-/Kleinschreibung).

**Q: Scan dauert sehr lange?**
A: Viele Dateien in PRIMARY = länger. Nutze Pause oder wähle kleineren PRIMARY-Ordner.

---

**Version:** 2.0
**Modus:** Primary/Secondary (Dual Folder)
**Status:** Production Ready ✅
