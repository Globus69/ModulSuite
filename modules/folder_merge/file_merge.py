#!/usr/bin/env python3
"""Folder Merge – Zusammenführen mehrerer Quellordner in einen Zielordner.
Bereinigt verschachtelte Ordnerstrukturen: relative Struktur behalten,
Duplikate bitgenau entfernen, verschieben statt kopieren, leere Ordner aufräumen."""

import difflib
import os
import queue
import re
import shutil
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Konstanten ───────────────────────────────────────────────────────────────
CHUNK_SIZE = 64 * 1024
SIMILARITY_THRESHOLD = 1.00
DEDUP_NAME_THRESHOLD = 1.00

# ── Farb-Palette ─────────────────────────────────────────────────────────────
C = {
    "bg":      "#1A1A2E",
    "panel":   "#16213E",
    "card":    "#0F3460",
    "accent":  "#3498DB",
    "success": "#2ECC71",
    "warning": "#F39C12",
    "danger":  "#E74C3C",
    "text":    "#ECF0F1",
    "muted":   "#7F8C8D",
    "log_bg":  "#0D1117",
    "target":  "#5DADE2",
    "source":  "#A9CCE3",
    "empty":   "#F0B27A",
}


class _MergeAbortedError(Exception):
    pass


def name_similarity(a, b):
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def files_identical(a, b):
    try:
        if os.path.getsize(a) != os.path.getsize(b):
            return False
        with open(a, 'rb') as fa, open(b, 'rb') as fb:
            while True:
                ca, cb = fa.read(CHUNK_SIZE), fb.read(CHUNK_SIZE)
                if ca != cb:
                    return False
                if not ca:
                    return True
    except OSError:
        return False


def _styled_btn(parent, text, cmd, color=None, **kw):
    return tk.Button(
        parent, text=text, command=cmd,
        bg=color or C["card"], fg=C["text"],
        activebackground=C["accent"], activeforeground=C["text"],
        relief=tk.FLAT, font=("Arial", 11, "bold"),
        cursor="hand2", padx=14, pady=7, bd=0, **kw,
    )


class FileMergeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Folder Merge")
        self.root.minsize(720, 700)
        self.root.configure(bg=C["bg"])

        self.source_folders = []
        self.is_running = False
        self.merge_request_queue = queue.Queue()
        self.merge_response_queue = queue.Queue()

        self._build_gui()

    # ── UI-Aufbau ────────────────────────────────────────────────────────────

    def _build_gui(self):
        self._build_header()

        scroll_canvas = tk.Canvas(self.root, bg=C["bg"], highlightthickness=0)
        vsb = tk.Scrollbar(self.root, orient="vertical", command=scroll_canvas.yview,
                           bg=C["panel"])
        scroll_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._inner = tk.Frame(scroll_canvas, bg=C["bg"])
        self._inner.bind("<Configure>",
            lambda e: scroll_canvas.configure(
                scrollregion=scroll_canvas.bbox("all")))
        scroll_canvas.create_window((0, 0), window=self._inner, anchor="nw")
        scroll_canvas.bind_all(
            "<MouseWheel>",
            lambda e: scroll_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        main = self._inner
        pad = {"padx": 24}

        self._section(main, "1", "Zielordner", C["target"])
        self._build_target(main, **pad)

        self._section(main, "2", "Quellordner", C["source"])
        self._build_sources(main, **pad)

        self._section(main, "3", "Ordner-Ähnlichkeit  (Merge)", C["accent"])
        self._build_slider(main, "threshold", SIMILARITY_THRESHOLD,
                           "← mehr Dialoge          weniger Dialoge →",
                           self._on_threshold_change, **pad)

        self._section(main, "4", "Zusammenführen starten", C["success"])
        self._build_merge_block(main, **pad)

        self._section(main, "5", "Duplikate bereinigen", C["warning"])
        self._build_dedup_block(main, **pad)

        self._section(main, "6", "Leere Ordner löschen", C["empty"])
        self._build_empty_block(main, **pad)

        self._section(main, "7", "Aktivitäts-Log", C["muted"])
        self._build_log(main, **pad)

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=C["card"], height=64)
        hdr.pack(fill=tk.X, side=tk.TOP)
        hdr.pack_propagate(False)
        tk.Label(hdr, text="📁  Folder Merge", font=("Arial", 22, "bold"),
                 bg=C["card"], fg=C["text"]).pack(side=tk.LEFT, padx=24, pady=14)
        tk.Label(hdr, text="Zusammenführen · Duplikate bereinigen · Leere Ordner aufräumen",
                 font=("Arial", 10), bg=C["card"], fg=C["muted"]).pack(
            side=tk.LEFT, pady=14)

    def _section(self, parent, num, title, color):
        f = tk.Frame(parent, bg=C["bg"])
        f.pack(fill=tk.X, padx=24, pady=(16, 4))
        badge = tk.Label(f, text=f" {num} ", bg=color, fg=C["text"],
                         font=("Arial", 10, "bold"))
        badge.pack(side=tk.LEFT)
        tk.Label(f, text=f"  {title}", bg=C["bg"], fg=color,
                 font=("Arial", 12, "bold")).pack(side=tk.LEFT)
        sep = tk.Frame(parent, bg=color, height=1)
        sep.pack(fill=tk.X, padx=24, pady=(0, 6))

    def _build_target(self, parent, **kw):
        f = tk.Frame(parent, bg=C["panel"], padx=14, pady=10)
        f.pack(fill=tk.X, **kw, pady=4)

        self.target_var = tk.StringVar()
        entry = tk.Entry(f, textvariable=self.target_var, state="readonly",
                         readonlybackground=C["card"], fg=C["target"],
                         relief=tk.FLAT, font=("Menlo", 10), bd=0)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 10))
        _styled_btn(f, "📂  Auswählen", self._select_target,
                    color=C["accent"]).pack(side=tk.RIGHT)

    def _build_sources(self, parent, **kw):
        f = tk.Frame(parent, bg=C["panel"], padx=14, pady=10)
        f.pack(fill=tk.X, **kw, pady=4)

        list_frame = tk.Frame(f, bg=C["panel"])
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.source_listbox = tk.Listbox(
            list_frame, height=5, bg=C["log_bg"], fg=C["source"],
            selectbackground=C["card"], selectforeground=C["text"],
            font=("Menlo", 10), relief=tk.FLAT, bd=0,
        )
        sb = tk.Scrollbar(list_frame, orient=tk.VERTICAL,
                          command=self.source_listbox.yview, bg=C["panel"])
        self.source_listbox.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.source_listbox.pack(fill=tk.BOTH, expand=True)

        btn_col = tk.Frame(f, bg=C["panel"])
        btn_col.pack(side=tk.RIGHT, padx=(10, 0))
        _styled_btn(btn_col, "+  Hinzufügen", self._add_source,
                    color=C["success"]).pack(fill=tk.X, pady=(0, 6))
        _styled_btn(btn_col, "−  Entfernen", self._remove_source,
                    color=C["danger"]).pack(fill=tk.X)

    def _build_slider(self, parent, attr, default, hint_text, callback, **kw):
        f = tk.Frame(parent, bg=C["panel"], padx=14, pady=10)
        f.pack(fill=tk.X, **kw, pady=4)

        var = tk.IntVar(value=int(default * 100))
        setattr(self, f"{attr}_var", var)

        lbl = tk.Label(f, text=f"Schwellenwert: {var.get()} %",
                       bg=C["panel"], fg=C["text"], font=("Arial", 11, "bold"))
        lbl.pack(anchor=tk.W)
        setattr(self, f"{attr}_label", lbl)

        scale = tk.Scale(
            f, from_=0, to=100, orient=tk.HORIZONTAL, variable=var,
            command=callback, bg=C["panel"], fg=C["text"],
            troughcolor=C["card"], activebackground=C["accent"],
            highlightthickness=0, showvalue=False, sliderlength=20,
            tickinterval=25, font=("Arial", 9),
        )
        scale.pack(fill=tk.X)
        setattr(self, f"{attr}_scale", scale)

        tk.Label(f, text=hint_text, bg=C["panel"], fg=C["muted"],
                 font=("Arial", 9)).pack(anchor=tk.W)

    def _build_merge_block(self, parent, **kw):
        f = tk.Frame(parent, bg=C["panel"], padx=14, pady=10)
        f.pack(fill=tk.X, **kw, pady=4)

        self.start_btn = _styled_btn(f, "▶  Zusammenführen starten",
                                     self._start_merge, color=C["success"])
        self.start_btn.pack(fill=tk.X)

        self.merge_progress_var = tk.DoubleVar()
        self._make_progress(f, self.merge_progress_var, "merge")

    def _build_dedup_block(self, parent, **kw):
        f = tk.Frame(parent, bg=C["panel"], padx=14, pady=10)
        f.pack(fill=tk.X, **kw, pady=4)

        self._build_slider(f, "dedup_threshold", DEDUP_NAME_THRESHOLD,
                           "← mehr Treffer               weniger Treffer →",
                           self._on_dedup_threshold_change)

        self.dedup_btn = _styled_btn(f, "🔍  Duplikate bereinigen",
                                     self._start_dedup, color=C["warning"])
        self.dedup_btn.pack(fill=tk.X, pady=(8, 0))

        self.dedup_progress_var = tk.DoubleVar()
        self._make_progress(f, self.dedup_progress_var, "dedup")

    def _build_empty_block(self, parent, **kw):
        f = tk.Frame(parent, bg=C["panel"], padx=14, pady=10)
        f.pack(fill=tk.X, **kw, pady=4)

        row = tk.Frame(f, bg=C["panel"])
        row.pack(fill=tk.X, pady=(0, 8))
        self.empty_dir_var = tk.StringVar()
        tk.Entry(row, textvariable=self.empty_dir_var, state="readonly",
                 readonlybackground=C["card"], fg=C["empty"],
                 relief=tk.FLAT, font=("Menlo", 10), bd=0
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 10))
        _styled_btn(row, "📂  Auswählen", self._select_empty_dir,
                    color=C["accent"]).pack(side=tk.RIGHT)

        self.empty_btn = _styled_btn(f, "🗑  Leere Ordner löschen",
                                     self._start_remove_empty, color=C["empty"])
        self.empty_btn.pack(fill=tk.X)

        self.empty_progress_var = tk.DoubleVar()
        self._make_progress(f, self.empty_progress_var, "empty")

    def _make_progress(self, parent, var, attr):
        canvas = tk.Canvas(parent, height=4, bg=C["card"], highlightthickness=0)
        canvas.pack(fill=tk.X, pady=(6, 2))
        setattr(self, f"{attr}_canvas", canvas)

        status = tk.StringVar(value="Bereit")
        setattr(self, f"{attr}_status_var", status)
        tk.Label(parent, textvariable=status, bg=C["panel"], fg=C["muted"],
                 font=("Arial", 9), anchor=tk.W).pack(anchor=tk.W)

    def _draw_progress(self, canvas, pct, color=None):
        canvas.delete("all")
        w = canvas.winfo_width()
        if w > 0 and pct > 0:
            canvas.create_rectangle(0, 0, w * pct / 100, 4,
                                    fill=color or C["accent"], outline="")

    def _build_log(self, parent, **kw):
        f = tk.Frame(parent, bg=C["panel"], padx=14, pady=10)
        f.pack(fill=tk.BOTH, expand=True, **kw, pady=(4, 20))

        hdr = tk.Frame(f, bg=C["panel"])
        hdr.pack(fill=tk.X, pady=(0, 6))
        tk.Label(hdr, text="Log", bg=C["panel"], fg=C["muted"],
                 font=("Arial", 9, "bold")).pack(side=tk.LEFT)
        tk.Button(hdr, text="✕ Leeren", bg=C["panel"], fg=C["muted"],
                  relief=tk.FLAT, font=("Arial", 9), cursor="hand2", bd=0,
                  command=lambda: [
                      self.log_text.configure(state=tk.NORMAL),
                      self.log_text.delete("1.0", tk.END),
                      self.log_text.configure(state=tk.DISABLED),
                  ]).pack(side=tk.RIGHT)

        self.log_text = tk.Text(
            f, height=12, bg=C["log_bg"], fg="#58A6FF",
            insertbackground="#58A6FF", relief=tk.FLAT,
            font=("Menlo", 10), padx=10, pady=8, state=tk.DISABLED,
        )
        sb = tk.Scrollbar(f, orient=tk.VERTICAL, command=self.log_text.yview,
                          bg=C["panel"])
        self.log_text.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.log_text.tag_config("ok",      foreground=C["success"])
        self.log_text.tag_config("warn",    foreground=C["warning"])
        self.log_text.tag_config("err",     foreground=C["danger"])
        self.log_text.tag_config("dup",     foreground=C["danger"])
        self.log_text.tag_config("move",    foreground=C["source"])
        self.log_text.tag_config("head",    foreground=C["accent"])
        self.log_text.tag_config("dim",     foreground=C["muted"])

    # ── Slider-Callbacks ─────────────────────────────────────────────────────

    def _on_threshold_change(self, val):
        global SIMILARITY_THRESHOLD
        iv = int(float(val))
        self.threshold_var.set(iv)
        self.threshold_label.config(text=f"Schwellenwert: {iv} %")
        SIMILARITY_THRESHOLD = iv / 100.0

    def _on_dedup_threshold_change(self, val):
        global DEDUP_NAME_THRESHOLD
        iv = int(float(val))
        self.dedup_threshold_var.set(iv)
        self.dedup_threshold_label.config(text=f"Dateinamen-Toleranz: {iv} %")
        DEDUP_NAME_THRESHOLD = iv / 100.0

    # ── Ordner-Auswahl ────────────────────────────────────────────────────────

    def _select_target(self):
        p = filedialog.askdirectory(title="Zielordner auswählen")
        if p:
            self.target_var.set(p)

    def _add_source(self):
        p = filedialog.askdirectory(title="Quellordner hinzufügen")
        if p and p not in self.source_folders:
            self.source_folders.append(p)
            self.source_listbox.insert(tk.END, p)

    def _remove_source(self):
        sel = self.source_listbox.curselection()
        if sel:
            idx = sel[0]
            self.source_folders.pop(idx)
            self.source_listbox.delete(idx)

    def _select_empty_dir(self):
        p = filedialog.askdirectory(title="Ordner auswählen (leere Unterordner löschen)")
        if p:
            self.empty_dir_var.set(p)

    # ── Log ───────────────────────────────────────────────────────────────────

    def _log(self, msg, tag=None):
        self.root.after(0, self._append_log, msg, tag)

    def _append_log(self, msg, tag=None):
        self.log_text.configure(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  {msg}\n"
        if tag:
            self.log_text.insert(tk.END, line, tag)
        else:
            self.log_text.insert(tk.END, line)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    # ── Merge ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _is_subpath(child, parent):
        try:
            child = os.path.realpath(child)
            parent = os.path.realpath(parent)
            return child == parent or child.startswith(parent + os.sep)
        except (OSError, ValueError):
            return False

    def _start_merge(self):
        target = self.target_var.get()
        if not target:
            messagebox.showwarning("Fehler", "Bitte einen Zielordner auswählen.")
            return
        if not self.source_folders:
            messagebox.showwarning("Fehler", "Bitte mindestens einen Quellordner hinzufügen.")
            return
        if self.is_running:
            return

        for src in self.source_folders:
            if self._is_subpath(src, target):
                messagebox.showwarning("Fehler",
                    f"Quellordner liegt innerhalb des Zielordners:\n{src}")
                return
            if self._is_subpath(target, src):
                messagebox.showwarning("Fehler",
                    f"Zielordner liegt innerhalb eines Quellordners:\n{src}")
                return

        self.is_running = True
        self.start_btn.configure(state=tk.DISABLED)
        self.dedup_btn.configure(state=tk.DISABLED)
        self.merge_progress_var.set(0)
        self.merge_status_var.set("Läuft …")

        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

        self._schedule_merge_dialog_poll()
        threading.Thread(target=self._run_merge,
                         args=(target, list(self.source_folders)), daemon=True).start()

    def _schedule_merge_dialog_poll(self):
        if not self.is_running:
            return
        self.root.after(150, self._poll_merge_dialog)

    def _poll_merge_dialog(self):
        if not self.is_running:
            return
        try:
            req = self.merge_request_queue.get_nowait()
        except queue.Empty:
            self._schedule_merge_dialog_poll()
            return
        if req[0] == "similar_folder":
            self._show_similar_folder_dialog(req[1], req[2])
        self._schedule_merge_dialog_poll()

    def _show_similar_folder_dialog(self, current, found):
        dlg = tk.Toplevel(self.root)
        dlg.title("Ordner-Ähnlichkeit")
        dlg.configure(bg=C["bg"])
        dlg.minsize(480, 0)
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.protocol("WM_DELETE_WINDOW", lambda: None)

        result = {"value": "skip"}
        ratio = name_similarity(current, found)

        tk.Label(dlg, text="Ähnlicher Ordner gefunden",
                 bg=C["bg"], fg=C["text"], font=("Arial", 13, "bold")).pack(pady=(20, 10))

        for label, value, color in [
            ("Quellordner:", current, C["source"]),
            ("Gefunden:",    found,   C["target"]),
            ("Übereinstimmung:", f"{ratio*100:.1f} %",
             C["success"] if ratio >= 0.9 else C["warning"]),
        ]:
            row = tk.Frame(dlg, bg=C["panel"], padx=16, pady=6)
            row.pack(fill=tk.X, padx=20, pady=2)
            tk.Label(row, text=label, bg=C["panel"], fg=C["muted"],
                     font=("Arial", 10), width=18, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=value, bg=C["panel"], fg=color,
                     font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        tk.Label(dlg, text="Soll der vorhandene Ordner genutzt werden?",
                 bg=C["bg"], fg=C["muted"], font=("Arial", 10)).pack(pady=(12, 6))

        btn_row = tk.Frame(dlg, bg=C["bg"])
        btn_row.pack(pady=16)

        for text, color, val in [
            ("✓  Ja, zusammenführen", C["success"],  "use_existing"),
            ("✕  Nein, neuer Ordner", C["warning"],  "skip"),
            ("⏹  Abbruch",           C["danger"],   "abort"),
        ]:
            tk.Button(btn_row, text=text, bg=color, fg=C["text"], relief=tk.FLAT,
                      font=("Arial", 11, "bold"), padx=12, pady=7, cursor="hand2",
                      command=lambda v=val: [result.__setitem__("value", v), dlg.destroy()]
                      ).pack(side=tk.LEFT, padx=5)

        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")

        self.root.wait_window(dlg)
        self.merge_response_queue.put(result["value"])

    def _find_best_matching_folder(self, parent_dir, wanted):
        if not os.path.isdir(parent_dir):
            return None, None, 0.0
        best_path, best_ratio = None, 0.0
        for entry in os.listdir(parent_dir):
            sub = os.path.join(parent_dir, entry)
            if not os.path.isdir(sub):
                continue
            r = name_similarity(entry, wanted)
            if r >= 1.0:
                return sub, sub, 1.0
            if r > best_ratio:
                best_ratio, best_path = r, sub
        return None, best_path, best_ratio

    def _resolve_target_dir(self, target_root, rel_dir):
        norm = (rel_dir or "").strip().strip(os.sep)
        if not norm or norm == ".":
            return target_root
        cache = getattr(self, "_resolve_cache", None)
        if cache is not None and norm in cache:
            return cache[norm]
        current = target_root
        segments = [p for p in rel_dir.split(os.sep) if p]
        path_so_far = ""
        for seg in segments:
            path_so_far = os.path.join(path_so_far, seg) if path_so_far else seg
            if cache is not None and path_so_far in cache:
                current = cache[path_so_far]
                continue
            exact, similar, ratio = self._find_best_matching_folder(current, seg)
            if exact:
                current = exact
                if cache is not None:
                    cache[path_so_far] = current
                continue
            if similar and ratio >= SIMILARITY_THRESHOLD and ratio < 1.0:
                self.merge_request_queue.put(("similar_folder", seg, os.path.basename(similar)))
                response = self.merge_response_queue.get()
                if response == "abort":
                    raise _MergeAbortedError("Abgebrochen")
                if response == "use_existing":
                    current = similar
                    if cache is not None:
                        cache[path_so_far] = current
                    continue
            new_dir = os.path.join(current, seg)
            os.makedirs(new_dir, exist_ok=True)
            current = new_dir
            if cache is not None:
                cache[path_so_far] = current
        return current

    def _merge_single_file(self, src_file, dest_dir, rel_path, log_lines, stats):
        fname = os.path.basename(src_file)
        dest_file = os.path.join(dest_dir, fname)
        if not os.path.exists(dest_file):
            os.makedirs(dest_dir, exist_ok=True)
            shutil.move(src_file, dest_file)
            stats["moved"] += 1
            self._log(f"  verschoben  →  {rel_path}", "move")
            log_lines.append(f"  verschoben: {rel_path}")
            return
        if files_identical(src_file, dest_file):
            os.remove(src_file)
            stats["deleted_dup"] += 1
            self._log(f"  Duplikat gelöscht  →  {rel_path}", "dup")
            log_lines.append(f"  Duplikat gelöscht: {rel_path}")
            return
        stem, ext = os.path.splitext(fname)
        counter = 1
        while True:
            new_name = f"{stem}_{counter}{ext}"
            new_dest = os.path.join(dest_dir, new_name)
            if not os.path.exists(new_dest):
                shutil.move(src_file, new_dest)
                stats["moved"] += 1
                self._log(f"  verschoben → {new_name}  (Namenskollision)", "move")
                log_lines.append(f"  verschoben → {new_name}: {rel_path}")
                break
            if files_identical(src_file, new_dest):
                os.remove(src_file)
                stats["deleted_dup"] += 1
                self._log(f"  Duplikat (≙ {new_name}) gelöscht", "dup")
                log_lines.append(f"  Duplikat (≙ {new_name}) gelöscht: {rel_path}")
                break
            counter += 1

    _IGNORABLE = {".DS_Store", "Thumbs.db", "desktop.ini"}

    @classmethod
    def _is_dir_only_ignorable(cls, d):
        try:
            return all(e in cls._IGNORABLE for e in os.listdir(d))
        except OSError:
            return False

    @classmethod
    def _purge_ignorable_and_rmdir(cls, d):
        for e in os.listdir(d):
            if e in cls._IGNORABLE:
                try:
                    os.remove(os.path.join(d, e))
                except OSError:
                    pass
        os.rmdir(d)

    @classmethod
    def _remove_empty_dirs_upward(cls, dirpath, source_root):
        norm_root = os.path.normpath(source_root)
        while dirpath and os.path.normpath(dirpath) != norm_root:
            if not os.path.isdir(dirpath):
                break
            if os.path.basename(dirpath) == "_Quelle":
                break
            try:
                if not cls._is_dir_only_ignorable(dirpath):
                    break
                cls._purge_ignorable_and_rmdir(dirpath)
            except OSError:
                break
            dirpath = os.path.dirname(dirpath)

    def _run_merge(self, target, sources):
        file_list = []
        for src in sources:
            if not os.path.isdir(src):
                continue
            for dirpath, _, filenames in os.walk(src):
                if os.path.basename(dirpath) == "_Quelle":
                    continue
                for fname in filenames:
                    src_file = os.path.join(dirpath, fname)
                    rel = os.path.relpath(src_file, src)
                    file_list.append((src, rel, src_file))
        file_list.sort(key=lambda x: x[1].count(os.sep))

        total = len(file_list)
        if total == 0:
            self._log("Keine Dateien in den Quellordnern gefunden.", "warn")
            self._finish_task(self.merge_status_var)
            return

        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._log(f"=== Merge gestartet: {ts} ===", "head")
        self._log(f"Ziel: {target}", "head")
        self._log(f"Quellen: {len(sources)}  ·  Dateien: {total}", "head")
        self._log("")

        log_lines = [f"=== File Merge Log ===", f"Datum: {ts}",
                     f"Zielordner: {target}", ""]
        stats = {"moved": 0, "deleted_dup": 0, "errors": 0}
        self._resolve_cache = {}
        aborted = False

        for i, (source_root, rel_path, src_file) in enumerate(file_list):
            try:
                dest_dir = self._resolve_target_dir(target, os.path.dirname(rel_path))
                self._merge_single_file(src_file, dest_dir, rel_path, log_lines, stats)
                src_dir = os.path.dirname(src_file)
                if os.path.isdir(src_dir):
                    self._remove_empty_dirs_upward(src_dir, source_root)
            except _MergeAbortedError:
                aborted = True
                self._log("*** ABBRUCH durch Benutzer ***", "warn")
                log_lines.append("*** ABBRUCH ***")
                break
            except Exception as e:
                stats["errors"] += 1
                self._log(f"  FEHLER: {rel_path} – {e}", "err")
                log_lines.append(f"  FEHLER: {rel_path} – {e}")

            pct = ((i + 1) / total) * 100
            self.root.after(0, self._update_merge_progress, pct, i + 1, total)

        empty_removed = 0
        if not aborted:
            self._log("", "dim")
            self._log("Leere Quellordner aufräumen …", "dim")
            for src in sources:
                if not os.path.isdir(src):
                    continue
                while True:
                    n = 0
                    for dp, _, _ in os.walk(src, topdown=False):
                        if os.path.basename(dp) == "_Quelle":
                            continue
                        try:
                            if self._is_dir_only_ignorable(dp):
                                self._purge_ignorable_and_rmdir(dp)
                                n += 1
                        except OSError:
                            pass
                    empty_removed += n
                    if n == 0:
                        break

        summary = (
            f"{'ABGEBROCHEN. Bis dahin: ' if aborted else ''}"
            f"{stats['moved']} Dateien verschoben  ·  "
            f"{stats['deleted_dup']} Duplikate gelöscht"
            + (f"  ·  {empty_removed} leere Ordner entfernt" if not aborted else "")
            + (f"  ·  {stats['errors']} Fehler" if stats["errors"] else "")
        )
        self._log("", "dim")
        self._log(summary, "ok" if not aborted else "warn")
        self._log("=== " + ("Abgebrochen" if aborted else "Fertig") + " ===", "head")
        log_lines += ["", summary]

        log_path = os.path.join(target, "merge_log.txt")
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("\n".join(log_lines))
            self._log(f"Log gespeichert: {log_path}", "dim")
        except Exception as e:
            self._log(f"Log-Fehler: {e}", "err")

        self._resolve_cache = None
        self._finish_task(self.merge_status_var)

    def _update_merge_progress(self, pct, cur, total):
        self.merge_progress_var.set(pct)
        self.merge_status_var.set(f"{cur} / {total} Dateien  ({pct:.0f} %)")
        self._draw_progress(self.merge_canvas, pct, C["success"])

    # ── Dedup ─────────────────────────────────────────────────────────────────

    _DEDUP_RE = re.compile(r'^(.+)_(\d+)(\.[^.]+)$')

    def _start_dedup(self):
        target = self.target_var.get()
        if not target:
            messagebox.showwarning("Fehler", "Bitte einen Zielordner auswählen.")
            return
        if not os.path.isdir(target):
            messagebox.showwarning("Fehler", "Zielordner existiert nicht.")
            return
        if self.is_running:
            return
        self.is_running = True
        self.start_btn.configure(state=tk.DISABLED)
        self.dedup_btn.configure(state=tk.DISABLED)
        self.dedup_progress_var.set(0)
        self.dedup_status_var.set("Läuft …")
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
        threading.Thread(target=self._run_dedup, args=(target,), daemon=True).start()

    def _run_dedup(self, target):
        self._log(f"=== Duplikate bereinigen: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===", "head")
        self._log(f"Zielordner: {target}", "head")
        self._log("")

        candidates = []
        for dp, _, fnames in os.walk(target):
            for fn in fnames:
                m = self._DEDUP_RE.match(fn)
                if m:
                    full = os.path.join(dp, fn)
                    base_name = m.group(1) + m.group(3)
                    base_path = os.path.join(dp, base_name)
                    candidates.append((full, base_path, fn, base_name))

        total = len(candidates)
        if total == 0:
            self._log("Keine nummerierten Duplikate gefunden.", "ok")
            self._finish_task(self.dedup_status_var)
            return

        self._log(f"{total} nummerierte Dateien zum Prüfen", "dim")
        self._log("")
        deleted = kept = errors = 0

        for i, (dup_path, base_path, dup_name, base_name) in enumerate(candidates):
            rel = os.path.relpath(dup_path, target)
            try:
                if os.path.exists(base_path) and files_identical(dup_path, base_path):
                    os.remove(dup_path)
                    self._log(f"  Gelöscht: {rel}  (≙ {base_name})", "dup")
                    deleted += 1
                else:
                    self._log(f"  Behalten: {rel}  (unterschiedlich)", "dim")
                    kept += 1
            except Exception as e:
                self._log(f"  FEHLER: {rel} – {e}", "err")
                errors += 1

            pct = ((i + 1) / total) * 100
            self.root.after(0, self._update_dedup_progress, pct, i + 1, total)

        self._log("", "dim")
        self._log(
            f"Ergebnis: {deleted} gelöscht  ·  {kept} behalten"
            + (f"  ·  {errors} Fehler" if errors else ""),
            "ok",
        )
        self._log("=== Fertig ===", "head")
        self._finish_task(self.dedup_status_var)

    def _update_dedup_progress(self, pct, cur, total):
        self.dedup_progress_var.set(pct)
        self.dedup_status_var.set(f"{cur} / {total}  ({pct:.0f} %)")
        self._draw_progress(self.dedup_canvas, pct, C["warning"])

    # ── Leere Ordner ──────────────────────────────────────────────────────────

    def _start_remove_empty(self):
        target = self.empty_dir_var.get()
        if not target:
            messagebox.showwarning("Fehler", "Bitte einen Ordner auswählen.")
            return
        if not os.path.isdir(target):
            messagebox.showwarning("Fehler", "Ordner existiert nicht.")
            return
        if self.is_running:
            return
        self.is_running = True
        self.start_btn.configure(state=tk.DISABLED)
        self.dedup_btn.configure(state=tk.DISABLED)
        self.empty_btn.configure(state=tk.DISABLED)
        self.empty_progress_var.set(0)
        self.empty_status_var.set("Läuft …")
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)
        threading.Thread(target=self._run_remove_empty, args=(target,), daemon=True).start()

    def _run_remove_empty(self, target):
        self._log(f"=== Leere Ordner löschen: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===", "head")
        self._log(f"Ordner: {target}", "head")
        self._log("")
        deleted = errors = round_nr = 0
        norm_target = os.path.normpath(target)

        while True:
            round_nr += 1
            round_del = 0
            self.root.after(0, lambda r=round_nr: self.empty_status_var.set(
                f"Durchlauf {r}: Scanne …"))
            self._log(f"Durchlauf {round_nr} …", "dim")

            all_dirs = [
                dp for dp, _, _ in os.walk(target, topdown=False)
                if os.path.normpath(dp) != norm_target
            ]
            if not all_dirs:
                if round_nr == 1:
                    self._log("Keine Unterordner gefunden.", "dim")
                break

            for i, dp in enumerate(all_dirs):
                rel = os.path.relpath(dp, target)
                try:
                    if os.path.isdir(dp) and self._is_dir_only_ignorable(dp):
                        self._purge_ignorable_and_rmdir(dp)
                        self._log(f"  Gelöscht: {rel}", "dup")
                        round_del += 1
                        deleted += 1
                except OSError as e:
                    self._log(f"  FEHLER: {rel} – {e}", "err")
                    errors += 1

                pct = ((i + 1) / len(all_dirs)) * 100
                short = rel if len(rel) <= 45 else "…" + rel[-44:]
                self.root.after(0, self._update_empty_progress,
                                pct, i + 1, len(all_dirs), round_nr, short)

            if round_del == 0:
                break
            self._log(f"  → {round_del} gelöscht in Durchlauf {round_nr}", "ok")

        self._log("", "dim")
        self._log(
            f"Ergebnis: {deleted} leere Ordner gelöscht"
            + (f"  ·  {errors} Fehler" if errors else ""),
            "ok",
        )
        self._log("=== Fertig ===", "head")
        self._finish_remove_empty()

    def _update_empty_progress(self, pct, cur, total, rnd, rel):
        self.empty_progress_var.set(pct)
        self.empty_status_var.set(
            f"Durchlauf {rnd}: {cur}/{total} ({pct:.0f} %)  ▸ {rel}")
        self._draw_progress(self.empty_canvas, pct, C["empty"])

    # ── Aufräumen ─────────────────────────────────────────────────────────────

    def _finish_task(self, status_var):
        def _done():
            self.is_running = False
            self.start_btn.configure(state=tk.NORMAL)
            self.dedup_btn.configure(state=tk.NORMAL)
            status_var.set("Fertig")
        self.root.after(0, _done)

    def _finish_remove_empty(self):
        def _done():
            self.is_running = False
            self.start_btn.configure(state=tk.NORMAL)
            self.dedup_btn.configure(state=tk.NORMAL)
            self.empty_btn.configure(state=tk.NORMAL)
            self.empty_status_var.set("Fertig")
        self.root.after(0, _done)


def main():
    root = tk.Tk()
    FileMergeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
