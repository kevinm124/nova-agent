"""
The agent's tools. Each function is something Nova can do on your computer.

Gemini reads each function's name, arguments and docstring to decide when to
use it, so the docstrings are written for the AI, not just for humans.
"""

import json
import os
import platform
import shutil
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

import psutil

# ---------------------------------------------------------------------------
# Hooks for the interface
# ---------------------------------------------------------------------------
# The interface (terminal now, a GUI later) plugs its own functions in here.
# This keeps the tools independent of how they are displayed.


def _default_confirm(question: str) -> bool:
    return input(f"{question} [y/n] ").strip().lower() in ("y", "yes", "d", "da")


confirm = _default_confirm          # asks the user before anything risky
on_tool_used = lambda name: None    # tells the interface which tool is running


def _announce(name):
    on_tool_used(name)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

HOME = Path.home()
DATA_DIR = Path(__file__).parent / "data"
NOTES_FILE = DATA_DIR / "notes.json"

# Friendly names the user can say instead of a full path
FOLDER_SHORTCUTS = {
    "downloads": HOME / "Downloads",
    "prenosi": HOME / "Downloads",
    "desktop": HOME / "Desktop",
    "namizje": HOME / "Desktop",
    "documents": HOME / "Documents",
    "dokumenti": HOME / "Documents",
    "pictures": HOME / "Pictures",
    "slike": HOME / "Pictures",
    "home": HOME,
}

FILE_CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".heic"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".csv", ".md"},
    "Videos": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    "Music": {".mp3", ".wav", ".flac", ".m4a", ".ogg"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Installers": {".exe", ".msi", ".dmg", ".deb", ".appimage"},
    "Code": {".py", ".js", ".html", ".css", ".cs", ".cpp", ".java", ".json", ".sql"},
}


def _resolve_folder(folder: str) -> Path:
    """Turn 'downloads' or a full path into a real folder path."""
    key = folder.strip().lower()
    if key in FOLDER_SHORTCUTS:
        return FOLDER_SHORTCUTS[key]
    return Path(folder).expanduser()


def _category_for(path: Path) -> str:
    ext = path.suffix.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"


def _gb(num_bytes) -> float:
    return round(num_bytes / 1024**3, 1)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


def get_system_status() -> dict:
    """Check the computer's health: CPU, RAM, disk space, battery and uptime.

    Use this when the user asks how their computer is doing, why it is slow,
    or how much space or memory is left.
    """
    _announce("Checking system status")
    ram = psutil.virtual_memory()

    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue
        if usage.total < 1024**3:
            continue
        disks.append({
            "drive": part.mountpoint,
            "used_percent": usage.percent,
            "free_gb": _gb(usage.free),
            "total_gb": _gb(usage.total),
        })

    battery = psutil.sensors_battery()
    top = sorted(
        psutil.process_iter(["name", "memory_percent"]),
        key=lambda p: p.info["memory_percent"] or 0,
        reverse=True,
    )[:5]

    return {
        "os": f"{platform.system()} {platform.release()}",
        "cpu_percent": psutil.cpu_percent(interval=1),
        "cpu_cores": psutil.cpu_count(logical=False) or psutil.cpu_count(),
        "ram_used_percent": ram.percent,
        "ram_used_gb": _gb(ram.used),
        "ram_total_gb": _gb(ram.total),
        "disks": disks,
        "battery_percent": battery.percent if battery else None,
        "charging": battery.power_plugged if battery else None,
        "uptime": str(timedelta(seconds=int(time.time() - psutil.boot_time()))),
        "top_memory_apps": [
            {"name": p.info["name"], "memory_percent": round(p.info["memory_percent"] or 0, 1)}
            for p in top
        ],
    }


def organize_folder(folder: str) -> str:
    """Tidy up a folder by moving its files into subfolders by type
    (Images, Documents, Videos, Music, Archives, Installers, Code, Other).

    Args:
        folder: A shortcut like "downloads", "desktop", "documents", or a full path.
    """
    _announce(f"Organizing {folder}")
    path = _resolve_folder(folder)
    if not path.is_dir():
        return f"Folder not found: {path}"

    files = [f for f in path.iterdir() if f.is_file() and not f.name.startswith(".")]
    if not files:
        return f"Nothing to organize, {path} has no loose files."

    plan = {}
    for f in files:
        plan.setdefault(_category_for(f), []).append(f)
    summary = ", ".join(f"{len(v)} → {k}" for k, v in plan.items())

    if not confirm(f"Move {len(files)} files in {path}? ({summary})"):
        return "Cancelled by the user. Nothing was moved."

    moved = 0
    for category, group in plan.items():
        target_dir = path / category
        target_dir.mkdir(exist_ok=True)
        for f in group:
            target = target_dir / f.name
            counter = 1
            while target.exists():  # never overwrite an existing file
                target = target_dir / f"{f.stem} ({counter}){f.suffix}"
                counter += 1
            shutil.move(str(f), str(target))
            moved += 1

    return f"Moved {moved} files in {path}: {summary}."


