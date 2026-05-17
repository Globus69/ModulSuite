# Folder Merge — Redesign-Analyse & Planungsphase

---

## 1. Ist-Analyse: Was ist das Problem?

### Aktuelle Struktur (eine App, 7 Sektionen vertikal)
```
┌─────────────────────────────┐
│ Header                      │
├─────────────────────────────┤
│ 1. Zielordner               │
│ 2. Quellordner (Liste)      │
│ 3. Ordner-Ähnlichkeit       │  ← Merge-Einstellungen
│ 4. Zusammenführen starten   │  ← Merge-Aktion
│ 5. Dateinamen-Toleranz      │  ← Dedup-Einstellungen
│ 6. Duplikate bereinigen     │  ← Dedup-Aktion
│ 7. Leere Ordner löschen     │  ← 3. unabhängige Funktion
│ 8. Log                      │  ← geteilt von allen
└─────────────────────────────┘
```

### UX-Probleme
- **Kognitive Überlastung:** 3 völlig verschiedene Workflows in einem Scroll-Fenster
- **Kontextsprünge:** Zielordner oben, Aktionen unten — Bezug unklar
- **Log ist geteilt:** Welche Aktion hat was geloggt? Schwer zu trennen
- **Scrollpflicht:** Benutzer muss scrollen um Kontext + Aktion gleichzeitig zu sehen
- **Kein visueller Fokus:** Alle Sektionen gleichwertig, keine klare Hauptaktion

### Drei thematisch unabhängige Workflows
| Workflow | Eingabe | Aktion | Unabhängig? |
|---------|---------|--------|------------|
| **Merge** | Ziel + Quellen + Ähnlichkeit | Verschieben, Ordner zusammenführen | Ja |
| **Dedup** | Zielordner + Toleranz | Nummerierte Duplikate löschen | Ja — braucht nur 1 Ordner |
| **Empty** | Beliebiger Ordner | Leere Ordner löschen | Ja — völlig eigenständig |

---

## 2. Lösungs-Optionen (Bewertung)

### Option A: 3 komplett separate Apps (3× module.json)
```
Dashboard → [Folder Merge] [Dedup Cleaner] [Empty Folder Remover]
```
**Pro:** Maximal fokussiert, jede App hat klaren Zweck  
**Con:** Keine gemeinsame Logik, Code-Duplizierung; für verwandte Tools übertrieben  
**Bewertung: ★★★☆☆**

---

### Option B: Tab-Navigation (eine App, 3 Tabs)
```
┌──────────────────────────────────┐
│ [Merge] [Dedup] [Empty Folders]  │  ← Tabs
├──────────────────────────────────┤
│                                  │
│    Aktiver Tab-Inhalt            │
│                                  │
└──────────────────────────────────┘
```
**Pro:** Eine App, klare Trennung, bewährtes UX-Pattern  
**Con:** Nur ein Workflow sichtbar, kein Überblick  
**Bewertung: ★★★★☆**

---

### Option C: 3-Spalten-Layout (eine App, nebeneinander) ← EMPFEHLUNG
```
┌──────────────┬──────────────┬──────────────┐
│  MERGE       │  DEDUP       │  EMPTY       │
│              │              │              │
│ Ziel:  [___] │ Ordner: [__] │ Ordner: [__] │
│ + Quellen    │ Toleranz     │              │
│   [Liste]    │ [Slider]     │              │
│              │              │              │
│ [▶ Starten]  │ [🔍 Starten] │ [🗑 Starten] │
│              │              │              │
│ ▓▓▓▓░░ 60%  │ ▓▓░░░░ 33%  │ Bereit       │
├──────────────┴──────────────┴──────────────┤
│  LOG (gemeinsam, farblich getrennt)         │
└─────────────────────────────────────────────┘
```
**Pro:** Alle Workflows auf einen Blick, kein Scrollen, direkte Vergleichbarkeit  
**Con:** Fenster muss breit sein (min. 1100px), auf kleinen Bildschirmen eng  
**Bewertung: ★★★★★**

---

### Option D: Hub + 3 Sub-Fenster (Launcher-Prinzip)
```
┌─────────────────────────────────┐
│ Folder Suite                    │
│ ┌────────┐ ┌────────┐ ┌──────┐ │
│ │ MERGE  │ │ DEDUP  │ │EMPTY │ │
│ │ ▶      │ │ 🔍     │ │ 🗑   │ │
│ └────────┘ └────────┘ └──────┘ │
└─────────────────────────────────┘
         ↓ Klick öffnet jeweiliges Fenster
```
**Pro:** Kleine Hauptapp, Fokus-Fenster bei Bedarf  
**Con:** Mehr Klicks, Kontext verteilt auf Fenster, Orchestrierung aufwändig  
**Bewertung: ★★★☆☆**

