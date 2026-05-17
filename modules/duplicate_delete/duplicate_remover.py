#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import hashlib
import os
from pathlib import Path
import threading
from collections import defaultdict
import time

# ── Farb-Palette ────────────────────────────────────────────────────────────
C = {
    "bg":        "#1A1A2E",
    "panel":     "#16213E",
    "card":      "#0F3460",
    "accent":    "#3498DB",
    "success":   "#2ECC71",
    "warning":   "#F39C12",
    "danger":    "#E74C3C",
    "text":      "#ECF0F1",
    "muted":     "#7F8C8D",
    "primary_fg":"#5DADE2",
    "secondary_fg":"#EC7063",
    "log_bg":    "#0D1117",
    "log_text":  "#58A6FF",
}

class _Btn(tk.Label):
    """macOS-sicherer Button via tk.Label — respektiert bg/fg vollständig."""
    def __init__(self, parent, text, command, bg, fg=None, **kw):
        self._cmd    = command
        self._bg     = bg
        self._fg     = fg or C["text"]
        self._active = True
        super().__init__(parent, text=text, bg=bg, fg=self._fg,
                         font=("Arial", 11, "bold"), padx=14, pady=8,
                         cursor="hand2", **kw)
        self.bind("<Button-1>", self._click)
        self.bind("<Enter>",    self._hover_on)
        self.bind("<Leave>",    self._hover_off)

    def _click(self, _):
        if self._active: self._cmd()

    def _hover_on(self, _):
        if self._active: super().configure(bg=C["accent"])

    def _hover_off(self, _):
        super().configure(bg=self._bg if self._active else C["card"])

    def configure(self, **kw):
        if "state" in kw:
            state = kw.pop("state")
            if "bg" in kw:
                self._bg = kw.pop("bg")
            if state == tk.DISABLED:
                self._active = False
                super().configure(bg=C["card"], fg=C["muted"], cursor="", **kw)
            else:
                self._active = True
                super().configure(bg=self._bg, fg=self._fg, cursor="hand2", **kw)
        else:
            if "bg" in kw:
                self._bg = kw["bg"]
            super().configure(**kw)

    config = configure


def btn(parent, text, command, color=None, width=None, **kwargs):
    kw = {"width": width} if width else {}
    kw.update(kwargs)
    return _Btn(parent, text, command, bg=color or C["card"], **kw)

styled_btn = btn


