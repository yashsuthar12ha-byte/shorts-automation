#!/usr/bin/env bash
# =============================================================================
# AI Game Shorts - Quick Setup Script (macOS/Linux)
# =============================================================================
# Usage: bash scripts/setup.sh

set -euo pipefail

cd "$(dirname "$0")/.."

echo "🎮 AI Game Shorts - Quick Setup"
echo "================================"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip -q

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt -q
pip install -e . -q

# Setup directories
echo "📁 Creating directories..."
mkdir -p sample_data output/clips output/thumbnails output/subtitles output/music output/temp

# Create .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Created .env - add your API keys before running"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next:"
echo "  1. Add videos to sample_data/"
echo "  2. Edit .env with API keys"
echo "  3. Run: source venv/bin/activate"
echo "  4. Run: python scripts/run_pipeline.py create"
echo ""