---

## 3. Empfehlung: Option C (3-Spalten) + Log unten

### Begründung
- Alle 3 Workflows **gleichzeitig sichtbar** — der Nutzer kann z.B. erst Merge, dann Dedup, dann Empty in einem Sitzung erledigen ohne Kontextwechsel
- **Visueller Spalten-Fokus** — jede Spalte ist ein abgeschlossener Workflow mit eigener Statuszeile und eigenem Fortschrittsbalken
- **Gemeinsamer Log** unten mit Farb-Tags je Workflow (Blau=Merge, Orange=Dedup, Grün=Empty)
- Passt zum **Dark-Theme** des Dashboards

---

## 4. Geplante neue Struktur

### Dateien (eine App, neues Design)
```
modules/folder_merge/
├── file_merge.py          ← Komplette Neuentwicklung (3-Spalten)
│   ├── class MergeEngine  ← reine Logik (kein UI)
│   ├── class DedupEngine  ← reine Logik
│   ├── class EmptyEngine  ← reine Logik
│   └── class FolderSuiteApp ← UI-Orchestrierung
├── module.json
└── start.command
```

### Fenster-Layout (1200×750 min.)
```
┌─────────────────────────────────────────────────────────────────────┐
│ 📁  Folder Suite        Merge · Dedup · Empty Folders               │
├──────────────────┬───────────────────┬──────────────────────────────┤
│  📦 MERGE        │  🔍 DEDUP          │  🗑 LEERE ORDNER             │
│──────────────────│───────────────────│──────────────────────────────│
│ Zielordner:      │ Zielordner:        │ Ordner:                      │
│ [__________] [+] │ [__________] [+]  │ [__________] [+]             │
│                  │                   │                               │
│ Quellordner:     │ Toleranz:         │                               │
│ [Liste     ]     │ [Slider 100%]     │                               │
│ [+] [-]          │                   │                               │
│                  │                   │                               │
│ Ordner-Ähnl.:    │                   │                               │
│ [Slider 100%]    │                   │                               │
│                  │                   │                               │
│ [▶ Merge ]       │ [🔍 Bereinigen]   │ [🗑 Löschen]                 │
│ ████░░░ 60%      │ ████████░ 80%     │ Bereit                        │
├──────────────────┴───────────────────┴──────────────────────────────┤
│ LOG  [🔵 Merge] [🟠 Dedup] [🟢 Empty]   Alle  ✕ Leeren             │
│ [10:23:01] 📦 verschoben → Projekte/2024/code.py                    │
│ [10:23:02] 🔍 Duplikat gelöscht → backup_1.dat                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Implementierungs-Schritte (To-Do)

### Phase A: Architektur (Logik von UI trennen)
- [ ] A1. `MergeEngine`-Klasse extrahieren (reine Logik, kein tkinter)
- [ ] A2. `DedupEngine`-Klasse extrahieren
- [ ] A3. `EmptyEngine`-Klasse extrahieren
- [ ] A4. Alle Engines teilen `files_identical()` und `name_similarity()`

### Phase B: UI — 3-Spalten-Layout
- [ ] B1. Haupt-Frame in 3 gleiche Spalten aufteilen (`grid`, weight=1)
- [ ] B2. Spalte 1 — Merge-Panel (Ziel, Quellen, Slider, Start, Progress)
- [ ] B3. Spalte 2 — Dedup-Panel (Ordner, Slider, Start, Progress)
- [ ] B4. Spalte 3 — Empty-Panel (Ordner, Start, Progress)
- [ ] B5. Spalten-Trennlinien (1px, dunkel)

### Phase C: Gemeinsamer Log
- [ ] C1. Log-Bereich unten mit Filter-Tabs (Alle / Merge / Dedup / Empty)
- [ ] C2. Jede Engine loggt mit eigenem Farb-Tag
- [ ] C3. Löschen-Button nur für aktiven Filter

### Phase D: Test
- [ ] D1. Alle 3 Workflows einzeln testen
- [ ] D2. Parallelbetrieb prüfen (z.B. Dedup während Merge läuft)
- [ ] D3. Fenster-Resize-Verhalten testen

---

## 6. Entscheidungen

| Frage | Entscheidung | Grund |
|-------|-------------|-------|
| Parallelbetrieb? | Jeder Workflow hat eigenes `is_running`-Flag | Unabhängige Threads möglich |
| Zielordner teilen? | Nein — jede Spalte hat eigenes Ordner-Feld | Klarheit, kein versteckter Zustand |
| Log teilen? | Ja — ein Log mit Filter | Überblick ohne zu viel Fenster |
| Mindest-Breite | 1100px | 3 Spalten à ~340px + Padding |
