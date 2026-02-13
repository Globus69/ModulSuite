#!/usr/bin/env python3
"""
ModulSuite - Lokale Plugin-basierte Desktop-Anwendung
Scannt ~/ModulSuite/Plugins/ nach JSON-definierten Modulen
"""

import os
import json
import subprocess
import tkinter as tk
from tkinter import ttk, scrolledtext
from pathlib import Path
from typing import List, Dict

class Module:
    """Repräsentiert ein einzelnes Modul"""
    def __init__(self, path: Path, config: Dict):
        self.path = path
        self.name = config.get("name", "Unnamed")
        self.description = config.get("description", "")
        self.icon = config.get("icon", "📦")
        self.script = config.get("script", "")
        self.script_path = path / self.script if self.script else None

    def execute(self) -> tuple:
        """Führt das Modul-Skript aus"""
        if not self.script_path or not self.script_path.exists():
            return False, f"Skript nicht gefunden: {self.script_path}"

        try:
            # Macht das Skript ausführbar
            os.chmod(self.script_path, 0o755)

            # Führt das Skript aus
            result = subprocess.run(
                [str(self.script_path)],
                cwd=self.path,
                capture_output=True,
                text=True,
                timeout=30
            )

            output = result.stdout if result.stdout else result.stderr
            return result.returncode == 0, output

        except subprocess.TimeoutExpired:
            return False, "Timeout: Skript hat zu lange gedauert (>30s)"
        except Exception as e:
            return False, f"Fehler: {str(e)}"


class ModulSuite:
    """Hauptanwendung"""

    def __init__(self):
        self.plugins_dir = Path.home() / "ModulSuite" / "Plugins"
        self.modules: List[Module] = []

        # GUI Setup
        self.root = tk.Tk()
        self.root.title("ModulSuite")
        self.root.geometry("800x600")

        self.setup_ui()
        self.load_modules()

    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""

        # Header
        header = tk.Frame(self.root, bg="#2c3e50", height=60)
        header.pack(fill=tk.X)

        title = tk.Label(
            header,
            text="📦 ModulSuite",
            font=("Arial", 20, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title.pack(pady=10)

        # Info Label
        info = tk.Label(
            self.root,
            text=f"Plugin-Verzeichnis: {self.plugins_dir}",
            font=("Arial", 10),
            fg="gray"
        )
        info.pack(pady=5)

        # Reload Button
        reload_btn = tk.Button(
            self.root,
            text="🔄 Module neu laden",
            command=self.reload_modules,
            font=("Arial", 11)
        )
        reload_btn.pack(pady=5)

        # Scrollbarer Module-Bereich
        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)

        self.modules_frame = tk.Frame(canvas)
        self.modules_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.modules_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Output Bereich
        output_label = tk.Label(self.root, text="📄 Ausgabe:", font=("Arial", 12, "bold"))
        output_label.pack(anchor="w", padx=10)

        self.output_text = scrolledtext.ScrolledText(
            self.root,
            height=10,
            font=("Courier", 10),
            bg="#1e1e1e",
            fg="#00ff00"
        )
        self.output_text.pack(fill=tk.BOTH, padx=10, pady=5, expand=False)

    def load_modules(self):
        """Scannt das Plugin-Verzeichnis und lädt alle Module"""
        self.modules.clear()

        # Erstellt Plugin-Verzeichnis falls nicht vorhanden
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        # Scannt nach Modulen
        for item in self.plugins_dir.iterdir():
            if item.is_dir():
                module_json = item / "module.json"
                if module_json.exists():
                    try:
                        with open(module_json, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        module = Module(item, config)
                        self.modules.append(module)
                    except Exception as e:
                        print(f"Fehler beim Laden von {item.name}: {e}")

        self.render_modules()

        if not self.modules:
            self.log("⚠️  Keine Module gefunden. Erstelle Beispiel-Module...")
            self.log(f"💡 Lege Module in: {self.plugins_dir}")

    def render_modules(self):
        """Rendert alle Module als Buttons"""
        # Löscht alte Buttons
        for widget in self.modules_frame.winfo_children():
            widget.destroy()

        if not self.modules:
            no_modules = tk.Label(
                self.modules_frame,
                text="Keine Module gefunden\n\nLege Module im Plugins-Ordner ab.",
                font=("Arial", 12),
                fg="gray",
                pady=50
            )
            no_modules.pack()
            return

        # Erstellt Button-Grid (3 Spalten)
        for idx, module in enumerate(self.modules):
            row = idx // 3
            col = idx % 3

            btn_frame = tk.Frame(
                self.modules_frame,
                bg="white",
                relief=tk.RAISED,
                borderwidth=2
            )
            btn_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # Module Button
            btn = tk.Button(
                btn_frame,
                text=f"{module.icon}\n{module.name}",
                font=("Arial", 14),
                width=15,
                height=5,
                command=lambda m=module: self.execute_module(m),
                bg="#3498db",
                fg="white",
                relief=tk.FLAT,
                cursor="hand2"
            )
            btn.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

            # Beschreibung
            if module.description:
                desc = tk.Label(
                    btn_frame,
                    text=module.description,
                    font=("Arial", 9),
                    fg="gray",
                    wraplength=150
                )
                desc.pack(pady=5)

        # Grid-Konfiguration
        for i in range(3):
            self.modules_frame.columnconfigure(i, weight=1)

    def execute_module(self, module: Module):
        """Führt ein Modul aus"""
        self.log(f"\n{'='*60}")
        self.log(f"▶️  Führe aus: {module.name}")
        self.log(f"{'='*60}")

        success, output = module.execute()

        if success:
            self.log(f"✅ Erfolgreich ausgeführt:\n{output}")
        else:
            self.log(f"❌ Fehler:\n{output}")

    def reload_modules(self):
        """Lädt alle Module neu"""
        self.log("\n🔄 Lade Module neu...")
        self.load_modules()
        self.log(f"✅ {len(self.modules)} Module geladen")

    def log(self, message: str):
        """Schreibt in den Output-Bereich"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)

    def run(self):
        """Startet die Anwendung"""
        self.root.mainloop()


if __name__ == "__main__":
    app = ModulSuite()
    app.run()
