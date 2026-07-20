# AI Game Shorts 🎮

**Autonomous AI YouTube Shorts Creator for AAA Gaming Content**

AI Game Shorts is a fully autonomous, beginner-friendly tool that scans gameplay footage, detects the most engaging moments using AI, and automatically creates, schedules, and uploads YouTube Shorts.

---

## Features ✨

| Feature | Description |
|---------|-------------|
| **Scene Detection** | Automatically detects scene changes using histogram analysis |
| **Highlight Detection** | Identifies exciting moments via motion analysis, audio peaks, and AI |
| **AI Content Analysis** | Uses GPT-4o/Gemini to understand and classify gameplay moments |
| **Auto Captions** | Speech-to-text with Whisper, auto-generated subtitles |
| **AI Titles** | Click-optimized title generation with multiple style options |
| **AI Hashtags** | Context-aware hashtag generation for maximum reach |
| **Thumbnail Creation** | Dynamic thumbnail extraction with text overlay |
| **Background Music** | Auto-adds background music to Shorts |
| **YouTube Upload** | One-click OAuth and upload to YouTube |
| **Smart Scheduling** | Uploads at optimal times based on audience analytics |
| **Self-Learning** | Improves titles, clip selection, and scheduling from performance data |
| **Performance Analytics** | Tracks views, likes, CTR, retention |
| **Modular Architecture** | Easy to extend with new features |

---

## Requirements 📋

- **Python 3.10 or higher**
- **FFmpeg** (system install)
- **OpenAI API key** OR **Gemini API key**
- **YouTube Data API credentials** (for uploading)

---

## One-Click Setup 🚀

### Option 1: Quick Start (macOS/Linux)

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-game-shorts.git
cd ai-game-shorts

# Run the setup script
bash scripts/setup.sh

# Activate environment
source venv/bin/activate

# Add gameplay videos to sample_data/
# Create your first Short!
python scripts/run_pipeline.py create
```

### Option 2: Full Deployment

```bash
bash scripts/deploy.sh
```

### Option 3: Manual Setup (All Platforms)

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup directories
mkdir -p sample_data output/clips output/thumbnails output/subtitles output/music

# 4. Configure
cp .env.example .env
# Edit .env with your API keys

# 5. Run setup wizard
python scripts/run_pipeline.py setup
```

---

## Configuration ⚙️

### 1. API Keys (`.env` file)

```env
# AI Provider (choose one)
AI_GAME_SHORTS_OPENAI_KEY=sk-your-openai-key
AI_GAME_SHORTS_GEMINI_KEY=your-gemini-key

# YouTube API (after OAuth setup)
AI_GAME_SHORTS_YOUTUBE_CLIENT_SECRET=config/youtube_credentials.json
```

### 2. Settings (`config/settings.yaml`)

All behavior is configured via YAML:
- **AI Provider**: Switch between OpenAI/Gemini
- **Shorts settings**: Duration, resolution, transitions
- **Scene detection**: Sensitivity thresholds
- **Caption styles**: Font, position, animation
- **Upload schedule**: Best posting times and days
- **Hashtag/Learning settings**: Behavior tuning

### 3. YouTube API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing
3. Enable **YouTube Data API v3**
4. Create **OAuth 2.0 Client ID** (Desktop application)
5. Download JSON → save as `config/youtube_credentials.json`
6. First upload will open browser for OAuth consent

---

## Usage 🎯

### Create a Single Short

```bash
# Process a specific video
python scripts/run_pipeline.py create --video "sample_data/elden_ring_gameplay.mp4"

# Dry run (test without uploading)
python scripts/run_pipeline.py create --dry-run

# Specify game name manually
python scripts/run_pipeline.py create --video "clip.mp4" --game "Elden Ring"
```

### Batch Processing

```bash
# Process all videos in sample_data/
python scripts/run_pipeline.py batch

# Process videos from a specific directory
python scripts/run_pipeline.py batch --dir "D:/gameplay_videos"
```

### Watch Mode (Auto-Process New Videos)

```bash
python scripts/run_pipeline.py watch
```

### Analytics

```bash
# View performance dashboard
python scripts/run_pipeline.py analytics

# Run learning cycle (optimize from past performance)
python scripts/run_pipeline.py learn
```

### Setup Wizard

```bash
python scripts/run_pipeline.py setup
```

---

## Project Structure 📁

