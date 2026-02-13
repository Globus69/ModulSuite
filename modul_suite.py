#!/usr/bin/env python3
"""
SWS Suite - Lokale Plugin-basierte Desktop-Anwendung
Scannt ~/SWS_SUITE/Plugins/ nach JSON-definierten Modulen
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


class ModernButton(tk.Canvas):
    """Moderner Button mit Hover-Effekt"""
    def __init__(self, parent, text, icon, description, command, **kwargs):
        super().__init__(parent, **kwargs)

        self.command = command
        self.text = text
        self.icon = icon
        self.description = description

        # Farben
        self.bg_normal = "#2D3E50"
        self.bg_hover = "#34495E"
        self.fg_color = "#ECF0F1"
        self.accent_color = "#3498DB"

        self.configure(
            bg=self.bg_normal,
            highlightthickness=0,
            relief="flat"
        )

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        """Zeichnet Button neu bei Größenänderung"""
        self.delete("all")
        w, h = event.width, event.height

        # Icon
        self.create_text(
            w/2, h/3,
            text=self.icon,
            font=("Arial", 40),
            fill=self.fg_color,
            tags="content"
        )

        # Name
        self.create_text(
            w/2, h/2 + 10,
            text=self.text,
            font=("Arial", 14, "bold"),
            fill=self.fg_color,
            tags="content"
        )

        # Beschreibung
        if self.description:
            self.create_text(
                w/2, h - 25,
                text=self.description[:40] + "..." if len(self.description) > 40 else self.description,
                font=("Arial", 9),
                fill="#BDC3C7",
                tags="content",
                width=w-20
            )

    def _on_enter(self, event):
        self.configure(bg=self.bg_hover)
        self.configure(cursor="hand2")

    def _on_leave(self, event):
        self.configure(bg=self.bg_normal)

    def _on_click(self, event):
        if self.command:
            self.command()


class ModulSuite:
    """Hauptanwendung"""

    def __init__(self):
        self.plugins_dir = Path.home() / "SWS_SUITE" / "Plugins"
        self.modules: List[Module] = []

        # GUI Setup
        self.root = tk.Tk()
        self.root.title("SWS Suite")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # Farben
        self.bg_main = "#1A1A2E"
        self.bg_secondary = "#16213E"
        self.accent = "#0F3460"
        self.text_color = "#E94560"

        self.root.configure(bg=self.bg_main)

        self.setup_ui()
        self.load_modules()

    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""

        # Header
        header = tk.Frame(self.root, bg=self.accent, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title = tk.Label(
            header,
            text="⚡ SWS SUITE",
            font=("Arial", 28, "bold"),
            bg=self.accent,
            fg="#ECF0F1"
        )
        title.pack(side=tk.LEFT, padx=30, pady=20)

        # Info & Reload Container
        info_frame = tk.Frame(header, bg=self.accent)
        info_frame.pack(side=tk.RIGHT, padx=30)

        info = tk.Label(
            info_frame,
            text=f"📂 {self.plugins_dir}",
            font=("Arial", 10),
            bg=self.accent,
            fg="#BDC3C7"
        )
        info.pack(anchor="e")

        reload_btn = tk.Button(
            info_frame,
            text="🔄 Neu laden",
            command=self.reload_modules,
            font=("Arial", 11, "bold"),
            bg="#2C3E50",
            fg="#ECF0F1",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            borderwidth=0
        )
        reload_btn.pack(pady=(5, 0))

        # Main Content Area mit Scrollbar
        content_frame = tk.Frame(self.root, bg=self.bg_main)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Canvas für scrollbare Module
        canvas = tk.Canvas(
            content_frame,
            bg=self.bg_main,
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)

        self.modules_frame = tk.Frame(canvas, bg=self.bg_main)
        self.modules_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.modules_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Output Bereich
        output_frame = tk.Frame(self.root, bg=self.bg_secondary)
        output_frame.pack(fill=tk.BOTH, padx=20, pady=(0, 20))

        output_header = tk.Frame(output_frame, bg=self.bg_secondary)
        output_header.pack(fill=tk.X, pady=(10, 5))

        output_label = tk.Label(
            output_header,
            text="📄 Ausgabe",
            font=("Arial", 12, "bold"),
            bg=self.bg_secondary,
            fg="#ECF0F1"
        )
        output_label.pack(side=tk.LEFT, padx=10)

        clear_btn = tk.Button(
            output_header,
            text="🗑️ Löschen",
            command=lambda: self.output_text.delete(1.0, tk.END),
            font=("Arial", 9),
            bg="#E74C3C",
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=3,
            cursor="hand2"
        )
        clear_btn.pack(side=tk.RIGHT, padx=10)

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            height=8,
            font=("Menlo", 10),
            bg="#0D1117",
            fg="#58A6FF",
            insertbackground="#58A6FF",
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.output_text.pack(fill=tk.BOTH, padx=10, pady=(0, 10))

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
            self.log("⚠️  Keine Module gefunden.")
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
                font=("Arial", 14),
                fg="#7F8C8D",
                bg=self.bg_main,
                pady=100
            )
            no_modules.pack()
            return

        # Festes 4-Spalten Grid
        cols = 4

        # Erstellt Button-Grid
        for idx, module in enumerate(self.modules):
            row = idx // cols
            col = idx % cols

            btn = ModernButton(
                self.modules_frame,
                text=module.name,
                icon=module.icon,
                description=module.description,
                command=lambda m=module: self.execute_module(m),
                width=260,
                height=180
            )
            btn.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        # Grid-Konfiguration
        for i in range(cols):
            self.modules_frame.columnconfigure(i, weight=1)

        for i in range((len(self.modules) + cols - 1) // cols):
            self.modules_frame.rowconfigure(i, weight=0)

    def execute_module(self, module: Module):
        """Führt ein Modul aus"""
        self.log(f"\n{'='*60}")
        self.log(f"▶️  {module.name}")
        self.log(f"{'='*60}")

        success, output = module.execute()

        if success:
            self.log(f"✅ Erfolgreich:\n{output}")
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