def find_files(name: str, folder: str = "home") -> list:
    """Search for files whose name contains the given text.

    Args:
        name: Part of the file name to look for, e.g. "cv" or "invoice".
        folder: Where to search. A shortcut like "downloads" or a full path.
            Defaults to the user's home folder.
    """
    _announce(f"Searching for '{name}'")
    root = _resolve_folder(folder)
    needle = name.lower()
    results = []
    skip = {"node_modules", ".git", "AppData", "__pycache__", ".cache", "Library"}

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip and not d.startswith(".")]
        for filename in filenames:
            if needle in filename.lower():
                full = Path(dirpath) / filename
                try:
                    modified = datetime.fromtimestamp(full.stat().st_mtime)
                except OSError:
                    continue
                results.append({"path": str(full), "modified": modified.strftime("%Y-%m-%d")})
                if len(results) >= 20:
                    return results
    return results


# Only these apps can be opened. A fixed list means the AI can never run an
# arbitrary command on your computer.
APPS = {
    "Windows": {
        "vs code": "code", "notepad": "notepad", "calculator": "calc",
        "explorer": "explorer", "chrome": "chrome", "edge": "msedge",
        "terminal": "wt", "task manager": "taskmgr", "settings": "ms-settings:",
        "spotify": "spotify:", "discord": "discord:",
    },
    "Darwin": {
        "vs code": "Visual Studio Code", "calculator": "Calculator", "finder": "Finder",
        "chrome": "Google Chrome", "safari": "Safari", "terminal": "Terminal",
        "spotify": "Spotify", "discord": "Discord",
    },
    "Linux": {
        "vs code": "code", "calculator": "gnome-calculator", "files": "nautilus",
        "chrome": "google-chrome", "firefox": "firefox", "terminal": "gnome-terminal",
    },
}


def open_app(app: str) -> str:
    """Open an application on the computer.

    Args:
        app: The app name, e.g. "vs code", "chrome", "calculator", "spotify",
            "discord", "task manager", "settings".
    """
    _announce(f"Opening {app}")
    system = platform.system()
    known = APPS.get(system, {})
    command = known.get(app.strip().lower())
    if not command:
        return f"I can't open '{app}'. Apps I know: {', '.join(known)}."

    try:
        if system == "Windows":
            os.startfile(command)
        elif system == "Darwin":
            subprocess.Popen(["open", "-a", command])
        else:
            subprocess.Popen([command])
    except (OSError, FileNotFoundError):
        return f"'{app}' doesn't seem to be installed."
    return f"Opened {app}."


def _load_notes() -> list:
    if NOTES_FILE.exists():
        return json.loads(NOTES_FILE.read_text(encoding="utf-8"))
    return []


def _save_notes(notes: list):
    DATA_DIR.mkdir(exist_ok=True)
    NOTES_FILE.write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")


def add_note(text: str) -> str:
    """Save a note or reminder for the user.

    Args:
        text: What to remember, e.g. "buy thermal paste" or "exam on Friday".
    """
    _announce("Saving note")
    notes = _load_notes()
    notes.append({"id": len(notes) + 1, "text": text, "created": datetime.now().strftime("%Y-%m-%d %H:%M")})
    _save_notes(notes)
    return f"Saved note #{len(notes)}."


def list_notes() -> list:
    """Show all of the user's saved notes and reminders."""
    _announce("Reading notes")
    return _load_notes()


def delete_note(note_id: int) -> str:
    """Delete one saved note.

    Args:
        note_id: The number of the note to delete.
    """
    _announce(f"Deleting note #{note_id}")
    notes = _load_notes()
    remaining = [n for n in notes if n["id"] != note_id]
    if len(remaining) == len(notes):
        return f"There is no note #{note_id}."
    if not confirm(f"Delete note #{note_id}?"):
        return "Cancelled by the user."
    for i, n in enumerate(remaining, start=1):  # renumber so ids stay 1, 2, 3...
        n["id"] = i
    _save_notes(remaining)
    return f"Deleted note #{note_id}."


# Every tool Nova can use. Add a new function above and list it here.
ALL_TOOLS = [
    get_system_status,
    organize_folder,
    find_files,
    open_app,
    add_note,
    list_notes,
    delete_note,
]
