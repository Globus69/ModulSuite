# 🆕 Neue Features - Version 2.0

## Hauptneuerung: Dual Folder Mode (Primary/Secondary)

### Was ist neu?

Die Software bietet jetzt **zwei Modi**:

1. **Single Folder Mode** (Original)
   - Findet Duplikate in einem Ordner
   - Intelligente Priorisierung
   - User-Popups bei ähnlichen Namen

2. **Primary/Secondary Mode** (NEU!)
   - Vergleicht zwei Ordner
   - PRIMARY = Referenz (schreibgeschützt)
   - SECONDARY = wird bereinigt
   - Nur Namens- UND Inhalts-Übereinstimmung → Löschung

---

## 🎯 Primary/Secondary Mode

### Konzept

```
PRIMARY (Master)              SECONDARY (Backup/Downloads)
├── photo.jpg                 ├── photo.jpg → GELÖSCHT
├── document.pdf              ├── document.pdf → BLEIBT (anders)
└── video.mp4                 ├── video.mp4 → GELÖSCHT
                              └── extra.txt → BLEIBT (nicht in PRIMARY)

Ergebnis:
- PRIMARY: Unverändert (3 Dateien)
- SECONDARY: Nur Unique (2 Dateien: document.pdf, extra.txt)
```

### Anwendungsfälle

1. **Backup-Ordner bereinigen**
   - PRIMARY = Haupt-Archiv
   - SECONDARY = Backup-Kopie
   - Entferne alle redundanten Duplikate aus Backup

2. **Download-Ordner aufräumen**
   - PRIMARY = Deine organisierte Foto-Sammlung
   - SECONDARY = Download-Ordner
   - Lösche bereits archivierte Fotos aus Downloads

3. **Projekt-Synchronisation**
   - PRIMARY = Master-Projekt
   - SECONDARY = Alte Arbeitsversion
   - Behalte nur unterschiedliche Versionen

---

## 🔄 Mode-Vergleich

| Feature | Single Mode | Primary/Secondary |
|---------|-------------|-------------------|
| **Ordner-Anzahl** | 1 | 2 |
| **Löschen aus** | Gleicher Ordner | Nur SECONDARY |
| **PRIMARY Schutz** | N/A | ✅ 100% geschützt |
| **Vergleichs-Methode** | Hash-basiert | Name + Hash |
| **User-Popups** | ✅ Bei ähnlichen Namen | ❌ Automatisch |
| **Nummerierungs-Erkennung** | ✅ (1), (2) etc. | ❌ Nein |
| **Use Case** | Ordner aufräumen | Ordner vergleichen |

---

## 📖 Verwendung

### Single Mode (Original)

1. Wähle Radio Button: "Single Folder"
2. Klick "Select Folder"
3. Wähle Ordner
4. Beobachte Scan

**Funktioniert wie bisher!**

### Primary/Secondary Mode (NEU)

1. Wähle Radio Button: "Primary/Secondary"
2. Klick "Select Primary Folder" → Referenz-Ordner
3. Klick "Select Secondary Folder" → Zu bereinigender Ordner
4. Klick "Start Scan"
5. Beobachte Activity Log

---

## 🧪 Testen

### Single Mode Test:
```bash
cd TESTS_VALIDATION
python3 create_test_data.py
# Im GUI: Wähle TESTS_VALIDATION/TEST
```

### Dual Mode Test:
```bash
cd TESTS_VALIDATION
python3 create_dual_test_data.py
# Im GUI:
#   PRIMARY: TESTS_VALIDATION/TEST_PRIMARY
#   SECONDARY: TESTS_VALIDATION/TEST_SECONDARY
```

---

## 🔒 Sicherheit

### Single Mode:
- Intelligente Dateiauswahl
- User-Popups bei Unsicherheit
- Bevorzugt Dateien ohne (1), (2) Nummerierung

### Dual Mode:
- **PRIMARY ist 100% geschützt** (nur Lese-Zugriff)
- **SECONDARY wird bereinigt** (Schreib-Zugriff)
- Nur bei exakter Namens- UND Inhalts-Übereinstimmung
- Keine Löschung bei Unsicherheit

---

## 📊 Neue Statistiken

### Single Mode Statistik:
```
Mode:                     Single Folder
Total files scanned:      30
Duplicate groups found:   10
Files deleted:            15
Files kept:               15
```

### Dual Mode Statistik:
```
Mode:                     Primary/Secondary
Primary files (protected): 10
Secondary files (scanned): 11
Files deleted:            7
Files kept in secondary:  4
Space freed:              102.50 KB
```

---

## 🎨 GUI Änderungen

### Neue Elemente:

1. **Mode-Auswahl** (oben)
   - Radio Buttons für Single/Dual Mode
   - Dynamischer Wechsel

2. **Dual Mode Buttons**
   - "Select Primary Folder" (blau markiert)
   - "Select Secondary Folder" (rot markiert)
   - "Start Scan" (wird aktiv nach beiden Auswahlen)

3. **Folder Labels**
   - Zeigt ausgewählte Ordner mit ✓
   - Farbcodiert (blau/rot)

---

## 💾 Kompatibilität

- ✅ Alte Single-Mode Funktionalität **komplett erhalten**
- ✅ Alle bisherigen Features funktionieren
- ✅ Bestehende Tests laufen weiter
- ✅ Keine Breaking Changes

---

## 📚 Dokumentation

### Neue Dokumente:
- **DUAL_MODE_GUIDE.md** - Ausführliche Anleitung für Dual Mode
- **README_NEW_FEATURES.md** - Diese Datei
- **create_dual_test_data.py** - Test-Daten Generator für Dual Mode

### Aktualisierte Dokumente:
- **duplicate_remover.py** - Erweitert mit Dual Mode
- **STRUKTUR.md** - Aktualisierte Projekt-Struktur

---

## 🚀 Migration von v1.0 zu v2.0

**Keine Migration nötig!**

- Alte Verwendung funktioniert weiterhin
- Einfach Single Mode wählen = alte Funktionalität
- Dual Mode ist optional/zusätzlich

---

## 🔮 Geplante Features

Mögliche zukünftige Erweiterungen:
- [ ] Dry-Run Mode (zeige was gelöscht würde)
- [ ] Whitelist/Blacklist für Datei-Typen
- [ ] Export der Scan-Ergebnisse (CSV/JSON)
- [ ] Undo-Funktionalität

---

## 📞 Support

Bei Fragen:
1. Lies **DUAL_MODE_GUIDE.md** für Dual Mode Details
2. Lies **README.md** für allgemeine Infos
3. Teste mit den mitgelieferten Test-Daten
4. Prüfe das Activity Log bei Problemen

---

**Version:** 2.0
**Release:** 11. Februar 2026
**Status:** Production Ready ✅
