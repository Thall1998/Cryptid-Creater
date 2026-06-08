import os
from dataclasses import dataclass

from dotenv import load_dotenv


# Settings is a simple container for values the bot needs at startup.
# frozen=True means the values should not be changed after they are loaded.
@dataclass(frozen=True)
class Settings:
    discord_token: str
    gemini_api_key: str
    gemini_model: str
    sync_commands: bool
    keep_alive: bool
    database_path: str


def load_settings() -> Settings:
    # Loads variables from a local .env file into the environment.
    # Example: DISCORD_TOKEN=abc123
    load_dotenv()

    # Pull the required secret keys out of environment variables.
    # strip() removes accidental spaces before or after the value.
    discord_token = os.getenv("DISCORD_TOKEN", "").strip()
    gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()

    # These two are required. Without them the bot cannot log in or call AI.
    if not discord_token:
        raise RuntimeError("Missing DISCORD_TOKEN. Add it to your .env file.")

    if not gemini_api_key:
        raise RuntimeError("Missing GEMINI_API_KEY. Add it to your .env file.")

    # Render Web Services provide PORT and expect the process to bind to it.
    keep_alive_default = "true" if os.getenv("PORT") else "false"

    # Optional settings have default values so the bot can run with a simple .env.
    return Settings(
        discord_token=discord_token,
        gemini_api_key=gemini_api_key,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip(),
        sync_commands=os.getenv("SYNC_COMMANDS", "true").lower() == "true",
        keep_alive=os.getenv("KEEP_ALIVE", keep_alive_default).lower() == "true",
        database_path=os.getenv("DATABASE_PATH", "data/cryptid_stories.sqlite3").strip(),
    )
