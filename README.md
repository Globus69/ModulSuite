# ⚡ SWS Suite

Eine lokale, plugin-basierte Desktop-Anwendung für macOS mit modernem Dark-Theme Design, die Module über JSON-Definitionen lädt und ausführt.

## 🚀 Features

- ✅ **Modernes UI**: Dark-Theme mit Hover-Effekten und responsivem Layout
- ✅ **Offline-First**: Keine Cloud, kein Netzwerk
- ✅ **Plugin-System**: Einfaches Hinzufügen neuer Module
- ✅ **JSON-basiert**: Konfiguration über JSON-Dateien
- ✅ **Skript-Ausführung**: Shell-Skripte, Python, etc.
- ✅ **Auto-Loading**: Automatisches Scannen beim Start
- ✅ **Responsive**: Buttons passen sich der Fenstergröße an

## 📋 Voraussetzungen

- Python 3.7+
- macOS (läuft auch auf Linux/Windows mit kleineren Anpassungen)
- Tkinter (normalerweise vorinstalliert)

## 🛠️ Installation & Start

### Einfachster Weg (Doppelklick):
```
Doppelklick auf: /Users/SWS/DEVELOP/SWS_Suite.command
```

### Oder via Terminal:
```bash
cd /Users/SWS/DEVELOP/SWS_SUITE
python3 modul_suite.py
```

## 📂 Struktur

```
/Users/SWS/DEVELOP/
├── SWS_Suite.command          ← Start-Datei (Doppelklick)
└── SWS_SUITE/                 ← Hauptprojekt
    ├── modul_suite.py         ← Hauptanwendung
    ├── ExamplePlugins/        ← Beispiel-Module im Repo
    ├── _Archive/              ← Original-Projekte
    └── README.md

~/SWS_SUITE/                   ← Plugin-Installation
└── Plugins/
    ├── hello_world/
    ├── system_info/
    ├── file_counter/
    ├── duplicate_remover/
    └── folder_merge/
```

## 🔌 Neues Modul erstellen

1. **Ordner erstellen:**
   ```bash
   mkdir -p ~/SWS_SUITE/Plugins/mein_modul
   ```

2. **`module.json` erstellen:**
   ```json
   {
     "name": "Mein Modul",
     "description": "Beschreibung des Moduls",
     "icon": "🎯",
     "script": "script.sh"
   }
   ```

3. **Skript erstellen:**
   ```bash
   cat > ~/SWS_SUITE/Plugins/mein_modul/script.sh << 'EOF'
   #!/bin/bash
   echo "Hallo von meinem Modul!"
   EOF

   chmod +x ~/SWS_SUITE/Plugins/mein_modul/script.sh
   ```

4. **Module neu laden** mit dem 🔄 Button in der App

## 🎨 Design

- **Hauptfarbe**: Dark Blue (#1A1A2E)
- **Accent**: Deep Blue (#0F3460)
- **Buttons**: Slate (#2D3E50) mit Hover-Effekt
- **Text**: Light Gray (#ECF0F1)
- **Output**: GitHub Dark Theme (#0D1117)

## 🧪 Verfügbare Module

Die App kommt mit fünf Beispiel-Modulen:

### Einfache Tools:
1. **Hello World** 👋 - Einfaches Test-Modul
2. **System Info** 💻 - Zeigt Systeminformationen
3. **File Counter** 📁 - Zählt Dateien im Home-Verzeichnis

### Professionelle Tools:
4. **Duplicate Remover** 🗂️ - Findet und entfernt Duplikat-Dateien
   - SHA-256 Hashing für 100% Genauigkeit
   - Single Folder Mode & Primary/Secondary Mode
   - Live Activity Log & Pause/Abort-Funktion

5. **Folder Merge** 📂 - Führt mehrere Ordner zusammen
   - Bitgenaue Duplikat-Erkennung
   - Intelligentes Ordner-Matching
   - Automatisches Aufräumen leerer Ordner

## 🔧 Erweiterte Nutzung

### Python-Skripte ausführen

```json
{
  "name": "Python Modul",
  "icon": "🐍",
  "script": "script.py"
}
```

Skript:
```python
#!/usr/bin/env python3
print("Hello from Python!")
```

### GUI-Anwendungen starten

Für Module, die eigene GUIs öffnen (wie Duplicate Remover):

```bash
#!/bin/bash
python3 "$(dirname "$0")/my_gui_app.py" &
echo "✅ GUI wurde geöffnet!"
```

## 🎯 Roadmap / Erweiterungsideen

- [x] Modernes Dark-Theme Design
- [x] Responsive Button-Layout
- [x] Hover-Effekte
- [ ] Parameter-Dialog für Module
- [ ] Modul-Kategorien/Tags
- [ ] Suche/Filter
- [ ] Favoriten
- [ ] Ausführungshistorie
- [ ] Modul-Templates

## 📝 Lizenz

MIT

## 🤝 Beitragen

Einfach neue Module im Plugins-Ordner erstellen und teilen!
