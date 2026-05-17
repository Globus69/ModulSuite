#!/usr/bin/env python3
"""Create test data for Primary/Secondary folder mode"""

import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).parent
PRIMARY_DIR = BASE_DIR / "TEST_PRIMARY"
SECONDARY_DIR = BASE_DIR / "TEST_SECONDARY"

# Clean directories
if PRIMARY_DIR.exists():
    shutil.rmtree(PRIMARY_DIR)
if SECONDARY_DIR.exists():
    shutil.rmtree(SECONDARY_DIR)

PRIMARY_DIR.mkdir()
SECONDARY_DIR.mkdir()

print("Creating test data for PRIMARY/SECONDARY mode...")
print("="*60)

# Test Case 1: Exact duplicates (same name, same content)
# Expected: Delete from SECONDARY
content1 = b"This is document 1 - identical in both folders"
(PRIMARY_DIR / "document1.txt").write_bytes(content1)
(SECONDARY_DIR / "document1.txt").write_bytes(content1)
print("✓ Test 1: Exact duplicate (same name, same content)")
print("  Expected: DELETE from SECONDARY")

# Test Case 2: Same name, different content
# Expected: Keep in SECONDARY
content2a = b"Original version in PRIMARY"
content2b = b"Modified version in SECONDARY"
(PRIMARY_DIR / "document2.txt").write_bytes(content2a)
(SECONDARY_DIR / "document2.txt").write_bytes(content2b)
print("✓ Test 2: Same name, different content")
print("  Expected: KEEP in SECONDARY")

# Test Case 3: Multiple files with same name in PRIMARY
# Expected: Check against all PRIMARY versions
content3 = b"Photo content version A"
(PRIMARY_DIR / "photo.jpg").write_bytes(content3)
subdir1 = PRIMARY_DIR / "archive"
subdir1.mkdir()
(subdir1 / "photo.jpg").write_bytes(content3)  # Same name, nested
(SECONDARY_DIR / "photo.jpg").write_bytes(content3)
print("✓ Test 3: File in SECONDARY matches PRIMARY (nested)")
print("  Expected: DELETE from SECONDARY")

# Test Case 4: File only in SECONDARY
# Expected: Keep (no match in PRIMARY)
content4 = b"This file only exists in SECONDARY"
(SECONDARY_DIR / "unique_to_secondary.txt").write_bytes(content4)
print("✓ Test 4: File only in SECONDARY")
print("  Expected: KEEP (no match in PRIMARY)")

# Test Case 5: File only in PRIMARY
# Expected: Primary never touched
content5 = b"This file only exists in PRIMARY"
(PRIMARY_DIR / "unique_to_primary.txt").write_bytes(content5)
print("✓ Test 5: File only in PRIMARY")
print("  Expected: PRIMARY UNCHANGED")

# Test Case 6: Multiple duplicates in SECONDARY
# Expected: Only exact name match deleted
content6 = b"Backup file duplicated multiple times"
(PRIMARY_DIR / "backup.dat").write_bytes(content6)
(SECONDARY_DIR / "backup.dat").write_bytes(content6)
(SECONDARY_DIR / "backup (1).dat").write_bytes(content6)
(SECONDARY_DIR / "backup (2).dat").write_bytes(content6)
print("✓ Test 6: Multiple copies in SECONDARY")
print("  Expected: Only 'backup.dat' DELETED (name match)")

# Test Case 7: Nested folders in SECONDARY
# Expected: Works across nested structure
content7 = b"Nested folder test content"
(PRIMARY_DIR / "nested.txt").write_bytes(content7)
sec_nested = SECONDARY_DIR / "deep" / "folder"
sec_nested.mkdir(parents=True)
(sec_nested / "nested.txt").write_bytes(content7)
print("✓ Test 7: Nested folder in SECONDARY")
print("  Expected: DELETE from SECONDARY nested folder")

# Test Case 8: Large file (simulate)
content8 = b"A" * 1024 * 100  # 100KB
(PRIMARY_DIR / "large_file.bin").write_bytes(content8)
(SECONDARY_DIR / "large_file.bin").write_bytes(content8)
print("✓ Test 8: Large file (100KB)")
print("  Expected: DELETE from SECONDARY, show freed space")

# Test Case 9: Different name, same content (should NOT delete)
# Expected: Keep (name must match first)
content9 = b"Same content, different names"
(PRIMARY_DIR / "original_name.txt").write_bytes(content9)
(SECONDARY_DIR / "different_name.txt").write_bytes(content9)
print("✓ Test 9: Different names, same content")
print("  Expected: KEEP (name mismatch)")

# Test Case 10: Empty files
content10 = b""
(PRIMARY_DIR / "empty.txt").write_bytes(content10)
(SECONDARY_DIR / "empty.txt").write_bytes(content10)
print("✓ Test 10: Empty files")
print("  Expected: DELETE from SECONDARY")

print("\n" + "="*60)
print("Test data creation complete!")
print(f"PRIMARY folder:   {len(list(PRIMARY_DIR.rglob('*.*')))} files")
print(f"SECONDARY folder: {len(list(SECONDARY_DIR.rglob('*.*')))} files")
print("="*60)

print("\nEXPECTED RESULTS:")
print("-"*60)
print("Files to DELETE from SECONDARY:")
print("  - document1.txt (exact duplicate)")
print("  - photo.jpg (matches PRIMARY)")
print("  - backup.dat (exact name & content match)")
print("  - nested.txt (in deep/folder/)")
print("  - large_file.bin (100KB freed)")
print("  - empty.txt (empty duplicate)")
print("\nFiles to KEEP in SECONDARY:")
print("  - document2.txt (different content)")
print("  - unique_to_secondary.txt (not in PRIMARY)")
print("  - different_name.txt (name mismatch)")
print("  - backup (1).dat (name mismatch)")
print("  - backup (2).dat (name mismatch)")
print("\nPRIMARY folder: COMPLETELY UNCHANGED (protected)")
print("="*60)
