# SWS Suite — Protokoll

## 2026-05-17 — Analyse & Planung

### Analysiert
- `DuplicateDelete/duplicate_remover.py` — Tkinter GUI, SHA-256 Duplikat-Tool, v2.0.1
- `Folder_Merge/file_merge.py` — Tkinter GUI, Ordner-Merge-Tool
- `modul_suite.py` — Tkinter Plugin-Launcher mit 4-Spalten-Grid

### Festgestellt
- Launcher sucht in `~/SWS_SUITE/Plugins/` → Pfad existiert nicht, Module werden nicht gefunden
- `execute_module()` nutzt `subprocess.run(..., timeout=30)` → blockiert bei GUI-Apps
- Keine `module.json` Dateien für die beiden Tools vorhanden
- Verzeichnisnamen inkonsistent (`DuplicateDelete` vs `Folder_Merge`)

### Erstellt
- `PROJEKTE_ÜBERSICHT.md` — Beschreibung aller Projekte
- `KONZEPT.md` — Architektur- und UX-Konzept
- `TODO.md` — nummerierte To-Do-Liste (23 Punkte, 5 Phasen)
- `UMSETZUNG.md` — Technische Entscheidungen
- `PROTOKOLL.md` — dieses Dokument

### Nächster Schritt
Phase 2 starten (TODO 6–10): Verzeichnis-Reorganisation und module.json erstellen.
