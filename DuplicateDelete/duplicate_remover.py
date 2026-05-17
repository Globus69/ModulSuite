#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import hashlib
import os
from pathlib import Path
import threading
from collections import defaultdict
import time

class DuplicateFileRemover:
    def __init__(self, root):
        self.root = root
        self.root.title("Duplicate File Remover")
        self.root.geometry("750x550")

        self.scanning = False
        self.paused = False
        self.abort = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Initially not paused

        # Mode: 'single' or 'dual'
        self.mode = None
        self.primary_folder = None
        self.secondary_folder = None

        # Statistics
        self.stats = {
            'total_files': 0,
            'primary_files': 0,
            'secondary_files': 0,
            'duplicate_groups': 0,
            'files_deleted': 0,
            'space_freed': 0,
            'files_kept': 0,
            'user_decisions': 0,
            'errors': 0
        }

        # Mode selection frame
        mode_frame = tk.Frame(root)
        mode_frame.pack(pady=10)

        tk.Label(mode_frame, text="Mode:", font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=5)

        self.mode_var = tk.StringVar(value="single")
        tk.Radiobutton(mode_frame, text="Single Folder (find duplicates)",
                      variable=self.mode_var, value="single",
                      command=self.on_mode_change, font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(mode_frame, text="Primary/Secondary (clean secondary)",
                      variable=self.mode_var, value="dual",
                      command=self.on_mode_change, font=('Arial', 10)).pack(side=tk.LEFT, padx=10)

        # Folder selection frame
        self.folder_frame = tk.Frame(root)
        self.folder_frame.pack(pady=5)

        # Single mode button
        self.single_select_btn = tk.Button(self.folder_frame, text="Select Folder",
                                           command=self.select_single_folder,
                                           width=20, height=2, font=('Arial', 12, 'bold'))

        # Dual mode buttons
        self.dual_frame = tk.Frame(self.folder_frame)

        primary_frame = tk.Frame(self.dual_frame)
        primary_frame.pack(pady=3)
        tk.Label(primary_frame, text="Primary (Reference):",
                font=('Arial', 10, 'bold'), fg='blue', width=20).pack(side=tk.LEFT)
        self.primary_btn = tk.Button(primary_frame, text="Select Primary Folder",
                                     command=self.select_primary_folder,
                                     width=20, font=('Arial', 10))
        self.primary_btn.pack(side=tk.LEFT, padx=5)
        self.primary_label = tk.Label(primary_frame, text="", fg='blue', font=('Arial', 9))
        self.primary_label.pack(side=tk.LEFT, padx=5)

        secondary_frame = tk.Frame(self.dual_frame)
        secondary_frame.pack(pady=3)
        tk.Label(secondary_frame, text="Secondary (Clean):",
                font=('Arial', 10, 'bold'), fg='red', width=20).pack(side=tk.LEFT)
        self.secondary_btn = tk.Button(secondary_frame, text="Select Secondary Folder",
                                       command=self.select_secondary_folder,
                                       width=20, font=('Arial', 10))
        self.secondary_btn.pack(side=tk.LEFT, padx=5)
        self.secondary_label = tk.Label(secondary_frame, text="", fg='red', font=('Arial', 9))
        self.secondary_label.pack(side=tk.LEFT, padx=5)

        # Start button for dual mode
        self.start_btn = tk.Button(self.dual_frame, text="Start Scan",
                                   command=self.start_dual_scan,
                                   width=20, height=2, font=('Arial', 12, 'bold'),
                                   state=tk.DISABLED)
        self.start_btn.pack(pady=10)

        # Show single mode by default
        self.single_select_btn.pack()

        # Progress label
        self.progress_label = tk.Label(root, text="", wraplength=700, font=('Arial', 10))
        self.progress_label.pack(pady=5)

        # Log window
        log_frame = tk.Frame(root)
        log_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="Activity Log:", font=('Arial', 9, 'bold')).pack(anchor=tk.W)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=85,
                                                   font=('Courier', 9), state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Control buttons frame
        self.control_frame = tk.Frame(root)
        self.control_frame.pack(pady=5)

        self.pause_btn = tk.Button(self.control_frame, text="Pause", command=self.pause_scan,
                                    width=15, state=tk.DISABLED, font=('Arial', 10))
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        self.abort_btn = tk.Button(self.control_frame, text="Abort", command=self.abort_scan,
                                    width=15, state=tk.DISABLED, font=('Arial', 10))
        self.abort_btn.pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_label = tk.Label(root, text="Ready", fg="green", font=('Arial', 10, 'bold'))
        self.status_label.pack(pady=5)

    def on_mode_change(self):
        """Handle mode change between single and dual"""
        if self.scanning:
            messagebox.showwarning("Scanning", "Cannot change mode during scan.")
            return

        mode = self.mode_var.get()

        # Hide all folder selection widgets
        self.single_select_btn.pack_forget()
        self.dual_frame.pack_forget()

        # Show appropriate widgets for selected mode
        if mode == "single":
            self.single_select_btn.pack()
        else:  # dual
            self.dual_frame.pack()

        # Reset selections
        self.primary_folder = None
        self.secondary_folder = None
        self.primary_label.config(text="")
        self.secondary_label.config(text="")
        self.start_btn.config(state=tk.DISABLED)

    def select_primary_folder(self):
        """Select primary (reference) folder"""
        folder = filedialog.askdirectory(title="Select Primary Folder (Reference - Won't be Modified)")
        if folder:
            self.primary_folder = folder
            self.primary_label.config(text=f"✓ {Path(folder).name}")
            self.check_dual_ready()

    def select_secondary_folder(self):
        """Select secondary (to be cleaned) folder"""
        folder = filedialog.askdirectory(title="Select Secondary Folder (Will be Cleaned)")
        if folder:
            if self.primary_folder and folder == self.primary_folder:
                messagebox.showerror("Error", "Secondary folder must be different from Primary folder!")
                return
            # Check if folders overlap
            if self.primary_folder:
                primary_path = Path(self.primary_folder).resolve()
                secondary_path = Path(folder).resolve()
                if secondary_path.is_relative_to(primary_path) or primary_path.is_relative_to(secondary_path):
                    messagebox.showerror("Error", "Secondary folder cannot be inside Primary folder or vice versa!")
                    return
            self.secondary_folder = folder
            self.secondary_label.config(text=f"✓ {Path(folder).name}")
            self.check_dual_ready()

    def check_dual_ready(self):
        """Enable start button if both folders are selected"""
        if self.primary_folder and self.secondary_folder:
            self.start_btn.config(state=tk.NORMAL)
        else:
            self.start_btn.config(state=tk.DISABLED)

    def start_dual_scan(self):
        """Start dual folder scan"""
        if self.scanning:
            messagebox.showwarning("Scanning", "A scan is already in progress.")
            return

        if not self.primary_folder or not self.secondary_folder:
            messagebox.showerror("Error", "Please select both Primary and Secondary folders.")
            return

        # Validate folders exist
        if not os.path.exists(self.primary_folder):
            messagebox.showerror("Error", "Primary folder does not exist!")
            return
        if not os.path.exists(self.secondary_folder):
            messagebox.showerror("Error", "Secondary folder does not exist!")
            return

        # Reset statistics
        self.stats = {
            'total_files': 0,
            'primary_files': 0,
            'secondary_files': 0,
            'duplicate_groups': 0,
            'files_deleted': 0,
            'space_freed': 0,
            'files_kept': 0,
            'user_decisions': 0,
            'errors': 0
        }

        # Clear log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        self.log(f"Starting DUAL FOLDER scan", "info")
        self.log(f"PRIMARY (Reference): {self.primary_folder}", "info")
        self.log(f"SECONDARY (Clean):   {self.secondary_folder}", "warning")

        self.scanning = True
        self.paused = False
        self.abort = False
        self.primary_btn.config(state=tk.DISABLED)
        self.secondary_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.abort_btn.config(state=tk.NORMAL)

        thread = threading.Thread(target=self.scan_dual_folders, daemon=True)
        thread.start()

    def log(self, message, level="info"):
        """Add message to log window"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = time.strftime("%H:%M:%S")

        if level == "info":
            prefix = "ℹ️"
        elif level == "success":
            prefix = "✓"
        elif level == "warning":
            prefix = "⚠️"
        elif level == "error":
            prefix = "✗"
        elif level == "delete":
            prefix = "🗑️"
        elif level == "keep":
            prefix = "📌"
        else:
            prefix = "•"

        self.log_text.insert(tk.END, f"[{timestamp}] {prefix} {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

    def select_single_folder(self):
        """Select single folder for duplicate detection"""
        if self.scanning:
            messagebox.showwarning("Scanning", "A scan is already in progress.")
            return

        folder = filedialog.askdirectory(title="Select Folder to Scan for Duplicates")
        if folder:
            # Reset statistics
            self.stats = {
                'total_files': 0,
                'primary_files': 0,
                'secondary_files': 0,
                'duplicate_groups': 0,
                'files_deleted': 0,
                'space_freed': 0,
                'files_kept': 0,
                'user_decisions': 0,
                'errors': 0
            }

            # Clear log
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)

            self.log(f"Starting SINGLE FOLDER scan: {folder}", "info")

            self.scanning = True
            self.paused = False
            self.abort = False
            self.single_select_btn.config(state=tk.DISABLED)
            self.pause_btn.config(state=tk.NORMAL)
            self.abort_btn.config(state=tk.NORMAL)
            thread = threading.Thread(target=self.scan_folder, args=(folder,), daemon=True)
            thread.start()

    def pause_scan(self):
        if self.paused:
            self.paused = False
            self.pause_event.set()  # Signal threads to continue
            self.pause_btn.config(text="Pause")
            self.status_label.config(text="Scanning...", fg="green")
            self.log("Scan resumed", "info")
        else:
            self.paused = True
            self.pause_event.clear()  # Signal threads to pause
            self.pause_btn.config(text="Resume")
            self.status_label.config(text="Paused", fg="orange")
            self.log("Scan paused", "warning")

    def abort_scan(self):
        self.abort = True
        self.status_label.config(text="Aborting...", fg="red")
        self.log("Abort requested by user", "warning")

    def get_file_hash(self, filepath):
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.log(f"Error hashing {Path(filepath).name}: {str(e)}", "error")
            self.stats['errors'] += 1
            return None

    def filenames_similar(self, name1, name2):
        """Check if filenames differ only in last 2-3 characters before extension"""
        if name1 == name2:
            return False

        # Get stem (filename without extension) and extension
        stem1 = Path(name1).stem
        stem2 = Path(name2).stem
        ext1 = Path(name1).suffix
        ext2 = Path(name2).suffix

        # Extensions must match
        if ext1 != ext2:
            return False

        # Stems must be long enough (at least 6 chars) to avoid false positives
        min_length = 6

        # Check if stems differ only in the last 2 or 3 characters
        for suffix_len in [2, 3]:
            if len(stem1) >= min_length and len(stem2) >= min_length:
                if stem1[:-suffix_len] == stem2[:-suffix_len]:
                    return True
        return False

    def has_copy_numbering(self, filename):
        """Check if filename has copy numbering like (1), (2), etc."""
        import re
        return bool(re.search(r'\s*\(\d+\)$', Path(filename).stem))

    def ask_user_decision(self, file1, file2):
        """Show popup for user decision on similar filenames"""
        self.stats['user_decisions'] += 1
        self.log(f"User decision required: {Path(file1).name} vs {Path(file2).name}", "warning")

        decision = {"result": None}

        def on_delete():
            decision["result"] = "delete"
            dialog.destroy()

        def on_keep():
            decision["result"] = "keep"
            dialog.destroy()

        def on_cancel():
            decision["result"] = "cancel"
            dialog.destroy()

        dialog = tk.Toplevel(self.root)
        dialog.title("Similar Filenames Detected")
        dialog.geometry("600x250")
        dialog.transient(self.root)
        dialog.grab_set()

        msg = (f"These files have identical content but similar names:\n\n"
               f"Keep:   {Path(file1).name}\n"
               f"        {file1}\n\n"
               f"Delete: {Path(file2).name}\n"
               f"        {file2}\n\n"
               f"What should I do?")
        tk.Label(dialog, text=msg, wraplength=550, justify=tk.LEFT, font=('Arial', 9)).pack(pady=15)

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Delete Duplicate", command=on_delete,
                  width=15, font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Keep Both", command=on_keep,
                  width=15, font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=on_cancel,
                  width=15, font=('Arial', 10)).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(dialog)
        return decision["result"]

    def get_file_size(self, filepath):
        """Get file size in bytes"""
        try:
            return os.path.getsize(filepath)
        except:
            return 0

    def format_size(self, bytes):
        """Format bytes to human readable size"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"

    def scan_dual_folders(self):
        """Scan primary and secondary folders, delete duplicates only from secondary"""
        try:
            self.status_label.config(text="Scanning...", fg="green")

            # Phase 1: Collect files from primary folder
            self.log("Phase 1: Collecting PRIMARY folder files...", "info")
            primary_files = {}  # {filename: [(path, hash), ...]}

            for root, dirs, files in os.walk(self.primary_folder):
                if self.abort:
                    break
                for file in files:
                    if not file.startswith('.'):
                        filepath = os.path.join(root, file)
                        if file not in primary_files:
                            primary_files[file] = []
                        primary_files[file].append(filepath)

            if self.abort:
                self.update_ui("Scan aborted by user.", "ready")
                return

            self.stats['primary_files'] = sum(len(paths) for paths in primary_files.values())
            self.log(f"Found {self.stats['primary_files']} files in PRIMARY folder", "info")

            # Phase 2: Hash primary files
            self.log("Phase 2: Hashing PRIMARY files...", "info")
            primary_hashes = {}  # {filename: {hash: [paths]}}

            total_primary = self.stats['primary_files']
            idx = 0

            for filename, paths in primary_files.items():
                for filepath in paths:
                    while self.paused and not self.abort:
                        self.pause_event.wait(timeout=0.1)

                    if self.abort:
                        self.update_ui("Scan aborted by user.", "ready")
                        return

                    idx += 1
                    progress_pct = int(idx / total_primary * 100) if total_primary > 0 else 0
                    self.progress_label.config(
                        text=f"Hashing PRIMARY: {idx}/{total_primary} ({progress_pct}%) - {Path(filepath).name[:40]}"
                    )
                    self.root.update()

                    file_hash = self.get_file_hash(filepath)
                    if file_hash:
                        if filename not in primary_hashes:
                            primary_hashes[filename] = {}
                        if file_hash not in primary_hashes[filename]:
                            primary_hashes[filename][file_hash] = []
                        primary_hashes[filename][file_hash].append(filepath)

            # Phase 3: Collect and compare secondary files
            self.log("Phase 3: Scanning SECONDARY folder...", "info")

            for root, dirs, files in os.walk(self.secondary_folder):
                if self.abort:
                    break
                for file in files:
                    if not file.startswith('.'):
                        self.stats['secondary_files'] += 1

            self.log(f"Found {self.stats['secondary_files']} files in SECONDARY folder", "info")

            # Phase 4: Process secondary files
            self.log("Phase 4: Comparing SECONDARY files with PRIMARY...", "info")

            idx = 0
            for root, dirs, files in os.walk(self.secondary_folder):
                if self.abort:
                    break

                for file in files:
                    if file.startswith('.'):
                        continue

                    while self.paused and not self.abort:
                        self.pause_event.wait(timeout=0.1)

                    if self.abort:
                        break

                    idx += 1
                    secondary_path = os.path.join(root, file)

                    progress_pct = int(idx / self.stats['secondary_files'] * 100) if self.stats['secondary_files'] > 0 else 0
                    self.progress_label.config(
                        text=f"Checking SECONDARY: {idx}/{self.stats['secondary_files']} ({progress_pct}%) - {file[:40]}"
                    )
                    self.root.update()

                    # Check if filename exists in primary (MUST match name first)
                    if file in primary_hashes:
                        # Hash the secondary file
                        secondary_hash = self.get_file_hash(secondary_path)
                        if secondary_hash:
                            # Check if this hash exists in primary for this filename
                            if secondary_hash in primary_hashes[file]:
                                # Found duplicate! Delete from secondary
                                file_size = self.get_file_size(secondary_path)
                                try:
                                    os.remove(secondary_path)
                                    self.stats['files_deleted'] += 1
                                    self.stats['space_freed'] += file_size
                                    primary_ref = primary_hashes[file][secondary_hash][0]
                                    self.log(f"DELETE: {secondary_path}", "delete")
                                    self.log(f"  → Duplicate of PRIMARY: {primary_ref}", "info")
                                    self.log(f"  → Freed: {self.format_size(file_size)}", "success")
                                except Exception as e:
                                    self.log(f"ERROR deleting {file}: {str(e)}", "error")
                                    self.stats['errors'] += 1
                            else:
                                self.log(f"KEEP: {secondary_path} (same name, different content)", "keep")
                                self.stats['files_kept'] += 1
                    else:
                        # Filename not in primary - keep file
                        self.stats['files_kept'] += 1

            if self.abort:
                self.update_ui(f"Scan aborted. Deleted {self.stats['files_deleted']} files.", "ready")
                self.show_statistics_dual()
                return

            self.stats['total_files'] = self.stats['primary_files'] + self.stats['secondary_files']

            self.log("\n" + "="*60, "info")
            self.log("Dual folder scan completed successfully!", "success")
            self.log(f"PRIMARY folder is UNCHANGED (protected)", "success")
            self.log(f"SECONDARY folder cleaned of {self.stats['files_deleted']} duplicates", "success")
            self.update_ui("Dual scan complete!", "ready")
            self.show_statistics_dual()

        except Exception as e:
            self.log(f"CRITICAL ERROR: {str(e)}", "error")
            self.stats['errors'] += 1
            self.update_ui(f"Error: {str(e)}", "error")
            self.show_statistics_dual()

    def scan_folder(self, folder):
        """Original single folder scan"""
        try:
            self.status_label.config(text="Scanning...", fg="green")
            self.log("Phase 1: Collecting files...", "info")

            # Collect all files
            all_files = []
            for root, dirs, files in os.walk(folder):
                if self.abort:
                    break
                for file in files:
                    if not file.startswith('.'):
                        all_files.append(os.path.join(root, file))

            if self.abort:
                self.update_ui("Scan aborted by user.", "ready")
                return

            self.stats['total_files'] = len(all_files)
            self.log(f"Found {self.stats['total_files']} files to analyze", "info")

            # Calculate hashes
            self.log("Phase 2: Calculating file hashes (SHA-256)...", "info")
            hash_map = defaultdict(list)
            total = len(all_files)

            for idx, filepath in enumerate(all_files):
                while self.paused and not self.abort:
                    self.pause_event.wait(timeout=0.1)

                if self.abort:
                    self.update_ui("Scan aborted by user.", "ready")
                    return

                progress_pct = int((idx + 1) / total * 100)
                self.progress_label.config(
                    text=f"Hashing: {idx + 1}/{total} ({progress_pct}%) - {Path(filepath).name[:50]}"
                )
                self.root.update()

                file_hash = self.get_file_hash(filepath)
                if file_hash:
                    hash_map[file_hash].append(filepath)

            # Find duplicates
            duplicate_groups = {h: files for h, files in hash_map.items() if len(files) > 1}
            self.stats['duplicate_groups'] = len(duplicate_groups)

            if self.stats['duplicate_groups'] == 0:
                self.log("No duplicate files found!", "success")
                self.update_ui("Scan complete. No duplicates found.", "ready")
                self.show_statistics()
                return

            self.log(f"Found {self.stats['duplicate_groups']} groups of duplicate files", "warning")
            self.log("Phase 3: Processing duplicates...", "info")

            # Handle duplicates
            for file_hash, files in duplicate_groups.items():
                if self.abort:
                    self.update_ui(f"Scan aborted. Deleted {self.stats['files_deleted']} files.", "ready")
                    self.show_statistics()
                    return

                while self.paused and not self.abort:
                    self.pause_event.wait(timeout=0.1)

                self.log(f"\nProcessing duplicate group ({len(files)} identical files):", "info")

                # Sort files: prefer files without copy numbering
                files_no_numbering = [f for f in files if not self.has_copy_numbering(f)]
                files_with_numbering = [f for f in files if self.has_copy_numbering(f)]

                # Keep one file without numbering if available, otherwise keep first file
                if files_no_numbering:
                    keep_file = files_no_numbering[0]
                    to_check = files_no_numbering[1:] + files_with_numbering
                else:
                    keep_file = files[0]
                    to_check = files[1:]

                self.log(f"  KEEP: {keep_file}", "keep")
                self.stats['files_kept'] += 1

                for dup_file in to_check:
                    if self.abort:
                        break

                    file_size = self.get_file_size(dup_file)

                    # Check if filenames are similar (differ only in last 2-3 chars)
                    if self.filenames_similar(Path(keep_file).name, Path(dup_file).name):
                        decision = self.ask_user_decision(keep_file, dup_file)
                        if decision == "delete":
                            try:
                                os.remove(dup_file)
                                self.stats['files_deleted'] += 1
                                self.stats['space_freed'] += file_size
                                self.log(f"  DELETE: {dup_file} ({self.format_size(file_size)})", "delete")
                            except Exception as e:
                                self.log(f"  ERROR deleting {Path(dup_file).name}: {str(e)}", "error")
                                self.stats['errors'] += 1
                        elif decision == "keep":
                            self.log(f"  KEEP BOTH: {dup_file} (user choice)", "keep")
                            self.stats['files_kept'] += 1
                        elif decision == "cancel":
                            self.log(f"  SKIP: {dup_file} (user cancelled)", "warning")
                    else:
                        # Auto-delete if names are not similar
                        try:
                            os.remove(dup_file)
                            self.stats['files_deleted'] += 1
                            self.stats['space_freed'] += file_size
                            self.log(f"  DELETE: {dup_file} ({self.format_size(file_size)})", "delete")
                        except Exception as e:
                            self.log(f"  ERROR deleting {Path(dup_file).name}: {str(e)}", "error")
                            self.stats['errors'] += 1

            self.log("\n" + "="*60, "info")
            self.log("Scan completed successfully!", "success")
            self.update_ui("Scan complete!", "ready")
            self.show_statistics()

        except Exception as e:
            self.log(f"CRITICAL ERROR: {str(e)}", "error")
            self.stats['errors'] += 1
            self.update_ui(f"Error: {str(e)}", "error")
            self.show_statistics()

    def show_statistics(self):
        """Show final statistics for single folder mode"""
        stats_msg = (
            f"📊 SCAN STATISTICS 📊\n\n"
            f"Mode:                     Single Folder\n"
            f"Total files scanned:      {self.stats['total_files']}\n"
            f"Duplicate groups found:   {self.stats['duplicate_groups']}\n"
            f"Files deleted:            {self.stats['files_deleted']}\n"
            f"Files kept:               {self.stats['files_kept']}\n"
            f"Space freed:              {self.format_size(self.stats['space_freed'])}\n"
            f"User decisions required:  {self.stats['user_decisions']}\n"
            f"Errors encountered:       {self.stats['errors']}\n"
        )

        self.log("\n" + stats_msg, "info")

        stats_window = tk.Toplevel(self.root)
        stats_window.title("Scan Statistics")
        stats_window.geometry("450x280")
        stats_window.transient(self.root)

        tk.Label(stats_window, text=stats_msg, font=('Courier', 11),
                 justify=tk.LEFT, padx=20, pady=20).pack()

        tk.Button(stats_window, text="OK", command=stats_window.destroy,
                  width=15, font=('Arial', 10)).pack(pady=10)

    def show_statistics_dual(self):
        """Show final statistics for dual folder mode"""
        stats_msg = (
            f"📊 SCAN STATISTICS 📊\n\n"
            f"Mode:                     Primary/Secondary\n"
            f"Primary files (protected): {self.stats['primary_files']}\n"
            f"Secondary files (scanned): {self.stats['secondary_files']}\n"
            f"Files deleted:            {self.stats['files_deleted']}\n"
            f"Files kept in secondary:  {self.stats['files_kept']}\n"
            f"Space freed:              {self.format_size(self.stats['space_freed'])}\n"
            f"Errors encountered:       {self.stats['errors']}\n"
        )

        self.log("\n" + stats_msg, "info")

        stats_window = tk.Toplevel(self.root)
        stats_window.title("Dual Scan Statistics")
        stats_window.geometry("450x280")
        stats_window.transient(self.root)

        tk.Label(stats_window, text=stats_msg, font=('Courier', 11),
                 justify=tk.LEFT, padx=20, pady=20).pack()

        tk.Button(stats_window, text="OK", command=stats_window.destroy,
                  width=15, font=('Arial', 10)).pack(pady=10)

    def update_ui(self, message, state):
        """Update UI after scan completion"""
        self.progress_label.config(text=message)
        if state == "ready":
            self.status_label.config(text="Ready", fg="green")
        elif state == "error":
            self.status_label.config(text="Error", fg="red")

        self.scanning = False

        # Re-enable mode-specific buttons
        mode = self.mode_var.get()
        if mode == "single":
            self.single_select_btn.config(state=tk.NORMAL)
        else:
            self.primary_btn.config(state=tk.NORMAL)
            self.secondary_btn.config(state=tk.NORMAL)
            self.check_dual_ready()

        self.pause_btn.config(state=tk.DISABLED, text="Pause")
        self.abort_btn.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = DuplicateFileRemover(root)
    root.mainloop()
