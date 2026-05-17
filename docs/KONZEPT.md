# SWS Suite — Konzept

## Ziel

Ein zentrales Dashboard (`modul_suite.py`) startet eigenständige GUI-Tools als separate Prozesse. Jedes Tool läuft in seinem eigenen Fenster — unabhängig, nicht eingebettet.

---

## Architektur

```
SWS_SUITE/
├── modul_suite.py          ← Zentraler Launcher (Dashboard)
├── modules/
│   ├── duplicate_delete/
│   │   ├── module.json     ← Modul-Descriptor
│   │   ├── duplicate_remover.py
│   │   └── start.command
│   └── folder_merge/
│       ├── module.json
│       ├── file_merge.py
│       └── start.command
└── docs/
    ├── KONZEPT.md
    ├── TODO.md
    ├── UMSETZUNG.md
    └── PROTOKOLL.md
```

---

## Modul-Descriptor (module.json)

```json
{
  "name": "Duplicate Delete",
  "description": "Findet und entfernt identische Dateien (SHA-256)",
  "icon": "🗂️",
  "version": "2.0.1",
  "script": "duplicate_remover.py",
  "launch_mode": "gui"
}
```

`launch_mode: "gui"` → Modul wird als separater Prozess gestartet (`subprocess.Popen`), kein Output-Capture, kein Timeout.

---

## Launcher-Änderungen

### Problem heute
`module.execute()` ruft Skripte mit `subprocess.run(..., timeout=30, capture_output=True)` auf — blockiert den Launcher und kann kein GUI-Fenster öffnen.

### Lösung
```python
# Für GUI-Module: Popen (fire-and-forget)
subprocess.Popen(["python3", str(self.script_path)], cwd=self.path)

# Für CLI-Module: run mit Output-Capture (bisheriges Verhalten)
subprocess.run([str(self.script_path)], ...)
```

Das `launch_mode`-Feld in `module.json` steuert, welcher Pfad genommen wird.

### Pfad-Fix
Aktuell: `Path.home() / "SWS_SUITE" / "Plugins"`  
Neu: `Path(__file__).parent / "modules"` (relativ zur Suite)

---

## UX-Konzept

- **Dashboard:** 4-Spalten-Grid mit Icon-Kacheln (bestehend, gut)
- **Kachel zeigt:** Icon, Name, Kurzbeschreibung, Version
- **Klick:** Öffnet Tool-Fenster separat, Dashboard bleibt offen
- **Status-Indikator:** Kachel zeigt "läuft" wenn Prozess aktiv ist (optional, Phase 2)
- **Farben/Design:** Bestehendes Dark-Theme beibehalten

---

## Erweiterbarkeit

Neue Tools einfach hinzufügen:
1. Ordner unter `modules/` anlegen
2. `module.json` erstellen
3. Skript hinzufügen
4. Dashboard neu laden → Kachel erscheint automatisch
