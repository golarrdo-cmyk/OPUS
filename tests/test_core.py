import json
from types import SimpleNamespace

import pytest

from dietbot.db import Database
from dietbot.handlers import has_access, parse_number, render_meal
from dietbot.nutrition import daily_targets, meal_totals
from dietbot.vision import FoodRecognizer

ITEMS = [
    {"name": "Гречка", "grams": 200, "kcal_per_100g": 110, "protein_per_100g": 4,
     "fat_per_100g": 1, "carbs_per_100g": 21, "confidence": "high"},
    {"name": "Котлета", "grams": 100, "kcal_per_100g": 250, "protein_per_100g": 15,
     "fat_per_100g": 18, "carbs_per_100g": 8, "confidence": "low"},
]


def test_targets_female_lose():
    tg = daily_targets("female", 80, 165, 35, "light", "lose")
    # BMR = 800 + 1031.25 - 175 - 161 = 1495.25; *1.375*0.85 = 1747.6
    assert tg.kcal == 1748
    assert tg.protein == 128 and tg.fat == 72


def test_targets_floor():
    assert daily_targets("female", 45, 150, 60, "low", "lose").kcal == 1200


def test_meal_totals_and_factor():
    total = meal_totals(ITEMS)
    assert total.kcal == pytest.approx(470)
    assert meal_totals(ITEMS, 0.5).kcal == pytest.approx(235)


def test_render_meal_marks_low_confidence():
    text = render_meal("ru", "Гречка с котлетой", ITEMS, 1.0, "Добавь овощей", 470, 1748)
    assert "470 ккал" in text and "(примерно)" in text and "×" not in text
    assert "×1.25" in render_meal("ru", "x", ITEMS, 1.25, "", 0, 1748)


def test_parse_number():
    assert parse_number("72,4", 35, 300) == 72.4
    assert parse_number("abc", 35, 300) is None
    assert parse_number("500", 35, 300) is None


def test_access():
    cfg = SimpleNamespace(free_photos=5)
    assert has_access({"paid_until": None, "photos_used": 4}, cfg)
    assert not has_access({"paid_until": None, "photos_used": 5}, cfg)
    assert has_access({"paid_until": "2999-01-01T00:00:00+00:00", "photos_used": 99}, cfg)


async def test_db_roundtrip(tmp_path):
    db = Database(str(tmp_path / "t.sqlite3"))
    await db.connect()
    user = await db.ensure_user(1, "ru")
    assert user["photos_used"] == 0
    await db.save_profile(1, sex="male", kcal=2000, bogus="x")
    meal_id = await db.add_meal(1, "2026-09-29", "Гречка", ITEMS)
    await db.set_meal_factor(meal_id, 1, 1.5)
    meals = await db.meals_for_day(1, "2026-09-29")
    assert meals[0]["factor"] == 1.5 and json.loads(meals[0]["items"])[0]["name"] == "Гречка"
    assert await db.get_meal(meal_id, 2) is None  # чужое блюдо недоступно
    await db.add_weight(1, "2026-09-29", 80.0)
    assert (await db.get_user(1))["weight"] == 80.0
    await db.close()


class FakeMessages:
    def __init__(self, payload, stop_reason="end_turn"):
        self.payload, self.stop_reason, self.kwargs = payload, stop_reason, None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            stop_reason=self.stop_reason,
            content=[SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text=json.dumps(self.payload))],
        )


def fake_client(messages):
    return SimpleNamespace(beta=SimpleNamespace(messages=messages))


async def test_recognizer_request_shape():
    payload = {"is_food": True, "dish": "Гречка", "items": ITEMS[:1], "comment": "ok"}
    msgs = FakeMessages(payload)
    result = await FoodRecognizer("claude-opus-5-5", fake_client(msgs)).analyze(b"\xff\xd8", "ru", "200 г")
    assert result.items[0].grams == 200
    kw = msgs.kwargs
    assert kw["output_config"]["effort"] == "low" and kw["fallbacks"] == "default"
    assert kw["messages"][0]["content"][0]["type"] == "image"
    assert "Russian" in kw["system"]


async def test_recognizer_haiku_omits_unsupported_params():
    msgs = FakeMessages({"is_food": False, "dish": "", "items": [], "comment": ""})
    await FoodRecognizer("claude-haiku-4-5", fake_client(msgs)).analyze(b"x", "en")
    assert "effort" not in msgs.kwargs["output_config"] and "fallbacks" not in msgs.kwargs
