import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Config:
    """
    Configuration class for the bot.
    Loads all settings from environment variables.
    """

    # Bot token from @BotFather
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8283774586:AAFjmKWo0HfCOTFzK5BbgiVFjpi_2abstP0")

    # Admin user IDs (comma-separated in .env)
    ADMIN_IDS: List[int] = [
        int(id_.strip())
        for id_ in os.getenv("ADMIN_IDS", "1920079641").split(",")
        if id_.strip()
    ]

    # Photographer ID (receives reminders)
    PHOTOGRAPHER_ID: int = int(os.getenv("PHOTOGRAPHER_ID", "1920079641"))

    # Database path
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "events.db")

    @classmethod
    def validate(cls):
        """Validate that required config values are set"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is not set in .env file")
        if not cls.ADMIN_IDS:
            raise ValueError("ADMIN_IDS is not set in .env file")
        if not cls.PHOTOGRAPHER_ID:
            raise ValueError("PHOTOGRAPHER_ID is not set in .env file")


# Validate config on import
Config.validate()