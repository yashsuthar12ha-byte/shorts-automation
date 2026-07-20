"""
Tests for the pipeline workflow.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pipeline.workflow import Pipeline, PipelineResult
from core.scene_detector import Scene
from core.highlight_analyzer import Highlight
from core.clip_extractor import ExtractedClip


class TestPipeline:
    """Test suite for the Pipeline orchestrator."""

    def test_pipeline_result_defaults(self):
        """Test PipelineResult default values."""
        result = PipelineResult(video_path=Path("test.mp4"), game_name="TestGame")
        assert result.clips_created == 0
        assert result.clips == []
        assert result.titles == []
        assert result.uploaded_ids == []
        assert result.errors == []

    def test_pipeline_result_to_dict(self):
        """Test PipelineResult serialization."""
        result = PipelineResult(
            video_path=Path("test.mp4"),
            game_name="TestGame",
            clips_created=3,
            clips=[Mock(), Mock(), Mock()],
            uploaded_ids=["vid1", "vid2"],
        )
        d = result.to_dict()
        assert d["game"] == "TestGame"
        assert d["clips"] == 3
        assert d["uploaded"] == 2

    def test_pipeline_result_with_errors(self):
        """Test PipelineResult with errors."""
        result = PipelineResult(
            video_path=Path("test.mp4"),
            game_name="Test",
            errors=["error1", "error2"],
        )
        assert len(result.errors) == 2
        d = result.to_dict()
        assert d["errors"] == 2

    @patch("pipeline.workflow.Pipeline._resolve_video")
    def test_pipeline_no_video(self, mock_resolve):
        """Test pipeline fails gracefully with no video."""
        mock_resolve.return_value = None
        pipeline = Pipeline(dry_run=True)
        result = pipeline.run()
        assert len(result.errors) > 0

    @patch("pipeline.workflow.VideoProcessor.get_metadata")
    @patch("pipeline.workflow.Pipeline._resolve_video")
    def test_pipeline_invalid_video(self, mock_resolve, mock_metadata):
        """Test pipeline handles invalid video."""
        mock_resolve.return_value = Path("test.mp4")
        from media.video_processor import VideoMetadata
        mock_metadata.return_value = VideoMetadata(
            path=Path("test.mp4"), filename="test.mp4",
            duration=5.0, width=100, height=100, fps=30,
            codec="h264", bitrate=1000, file_size_mb=1.0, has_audio=False,
        )
        pipeline = Pipeline(dry_run=True)
        with patch.object(pipeline.video_processor, "is_valid_for_shorts", return_value=False):
            result = pipeline.run()
            assert len(result.errors) > 0


class TestPipelineResult:
    """Test PipelineResult edge cases."""

    def test_empty_clips(self):
        result = PipelineResult(video_path=Path("test.mp4"), game_name="Game")
        assert result.clips_created == 0

    def test_large_result(self):
        clips = [ExtractedClip(
            path=Path(f"clip_{i}.mp4"),
            highlight=Highlight(
                index=i, scene=Scene(i, 0, 300, 0.0, 10.0, 10.0, 0.8),
                start_time=0.0, end_time=10.0, duration=10.0, score=0.9
            ),
            duration=10.0, file_size_mb=5.0,
        ) for i in range(10)]
        result = PipelineResult(
            video_path=Path("test.mp4"),
            game_name="Test",
            clips=clips,
            clips_created=10,
            titles=["Title 1", "Title 2"],
            hashtags=["#gaming", "#shorts"],
            uploaded_ids=["id1", "id2"],
        )
        assert result.clips_created == 10
        assert len(result.uploaded_ids) == 2
