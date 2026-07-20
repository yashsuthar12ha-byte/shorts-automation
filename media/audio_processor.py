"""
Audio Processor - Handles audio extraction, analysis, and background music.
Provides volume adjustments and audio level detection for highlight scoring.
"""
import subprocess
import numpy as np
from pathlib import Path
from typing import Optional, List
from utils.config_loader import config
from utils.file_utils import ensure_dir
from utils.logger import get_logger

log = get_logger(__name__)


class AudioProcessor:
    """Processes audio tracks for Shorts generation."""

    def __init__(self):
        self.temp_dir = Path(config.get("general", "temp_dir", default="output/temp"))
        ensure_dir(self.temp_dir)
        self.music_dir = Path(config.get("shorts", "background_music", "library_dir",
                                          default="output/music"))
        ensure_dir(self.music_dir)

    def extract_audio(self, video_path: Path, output_path: Optional[Path] = None) -> Optional[Path]:
        """Extract audio track from video file."""
        if output_path is None:
            output_path = self.temp_dir / f"{video_path.stem}_audio.wav"

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # WAV format
            "-ar", "16000",  # 16kHz for Whisper
            "-ac", "1",  # Mono
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and output_path.exists():
            return output_path
        log.warning(f"Audio extraction failed for {video_path.name}")
        return None

    def detect_audio_peaks(self, audio_path: Path) -> List[dict]:
        """Detect peaks in audio as indicators of exciting moments."""
        try:
            import librosa
            y, sr = librosa.load(str(audio_path), sr=16000)

            # Calculate energy in windows
            hop_length = int(sr * 0.5)  # 0.5 second windows
            energy = np.array([
                np.sum(np.abs(y[i:i+hop_length])**2)
                for i in range(0, len(y), hop_length)
            ])

            # Normalize
            energy = energy / max(energy.max(), 1e-10)

            # Find peaks above threshold
            threshold = config.get("highlight_detection", "excitement_threshold", default=0.7)
            peaks = []
            for i, e in enumerate(energy):
                if e > threshold:
                    peaks.append({
                        "time": i * 0.5,
                        "energy": float(e),
                        "duration": 0.5,
                    })

            log.info(f"Found {len(peaks)} audio peaks")
            return peaks

        except ImportError:
            log.warning("librosa not available for audio peak detection")
            return []
        except Exception as e:
            log.warning(f"Audio peak detection failed: {e}")
            return []

    def add_background_music(self, video_path: Path, output_path: Path,
                              music_volume: Optional[float] = None) -> Path:
        """Add background music to a video at a lower volume."""
        music_volume = music_volume or config.get("shorts", "background_music", "volume",
                                                   default=0.15)

        music_files = self._get_music_files()
        if not music_files:
            log.info("No background music files found, skipping")
            return video_path

        import random
        music_path = random.choice(music_files)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(music_path),
            "-filter_complex",
            f"[1:a]volume={music_volume}[music];"
            f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and output_path.exists():
            log.info(f"Background music added to {output_path.name}")
            return output_path

        log.warning("Failed to add background music")
        return video_path

    def _get_music_files(self) -> List[Path]:
        """Get list of available background music files."""
        if not self.music_dir.exists():
            return []
        music_files = []
        for ext in [".mp3", ".wav", ".m4a", ".ogg"]:
            music_files.extend(self.music_dir.glob(f"*{ext}"))
        return music_files

    def adjust_audio_volume(self, video_path: Path, output_path: Path,
                             volume: float = 1.0) -> Path:
        """Adjust the audio volume of a video."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-af", f"volume={volume}",
            "-c:v", "copy",
            str(output_path),
        ]
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return output_path
