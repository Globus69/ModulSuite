# SWS Suite — Projektübersicht

## Enthaltene Projekte

### 1. DuplicateDelete
**Pfad:** `DuplicateDelete/duplicate_remover.py`  
**Start:** `DuplicateDelete/start.command`  
**Typ:** Python/Tkinter GUI-Anwendung  
**Version:** 2.0.1

**Funktion:** Findet und entfernt bitgenau identische Dateien (SHA-256 Hashing).

**Modi:**
- **Single Folder Mode** — Duplikate innerhalb eines Ordners (bevorzugt Dateien ohne "(1)"-Nummerierung)
- **Primary/Secondary Mode** — Vergleicht zwei Ordner; PRIMARY ist schreibgeschützt, SECONDARY wird bereinigt

**Features:** Live-Log, Pause/Abort, Statistik, Unterordner-Scan, sichere Operationen

---

### 2. Folder_Merge
**Pfad:** `Folder_Merge/file_merge.py`  
**Start:** `Folder_Merge/start.command`  
**Typ:** Python/Tkinter GUI-Anwendung

**Funktion:** Führt mehrere Quellordner in einen Zielordner zusammen.

**Features:**
- Mehrere Quellen → 1 Ziel (Dateien werden *verschoben*, nicht kopiert)
- Ordner-Matching mit einstellbarer Ähnlichkeit (0–100%)
- Bitgenaue Duplikat-Erkennung → Quelldatei wird gelöscht
- Namenskollision → automatische Nummerierung (`name_1.ext`)
- Leere Ordner werden aufgeräumt
- Alle Aktionen werden in `merge_log.txt` protokolliert

---

### 3. ModulSuite Launcher
**Pfad:** `modul_suite.py`  
**Typ:** Python/Tkinter GUI-Launcher

**Funktion:** Plugin-basiertes Dashboard. Scannt ein Verzeichnis nach `module.json`-Dateien und zeigt Module als klickbare Kacheln (4-Spalten-Grid).

**Aktuelles Problem:** Sucht in `~/SWS_SUITE/Plugins/` — Pfad stimmt nicht mit tatsächlicher Struktur überein. Außerdem startet `execute_module()` Skripte synchron mit 30s-Timeout und captured Output — ungeeignet für GUI-Anwendungen, die als eigene Fenster laufen sollen.

---

## Ziel-Architektur

Der Launcher (`modul_suite.py`) soll als zentrales Dashboard fungieren. Jedes Modul (DuplicateDelete, Folder_Merge) wird als separater Prozess gestartet — es öffnet sein eigenes Fenster und läuft unabhängig.
