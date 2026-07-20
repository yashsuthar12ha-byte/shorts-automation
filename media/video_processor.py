"""
Video Processor - Handles video file operations and transformations.
Provides metadata extraction, format conversion, and quality analysis.
"""
import subprocess
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from utils.config_loader import config
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class VideoMetadata:
    """Extracted video metadata."""
    path: Path
    filename: str
    duration: float  # seconds
    width: int
    height: int
    fps: float
    codec: str
    bitrate: int
    file_size_mb: float
    has_audio: bool


class VideoProcessor:
    """Processes and analyzes video files."""

    def __init__(self):
        self.supported_formats = config.get("video_input", "supported_formats",
                                            default=[".mp4", ".mov", ".avi", ".mkv", ".webm"])

    def get_metadata(self, video_path: Path) -> VideoMetadata:
        """Extract comprehensive metadata from a video file using ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)

        # Get video stream info
        video_stream = None
        audio_stream = None
        for stream in data.get("streams", []):
            if stream["codec_type"] == "video" and video_stream is None:
                video_stream = stream
            elif stream["codec_type"] == "audio" and audio_stream is None:
                audio_stream = stream

        width = int(video_stream.get("width", 0)) if video_stream else 0
        height = int(video_stream.get("height", 0)) if video_stream else 0
        fps_str = video_stream.get("r_frame_rate", "30/1") if video_stream else "30/1"
        num, den = fps_str.split("/")
        fps = float(num) / float(den) if float(den) > 0 else 30.0

        format_info = data.get("format", {})
        duration = float(format_info.get("duration", 0))
        bitrate = int(format_info.get("bit_rate", 0))
        size_bytes = int(format_info.get("size", 0))
        file_size_mb = size_bytes / (1024 * 1024)

        return VideoMetadata(
            path=video_path,
            filename=video_path.name,
            duration=duration,
            width=width,
            height=height,
            fps=fps,
            codec=video_stream.get("codec_name", "unknown") if video_stream else "unknown",
            bitrate=bitrate,
            file_size_mb=round(file_size_mb, 2),
            has_audio=audio_stream is not None,
        )

    def is_valid_for_shorts(self, metadata: VideoMetadata) -> bool:
        """Check if a video is suitable for Shorts generation."""
        if metadata.duration < 15:
            log.warning(f"{metadata.filename}: too short ({metadata.duration:.1f}s)")
            return False
        if metadata.duration > 7200:  # 2 hours max
            log.warning(f"{metadata.filename}: too long ({metadata.duration/60:.1f}min)")
            return False
        if metadata.file_size_mb > 5000:  # 5GB max
            log.warning(f"{metadata.filename}: too large ({metadata.file_size_mb:.0f}MB)")
            return False
        return True

    def list_input_videos(self) -> List[Path]:
        """List all supported video files in the input directory."""
        input_dir = Path(config.get("video_input", "input_dir", default="sample_data"))
        videos = []
        if input_dir.exists():
            for f in input_dir.iterdir():
                if f.suffix.lower() in self.supported_formats:
                    videos.append(f)
        return sorted(videos)

    def detect_game_name(self, video_path: Path) -> str:
        """Try to detect the game name from the filename."""
        import re
        name = video_path.stem
        # Remove common suffixes
        name = re.sub(r"[-_\s]*(gameplay|walkthrough|part\d|1080p|60fps|pc|ps5|ps4|xbox)"
                      r"[-_\s]*", " ", name, flags=re.IGNORECASE)
        name = re.sub(r"\s+", " ", name).strip()
        return name or "AAA Game"
