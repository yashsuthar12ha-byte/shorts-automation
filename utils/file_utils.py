import os
import shutil
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime


def ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_dir(path: Path) -> None:
    """Remove and recreate a directory."""
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def list_videos(directory: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """List all video files in a directory."""
    if extensions is None:
        extensions = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
    videos = []
    if directory.exists():
        for f in directory.iterdir():
            if f.suffix.lower() in extensions:
                videos.append(f)
    return sorted(videos)


def save_json(data: dict, path: Path) -> None:
    """Save data as JSON with nice formatting."""
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(path: Path) -> dict:
    """Load JSON file."""
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def parse_timestamp(ts: str) -> float:
    """Convert MM:SS to seconds."""
    parts = ts.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return float(parts[-1])


def get_timestamp() -> str:
    """Get current timestamp string for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sanitize_filename(name: str) -> str:
    """Remove characters that are invalid in filenames."""
    invalid = '<>:"/\\|?*'
    for c in invalid:
        name = name.replace(c, "")
    return name.strip() or "untitled"
