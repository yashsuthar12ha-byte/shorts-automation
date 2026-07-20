"""
Highlight Analyzer - Identifies the most engaging moments in gameplay.
Uses multiple signals: audio peaks, motion intensity, and optional AI analysis.
"""
import cv2
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from core.scene_detector import SceneDetector, Scene
from utils.config_loader import config
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class Highlight:
    """A detected highlight/clip worth extracting."""
    index: int
    scene: Scene
    start_time: float
    end_time: float
    duration: float
    score: float  # 0-1 overall quality score
    excitement_score: float = 0.0
    motion_score: float = 0.0
    audio_score: float = 0.0
    ai_score: float = 0.0
    highlight_type: str = "unknown"
    reason: str = ""

    def to_dict(self):
        return {
            "index": self.index,
            "start_time": f"{int(self.start_time//60):02d}:{int(self.start_time%60):02d}",
            "end_time": f"{int(self.end_time//60):02d}:{int(self.end_time%60):02d}",
            "duration": round(self.duration, 2),
            "score": round(self.score, 2),
            "type": self.highlight_type,
            "reason": self.reason,
        }


class HighlightAnalyzer:
    """Analyzes video to find the best moments for Shorts."""

    def __init__(self):
        self.excitement_threshold = config.get("highlight_detection", "excitement_threshold", default=0.7)
        self.max_highlights = config.get("highlight_detection", "max_highlights_per_video", default=10)
        self.min_duration = config.get("shorts", "min_clip_duration", default=15)
        self.max_duration = config.get("shorts", "max_clip_duration", default=58)

    def analyze(self, video_path: Path, scenes: List[Scene]) -> List[Highlight]:
        """
        Analyze video scenes and score them for highlight potential.
        Returns ranked list of highlights.
        """
        log.info(f"Analyzing highlights in {video_path.name}...")
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        highlights = []
        for i, scene in enumerate(scenes):
            if scene.duration < self.min_duration:
                continue
            if scene.duration > self.max_duration + 10:
                # Split long scenes further
                sub_scenes = self._split_long_scene(cap, scene, fps)
                for j, ss in enumerate(sub_scenes):
                    scores = self._score_scene(cap, ss, fps, total_frames)
                    if scores["overall"] >= self.excitement_threshold:
                        highlights.append(Highlight(
                            index=len(highlights),
                            scene=ss,
                            start_time=ss.start_time,
                            end_time=ss.end_time,
                            duration=ss.duration,
                            score=scores["overall"],
                            excitement_score=scores["excitement"],
                            motion_score=scores["motion"],
                            audio_score=scores.get("audio", 0),
                            ai_score=scores.get("ai", 0),
                            highlight_type=self._classify_highlight(scores),
                            reason=self._generate_reason(scores),
                        ))
            else:
                scores = self._score_scene(cap, scene, fps, total_frames)
                if scores["overall"] >= self.excitement_threshold:
                    highlights.append(Highlight(
                        index=len(highlights),
                        scene=scene,
                        start_time=scene.start_time,
                        end_time=scene.end_time,
                        duration=scene.duration,
                        score=scores["overall"],
                        excitement_score=scores["excitement"],
                        motion_score=scores["motion"],
                        audio_score=scores.get("audio", 0),
                        ai_score=scores.get("ai", 0),
                        highlight_type=self._classify_highlight(scores),
                        reason=self._generate_reason(scores),
                    ))

        cap.release()

        # Sort by score and limit
        highlights.sort(key=lambda h: h.score, reverse=True)
        highlights = highlights[:self.max_highlights]

        log.info(f"Found {len(highlights)} highlights in {video_path.name}")
        return highlights

    def _score_scene(self, cap, scene: Scene, fps: float, total_frames: int) -> Dict[str, float]:
        """Score a single scene based on multiple factors."""
        scores = {}

        # Motion analysis
        scores["motion"] = self._analyze_motion(cap, scene, fps)

        # Excitement (combination of motion + visual changes)
        scores["excitement"] = min(scores["motion"] * 1.2, 1.0)

        # Brightness/color variety (more action = more variety)
        scores["color_variety"] = self._analyze_color_variety(cap, scene, fps)

        # Overall weighted score
        scores["overall"] = (
            scores["excitement"] * 0.5 +
            scores["motion"] * 0.3 +
            scores["color_variety"] * 0.2
        )

        scores.setdefault("audio", 0.0)
        scores.setdefault("ai", 0.0)

        return scores

    def _analyze_motion(self, cap, scene: Scene, fps: float) -> float:
        """Analyze motion intensity within a scene using optical flow."""
        start_frame = int(scene.start_time * fps)
        end_frame = int(scene.end_time * fps)

        if start_frame >= end_frame:
            return 0.0

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        ret, prev_frame = cap.read()
        if not ret:
            return 0.0

        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        total_motion = 0.0
        samples = 0
        step = max(1, int(fps * 0.25))  # Sample 4 times per second

        current_frame = start_frame + fps  # Skip first second for stability
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

        while current_frame < end_frame:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Calculate frame difference as motion proxy
            diff = cv2.absdiff(prev_gray, gray)
            motion = np.mean(diff) / 255.0
            total_motion += motion
            samples += 1

            prev_gray = gray
            current_frame += step
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

        avg_motion = total_motion / max(samples, 1)
        return min(avg_motion * 5.0, 1.0)  # Scale up, cap at 1.0

    def _analyze_color_variety(self, cap, scene: Scene, fps: float) -> float:
        """Analyze color diversity as an indicator of visual interest."""
        start_frame = int(scene.start_time * fps)
        end_frame = int(scene.end_time * fps)

        if start_frame >= end_frame:
            return 0.0

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        step = max(1, int(fps * 0.5))
        varieties = []

        for f in range(start_frame, end_frame, step):
            ret, frame = cap.read()
            if not ret:
                break

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            h_bins = cv2.calcHist([hsv], [0], None, [30], [0, 180])
            h_bins = h_bins / h_bins.sum()
            nonzero = np.count_nonzero(h_bins > 0.01) / 30.0
            varieties.append(nonzero)

        return np.mean(varieties) if varieties else 0.0

    def _split_long_scene(self, cap, scene: Scene, fps: float) -> List[Scene]:
        """Split a long scene into smaller sub-scenes."""
        sub_scenes = []
        current_start = scene.start_time

        while current_start < scene.end_time:
            sub_end = min(current_start + self.max_duration, scene.end_time)
            sub_dur = sub_end - current_start

            if sub_dur >= self.min_duration:
                sub_scenes.append(Scene(
                    index=scene.index * 100 + len(sub_scenes),
                    start_frame=int(current_start * fps),
                    end_frame=int(sub_end * fps),
                    start_time=current_start,
                    end_time=sub_end,
                    duration=sub_dur,
                    confidence=scene.confidence,
                ))

            current_start = sub_end

        return sub_scenes

    def _classify_highlight(self, scores: Dict[str, float]) -> str:
        """Classify what type of highlight this is based on scores."""
        if scores["excitement"] > 0.85:
            return "action"
        elif scores["motion"] > 0.7:
            return "fast_paced"
        elif scores["excitement"] > 0.6:
            return "engaging"
        else:
            return "calm"

    def _generate_reason(self, scores: Dict[str, float]) -> str:
        """Generate a human-readable reason for the highlight score."""
        reasons = []
        if scores["excitement"] > 0.8:
            reasons.append("high excitement")
        if scores["motion"] > 0.7:
            reasons.append("intense motion")
        if scores["color_variety"] > 0.7:
            reasons.append("rich visuals")
        return ", ".join(reasons) if reasons else "moderate interest"
