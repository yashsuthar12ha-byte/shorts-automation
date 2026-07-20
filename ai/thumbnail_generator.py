"""
Thumbnail Generator - Creates eye-catching thumbnails for Shorts.
Uses Pillow for image processing and compositing.
"""
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import random
from utils.config_loader import config
from utils.file_utils import ensure_dir, sanitize_filename
from utils.logger import get_logger

log = get_logger(__name__)


class ThumbnailGenerator:
    """Creates engaging thumbnails for YouTube Shorts."""

    def __init__(self):
        self.enabled = config.get("thumbnail", "enabled", default=True)
        self.style = config.get("thumbnail", "style", default="dynamic")
        self.text_overlay = config.get("thumbnail", "text_overlay", default=True)
        self.font_color = config.get("thumbnail", "font_color", default="white")
        self.bg_color = config.get("thumbnail", "background_color", default="black")
        self.output_dir = config.output_dir / "thumbnails"
        ensure_dir(self.output_dir)

    def generate(self, video_path: Path, title: str = "",
                 game_name: str = "") -> Optional[Path]:
        """Generate a thumbnail from the video's most interesting frame."""
        if not self.enabled:
            return None

        log.info(f"Generating thumbnail for {video_path.name}...")

        try:
            thumbnail_path = self.output_dir / f"{video_path.stem}_thumb.jpg"

            # Extract a frame from the video at ~30% in (often a good spot)
            from moviepy.video.io.VideoFileClip import VideoFileClip
            clip = VideoFileClip(str(video_path))
            duration = clip.duration

            # Try multiple positions and pick the most interesting frame
            positions = [duration * 0.2, duration * 0.3, duration * 0.5, duration * 0.7]
            best_frame = None
            best_score = -1

            for pos in positions:
                if pos < duration:
                    frame = clip.get_frame(pos)
                    score = self._score_frame_interest(frame)
                    if score > best_score:
                        best_score = score
                        best_frame = frame

            clip.close()

            if best_frame is None:
                return None

            # Convert to PIL Image
            img = Image.fromarray(best_frame)

            # Resize to 9:16 portrait
            img = self._resize_for_thumbnail(img)

            # Enhance
            img = self._enhance_image(img)

            # Add text overlay
            if self.text_overlay and title:
                img = self._add_text_overlay(img, title, game_name)

            # Save
            img.save(str(thumbnail_path), "JPEG", quality=90)
            log.info(f"Thumbnail saved: {thumbnail_path.name}")

            return thumbnail_path

        except Exception as e:
            log.error(f"Thumbnail generation failed: {e}")
            return None

    def _resize_for_thumbnail(self, img: Image.Image) -> Image.Image:
        """Resize to 1080x1920 maintaining aspect ratio with crop."""
        target = (1080, 1920)
        img_ratio = img.width / img.height
        target_ratio = target[0] / target[1]

        if img_ratio > target_ratio:
            # Wider than target - crop sides
            new_height = target[1]
            new_width = int(new_height * img_ratio)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            left = (img.width - target[0]) // 2
            img = img.crop((left, 0, left + target[0], target[1]))
        else:
            # Taller than target - crop top/bottom
            new_width = target[0]
            new_height = int(new_width / img_ratio)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            top = 0
            img = img.crop((0, top, target[0], top + target[1]))

        return img

    def _enhance_image(self, img: Image.Image) -> Image.Image:
        """Enhance image contrast, saturation, and sharpness."""
        # Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.2)

        # Increase saturation
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.3)

        # Increase sharpness
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)

        return img

    def _add_text_overlay(self, img: Image.Image, title: str,
                          game_name: str) -> Image.Image:
        """Add text overlay to thumbnail."""
        draw = ImageDraw.Draw(img)
        w, h = img.size

        # Try to load a nice font, fall back to default
        font_large = None
        font_small = None
        for font_path in [
            "C:\\Windows\\Fonts\\impact.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]:
            try:
                font_large = ImageFont.truetype(font_path, 120)
                font_small = ImageFont.truetype(font_path, 60)
                break
            except (IOError, OSError):
                continue

        if font_large is None:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Semi-transparent gradient overlay at bottom
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        for i in range(h // 3):
            alpha = int(180 * (1 - i / (h // 3)))
            overlay_draw.line([(0, h - i), (w, h - i)], fill=(0, 0, 0, alpha))
        img = Image.alpha_composite(img.convert("RGBA"), overlay)
        draw = ImageDraw.Draw(img)

        # Game name (small, top-left area)
        if game_name:
            game_text = game_name.upper()
            bbox = draw.textbbox((0, 0), game_text, font=font_small)
            tw = bbox[2] - bbox[0]
            draw.text(
                ((w - tw) // 2, h - 200),
                game_text,
                font=font_small,
                fill=(255, 255, 255),
                stroke_width=3,
                stroke_color="black",
            )

        # Title (large, centered at bottom)
        short_title = title[:50] if len(title) > 50 else title
        bbox = draw.textbbox((0, 0), short_title, font=font_large)
        tw = bbox[2] - bbox[0]
        draw.text(
            ((w - tw) // 2, h - 330),
            short_title,
            font=font_large,
            fill=(255, 255, 50),
            stroke_width=4,
            stroke_color="black",
        )

        return img

    def _score_frame_interest(self, frame) -> float:
        """Score a frame by visual interest (brightness, contrast, color)."""
        import numpy as np
        gray = frame.mean(axis=2) if frame.ndim == 3 else frame
        brightness = gray.mean() / 255.0
        contrast = gray.std() / 255.0

        if frame.ndim == 3:
            color_std = frame.std(axis=(0, 1)).mean() / 255.0
        else:
            color_std = 0

        # Score: prefer well-lit frames with good contrast and color
        return (1 - abs(brightness - 0.5)) * 0.3 + contrast * 0.4 + color_std * 0.3
