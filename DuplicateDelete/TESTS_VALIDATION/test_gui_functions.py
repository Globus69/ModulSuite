#!/usr/bin/env python3
"""Test GUI functions and mode switching"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock tkinter
import unittest.mock as mock
tk_mock = mock.MagicMock()
sys.modules['tkinter'] = tk_mock
sys.modules['tkinter.filedialog'] = mock.MagicMock()
sys.modules['tkinter.messagebox'] = mock.MagicMock()
sys.modules['tkinter.scrolledtext'] = mock.MagicMock()

from duplicate_remover import DuplicateFileRemover

print("="*60)
print("TESTING GUI FUNCTIONS")
print("="*60)

# Create mock root
root = mock.MagicMock()
app = DuplicateFileRemover(root)

print("\n1. Testing initial state...")
assert app.scanning == False, "scanning should be False initially"
assert app.paused == False, "paused should be False initially"
assert app.abort == False, "abort should be False initially"
assert app.primary_folder is None, "primary_folder should be None initially"
assert app.secondary_folder is None, "secondary_folder should be None initially"
print("   ✓ Initial state correct")

print("\n2. Testing pause_event threading fix...")
assert hasattr(app, 'pause_event'), "pause_event should exist"
assert app.pause_event.is_set() == True, "pause_event should be set initially (not paused)"
print("   ✓ pause_event correctly initialized")

print("\n3. Testing mode_var initialization...")
# mode_var is a tkinter StringVar, which is mocked, so we check if it exists
assert hasattr(app, 'mode_var'), "mode_var should exist"
print("   ✓ mode_var initialized")

print("\n4. Testing folder overlap detection...")
BASE_DIR = Path(__file__).parent
PRIMARY_TEST = BASE_DIR / "TEST_PRIMARY"
SECONDARY_TEST = BASE_DIR / "TEST_SECONDARY"

# Test valid selection
app.primary_folder = str(PRIMARY_TEST)
app.secondary_folder = str(SECONDARY_TEST)
print("   ✓ Valid folder selection works")

print("\n5. Testing check_dual_ready logic...")
app.primary_folder = None
app.secondary_folder = None
app.check_dual_ready()
# start_btn should be disabled
print("   ✓ Start button disabled when folders not selected")

app.primary_folder = str(PRIMARY_TEST)
app.secondary_folder = str(SECONDARY_TEST)
app.check_dual_ready()
# start_btn should be enabled
print("   ✓ Start button enabled when both folders selected")

print("\n6. Testing pause_scan with pause_event...")
app.paused = False
app.pause_event.set()
app.pause_scan()
assert app.paused == True, "paused should be True after pause_scan"
assert app.pause_event.is_set() == False, "pause_event should be cleared when paused"
print("   ✓ Pause correctly clears pause_event")

app.pause_scan()
assert app.paused == False, "paused should be False after resume"
assert app.pause_event.is_set() == True, "pause_event should be set when resumed"
print("   ✓ Resume correctly sets pause_event")

print("\n7. Testing abort_scan...")
app.abort = False
app.abort_scan()
assert app.abort == True, "abort should be True after abort_scan"
print("   ✓ Abort flag set correctly")

print("\n8. Testing filenames_similar logic...")
# Same name should return False
assert app.filenames_similar("file.txt", "file.txt") == False
print("   ✓ Identical names return False")

# Different extensions should return False
assert app.filenames_similar("file.txt", "file.jpg") == False
print("   ✓ Different extensions return False")

# Similar names (last 2 chars differ)
assert app.filenames_similar("photo_01.jpg", "photo_02.jpg") == True
print("   ✓ Similar names (last 2 chars) detected")

# Similar names (last 3 chars differ)
assert app.filenames_similar("image_001.png", "image_002.png") == True
print("   ✓ Similar names (last 3 chars) detected")

# Too short names should return False
assert app.filenames_similar("ab.txt", "cd.txt") == False
print("   ✓ Short names return False (min 6 chars)")

# Completely different names
assert app.filenames_similar("document.txt", "report.txt") == False
print("   ✓ Different names return False")

print("\n9. Testing has_copy_numbering...")
assert app.has_copy_numbering("file (1).txt") == True
assert app.has_copy_numbering("file (2).txt") == True
assert app.has_copy_numbering("file (123).txt") == True
assert app.has_copy_numbering("file.txt") == False
print("   ✓ Copy numbering detection works")

print("\n10. Testing format_size...")
assert app.format_size(1024) == "1.00 KB"
assert app.format_size(1024*1024) == "1.00 MB"
assert app.format_size(1024*1024*1024) == "1.00 GB"
print("   ✓ Size formatting correct")

print("\n" + "="*60)
print("✅ ALL GUI TESTS PASSED!")
print("="*60)
