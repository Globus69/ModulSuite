#!/bin/bash

# SWS Suite Launcher
# Startet die SWS Suite Desktop-Anwendung

# Wechsle ins Projektverzeichnis
cd "$(dirname "$0")/SWS_SUITE"

# Starte die Anwendung
python3 modul_suite.py
