"""Хранилище: профили, дневник питания, взвешивания. SQLite через aiosqlite."""
import json
from datetime import datetime, timezone

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    lang TEXT NOT NULL DEFAULT 'ru',
    sex TEXT, age INTEGER, height REAL, weight REAL, goal_weight REAL,
    activity TEXT, goal TEXT,
    kcal INTEGER, protein INTEGER, fat INTEGER, carbs INTEGER,
    tz_offset INTEGER NOT NULL DEFAULT 180,
    photos_used INTEGER NOT NULL DEFAULT 0,
    paid_until TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    day TEXT NOT NULL,
    created_at TEXT NOT NULL,
    dish TEXT NOT NULL,
    items TEXT NOT NULL,
    factor REAL NOT NULL DEFAULT 1.0
);
CREATE INDEX IF NOT EXISTS meals_user_day ON meals(user_id, day);
CREATE TABLE IF NOT EXISTS weights (
    user_id INTEGER NOT NULL,
    day TEXT NOT NULL,
    weight REAL NOT NULL,
    PRIMARY KEY (user_id, day)
);
"""

PROFILE_FIELDS = (
    "sex", "age", "height", "weight", "goal_weight", "activity", "goal",
    "kcal", "protein", "fat", "carbs",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: str):
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()

    async def close(self) -> None:
        if self.conn:
            await self.conn.close()

    async def get_user(self, user_id: int) -> aiosqlite.Row | None:
        async with self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cur:
            return await cur.fetchone()

    async def ensure_user(self, user_id: int, lang: str) -> aiosqlite.Row:
        await self.conn.execute(
            "INSERT OR IGNORE INTO users (id, lang, created_at) VALUES (?, ?, ?)",
            (user_id, lang, now_iso()),
        )
        await self.conn.commit()
        return await self.get_user(user_id)

    async def save_profile(self, user_id: int, **fields) -> None:
        cols = [f for f in fields if f in PROFILE_FIELDS]
        sql = f"UPDATE users SET {', '.join(f'{c} = ?' for c in cols)} WHERE id = ?"
        await self.conn.execute(sql, [fields[c] for c in cols] + [user_id])
        await self.conn.commit()

    async def use_photo(self, user_id: int) -> None:
        await self.conn.execute("UPDATE users SET photos_used = photos_used + 1 WHERE id = ?", (user_id,))
        await self.conn.commit()

    async def add_meal(self, user_id: int, day: str, dish: str, items: list[dict]) -> int:
        cur = await self.conn.execute(
            "INSERT INTO meals (user_id, day, created_at, dish, items) VALUES (?, ?, ?, ?, ?)",
            (user_id, day, now_iso(), dish, json.dumps(items, ensure_ascii=False)),
        )
        await self.conn.commit()
        return cur.lastrowid

    async def get_meal(self, meal_id: int, user_id: int) -> aiosqlite.Row | None:
        async with self.conn.execute(
            "SELECT * FROM meals WHERE id = ? AND user_id = ?", (meal_id, user_id)
        ) as cur:
            return await cur.fetchone()

    async def set_meal_factor(self, meal_id: int, user_id: int, factor: float) -> None:
        await self.conn.execute(
            "UPDATE meals SET factor = ? WHERE id = ? AND user_id = ?", (factor, meal_id, user_id)
        )
        await self.conn.commit()

    async def delete_meal(self, meal_id: int, user_id: int) -> None:
        await self.conn.execute("DELETE FROM meals WHERE id = ? AND user_id = ?", (meal_id, user_id))
        await self.conn.commit()

    async def meals_for_day(self, user_id: int, day: str) -> list[aiosqlite.Row]:
        async with self.conn.execute(
            "SELECT * FROM meals WHERE user_id = ? AND day = ? ORDER BY id", (user_id, day)
        ) as cur:
            return list(await cur.fetchall())

    async def add_weight(self, user_id: int, day: str, weight: float) -> None:
        await self.conn.execute(
            "INSERT OR REPLACE INTO weights (user_id, day, weight) VALUES (?, ?, ?)",
            (user_id, day, weight),
        )
        await self.conn.execute("UPDATE users SET weight = ? WHERE id = ?", (weight, user_id))
        await self.conn.commit()

    async def weight_history(self, user_id: int, limit: int = 10) -> list[aiosqlite.Row]:
        async with self.conn.execute(
            "SELECT day, weight FROM weights WHERE user_id = ? ORDER BY day DESC LIMIT ?",
            (user_id, limit),
        ) as cur:
            return list(await cur.fetchall())
