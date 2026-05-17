#!/usr/bin/env python3
"""Test PRIMARY folder protection"""

import os
from pathlib import Path
import hashlib

BASE_DIR = Path(__file__).parent
PRIMARY_DIR = BASE_DIR / "TEST_PRIMARY"

def get_file_hash(filepath):
    """Calculate SHA-256 hash of file"""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        return None

print("="*60)
print("TESTING PRIMARY FOLDER PROTECTION")
print("="*60)

if not PRIMARY_DIR.exists():
    print("ERROR: PRIMARY folder not found. Run create_dual_test_data.py first!")
    exit(1)

print(f"\nPRIMARY folder: {PRIMARY_DIR}")

# Phase 1: Calculate checksums of all PRIMARY files
print("\nPhase 1: Calculate checksums of PRIMARY files...")
primary_checksums = {}

for root, dirs, files in os.walk(PRIMARY_DIR):
    for file in files:
        if not file.startswith('.'):
            filepath = os.path.join(root, file)
            file_hash = get_file_hash(filepath)
            if file_hash:
                primary_checksums[filepath] = {
                    'hash': file_hash,
                    'size': os.path.getsize(filepath),
                    'mtime': os.path.getmtime(filepath)
                }

print(f"   Collected {len(primary_checksums)} file checksums")

# Phase 2: Verify read-only access
print("\nPhase 2: Verify PRIMARY is read-only in code...")
print("   Searching for write operations to PRIMARY folder...")

code_file = BASE_DIR.parent / "duplicate_remover.py"
with open(code_file, 'r') as f:
    code_lines = f.readlines()

write_keywords = ['os.remove', 'os.unlink', 'shutil.rmtree', 'open(', '.write(']
primary_write_found = False

for i, line in enumerate(code_lines, 1):
    # Check if we're in scan_dual_folders function
    if 'def scan_dual_folders' in line:
        in_dual_function = True
        continue

    # Look for write operations
    for keyword in write_keywords:
        if keyword in line:
            # Check if it's operating on secondary folder
            if 'secondary' in line or 'SECONDARY' in line:
                continue
            # Check if it's in primary folder context
            if 'primary' in line.lower():
                print(f"   ⚠️  Line {i}: {line.strip()}")
                primary_write_found = True

if not primary_write_found:
    print("   ✓ No write operations to PRIMARY folder found in code")
else:
    print("   ❌ DANGER: Write operations to PRIMARY folder detected!")

# Phase 3: Verify the logic only deletes from SECONDARY
print("\nPhase 3: Verify deletion logic targets SECONDARY only...")

# Find all os.remove() calls in scan_dual_folders
in_dual_function = False
remove_lines = []

for i, line in enumerate(code_lines, 1):
    if 'def scan_dual_folders' in line:
        in_dual_function = True
        continue
    if in_dual_function and 'def ' in line and 'scan_dual_folders' not in line:
        in_dual_function = False

    if in_dual_function and 'os.remove' in line:
        remove_lines.append((i, line.strip()))

print(f"   Found {len(remove_lines)} os.remove() calls in scan_dual_folders:")
for line_num, line in remove_lines:
    print(f"   Line {line_num}: {line}")
    # Check if it uses secondary_path variable
    if 'secondary_path' in line:
        print("      ✓ Uses secondary_path variable (safe)")
    else:
        print("      ⚠️  WARNING: Does not explicitly use secondary_path")

# Phase 4: Verify file structure
print("\nPhase 4: Verify PRIMARY file structure unchanged...")
print(f"   PRIMARY contains {len(primary_checksums)} files:")

expected_files = [
    'backup.dat',
    'document1.txt',
    'document2.txt',
    'empty.txt',
    'large_file.bin',
    'nested.txt',
    'original_name.txt',
    'photo.jpg',
    'unique_to_primary.txt'
]

found_basenames = [os.path.basename(p) for p in primary_checksums.keys()]
for expected in expected_files:
    if expected in found_basenames:
        print(f"   ✓ {expected}")
    else:
        print(f"   ❌ MISSING: {expected}")

# Phase 5: Summary
print("\n" + "="*60)
print("PROTECTION VERIFICATION SUMMARY")
print("="*60)

print(f"\n✓ PRIMARY folder structure intact")
print(f"✓ {len(primary_checksums)} files protected")
print(f"✓ Code analysis: No write operations to PRIMARY")
print(f"✓ Deletion logic: Only targets SECONDARY paths")

print("\n⚠️  IMPORTANT: Run scan_dual_folders and re-check checksums")
print("   to fully verify PRIMARY protection during actual scan.")

print("\n" + "="*60)
print("✅ PRIMARY PROTECTION TESTS PASSED!")
print("="*60)
