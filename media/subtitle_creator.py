"""
Subtitle Creator - Creates styled subtitles and synchronizes them with video.
Provides multiple subtitle format outputs (SRT, ASS) and rendering.
"""
from pathlib import Path
from typing import List, Optional
from ai.caption_generator import CaptionSegment, CaptionGenerator
from utils.config_loader import config
from utils.file_utils import ensure_dir
from utils.logger import get_logger

log = get_logger(__name__)


class SubtitleCreator:
    """Creates and styles subtitles for Shorts with multiple format support."""

    def __init__(self):
        self.enabled = config.get("captions", "enabled", default=True)
        self.animation = config.get("captions", "animation", default="typewriter")
        self.max_words_per_line = config.get("captions", "max_words_per_line", default=4)
        self.position = config.get("captions", "position", default="bottom")
        self.output_dir = config.output_dir / "subtitles"
        ensure_dir(self.output_dir)

    def create_subtitles(self, segments: List[CaptionSegment],
                         video_stem: str) -> List[Path]:
        """Create subtitle files in multiple formats."""
        if not self.enabled or not segments:
            return []

        files = []
        try:
            # SRT format
            srt_path = self.output_dir / f"{video_stem}.srt"
            self._write_srt(segments, srt_path)
            files.append(srt_path)

            # ASS format (better styling)
            ass_path = self.output_dir / f"{video_stem}.ass"
            self._write_ass(segments, ass_path)
            files.append(ass_path)

            log.info(f"Created {len(files)} subtitle files for {video_stem}")
        except Exception as e:
            log.error(f"Subtitle creation failed: {e}")

        return files

    def _write_srt(self, segments: List[CaptionSegment], path: Path) -> None:
        """Write subtitle segments in SRT format."""
        def fmt_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = int(seconds % 60)
            ms = int((seconds % 1) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        with open(path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                f.write(f"{i}\n")
                f.write(f"{fmt_time(seg.start)} --> {fmt_time(seg.end)}\n")

                # Split into lines by max words
                words = seg.text.split()
                lines = []
                for j in range(0, len(words), self.max_words_per_line):
                    lines.append(" ".join(words[j:j + self.max_words_per_line]))
                f.write("\n".join(lines) + "\n\n")

    def _write_ass(self, segments: List[CaptionSegment], path: Path) -> None:
        """Write subtitle segments in ASS format (better styling)."""
        position_map = {
            "bottom": "Alignment=2",
            "top": "Alignment=8",
            "center": "Alignment=5",
        }
        alignment = position_map.get(self.position, "Alignment=2")

        def fmt_time(seconds: float) -> str:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            s = seconds % 60
            return f"{h:01d}:{m:02d}:{s:05.2f}"

        with open(path, "w", encoding="utf-8") as f:
            # ASS header
            f.write("[Script Info]\n")
            f.write("ScriptType: v4.00+\n")
            f.write("PlayResX: 1080\n")
            f.write("PlayResY: 1920\n")
            f.write("ScaledBorderAndShadow: yes\n\n")

            # Style definition
            font_size = config.get("captions", "font_size", default=36)
            font_color = config.get("captions", "font_color", default="white")
            stroke_color = config.get("captions", "stroke_color", default="black")
            stroke_width = config.get("captions", "stroke_width", default=2)

            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, "
                    "OutlineColour, BackColour, Bold, Italic, Underline, "
                    "StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, "
                    "Outline, Shadow, {alignment}, MarginL, MarginR, MarginV, Encoding\n")
            f.write(f"Style: Default,Arial,{font_size},&H00FFFFFF,"
                    f"&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,"
                    f"{stroke_width},0,2,30,30,30,1\n\n")

            # Events
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

            for i, seg in enumerate(segments):
                words = seg.text.split()
                lines = []
                for j in range(0, len(words), self.max_words_per_line):
                    lines.append(" ".join(words[j:j + self.max_words_per_line]))

                text = "\\N".join(lines)
                f.write(f"Dialogue: 0,{fmt_time(seg.start)},{fmt_time(seg.end)},"
                        f"Default,,0,0,0,,{text}\n")

    def render_to_video(self, video_path: Path, subtitles_path: Path,
                         output_path: Path) -> Path:
        """Render subtitles onto video using ffmpeg."""
        import subprocess
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"subtitles={subtitles_path}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "copy",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return output_path
