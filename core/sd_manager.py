"""
SmartBell Manager — SD Card File Operations
Handles reading, writing, renumbering MP3 files and sounds.txt
Supports Music tracks (0001-0100) and Ringtones (0101-0110)
"""

import os
import shutil
import string
import time

MAX_MUSIC_TRACKS = 100
MAX_RINGTONES = 10
RINGTONE_START = 101
MAX_TRACKS = MAX_MUSIC_TRACKS  # backward compat


def detect_sd_cards():
    drives = []
    try:
        import ctypes
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for i in range(26):
            if bitmask & (1 << i):
                letter = string.ascii_uppercase[i]
                drive = f"{letter}:\\"
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
                if drive_type == 2:
                    drives.append(drive)
    except Exception:
        pass
    return drives


def get_mp3_path(sd_root):
    return os.path.join(sd_root, "mp3")


def get_sounds_path(sd_root):
    return os.path.join(sd_root, "sounds.txt")


def ensure_folders(sd_root):
    mp3_path = get_mp3_path(sd_root)
    os.makedirs(mp3_path, exist_ok=True)
    return mp3_path


def load_sounds_map(sd_root):
    sounds_path = get_sounds_path(sd_root)
    sounds_map = {}
    if not os.path.exists(sounds_path):
        return sounds_map
    try:
        with open(sounds_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "," not in line:
                    continue
                parts = line.split(",", 1)
                if len(parts) == 2:
                    sounds_map[parts[0].strip()] = parts[1].strip()
    except Exception as e:
        print(f"[SD] Error reading sounds.txt: {e}")
    return sounds_map


def save_sounds_map(sd_root, sounds_map):
    sounds_path = get_sounds_path(sd_root)
    try:
        with open(sounds_path, "w", encoding="utf-8") as f:
            for number in sorted(sounds_map.keys(), key=lambda x: int(x)):
                f.write(f"{number},{sounds_map[number]}\n")
    except Exception as e:
        print(f"[SD] Error writing sounds.txt: {e}")
        raise


# ========================================================
#  MUSIC TRACKS (0001 - 0100)
# ========================================================

def load_existing_songs(sd_root):
    mp3_path = get_mp3_path(sd_root)
    songs = []
    if not os.path.exists(mp3_path):
        return songs

    sounds_map = load_sounds_map(sd_root)

    files = sorted([
        f for f in os.listdir(mp3_path)
        if f.lower().endswith(".mp3")
        and len(f) >= 8
        and f[:4].isdigit()
        and int(f[:4]) <= MAX_MUSIC_TRACKS
        and not f.startswith("_TEMP_")
    ])

    for file in files:
        number = file[:4]
        name = sounds_map.get(number, os.path.splitext(file)[0])
        songs.append((number, name))

    return songs


def get_next_number(existing_songs):
    if not existing_songs:
        return 1
    last = max(int(num) for num, _ in existing_songs)
    return last + 1


def get_song_count(existing_songs):
    return len(existing_songs)


def can_add_songs(existing_songs, new_count):
    total = len(existing_songs) + new_count
    return total <= MAX_MUSIC_TRACKS


def get_file_path(sd_root, track_number):
    if isinstance(track_number, int):
        track_number = f"{track_number:04d}"
    return os.path.join(get_mp3_path(sd_root), f"{track_number}.mp3")


def add_songs(sd_root, file_paths, existing_songs):
    mp3_path = ensure_folders(sd_root)
    sounds_map = load_sounds_map(sd_root)
    next_num = get_next_number(existing_songs)
    added = []

    for file_path in file_paths:
        if next_num > MAX_MUSIC_TRACKS:
            break
        number = f"{next_num:04d}"
        dest = os.path.join(mp3_path, f"{number}.mp3")
        display_name = os.path.splitext(os.path.basename(file_path))[0]
        shutil.copy2(file_path, dest)
        sounds_map[number] = display_name
        added.append((number, display_name))
        next_num += 1

    save_sounds_map(sd_root, sounds_map)
    return added


def replace_song(sd_root, track_number, new_file_path):
    if isinstance(track_number, int):
        track_number = f"{track_number:04d}"
    dest = os.path.join(get_mp3_path(sd_root), f"{track_number}.mp3")
    shutil.copy2(new_file_path, dest)


def safe_remove(file_path, retries=3):
    for attempt in range(retries):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            return True
        except PermissionError:
            time.sleep(0.3)
    return False


def safe_rename(src, dst, retries=3):
    for attempt in range(retries):
        try:
            if os.path.exists(dst):
                os.remove(dst)
                time.sleep(0.1)
            os.rename(src, dst)
            return True
        except (PermissionError, FileExistsError, OSError):
            time.sleep(0.3)
    try:
        if os.path.exists(dst):
            os.remove(dst)
            time.sleep(0.1)
        shutil.move(src, dst)
        return True
    except Exception:
        return False


def delete_songs(sd_root, track_numbers):
    mp3_path = get_mp3_path(sd_root)
    for number in track_numbers:
        file_path = os.path.join(mp3_path, f"{number}.mp3")
        if not safe_remove(file_path):
            raise PermissionError(f"Cannot delete {file_path} — file is locked")
    time.sleep(0.2)
    renumber_files(sd_root)


def renumber_files(sd_root):
    """Renumber music files (0001-0100) only. Ringtones untouched."""
    mp3_path = get_mp3_path(sd_root)
    if not os.path.exists(mp3_path):
        return

    for f in os.listdir(mp3_path):
        if f.startswith("_TEMP_"):
            safe_remove(os.path.join(mp3_path, f))

    time.sleep(0.1)

    # Only music files (0001-0100)
    files = sorted([
        f for f in os.listdir(mp3_path)
        if f.lower().endswith(".mp3")
        and not f.startswith("_TEMP_")
        and f[:4].isdigit()
        and int(f[:4]) <= MAX_MUSIC_TRACKS
    ])

    sounds_map = load_sounds_map(sd_root)

    # Preserve ringtone entries
    ringtone_entries = {k: v for k, v in sounds_map.items()
                        if k.isdigit() and int(k) >= RINGTONE_START}

    if not files:
        save_sounds_map(sd_root, ringtone_entries)
        return

    already_sequential = True
    for i, file in enumerate(files, start=1):
        expected = f"{i:04d}.mp3"
        if file != expected:
            already_sequential = False
            break

    if already_sequential:
        new_sounds_map = {}
        for i, file in enumerate(files, start=1):
            number = f"{i:04d}"
            old_number = file[:4]
            display_name = sounds_map.get(old_number, os.path.splitext(file)[0])
            new_sounds_map[number] = display_name
        new_sounds_map.update(ringtone_entries)
        save_sounds_map(sd_root, new_sounds_map)
        return

    # Phase 1: Rename to temp
    temp_entries = []
    for i, file in enumerate(files):
        old_path = os.path.join(mp3_path, file)
        temp_name = f"_TEMP_{i:04d}.mp3"
        temp_path = os.path.join(mp3_path, temp_name)

        if not safe_rename(old_path, temp_path):
            for temp_n, orig_n, _ in temp_entries:
                safe_rename(
                    os.path.join(mp3_path, temp_n),
                    os.path.join(mp3_path, orig_n)
                )
            raise OSError(f"Renumber failed at {file}")

        old_number = file[:4] if file[:4].isdigit() else "0000"
        display_name = sounds_map.get(old_number, os.path.splitext(file)[0])
        temp_entries.append((temp_name, file, display_name))

    time.sleep(0.1)

    # Phase 2: Rename to final
    new_sounds_map = {}
    for i, (temp_name, orig_name, display_name) in enumerate(temp_entries, start=1):
        new_number = f"{i:04d}"
        final_name = f"{new_number}.mp3"
        temp_path = os.path.join(mp3_path, temp_name)
        final_path = os.path.join(mp3_path, final_name)

        if not safe_rename(temp_path, final_path):
            raise OSError(f"Renumber failed at phase 2: {temp_name} -> {final_name}")

        new_sounds_map[new_number] = display_name

    new_sounds_map.update(ringtone_entries)
    save_sounds_map(sd_root, new_sounds_map)
    print(f"[SD] Renumbered {len(temp_entries)} music files.")


# ========================================================
#  RINGTONES (0101 - 0110)
# ========================================================

def load_existing_ringtones(sd_root):
    """Load ringtones from SD. Returns list of (slot, number_str, name)."""
    mp3_path = get_mp3_path(sd_root)
    ringtones = []
    if not os.path.exists(mp3_path):
        return ringtones

    sounds_map = load_sounds_map(sd_root)

    for slot in range(1, MAX_RINGTONES + 1):
        track_num = RINGTONE_START + slot - 1
        number = f"{track_num:04d}"
        file_path = os.path.join(mp3_path, f"{number}.mp3")

        if os.path.exists(file_path):
            name = sounds_map.get(number, f"Ringtone {slot}")
            ringtones.append((slot, number, name))

    return ringtones


def get_next_ringtone_slot(existing_ringtones):
    """Get next empty slot (1-10). Returns None if full."""
    used_slots = {slot for slot, _, _ in existing_ringtones}
    for i in range(1, MAX_RINGTONES + 1):
        if i not in used_slots:
            return i
    return None


def add_ringtone(sd_root, file_path, slot=None):
    """
    Add ringtone to specific slot or next available.
    Writes immediately to SD.
    Returns (slot, number, name) or None.
    """
    mp3_path = ensure_folders(sd_root)
    sounds_map = load_sounds_map(sd_root)
    existing = load_existing_ringtones(sd_root)

    if slot is None:
        slot = get_next_ringtone_slot(existing)
        if slot is None:
            return None

    if slot < 1 or slot > MAX_RINGTONES:
        return None

    track_num = RINGTONE_START + slot - 1
    number = f"{track_num:04d}"
    dest = os.path.join(mp3_path, f"{number}.mp3")
    display_name = os.path.splitext(os.path.basename(file_path))[0]

    shutil.copy2(file_path, dest)
    sounds_map[number] = display_name
    save_sounds_map(sd_root, sounds_map)

    print(f"[SD] Ringtone {slot} added: {display_name}")
    return (slot, number, display_name)


def delete_ringtone(sd_root, slot):
    """Delete ringtone from slot (1-10). Immediate."""
    mp3_path = get_mp3_path(sd_root)
    sounds_map = load_sounds_map(sd_root)

    track_num = RINGTONE_START + slot - 1
    number = f"{track_num:04d}"
    file_path = os.path.join(mp3_path, f"{number}.mp3")

    if not safe_remove(file_path):
        raise PermissionError(f"Cannot delete ringtone {slot}")

    if number in sounds_map:
        del sounds_map[number]
        save_sounds_map(sd_root, sounds_map)

    print(f"[SD] Ringtone {slot} deleted.")


def get_ringtone_file_path(sd_root, slot):
    track_num = RINGTONE_START + slot - 1
    return os.path.join(get_mp3_path(sd_root), f"{track_num:04d}.mp3")


# ========================================================
#  SYNC
# ========================================================

def get_songs_for_sync(sd_root):
    """Get ALL tracks (music + ringtones) for ESP32 sync."""
    songs = load_existing_songs(sd_root)
    result = [{"track": int(num), "name": name} for num, name in songs]

    ringtones = load_existing_ringtones(sd_root)
    for slot, number, name in ringtones:
        result.append({"track": int(number), "name": name})

    return result