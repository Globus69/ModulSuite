#!/usr/bin/env python3
"""File Merge - Zusammenführen mehrerer Quellordner in einen Zielordner.
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

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------
CHUNK_SIZE = 64 * 1024          # 64 KB Blöcke für bitweisen Vergleich
SIMILARITY_THRESHOLD = 1.00     # Mindest-Namensähnlichkeit (100 %) – nur exakt gleiche Namen zusammenführen
DEDUP_NAME_THRESHOLD = 1.00     # Mindest-Dateinamen-Ähnlichkeit (100 %) für Duplikat-Erkennung

class _MergeAbortedError(Exception):
    """Wird ausgelöst, wenn der Benutzer im Ähnlichkeits-Dialog 'Abbruch' wählt."""

# ---------------------------------------------------------------------------
# Hilfsfunktionen (rein, zustandslos)
# ---------------------------------------------------------------------------


def name_similarity(name_a, name_b):
    """Liefert Namensähnlichkeit im Bereich [0, 1] via difflib.SequenceMatcher."""
    if not name_a and not name_b:
        return 1.0
    if not name_a or not name_b:
        return 0.0
    return difflib.SequenceMatcher(None, name_a, name_b).ratio()


def files_identical(path_a, path_b):
    """Bitweiser Vergleich zweier Dateien (64 KB Chunks).
    Schneller Abbruch bei unterschiedlicher Größe."""
    try:
        if os.path.getsize(path_a) != os.path.getsize(path_b):
            return False
        with open(path_a, 'rb') as fa, open(path_b, 'rb') as fb:
            while True:
                chunk_a = fa.read(CHUNK_SIZE)
                chunk_b = fb.read(CHUNK_SIZE)
                if chunk_a != chunk_b:
                    return False
                if not chunk_a:
                    return True
    except OSError:
        return False


class FileMergeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Merge")
        self.root.minsize(650, 550)

        self.source_folders = []
        self.is_running = False
        # Queues für modalen Dialog (Worker → Main-Thread) bei Namens-Ähnlichkeit
        self.merge_request_queue = queue.Queue()
        self.merge_response_queue = queue.Queue()

        self._build_gui()

    def _build_gui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        # --- Zielordner ---
        ttk.Label(main, text="Zielordner:", font=("", 12, "bold")).pack(anchor=tk.W)
        target_frame = ttk.Frame(main)
        target_frame.pack(fill=tk.X, pady=(2, 10))

        self.target_var = tk.StringVar()
        tk.Entry(
            target_frame, textvariable=self.target_var, state="readonly",
            readonlybackground="#A8D0E6", fg="#000000", relief="sunken", bd=2,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(target_frame, text="Auswählen…", command=self._select_target).pack(
            side=tk.RIGHT, padx=(6, 0)
        )

        # --- Quellordner ---
        ttk.Label(main, text="Quellordner:", font=("", 12, "bold")).pack(anchor=tk.W)
        source_frame = ttk.Frame(main)
        source_frame.pack(fill=tk.X, pady=(2, 10))

        self.source_listbox = tk.Listbox(source_frame, height=6, selectmode=tk.SINGLE)
        self.source_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(
            source_frame, orient=tk.VERTICAL, command=self.source_listbox.yview
        )
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.source_listbox.configure(yscrollcommand=scrollbar.set)

        btn_frame = ttk.Frame(source_frame)
        btn_frame.pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btn_frame, text="+", width=3, command=self._add_source).pack(
            pady=(0, 4)
        )
        ttk.Button(btn_frame, text="-", width=3, command=self._remove_source).pack()

        # --- Toleranz-Regler ---
        ttk.Label(main, text="Ordner-Ähnlichkeit:", font=("", 11, "bold")).pack(anchor=tk.W)
        tol_frame = tk.Frame(main)
        tol_frame.pack(fill=tk.X, pady=(2, 10))

        self.threshold_var = tk.IntVar(value=int(SIMILARITY_THRESHOLD * 100))

        self.threshold_label = tk.Label(
            tol_frame, text=f"Schwellenwert: {self.threshold_var.get()} %",
            font=("", 11), anchor=tk.W,
        )
        self.threshold_label.pack(fill=tk.X)

        self.threshold_scale = tk.Scale(
            tol_frame, from_=0, to=100, orient=tk.HORIZONTAL,
            variable=self.threshold_var, command=self._on_threshold_change,
            length=300, sliderlength=20, tickinterval=25,
            showvalue=False, font=("", 9),
        )
        self.threshold_scale.pack(fill=tk.X)

        tk.Label(
            tol_frame,
            text="← mehr Dialoge                    weniger Dialoge →",
            font=("", 9), fg="gray",
        ).pack(fill=tk.X)

        # --- Zusammenführen ---
        ttk.Label(main, text="Zusammenführen:", font=("", 11, "bold")).pack(anchor=tk.W)
        self.start_btn = ttk.Button(
            main, text="Zusammenführen starten", command=self._start_merge,
        )
        self.start_btn.pack(fill=tk.X, pady=(2, 2))

        self.merge_progress_var = tk.DoubleVar()
        ttk.Progressbar(main, variable=self.merge_progress_var, maximum=100).pack(
            fill=tk.X, pady=(0, 2)
        )
        self.merge_status_var = tk.StringVar(value="Bereit")
        ttk.Label(main, textvariable=self.merge_status_var).pack(anchor=tk.W, pady=(0, 8))

        # --- Duplikate bereinigen ---
        ttk.Label(main, text="Duplikate bereinigen:", font=("", 11, "bold")).pack(anchor=tk.W)

        # --- Toleranz-Regler Dateinamen ---
        dedup_tol_frame = tk.Frame(main)
        dedup_tol_frame.pack(fill=tk.X, pady=(2, 10))

        self.dedup_threshold_var = tk.IntVar(value=int(DEDUP_NAME_THRESHOLD * 100))

        self.dedup_threshold_label = tk.Label(
            dedup_tol_frame, text=f"Dateinamen-Toleranz: {self.dedup_threshold_var.get()} %",
            font=("", 11), anchor=tk.W,
        )
        self.dedup_threshold_label.pack(fill=tk.X)

        self.dedup_threshold_scale = tk.Scale(
            dedup_tol_frame, from_=0, to=100, orient=tk.HORIZONTAL,
            variable=self.dedup_threshold_var, command=self._on_dedup_threshold_change,
            length=300, sliderlength=20, tickinterval=25,
            showvalue=False, font=("", 9),
        )
        self.dedup_threshold_scale.pack(fill=tk.X)

        tk.Label(
            dedup_tol_frame,
            text="← mehr Treffer                     weniger Treffer →",
            font=("", 9), fg="gray",
        ).pack(fill=tk.X)

        self.dedup_btn = ttk.Button(
            main, text="Duplikate bereinigen", command=self._start_dedup,
        )
        self.dedup_btn.pack(fill=tk.X, pady=(2, 2))

        self.dedup_progress_var = tk.DoubleVar()
        ttk.Progressbar(main, variable=self.dedup_progress_var, maximum=100).pack(
            fill=tk.X, pady=(0, 2)
        )
        self.dedup_status_var = tk.StringVar(value="Bereit")
        ttk.Label(main, textvariable=self.dedup_status_var).pack(anchor=tk.W, pady=(0, 8))

        # --- Leere Ordner löschen ---
        ttk.Label(main, text="Leere Ordner löschen:", font=("", 11, "bold")).pack(anchor=tk.W)
        empty_folder_frame = ttk.Frame(main)
        empty_folder_frame.pack(fill=tk.X, pady=(2, 2))

        self.empty_dir_var = tk.StringVar()
        tk.Entry(
            empty_folder_frame, textvariable=self.empty_dir_var, state="readonly",
            readonlybackground="#C8A200", fg="#000000", relief="sunken", bd=2,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(
            empty_folder_frame, text="Auswählen…", command=self._select_empty_dir
        ).pack(side=tk.RIGHT, padx=(6, 0))

        self.empty_btn = ttk.Button(
            main, text="Leere Ordner löschen", command=self._start_remove_empty,
        )
        self.empty_btn.pack(fill=tk.X, pady=(2, 2))

        self.empty_progress_var = tk.DoubleVar()
        ttk.Progressbar(main, variable=self.empty_progress_var, maximum=100).pack(
            fill=tk.X, pady=(0, 2)
        )
        self.empty_status_var = tk.StringVar(value="Bereit")
        ttk.Label(main, textvariable=self.empty_status_var).pack(anchor=tk.W, pady=(0, 8))

        # --- Log-Bereich ---
        ttk.Label(main, text="Log:", font=("", 12, "bold")).pack(anchor=tk.W)
        log_frame = ttk.Frame(main)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, height=10, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        log_scroll = ttk.Scrollbar(
            log_frame, orient=tk.VERTICAL, command=self.log_text.yview
        )
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=log_scroll.set)

    # --- Toleranz-Callback ---

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

    # --- Ordner-Auswahl ---

    def _select_target(self):
        path = filedialog.askdirectory(title="Zielordner auswählen")
        if path:
            self.target_var.set(path)

    def _add_source(self):
        path = filedialog.askdirectory(title="Quellordner hinzufügen")
        if path and path not in self.source_folders:
            self.source_folders.append(path)
            self.source_listbox.insert(tk.END, path)

    def _remove_source(self):
        sel = self.source_listbox.curselection()
        if sel:
            idx = sel[0]
            self.source_folders.pop(idx)
            self.source_listbox.delete(idx)

    # --- Log ---

    def _log(self, message):
        self.root.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    # --- Merge ---

    @staticmethod
    def _is_subpath(child, parent):
        """Prüft ob *child* ein Unterordner von *parent* ist (oder identisch)."""
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

        # Schutz: Quellordner darf nicht innerhalb des Zielordners liegen
        for src in self.source_folders:
            if self._is_subpath(src, target):
                messagebox.showwarning(
                    "Fehler",
                    f"Der Quellordner\n'{src}'\nliegt innerhalb des Zielordners.\n\n"
                    "Bitte einen Quellordner außerhalb des Zielordners wählen."
                )
                return
            if self._is_subpath(target, src):
                messagebox.showwarning(
                    "Fehler",
                    f"Der Zielordner\n'{target}'\nliegt innerhalb des Quellordners\n'{src}'.\n\n"
                    "Bitte Ziel- und Quellordner korrigieren."
                )
                return

        self.is_running = True
        self.start_btn.configure(state=tk.DISABLED)
        self.dedup_btn.configure(state=tk.DISABLED)
        self.merge_progress_var.set(0)
        self.merge_status_var.set("Läuft...")

        # Log-Text leeren
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

        # Dialog-Polling starten (Main-Thread prüft periodisch auf Anfragen des Workers)
        self._schedule_merge_dialog_poll()
        thread = threading.Thread(
            target=self._run_merge, args=(target, list(self.source_folders)), daemon=True
        )
        thread.start()

    def _schedule_merge_dialog_poll(self):
        """Plant periodische Prüfung auf Dialog-Anfragen (nur während Merge läuft)."""
        if not self.is_running:
            return
        self.root.after(150, self._poll_merge_dialog)

    def _poll_merge_dialog(self):
        """Prüft, ob der Worker eine Benutzerentscheidung braucht; zeigt ggf. modales Popup."""
        if not self.is_running:
            return
        try:
            req = self.merge_request_queue.get_nowait()
        except queue.Empty:
            self._schedule_merge_dialog_poll()
            return
        # req = ('similar_folder', aktueller_ordnername, gefundener_ordnername)
        if req[0] == "similar_folder":
            _, current_name, found_name = req
            self._show_similar_folder_dialog(current_name, found_name)
        self._schedule_merge_dialog_poll()

    def _show_similar_folder_dialog(self, current_name, found_name):
        """Modales Popup: Ordner ähnlich, aber nicht identisch.

        Bietet drei Optionen:
        - Ja      → vorhandenen Ordner nutzen  (merge_response = 'use_existing')
        - Nein    → neuen Ordner anlegen        (merge_response = 'skip')
        - Abbruch → gesamten Merge sofort beenden (merge_response = 'abort')

        Toleranz wird im Hauptfenster über den Slider eingestellt.
        """
        dlg = tk.Toplevel(self.root)
        dlg.title("Ordner-Ähnlichkeit")
        dlg.minsize(450, 0)
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.protocol("WM_DELETE_WINDOW", lambda: None)  # X-Button deaktivieren

        result = {"value": "skip"}

        # --- Aktuelle Ähnlichkeit berechnen ---
        ratio = name_similarity(current_name, found_name)

        # --- Nachricht ---
        msg = (
            f"Quellordner:  '{current_name}'\n"
            f"Ähnlicher Zielordner:  '{found_name}'\n"
            f"Übereinstimmung:  {ratio * 100:.1f} %\n\n"
            "Soll der vorhandene Ordner genutzt werden?\n\n"
            f"• Ja      → Dateien in '{found_name}' zusammenführen\n"
            f"• Nein    → Neuen Ordner '{current_name}' anlegen\n"
            "• Abbruch → Merge-Vorgang sofort beenden"
        )
        ttk.Label(dlg, text=msg, justify=tk.LEFT, padding=16).pack()

        # --- Buttons ---
        btn_frame = ttk.Frame(dlg, padding=(16, 8, 16, 16))
        btn_frame.pack(fill=tk.X)

        def _choose(val):
            result["value"] = val
            dlg.destroy()

        ttk.Button(btn_frame, text="Ja", width=10,
                   command=lambda: _choose("use_existing")).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="Nein", width=10,
                   command=lambda: _choose("skip")).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(btn_frame, text="Abbruch", width=10,
                   command=lambda: _choose("abort")).pack(side=tk.RIGHT)

        # Dialog zentrieren
        dlg.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dlg.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{x}+{y}")

        self.root.wait_window(dlg)
        self.merge_response_queue.put(result["value"])

    # ------------------------------------------------------------------
    # Schritt 3: Ordner-Matching (70 % Namensähnlichkeit)
    # ------------------------------------------------------------------

    def _find_best_matching_folder(self, parent_dir, wanted_name):
        """Sucht in *parent_dir* den Unterordner mit der höchsten Namensähnlichkeit.

        Rückgabe: (exact_path | None, best_similar_path | None, ratio).
        - exact_path  ≠ None  → exakter Treffer (100 %)
        - best_similar_path   → bester Treffer > 0 % (kann None sein)

        Die Filterung nach SIMILARITY_THRESHOLD erfolgt erst beim Aufrufer,
        damit der Benutzer den Schwellenwert im Dialog anpassen kann.
        """
        if not os.path.isdir(parent_dir):
            return None, None, 0.0

        best_path = None
        best_ratio = 0.0

        for entry in os.listdir(parent_dir):
            sub_path = os.path.join(parent_dir, entry)
            if not os.path.isdir(sub_path):
                continue
            r = name_similarity(entry, wanted_name)
            # Exakter Treffer → sofort zurückgeben
            if r >= 1.0:
                return sub_path, sub_path, 1.0
            if r > best_ratio:
                best_ratio = r
                best_path = sub_path

        return None, best_path, best_ratio

    # ------------------------------------------------------------------
    # Schritt 3–4: Relativen Ordnerpfad im Ziel auflösen (pro Ebene)
    # ------------------------------------------------------------------

    def _resolve_target_dir(self, target_root, relative_dir_path):
        """Löst *relative_dir_path* (leer = Wurzel) Ebene für Ebene im Ziel auf.

        Pro Hierarchie-Ebene:
        - 100 % Match         → vorhandenen Ordner nutzen
        - 70–99 % Match       → modales Popup (Benutzerentscheidung), dann neuen Ordner
        - < 70 % / kein Match → neuen Ordner mit Originalnamen anlegen

        *_resolve_cache* verhindert, dass derselbe Pfad mehrfach den Dialog auslöst.
        """
        norm = (relative_dir_path or "").strip().strip(os.sep)
        if not norm or norm == ".":
            return target_root

        cache = getattr(self, "_resolve_cache", None)
        if cache is not None and norm in cache:
            return cache[norm]

        current = target_root
        segments = [p for p in relative_dir_path.split(os.sep) if p]
        path_so_far = ""

        for seg in segments:
            path_so_far = os.path.join(path_so_far, seg) if path_so_far else seg
            # Bereits aufgelöst?
            if cache is not None and path_so_far in cache:
                current = cache[path_so_far]
                continue

            exact_path, similar_path, ratio = self._find_best_matching_folder(current, seg)

            # 100 % → vorhandenen Ordner nutzen
            if exact_path:
                current = exact_path
                if cache is not None:
                    cache[path_so_far] = current
                continue

            # Ähnlichkeit >= Schwellenwert und nicht exakt → Dialog anzeigen
            # Der Benutzer kann im Dialog den Schwellenwert anpassen
            if similar_path and ratio >= SIMILARITY_THRESHOLD and ratio < 1.0:
                self.merge_request_queue.put(
                    ("similar_folder", seg, os.path.basename(similar_path))
                )
                # Worker wartet hier, bis Main-Thread geantwortet hat
                response = self.merge_response_queue.get()
                if response == "abort":
                    raise _MergeAbortedError("Vom Benutzer abgebrochen")
                if response == "use_existing":
                    current = similar_path
                    if cache is not None:
                        cache[path_so_far] = current
                    continue
                # "skip" → neuen Ordner mit Originalnamen anlegen (siehe unten)

            # < 70 % oder "skip" → neuen Ordner anlegen
            new_dir = os.path.join(current, seg)
            os.makedirs(new_dir, exist_ok=True)
            current = new_dir
            if cache is not None:
                cache[path_so_far] = current

        return current

    # ------------------------------------------------------------------
    # Schritt 5a–b: Einzeldatei in den Zielordner mergen
    # ------------------------------------------------------------------

    def _merge_single_file(self, src_file, dest_dir, rel_path, log_lines, stats):
        """Verarbeitet eine einzelne Datei:

        1. Zielpfad berechnen (dest_dir + Dateiname).
        2. Zieldatei existiert UND ist bitgenau identisch → Quelle löschen.
        3. Zieldatei existiert, aber Inhalt verschieden → nummerierte Kopie
           (name_1.ext, name_2.ext …) anlegen, bitgenauen Check gegen
           jede nummerierte Variante.
        4. Zieldatei existiert nicht → verschieben.
        5. Bei Fehler: NIE löschen, Fehler loggen, weiter mit nächster Datei.
        """
        fname = os.path.basename(src_file)
        dest_file = os.path.join(dest_dir, fname)

        # --- Fall A: Ziel existiert noch nicht → einfach verschieben ---
        if not os.path.exists(dest_file):
            os.makedirs(dest_dir, exist_ok=True)
            shutil.move(src_file, dest_file)
            stats["moved"] += 1
            action = "verschoben"
            self._log(f"  {rel_path}: {action}")
            log_lines.append(f"  {rel_path}: {action}")
            return

        # --- Fall B: Ziel existiert und ist bitgenau identisch → Quelle löschen ---
        if files_identical(src_file, dest_file):
            os.remove(src_file)
            stats["deleted_dup"] += 1
            action = "Duplikat → Quelle gelöscht"
            self._log(f"  {rel_path}: {action}")
            log_lines.append(f"  {rel_path}: {action}")
            return

        # --- Fall C: Namenskollision, aber Inhalt verschieden ---
        #     Nummerierte Variante suchen / anlegen
        stem, ext = os.path.splitext(fname)
        counter = 1
        while True:
            new_name = f"{stem}_{counter}{ext}"
            new_dest = os.path.join(dest_dir, new_name)
            if not os.path.exists(new_dest):
                # Platz frei → verschieben
                shutil.move(src_file, new_dest)
                stats["moved"] += 1
                action = f"verschoben → {new_name}"
                break
            if files_identical(src_file, new_dest):
                # Identisch mit nummerierter Variante → Quelle löschen
                os.remove(src_file)
                stats["deleted_dup"] += 1
                action = f"Duplikat (≙ {new_name}) → Quelle gelöscht"
                break
            counter += 1

        self._log(f"  {rel_path}: {action}")
        log_lines.append(f"  {rel_path}: {action}")

    # ------------------------------------------------------------------
    # Schritt 5c: Leere Quellordner nach oben entfernen
    # ------------------------------------------------------------------

    # OS-Metadateien, die beim Leer-Check ignoriert werden
    _IGNORABLE_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}

    @classmethod
    def _is_dir_only_ignorable(cls, dirpath):
        """True wenn *dirpath* nur ignorierbare Metadateien enthält (keine echten Dateien/Ordner)."""
        try:
            entries = os.listdir(dirpath)
        except OSError:
            return False
        for entry in entries:
            if entry in cls._IGNORABLE_FILES:
                continue
            return False  # echte Datei oder Unterordner → nicht leer
        return True

    @classmethod
    def _purge_ignorable_and_rmdir(cls, dirpath):
        """Entfernt ignorierbare Metadateien und löscht den Ordner."""
        for entry in os.listdir(dirpath):
            if entry in cls._IGNORABLE_FILES:
                try:
                    os.remove(os.path.join(dirpath, entry))
                except OSError:
                    pass
        os.rmdir(dirpath)

    @classmethod
    def _remove_empty_dirs_upward(cls, dirpath, source_root):
        """Löscht *dirpath* und Elternordner aufwärts, solange leer und
        unterhalb *source_root*.  '_Quelle'-Ordner bleiben geschützt.
        Ignoriert OS-Metadateien (.DS_Store etc.)."""
        norm_root = os.path.normpath(source_root)
        while dirpath and os.path.normpath(dirpath) != norm_root:
            if not os.path.isdir(dirpath):
                break
            if os.path.basename(dirpath) == "_Quelle":
                break
            try:
                if not cls._is_dir_only_ignorable(dirpath):
                    break          # echte Inhalte → abbrechen
                cls._purge_ignorable_and_rmdir(dirpath)
            except OSError:
                break
            dirpath = os.path.dirname(dirpath)

    # ------------------------------------------------------------------
    # Hauptablauf: _run_merge  (Schritte 2–7)
    # ------------------------------------------------------------------

    def _run_merge(self, target, sources):
        """Kompletter Merge-Ablauf (läuft im Worker-Thread).

        Schritt 1: Benutzer hat Quell- und Zielordner in der GUI gewählt (erledigt).
        Schritt 2: Rekursiv alle Quellordner durchlaufen; relativen Pfad aufbauen.
        Schritt 3: Pro Ordnerebene: 70 % Namensähnlichkeit prüfen → Match nutzen.
        Schritt 4: Bei Unklarheit (70–99 %) → modales Popup; Benutzer entscheidet.
        Schritt 5: Pro Datei: bitgenau vergleichen → Duplikat löschen ODER verschieben.
                   Danach leeren Quellordner aufwärts entfernen.
        Schritt 6: Alle verbleibenden leeren Ordner in Quellen löschen; Abschlussmeldung.
        Schritt 7: Fehlerbehandlung – bei Fehler nie löschen, loggen, weiter.
        """

        # ============================================================
        # Schritt 2: Alle Dateien mit relativem Pfad sammeln
        # ============================================================
        file_list = []   # [(source_root, rel_path, abs_src_file), …]
        for src in sources:
            if not os.path.isdir(src):
                continue
            for dirpath, _, filenames in os.walk(src):
                # _Quelle-Ordner niemals anfassen
                if os.path.basename(dirpath) == "_Quelle":
                    continue
                for fname in filenames:
                    src_file = os.path.join(dirpath, fname)
                    rel = os.path.relpath(src_file, src)
                    file_list.append((src, rel, src_file))

        # Flachste Pfade zuerst → Ordnerstruktur im Ziel wird korrekt aufgebaut
        file_list.sort(key=lambda x: x[1].count(os.sep))

        total = len(file_list)
        if total == 0:
            self._log("Keine Dateien in den Quellordnern gefunden.")
            self._finish_task(self.merge_status_var)
            return

        # --- Log-Header ---
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._log(f"=== Bereinigung gestartet: {ts} ===")
        self._log(f"Zielordner: {target}")
        self._log(f"Quellordner: {len(sources)}")
        self._log(f"Dateien gesamt: {total}")
        self._log("")

        log_lines = [
            "=== File Merge Log ===",
            f"Datum: {ts}",
            f"Zielordner: {target}",
            "",
        ]
        stats = {"moved": 0, "deleted_dup": 0, "errors": 0}

        # Cache für aufgelöste relative Ordnerpfade (verhindert mehrfache Dialoge)
        self._resolve_cache = {}

        # ============================================================
        # Schritt 5: Jede Datei verarbeiten
        # ============================================================
        aborted = False
        for i, (source_root, rel_path, src_file) in enumerate(file_list):
            rel_dir = os.path.dirname(rel_path)

            try:
                # ---- Schritt 3–4: Zielordner auflösen ----
                dest_dir = self._resolve_target_dir(target, rel_dir)

                # ---- Schritt 5a–b: Datei mergen ----
                self._merge_single_file(src_file, dest_dir, rel_path, log_lines, stats)

                # ---- Schritt 5c: Leere Quellordner aufräumen ----
                src_dir = os.path.dirname(src_file)
                if os.path.isdir(src_dir):
                    self._remove_empty_dirs_upward(src_dir, source_root)

            except _MergeAbortedError:
                aborted = True
                self._log("")
                self._log("*** ABBRUCH durch Benutzer ***")
                self._log("Quell- und Zielordner bleiben ab hier unverändert.")
                log_lines.append("")
                log_lines.append("*** ABBRUCH durch Benutzer ***")
                log_lines.append("Quell- und Zielordner bleiben ab hier unverändert.")
                break

            except Exception as e:
                # Schritt 7: Fehler loggen, Datei bleibt in Quelle (nie löschen!)
                stats["errors"] += 1
                self._log(f"  FEHLER: {rel_path} – {e}")
                log_lines.append(f"  FEHLER: {rel_path} – {e}")

            # Fortschrittsanzeige aktualisieren
            progress = ((i + 1) / total) * 100
            self.root.after(0, self._update_merge_progress, progress, i + 1, total)

        # ============================================================
        # Schritt 6: Verbleibende leere Quellordner löschen
        #            (inkl. .DS_Store-only Ordner, mehrere Durchläufe)
        #            → Bei Abbruch: komplett überspringen!
        # ============================================================
        empty_removed = 0
        if not aborted:
            self._log("")
            self._log("Räume verbleibende leere Quellordner auf …")
            for src in sources:
                if not os.path.isdir(src):
                    continue
                # Mehrere Durchläufe, bis nichts mehr gelöscht wird
                while True:
                    round_removed = 0
                    for dirpath, _, _ in os.walk(src, topdown=False):
                        if os.path.basename(dirpath) == "_Quelle":
                            continue
                        try:
                            if self._is_dir_only_ignorable(dirpath):
                                self._purge_ignorable_and_rmdir(dirpath)
                                round_removed += 1
                        except OSError:
                            pass
                    empty_removed += round_removed
                    if round_removed == 0:
                        break
            self._log(f"  {empty_removed} leere Ordner entfernt")

        # --- Abschlussmeldung ---
        if aborted:
            summary = (
                f"ABGEBROCHEN. Bis zum Abbruch: {stats['moved']} Dateien verschoben, "
                f"{stats['deleted_dup']} Duplikate gelöscht. "
                f"Verbleibende Dateien sind unverändert."
            )
        else:
            summary = (
                f"Bereinigung abgeschlossen. {stats['moved']} Dateien verschoben, "
                f"{stats['deleted_dup']} Duplikate gelöscht, "
                f"{empty_removed} leere Ordner entfernt."
            )
        if stats["errors"]:
            summary += f"  ({stats['errors']} Fehler – Details oben)"
        self._log("")
        self._log(summary)
        self._log("\n=== " + ("Abgebrochen" if aborted else "Fertig") + " ===")
        log_lines.append("")
        log_lines.append(summary)

        # --- Log-Datei schreiben ---
        log_path = os.path.join(target, "merge_log.txt")
        try:
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("\n".join(log_lines))
            self._log(f"\nLog gespeichert: {log_path}")
        except Exception as e:
            self._log(f"\nFEHLER beim Speichern der Logdatei: {e}")

        # Cache aufräumen
        self._resolve_cache = None
        self._finish_task(self.merge_status_var)

    def _update_merge_progress(self, percent, current, total):
        self.merge_progress_var.set(percent)
        self.merge_status_var.set(f"{current} / {total} Dateien ({percent:.0f}%)")

    def _update_dedup_progress(self, percent, current, total):
        self.dedup_progress_var.set(percent)
        self.dedup_status_var.set(f"{current} / {total} Dateien ({percent:.0f}%)")

    def _finish_task(self, status_var):
        def _done():
            self.is_running = False
            self.start_btn.configure(state=tk.NORMAL)
            self.dedup_btn.configure(state=tk.NORMAL)
            status_var.set("Fertig")

        self.root.after(0, _done)

    # --- Duplikate bereinigen ---

    # Regex: name_1.ext, name_2.ext, subdir/name_123.ext etc.
    _DEDUP_RE = re.compile(r'^(.+)_(\d+)(\.[^.]+)$')

    def _start_dedup(self):
        target = self.target_var.get()
        if not target:
            messagebox.showwarning("Fehler", "Bitte einen Zielordner auswählen.")
            return
        if not os.path.isdir(target):
            messagebox.showwarning("Fehler", "Der Zielordner existiert nicht.")
            return
        if self.is_running:
            return

        self.is_running = True
        self.start_btn.configure(state=tk.DISABLED)
        self.dedup_btn.configure(state=tk.DISABLED)
        self.dedup_progress_var.set(0)
        self.dedup_status_var.set("Läuft...")

        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

        thread = threading.Thread(
            target=self._run_dedup, args=(target,), daemon=True
        )
        thread.start()

    def _run_dedup(self, target):
        self._log(f"=== Duplikate bereinigen: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
        self._log(f"Zielordner: {target}")
        self._log("")

        # Alle Dateien mit Nummerierungsmuster sammeln
        candidates = []
        for dirpath, _, filenames in os.walk(target):
            for fname in filenames:
                m = self._DEDUP_RE.match(fname)
                if m:
                    full_path = os.path.join(dirpath, fname)
                    base_name = m.group(1) + m.group(3)  # name.ext
                    base_path = os.path.join(dirpath, base_name)
                    candidates.append((full_path, base_path, fname, base_name))

        total = len(candidates)
        if total == 0:
            self._log("Keine nummerierten Duplikate gefunden.")
            self._finish_task(self.dedup_status_var)
            return

        self._log(f"Gefunden: {total} nummerierte Dateien zum Prüfen")
        self._log("")

        deleted = 0
        kept = 0
        errors = 0

        for i, (dup_path, base_path, dup_name, base_name) in enumerate(candidates):
            rel_dup = os.path.relpath(dup_path, target)

            try:
                if os.path.exists(base_path) and files_identical(dup_path, base_path):
                    os.remove(dup_path)
                    self._log(f"  Gelöscht: {rel_dup} (identisch mit {base_name})")
                    deleted += 1
                else:
                    self._log(f"  Behalten: {rel_dup} (unterschiedlich)")
                    kept += 1
            except Exception as e:
                self._log(f"  FEHLER: {rel_dup} - {e}")
                errors += 1

            progress = ((i + 1) / total) * 100
            self.root.after(0, self._update_dedup_progress, progress, i + 1, total)

        self._log("")
        self._log(
            f"Zusammenfassung: {deleted} gelöscht, "
            f"{kept} behalten (unterschiedlich), "
            f"{errors} Fehler"
        )
        self._log("\n=== Fertig ===")
        self._finish_task(self.dedup_status_var)

    # --- Leere Ordner löschen ---

    def _select_empty_dir(self):
        path = filedialog.askdirectory(title="Ordner auswählen (leere Unterordner löschen)")
        if path:
            self.empty_dir_var.set(path)

    def _start_remove_empty(self):
        target = self.empty_dir_var.get()
        if not target:
            messagebox.showwarning("Fehler", "Bitte einen Ordner auswählen.")
            return
        if not os.path.isdir(target):
            messagebox.showwarning("Fehler", "Der gewählte Ordner existiert nicht.")
            return
        if self.is_running:
            return

        self.is_running = True
        self.start_btn.configure(state=tk.DISABLED)
        self.dedup_btn.configure(state=tk.DISABLED)
        self.empty_btn.configure(state=tk.DISABLED)
        self.empty_progress_var.set(0)
        self.empty_status_var.set("Läuft...")

        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

        thread = threading.Thread(
            target=self._run_remove_empty, args=(target,), daemon=True
        )
        thread.start()

    def _run_remove_empty(self, target):
        self._log(f"=== Leere Ordner löschen: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
        self._log(f"Ordner: {target}")
        self._log("")

        deleted = 0
        errors = 0
        round_nr = 0

        # Mehrere Durchläufe: nach Löschen von Kindern können Eltern leer werden
        while True:
            round_nr += 1
            round_deleted = 0

            # Scan-Phase anzeigen
            self.root.after(0, self._set_empty_status,
                            f"Durchlauf {round_nr}: Scanne Ordnerstruktur …")
            self._log(f"Durchlauf {round_nr}: Scanne Ordnerstruktur …")

            # Bottom-up alle Unterordner sammeln (frisch pro Durchlauf)
            all_dirs = []
            norm_target = os.path.normpath(target)
            for dirpath, dirnames, _ in os.walk(target, topdown=False):
                # Den Wurzelordner selbst nie löschen
                if os.path.normpath(dirpath) == norm_target:
                    continue
                all_dirs.append(dirpath)

            total = len(all_dirs)
            if total == 0:
                if round_nr == 1:
                    self._log("Keine Unterordner gefunden.")
                break

            self._log(f"  {total} Ordner zu prüfen")

            for i, dirpath in enumerate(all_dirs):
                rel = os.path.relpath(dirpath, target)
                try:
                    if os.path.isdir(dirpath) and self._is_dir_only_ignorable(dirpath):
                        self._purge_ignorable_and_rmdir(dirpath)
                        self._log(f"  Gelöscht: {rel}")
                        round_deleted += 1
                        deleted += 1
                except OSError as e:
                    self._log(f"  FEHLER: {rel} – {e}")
                    errors += 1

                progress = ((i + 1) / total) * 100
                # Kurzer Ordnername für Statuszeile (max. 40 Zeichen)
                short_rel = rel if len(rel) <= 40 else "…" + rel[-39:]
                self.root.after(0, self._update_empty_progress,
                                progress, i + 1, total, round_nr, short_rel)

            if round_deleted == 0:
                break
            self._log(f"  → Durchlauf {round_nr}: {round_deleted} gelöscht")
            self._log("")

        self._log("")
        self._log(f"Zusammenfassung: {deleted} leere Ordner gelöscht, {errors} Fehler")
        self._log("\n=== Fertig ===")
        self._finish_remove_empty()

    def _set_empty_status(self, text):
        self.empty_status_var.set(text)

    def _update_empty_progress(self, percent, current, total, round_nr, rel_name):
        self.empty_progress_var.set(percent)
        self.empty_status_var.set(
            f"Durchlauf {round_nr}: {current}/{total} ({percent:.0f}%)  ▸ {rel_name}"
        )

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
