# SWS Suite

Zentrales Dashboard zum Starten eigenständiger GUI-Tools. Modernes Dark-Theme, plugin-basiert, offline.

## Start

```bash
# Doppelklick im Finder:
start.command

# Oder im Terminal:
python3 modul_suite.py
```

## Enthaltene Module

| Modul | Beschreibung |
|-------|-------------|
| 🗂️ Duplicate Delete v2.0.1 | Findet & entfernt identische Dateien (SHA-256), Single- & Primary/Secondary-Modus |
| 📁 Folder Merge v1.0 | Führt mehrere Ordner zusammen, bereinigt Duplikate, räumt leere Ordner auf |

## Verzeichnisstruktur

```
SWS_SUITE/
├── modul_suite.py          ← Launcher (Dashboard)
├── start.command           ← Doppelklick-Start
├── modules/
│   ├── duplicate_delete/   ← Duplicate Delete Tool
│   │   ├── module.json
│   │   └── duplicate_remover.py
│   └── folder_merge/       ← Folder Merge Tool
│       ├── module.json
│       └── file_merge.py
└── docs/                   ← Konzept, TODO, Protokoll
```

## Neues Modul hinzufügen

1. Ordner unter `modules/mein_tool/` anlegen
2. `module.json` erstellen:
```json
{
  "name": "Mein Tool",
  "description": "Kurze Beschreibung",
  "icon": "🔧",
  "version": "1.0",
  "script": "main.py",
  "launch_mode": "gui"
}
```
3. Skript hinzufügen
4. Im Dashboard auf 🔄 klicken → Kachel erscheint automatisch

## Voraussetzungen

- Python 3.7+
- macOS (Tkinter vorinstalliert)
