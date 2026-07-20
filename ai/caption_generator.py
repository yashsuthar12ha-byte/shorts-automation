"""
Caption Generator - Creates and renders subtitles for Shorts.
Uses Whisper for speech-to-text and MoviePy/PIL for rendering.
"""
import json
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from utils.config_loader import config
from utils.file_utils import ensure_dir
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class CaptionSegment:
    """A single subtitle segment with timing and text."""
    start: float
    end: float
    text: str


class CaptionGenerator:
    """Generates and renders captions/subtitles for Shorts."""

    def __init__(self):
        self.enabled = config.get("captions", "enabled", default=True)
        self.position = config.get("captions", "position", default="bottom")
        self.font_size = config.get("captions", "font_size", default=36)
        self.font_color = config.get("captions", "font_color", default="white")
        self.stroke_color = config.get("captions", "stroke_color", default="black")
        self.stroke_width = config.get("captions", "stroke_width", default=2)
        self.animation = config.get("captions", "animation", default="typewriter")

    def transcribe(self, video_path: Path) -> List[CaptionSegment]:
        """Transcribe audio from video using Whisper."""
        log.info(f"Transcribing audio from {video_path.name}...")

        try:
            import whisper
            model_name = config.get("ai", "whisper", "model", default="base")
            model = whisper.load_model(model_name)
            result = model.transcribe(str(video_path), language="en")

            segments = []
            for seg in result.get("segments", []):
                segments.append(CaptionSegment(
                    start=seg["start"],
                    end=seg["end"],
                    text=seg["text"].strip(),
                ))

            log.info(f"Transcribed {len(segments)} segments")
            return segments

        except ImportError:
            log.warning("whisper not installed. Install with: pip install whisper-openai")
            return []
        except Exception as e:
            log.error(f"Transcription failed: {e}")
            return []

    def extract_words(self, segments: List[CaptionSegment]) -> List[CaptionSegment]:
        """Split segments into individual words with timing."""
        words = []
        for seg in segments:
            word_timing = self._estimate_word_timing(seg)
            words.extend(word_timing)
        return words

    def _estimate_word_timing(self, segment: CaptionSegment) -> List[CaptionSegment]:
        """Estimate per-word timing from a segment."""
        words = segment.text.split()
        if not words:
            return []

        duration = segment.end - segment.start
        word_duration = duration / max(len(words), 1)

        word_segments = []
        for i, word in enumerate(words):
            word_segments.append(CaptionSegment(
                start=segment.start + i * word_duration,
                end=segment.start + (i + 1) * word_duration,
                text=word,
            ))
        return word_segments

    def render_subtitles(self, video_path: Path, segments: List[CaptionSegment],
                         output_path: Path) -> Path:
        """Render subtitles onto the video using ffmpeg subtitles filter."""
        if not segments:
            log.info("No captions to render")
            return video_path

        try:
            srt_path = output_path.with_suffix(".srt")
            self._write_srt(segments, srt_path)

            import subprocess
            cmd = [
                "ffmpeg", "-y",
                "-i", str(video_path),
                "-vf", f"subtitles={srt_path}:force_style='FontSize={self.font_size},"
                       f"PrimaryColor=&H{self._color_to_bgr(self.font_color)},"
                       f"OutlineColor=&H{self._color_to_bgr(self.stroke_color)},"
                       f"Outline={self.stroke_width},"
                       f"BorderStyle=1'",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "22",
                "-c:a", "copy",
                str(output_path),
            ]
            subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            log.info(f"Subtitles rendered to {output_path.name}")
            return output_path

        except Exception as e:
            log.error(f"Subtitle rendering failed: {e}")
            return video_path

    def _write_srt(self, segments: List[CaptionSegment], path: Path) -> None:
        """Write segments to SRT subtitle format."""
        def format_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds % 1) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        with open(path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                f.write(f"{i}\n")
                f.write(f"{format_time(seg.start)} --> {format_time(seg.end)}\n")
                f.write(f"{seg.text}\n\n")

    def _color_to_bgr(self, color_name: str) -> str:
        """Convert named color to BGR hex for ffmpeg subtitles."""
        colors = {
            "white": "FFFFFF",
            "black": "000000",
            "yellow": "00FFFF",
            "red": "0000FF",
            "cyan": "FFFF00",
            "green": "00FF00",
        }
        return colors.get(color_name.lower(), "FFFFFF")
