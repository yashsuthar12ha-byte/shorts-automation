"""
YouTube Analytics - Tracks video performance and provides learning insights.
Analyzes metrics to improve future content generation.
"""
import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from utils.config_loader import config
from utils.file_utils import ensure_dir, save_json, load_json
from utils.logger import get_logger

log = get_logger(__name__)


class AnalyticsTracker:
    """Tracks and analyzes YouTube Shorts performance."""

    def __init__(self):
        self.enabled = config.get("analytics", "enabled", default=True)
        self.track_metrics = config.get("analytics", "track_metrics", default=[])
        self.feedback_days = config.get("analytics", "learning", "feedback_window_days",
                                         default=7)
        self.history_path = config.output_dir / "upload_history.json"
        self.analytics_path = config.output_dir / "analytics.json"
        self.insights_path = config.output_dir / "insights.json"
        ensure_dir(config.output_dir)

        # YouTube API service (initialized when needed)
        self._service = None

    def _init_service(self):
        """Initialize YouTube API service for analytics."""
        if self._service is None:
            try:
                from youtube.uploader import YouTubeUploader
                uploader = YouTubeUploader()
                if uploader.authenticate():
                    self._service = uploader.service
            except Exception as e:
                log.warning(f"Analytics API init failed: {e}")

    def fetch_performance(self, video_id: str) -> Dict:
        """Fetch performance metrics for a specific video."""
        if not self.enabled:
            return {}

        try:
            self._init_service()
            if not self._service:
                return {}

            request = self._service.videos().list(
                part="statistics,snippet",
                id=video_id,
            )
            response = request.execute()

            items = response.get("items", [])
            if not items:
                return {}

            stats = items[0].get("statistics", {})
            snippet = items[0].get("snippet", {})

            metrics = {
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
                "favorites": int(stats.get("favoriteCount", 0)),
                "fetched_at": datetime.now().isoformat(),
            }

            # Save to analytics
            analytics = load_json(self.analytics_path)
            if "videos" not in analytics:
                analytics["videos"] = {}
            analytics["videos"][video_id] = metrics
            save_json(analytics, self.analytics_path)

            return metrics

        except Exception as e:
            log.warning(f"Failed to fetch analytics for {video_id}: {e}")
            return {}

    def fetch_all_performance(self) -> List[Dict]:
        """Fetch performance for all uploaded videos."""
        history = load_json(self.history_path)
        results = []

        for upload in history.get("uploads", []):
            video_id = upload.get("video_id")
            if video_id:
                metrics = self.fetch_performance(video_id)
                if metrics:
                    results.append(metrics)

        return results

    def get_best_performing_titles(self) -> List[str]:
        """Analyze which title patterns perform best."""
        analytics = load_json(self.analytics_path)
        videos = analytics.get("videos", {})

        scored = []
        for vid, data in videos.items():
            views = data.get("views", 0)
            likes = data.get("likes", 0)
            title = data.get("title", "")

            if views > 0:
                engagement = (likes / max(views, 1)) * 100
                scored.append({
                    "title": title,
                    "views": views,
                    "engagement": engagement,
                    "score": views * (1 + engagement / 100),
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return [s["title"] for s in scored[:10]]

    def get_performance_trends(self) -> Dict:
        """Analyze performance trends over time."""
        history = load_json(self.history_path)
        analytics = load_json(self.analytics_path)

        trends = {
            "total_uploads": 0,
            "avg_views": 0,
            "avg_likes": 0,
            "best_day": "",
            "best_time": "",
        }

        uploads = history.get("uploads", [])
        if not uploads:
            return trends

        trends["total_uploads"] = len(uploads)

        views = []
        likes = []
        day_performance = {}
        hour_performance = {}

        for upload in uploads:
            video_id = upload.get("video_id")
            if video_id and video_id in analytics.get("videos", {}):
                stats = analytics["videos"][video_id]
                v = stats.get("views", 0)
                l = stats.get("likes", 0)
                views.append(v)
                likes.append(l)

                # Track by day
                uploaded_at = upload.get("uploaded_at", "")
                try:
                    dt = datetime.fromisoformat(uploaded_at)
                    day = dt.strftime("%A")
                    hour = dt.hour

                    if day not in day_performance:
                        day_performance[day] = []
                    day_performance[day].append(v)

                    if hour not in hour_performance:
                        hour_performance[hour] = []
                    hour_performance[hour].append(v)
                except (ValueError, TypeError):
                    pass

        if views:
            trends["avg_views"] = round(np.mean(views), 1)
            trends["avg_likes"] = round(np.mean(likes), 1)

        # Best day
        if day_performance:
            best_day = max(day_performance, key=lambda d: np.mean(day_performance[d]))
            trends["best_day"] = best_day

        # Best hour
        if hour_performance:
            best_hour = max(hour_performance, key=lambda h: np.mean(hour_performance[h]))
            trends["best_time"] = f"{best_hour:02d}:00"

        return trends

    def generate_insights(self) -> Dict:
        """Generate actionable insights for content improvement."""
        trends = self.get_performance_trends()
        best_titles = self.get_best_performing_titles()

        insights = {
            "generated_at": datetime.now().isoformat(),
            "trends": trends,
            "best_title_patterns": best_titles[:5],
            "recommendations": [],
            "learning_data": {},
        }

        # Generate recommendations
        if trends.get("best_day"):
            insights["recommendations"].append(
                f"Post on {trends['best_day']} for best performance"
            )

        if trends.get("best_time"):
            insights["recommendations"].append(
                f"Schedule uploads around {trends['best_time']}"
            )

        if trends.get("avg_views", 0) < 100:
            insights["recommendations"].append(
                "Focus on more engaging clip selection and better titles"
            )

        if trends.get("avg_likes", 0) > 0 and trends.get("avg_views", 0) > 0:
            engagement_rate = (trends["avg_likes"] / trends["avg_views"]) * 100
            insights["learning_data"]["avg_engagement_rate"] = round(engagement_rate, 2)

        # Save insights
        save_json(insights, self.insights_path)
        log.info("Analytics insights generated")

        return insights

    def get_improvement_suggestions(self) -> Dict:
        """Get suggestions for improving future Shorts based on past performance."""
        insights = self.generate_insights()

        suggestions = {
            "title_style": "",
            "best_posting_time": insights.get("trends", {}).get("best_time", "12:00"),
            "best_day": insights.get("trends", {}).get("best_day", "Saturday"),
            "content_focus": "",
        }

        best_titles = insights.get("best_title_patterns", [])
        if best_titles:
            # Analyze common patterns in best titles
            suggestions["title_style"] = "Use curiosity gaps and power words"

        return suggestions
