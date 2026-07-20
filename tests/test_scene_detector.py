"""
Tests for the Scene Detector module.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
import numpy as np
import cv2
from core.scene_detector import SceneDetector, Scene


class TestSceneDetector:
    """Test suite for SceneDetector."""

    def setup_method(self):
        self.detector = SceneDetector(threshold=30.0)

    def test_scene_dataclass(self):
        """Test Scene dataclass creation and to_dict."""
        scene = Scene(
            index=0,
            start_frame=0,
            end_frame=300,
            start_time=0.0,
            end_time=10.0,
            duration=10.0,
            confidence=0.85,
        )
        assert scene.index == 0
        assert scene.duration == 10.0
        assert scene.confidence == 0.85

        d = scene.to_dict()
        assert d["start_time"] == "00:00"
        assert d["end_time"] == "00:10"
        assert d["duration"] == 10.0

    def test_histogram_calculation(self):
        """Test histogram calculation with synthetic frame."""
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        hist = self.detector._calc_histogram(frame)
        assert hist is not None
        assert hist.shape == (50, 60)
        assert np.isclose(hist.sum(), 1.0, atol=0.1)

    def test_histogram_diff_same(self):
        """Test that identical frames have low difference."""
        frame = np.ones((100, 100, 3), dtype=np.uint8) * 128
        h1 = self.detector._calc_histogram(frame)
        h2 = self.detector._calc_histogram(frame)
        diff = self.detector._histogram_diff(h1, h2)
        assert diff < 1.0  # Very similar

    def test_histogram_diff_different(self):
        """Test that different frames have higher difference."""
        frame1 = np.ones((100, 100, 3), dtype=np.uint8) * 0  # Black
        frame2 = np.ones((100, 100, 3), dtype=np.uint8) * 255  # White
        h1 = self.detector._calc_histogram(frame1)
        h2 = self.detector._calc_histogram(frame2)
        diff = self.detector._histogram_diff(h1, h2)
        assert diff > 1.0  # Very different

    def test_black_frame_detection(self):
        """Test black frame detection."""
        black = np.zeros((100, 100, 3), dtype=np.uint8)
        assert self.detector._detect_black_frames(black)

        white = np.ones((100, 100, 3), dtype=np.uint8) * 255
        assert not self.detector._detect_black_frames(white)

    def test_detect_on_synthetic_video(self, tmp_path):
        """Test scene detection on a synthetic video with known scene changes."""
        video_path = tmp_path / "test_video.mp4"
        self._create_synthetic_video(video_path)

        scenes = self.detector.detect(video_path)
        assert len(scenes) > 0
        assert all(isinstance(s, Scene) for s in scenes)

    def _create_synthetic_video(self, path: Path, duration: float = 10.0,
                                 fps: float = 30, width: int = 640, height: int = 480):
        """Create a synthetic test video with one scene change."""
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(path), fourcc, fps, (width, height))

        # First half: red frames
        for _ in range(int(fps * duration / 2)):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:, :] = [0, 0, 255]  # Red
            out.write(frame)

        # Second half: blue frames (scene change)
        for _ in range(int(fps * duration / 2)):
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:, :] = [255, 0, 0]  # Blue
            out.write(frame)

        out.release()


class TestScene:
    """Test Scene class edge cases."""

    def test_zero_duration(self):
        scene = Scene(0, 0, 0, 0.0, 0.0, 0.0, 0.0)
        assert scene.duration == 0.0

    def test_long_duration(self):
        scene = Scene(0, 0, 18000, 0.0, 600.0, 600.0, 0.9)
        assert scene.duration == 600.0
        assert scene.to_dict()["start_time"] == "00:00"
        assert scene.to_dict()["end_time"] == "10:00"
