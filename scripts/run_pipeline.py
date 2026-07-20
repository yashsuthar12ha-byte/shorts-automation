#!/usr/bin/env python3
"""
AI Game Shorts - CLI Entry Point
One-click command to run the full pipeline.
Usage:
    python run_pipeline.py --video "path/to/video.mp4"
    python run_pipeline.py --batch
    python run_pipeline.py --dry-run
    python run_pipeline.py --watch
"""
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import click
from pathlib import Path
from utils.config_loader import config
from utils.logger import setup_logger, get_logger
from pipeline.workflow import Pipeline
from pipeline.learning import LearningSystem
from youtube.analytics import AnalyticsTracker


@click.group()
@click.option("--log-level", default=None, help="Log level (DEBUG, INFO, WARNING, ERROR)")
@click.option("--dry-run", is_flag=True, help="Process videos without uploading")
def cli(log_level, dry_run):
    """AI Game Shorts - Autonomous YouTube Shorts Creator for Gaming Content."""
    level = log_level or config.get("general", "log_level", default="INFO")
    setup_logger(level)
    if dry_run:
        import os
        os.environ["AI_GAME_SHORTS_DRY_RUN"] = "true"
        click.echo("🧪 DRY RUN MODE - No videos will be uploaded")


@cli.command()
@click.option("--video", "-v", type=click.Path(exists=True), help="Path to gameplay video")
@click.option("--game", "-g", default="", help="Game name (auto-detected if not provided)")
def create(video, game):
    """Process a video and create a YouTube Short."""
    click.echo("🎮 AI Game Shorts - Creating Short...")

    pipeline = Pipeline()
    video_path = Path(video) if video else None

    if game:
        import os
        os.environ["DEFAULT_GAME_NAME"] = game

    result = pipeline.run(video_path)

    if result.errors:
        click.echo(f"❌ Completed with {len(result.errors)} errors")
        for err in result.errors:
            click.echo(f"   - {err}")
    else:
        click.echo(f"✅ Success! Created {result.clips_created} clips")
        if result.uploaded_ids:
            for vid in result.uploaded_ids:
                click.echo(f"   📺 https://youtu.be/{vid}")
        if result.titles:
            click.echo(f"   📝 Title: {result.titles[0]}")

    return result


@cli.command()
@click.option("--dir", "-d", "input_dir", type=click.Path(exists=True),
              help="Directory containing video files")
def batch(input_dir):
    """Process all videos in a directory."""
    click.echo("🎮 AI Game Shorts - Batch Processing...")

    if input_dir:
        import os
        os.environ["AI_GAME_SHORTS_INPUT_DIR"] = input_dir

    pipeline = Pipeline()
    results = pipeline.run_batch()

    successful = sum(1 for r in results if not r.errors)
    total_clips = sum(r.clips_created for r in results)
    total_uploads = sum(len(r.uploaded_ids) for r in results)

    click.echo(f"✅ Batch complete: {successful}/{len(results)} processed")
    click.echo(f"   Clips created: {total_clips}")
    click.echo(f"   Videos uploaded: {total_uploads}")


