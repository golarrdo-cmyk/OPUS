import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    bot_token: str
    model: str
    free_photos: int
    db_path: str


def load_config() -> Config:
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set")
    return Config(
        bot_token=token,
        model=os.environ.get("MODEL", "claude-opus-5-5"),
        free_photos=int(os.environ.get("FREE_PHOTOS", "5")),
        db_path=os.environ.get("DB_PATH", "dietbot.sqlite3"),
    )