```
ai-game-shorts/
├── config/                        # Configuration files
│   ├── settings.yaml              # Main settings (edit this!)
│   ├── prompts.yaml               # AI prompt templates
│   └── youtube_credentials.json   # YouTube OAuth (keep secret)
│
├── core/                          # Core video analysis
│   ├── scene_detector.py          # Detects scene changes
│   ├── highlight_analyzer.py      # Finds engaging moments
│   └── clip_extractor.py          # Extracts and crops clips
│
├── ai/                            # AI-powered generators
│   ├── content_analyzer.py        # Understands gameplay context
│   ├── caption_generator.py       # Speech-to-text + captions
│   ├── title_generator.py         # Catchy title generation
│   ├── hashtag_generator.py       # Hashtag optimization
│   └── thumbnail_generator.py     # Thumbnail creation
│
├── media/                         # Media processing
│   ├── video_processor.py         # Video metadata and validation
│   ├── audio_processor.py         # Audio extraction + background music
│   └── subtitle_creator.py        # SRT/ASS subtitle generation
│
├── youtube/                       # YouTube integration
│   ├── uploader.py                # OAuth + video upload
│   ├── scheduler.py               # Smart upload scheduling
│   └── analytics.py               # Performance tracking
│
├── pipeline/                      # Orchestration
│   ├── workflow.py                # Main pipeline coordinator
│   └── learning.py                # Self-improvement engine
│
├── utils/                         # Utilities
│   ├── config_loader.py           # YAML + .env loader
│   ├── file_utils.py              # File operations
│   └── logger.py                  # Logging setup
│
├── scripts/                       # Entry points
│   ├── run_pipeline.py            # CLI with click
│   ├── deploy.sh                  # One-click deploy
│   └── setup.sh                   # Quick setup
│
├── tests/                         # Test suite
├── output/                        # Generated content
├── sample_data/                   # Place your videos here
├── requirements.txt               # Python dependencies
└── .env.example                   # Environment template
```

---

## How It Works 🔄

```
Gameplay Video → Scene Detection → Highlight Analysis → Clip Extraction
                                                          ↓
                                          Caption Generation (Whisper)
                                                          ↓
                                          Title Generation (AI)
                                                          ↓
                                          Hashtag Generation (AI)
                                                          ↓
                                          Thumbnail Creation
                                                          ↓
                                          Background Music
                                                          ↓
                                          YouTube Upload → Scheduling
                                                          ↓
                                          Analytics → Self-Learning → Improvement
```

### Pipeline Steps

1. **Scene Detection** - Scans video frame-by-frame, detects transitions using histogram analysis
2. **Highlight Analysis** - Scores scenes by motion intensity, audio peaks, visual interest
3. **AI Enhancement** - Optional AI analysis classifies scenes and selects best clips
4. **Clip Extraction** - Extracts top clips, crops to 9:16 portrait for Shorts
5. **Caption Generation** - Transcribes audio via Whisper, renders styled subtitles
6. **Content Generation** - AI generates titles, hashtags, descriptions
7. **Thumbnail Creation** - Grabs best frame, enhances, adds text overlay
8. **Upload Pipeline** - Authenticates with YouTube, uploads with metadata
9. **Analytics & Learning** - Tracks performance, optimizes future content

---

## File-by-File Explanation 📖

### `config/settings.yaml`
The brain of the project. Controls every aspect: AI provider choice, scene detection sensitivity, caption styling, upload schedule, and learning parameters. All values have sensible defaults.

### `config/prompts.yaml`
AI prompt templates. Edit these to change how the AI analyzes scenes, generates titles, and selects highlights. Uses `{placeholder}` variables that are filled automatically.

### `core/scene_detector.py`
Analyzes video frame-by-frame using HSV histogram comparison to detect cuts and transitions. Supports content-based, audio-based, and hybrid detection methods.

### `core/highlight_analyzer.py`
Scores each scene for highlight potential using motion analysis (frame differencing), color variety, and optional audio peak detection. Returns ranked highlights.

### `core/clip_extractor.py`
Uses FFmpeg to extract highlight clips from source video. Crops to 9:16 portrait aspect ratio, scales to 1080×1920, applies consistent encoding settings.

### `ai/content_analyzer.py`
Uses OpenAI or Gemini to understand gameplay context. Classifies scenes (cutscene, boss fight, dialogue, etc.) and selects the best highlights based on narrative value.

### `ai/caption_generator.py`
Wraps OpenAI Whisper for speech-to-text transcription. Creates time-coded captions and renders them onto video using FFmpeg subtitles filter.

### `ai/title_generator.py`
Generates click-optimized titles using AI with customizable templates. Supports styles like "click_optimized", "descriptive", and "funny".

### `ai/hashtag_generator.py`
Creates context-aware hashtags combining game-specific tags, trending formats, and broad gaming tags. Uses AI when available, template fallback otherwise.

### `ai/thumbnail_generator.py`
Extracts the most interesting frame from each clip (scored by brightness, contrast, and color), enhances it, and adds text overlay with game name and title.

