"""
Title Generator - Creates catchy, click-optimized titles using AI.
"""
import json
from pathlib import Path
from typing import List, Optional
from utils.config_loader import config
from utils.logger import get_logger

log = get_logger(__name__)


class TitleGenerator:
    """Generates optimized YouTube Shorts titles using AI templates."""

    def __init__(self):
        self.style = config.get("titles", "style", default="click_optimized")
        self.max_length = config.get("titles", "max_length", default=100)
        self.include_emojis = config.get("titles", "include_emojis", default=True)
        self.include_game_name = config.get("titles", "include_game_name", default=True)
        self.templates = config.get("titles", "templates", default=[])
        self._client = None

    def generate(self, game_name: str = "", scene_description: str = "",
                 scene_type: str = "", excitement: int = 5, humor: int = 5,
                 epicness: int = 5) -> List[str]:
        """Generate titles using AI or template fallback."""
        log.info("Generating titles...")

        # Try AI first
        ai_titles = self._generate_with_ai(
            game_name, scene_description, scene_type,
            excitement, humor, epicness
        )
        if ai_titles:
            return ai_titles[:5]

        # Fallback to template-based generation
        return self._generate_from_templates(
            game_name, scene_description, scene_type,
            excitement, humor, epicness
        )

    def _generate_with_ai(self, game_name: str, scene_description: str,
                           scene_type: str, excitement: int, humor: int,
                           epicness: int) -> List[str]:
        """Use AI to generate titles."""
        provider = config.ai_provider
        key = config.openai_key if provider == "openai" else config.gemini_key
        if not key or key == "your_openai_api_key_here":
            return []

        prompt_template = config.get_prompt("title_generation", "")
        if not prompt_template:
            return []

        style_instructions = {
            "click_optimized": "Create curiosity gaps, use power words",
            "descriptive": "Clearly describe what happens in the clip",
            "funny": "Make it humorous and entertaining",
        }

        prompt = prompt_template.format(
            game_name=game_name or "this game",
            scene_type=scene_type or "gameplay",
            scene_description=scene_description or "an exciting moment",
            excitement=excitement,
            humor=humor,
            epicness=epicness,
            style=self.style,
            max_length=self.max_length,
            emoji_instruction="Include ONE relevant emoji at the start" if self.include_emojis else "No emojis",
            style_specific_instructions=style_instructions.get(self.style, ""),
        )

        try:
            if provider == "openai":
                from openai import OpenAI
                client = OpenAI(api_key=key)
                response = client.chat.completions.create(
                    model=config.get("ai", "openai", "model", default="gpt-4o"),
                    messages=[
                        {"role": "system", "content": "You are a YouTube title expert. Respond with valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=500,
                    temperature=0.8,
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

            # Parse JSON response
            import re
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                titles = data.get("titles", [])
                return [t[:self.max_length] for t in titles if t]

        except Exception as e:
            log.warning(f"AI title generation failed: {e}")

        return []

    def _generate_from_templates(self, game_name: str, scene_description: str,
                                  scene_type: str, excitement: int, humor: int,
                                  epicness: int) -> List[str]:
        """Generate titles from templates as fallback."""
        adjectives = {
            "action": ["INSANE", "EPIC", "UNBELIEVABLE", "CRAZY", "LEGENDARY"],
            "fast_paced": ["INTENSE", "NON-STOP", "INSANE", "WILD"],
            "engaging": ["AMAZING", "INCREDIBLE", "STUNNING"],
            "calm": ["BEAUTIFUL", "PEACEFUL", "ATMOSPHERIC"],
        }

        moments = {
            "action": "gameplay",
            "boss_fight": "boss fight",
            "cutscene": "cinematic",
            "combat": "combat",
            "exploration": "discovery",
            "dialogue": "dialogue scene",
            "unknown": "moment",
        }

        adj_list = adjectives.get(scene_type, ["AMAZING"])
        moment_word = moments.get(scene_type, "moment")
        adj = adj_list[min(excitement, len(adj_list) - 1)]

        titles = []
        for template in self.templates:
            title = template.format(
                emoji="🔥",
                title=f"{adj} {moment_word}",
                game=game_name or "Game",
                moment=moment_word,
                adjective=adj.lower(),
            )
            if len(title) <= self.max_length:
                titles.append(title)

        return titles[:5]

    def pick_best(self, titles: List[str]) -> str:
        """Pick the best title from the list."""
        if not titles:
            return "Amazing Gaming Moment 🔥"
        return titles[0]

    def select_title(self, titles: List[str]) -> str:
        """Alias for pick_best."""
        return self.pick_best(titles)
