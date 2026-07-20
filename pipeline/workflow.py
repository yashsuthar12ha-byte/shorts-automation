"""
Workflow Engine - Orchestrates the full pipeline from video input to YouTube upload.
This is the main coordinator that ties all modules together.
"""
import os
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from dataclasses import dataclass, field

from core.scene_detector import SceneDetector, Scene
from core.highlight_analyzer import HighlightAnalyzer, Highlight
from core.clip_extractor import ClipExtractor, ExtractedClip

from ai.content_analyzer import AIContentAnalyzer
from ai.caption_generator import CaptionGenerator
from ai.title_generator import TitleGenerator
from ai.hashtag_generator import HashtagGenerator
from ai.thumbnail_generator import ThumbnailGenerator

from media.video_processor import VideoProcessor
from media.audio_processor import AudioProcessor
from media.subtitle_creator import SubtitleCreator

from youtube.uploader import YouTubeUploader
from youtube.scheduler import UploadScheduler
from youtube.analytics import AnalyticsTracker

from utils.config_loader import config
from utils.file_utils import ensure_dir, get_timestamp
from utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class PipelineResult:
    """Result of a single pipeline run."""
    video_path: Path = Path("")
    game_name: str = ""
    clips_created: int = 0
    clips: List[ExtractedClip] = field(default_factory=list)
    titles: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)
    thumbnail_paths: List[Path] = field(default_factory=list)
    uploaded_ids: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0

    def to_dict(self):
        return {
            "video": str(self.video_path),
            "game": self.game_name,
            "clips": len(self.clips),
            "uploaded": len(self.uploaded_ids),
            "errors": len(self.errors),
            "duration_seconds": round(self.duration_seconds, 1),
        }