### `media/video_processor.py`
Extracts video metadata (duration, resolution, codec, FPS) using FFprobe. Validates videos for Shorts suitability and auto-detects game names from filenames.

### `media/audio_processor.py`
Extracts audio tracks for Whisper transcription. Detects audio energy peaks for highlight scoring. Adds background music at configurable volume.

### `media/subtitle_creator.py`
Creates subtitle files in SRT and ASS formats with proper timing and styling. Supports configurable position, font size, and max words per line.

### `youtube/uploader.py`
Handles full OAuth 2.0 flow for YouTube API authentication. Uploads videos with titles, descriptions, hashtags, and optional thumbnails. Manages token refresh.

### `youtube/scheduler.py`
Manages upload queue and calculates optimal posting times based on configurable schedule. Prevents exceeding daily upload limits.

### `youtube/analytics.py`
Fetches video performance metrics (views, likes, comments) via YouTube API. Generates trend analysis and actionable recommendations.

### `pipeline/workflow.py`
The main orchestrator. Coordinates all modules in the correct sequence, handles errors gracefully, and produces a complete PipelineResult with all outputs.

### `pipeline/learning.py`
Self-improvement engine. Analyzes past video performance to optimize title patterns, clip selection weights, and posting schedule. Gets smarter over time.

### `utils/config_loader.py`
Singleton configuration manager. Loads settings.yaml, resolves environment variables for secrets, provides nested key access with defaults.

### `utils/file_utils.py`
Collection of file operations: directory management, video listing, JSON persistence, timestamp formatting, and filename sanitization.

### `utils/logger.py`
Configures loguru with rich console output and optional file logging with rotation. Provides named logger instances.

---

## Deployment ☁️

### Local / Server

```bash
# Full deployment (recommended for first time)
sudo bash scripts/deploy.sh

# Or for quick updates
git pull
source venv/bin/activate
pip install -r requirements.txt
```

### GitHub Actions (CI/CD)

The `.github/workflows/ci.yml` file provides:
- Automatic test running on push/PR
- Lint checking with flake8
- Optional auto-deploy to server via SSH

To enable auto-deploy:
1. Add secrets to GitHub repo: `SSH_HOST`, `SSH_USER`, `SSH_KEY`
2. Uncomment the deploy section in `ci.yml`

### Docker (Coming Soon)

```bash
# Future support
docker build -t ai-game-shorts .
docker run -v ./sample_data:/app/sample_data ai-game-shorts
```

---

## Future Upgrades 🚀

### Short-term (Beginner-Friendly)
- **More AI Providers**: Claude, Mistral, local LLMs
- **Web Dashboard**: Streamlit UI for monitoring and manual editing
- **Template System**: Pre-made Shorts templates for different games
- **Multi-language Support**: Captions and titles in multiple languages

### Medium-term
- **Real-time Processing**: Stream gameplay directly for instant Shorts
- **Game-specific Models**: Fine-tuned models for popular games
- **Trend Integration**: Auto-detect trending games and topics
- **Cross-platform**: TikTok, Instagram Reels support

### Long-term
- **Full MLOps Pipeline**: Model training from collected data
- **Automatic Content Planning**: AI decides what to record and when
- **Community Features**: Share templates and trained models
- **Advanced Video Synthesis**: AI-generated transitions and effects

---

## Performance Tips 💡

1. **GPU Acceleration**: Install PyTorch with CUDA for faster Whisper transcription
2. **Whisper Model**: Use "tiny" or "base" for speed, "large" for accuracy
3. **Scene Threshold**: Lower = more scenes detected (30 is good for most games)
4. **Batch Processing**: Process videos overnight when CPU is idle
5. **Storage**: A 10-minute 4K video produces ~30MB of clips
6. **API Costs**: OpenAI GPT-4o costs ~$0.01 per video analysis

---

## Troubleshooting 🔧

| Problem | Solution |
|---------|----------|
| "FFmpeg not found" | Install FFmpeg: `sudo apt install ffmpeg` or `brew install ffmpeg` |
| "OpenAI key not set" | Copy `.env.example` to `.env` and add your key |
| "YouTube auth failed" | Delete `output/youtube_token.json` and re-authenticate |
| "No scenes detected" | Lower `threshold` in `settings.yaml` (try 20) |
| "No highlights found" | Lower `excitement_threshold` in `settings.yaml` |
| "Video too short" | Minimum 15 seconds of gameplay needed |
| "Upload quota exceeded" | YouTube API has daily quota; wait or use multiple accounts |

---

## License 📄

MIT License - feel free to use, modify, and distribute.

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit a pull request

---

**Made for gamers, by AI** 🎮✨
