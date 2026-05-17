# SWS Suite — To-Do Liste

## Phase 1: Struktur & Dokumentation
- [x] 1. Alle Projekte analysieren und verstehen
- [x] 2. `PROJEKTE_ÜBERSICHT.md` erstellen (was macht jedes Tool)
- [x] 3. `KONZEPT.md` erstellen (Architektur & UX-Plan)
- [x] 4. `TODO.md` erstellen (diese Datei)
- [x] 5. `CLAUDE.md` aktualisieren (Projektstruktur dokumentieren)

## Phase 2: Verzeichnis-Reorganisation
- [x] 6. Neues Verzeichnis `modules/` anlegen
- [x] 7. `DuplicateDelete/` → `modules/duplicate_delete/` kopiert
- [x] 8. `Folder_Merge/` → `modules/folder_merge/` kopiert
- [x] 9. `module.json` für DuplicateDelete erstellt
- [x] 10. `module.json` für Folder_Merge erstellt

## Phase 3: Launcher-Verbesserungen
- [x] 11. Pfad in `modul_suite.py` auf `./modules/` korrigiert
- [x] 12. `launch_mode`-Unterstützung eingebaut (`"gui"` vs `"cli"`)
- [x] 13. GUI-Module mit `subprocess.Popen` gestartet (fire-and-forget)
- [x] 14. Modul-Kachel zeigt Version aus `module.json`
- [x] 15. `start.command` für den Launcher erstellt

## Phase 4: Test & Feinschliff
- [ ] 16. Launcher starten und beide Module aus Dashboard öffnen
- [ ] 17. Sicherstellen dass Dashboard während Modul läuft reagiert (nicht blockiert)
- [ ] 18. `PROTOKOLL.md` mit Ergebnissen befüllen
- [ ] 19. README.md im Root aktualisiert ✅ (bereits erledigt)

## Phase 5 (Optional/Später)
- [ ] 20. Prozess-Status-Anzeige in Kacheln (grüner Punkt wenn Tool läuft)
- [ ] 21. Modul-Detailansicht (Klick auf Info-Icon zeigt README)
- [ ] 22. Suchfeld/Filter im Dashboard
- [ ] 23. Originale `DuplicateDelete/` und `Folder_Merge/` Ordner aufräumen (nach Verifikation)
