#!/usr/bin/env python3
"""Empty Remover — Leere Unterordner rekursiv finden und löschen."""

import os, threading
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox

C = {
    "bg":      "#1A1A2E", "panel":  "#16213E", "card":   "#0F3460",
    "accent":  "#3498DB", "success":"#2ECC71", "warning":"#F39C12",
    "danger":  "#E74C3C", "text":   "#ECF0F1", "muted":  "#7F8C8D",
    "log_bg":  "#0D1117", "empty":  "#F0B27A",
}

IGNORE = {".DS_Store", "Thumbs.db", "desktop.ini"}

def btn(parent, text, cmd, color=None, **kw):
    bg = color or C["card"]
    return tk.Button(parent, text=text, command=cmd,
        bg=bg, fg=C["text"], activebackground=C["accent"],
        activeforeground=C["text"], disabledforeground=C["muted"],
        highlightbackground=bg, highlightthickness=0,
        relief=tk.FLAT, font=("Arial", 11, "bold"),
        cursor="hand2", padx=14, pady=8, bd=0, **kw)

def ignorable(d):
    try: return all(e in IGNORE for e in os.listdir(d))
    except OSError: return False

def purge_rmdir(d):
    for e in os.listdir(d):
        if e in IGNORE:
            try: os.remove(os.path.join(d, e))
            except OSError: pass
    os.rmdir(d)


class EmptyRemoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Empty Remover")
        self.root.geometry("640x540")
        self.root.minsize(540, 440)
        self.root.configure(bg=C["bg"])
        self.running = False
        self._build()

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["card"], height=60)
        hdr.pack(fill=tk.X); hdr.pack_propagate(False)
        tk.Label(hdr, text="🗑️  Empty Remover", font=("Arial", 20, "bold"),
                 bg=C["card"], fg=C["text"]).pack(side=tk.LEFT, padx=20, pady=12)
        tk.Label(hdr, text="Leere Unterordner rekursiv finden und löschen",
                 font=("Arial", 10), bg=C["card"], fg=C["muted"]).pack(side=tk.LEFT)

        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=14)

        # Ordner
        self._lbl(body, "ORDNER")
        frow = tk.Frame(body, bg=C["panel"], padx=12, pady=10)
        frow.pack(fill=tk.X, pady=(4, 10))
        self._folder_var = tk.StringVar()
        tk.Entry(frow, textvariable=self._folder_var, state="readonly",
                 readonlybackground=C["card"], fg=C["empty"],
                 relief=tk.FLAT, font=("Menlo", 10), bd=0
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0, 10))
        btn(frow, "📂  Wählen", self._pick, color=C["accent"]).pack(side=tk.RIGHT)

        # Info-Box
        info = tk.Frame(body, bg=C["panel"], padx=14, pady=12)
        info.pack(fill=tk.X, pady=(0, 10))
        tk.Label(info, text="Was wird gelöscht?", bg=C["panel"], fg=C["text"],
                 font=("Arial", 10, "bold")).pack(anchor=tk.W)
        tk.Label(info,
                 text="Unterordner ohne Inhalt (oder nur mit .DS_Store / Thumbs.db).\n"
                      "Mehrere Durchläufe: erst Kinder, dann Eltern.\n"
                      "Der Wurzelordner selbst wird nie gelöscht.",
                 bg=C["panel"], fg=C["muted"], font=("Arial", 10), justify=tk.LEFT
                 ).pack(anchor=tk.W, pady=(4, 0))

        # Statistik-Karten (live)
        stats_row = tk.Frame(body, bg=C["bg"])
        stats_row.pack(fill=tk.X, pady=(0, 10))
        self._stat_deleted = self._stat_card(stats_row, "Gelöscht", "0", C["danger"])
        self._stat_rounds  = self._stat_card(stats_row, "Durchläufe", "0", C["accent"])
        self._stat_errors  = self._stat_card(stats_row, "Fehler", "0", C["warning"])

        # Start + Progress
        self._start_btn = btn(body, "🗑️  Leere Ordner löschen", self._start, color=C["empty"])
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
        for tag, color in [("ok", C["success"]), ("del", C["danger"]),
                            ("head", C["accent"]), ("warn", C["warning"]),
                            ("dim", C["muted"])]:
            self._log.tag_config(tag, foreground=color)

    def _lbl(self, p, t):
        tk.Label(p, text=t, bg=C["bg"], fg=C["muted"],
                 font=("Arial", 9, "bold")).pack(anchor=tk.W)

    def _stat_card(self, parent, label, value, color):
        f = tk.Frame(parent, bg=C["panel"], padx=20, pady=10)
        f.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 8))
        v_lbl = tk.Label(f, text=value, bg=C["panel"], fg=color,
                          font=("Arial", 22, "bold"))
        v_lbl.pack()
        tk.Label(f, text=label, bg=C["panel"], fg=C["muted"],
                 font=("Arial", 9)).pack()
        return v_lbl

    def _pick(self):
        p = filedialog.askdirectory(title="Ordner wählen (leere Unterordner löschen)")
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
        self._stat_deleted.config(text="0")
        self._stat_rounds.config(text="0")
        self._stat_errors.config(text="0")
        self._status.set("Läuft …")
        threading.Thread(target=self._run, args=(folder,), daemon=True).start()

    def _run(self, folder):
        self._wlog(f"=== Empty Remover: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===", "head")
        self._wlog(f"Ordner: {folder}", "head")
        self._wlog("")

        deleted = errors = round_nr = 0
        norm = os.path.normpath(folder)

        while True:
            round_nr += 1
            round_del = 0
            self._wlog(f"Durchlauf {round_nr} …", "dim")

            all_dirs = [
                dp for dp, _, _ in os.walk(folder, topdown=False)
                if os.path.normpath(dp) != norm
            ]
            if not all_dirs:
                if round_nr == 1:
                    self._wlog("Keine Unterordner gefunden.", "ok")
                break

            for i, dp in enumerate(all_dirs):
                rel = os.path.relpath(dp, folder)
                try:
                    if os.path.isdir(dp) and ignorable(dp):
                        purge_rmdir(dp)
                        self._wlog(f"  🗑  {rel}", "del")
                        round_del += 1
                        deleted   += 1
                except OSError as e:
                    self._wlog(f"  ⚠  FEHLER: {rel} – {e}", "warn")
                    errors += 1

                pct = (i + 1) / len(all_dirs) * 100
                short = rel if len(rel) <= 50 else "…" + rel[-49:]
                self.root.after(0, self._set_bar, pct, round_nr, short)
                self.root.after(0, self._stat_deleted.config, {"text": str(deleted)})
                self.root.after(0, self._stat_rounds.config,  {"text": str(round_nr)})
                self.root.after(0, self._stat_errors.config,  {"text": str(errors)})

            if round_del == 0:
                break
            self._wlog(f"  → {round_del} Ordner in Durchlauf {round_nr} gelöscht", "ok")

        self._wlog("")
        self._wlog(
            f"{deleted} leere Ordner gelöscht  ·  {round_nr} Durchläufe"
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

    def _set_bar(self, pct, rnd, rel):
        self._bar.delete("all")
        w = self._bar.winfo_width()
        if w > 0:
            self._bar.create_rectangle(0, 0, w * pct / 100, 5,
                                        fill=C["empty"], outline="")
        self._status.set(f"Durchlauf {rnd}  ▸  {rel}")

    def _done(self):
        def _d():
            self.running = False
            self._start_btn.configure(state=tk.NORMAL)
            self._status.set("Fertig")
        self.root.after(0, _d)


if __name__ == "__main__":
    root = tk.Tk()
    EmptyRemoverApp(root)
    root.mainloop()
