# 📦 ModulSuite

Eine lokale, plugin-basierte Desktop-Anwendung für macOS, die Module über JSON-Definitionen lädt und ausführt.

## 🚀 Features

- ✅ **Offline-First**: Keine Cloud, kein Netzwerk
- ✅ **Plugin-System**: Einfaches Hinzufügen neuer Module
- ✅ **JSON-basiert**: Konfiguration über JSON-Dateien
- ✅ **Skript-Ausführung**: Shell-Skripte, Python, etc.
- ✅ **Auto-Loading**: Automatisches Scannen beim Start

## 📋 Voraussetzungen

- Python 3.7+
- macOS (läuft auch auf Linux/Windows mit kleineren Anpassungen)
- Tkinter (normalerweise vorinstalliert)

## 🛠️ Installation

1. **Repository klonen:**
   ```bash
   git clone <repo-url>
   cd ModulSuite
   ```

2. **Starten:**
   ```bash
   python3 modul_suite.py
   ```

   Oder ausführbar machen:
   ```bash
   chmod +x modul_suite.py
   ./modul_suite.py
   ```

## 📂 Struktur

```
~/ModulSuite/
└── Plugins/
    ├── hello_world/
    │   ├── module.json
    │   └── script.sh
    ├── system_info/
    │   ├── module.json
    │   └── script.sh
    └── ...
```

## 🔌 Neues Modul erstellen

1. **Ordner erstellen:**
   ```bash
   mkdir -p ~/ModulSuite/Plugins/mein_modul
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
   touch ~/ModulSuite/Plugins/mein_modul/script.sh
   chmod +x ~/ModulSuite/Plugins/mein_modul/script.sh
   ```

4. **Skript bearbeiten:**
   ```bash
   #!/bin/bash
   echo "Hallo von meinem Modul!"
   ```

5. **Module neu laden** in der App oder App neu starten

## 🎨 JSON-Schema

```json
{
  "name": "String (Pflicht)",
  "description": "String (Optional)",
  "icon": "String/Emoji (Optional, Standard: 📦)",
  "script": "String (Pflicht - relativer Pfad)"
}
```

## 🧪 Verfügbare Module

Die App kommt mit fünf Beispiel-Modulen:

### Einfache Tools:
1. **Hello World** 👋 - Einfaches Test-Modul
2. **System Info** 💻 - Zeigt Systeminformationen
3. **File Counter** 📁 - Zählt Dateien im Home-Verzeichnis

### Professionelle Tools:
4. **Duplicate Remover** 🗂️ - Findet und entfernt Duplikat-Dateien mit SHA-256 Hashing
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

### Mit Parametern arbeiten

Module können Umgebungsvariablen nutzen:

```bash
#!/bin/bash
echo "Working Directory: $PWD"
echo "Module Name: $0"
```

## 🎯 Roadmap / Erweiterungsideen

- [ ] Parameter-Dialog für Module
- [ ] Modul-Kategorien/Tags
- [ ] Suche/Filter
- [ ] Favoriten
- [ ] Ausführungshistorie
- [ ] Dark Mode
- [ ] Modul-Templates

## 📝 Lizenz

MIT

## 🤝 Beitragen

Einfach neue Module im Plugins-Ordner erstellen und teilen!
