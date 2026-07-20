"""
Hashtag Generator - Creates relevant hashtags for YouTube Shorts.
Uses AI when available, with template-based fallback.
"""
import json
import random
from pathlib import Path
from typing import List
from utils.config_loader import config
from utils.logger import get_logger

log = get_logger(__name__)


class HashtagGenerator:
    """Generates optimized hashtags for gaming Shorts."""

    def __init__(self):
        self.count = config.get("hashtags", "count", default=8)
        self.max_length = config.get("hashtags", "max_hashtag_length", default=20)
        self.include_trending = config.get("hashtags", "include_trending", default=True)

        # Broad gaming hashtags always included
        self.generic_tags = [
            "#gaming", "#shorts", "#gamer", "#videogames",
            "#gameplay", "#gamingontiktok", "#gamingcommunity",
            "#epicgaming", "#gameclips", "#gamingvideos",
        ]

    def generate(self, game_name: str = "", scene_description: str = "",
                 scene_type: str = "") -> List[str]:
        """Generate hashtags using AI or template fallback."""
        log.info("Generating hashtags...")

        # Try AI first
        ai_tags = self._generate_with_ai(game_name, scene_description, scene_type)
        if ai_tags:
            return ai_tags[:self.count]

        # Fallback to template-based
        return self._generate_from_templates(game_name, scene_type)

    def _generate_with_ai(self, game_name: str, scene_description: str,
                           scene_type: str) -> List[str]:
        """Use AI to generate contextual hashtags."""
        provider = config.ai_provider
        key = config.openai_key if provider == "openai" else config.gemini_key
        if not key or key == "your_openai_api_key_here":
            return []

        prompt_template = config.get_prompt("hashtag_generation", "")
        if not prompt_template:
            return []

        game_short = game_name.replace(" ", "").lower()[:15] if game_name else "gaming"

        prompt = prompt_template.format(
            count=self.count,
            game_name=game_name or "Gaming",
            game_name_short=game_short,
            scene_description=scene_description or "gaming moment",
            scene_type=scene_type or "gameplay",
            max_length=self.max_length,
        )

        try:
            if provider == "openai":
                from openai import OpenAI
                client = OpenAI(api_key=key)
                response = client.chat.completions.create(
                    model=config.get("ai", "openai", "model", default="gpt-4o"),
                    messages=[
                        {"role": "system", "content": "You are a social media hashtag expert. Respond with JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=300,
                    temperature=0.7,
                )
                text = response.choices[0].message.content.strip()
            else:
                import google.generativeai as genai
                genai.configure(api_key=key)
                model = genai.GenerativeModel(
                    config.get("ai", "gemini", "model", default="gemini-1.5-pro")
                )
                response = model.generate_content(prompt)
                text = response.text.strip()

            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                tags = data.get("hashtags", [])
                return [f"#{t.strip('#')}" for t in tags]

        except Exception as e:
            log.warning(f"AI hashtag generation failed: {e}")

        return []

    def _generate_from_templates(self, game_name: str, scene_type: str) -> List[str]:
        """Generate hashtags from templates as fallback."""
        tags = set()

        # Always add generic tags
        tags.add("#gaming")
        tags.add("#shorts")
        tags.add("#gamer")

        # Add game-specific tag
        if game_name:
            game_tag = f"#{game_name.replace(' ', '').replace(':', '')}"
            if len(game_tag) <= self.max_length:
                tags.add(game_tag)

        # Add scene-type tags
        scene_tags = {
            "action": ["#epicclips", "#actiongame"],
            "boss_fight": ["#bossfight", "#epicbattle"],
            "cutscene": ["#cutscene", "#cinematic"],
            "combat": ["#combat", "#fpsgaming"],
            "exploration": ["#exploration", "#opengame"],
            "dialogue": ["#story", "#rpg"],
            "funny": ["#funnygaming", "#fail"],
            "unknown": ["#gameplayclips"],
        }
        for st, stags in scene_tags.items():
            if st in scene_type.lower() or st == "unknown":
                for t in stags:
                    if len(t) <= self.max_length:
                        tags.add(t)

        # Add trending tags
        trending = [
            "#gamingontiktok", "#gameclips", "#gamingcommunity",
            "#epicgaming", "#gamingvideos",
        ]
        if self.include_trending:
            tags.add(random.choice(trending))

        tag_list = list(tags)
        random.shuffle(tag_list)
        return tag_list[:self.count]

    def format_tags(self, tags: List[str]) -> str:
        """Format hashtags as a space-separated string."""
        return " ".join(tags)
