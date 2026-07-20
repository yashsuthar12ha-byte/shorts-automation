"""
Learning System - Continuously improves content generation based on analytics.
Analyzes past performance and adapts titles, clip selection, and scheduling.
"""
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from utils.config_loader import config
from utils.file_utils import load_json, save_json
from utils.logger import get_logger

log = get_logger(__name__)


class LearningSystem:
    """
    Self-improvement engine that learns from video performance.
    Adjusts title styles, clip selection criteria, hashtags, and scheduling.
    """

    def __init__(self):
        self.enabled = config.get("analytics", "learning", "enabled", default=True)
        self.feedback_days = config.get("analytics", "learning", "feedback_window_days",
                                         default=7)
        self.learning_data_path = config.output_dir / "learning_data.json"
        self._learning_data = self._load_learning_data()

    def _load_learning_data(self) -> Dict:
        """Load persistent learning data."""
        return load_json(self.learning_data_path)

    def _save_learning_data(self):
        """Save learning data."""
        save_json(self._learning_data, self.learning_data_path)

    def record_outcome(self, video_data: Dict):
        """Record the outcome of a video upload for learning."""
        if not self.enabled:
            return

        outcomes = self._learning_data.setdefault("outcomes", [])
        outcomes.append({
            **video_data,
            "recorded_at": datetime.now().isoformat(),
        })

        # Keep only recent outcomes
        cutoff = datetime.now() - timedelta(days=self.feedback_days * 30)
        outcomes[:] = [
            o for o in outcomes
            if datetime.fromisoformat(o.get("recorded_at", "2000-01-01")) > cutoff
        ]

        self._save_learning_data()

    def optimize_title_style(self) -> Dict:
        """
        Analyze which title patterns perform best and return optimized style.
        Returns weights for different title components.
        """
        outcomes = self._learning_data.get("outcomes", [])
        if len(outcomes) < 3:
            return {"style": "default", "use_emojis": True, "use_curiosity": True}

        # Score each title pattern
        patterns = {}
        for outcome in outcomes:
            title = outcome.get("title", "")
            views = outcome.get("views", 0)

            # Pattern analysis
            has_emoji = any(c in title for c in "🔥🤯😱💥⭐👀🎮")
            has_curiosity = any(w in title.lower() for w in ["you won't", "insane", "unbelievable", "crazy", "epic", "this "])
            has_game_name = any(outcome.get("game", "").lower() in title.lower() for _ in [1])
            has_question = "?" in title

            pattern_key = f"emoji={has_emoji}_curiosity={has_curiosity}_game={has_game_name}"
            if pattern_key not in patterns:
                patterns[pattern_key] = {"views": [], "count": 0}
            patterns[pattern_key]["views"].append(views)
            patterns[pattern_key]["count"] += 1

        if not patterns:
            return {"style": "default", "use_emojis": True, "use_curiosity": True}

        # Find best performing pattern
        best_pattern = max(
            patterns.values(),
            key=lambda p: np.mean(p["views"]) if p["views"] else 0
        )

        avg_views = np.mean(best_pattern["views"]) if best_pattern["views"] else 0

        return {
            "style": "learned",
            "use_emojis": "emoji=True" in str(best_pattern),
            "use_curiosity": "curiosity=True" in str(best_pattern),
            "expected_views": round(avg_views, 1),
        }

    def optimize_clip_selection(self) -> Dict:
        """
        Learn which clip characteristics drive the most engagement.
        Returns adjusted weights for highlight scoring.
        """
        outcomes = self._learning_data.get("outcomes", [])
        if len(outcomes) < 3:
            return {
                "motion_weight": 0.3,
                "excitement_weight": 0.5,
                "color_weight": 0.2,
            }

        # Analyze which clip types perform best
        type_performance = {}
        for outcome in outcomes:
            clip_type = outcome.get("clip_type", "unknown")
            views = outcome.get("views", 0)
            likes = outcome.get("likes", 0)

            if clip_type not in type_performance:
                type_performance[clip_type] = {"views": [], "likes": [], "engagement": []}
            type_performance[clip_type]["views"].append(views)
            type_performance[clip_type]["likes"].append(likes)
            if views > 0:
                type_performance[clip_type]["engagement"].append(likes / views)

        # Calculate optimal weights
        best_types = sorted(
            type_performance.keys(),
            key=lambda t: np.mean(type_performance[t]["views"]) if type_performance[t]["views"] else 0,
            reverse=True,
        )

        # Determine if action or variety performs better
        action_score = sum(
            np.mean(type_performance[t]["views"])
            for t in best_types[:2]
            if type_performance[t]["views"]
        ) / max(len(best_types[:2]), 1)

        return {
            "preferred_clip_types": best_types[:3],
            "motion_weight": 0.4 if "action" in str(best_types[:3]) else 0.2,
            "excitement_weight": 0.4,
            "color_weight": 0.2,
        }

    def optimize_schedule(self) -> Dict:
        """
        Learn the best posting schedule based on historical performance.
        Returns optimal posting days and times.
        """
        outcomes = self._learning_data.get("outcomes", [])
        if len(outcomes) < 3:
            return {"best_days": ["saturday", "sunday"], "best_hours": ["12:00", "19:00"]}

        day_performance = {}
        hour_performance = {}

        for outcome in outcomes:
            uploaded_at = outcome.get("uploaded_at", "")
            views = outcome.get("views", 0)

            try:
                dt = datetime.fromisoformat(uploaded_at)
                day = dt.strftime("%A").lower()
                hour = dt.hour

                if day not in day_performance:
                    day_performance[day] = []
                day_performance[day].append(views)

                hour_key = f"{hour:02d}:00"
                if hour_key not in hour_performance:
                    hour_performance[hour_key] = []
                hour_performance[hour_key].append(views)
            except (ValueError, TypeError):
                pass

        best_days = sorted(
            day_performance.keys(),
            key=lambda d: np.mean(day_performance[d]) if day_performance[d] else 0,
            reverse=True,
        )

        best_hours = sorted(
            hour_performance.keys(),
            key=lambda h: np.mean(hour_performance[h]) if hour_performance[h] else 0,
            reverse=True,
        )

        return {
            "best_days": best_days[:3],
            "best_hours": best_hours[:3],
        }

    def get_optimized_config(self) -> Dict:
        """
        Get a fully optimized configuration based on learned patterns.
        This can be used to update settings.yaml automatically.
        """
        if not self.enabled:
            return {}

        title_style = self.optimize_title_style()
        clip_weights = self.optimize_clip_selection()
        schedule = self.optimize_schedule()

        optimized = {
            "titles": {
                "include_emojis": title_style.get("use_emojis", True),
                "style": title_style.get("style", "click_optimized"),
            },
            "highlight_detection": {
                "excitement_threshold": 0.6,  # Lower threshold = more clips
                "motion_weight": clip_weights.get("motion_weight", 0.3),
                "excitement_weight": clip_weights.get("excitement_weight", 0.5),
            },
            "youtube": {
                "schedule": {
                    "best_times": schedule.get("best_hours", ["12:00", "19:00"]),
                    "days": schedule.get("best_days", ["saturday", "sunday"]),
                }
            },
            "learning_metadata": {
                "last_optimized": datetime.now().isoformat(),
                "total_videos_analyzed": len(self._learning_data.get("outcomes", [])),
            },
        }

        return optimized

    def apply_optimizations(self):
        """Apply learned optimizations to the live configuration."""
        optimized = self.get_optimized_config()
        if not optimized:
            return

        log.info("Applying learned optimizations...")

        # Log what changed
        titles_cfg = optimized.get("titles", {})
        if titles_cfg.get("include_emojis") is not None:
            log.info(f"  Emoji in titles: {titles_cfg['include_emojis']}")

        schedule = optimized.get("youtube", {}).get("schedule", {})
        if schedule.get("best_times"):
            log.info(f"  Best times: {schedule['best_times']}")
        if schedule.get("days"):
            log.info(f"  Best days: {schedule['days']}")

        self._learning_data["last_applied_optimization"] = optimized
        self._learning_data["last_applied_at"] = datetime.now().isoformat()
        self._save_learning_data()

        log.info("Optimizations applied successfully")
