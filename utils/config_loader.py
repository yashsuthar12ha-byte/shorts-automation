import os
import yaml
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Central configuration manager. Loads settings.yaml + .env + defaults."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def __init__(self):
        if self._loaded:
            return
        self._loaded = True
        load_dotenv()
        self._settings = self._load_yaml()
        self._prompts = self._load_prompts()
        self._resolve_secrets()

    def _load_yaml(self):
        path = Path(__file__).parent.parent / "config" / "settings.yaml"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_prompts(self):
        path = Path(__file__).parent.parent / "config" / "prompts.yaml"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def _resolve_secrets(self):
        """Read API keys from environment variables securely."""
        secrets = self._settings.get("secrets", {})
        for key, env_var in secrets.items():
            value = os.getenv(env_var)
            if value:
                self._settings.setdefault("secrets", {})[key] = value

    def get(self, *keys, default=None):
        """Safely traverse nested keys. Usage: config.get('ai','openai','model')"""
        val = self._settings
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
                if val is None:
                    return default
            else:
                return default
        return val if val is not None else default

    def get_prompt(self, name, default=""):
        return self._prompts.get(name, default)

    @property
    def openai_key(self):
        return self.get("secrets", "openai_api_key_env") or os.getenv("AI_GAME_SHORTS_OPENAI_KEY")

    @property
    def gemini_key(self):
        return self.get("secrets", "gemini_api_key_env") or os.getenv("AI_GAME_SHORTS_GEMINI_KEY")

    @property
    def ai_provider(self):
        return self.get("ai", "provider", default="openai")

    @property
    def output_dir(self):
        return Path(self.get("general", "output_dir", default="output"))

    @property
    def temp_dir(self):
        return Path(self.get("general", "temp_dir", default="output/temp"))


config = Config()
