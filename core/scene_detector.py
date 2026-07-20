"""
Scene Detector - Detects scene changes in gameplay videos.
Uses content-based analysis (histogram, motion) and optional audio analysis.
"""
import cv2
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
from utils.config_loader import config
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class Scene:
    """Represents a detected scene/cut in the video."""
    index: int
    start_frame: int
    end_frame: int
    start_time: float  # seconds
    end_time: float    # seconds
    duration: float    # seconds
    confidence: float  # 0-1 how confident this is a scene change
    scene_type: str = "unknown"  # filled by AI later
    description: str = ""

    def to_dict(self):
        return {
            "index": self.index,
            "start_time": f"{int(self.start_time//60):02d}:{int(self.start_time%60):02d}",
            "end_time": f"{int(self.end_time//60):02d}:{int(self.end_time%60):02d}",
            "duration": round(self.duration, 2),
            "confidence": round(self.confidence, 2),
            "scene_type": self.scene_type,
            "description": self.description,
        }


class SceneDetector:
    """Detects scene transitions in gameplay footage."""

    def __init__(self, threshold: Optional[float] = None, method: Optional[str] = None):
        self.threshold = threshold or config.get("scene_detection", "threshold", default=30.0)
        self.method = method or config.get("scene_detection", "method", default="hybrid")
        self.min_scene_length = config.get("scene_detection", "min_scene_length", default=3.0)

    def detect(self, video_path: Path) -> List[Scene]:
        """Main entry point - detect all scenes in a video."""
        log.info(f"Detecting scenes in {video_path.name}...")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        scenes = []
        prev_hist = None
        scene_start = 0
        scene_idx = 0

        frame_count = 0
        batch_size = int(fps * 0.5)  # Check every 0.5 seconds for performance
        ret = True

        while ret:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % batch_size == 0:
                current_time = frame_count / fps
                hist = self._calc_histogram(frame)

                if prev_hist is not None:
                    diff = self._histogram_diff(prev_hist, hist)

                    if self.method in ("content", "hybrid"):
                        if diff > self.threshold:
                            # End previous scene
                            scene_dur = current_time - scene_start
                            if scene_dur >= self.min_scene_length:
                                scenes.append(Scene(
                                    index=scene_idx,
                                    start_frame=int(scene_start * fps),
                                    end_frame=frame_count,
                                    start_time=scene_start,
                                    end_time=current_time,
                                    duration=scene_dur,
                                    confidence=min(diff / 100.0, 1.0),
                                ))
                                scene_idx += 1
                                scene_start = current_time

                prev_hist = hist

            frame_count += 1

        cap.release()

        # Add final scene
        if duration - scene_start >= self.min_scene_length:
            scenes.append(Scene(
                index=scene_idx,
                start_frame=int(scene_start * fps),
                end_frame=total_frames,
                start_time=scene_start,
                end_time=duration,
                duration=duration - scene_start,
                confidence=0.5,
            ))

        log.info(f"Detected {len(scenes)} scenes in {video_path.name}")
        return scenes

    def _calc_histogram(self, frame: np.ndarray) -> np.ndarray:
        """Calculate HSV histogram for a frame."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        return hist

    def _histogram_diff(self, h1: np.ndarray, h2: np.ndarray) -> float:
        """Calculate difference between two histograms."""
        diff = cv2.compareHist(h1, h2, cv2.HISTCMP_CHISQR)
        return diff

    def _detect_black_frames(self, frame: np.ndarray) -> bool:
        """Detect fade-to-black transitions."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        return mean_brightness < 15  # Very dark frame threshold
