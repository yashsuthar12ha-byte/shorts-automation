"""
Content Analyzer - Uses AI to understand what's happening in the gameplay.
Provides scene classification and highlight scoring via LLM.
"""
import json
from pathlib import Path
from typing import List, Optional, Dict
from core.scene_detector import Scene
from core.highlight_analyzer import Highlight
from utils.config_loader import config
from utils.logger import get_logger

log = get_logger(__name__)


class AIContentAnalyzer:
    """Analyzes gameplay content using AI (OpenAI or Gemini)."""

    def __init__(self):
        self.provider = config.ai_provider
        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize the AI client based on configured provider."""
        if self.provider == "openai":
            from openai import OpenAI
            key = config.openai_key
            if key and key != "your_openai_api_key_here":
                self._client = OpenAI(api_key=key)
                log.info("OpenAI client initialized")
            else:
                log.warning("OpenAI key not set. Set AI_GAME_SHORTS_OPENAI_KEY in .env")
                self._client = None
        elif self.provider == "gemini":
            import google.generativeai as genai
            key = config.gemini_key
            if key and key != "your_gemini_api_key_here":
                genai.configure(api_key=key)
                self._client = genai.GenerativeModel(
                    config.get("ai", "gemini", "model", default="gemini-1.5-pro")
                )
                log.info("Gemini client initialized")
            else:
                log.warning("Gemini key not set. Set AI_GAME_SHORTS_GEMINI_KEY in .env")
                self._client = None

    def is_available(self) -> bool:
        """Check if AI service is configured and available."""
        return self._client is not None

    def analyze_scenes(self, scenes: List[Scene], game_name: str = "") -> List[Scene]:
        """Use AI to classify each scene and add descriptions."""
        if not self.is_available():
            log.info("AI not available, skipping scene analysis")
            return scenes

        log.info(f"Analyzing {len(scenes)} scenes with AI...")
        prompt_template = config.get_prompt("scene_analysis", "")

        for scene in scenes:
            if not prompt_template:
                break
            prompt = prompt_template.format(
                game_name=game_name or "Unknown Game",
                scene_context=self._build_scene_context(scene),
                audio_cues="not available",
                visual_changes=f"Duration: {scene.duration:.1f}s",
                subtitles="not available",
            )
            try:
                result = self._query_ai(prompt)
                parsed = self._parse_json_response(result)
                if parsed:
                    scene.scene_type = parsed.get("scene_type", "unknown")
                    scene.description = parsed.get("summary", "")
            except Exception as e:
                log.warning(f"AI analysis failed for scene {scene.index}: {e}")

        return scenes

    def select_best_highlights(self, highlights: List[Highlight],
                                game_name: str = "", max_clips: int = 5) -> List[Highlight]:
        """Use AI to select and rank the best highlights."""
        if not self.is_available() or not highlights:
            return highlights

        prompt_template = config.get_prompt("highlight_selection", "")
        if not prompt_template:
            return highlights[:max_clips]

        moments_text = "\n".join([
            f"  Moment {h.index}: {h.start_time:.1f}s-{h.end_time:.1f}s "
            f"(score: {h.score:.2f}, type: {h.highlight_type})"
            for h in highlights
        ])

        prompt = prompt_template.format(
            game_name=game_name or "Unknown Game",
            moments=moments_text,
            max_clips=max_clips,
        )

        try:
            result = self._query_ai(prompt)
            parsed = self._parse_json_response(result)
            if parsed and "selected_moments" in parsed:
                selected_indices = {m["index"] for m in parsed["selected_moments"]}
                filtered = [h for h in highlights if h.index in selected_indices]
                if filtered:
                    log.info(f"AI selected {len(filtered)} highlights")
                    return filtered[:max_clips]
        except Exception as e:
            log.warning(f"AI highlight selection failed: {e}")

        return highlights[:max_clips]

    def _build_scene_context(self, scene: Scene) -> str:
        """Build context string for a scene."""
        return (
            f"Scene at {scene.start_time:.1f}s to {scene.end_time:.1f}s, "
            f"duration {scene.duration:.1f}s"
        )

    def _query_ai(self, prompt: str) -> str:
        """Send a prompt to the configured AI and return the response."""
        if self.provider == "openai":
            response = self._client.chat.completions.create(
                model=config.get("ai", "openai", "model", default="gpt-4o"),
                messages=[
                    {"role": "system", "content": "You are a gaming content analysis expert. Respond with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=config.get("ai", "openai", "max_tokens", default=2000),
                temperature=config.get("ai", "openai", "temperature", default=0.7),
            )
            return response.choices[0].message.content.strip()
        else:
            response = self._client.generate_content(prompt)
            return response.text.strip()

    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """Extract JSON from AI response (handles markdown code blocks)."""
        import re
        # Try to find JSON in markdown code blocks
        match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if match:
            text = match.group(1).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            log.warning(f"Failed to parse AI response as JSON: {text[:200]}")
            return None
