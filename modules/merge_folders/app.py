#!/usr/bin/env python3
"""Merge Folders — Mehrere Quellordner in einen Zielordner zusammenführen."""

import difflib, os, queue, shutil, threading
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

CHUNK_SIZE = 64 * 1024

C = {
    "bg":      "#1A1A2E", "panel":  "#16213E", "card":   "#0F3460",
    "accent":  "#3498DB", "success":"#2ECC71", "warning":"#F39C12",
    "danger":  "#E74C3C", "text":   "#ECF0F1", "muted":  "#7F8C8D",
    "log_bg":  "#0D1117", "target": "#5DADE2", "source": "#A9CCE3",
}


# ── Hilfsfunktionen ──────────────────────────────────────────────────────────

def name_similarity(a, b):
    if not a and not b: return 1.0
    if not a or not b:  return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()

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


class _Aborted(Exception): pass


# ── App ──────────────────────────────────────────────────────────────────────

class MergeFoldersApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Merge Folders")
        self.root.geometry("780x640")
        self.root.minsize(680, 560)
        self.root.configure(bg=C["bg"])

        self.sources = []
        self.running = False
        self._req_q  = queue.Queue()
        self._res_q  = queue.Queue()
        self._sim    = tk.IntVar(value=100)

        self._build()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["card"], height=60)
        hdr.pack(fill=tk.X); hdr.pack_propagate(False)
        tk.Label(hdr, text="📦  Merge Folders", font=("Arial", 20, "bold"),
                 bg=C["card"], fg=C["text"]).pack(side=tk.LEFT, padx=20, pady=12)
        tk.Label(hdr, text="Quellordner → Zielordner  ·  Duplikate bitgenau erkennen",
                 font=("Arial", 10), bg=C["card"], fg=C["muted"]).pack(side=tk.LEFT)

        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=14)

        # Zielordner
        self._label(body, "ZIELORDNER")
        trow = tk.Frame(body, bg=C["panel"], padx=12, pady=10)
        trow.pack(fill=tk.X, pady=(4, 10))
        self._target_var = tk.StringVar()
        tk.Entry(trow, textvariable=self._target_var, state="readonly",
                 readonlybackground=C["card"], fg=C["target"],
                 relief=tk.FLAT, font=("Menlo", 10), bd=0
                 ).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(0,10))
        btn(trow, "📂  Wählen", self._pick_target, color=C["accent"]).pack(side=tk.RIGHT)

        # Quellordner
        self._label(body, "QUELLORDNER  (mind. 1)")
        sframe = tk.Frame(body, bg=C["panel"], padx=12, pady=10)
        sframe.pack(fill=tk.X, pady=(4, 10))

        lbox_wrap = tk.Frame(sframe, bg=C["panel"])
        lbox_wrap.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._lbox = tk.Listbox(lbox_wrap, height=5, bg=C["log_bg"], fg=C["source"],
                                selectbackground=C["card"], font=("Menlo", 10),
                                relief=tk.FLAT, bd=0)
        sb = tk.Scrollbar(lbox_wrap, orient=tk.VERTICAL, command=self._lbox.yview, bg=C["panel"])
        self._lbox.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._lbox.pack(fill=tk.BOTH, expand=True)

        bcol = tk.Frame(sframe, bg=C["panel"])
        bcol.pack(side=tk.RIGHT, padx=(10, 0))
        btn(bcol, "+  Hinzufügen", self._add_source, color=C["success"]).pack(fill=tk.X, pady=(0, 6))
        btn(bcol, "−  Entfernen",  self._del_source, color=C["danger"]).pack(fill=tk.X)

        # Ähnlichkeits-Slider
        self._label(body, "ORDNER-ÄHNLICHKEIT")
        sslide = tk.Frame(body, bg=C["panel"], padx=12, pady=10)
        sslide.pack(fill=tk.X, pady=(4, 10))
        self._sim_lbl = tk.Label(sslide, text="100 %  — nur exakt gleiche Ordnernamen",
                                  bg=C["panel"], fg=C["text"], font=("Arial", 11, "bold"))
        self._sim_lbl.pack(anchor=tk.W)
        tk.Scale(sslide, from_=0, to=100, orient=tk.HORIZONTAL, variable=self._sim,
                 command=self._on_sim, bg=C["panel"], fg=C["text"],
                 troughcolor=C["card"], activebackground=C["accent"],
                 highlightthickness=0, showvalue=False, sliderlength=20,
                 tickinterval=25).pack(fill=tk.X)
        tk.Label(sslide, text="← mehr Dialoge bei Ähnlichkeit          sicherer →",
                 bg=C["panel"], fg=C["muted"], font=("Arial", 9)).pack(anchor=tk.W)

        # Start + Progress
        self._start_btn = btn(body, "▶  Zusammenführen starten", self._start,
                               color=C["success"])
        self._start_btn.pack(fill=tk.X, pady=(0, 6))

        self._bar_canvas = tk.Canvas(body, height=5, bg=C["panel"], highlightthickness=0)
        self._bar_canvas.pack(fill=tk.X, pady=(0, 2))
        self._status_var = tk.StringVar(value="Bereit")
        tk.Label(body, textvariable=self._status_var, bg=C["bg"],
                 fg=C["muted"], font=("Arial", 9), anchor=tk.W).pack(anchor=tk.W)

        # Log
        self._label(body, "LOG")
        logwrap = tk.Frame(body, bg=C["panel"])
        logwrap.pack(fill=tk.BOTH, expand=True, pady=(4, 0))
        self._log = tk.Text(logwrap, bg=C["log_bg"], fg="#58A6FF",
                             font=("Menlo", 10), relief=tk.FLAT,
                             padx=8, pady=6, state=tk.DISABLED)
        lsb = tk.Scrollbar(logwrap, orient=tk.VERTICAL, command=self._log.yview, bg=C["panel"])
        self._log.configure(yscrollcommand=lsb.set)
        lsb.pack(side=tk.RIGHT, fill=tk.Y)
        self._log.pack(fill=tk.BOTH, expand=True)
        for tag, color in [("ok", C["success"]), ("dup", C["danger"]),
                            ("move", C["source"]), ("head", C["accent"]),
                            ("warn", C["warning"]), ("dim", C["muted"])]:
            self._log.tag_config(tag, foreground=color)

    def _label(self, parent, text):
        tk.Label(parent, text=text, bg=C["bg"], fg=C["muted"],
                 font=("Arial", 9, "bold")).pack(anchor=tk.W)

    # ── Callbacks ────────────────────────────────────────────────────────────

    def _on_sim(self, val):
        iv = int(float(val))
        hint = "nur exakt gleiche Ordnernamen" if iv == 100 else \
               "Dialog bei Ähnlichkeit" if iv >= 70 else "viele Dialoge"
        self._sim_lbl.config(text=f"{iv} %  — {hint}")

    def _pick_target(self):
        p = filedialog.askdirectory(title="Zielordner wählen")
        if p: self._target_var.set(p)

    def _add_source(self):
        p = filedialog.askdirectory(title="Quellordner hinzufügen")
        if p and p not in self.sources:
            self.sources.append(p)
            self._lbox.insert(tk.END, Path(p).name + "   " + p)

    def _del_source(self):
        sel = self._lbox.curselection()
        if sel:
            self.sources.pop(sel[0])
            self._lbox.delete(sel[0])

    # ── Merge starten ─────────────────────────────────────────────────────────

    def _start(self):
        target = self._target_var.get()
        if not target:
            messagebox.showwarning("Fehler", "Bitte Zielordner wählen.")
            return
        if not self.sources:
            messagebox.showwarning("Fehler", "Bitte mind. 1 Quellordner hinzufügen.")
            return
        if self.running: return

        for src in self.sources:
            if self._subpath(src, target):
                messagebox.showwarning("Fehler", f"Quellordner liegt im Zielordner:\n{src}")
                return
            if self._subpath(target, src):
                messagebox.showwarning("Fehler", f"Zielordner liegt im Quellordner:\n{src}")
                return

        self.running = True
        self._start_btn.configure(state=tk.DISABLED)
        self._log.configure(state=tk.NORMAL)
        self._log.delete("1.0", tk.END)
        self._log.configure(state=tk.DISABLED)
        self._status_var.set("Läuft …")
        self._schedule_dialog_poll()
        threading.Thread(target=self._run, args=(target, list(self.sources)), daemon=True).start()

    def _schedule_dialog_poll(self):
        if not self.running: return
        self.root.after(150, self._poll_dialog)

    def _poll_dialog(self):
        if not self.running: return
        try:
            req = self._req_q.get_nowait()
            if req[0] == "similar_folder":
                self._show_sim_dialog(req[1], req[2])
        except queue.Empty:
            pass
        self._schedule_dialog_poll()

    def _show_sim_dialog(self, current, found):
        ratio = name_similarity(current, found)
        dlg = tk.Toplevel(self.root)
        dlg.title("Ähnlicher Ordner gefunden")
        dlg.configure(bg=C["bg"])
        dlg.minsize(460, 0)
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.protocol("WM_DELETE_WINDOW", lambda: None)

        result = {"v": "skip"}

        tk.Label(dlg, text="Ähnlicher Ordner gefunden",
                 bg=C["bg"], fg=C["text"], font=("Arial", 13, "bold")).pack(pady=(18, 8))

        for label, val, color in [
            ("Quelle:", current, C["source"]),
            ("Gefunden:", found, C["target"]),
            ("Übereinstimmung:", f"{ratio*100:.1f} %",
             C["success"] if ratio >= .9 else C["warning"]),
        ]:
            row = tk.Frame(dlg, bg=C["panel"], padx=14, pady=6)
            row.pack(fill=tk.X, padx=18, pady=2)
            tk.Label(row, text=label, bg=C["panel"], fg=C["muted"],
                     font=("Arial", 10), width=16, anchor=tk.W).pack(side=tk.LEFT)
            tk.Label(row, text=val, bg=C["panel"], fg=color,
                     font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        brow = tk.Frame(dlg, bg=C["bg"])
        brow.pack(pady=16)
        for text, color, val in [
            ("✓  Zusammenführen", C["success"], "use_existing"),
            ("✕  Neuer Ordner",   C["warning"], "skip"),
            ("⏹  Abbrechen",     C["danger"],  "abort"),
        ]:
            tk.Button(brow, text=text, bg=color, fg=C["text"], relief=tk.FLAT,
                      font=("Arial", 11, "bold"), padx=12, pady=7, cursor="hand2",
                      command=lambda v=val: [result.__setitem__("v", v), dlg.destroy()]
                      ).pack(side=tk.LEFT, padx=5)

        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()  - dlg.winfo_width())  // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")
        self.root.wait_window(dlg)
        self._res_q.put(result["v"])

    # ── Worker-Thread ─────────────────────────────────────────────────────────

    @staticmethod
    def _subpath(child, parent):
        try:
            c, p = os.path.realpath(child), os.path.realpath(parent)
            return c == p or c.startswith(p + os.sep)
        except (OSError, ValueError):
            return False

    def _find_match(self, parent_dir, wanted):
        if not os.path.isdir(parent_dir): return None, None, 0.0
        best, ratio = None, 0.0
        for e in os.listdir(parent_dir):
            sub = os.path.join(parent_dir, e)
            if not os.path.isdir(sub): continue
            r = name_similarity(e, wanted)
            if r >= 1.0: return sub, sub, 1.0
            if r > ratio: ratio, best = r, sub
        return None, best, ratio

    def _resolve(self, target_root, rel_dir):
        norm = (rel_dir or "").strip().strip(os.sep)
        if not norm or norm == ".": return target_root
        cache = getattr(self, "_cache", {})
        if norm in cache: return cache[norm]
        cur = target_root
        pf  = ""
        sim = self._sim.get() / 100.0
        for seg in rel_dir.split(os.sep):
            if not seg: continue
            pf = os.path.join(pf, seg) if pf else seg
            if pf in cache: cur = cache[pf]; continue
            exact, similar, ratio = self._find_match(cur, seg)
            if exact:
                cur = exact; cache[pf] = cur; continue
            if similar and ratio >= sim and ratio < 1.0:
                self._req_q.put(("similar_folder", seg, os.path.basename(similar)))
                resp = self._res_q.get()
                if resp == "abort": raise _Aborted()
                if resp == "use_existing":
                    cur = similar; cache[pf] = cur; continue
            new = os.path.join(cur, seg)
            os.makedirs(new, exist_ok=True)
            cur = new; cache[pf] = cur
        self._cache = cache
        return cur

    def _merge_file(self, src, dest_dir, rel, stats):
        fname = os.path.basename(src)
        dest  = os.path.join(dest_dir, fname)
        if not os.path.exists(dest):
            os.makedirs(dest_dir, exist_ok=True)
            shutil.move(src, dest)
            stats["moved"] += 1
            self._wlog(f"  verschoben  →  {rel}", "move")
            return
        if files_identical(src, dest):
            os.remove(src)
            stats["dup"] += 1
            self._wlog(f"  Duplikat gelöscht  →  {rel}", "dup")
            return
        stem, ext = os.path.splitext(fname)
        n = 1
        while True:
            nd = os.path.join(dest_dir, f"{stem}_{n}{ext}")
            if not os.path.exists(nd):
                shutil.move(src, nd)
                stats["moved"] += 1
                self._wlog(f"  verschoben → {stem}_{n}{ext}  (Namenskollision)", "move")
                break
            if files_identical(src, nd):
                os.remove(src)
                stats["dup"] += 1
                self._wlog(f"  Duplikat (≙ {stem}_{n}{ext}) gelöscht", "dup")
                break
            n += 1

    _IGNORE = {".DS_Store", "Thumbs.db", "desktop.ini"}

    @classmethod
    def _ignorable(cls, d):
        try: return all(e in cls._IGNORE for e in os.listdir(d))
        except OSError: return False

    @classmethod
    def _purge_rmdir(cls, d):
        for e in os.listdir(d):
            if e in cls._IGNORE:
                try: os.remove(os.path.join(d, e))
                except OSError: pass
        os.rmdir(d)

    def _cleanup_up(self, dirpath, src_root):
        norm = os.path.normpath(src_root)
        while dirpath and os.path.normpath(dirpath) != norm:
            if not os.path.isdir(dirpath) or os.path.basename(dirpath) == "_Quelle": break
            try:
                if not self._ignorable(dirpath): break
                self._purge_rmdir(dirpath)
            except OSError: break
            dirpath = os.path.dirname(dirpath)

    def _run(self, target, sources):
        file_list = []
        for src in sources:
            if not os.path.isdir(src): continue
            for dp, _, fns in os.walk(src):
                if os.path.basename(dp) == "_Quelle": continue
                for fn in fns:
                    fp  = os.path.join(dp, fn)
                    rel = os.path.relpath(fp, src)
                    file_list.append((src, rel, fp))
        file_list.sort(key=lambda x: x[1].count(os.sep))

        total = len(file_list)
        if total == 0:
            self._wlog("Keine Dateien gefunden.", "warn")
            self._done(); return

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._wlog(f"=== Merge gestartet: {ts} ===", "head")
        self._wlog(f"Ziel: {target}  ·  Quellen: {len(sources)}  ·  Dateien: {total}", "head")
        self._wlog("")

        stats   = {"moved": 0, "dup": 0, "err": 0}
        self._cache = {}
        aborted = False

        for i, (src_root, rel, fp) in enumerate(file_list):
            try:
                dest_dir = self._resolve(target, os.path.dirname(rel))
                self._merge_file(fp, dest_dir, rel, stats)
                sd = os.path.dirname(fp)
                if os.path.isdir(sd): self._cleanup_up(sd, src_root)
            except _Aborted:
                aborted = True
                self._wlog("*** ABBRUCH ***", "warn"); break
            except Exception as e:
                stats["err"] += 1
                self._wlog(f"  FEHLER: {rel} – {e}", "warn")
            pct = (i + 1) / total * 100
            self.root.after(0, self._set_bar, pct, i + 1, total)

        empty = 0
        if not aborted:
            for src in sources:
                if not os.path.isdir(src): continue
                while True:
                    n = 0
                    for dp, _, _ in os.walk(src, topdown=False):
                        if os.path.basename(dp) == "_Quelle": continue
                        try:
                            if self._ignorable(dp):
                                self._purge_rmdir(dp); n += 1
                        except OSError: pass
                    empty += n
                    if n == 0: break

        summary = (
            f"{'Abgebrochen. Bis dahin: ' if aborted else ''}"
            f"{stats['moved']} verschoben  ·  {stats['dup']} Duplikate gelöscht"
            + (f"  ·  {empty} leere Ordner entfernt" if not aborted else "")
            + (f"  ·  {stats['err']} Fehler" if stats['err'] else "")
        )
        self._wlog("", "dim")
        self._wlog(summary, "ok" if not aborted else "warn")
        self._wlog("=== Fertig ===", "head")

        log_path = os.path.join(target, "merge_log.txt")
        try:
            with open(log_path, "w") as f:
                f.write(f"Merge {ts}\n{summary}\n")
            self._wlog(f"Log: {log_path}", "dim")
        except Exception: pass

        self._cache = {}
        self._done()

    def _wlog(self, msg, tag=None):
        self.root.after(0, self._append, msg, tag)

    def _append(self, msg, tag):
        self._log.configure(state=tk.NORMAL)
        ts   = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}]  {msg}\n"
        self._log.insert(tk.END, line, tag or "")
        self._log.see(tk.END)
        self._log.configure(state=tk.DISABLED)

    def _set_bar(self, pct, cur, total):
        self._bar_canvas.delete("all")
        w = self._bar_canvas.winfo_width()
        if w > 0:
            self._bar_canvas.create_rectangle(0, 0, w * pct / 100, 5,
                                               fill=C["success"], outline="")
        self._status_var.set(f"{cur} / {total}  ({pct:.0f} %)")

    def _done(self):
        def _d():
            self.running = False
            self._start_btn.configure(state=tk.NORMAL)
            self._status_var.set("Fertig")
        self.root.after(0, _d)


if __name__ == "__main__":
    root = tk.Tk()
    MergeFoldersApp(root)
    root.mainloop()