@cli.command()
def watch():
    """Watch input directory and process new videos automatically."""
    click.echo("🎮 AI Game Shorts - Watching for new videos...")

    import time
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    input_dir = Path(config.get("video_input", "input_dir", default="sample_data"))
    input_dir.mkdir(parents=True, exist_ok=True)

    processed = set()

    class VideoHandler(FileSystemEventHandler):
        def on_created(self, event):
            if not event.is_directory:
                path = Path(event.src_path)
                if path.suffix.lower() in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
                    if str(path) not in processed:
                        processed.add(str(path))
                        click.echo(f"📁 New video detected: {path.name}")
                        pipeline = Pipeline()
                        result = pipeline.run(path)
                        if result.uploaded_ids:
                            click.echo(f"   ✅ Uploaded: https://youtu.be/{result.uploaded_ids[0]}")

    event_handler = VideoHandler()
    observer = Observer()
    observer.schedule(event_handler, str(input_dir), recursive=False)
    observer.start()

    click.echo(f"👀 Watching {input_dir} for new videos...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        click.echo("\n👋 Stopped watching")


@cli.command()
def schedule():
    """Run the scheduler to upload at optimal times."""
    click.echo("🎮 AI Game Shorts - Running Scheduler...")

    from youtube.scheduler import UploadScheduler
    scheduler = UploadScheduler()

    next_time = scheduler.get_next_upload_time()
    if next_time:
        click.echo(f"⏰ Next upload time: {next_time}")
    else:
        click.echo("No upcoming upload slots available today")

    # Process next item in queue
    next_item = scheduler.get_next_from_queue()
    if next_item:
        click.echo(f"📤 Next in queue: {next_item.get('title', 'unknown')}")
    else:
        click.echo("Queue is empty - create new Shorts first")


@cli.command()
def learn():
    """Analyze past performance and optimize future content."""
    click.echo("🎮 AI Game Shorts - Learning from Analytics...")

    learning = LearningSystem()
    analytics = AnalyticsTracker()

    # Fetch latest analytics
    click.echo("📊 Fetching video analytics...")
    results = analytics.fetch_all_performance()
    click.echo(f"   Analyzed {len(results)} videos")

    # Generate insights
    insights = analytics.generate_insights()
    click.echo("📈 Insights:")
    for rec in insights.get("recommendations", []):
        click.echo(f"   💡 {rec}")

    # Apply optimizations
    click.echo("🔄 Applying learned optimizations...")
    learning.apply_optimizations()

    click.echo("✅ Learning cycle complete")


@cli.command()
def analytics():
    """View performance analytics and insights."""
    click.echo("🎮 AI Game Shorts - Analytics Dashboard...")

    analytics = AnalyticsTracker()
    insights = analytics.generate_insights()
    trends = insights.get("trends", {})

    click.echo(f"\n📊 Performance Overview:")
    click.echo(f"   Total Uploads: {trends.get('total_uploads', 0)}")
    click.echo(f"   Avg Views: {trends.get('avg_views', 0)}")
    click.echo(f"   Avg Likes: {trends.get('avg_likes', 0)}")
    click.echo(f"   Best Day: {trends.get('best_day', 'N/A')}")
    click.echo(f"   Best Time: {trends.get('best_time', 'N/A')}")

    recs = insights.get("recommendations", [])
    if recs:
        click.echo(f"\n💡 Recommendations:")
        for rec in recs:
            click.echo(f"   - {rec}")

    best_titles = insights.get("best_title_patterns", [])
    if best_titles:
        click.echo(f"\n🏆 Best Performing Titles:")
        for t in best_titles[:3]:
            click.echo(f"   - {t}")


@cli.command()
def setup():
    """Run initial setup and configuration."""
    click.echo("🎮 AI Game Shorts - Setup Wizard")
    click.echo("=" * 50)

    # Check dependencies
    click.echo("\n🔍 Checking dependencies...")
    deps = {
        "opencv": None,
        "moviepy": None,
        "openai": None,
        "PIL": None,
        "yaml": None,
    }

    for dep in deps:
        try:
            __import__(dep if dep != "PIL" else "PIL")
            deps[dep] = "✓"
        except ImportError:
            deps[dep] = "✗"

    for name, status in deps.items():
        click.echo(f"   {status} {name}")

    # Check ffmpeg
    import shutil
    ffmpeg = shutil.which("ffmpeg")
    click.echo(f"   {'✓' if ffmpeg else '✗'} ffmpeg ({ffmpeg or 'not found'})")

    # Check API keys
    import os
    openai_key = os.getenv("AI_GAME_SHORTS_OPENAI_KEY")
    gemini_key = os.getenv("AI_GAME_SHORTS_GEMINI_KEY")
    click.echo(f"   {'✓' if openai_key else '✗'} OpenAI API key")
    click.echo(f"   {'✓' if gemini_key else '✗'} Gemini API key")

    # Ensure directories
    for d in ["sample_data", "output/clips", "output/thumbnails",
              "output/subtitles", "output/music"]:
        Path(d).mkdir(parents=True, exist_ok=True)
        click.echo(f"   ✓ Created {d}/")

    click.echo("\n📋 Next steps:")
    click.echo("   1. Add gameplay videos to sample_data/")
    click.echo("   2. Copy .env.example to .env and add API keys")
    click.echo("   3. Run: python run_pipeline.py create")
    click.echo("\n✅ Setup complete!")


@cli.command()
@click.option("--force", is_flag=True, help="Skip confirmation")
def upgrade(force):
    """Upgrade the project to the latest version."""
    if not force:
        click.confirm("This will update the project. Continue?", abort=True)
    click.echo("🔄 Upgrade functionality coming soon!")
    click.echo("For now, pull the latest from GitHub and reinstall dependencies.")


if __name__ == "__main__":
    cli()
