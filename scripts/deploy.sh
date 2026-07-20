#!/usr/bin/env bash
# =============================================================================
# AI Game Shorts - One-Click Deployment Script
# =============================================================================
# This script automates setup on a fresh Ubuntu/Debian server or local machine.
# Usage: bash scripts/deploy.sh

set -euo pipefail

echo "🎮 AI Game Shorts - Deployment Script"
echo "========================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check OS
OS="$(uname -s)"
case "$OS" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*|MINGW*|MSYS*) MACHINE=Windows;;
    *)          MACHINE="UNKNOWN"
esac

info "Detected OS: $MACHINE"

# --- Install System Dependencies ---
install_system_deps() {
    info "Installing system dependencies..."

    if [ "$MACHINE" = "Linux" ]; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq \
            python3 python3-pip python3-venv \
            ffmpeg \
            git \
            curl \
            wget \
            build-essential \
            cmake
    elif [ "$MACHINE" = "Mac" ]; then
        if ! command -v brew &>/dev/null; then
            warn "Homebrew not found. Installing..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        brew install ffmpeg git python@3.11
    elif [ "$MACHINE" = "Windows" ]; then
        warn "Windows detected. Please install manually:"
        warn "  1. Python 3.10+ from https://python.org"
        warn "  2. FFmpeg from https://ffmpeg.org"
        warn "  3. Git from https://git-scm.com"
        warn "  4. Then run: pip install -r requirements.txt"
    fi
}

# --- Setup Python Environment ---
setup_python_env() {
    info "Setting up Python virtual environment..."

    if [ ! -d "venv" ]; then
        python3 -m venv venv
        info "Virtual environment created"
    fi

    # Activate
    if [ "$MACHINE" = "Windows" ]; then
        source venv/Scripts/activate 2>/dev/null || true
    else
        source venv/bin/activate 2>/dev/null || true
    fi

    # Upgrade pip
    pip install --upgrade pip -q

    # Install dependencies
    info "Installing Python dependencies..."
    pip install -r requirements.txt -q

    # Install project in development mode
    pip install -e . -q

    info "Python environment ready"
}

# --- Setup Configuration ---
setup_config() {
    info "Setting up configuration..."

    # Create .env if it doesn't exist
    if [ ! -f ".env" ]; then
        cp .env.example .env
        info "Created .env file - please add your API keys"
        warn "Edit .env to add your OpenAI/Gemini and YouTube API keys"
    else
        info ".env file already exists"
    fi

    # Create directories
    mkdir -p sample_data output/clips output/thumbnails output/subtitles output/music output/temp

    info "Directories created"
}

# --- Setup YouTube API ---
setup_youtube() {
    info "YouTube API setup instructions:"
    echo ""
    echo "  1. Go to https://console.cloud.google.com/apis/credentials"
    echo "  2. Create a new OAuth 2.0 Client ID (Desktop app)"
    echo "  3. Download the JSON and save as: config/youtube_credentials.json"
    echo "  4. Enable the YouTube Data API v3"
    echo ""
}

# --- Check Installation ---
verify_installation() {
    info "Verifying installation..."

    # Check Python
    python3 --version || error "Python3 not found"

    # Check FFmpeg
    ffmpeg -version &>/dev/null && info "FFmpeg: OK" || error "FFmpeg not found"

    # Check Python packages
    python3 -c "import cv2; print('OpenCV:', cv2.__version__)" 2>/dev/null && info "OpenCV: OK" || warn "OpenCV: Not installed"
    python3 -c "import torch; print('PyTorch:', torch.__version__)" 2>/dev/null && info "PyTorch: OK" || warn "PyTorch: Not installed (optional)"
    python3 -c "import openai; print('OpenAI: OK')" 2>/dev/null && info "OpenAI: OK" || warn "OpenAI: Not installed"

    info "Verification complete!"
}

# --- Main ---
main() {
    cd "$(dirname "$0")/.."  # Move to project root

    echo ""
    info "Starting deployment..."
    echo ""

    install_system_deps
    setup_python_env
    setup_config
    setup_youtube
    verify_installation

    echo ""
    echo "🎉========================================🎉"
    echo "   AI Game Shorts Deployment Complete!"
    echo "🎉========================================🎉"
    echo ""
    echo "Next steps:"
    echo "  1. Edit .env with your API keys"
    echo "  2. Add gameplay videos to sample_data/"
    echo "  3. Activate environment: source venv/bin/activate"
    echo "  4. Create your first Short: python scripts/run_pipeline.py create"
    echo ""
    echo "Or run the full setup wizard: python scripts/run_pipeline.py setup"
    echo ""
}

main "$@"
