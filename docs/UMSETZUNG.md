# SWS Suite — Umsetzung (Technische Details)

*Wird während der Implementierung befüllt.*

## Entscheidungen

### launch_mode in module.json
`"gui"` → `subprocess.Popen(["python3", script])` — öffnet eigenes Fenster, Launcher bleibt responsiv  
`"cli"` → `subprocess.run(...)` mit Output-Capture im Log-Bereich (bisheriges Verhalten)

### Pfad-Strategie
Relativ zur `modul_suite.py` Datei: `Path(__file__).parent / "modules"`  
Vorteil: Suite kann überall liegen, keine Abhängigkeit vom Home-Verzeichnis.

### Keine Integration der Tools
DuplicateDelete und Folder_Merge bleiben eigenständige Anwendungen. Der Launcher startet sie nur — er zeigt nicht ihre UI innerhalb des Dashboards. Das vereinfacht Wartung und ermöglicht Tools unabhängig zu aktualisieren.

## Änderungen an modul_suite.py

| Was | Vorher | Nachher |
|-----|--------|---------|
| Plugin-Pfad | `~/SWS_SUITE/Plugins/` | `./modules/` (relativ) |
| GUI-Start | `subprocess.run(..., timeout=30)` | `subprocess.Popen(...)` |
| launch_mode | nicht vorhanden | aus `module.json` gelesen |

## module.json Schema

```json
{
  "name": "string",
  "description": "string",
  "icon": "emoji",
  "version": "string",
  "script": "dateiname.py",
  "launch_mode": "gui" | "cli"
}
```
