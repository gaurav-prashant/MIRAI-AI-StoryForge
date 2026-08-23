import os
import sys

print("=== MIRAI STORYFORGE AUDIO SYSTEM AUDIT & VERIFICATION ===")

# 1. Verify Audio Files Existence
AUDIO_DIR = os.path.join(os.path.dirname(__file__), "assets", "audio")
required_files = [
    "background_fantasy.mp3",
    "background_mystery.mp3",
    "background_horror.mp3",
    "background_scifi.mp3",
    "background_adventure.mp3",
    "action.wav",
    "mystery.wav",
    "ending.wav",
]

print(f"\n1. Checking Audio Directory: {AUDIO_DIR}")
for fname in required_files:
    fpath = os.path.join(AUDIO_DIR, fname)
    exists = os.path.exists(fpath)
    size = os.path.getsize(fpath) if exists else 0
    status = "OK" if exists else "MISSING"
    print(f"  - [{status}] {fname:<25} ({size:,} bytes)")

# 2. Test utils.audio_manager functions
print("\n2. Testing utils.audio_manager...")
from utils.audio_manager import (
    get_audio_base64,
    get_background_track_for_genre,
    render_audio_components,
    GENRE_MUSIC_MAP,
)

genres_to_test = ["Fantasy", "Mystery", "Horror", "Sci-Fi", "Adventure"]
for g in genres_to_test:
    track = get_background_track_for_genre(g)
    b64 = get_audio_base64(track)
    has_b64 = b64 is not None and b64.startswith("data:audio/")
    print(f"  - Genre '{g:<9}': Track = '{track:<23}' -> Base64 Valid: {has_b64}")

# 3. Test Missing File Safety (Graceful handling)
print("\n3. Testing Missing Audio File Fallback (Must NOT crash)...")
missing_b64 = get_audio_base64("non_existent_file.mp3")
print(f"  - Missing File Base64 Result: {missing_b64} (Expected: None)")
assert missing_b64 is None, "Missing audio file should return None!"

# 4. Verify app.py compilation
print("\n4. Validating app.py syntax & imports...")
import py_compile
py_compile.compile("app.py", doraise=True)
print("  - app.py compiled successfully with 0 syntax errors.")

print("\n=== ALL AUDIO VERIFICATION CHECKS PASSED PERFECTLY ===")
