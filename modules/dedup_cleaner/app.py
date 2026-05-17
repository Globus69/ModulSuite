#!/usr/bin/env python3
"""Dedup Cleaner — Nummerierte Datei-Duplikate (name_1.ext) erkennen und löschen."""

import os, re, threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

CHUNK_SIZE = 64 * 1024

C = {
    "bg":      "#1A1A2E", "panel":  "#16213E", "card":   "#0F3460",
    "accent":  "#3498DB", "success":"#2ECC71", "warning":"#F39C12",
    "danger":  "#E74C3C", "text":   "#ECF0F1", "muted":  "#7F8C8D",
    "log_bg":  "#0D1117", "keep":   "#5DADE2", "del":    "#EC7063",
}

DEDUP_RE = re.compile(r'^(.+)_(\d+)(\.[^.]+)$')


def files_identical(a, b):
    try:
        if os.path.getsize(a) != os.path.getsize(b): return False
        with open(a, 'rb') as fa, open(b, 'rb') as fb:
            while True:
                ca, cb = fa.read(CHUNK_SIZE), fb.read(CHUNK_SIZE)
                if ca != cb: return False
                if not ca:   return True
    except OSError:
        return False

def btn(parent, text, cmd, color=None, **kw):
    return tk.Button(parent, text=text, command=cmd,
        bg=color or C["card"], fg=C["text"], activebackground=C["accent"],
        activeforeground=C["text"], relief=tk.FLAT, font=("Arial", 11, "bold"),
        cursor="hand2", padx=14, pady=8, bd=0, **kw)


class DedupCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dedup Cleaner")
        self.root.geometry("680x580")
        self.root.minsize(580, 480)
        self.root.configure(bg=C["bg"])

        self._tol = tk.IntVar(value=100)
        self.running = False
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["card"], height=60)
        hdr.pack(fill=tk.X); hdr.pack_propagate(False)
        tk.Label(hdr, text="🔍  Dedup Cleaner", font=("Arial", 20, "bold"),
                 bg=C["card"], fg=C["text"]).pack(side=tk.LEFT, padx=20, pady=12)
        tk.Label(hdr, text="Nummerierte Duplikate (name_1.ext) erkennen & löschen",
                 font=("Arial", 10), bg=C["card"], fg=C["muted"]).pack(side=tk.LEFT)

        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=14)

        # Ordner
        self._lbl(body, "ORDNER")
        frow = tk.Frame(body, bg=C["panel"], padx=12, pady=10)
        frow.pack(fill=tk.X, pady=(4, 10))
        self._folder_var = tk.StringVar()
        tk.Entry(frow, textvariable=self._folder_var, state="readonly",
                 readonlybackground=C["card"], fg=C["keep"],
                 relief=tk.FLAT, font=("Menlo", 10), bd=0
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 10))
        btn(frow, "📂  Wählen", self._pick, color=C["accent"]).pack(side=tk.RIGHT)

        # Info-Box
        info = tk.Frame(body, bg=C["panel"], padx=14, pady=12)
        info.pack(fill=tk.X, pady=(0, 10))
        tk.Label(info, text="Was wird gesucht?", bg=C["panel"], fg=C["text"],
                 font=("Arial", 10, "bold")).pack(anchor=tk.W)
        tk.Label(info,
                 text="Dateien nach dem Muster  name_1.ext, name_2.ext …\n"
                      "werden mit  name.ext  bitgenau verglichen.\n"
                      "Identische Dateien werden gelöscht — unterschiedliche bleiben erhalten.",
                 bg=C["panel"], fg=C["muted"], font=("Arial", 10), justify=tk.LEFT
                 ).pack(anchor=tk.W, pady=(4, 0))

        # Toleranz-Slider
        self._lbl(body, "DATEINAMEN-TOLERANZ")
        tframe = tk.Frame(body, bg=C["panel"], padx=12, pady=10)
        tframe.pack(fill=tk.X, pady=(4, 10))
        self._tol_lbl = tk.Label(tframe, text="100 %  — nur exakt gleiche Dateinamen",
                                  bg=C["panel"], fg=C["text"], font=("Arial", 11, "bold"))
        self._tol_lbl.pack(anchor=tk.W)
        tk.Scale(tframe, from_=0, to=100, orient=tk.HORIZONTAL, variable=self._tol,
                 command=self._on_tol, bg=C["panel"], fg=C["text"],
                 troughcolor=C["card"], activebackground=C["accent"],
                 highlightthickness=0, showvalue=False, sliderlength=20,
                 tickinterval=25).pack(fill=tk.X)
        tk.Label(tframe, text="← mehr Treffer (unsicherer)         weniger Treffer (sicherer) →",
                 bg=C["panel"], fg=C["muted"], font=("Arial", 9)).pack(anchor=tk.W)

        # Start + Progress
        self._start_btn = btn(body, "🔍  Duplikate bereinigen", self._start, color=C["warning"])
        self._start_btn.pack(fill=tk.X, pady=(0, 6))

        self._bar = tk.Canvas(body, height=5, bg=C["panel"], highlightthickness=0)
        self._bar.pack(fill=tk.X, pady=(0, 2))
        self._status = tk.StringVar(value="Bereit")
        tk.Label(body, textvariable=self._status, bg=C["bg"],
                 fg=C["muted"], font=("Arial", 9), anchor=tk.W).pack(anchor=tk.W)

        # Log
        self._lbl(body, "LOG")
        wrap = tk.Frame(body, bg=C["panel"])
        wrap.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self._log = tk.Text(wrap, bg=C["log_bg"], fg="#58A6FF",
                             font=("Menlo", 10), relief=tk.FLAT,
                             padx=8, pady=6, state=tk.DISABLED)
        lsb = tk.Scrollbar(wrap, orient=tk.VERTICAL, command=self._log.yview, bg=C["panel"])
        self._log.configure(yscrollcommand=lsb.set)
        lsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._log.pack(fill=tk.BOTH, expand=True)
        for tag, color in [("ok", C["success"]), ("del", C["del"]),
                            ("keep", C["keep"]), ("head", C["accent"]),
                            ("warn", C["warning"]), ("dim", C["muted"])]:
            self._log.tag_config(tag, foreground=color)

    def _lbl(self, p, t):
        tk.Label(p, text=t, bg=C["bg"], fg=C["muted"],
                 font=("Arial", 9, "bold")).pack(anchor=tk.W)

    def _on_tol(self, val):
        iv = int(float(val))
        hint = "nur exakt gleiche Dateinamen" if iv == 100 else \
               "ähnliche Dateinamen eingeschlossen" if iv >= 80 else "sehr tolerant"
        self._tol_lbl.config(text=f"{iv} %  — {hint}")

    def _pick(self):
        p = filedialog.askdirectory(title="Ordner für Duplikat-Bereinigung wählen")
        if p: self._folder_var.set(p)

    def _start(self):
        folder = self._folder_var.get()
        if not folder:
            messagebox.showwarning("Fehler", "Bitte einen Ordner wählen.")
            return
        if not os.path.isdir(folder):
            messagebox.showwarning("Fehler", "Ordner existiert nicht.")
            return
        if self.running: return

        self.running = True
        self._start_btn.configure(state=tk.DISABLED)
        self._log.configure(state=tk.NORMAL)
        self._log.delete("1.0", tk.END)
        self._log.configure(state=tk.DISABLED)
        self._status.set("Läuft …")
        threading.Thread(target=self._run, args=(folder,), daemon=True).start()

    def _run(self, folder):
        self._wlog(f"=== Dedup: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===", "head")
        self._wlog(f"Ordner: {folder}", "head")
        self._wlog("")

        candidates = []
        for dp, _, fns in os.walk(folder):
            for fn in fns:
                m = DEDUP_RE.match(fn)
                if m:
                    full      = os.path.join(dp, fn)
                    base_name = m.group(1) + m.group(3)
                    base_path = os.path.join(dp, base_name)
                    candidates.append((full, base_path, fn, base_name))

        total = len(candidates)
        if total == 0:
            self._wlog("Keine nummerierten Duplikate gefunden.", "ok")
            self._done(); return

        self._wlog(f"{total} nummerierte Dateien gefunden — prüfe …", "dim")
        self._wlog("")
        deleted = kept = errors = 0

        for i, (dup, base_path, dup_name, base_name) in enumerate(candidates):
            rel = os.path.relpath(dup, folder)
            try:
                if os.path.exists(base_path) and files_identical(dup, base_path):
                    os.remove(dup)
                    self._wlog(f"  🗑  Gelöscht   {rel}  (≙ {base_name})", "del")
                    deleted += 1
                else:
                    self._wlog(f"  📌  Behalten   {rel}  (unterschiedlich)", "keep")
                    kept += 1
            except Exception as e:
                self._wlog(f"  ⚠  FEHLER: {rel} – {e}", "warn")
                errors += 1

            pct = (i + 1) / total * 100
            self.root.after(0, self._set_bar, pct, i + 1, total)

        self._wlog("")
        self._wlog(
            f"{deleted} gelöscht  ·  {kept} behalten"
            + (f"  ·  {errors} Fehler" if errors else ""),
            "ok")
        self._wlog("=== Fertig ===", "head")
        self._done()

    def _wlog(self, msg, tag=None):
        self.root.after(0, self._append, msg, tag)

    def _append(self, msg, tag):
        self._log.configure(state=tk.NORMAL)
        ts = datetime.now().strftime("%H:%M:%S")
        self._log.insert(tk.END, f"[{ts}]  {msg}\n", tag or "")
        self._log.see(tk.END)
        self._log.configure(state=tk.DISABLED)

    def _set_bar(self, pct, cur, total):
        self._bar.delete("all")
        w = self._bar.winfo_width()
        if w > 0:
            self._bar.create_rectangle(0, 0, w * pct / 100, 5,
                                        fill=C["warning"], outline="")
        self._status.set(f"{cur} / {total}  ({pct:.0f} %)")

    def _done(self):
        def _d():
            self.running = False
            self._start_btn.configure(state=tk.NORMAL)
            self._status.set("Fertig")
        self.root.after(0, _d)


if __name__ == "__main__":
    root = tk.Tk()
    DedupCleanerApp(root)
    root.mainloop()