class DuplicateFileRemover:
    def __init__(self, root):
        self.root = root
        self.root.title("Duplicate Delete")
        self.root.geometry("860x680")
        self.root.minsize(700, 560)
        self.root.configure(bg=C["bg"])

        self.scanning = False
        self.paused = False
        self.abort = False
        self.pause_event = threading.Event()
        self.pause_event.set()

        self.mode = None
        self.primary_folder = None
        self.secondary_folder = None

        self.stats = self._empty_stats()
        self._build_ui()

    # ── Statistik-Template ──────────────────────────────────────────────────

    def _empty_stats(self):
        return {
            'total_files': 0, 'primary_files': 0, 'secondary_files': 0,
            'duplicate_groups': 0, 'files_deleted': 0, 'space_freed': 0,
            'files_kept': 0, 'user_decisions': 0, 'errors': 0,
        }

    # ── UI-Aufbau ───────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_mode_selector()
        self._build_folder_area()
        self._build_progress_bar()
        self._build_log()
        self._build_controls()
        self._build_statusbar()

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C["card"], height=64)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)

        tk.Label(hdr, text="🗂️  Duplicate Delete", font=("Arial", 22, "bold"),
                 bg=C["card"], fg=C["text"]).pack(side=tk.LEFT, padx=24, pady=14)
        tk.Label(hdr, text="SHA-256 · Bit-genaue Duplikat-Erkennung",
                 font=("Arial", 10), bg=C["card"], fg=C["muted"]).pack(
            side=tk.LEFT, pady=14)

    def _build_mode_selector(self):
        outer = tk.Frame(self.root, bg=C["bg"], pady=16)
        outer.pack(fill=tk.X, padx=24)

        tk.Label(outer, text="MODUS", font=("Arial", 9, "bold"),
                 bg=C["bg"], fg=C["muted"]).pack(anchor=tk.W)

        row = tk.Frame(outer, bg=C["bg"])
        row.pack(fill=tk.X, pady=(6, 0))

        self.mode_var = tk.StringVar(value="single")

        for value, label, desc in [
            ("single", "Single Folder", "Duplikate innerhalb eines Ordners finden"),
            ("dual",   "Primary / Secondary", "Secondary-Ordner anhand Primary bereinigen"),
        ]:
            card = tk.Frame(row, bg=C["panel"], padx=16, pady=12, relief=tk.FLAT, bd=0)
            card.pack(side=tk.LEFT, padx=(0, 12))

            rb = tk.Radiobutton(
                card, text=label, variable=self.mode_var, value=value,
                command=self.on_mode_change,
                bg=C["panel"], fg=C["text"],
                activebackground=C["panel"], activeforeground=C["accent"],
                selectcolor=C["accent"],
                highlightbackground=C["panel"], highlightthickness=0,
                font=("Arial", 12, "bold"), cursor="hand2",
            )
            rb.pack(anchor=tk.W)
            tk.Label(card, text=desc, bg=C["panel"], fg=C["muted"],
                     font=("Arial", 9)).pack(anchor=tk.W)

    def _build_folder_area(self):
        self.folder_area = tk.Frame(self.root, bg=C["bg"])
        self.folder_area.pack(fill=tk.X, padx=24, pady=(0, 8))

        # ── Single-Mode ─────────────────────────────────────────────────────
        self.single_frame = tk.Frame(self.folder_area, bg=C["bg"])
        self.single_select_btn = styled_btn(
            self.single_frame, "📂  Ordner wählen & scannen",
            self.select_single_folder, color=C["accent"])
        self.single_select_btn.pack(anchor=tk.W)
        self.single_frame.pack(fill=tk.X)

        # ── Dual-Mode ───────────────────────────────────────────────────────
        self.dual_frame = tk.Frame(self.folder_area, bg=C["bg"])

        for attr, color, label, btn_text, cmd in [
            ("primary",   C["primary_fg"],   "PRIMARY  (Referenz – wird NICHT verändert)",
             "📂  Primary wählen",    self.select_primary_folder),
            ("secondary", C["secondary_fg"],  "SECONDARY  (wird bereinigt)",
             "📂  Secondary wählen",  self.select_secondary_folder),
        ]:
            row = tk.Frame(self.dual_frame, bg=C["panel"], padx=14, pady=10)
            row.pack(fill=tk.X, pady=(0, 6))

            tk.Label(row, text=label, bg=C["panel"], fg=color,
                     font=("Arial", 10, "bold")).pack(anchor=tk.W)

            inner = tk.Frame(row, bg=C["panel"])
            inner.pack(fill=tk.X, pady=(4, 0))

            btn = styled_btn(inner, btn_text, cmd, color=C["card"], width=22)
            btn.pack(side=tk.LEFT)

            path_lbl = tk.Label(inner, text="—", bg=C["panel"], fg=color,
                                font=("Arial", 9), anchor=tk.W)
            path_lbl.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

            setattr(self, f"{attr}_btn", btn)
            setattr(self, f"{attr}_label", path_lbl)

        self.start_btn = styled_btn(
            self.dual_frame, "▶  Scan starten", self.start_dual_scan,
            color=C["success"])
        self.start_btn.configure(state=tk.DISABLED)
        self.start_btn.pack(anchor=tk.W, pady=(8, 0))

    def _build_progress_bar(self):
        frame = tk.Frame(self.root, bg=C["bg"])
        frame.pack(fill=tk.X, padx=24, pady=(4, 0))

        self.progress_label = tk.Label(frame, text="", bg=C["bg"],
                                        fg=C["muted"], font=("Arial", 9),
                                        anchor=tk.W)
        self.progress_label.pack(fill=tk.X)

        self.progress_canvas = tk.Canvas(frame, height=4, bg=C["panel"],
                                          highlightthickness=0)
        self.progress_canvas.pack(fill=tk.X, pady=(2, 0))
        self._progress_rect = None

    def _set_progress(self, pct):
        """Zeichnet Fortschrittsbalken (0–100)."""
        self.progress_canvas.delete("all")
        w = self.progress_canvas.winfo_width()
        if w > 0 and pct > 0:
            self.progress_canvas.create_rectangle(
                0, 0, w * pct / 100, 4, fill=C["accent"], outline="")

    def _build_log(self):
        frame = tk.Frame(self.root, bg=C["bg"])
        frame.pack(fill=tk.BOTH, expand=True, padx=24, pady=8)

        hdr = tk.Frame(frame, bg=C["bg"])
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="AKTIVITÄTS-LOG", font=("Arial", 9, "bold"),
                 bg=C["bg"], fg=C["muted"]).pack(side=tk.LEFT)
        tk.Button(hdr, text="✕ Leeren", command=self._clear_log,
                  bg=C["bg"], fg=C["muted"], relief=tk.FLAT,
                  font=("Arial", 9), cursor="hand2", bd=0).pack(side=tk.RIGHT)

        self.log_text = tk.Text(
            frame, font=("Menlo", 10), bg=C["log_bg"], fg=C["log_text"],
            insertbackground=C["log_text"], relief=tk.FLAT, padx=10, pady=8,
            state=tk.DISABLED,
        )
        sb = tk.Scrollbar(frame, command=self.log_text.yview, bg=C["panel"])
        self.log_text.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Farb-Tags
        self.log_text.tag_config("info",    foreground="#58A6FF")
        self.log_text.tag_config("success", foreground=C["success"])
        self.log_text.tag_config("warning", foreground=C["warning"])
        self.log_text.tag_config("error",   foreground=C["danger"])
        self.log_text.tag_config("delete",  foreground=C["secondary_fg"])
        self.log_text.tag_config("keep",    foreground=C["primary_fg"])
        self.log_text.tag_config("dim",     foreground=C["muted"])

    def _clear_log(self):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def _build_controls(self):
        frame = tk.Frame(self.root, bg=C["panel"], pady=10)
        frame.pack(fill=tk.X, padx=24, pady=(0, 4))

        self.pause_btn = styled_btn(frame, "⏸  Pause", self.pause_scan,
                                    color=C["warning"], width=14)
        self.pause_btn.configure(state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=(12, 8))

        self.abort_btn = styled_btn(frame, "⏹  Abbrechen", self.abort_scan,
                                    color=C["danger"], width=14)
        self.abort_btn.configure(state=tk.DISABLED)
        self.abort_btn.pack(side=tk.LEFT)

    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=C["card"], height=30)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)

        self.status_dot = tk.Label(bar, text="●", bg=C["card"],
                                    fg=C["success"], font=("Arial", 12))
        self.status_dot.pack(side=tk.LEFT, padx=(16, 4), pady=4)

        self.status_label = tk.Label(bar, text="Bereit", bg=C["card"],
                                      fg=C["text"], font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT, pady=4)

    # ── Modus-Wechsel ───────────────────────────────────────────────────────

    def on_mode_change(self):
        if self.scanning:
            messagebox.showwarning("Scan läuft", "Modus kann während des Scans nicht geändert werden.")
            return
        mode = self.mode_var.get()
        self.single_frame.pack_forget()
        self.dual_frame.pack_forget()
        if mode == "single":
            self.single_frame.pack(fill=tk.X)
        else:
            self.dual_frame.pack(fill=tk.X)
        self.primary_folder = None
        self.secondary_folder = None
        self.primary_label.config(text="—")
        self.secondary_label.config(text="—")
        self.start_btn.config(state=tk.DISABLED)

    # ── Ordner-Auswahl ──────────────────────────────────────────────────────

    def select_primary_folder(self):
        folder = filedialog.askdirectory(title="Primary-Ordner wählen (wird NICHT verändert)")
        if folder:
            self.primary_folder = folder
            self.primary_label.config(text=f"✓  {Path(folder).name}  ({folder})")
            self.check_dual_ready()

    def select_secondary_folder(self):
        folder = filedialog.askdirectory(title="Secondary-Ordner wählen (wird bereinigt)")
        if folder:
            if self.primary_folder and folder == self.primary_folder:
                messagebox.showerror("Fehler", "Secondary muss sich vom Primary unterscheiden.")
                return
            if self.primary_folder:
                pp = Path(self.primary_folder).resolve()
                sp = Path(folder).resolve()
                if sp.is_relative_to(pp) or pp.is_relative_to(sp):
                    messagebox.showerror("Fehler", "Ordner dürfen nicht ineinander liegen.")
                    return
            self.secondary_folder = folder
            self.secondary_label.config(text=f"✓  {Path(folder).name}  ({folder})")
            self.check_dual_ready()

    def check_dual_ready(self):
        if self.primary_folder and self.secondary_folder:
            self.start_btn.config(state=tk.NORMAL, bg=C["success"])
        else:
            self.start_btn.config(state=tk.DISABLED, bg=C["card"])

    def select_single_folder(self):
        if self.scanning:
            messagebox.showwarning("Scan läuft", "Scan läuft bereits.")
            return
        folder = filedialog.askdirectory(title="Ordner für Duplikat-Suche wählen")
        if folder:
            self.stats = self._empty_stats()
            self._clear_log()
            self.log(f"Single-Folder-Scan: {folder}", "info")
            self.scanning = True
            self.paused = False
            self.abort = False
            self.single_select_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.abort_btn.config(state=tk.NORMAL)
            threading.Thread(target=self.scan_folder, args=(folder,), daemon=True).start()

    # ── Dual-Scan starten ───────────────────────────────────────────────────

    def start_dual_scan(self):
        if self.scanning:
            messagebox.showwarning("Scan läuft", "Scan läuft bereits.")
            return
        if not self.primary_folder or not self.secondary_folder:
            messagebox.showerror("Fehler", "Bitte Primary und Secondary wählen.")
            return
        if not os.path.exists(self.primary_folder):
            messagebox.showerror("Fehler", "Primary-Ordner existiert nicht.")
            return
        if not os.path.exists(self.secondary_folder):
            messagebox.showerror("Fehler", "Secondary-Ordner existiert nicht.")
            return

        self.stats = self._empty_stats()
        self._clear_log()
        self.log("Dual-Folder-Scan gestartet", "info")
        self.log(f"PRIMARY   (geschützt): {self.primary_folder}", "keep")
        self.log(f"SECONDARY (bereinigen): {self.secondary_folder}", "warning")

        self.scanning = True
        self.paused = False
        self.abort = False
        self.primary_btn.config(state=tk.DISABLED)
        self.secondary_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.abort_btn.config(state=tk.NORMAL)
        threading.Thread(target=self.scan_dual_folders, daemon=True).start()

    # ── Pause / Abort ───────────────────────────────────────────────────────

    def pause_scan(self):
        if self.paused:
            self.paused = False
            self.pause_event.set()
            self.pause_btn.config(text="⏸  Pause")
            self._set_status("Scanning …", C["accent"])
            self.log("Scan fortgesetzt", "info")
        else:
            self.paused = True
            self.pause_event.clear()
            self.pause_btn.config(text="▶  Fortsetzen")
            self._set_status("Pausiert", C["warning"])
            self.log("Scan pausiert", "warning")

    def abort_scan(self):
        self.abort = True
        self._set_status("Wird abgebrochen …", C["danger"])
        self.log("Abbruch angefordert", "warning")

    # ── Logging ─────────────────────────────────────────────────────────────

    def log(self, message, level="info"):
        self.log_text.config(state=tk.NORMAL)
        ts = time.strftime("%H:%M:%S")
        icons = {"info": "ℹ", "success": "✓", "warning": "⚠",
                 "error": "✗", "delete": "🗑", "keep": "📌"}
        icon = icons.get(level, "•")
        self.log_text.insert(tk.END, f"[{ts}] {icon}  {message}\n", level)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

    def _set_status(self, text, color):
        self.status_label.config(text=text)
        self.status_dot.config(fg=color)

    # ── Hashing / Hilfsmethoden ─────────────────────────────────────────────

    def get_file_hash(self, filepath):
        sha = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for block in iter(lambda: f.read(4096), b""):
                    sha.update(block)
            return sha.hexdigest()
        except Exception as e:
            self.log(f"Hash-Fehler {Path(filepath).name}: {e}", "error")
            self.stats['errors'] += 1
            return None

    def filenames_similar(self, name1, name2):
        if name1 == name2:
            return False
        stem1, ext1 = Path(name1).stem, Path(name1).suffix
        stem2, ext2 = Path(name2).stem, Path(name2).suffix
        if ext1 != ext2:
            return False
        for n in [2, 3]:
            if len(stem1) >= 6 and len(stem2) >= 6:
                if stem1[:-n] == stem2[:-n]:
                    return True
        return False

    def has_copy_numbering(self, filename):
        import re
        return bool(re.search(r'\s*\(\d+\)$', Path(filename).stem))

    def get_file_size(self, filepath):
        try:
            return os.path.getsize(filepath)
        except:
            return 0

    def format_size(self, b):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if b < 1024.0:
                return f"{b:.2f} {unit}"
            b /= 1024.0
        return f"{b:.2f} TB"

    # ── Entscheidungs-Dialog ────────────────────────────────────────────────

    def ask_user_decision(self, file1, file2):
        self.stats['user_decisions'] += 1
        self.log(f"Entscheidung erforderlich: {Path(file1).name} vs {Path(file2).name}", "warning")

        decision = {"result": None}

        dlg = tk.Toplevel(self.root)
        dlg.title("Ähnliche Dateinamen")
        dlg.geometry("620x300")
        dlg.configure(bg=C["bg"])
        dlg.transient(self.root)
        dlg.grab_set()

        tk.Label(dlg, text="Identischer Inhalt – ähnliche Namen",
                 bg=C["bg"], fg=C["text"], font=("Arial", 13, "bold")).pack(pady=(20, 8))

        for color, label, path in [
            (C["primary_fg"],   "Behalten:",  file1),
            (C["secondary_fg"], "Löschen?:", file2),
        ]:
            row = tk.Frame(dlg, bg=C["panel"], padx=14, pady=8)
            row.pack(fill=tk.X, padx=20, pady=3)
            tk.Label(row, text=label, bg=C["panel"], fg=color,
                     font=("Arial", 10, "bold"), width=10, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=Path(path).name, bg=C["panel"], fg=C["text"],
                     font=("Arial", 10)).pack(side=tk.LEFT)

        btn_row = tk.Frame(dlg, bg=C["bg"])
        btn_row.pack(pady=20)

        for text, color, val in [
            ("🗑  Duplikat löschen", C["danger"],  "delete"),
            ("📌  Beide behalten",  C["accent"],  "keep"),
            ("Überspringen",        C["muted"],   "cancel"),
        ]:
            tk.Button(btn_row, text=text, bg=color, fg=C["text"], relief=tk.FLAT,
                      font=("Arial", 11, "bold"), padx=14, pady=8, cursor="hand2",
                      command=lambda v=val: [decision.__setitem__("result", v), dlg.destroy()]
                      ).pack(side=tk.LEFT, padx=6)

        self.root.wait_window(dlg)
        return decision["result"]

    # ── Scan: Einzelner Ordner ──────────────────────────────────────────────

    def scan_folder(self, folder):
        try:
            self._set_status("Scanning …", C["accent"])
            self.log("Phase 1: Dateien sammeln …", "info")

            all_files = []
            for root, _, files in os.walk(folder):
                if self.abort:
                    break
                for f in files:
                    if not f.startswith('.'):
                        all_files.append(os.path.join(root, f))

            if self.abort:
                self.update_ui("Abgebrochen.", "ready")
                return

            self.stats['total_files'] = len(all_files)
            self.log(f"{self.stats['total_files']} Dateien gefunden", "info")
            self.log("Phase 2: SHA-256-Hashing …", "info")

            hash_map = defaultdict(list)
            total = len(all_files)

            for idx, filepath in enumerate(all_files):
                while self.paused and not self.abort:
                    self.pause_event.wait(timeout=0.1)
                if self.abort:
                    self.update_ui("Abgebrochen.", "ready")
                    return
                pct = int((idx + 1) / total * 100)
                self.progress_label.config(
                    text=f"Hashing: {idx+1}/{total} ({pct}%) — {Path(filepath).name[:55]}")
                self._set_progress(pct)
                self.root.update()
                fh = self.get_file_hash(filepath)
                if fh:
                    hash_map[fh].append(filepath)

            dup_groups = {h: fs for h, fs in hash_map.items() if len(fs) > 1}
            self.stats['duplicate_groups'] = len(dup_groups)

            if not dup_groups:
                self.log("Keine Duplikate gefunden.", "success")
                self.update_ui("Scan abgeschlossen – keine Duplikate.", "ready")
                self.show_statistics()
                return

            self.log(f"{len(dup_groups)} Duplikat-Gruppen gefunden", "warning")
            self.log("Phase 3: Duplikate verarbeiten …", "info")

            for fh, files in dup_groups.items():
                if self.abort:
                    self.update_ui(f"Abgebrochen. {self.stats['files_deleted']} gelöscht.", "ready")
                    self.show_statistics()
                    return
                while self.paused and not self.abort:
                    self.pause_event.wait(timeout=0.1)

                self.log(f"Gruppe ({len(files)} identische Dateien):", "dim")

                no_num = [f for f in files if not self.has_copy_numbering(f)]
                with_num = [f for f in files if self.has_copy_numbering(f)]
                keep = no_num[0] if no_num else files[0]
                to_check = (no_num[1:] + with_num) if no_num else files[1:]

                self.log(f"  BEHALTEN: {keep}", "keep")
                self.stats['files_kept'] += 1

                for dup in to_check:
                    if self.abort:
                        break
                    size = self.get_file_size(dup)
                    if self.filenames_similar(Path(keep).name, Path(dup).name):
                        dec = self.ask_user_decision(keep, dup)
                        if dec == "delete":
                            try:
                                os.remove(dup)
                                self.stats['files_deleted'] += 1
                                self.stats['space_freed'] += size
                                self.log(f"  GELÖSCHT: {dup}  ({self.format_size(size)})", "delete")
                            except Exception as e:
                                self.log(f"  FEHLER: {Path(dup).name}: {e}", "error")
                                self.stats['errors'] += 1
                        elif dec == "keep":
                            self.log(f"  BEHALTEN (beide): {dup}", "keep")
                            self.stats['files_kept'] += 1
                        else:
                            self.log(f"  ÜBERSPRUNGEN: {dup}", "warning")
                    else:
                        try:
                            os.remove(dup)
                            self.stats['files_deleted'] += 1
                            self.stats['space_freed'] += size
                            self.log(f"  GELÖSCHT: {dup}  ({self.format_size(size)})", "delete")
                        except Exception as e:
                            self.log(f"  FEHLER: {Path(dup).name}: {e}", "error")
                            self.stats['errors'] += 1

            self.log("─" * 60, "dim")
            self.log("Scan erfolgreich abgeschlossen.", "success")
            self.update_ui("Scan abgeschlossen.", "ready")
            self.show_statistics()

        except Exception as e:
            self.log(f"KRITISCHER FEHLER: {e}", "error")
            self.stats['errors'] += 1
            self.update_ui(f"Fehler: {e}", "error")
            self.show_statistics()

    # ── Scan: Dual Folder ───────────────────────────────────────────────────

    def scan_dual_folders(self):
        try:
            self._set_status("Scanning …", C["accent"])

            self.log("Phase 1: PRIMARY-Dateien sammeln …", "info")
            primary_files = {}
            for root, _, files in os.walk(self.primary_folder):
                if self.abort:
                    break
                for f in files:
                    if not f.startswith('.'):
                        primary_files.setdefault(f, []).append(os.path.join(root, f))

            if self.abort:
                self.update_ui("Abgebrochen.", "ready")
                return

            self.stats['primary_files'] = sum(len(v) for v in primary_files.values())
            self.log(f"{self.stats['primary_files']} Dateien in PRIMARY", "info")

            self.log("Phase 2: PRIMARY hashen …", "info")
            primary_hashes = {}
            total_p = self.stats['primary_files']
            idx = 0

            for fname, paths in primary_files.items():
                for fp in paths:
                    while self.paused and not self.abort:
                        self.pause_event.wait(timeout=0.1)
                    if self.abort:
                        self.update_ui("Abgebrochen.", "ready")
                        return
                    idx += 1
                    pct = int(idx / total_p * 100) if total_p else 0
                    self.progress_label.config(
                        text=f"PRIMARY hashing: {idx}/{total_p} ({pct}%)")
                    self._set_progress(pct // 2)
                    self.root.update()
                    fh = self.get_file_hash(fp)
                    if fh:
                        primary_hashes.setdefault(fname, {}).setdefault(fh, []).append(fp)

            self.log("Phase 3: SECONDARY zählen …", "info")
            for root, _, files in os.walk(self.secondary_folder):
                for f in files:
                    if not f.startswith('.'):
                        self.stats['secondary_files'] += 1
            self.log(f"{self.stats['secondary_files']} Dateien in SECONDARY", "info")

            self.log("Phase 4: SECONDARY mit PRIMARY vergleichen …", "info")
            idx = 0
            for root, _, files in os.walk(self.secondary_folder):
                if self.abort:
                    break
                for f in files:
                    if f.startswith('.'):
                        continue
                    while self.paused and not self.abort:
                        self.pause_event.wait(timeout=0.1)
                    if self.abort:
                        break
                    idx += 1
                    sp = os.path.join(root, f)
                    pct = int(idx / self.stats['secondary_files'] * 100) if self.stats['secondary_files'] else 0
                    self.progress_label.config(
                        text=f"SECONDARY: {idx}/{self.stats['secondary_files']} ({pct}%)")
                    self._set_progress(50 + pct // 2)
                    self.root.update()

                    if f in primary_hashes:
                        sh = self.get_file_hash(sp)
                        if sh and sh in primary_hashes[f]:
                            size = self.get_file_size(sp)
                            try:
                                os.remove(sp)
                                self.stats['files_deleted'] += 1
                                self.stats['space_freed'] += size
                                ref = primary_hashes[f][sh][0]
                                self.log(f"GELÖSCHT: {sp}", "delete")
                                self.log(f"  ↳ Duplikat von PRIMARY: {ref}", "dim")
                                self.log(f"  ↳ Freigegeben: {self.format_size(size)}", "success")
                            except Exception as e:
                                self.log(f"FEHLER beim Löschen {f}: {e}", "error")
                                self.stats['errors'] += 1
                        else:
                            self.log(f"BEHALTEN: {sp}  (gleicher Name, anderer Inhalt)", "keep")
                            self.stats['files_kept'] += 1
                    else:
                        self.stats['files_kept'] += 1

            if self.abort:
                self.update_ui(f"Abgebrochen. {self.stats['files_deleted']} gelöscht.", "ready")
                self.show_statistics_dual()
                return

            self.stats['total_files'] = self.stats['primary_files'] + self.stats['secondary_files']
            self.log("─" * 60, "dim")
            self.log("Dual-Scan erfolgreich abgeschlossen.", "success")
            self.log(f"PRIMARY unverändert  ·  SECONDARY: {self.stats['files_deleted']} Duplikate entfernt", "success")
            self.update_ui("Dual-Scan abgeschlossen.", "ready")
            self.show_statistics_dual()

        except Exception as e:
            self.log(f"KRITISCHER FEHLER: {e}", "error")
            self.stats['errors'] += 1
            self.update_ui(f"Fehler: {e}", "error")
            self.show_statistics_dual()

    # ── Statistik-Fenster ───────────────────────────────────────────────────

    def _stats_window(self, title, rows):
        w = tk.Toplevel(self.root)
        w.title(title)
        w.configure(bg=C["bg"])
        w.geometry("480x" + str(80 + len(rows) * 34))
        w.resizable(False, False)
        w.transient(self.root)

        tk.Label(w, text=title, bg=C["bg"], fg=C["text"],
                 font=("Arial", 14, "bold")).pack(pady=(20, 10))

        for label, value, color in rows:
            row = tk.Frame(w, bg=C["panel"], padx=16, pady=6)
            row.pack(fill=tk.X, padx=20, pady=2)
            tk.Label(row, text=label, bg=C["panel"], fg=C["muted"],
                     font=("Arial", 10), width=26, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=str(value), bg=C["panel"], fg=color,
                     font=("Arial", 10, "bold")).pack(side=tk.RIGHT)

        styled_btn(w, "OK", w.destroy, color=C["accent"]).pack(pady=16)

    def show_statistics(self):
        s = self.stats
        self._stats_window("Scan-Statistik (Single Folder)", [
            ("Modus",              "Single Folder",                   C["text"]),
            ("Gescannte Dateien",  s['total_files'],                  C["accent"]),
            ("Duplikat-Gruppen",   s['duplicate_groups'],             C["warning"]),
            ("Gelöschte Dateien",  s['files_deleted'],                C["secondary_fg"]),
            ("Behaltene Dateien",  s['files_kept'],                   C["primary_fg"]),
            ("Freigegebener Platz",self.format_size(s['space_freed']),C["success"]),
            ("Nutzer-Entscheide",  s['user_decisions'],               C["muted"]),
            ("Fehler",             s['errors'],                       C["danger"] if s['errors'] else C["muted"]),
        ])

    def show_statistics_dual(self):
        s = self.stats
        self._stats_window("Scan-Statistik (Primary / Secondary)", [
            ("Modus",                  "Primary / Secondary",             C["text"]),
            ("PRIMARY-Dateien",        s['primary_files'],                C["primary_fg"]),
            ("SECONDARY-Dateien",      s['secondary_files'],              C["secondary_fg"]),
            ("Gelöschte Duplikate",    s['files_deleted'],                C["secondary_fg"]),
            ("Behaltene Dateien",      s['files_kept'],                   C["primary_fg"]),
            ("Freigegebener Platz",    self.format_size(s['space_freed']),C["success"]),
            ("Fehler",                 s['errors'],                       C["danger"] if s['errors'] else C["muted"]),
        ])

    # ── UI-Reset nach Scan ──────────────────────────────────────────────────

    def update_ui(self, message, state):
        self.progress_label.config(text=message)
        self._set_progress(0)
        if state == "ready":
            self._set_status("Bereit", C["success"])
        elif state == "error":
            self._set_status("Fehler", C["danger"])
        self.scanning = False
        mode = self.mode_var.get()
        if mode == "single":
            self.single_select_btn.config(state=tk.NORMAL)
        else:
            self.primary_btn.config(state=tk.NORMAL)
            self.secondary_btn.config(state=tk.NORMAL)
            self.check_dual_ready()
        self.pause_btn.config(state=tk.DISABLED, text="⏸  Pause")
        self.abort_btn.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    DuplicateFileRemover(root)
    root.mainloop()
