#!/usr/bin/env python3
"""Test the corrected dual mode implementation"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import duplicate_remover
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock tkinter before import
import unittest.mock as mock
sys.modules['tkinter'] = mock.MagicMock()
sys.modules['tkinter.filedialog'] = mock.MagicMock()
sys.modules['tkinter.messagebox'] = mock.MagicMock()
sys.modules['tkinter.scrolledtext'] = mock.MagicMock()

from duplicate_remover import DuplicateFileRemover
import hashlib
from collections import defaultdict

def get_file_hash(filepath):
    """Calculate SHA-256 hash of file"""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error hashing {filepath}: {e}")
        return None

def test_dual_mode_logic():
    """Test the dual mode hash comparison logic"""
    print("="*60)
    print("TESTING DUAL MODE HASH LOGIC")
    print("="*60)

    BASE_DIR = Path(__file__).parent
    PRIMARY_DIR = BASE_DIR / "TEST_PRIMARY"
    SECONDARY_DIR = BASE_DIR / "TEST_SECONDARY"

    if not PRIMARY_DIR.exists() or not SECONDARY_DIR.exists():
        print("ERROR: Test directories not found. Run create_dual_test_data.py first!")
        return False

    print(f"\nPrimary folder: {PRIMARY_DIR}")
    print(f"Secondary folder: {SECONDARY_DIR}")

    # Phase 1: Collect PRIMARY files
    print("\nPhase 1: Collecting PRIMARY files...")
    primary_files = {}
    for root, dirs, files in os.walk(PRIMARY_DIR):
        for file in files:
            if not file.startswith('.'):
                filepath = os.path.join(root, file)
                if file not in primary_files:
                    primary_files[file] = []
                primary_files[file].append(filepath)

    print(f"Found {sum(len(paths) for paths in primary_files.values())} files in PRIMARY")

    # Phase 2: Hash PRIMARY files
    print("\nPhase 2: Hashing PRIMARY files...")
    primary_hashes = {}

    for filename, paths in primary_files.items():
        for filepath in paths:
            file_hash = get_file_hash(filepath)
            if file_hash:
                if filename not in primary_hashes:
                    primary_hashes[filename] = {}
                if file_hash not in primary_hashes[filename]:
                    primary_hashes[filename][file_hash] = []
                primary_hashes[filename][file_hash].append(filepath)

    print(f"Hashed {len(primary_hashes)} unique filenames")

    # Phase 3: Check SECONDARY files
    print("\nPhase 3: Analyzing SECONDARY files...")

    to_delete = []
    to_keep = []

    for root, dirs, files in os.walk(SECONDARY_DIR):
        for file in files:
            if file.startswith('.'):
                continue

            secondary_path = os.path.join(root, file)

            # Check if FILENAME exists in PRIMARY (MUST match name first)
            if file in primary_hashes:
                secondary_hash = get_file_hash(secondary_path)
                if not secondary_hash:
                    continue

                # Check if this hash exists in primary for this filename
                if secondary_hash in primary_hashes[file]:
                    to_delete.append({
                        'path': secondary_path,
                        'name': file,
                        'hash': secondary_hash[:8],
                        'primary_ref': primary_hashes[file][secondary_hash][0]
                    })
                else:
                    # Same name, different content
                    to_keep.append({
                        'path': secondary_path,
                        'name': file,
                        'hash': secondary_hash[:8],
                        'reason': 'same name, different content'
                    })
            else:
                # Filename not in primary
                to_keep.append({
                    'path': secondary_path,
                    'name': file,
                    'hash': '',
                    'reason': 'name not in PRIMARY'
                })

    # Results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)

    print(f"\nFiles to DELETE from SECONDARY: {len(to_delete)}")
    for item in to_delete:
        print(f"  ✓ {item['name']}")
        print(f"    → Duplicate of: {item['primary_ref']}")

    print(f"\nFiles to KEEP in SECONDARY: {len(to_keep)}")
    for item in to_keep:
        reason = item.get('reason', '')
        if reason:
            print(f"  📌 {item['name']} ({reason})")
        else:
            print(f"  📌 {item['name']}")

    # Validation
    print("\n" + "="*60)
    print("VALIDATION")
    print("="*60)

    expected_delete = [
        'document1.txt',
        'photo.jpg',
        'backup.dat',
        'nested.txt',
        'large_file.bin',
        'empty.txt'
    ]

    expected_keep = [
        'document2.txt',
        'unique_to_secondary.txt',
        'different_name.txt',
        'backup (1).dat',
        'backup (2).dat'
    ]

    deleted_names = [item['name'] for item in to_delete]
    kept_names = [item['name'] for item in to_keep]

    errors = []

    for expected in expected_delete:
        if expected not in deleted_names:
            errors.append(f"ERROR: {expected} should be deleted but wasn't")

    for expected in expected_keep:
        if expected not in kept_names:
            errors.append(f"ERROR: {expected} should be kept but wasn't")

    for deleted in deleted_names:
        if deleted not in expected_delete:
            errors.append(f"ERROR: {deleted} was marked for deletion but shouldn't be")

    for kept in kept_names:
        if kept not in expected_keep:
            errors.append(f"ERROR: {kept} was kept but shouldn't be")

    if errors:
        print("\n❌ VALIDATION FAILED:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("\n✅ VALIDATION PASSED!")
        print("All files correctly identified for deletion/keeping.")
        return True

if __name__ == "__main__":
    success = test_dual_mode_logic()
    sys.exit(0 if success else 1)
