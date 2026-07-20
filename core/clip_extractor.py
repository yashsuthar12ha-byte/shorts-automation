"""
Clip Extractor - Extracts the best clips from source video based on highlights.
Handles cropping to 9:16 portrait, transitions, and audio mixing.
"""
import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from core.highlight_analyzer import Highlight
from utils.config_loader import config
from utils.file_utils import ensure_dir, sanitize_filename
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class ExtractedClip:
    """Represents a successfully extracted clip."""
    path: Path
    highlight: Highlight
    duration: float
    file_size_mb: float


class ClipExtractor:
    """Extracts and processes highlight clips from source video."""

    def __init__(self):
        self.output_dir = config.output_dir / "clips"
        self.temp_dir = config.temp_dir
        self.target_duration = config.get("shorts", "target_duration_seconds", default=58)
        self.resolution = config.get("shorts", "resolution", default=[1080, 1920])
        self.fps = config.get("shorts", "fps", default=30)
        self.use_ffmpeg = True  # Prefer ffmpeg for performance

        ensure_dir(self.output_dir)
        ensure_dir(self.temp_dir)

    def extract(self, video_path: Path, highlights: List[Highlight], game_name: str = "") -> List[ExtractedClip]:
        """Extract all highlight clips and crop to portrait mode."""
        log.info(f"Extracting {len(highlights)} clips from {video_path.name}...")
        clips = []

        for i, highlight in enumerate(highlights):
            output_filename = f"{sanitize_filename(game_name or 'clip')}_highlight_{i+1:02d}.mp4"
            output_path = self.output_dir / output_filename

            try:
                clip = self._extract_single(
                    video_path, highlight, output_path, game_name
                )
                clips.append(clip)
                log.info(f"  Created: {output_filename} ({clip.duration:.1f}s)")
            except Exception as e:
                log.error(f"  Failed to extract highlight {i}: {e}")

        return clips

    def _extract_single(self, video_path: Path, highlight: Highlight,
                        output_path: Path, game_name: str) -> ExtractedClip:
        """Extract a single clip using ffmpeg with center-crop to 9:16."""
        # Clamp to target duration
        start = highlight.start_time
        duration = min(highlight.duration, self.target_duration)

        # If clip is too short, pad by extending start
        if duration < 15:
            extra = (15 - duration) / 2
            start = max(0, start - extra)
            duration = min(15, highlight.end_time - start)

        width, height = self.resolution

        # ffmpeg command: extract, crop to portrait, scale to target
        cmd = [
            "ffmpeg",
            "-y",  # Overwrite output
            "-ss", str(start),
            "-i", str(video_path),
            "-t", str(duration),
            "-vf", f"crop=ih*9/16:ih,scale={width}:{height}",
            "-r", str(self.fps),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_path),
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr[:500]}")

        # Get file size
        size_mb = output_path.stat().st_size / (1024 * 1024)

        return ExtractedClip(
            path=output_path,
            highlight=highlight,
            duration=duration,
            file_size_mb=round(size_mb, 2),
        )

    def crop_to_portrait(self, input_path: Path, output_path: Path) -> Path:
        """Center-crop video to 9:16 portrait aspect ratio."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", "crop=ih*9/16:ih",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return output_path

    def cleanup(self):
        """Remove temporary files."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            ensure_dir(self.temp_dir)