class Pipeline:
    """
    Main pipeline that orchestrates the complete workflow:
    1. Load & analyze video
    2. Detect scenes
    3. Find highlights
    4. Extract clips
    5. Generate captions
    6. Generate titles
    7. Generate hashtags
    8. Create thumbnails
    9. Upload to YouTube (optional)
    10. Schedule next upload
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run or os.getenv("AI_GAME_SHORTS_DRY_RUN", "false").lower() == "true"
        self.start_time = datetime.now()

        # Initialize all modules
        self.video_processor = VideoProcessor()
        self.scene_detector = SceneDetector()
        self.highlight_analyzer = HighlightAnalyzer()
        self.clip_extractor = ClipExtractor()
        self.ai_analyzer = AIContentAnalyzer()
        self.caption_generator = CaptionGenerator()
        self.title_generator = TitleGenerator()
        self.hashtag_generator = HashtagGenerator()
        self.thumbnail_generator = ThumbnailGenerator()
        self.audio_processor = AudioProcessor()
        self.subtitle_creator = SubtitleCreator()
        self.youtube_uploader = YouTubeUploader()
        self.scheduler = UploadScheduler()
        self.analytics = AnalyticsTracker()

        # State
        self.current_game_name = ""
        self.video_metadata = None

        self._init_output()

    def _init_output(self):
        """Initialize output directories."""
        for subdir in ["clips", "subtitles", "thumbnails", "music", "temp"]:
            ensure_dir(config.output_dir / subdir)

    def run(self, video_path: Optional[Path] = None) -> PipelineResult:
        """
        Run the complete pipeline on a video.
        If no video_path is given, processes the first available video.
        """
        self.start_time = datetime.now()
        result = PipelineResult(video_path=video_path or Path(""))

        try:
            # 1. Find and validate video
            video_path = self._resolve_video(video_path)
            if not video_path:
                result.errors.append("No video files found")
                return result

            result.video_path = video_path
            log.info(f"{'='*60}")
            log.info(f"Starting pipeline for: {video_path.name}")
            log.info(f"{'='*60}")

            # 2. Get video info
            self.video_metadata = self.video_processor.get_metadata(video_path)
            self.current_game_name = self.video_processor.detect_game_name(video_path)
            result.game_name = self.current_game_name

            if not self.video_processor.is_valid_for_shorts(self.video_metadata):
                result.errors.append("Video not suitable for Shorts")
                return result

            log.info(f"  Game detected: {self.current_game_name}")
            log.info(f"  Duration: {self.video_metadata.duration:.0f}s")
            log.info(f"  Resolution: {self.video_metadata.width}x{self.video_metadata.height}")

            # 3. Detect scenes
            log.info(f"\n{'─'*40}")
            log.info("STEP 1: Scene Detection")
            scenes = self.scene_detector.detect(video_path)
            if not scenes:
                result.errors.append("No scenes detected")
                return result
            log.info(f"  Found {len(scenes)} scenes")

            # 4. AI scene analysis (optional)
            if self.ai_analyzer.is_available():
                log.info("  Running AI scene analysis...")
                scenes = self.ai_analyzer.analyze_scenes(scenes, self.current_game_name)

            # 5. Find highlights
            log.info(f"\n{'─'*40}")
            log.info("STEP 2: Highlight Detection")
            highlights = self.highlight_analyzer.analyze(video_path, scenes)
            if not highlights:
                result.errors.append("No highlights detected")
                return result
            log.info(f"  Found {len(highlights)} highlights")

            # 6. AI highlight selection
            if self.ai_analyzer.is_available():
                log.info("  Running AI highlight selection...")
                highlights = self.ai_analyzer.select_best_highlights(
                    highlights, self.current_game_name,
                    config.get("highlight_detection", "max_highlights_per_video", default=5)
                )

            # 7. Extract clips
            log.info(f"\n{'─'*40}")
            log.info("STEP 3: Clip Extraction")
            clips = self.clip_extractor.extract(video_path, highlights, self.current_game_name)
            if not clips:
                result.errors.append("No clips extracted")
                return result
            result.clips = clips
            result.clips_created = len(clips)
            log.info(f"  Extracted {len(clips)} clips")

            # 8. Process each clip
            for i, clip in enumerate(clips):
                log.info(f"\n{'─'*30}")
                log.info(f"Processing clip {i+1}/{len(clips)}")

                # 8a. Add captions / transcribe
                log.info("  Generating captions...")
                segments = self.caption_generator.transcribe(clip.path)

                if segments:
                    # Create subtitle files
                    self.subtitle_creator.create_subtitles(segments, clip.path.stem)

                    # Render subtitles onto video
                    subtitled_path = config.output_dir / "temp" / f"sub_{clip.path.name}"
                    self.caption_generator.render_subtitles(clip.path, segments, subtitled_path)
                    if subtitled_path.exists() and subtitled_path.stat().st_size > 0:
                        # Replace clip with subtitled version
                        import shutil
                        shutil.move(str(subtitled_path), str(clip.path))
                        log.info("  Subtitles rendered onto clip")

                # 8b. Add background music
                music_enabled = config.get("shorts", "background_music", "enabled", default=True)
                if music_enabled:
                    log.info("  Adding background music...")
                    music_path = config.output_dir / "temp" / f"music_{clip.path.name}"
                    result_path = self.audio_processor.add_background_music(clip.path, music_path)
                    if result_path != clip.path and result_path.exists():
                        import shutil
                        shutil.move(str(result_path), str(clip.path))
                        log.info("  Background music added")

                # 8c. Generate title & hashtags (once per clip)
                log.info("  Generating title...")
                titles = self.title_generator.generate(
                    game_name=self.current_game_name,
                    scene_description=clip.highlight.reason,
                    scene_type=clip.highlight.highlight_type,
                    excitement=int(clip.highlight.excitement_score * 10),
                )
                result.titles = titles

                log.info("  Generating hashtags...")
                hashtags = self.hashtag_generator.generate(
                    game_name=self.current_game_name,
                    scene_description=clip.highlight.reason,
                    scene_type=clip.highlight.highlight_type,
                )
                result.hashtags = hashtags

                log.info(f"  Title: {titles[0] if titles else 'N/A'}")
                log.info(f"  Hashtags: {' '.join(hashtags[:3])}...")

                # 8d. Generate thumbnail
                log.info("  Creating thumbnail...")
                best_title = self.title_generator.pick_best(titles)
                thumb_path = self.thumbnail_generator.generate(
                    clip.path, best_title, self.current_game_name
                )
                if thumb_path:
                    result.thumbnail_paths.append(thumb_path)

                # 8e. Upload to YouTube
                if not self.dry_run:
                    log.info("  Uploading to YouTube...")
                    video_id = self.youtube_uploader.upload_short(
                        video_path=clip.path,
                        title=best_title,
                        description=f"Amazing {self.current_game_name} gameplay moment!",
                        hashtags=self.hashtag_generator.format_tags(hashtags),
                        thumbnail_path=thumb_path,
                    )
                    if video_id:
                        result.uploaded_ids.append(video_id)
                        self.scheduler.mark_completed({
                            "title": best_title,
                            "video_id": video_id,
                            "game": self.current_game_name,
                        })
                        log.info(f"  Uploaded: https://youtu.be/{video_id}")
                else:
                    log.info(f"  [DRY RUN] Would upload: {best_title}")

            # 9. Calculate analytics and generate insights
            if result.uploaded_ids:
                log.info(f"\n{'─'*40}")
                log.info("Generating analytics insights...")
                self.analytics.fetch_all_performance()
                self.analytics.generate_insights()

            # 10. Summary
            result.duration_seconds = (datetime.now() - self.start_time).total_seconds()
            self._print_summary(result)

            return result

        except Exception as e:
            log.error(f"Pipeline failed: {e}")
            import traceback
            log.error(traceback.format_exc())
            result.errors.append(str(e))
            return result

    def _resolve_video(self, video_path: Optional[Path] = None) -> Optional[Path]:
        """Resolve the video to process."""
        if video_path and video_path.exists():
            return video_path

        # Search input directory
        videos = self.video_processor.list_input_videos()
        if videos:
            return videos[0]

        return None

    def _print_summary(self, result: PipelineResult):
        """Print a summary of the pipeline run."""
        log.info(f"\n{'='*60}")
        log.info("PIPELINE COMPLETE")
        log.info(f"{'='*60}")
        log.info(f"  Video:       {result.video_path.name}")
        log.info(f"  Game:        {result.game_name}")
        log.info(f"  Clips:       {result.clips_created}")
        log.info(f"  Uploaded:    {len(result.uploaded_ids)}")
        log.info(f"  Errors:      {len(result.errors)}")
        log.info(f"  Duration:    {result.duration_seconds:.1f}s")

        if result.errors:
            log.warning("  Errors:")
            for e in result.errors:
                log.warning(f"    - {e}")

        if result.titles:
            log.info(f"  Best title:  {result.titles[0]}")
        if result.uploaded_ids:
            log.info(f"  Video URLs:  {[f'https://youtu.be/{id}' for id in result.uploaded_ids]}")
        log.info(f"{'='*60}\n")

    def run_batch(self, video_paths: List[Path] = None) -> List[PipelineResult]:
        """Run pipeline on multiple videos."""
        if video_paths is None:
            video_paths = self.video_processor.list_input_videos()

        results = []
        for video_path in video_paths:
            result = self.run(video_path)
            results.append(result)

        return results

    def run_scheduled(self):
        """Run pipeline with scheduling logic."""
        # Check if we should upload now
        next_time = self.scheduler.get_next_upload_time()
        log.info(f"Next scheduled upload: {next_time}")

        # If queue has items, process them
        if self.scheduler.get_queue_size() > 0:
            next_item = self.scheduler.get_next_from_queue()
            if next_item:
                log.info(f"Processing queued item: {next_item.get('title')}")
                video_path = Path(next_item.get("video_path", ""))
                if video_path.exists():
                    return self.run(video_path)

        # Otherwise, process new video
        return self.run()

    def cleanup(self):
        """Clean up temporary files."""
        self.clip_extractor.cleanup()
        log.info("Temporary files cleaned up")
