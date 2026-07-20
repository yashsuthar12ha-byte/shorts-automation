# AI Game Shorts - AGENTS.md

This file helps AI coding assistants understand the project structure and conventions.

## Project: AI Game Shorts

Autonomous AI YouTube Shorts creator for AAA gaming content. Scans gameplay videos, detects engaging moments, creates Shorts, and uploads to YouTube automatically.

## Architecture

```
ai-game-shorts/
├── config/           # YAML/JSON configuration files
├── core/             # Scene detection, highlight analysis, clip extraction
├── ai/               # AI-powered content analysis, captions, titles, hashtags, thumbnails
├── media/            # Video, audio, subtitle processing
├── youtube/          # YouTube API: upload, schedule, analytics
├── pipeline/         # Workflow orchestration & self-learning system
├── utils/            # Config loader, file utils, logger
├── scripts/          # CLI entry point, deploy/setup scripts
├── tests/            # pytest test suite
├── output/           # Generated clips, thumbnails, subtitles
└── sample_data/      # Place gameplay videos here
```

## Key Conventions

- **Config-driven**: All settings in `config/settings.yaml`, no hardcoded values
- **AI Provider**: Switch between OpenAI/Gemini via `config/settings.yaml`
- **Dry Run**: Set `AI_GAME_SHORTS_DRY_RUN=true` to test without uploading
- **Secrets**: API keys go in `.env` file (never committed)

## Commands

```bash
# Create a Short from a video
python scripts/run_pipeline.py create --video "path/to/video.mp4"

# Process all videos in sample_data/
python scripts/run_pipeline.py batch

# View analytics dashboard
python scripts/run_pipeline.py analytics

# Run initial setup wizard
python scripts/run_pipeline.py setup

# Watch directory for new videos
python scripts/run_pipeline.py watch
```

## Code Style

- Python 3.10+ type hints on all functions
- Dataclasses for data objects
- loguru for logging
- No comments in code (self-documenting)
- YAML for configuration
- JSON for data persistence (output/ directory)

## Testing

```bash
pytest tests/ -v
```

## Dependencies

- Python 3.10+
- FFmpeg (system install)
- OpenAI or Gemini API key
- YouTube Data API credentials (for uploads)
