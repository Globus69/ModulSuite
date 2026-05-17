# SWS Suite — Projekt-Dokumentation

## Zweck
Zentrales Dashboard (`modul_suite.py`) das eigenständige GUI-Tools als separate Prozesse startet. Jedes Tool läuft im eigenen Fenster — unabhängig, nicht eingebettet.

## Verzeichnisstruktur (Ziel)
```
SWS_SUITE/
├── modul_suite.py          ← Zentraler Launcher
├── modules/
│   ├── duplicate_delete/   ← DuplicateDelete Tool
│   │   ├── module.json
│   │   ├── duplicate_remover.py
│   │   └── start.command
│   └── folder_merge/       ← Folder Merge Tool
│       ├── module.json
│       ├── file_merge.py
│       └── start.command
└── docs/
    ├── PROJEKTE_ÜBERSICHT.md   ← Beschreibung aller Tools
    ├── KONZEPT.md              ← Architektur & UX-Konzept
    ├── TODO.md                 ← Nummerierte Aufgabenliste
    ├── UMSETZUNG.md            ← Technische Details
    └── PROTOKOLL.md            ← Änderungsprotokoll
```

## Enthaltene Module

| Modul | Beschreibung | Status |
|-------|-------------|--------|
| DuplicateDelete | SHA-256 Duplikat-Erkennung, Single & Primary/Secondary Modus | v2.0.1, fertig |
| Folder_Merge | Ordner zusammenführen, Duplikate bereinigen, leere Ordner aufräumen | fertig |

## Planungs-Dokumente
- `PROJEKTE_ÜBERSICHT.md` — Was macht jedes Tool im Detail
- `KONZEPT.md` — Architektur-Entscheidungen und UX-Konzept
- `TODO.md` — Nummerierte To-Do-Liste (Phasen 1–5)
- `UMSETZUNG.md` — Technische Implementierungsdetails
- `PROTOKOLL.md` — Chronologisches Änderungsprotokoll

## Kernprinzipien
- Module sind **eigenständige** Anwendungen, nicht integriert
- Launcher startet sie via `subprocess.Popen` (fire-and-forget, kein Timeout)
- Neue Module einfach hinzufügen: Ordner + `module.json` → automatisch im Dashboard
- `launch_mode: "gui"` in module.json → separates Fenster
- `launch_mode: "cli"` → Output im Dashboard-Log

## Offene Aufgaben
Siehe `TODO.md` — aktuell bei Phase 1 (Punkte 1–5 erledigt), Phase 2 steht an.
