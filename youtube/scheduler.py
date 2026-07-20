"""
YouTube Scheduler - Manages upload scheduling based on best posting times.
Supports queue management and optimal time selection.
"""
import json
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
from utils.config_loader import config
from utils.file_utils import ensure_dir, save_json, load_json
from utils.logger import get_logger

log = get_logger(__name__)


class UploadScheduler:
    """Manages upload queue and schedules uploads at optimal times."""

    def __init__(self):
        self.enabled = config.get("youtube", "schedule", "enabled", default=True)
        self.max_per_day = config.get("youtube", "schedule", "max_per_day", default=3)
        self.best_times = config.get("youtube", "schedule", "best_times",
                                      default=["12:00", "15:00", "19:00", "21:00"])
        self.timezone_str = config.get("youtube", "schedule", "timezone", default="UTC")
        self.days = config.get("youtube", "schedule", "days",
                               default=["monday", "tuesday", "wednesday",
                                        "thursday", "friday", "saturday", "sunday"])
        self.queue_path = config.output_dir / "upload_queue.json"
        self.history_path = config.output_dir / "upload_history.json"
        ensure_dir(config.output_dir)

    def get_next_upload_time(self) -> Optional[datetime]:
        """Calculate the next optimal upload time."""
        if not self.enabled:
            return datetime.now(timezone.utc)

        today = datetime.now(timezone.utc)
        today_str = today.strftime("%A").lower()

        # Check if today is a scheduled day
        if today_str not in self.days:
            # Find next scheduled day
            day_map = ["monday", "tuesday", "wednesday", "thursday",
                       "friday", "saturday", "sunday"]
            current_idx = day_map.index(today_str)
            for offset in range(1, 8):
                next_idx = (current_idx + offset) % 7
                if day_map[next_idx] in self.days:
                    next_day = today + timedelta(days=offset)
                    return next_day.replace(
                        hour=int(self.best_times[0].split(":")[0]),
                        minute=int(self.best_times[0].split(":")[1]),
                        second=0, microsecond=0
                    )
            return today + timedelta(hours=1)

        # Find used slots today
        uploads_today = self._count_today_uploads(today)
        available_times = []

        for time_str in self.best_times:
            hour, minute = map(int, time_str.split(":"))
            slot_time = today.replace(hour=hour, minute=minute, second=0, microsecond=0)

            if slot_time > today and len(available_times) < (self.max_per_day - uploads_today):
                available_times.append(slot_time)

        if available_times:
            return available_times[0]

        return today + timedelta(hours=2)

    def _count_today_uploads(self, today: datetime) -> int:
        """Count how many uploads have happened today."""
        history = load_json(self.history_path)
        today_str = today.strftime("%Y-%m-%d")
        count = sum(
            1 for item in history.get("uploads", [])
            if item.get("date", "").startswith(today_str)
        )
        return count

    def add_to_queue(self, clip_info: Dict) -> None:
        """Add a clip to the upload queue."""
        queue = load_json(self.queue_path)
        if "items" not in queue:
            queue["items"] = []

        queue["items"].append({
            **clip_info,
            "added_at": datetime.now().isoformat(),
            "status": "pending",
        })
        save_json(queue, self.queue_path)
        log.info(f"Added to queue: {clip_info.get('title', 'untitled')}")

    def get_next_from_queue(self) -> Optional[Dict]:
        """Get the next pending item from the queue."""
        queue = load_json(self.queue_path)
        for item in queue.get("items", []):
            if item.get("status") == "pending":
                return item
        return None

    def mark_completed(self, clip_info: Dict) -> None:
        """Mark a queue item as completed and log to history."""
        queue = load_json(self.queue_path)
        for item in queue.get("items", []):
            if item.get("title") == clip_info.get("title"):
                item["status"] = "completed"
                item["completed_at"] = datetime.now().isoformat()
                break
        save_json(queue, self.queue_path)

        # Add to history
        history = load_json(self.history_path)
        if "uploads" not in history:
            history["uploads"] = []
        history["uploads"].append({
            **clip_info,
            "uploaded_at": datetime.now().isoformat(),
        })
        save_json(history, self.history_path)

    def get_queue_size(self) -> int:
        """Get number of pending items in queue."""
        queue = load_json(self.queue_path)
        return sum(1 for item in queue.get("items", []) if item.get("status") == "pending")

    def get_best_time_today(self) -> Optional[str]:
        """Get the best available time slot today."""
        today = datetime.now(timezone.utc)
        for time_str in self.best_times:
            hour, minute = map(int, time_str.split(":"))
            slot_time = today.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if slot_time > today:
                return time_str
        return None
